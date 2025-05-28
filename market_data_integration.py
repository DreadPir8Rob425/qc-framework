# Option Alpha Framework - Phase 2: Market Data Integration
# Real-time market data feeds with technical analysis and regime detection

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import asyncio
import threading
from collections import deque
import json

from oa_framework_enums import (
    LogCategory, MarketRegime, VolatilityEnvironment, 
    TechnicalIndicator, EventType
)
from oa_logging import FrameworkLogger
from oa_data_structures import Event
from enhanced_decision_engine import EnhancedMarketData

# =============================================================================
# MARKET DATA INTERFACES
# =============================================================================

class MarketDataProvider(ABC):
    """Abstract base class for market data providers"""
    
    @abstractmethod
    def get_current_quote(self, symbol: str) -> Optional[EnhancedMarketData]:
        """Get current market quote for symbol"""
        pass
    
    @abstractmethod
    def get_historical_data(self, symbol: str, bars: int, 
                          timeframe: str = '1D') -> List[EnhancedMarketData]:
        """Get historical data for symbol"""
        pass
    
    @abstractmethod
    def subscribe_to_updates(self, symbols: List[str], 
                           callback: Callable[[str, EnhancedMarketData], None]) -> None:
        """Subscribe to real-time updates"""
        pass
    
    @abstractmethod
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        pass

# =============================================================================
# SIMULATED MARKET DATA PROVIDER
# =============================================================================

class SimulatedMarketDataProvider(MarketDataProvider):
    """
    Simulated market data provider for backtesting and testing.
    Generates realistic price movements and technical patterns.
    """
    
    def __init__(self, logger: FrameworkLogger):
        self.logger = logger
        self._current_data: Dict[str, EnhancedMarketData] = {}
        self._historical_data: Dict[str, List[EnhancedMarketData]] = {}
        self._subscribers: List[Callable[[str, EnhancedMarketData], None]] = []
        
        # Market state
        self._market_open = True
        self._current_time = datetime.now()
        
        # Initialize with baseline data
        self._initialize_baseline_data()
        
        self.logger.info(LogCategory.MARKET_DATA, "Simulated market data provider initialized")
    
    def _initialize_baseline_data(self) -> None:
        """Initialize baseline market data for common symbols"""
        baseline_prices = {
            'SPY': 450.0,
            'QQQ': 380.0,
            'IWM': 200.0,
            'VIX': 18.0,
            'TLT': 100.0,
            'GLD': 180.0,
            'AAPL': 175.0,
            'MSFT': 380.0,
            'GOOGL': 140.0,
            'AMZN': 150.0,
            'TSLA': 250.0,
            'NVDA': 450.0
        }
        
        for symbol, base_price in baseline_prices.items():
            # Generate initial historical data (50 bars)
            historical_data = self._generate_historical_data(symbol, base_price, 50)
            self._historical_data[symbol] = historical_data
            
            # Set current data to latest historical bar
            if historical_data:
                self._current_data[symbol] = historical_data[-1]
    
    def _generate_historical_data(self, symbol: str, base_price: float, 
                                bars: int) -> List[EnhancedMarketData]:
        """Generate realistic historical data"""
        data = []
        current_price = base_price
        
        # Symbol-specific parameters
        if symbol == 'VIX':
            volatility = 0.15  # VIX is more volatile
            trend = -0.001  # Slight downward bias
        elif symbol in ['TSLA', 'NVDA']:
            volatility = 0.03  # High vol stocks
            trend = 0.001
        elif symbol in ['SPY', 'QQQ']:
            volatility = 0.015  # Market ETFs
            trend = 0.0005
        else:
            volatility = 0.02  # Default
            trend = 0.0
        
        for i in range(bars):
            timestamp = datetime.now() - timedelta(days=bars-i)
            
            # Generate OHLC using random walk with mean reversion
            daily_return = np.random.normal(trend, volatility)
            
            # Mean reversion component
            if abs(current_price - base_price) / base_price > 0.1:
                reversion = -0.5 * (current_price - base_price) / base_price
                daily_return += reversion
            
            # Calculate new price
            new_price = current_price * (1 + daily_return)
            
            # Generate intraday high/low
            intraday_vol = volatility * 0.5
            high = new_price * (1 + abs(np.random.normal(0, intraday_vol)))
            low = new_price * (1 - abs(np.random.normal(0, intraday_vol)))
            
            # Ensure proper OHLC relationship
            open_price = current_price
            close_price = new_price
            high = max(high, open_price, close_price)
            low = min(low, open_price, close_price)
            
            # Generate volume (higher volume on larger moves)
            base_volume = 1000000 if symbol in ['SPY', 'QQQ'] else 500000
            volume_factor = 1 + abs(daily_return) * 5
            volume = int(base_volume * volume_factor * np.random.uniform(0.5, 1.5))
            
            # Calculate IV rank (simulated)
            iv_rank = max(0, min(100, 50 + 20 * np.sin(i / 10) + np.random.normal(0, 10)))
            
            # Create market data
            market_data = EnhancedMarketData(
                symbol=symbol,
                timestamp=timestamp,
                open=round(open_price, 2),
                high=round(high, 2),
                low=round(low, 2),
                close=round(close_price, 2),
                volume=volume,
                bid=round(close_price - 0.01, 2),
                ask=round(close_price + 0.01, 2),
                iv_rank=round(iv_rank, 1),
                volatility=volatility * 100  # Convert to percentage
            )
            
            data.append(market_data)
            current_price = close_price
        
        return data
    
    def get_current_quote(self, symbol: str) -> Optional[EnhancedMarketData]:
        """Get current market quote"""
        return self._current_data.get(symbol)
    
    def get_historical_data(self, symbol: str, bars: int, 
                          timeframe: str = '1D') -> List[EnhancedMarketData]:
        """Get historical data"""
        if symbol not in self._historical_data:
            return []
        
        historical = self._historical_data[symbol]
        return historical[-bars:] if bars > 0 else historical
    
    def subscribe_to_updates(self, symbols: List[str], 
                           callback: Callable[[str, EnhancedMarketData], None]) -> None:
        """Subscribe to market data updates"""
        self._subscribers.append(callback)
        self.logger.info(LogCategory.MARKET_DATA, "Subscribed to market data updates",
                        symbols=symbols)
    
    def is_market_open(self) -> bool:
        """Check if market is open (simulated)"""
        return self._market_open
    
    def update_market_data(self, symbol: str, price_change_pct: float = None) -> None:
        """Manually update market data (for testing)"""
        if symbol not in self._current_data:
            return
        
        current = self._current_data[symbol]
        
        if price_change_pct is None:
            # Generate random price movement
            if symbol == 'VIX':
                price_change_pct = np.random.normal(0, 0.05)  # 5% daily vol for VIX
            else:
                price_change_pct = np.random.normal(0, 0.02)  # 2% daily vol for stocks
        
        # Calculate new prices
        new_close = current.close * (1 + price_change_pct)
        high = max(current.high, new_close * 1.005)
        low = min(current.low, new_close * 0.995)
        
        # Update current data
        updated_data = EnhancedMarketData(
            symbol=symbol,
            timestamp=datetime.now(),
            open=current.close,  # Previous close becomes new open
            high=round(high, 2),
            low=round(low, 2),
            close=round(new_close, 2),
            volume=int(current.volume * np.random.uniform(0.8, 1.2)),
            bid=round(new_close - 0.01, 2),
            ask=round(new_close + 0.01, 2),
            iv_rank=current.iv_rank,
            volatility=current.volatility
        )
        
        self._current_data[symbol] = updated_data
        
        # Add to historical data
        self._historical_data[symbol].append(updated_data)
        
        # Keep only last 200 bars
        if len(self._historical_data[symbol]) > 200:
            self._historical_data[symbol] = self._historical_data[symbol][-200:]
        
        # Notify subscribers
        for callback in self._subscribers:
            try:
                callback(symbol, updated_data)
            except Exception as e:
                self.logger.error(LogCategory.MARKET_DATA, 
                                "Error in market data callback", error=str(e))
    
    def simulate_market_scenario(self, scenario: str) -> None:
        """Simulate specific market scenarios for testing"""
        if scenario == 'bull_market':
            # Simulate strong upward movement
            for symbol in ['SPY', 'QQQ', 'IWM']:
                self.update_market_data(symbol, 0.02)  # 2% up
            self.update_market_data('VIX', -0.1)  # VIX down 10%
            
        elif scenario == 'bear_market':
            # Simulate strong downward movement
            for symbol in ['SPY', 'QQQ', 'IWM']:
                self.update_market_data(symbol, -0.03)  # 3% down
            self.update_market_data('VIX', 0.2)  # VIX up 20%
            
        elif scenario == 'high_volatility':
            # Simulate high volatility scenario
            for symbol in self._current_data.keys():
                if symbol != 'VIX':
                    change = np.random.normal(0, 0.05)  # 5% volatility
                    self.update_market_data(symbol, change)
            self.update_market_data('VIX', 0.3)  # VIX up 30%
            
        elif scenario == 'normal':
            # Simulate normal market conditions
            for symbol in self._current_data.keys():
                self.update_market_data(symbol)  # Random normal movement
        
        self.logger.info(LogCategory.MARKET_DATA, f"Simulated market scenario: {scenario}")

# =============================================================================
# MARKET REGIME DETECTOR
# =============================================================================

class MarketRegimeDetector:
    """
    Detects market regimes using technical analysis and market indicators.
    Supports multiple regime detection algorithms.
    """
    
    def __init__(self, logger: FrameworkLogger, market_data_provider: MarketDataProvider):
        self.logger = logger
        self.market_data_provider = market_data_provider
        self._current_regime = MarketRegime.SIDEWAYS
        self._regime_confidence = 0.5
        self._regime_history: deque = deque(maxlen=100)
    
    def detect_current_regime(self) -> Tuple[MarketRegime, float]:
        """
        Detect current market regime with confidence score.
        
        Returns:
            Tuple of (regime, confidence_score)
        """
        try:
            # Get market data for analysis
            spy_data = self.market_data_provider.get_historical_data('SPY', 50)
            vix_data = self.market_data_provider.get_current_quote('VIX')
            
            if not spy_data or len(spy_data) < 20:
                return self._current_regime, self._regime_confidence
            
            # Extract prices
            prices = [bar.close for bar in spy_data]
            highs = [bar.high for bar in spy_data]
            lows = [bar.low for bar in spy_data]
            
            # Calculate technical indicators
            sma_20 = np.mean(prices[-20:])
            sma_50 = np.mean(prices[-50:]) if len(prices) >= 50 else sma_20
            current_price = prices[-1]
            
            # Calculate price momentum
            returns_10d = [(prices[i] - prices[i-10]) / prices[i-10] for i in range(10, len(prices))]
            avg_return_10d = np.mean(returns_10d) if returns_10d else 0
            
            # Calculate volatility
            returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
            volatility = np.std(returns) * np.sqrt(252)  # Annualized
            
            # VIX level
            vix_level = vix_data.close if vix_data else 20
            
            # Regime detection logic
            regime_scores = {
                MarketRegime.BULL_MARKET: 0,
                MarketRegime.BEAR_MARKET: 0,
                MarketRegime.SIDEWAYS: 0,
                MarketRegime.HIGH_VOLATILITY: 0,
                MarketRegime.LOW_VOLATILITY: 0
            }
            
            # Price trend analysis
            if current_price > sma_20 > sma_50 and avg_return_10d > 0.02:
                regime_scores[MarketRegime.BULL_MARKET] += 40
            elif current_price < sma_20 < sma_50 and avg_return_10d < -0.02:
                regime_scores[MarketRegime.BEAR_MARKET] += 40
            else:
                regime_scores[MarketRegime.SIDEWAYS] += 30
            
            # Volatility analysis
            if vix_level > 25 or volatility > 0.25:
                regime_scores[MarketRegime.HIGH_VOLATILITY] += 30
            elif vix_level < 15 and volatility < 0.15:
                regime_scores[MarketRegime.LOW_VOLATILITY] += 30
            
            # Momentum analysis
            if avg_return_10d > 0.01:
                regime_scores[MarketRegime.BULL_MARKET] += 20
            elif avg_return_10d < -0.01:
                regime_scores[MarketRegime.BEAR_MARKET] += 20
            
            # Price action analysis (breakouts, support/resistance)
            recent_high = max(highs[-10:])
            recent_low = min(lows[-10:])
            price_range = recent_high - recent_low
            
            if current_price > recent_high * 0.99:  # Near highs
                regime_scores[MarketRegime.BULL_MARKET] += 15
            elif current_price < recent_low * 1.01:  # Near lows
                regime_scores[MarketRegime.BEAR_MARKET] += 15
            
            if price_range / current_price < 0.02:  # Low price range
                regime_scores[MarketRegime.SIDEWAYS] += 20
            
            # Determine best regime
            best_regime = max(regime_scores, key=regime_scores.get)
            confidence = regime_scores[best_regime] / 100.0
            
            # Smooth regime changes (require higher confidence to change)
            if best_regime != self._current_regime:
                if confidence > 0.6:  # Higher threshold for regime change
                    self._current_regime = best_regime
                    self._regime_confidence = confidence
                    self.logger.info(LogCategory.MARKET_DATA, 
                                   f"Market regime changed to {best_regime.value}",
                                   confidence=confidence)
            else:
                self._regime_confidence = confidence
            
            # Record regime history
            self._regime_history.append({
                'timestamp': datetime.now(),
                'regime': self._current_regime,
                'confidence': self._regime_confidence,
                'vix_level': vix_level,
                'volatility': volatility
            })
            
            return self._current_regime, self._regime_confidence
            
        except Exception as e:
            self.logger.error(LogCategory.MARKET_DATA, "Regime detection failed", error=str(e))
            return self._current_regime, self._regime_confidence
    
    def get_regime_history(self, periods: int = 20) -> List[Dict[str, Any]]:
        """Get recent regime detection history"""
        return list(self._regime_history)[-periods:]
    
    def get_regime_stability(self) -> float:
        """Calculate regime stability (how often regime changes)"""
        if len(self._regime_history) < 10:
            return 0.5
        
        recent_regimes = [entry['regime'] for entry in list(self._regime_history)[-20:]]
        regime_changes = sum(1 for i in range(1, len(recent_regimes)) 
                           if recent_regimes[i] != recent_regimes[i-1])
        
        stability = 1.0 - (regime_changes / len(recent_regimes))
        return max(0.0, min(1.0, stability))

# =============================================================================
# VOLATILITY ENVIRONMENT DETECTOR
# =============================================================================

class VolatilityEnvironmentDetector:
    """
    Detects volatility environment using VIX and realized volatility analysis.
    """
    
    def __init__(self, logger: FrameworkLogger, market_data_provider: MarketDataProvider):
        self.logger = logger
        self.market_data_provider = market_data_provider
        self._current_environment = VolatilityEnvironment.NORMAL_IV
        self._vol_history: deque = deque(maxlen=100)
    
    def detect_volatility_environment(self) -> Tuple[VolatilityEnvironment, Dict[str, float]]:
        """
        Detect current volatility environment.
        
        Returns:
            Tuple of (environment, metrics_dict)
        """
        try:
            # Get VIX data
            vix_data = self.market_data_provider.get_current_quote('VIX')
            vix_history = self.market_data_provider.get_historical_data('VIX', 30)
            
            # Get SPY data for realized volatility
            spy_history = self.market_data_provider.get_historical_data('SPY', 30)
            
            if not vix_data or not vix_history or not spy_history:
                return self._current_environment, {}
            
            current_vix = vix_data.close
            vix_prices = [bar.close for bar in vix_history]
            spy_prices = [bar.close for bar in spy_history]
            
            # Calculate metrics
            vix_percentile = self._calculate_percentile(current_vix, vix_prices)
            vix_ma = np.mean(vix_prices[-20:])
            
            # Calculate realized volatility (20-day)
            spy_returns = [(spy_prices[i] - spy_prices[i-1]) / spy_prices[i-1] 
                          for i in range(1, len(spy_prices))]
            realized_vol = np.std(spy_returns) * np.sqrt(252) * 100  # Annualized %
            
            # VIX term structure (simplified)
            vix_trend = (current_vix - vix_ma) / vix_ma if vix_ma > 0 else 0
            
            # IV vs RV ratio
            iv_rv_ratio = current_vix / realized_vol if realized_vol > 0 else 1.0
            
            metrics = {
                'current_vix': current_vix,
                'vix_percentile': vix_percentile,
                'vix_ma_20': vix_ma,
                'realized_vol_20d': realized_vol,
                'iv_rv_ratio': iv_rv_ratio,
                'vix_trend': vix_trend
            }
            
            # Environment detection logic
            if current_vix < 12 and vix_percentile < 20:
                environment = VolatilityEnvironment.LOW_IV
            elif current_vix > 30 and vix_percentile > 80:
                environment = VolatilityEnvironment.VERY_HIGH_IV
            elif current_vix > 22 and vix_percentile > 70:
                environment = VolatilityEnvironment.HIGH_IV
            elif vix_trend < -0.1 and iv_rv_ratio < 0.8:
                environment = VolatilityEnvironment.IV_CONTRACTION
            elif vix_trend > 0.15 and iv_rv_ratio > 1.2:
                environment = VolatilityEnvironment.IV_EXPANSION
            else:
                environment = VolatilityEnvironment.NORMAL_IV
            
            # Update current environment
            if environment != self._current_environment:
                self.logger.info(LogCategory.MARKET_DATA, 
                               f"Volatility environment changed to {environment.value}",
                               metrics=metrics)
                self._current_environment = environment
            
            # Record history
            self._vol_history.append({
                'timestamp': datetime.now(),
                'environment': environment,
                'metrics': metrics
            })
            
            return environment, metrics
            
        except Exception as e:
            self.logger.error(LogCategory.MARKET_DATA, "Volatility detection failed", error=str(e))
            return self._current_environment, {}
    
    def _calculate_percentile(self, value: float, data: List[float]) -> float:
        """Calculate percentile rank of value in data"""
        if not data:
            return 50.0
        
        sorted_data = sorted(data)
        rank = sum(1 for x in sorted_data if x <= value)
        percentile = (rank / len(sorted_data)) * 100
        return percentile
    
    def get_volatility_metrics(self) -> Dict[str, Any]:
        """Get comprehensive volatility metrics"""
        try:
            environment, metrics = self.detect_volatility_environment()
            
            # Add historical context
            if len(self._vol_history) > 10:
                recent_envs = [entry['environment'] for entry in list(self._vol_history)[-10:]]
                env_changes = sum(1 for i in range(1, len(recent_envs)) 
                                if recent_envs[i] != recent_envs[i-1])
                metrics['environment_stability'] = 1.0 - (env_changes / len(recent_envs))
            
            metrics['current_environment'] = environment.value
            return metrics
            
        except Exception as e:
            self.logger.error(LogCategory.MARKET_DATA, "Failed to get volatility metrics", 
                            error=str(e))
            return {}

# =============================================================================
# INTEGRATED MARKET DATA MANAGER
# =============================================================================

class MarketDataManager:
    """
    Central manager for all market data operations.
    Integrates market data provider, regime detection, and volatility analysis.
    """
    
    def __init__(self, logger: FrameworkLogger, event_bus=None):
        self.logger = logger
        self.event_bus = event_bus
        
        # Initialize components
        self.market_data_provider = SimulatedMarketDataProvider(logger)
        self.regime_detector = MarketRegimeDetector(logger, self.market_data_provider)
        self.volatility_detector = VolatilityEnvironmentDetector(logger, self.market_data_provider)
        
        # State tracking
        self._last_regime_check = datetime.now()
        self._last_volatility_check = datetime.now()
        self._update_frequency = 60  # Check every 60 seconds
        
        # Subscribe to market data updates
        self.market_data_provider.subscribe_to_updates(
            ['SPY', 'QQQ', 'IWM', 'VIX'], 
            self._on_market_data_update
        )
        
        self.logger.info(LogCategory.MARKET_DATA, "Market Data Manager initialized")
    
    def _on_market_data_update(self, symbol: str, data: EnhancedMarketData) -> None:
        """Handle market data updates"""
        try:
            # Check if we should update regime/volatility analysis
            now = datetime.now()
            
            if (now - self._last_regime_check).seconds >= self._update_frequency:
                regime, confidence = self.regime_detector.detect_current_regime()
                self._last_regime_check = now
                
                # Publish regime change event
                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type=EventType.MARKET_DATA_UPDATE.value,
                        timestamp=now,
                        data={
                            'type': 'regime_update',
                            'regime': regime.value,
                            'confidence': confidence
                        }
                    ))
            
            if (now - self._last_volatility_check).seconds >= self._update_frequency:
                vol_env, metrics = self.volatility_detector.detect_volatility_environment()
                self._last_volatility_check = now
                
                # Publish volatility update event
                if self.event_bus:
                    self.event_bus.publish(Event(
                        event_type=EventType.MARKET_DATA_UPDATE.value,
                        timestamp=now,
                        data={
                            'type': 'volatility_update',
                            'environment': vol_env.value,
                            'metrics': metrics
                        }
                    ))
            
        except Exception as e:
            self.logger.error(LogCategory.MARKET_DATA, "Error processing market data update",
                            symbol=symbol, error=str(e))
    
    def get_current_market_state(self) -> Dict[str, Any]:
        """Get comprehensive current market state"""
        regime, regime_confidence = self.regime_detector.detect_current_regime()
        vol_env, vol_metrics = self.volatility_detector.detect_volatility_environment()
        
        # Get key market prices
        spy_data = self.market_data_provider.get_current_quote('SPY')
        vix_data = self.market_data_provider.get_current_quote('VIX')
        
        market_state = {
            'timestamp': datetime.now().isoformat(),
            'market_regime': {
                'regime': regime.value,
                'confidence': regime_confidence,
                'stability': self.regime_detector.get_regime_stability()
            },
            'volatility_environment': {
                'environment': vol_env.value,
                'metrics': vol_metrics
            },
            'key_levels': {
                'SPY': spy_data.close if spy_data else None,
                'VIX': vix_data.close if vix_data else None
            },
            'market_open': self.market_data_provider.is_market_open()
        }
        
        return market_state
    
    def update_market_data(self, symbol: str, data: EnhancedMarketData) -> None:
        """Update market data for a symbol"""
        if hasattr(self.market_data_provider, 'update_market_data'):
            self.market_data_provider.update_market_data(symbol)
    
    def simulate_market_scenario(self, scenario: str) -> None:
        """Simulate market scenario for testing"""
        if hasattr(self.market_data_provider, 'simulate_market_scenario'):
            self.market_data_provider.simulate_market_scenario(scenario)
    
    def get_market_analytics(self) -> Dict[str, Any]:
        """Get comprehensive market analytics"""
        return {
            'market_state': self.get_current_market_state(),
            'regime_history': self.regime_detector.get_regime_history(),
            'volatility_metrics': self.volatility_detector.get_volatility_metrics()
        }

# =============================================================================
# FACTORY FUNCTIONS
# =============================================================================

def create_market_data_manager(logger: FrameworkLogger, event_bus=None) -> MarketDataManager:
    """Factory function to create market data manager"""
    return MarketDataManager(logger, event_bus)

def create_simulated_market_data_provider(logger: FrameworkLogger) -> SimulatedMarketDataProvider:
    """Factory function to create simulated market data provider"""
    return SimulatedMarketDataProvider(logger)