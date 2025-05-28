# Option Alpha Framework - Phase 2: Enhanced Decision Engine
# Comprehensive decision engine with full Option Alpha recipe support

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json

from oa_framework_enums import (
    DecisionType, DecisionResult, ComparisonOperator, TechnicalIndicator,
    LogCategory, MarketRegime, VolatilityEnvironment
)
from oa_logging import FrameworkLogger
from oa_data_structures import MarketData, Position
from decision_core import DecisionContext, DetailedDecisionResult, ComparisonEvaluator

# =============================================================================
# ENHANCED TECHNICAL INDICATOR ENGINE
# =============================================================================

class TechnicalIndicatorEngine:
    """
    Advanced technical indicator calculations for decision engine.
    Supports all indicators used in Option Alpha recipes.
    """
    
    def __init__(self, logger: FrameworkLogger):
        self.logger = logger
        self._indicator_cache: Dict[str, Dict] = {}
        
    def calculate_indicator(self, indicator_type: TechnicalIndicator, 
                          price_data: Union[List[float], pd.Series],
                          period: int = 14,
                          **kwargs) -> Optional[float]:
        """
        Calculate technical indicator value.
        
        Args:
            indicator_type: Type of indicator to calculate
            price_data: Historical price data
            period: Calculation period
            **kwargs: Additional parameters for specific indicators
            
        Returns:
            Current indicator value or None if insufficient data
        """
        try:
            # Convert to pandas Series for easier calculation
            if isinstance(price_data, list):
                prices = pd.Series(price_data)
            else:
                prices = price_data
                
            if len(prices) < period:
                self.logger.warning(LogCategory.DECISION_FLOW, 
                                  f"Insufficient data for {indicator_type.value}",
                                  required=period, available=len(prices))
                return None
            
            # Route to appropriate calculation method
            if indicator_type == TechnicalIndicator.RSI:
                return self._calculate_rsi(prices, period)
            elif indicator_type == TechnicalIndicator.SMA:
                return self._calculate_sma(prices, period)
            elif indicator_type == TechnicalIndicator.EMA:
                return self._calculate_ema(prices, period)
            elif indicator_type == TechnicalIndicator.MACD:
                return self._calculate_macd(prices, **kwargs)
            elif indicator_type == TechnicalIndicator.STOCH_K:
                high_data = kwargs.get('high_data', prices)
                low_data = kwargs.get('low_data', prices)
                return self._calculate_stochastic_k(prices, high_data, low_data, period)
            elif indicator_type == TechnicalIndicator.CCI:
                return self._calculate_cci(prices, period)
            elif indicator_type == TechnicalIndicator.ADX:
                high_data = kwargs.get('high_data', prices)
                low_data = kwargs.get('low_data', prices)
                return self._calculate_adx(prices, high_data, low_data, period)
            elif indicator_type == TechnicalIndicator.ATR:
                high_data = kwargs.get('high_data', prices)
                low_data = kwargs.get('low_data', prices)
                return self._calculate_atr(prices, high_data, low_data, period)
            elif indicator_type == TechnicalIndicator.WILLIAMS_R:
                high_data = kwargs.get('high_data', prices)
                low_data = kwargs.get('low_data', prices)
                return self._calculate_williams_r(prices, high_data, low_data, period)
            else:
                self.logger.warning(LogCategory.DECISION_FLOW, 
                                  f"Unsupported indicator: {indicator_type.value}")
                return None
                
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, 
                            f"Error calculating {indicator_type.value}",
                            error=str(e))
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int) -> float:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi.iloc[-1])
    
    def _calculate_sma(self, prices: pd.Series, period: int) -> float:
        """Calculate Simple Moving Average"""
        return float(prices.rolling(window=period).mean().iloc[-1])
    
    def _calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calculate Exponential Moving Average"""
        return float(prices.ewm(span=period).mean().iloc[-1])
    
    def _calculate_macd(self, prices: pd.Series, 
                       fast_period: int = 12, slow_period: int = 26,
                       signal_period: int = 9) -> float:
        """Calculate MACD (Moving Average Convergence Divergence)"""
        ema_fast = prices.ewm(span=fast_period).mean()
        ema_slow = prices.ewm(span=slow_period).mean()
        macd_line = ema_fast - ema_slow
        return float(macd_line.iloc[-1])
    
    def _calculate_stochastic_k(self, close: pd.Series, high: pd.Series, 
                               low: pd.Series, period: int) -> float:
        """Calculate Stochastic %K"""
        lowest_low = low.rolling(window=period).min()
        highest_high = high.rolling(window=period).max()
        
        stoch_k = 100 * ((close - lowest_low) / (highest_high - lowest_low))
        return float(stoch_k.iloc[-1])
    
    def _calculate_cci(self, prices: pd.Series, period: int) -> float:
        """Calculate Commodity Channel Index"""
        # Simplified CCI using close prices only
        typical_price = prices  # In full implementation, would use (H+L+C)/3
        sma = typical_price.rolling(window=period).mean()
        mad = typical_price.rolling(window=period).apply(
            lambda x: np.mean(np.abs(x - x.mean()))
        )
        
        cci = (typical_price - sma) / (0.015 * mad)
        return float(cci.iloc[-1])
    
    def _calculate_adx(self, close: pd.Series, high: pd.Series, 
                      low: pd.Series, period: int) -> float:
        """Calculate Average Directional Index (simplified)"""
        # Simplified ADX calculation
        tr = pd.DataFrame({
            'tr1': high - low,
            'tr2': (high - close.shift()).abs(),
            'tr3': (low - close.shift()).abs()
        }).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        
        # Simplified directional movement
        dm_plus = (high.diff().where(high.diff() > low.diff().abs(), 0)).rolling(window=period).mean()
        dm_minus = (low.diff().abs().where(low.diff().abs() > high.diff(), 0)).rolling(window=period).mean()
        
        di_plus = 100 * (dm_plus / atr)
        di_minus = 100 * (dm_minus / atr)
        
        dx = 100 * (di_plus - di_minus).abs() / (di_plus + di_minus)
        adx = dx.rolling(window=period).mean()
        
        return float(adx.iloc[-1])
    
    def _calculate_atr(self, close: pd.Series, high: pd.Series, 
                      low: pd.Series, period: int) -> float:
        """Calculate Average True Range"""
        tr = pd.DataFrame({
            'tr1': high - low,
            'tr2': (high - close.shift()).abs(),
            'tr3': (low - close.shift()).abs()
        }).max(axis=1)
        
        atr = tr.rolling(window=period).mean()
        return float(atr.iloc[-1])
    
    def _calculate_williams_r(self, close: pd.Series, high: pd.Series, 
                             low: pd.Series, period: int) -> float:
        """Calculate Williams %R"""
        highest_high = high.rolling(window=period).max()
        lowest_low = low.rolling(window=period).min()
        
        williams_r = -100 * ((highest_high - close) / (highest_high - lowest_low))
        return float(williams_r.iloc[-1])

# =============================================================================
# MARKET DATA PROVIDER
# =============================================================================

@dataclass
class EnhancedMarketData:
    """Enhanced market data with technical analysis support"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    bid: Optional[float] = None
    ask: Optional[float] = None
    iv_rank: Optional[float] = None
    volatility: Optional[float] = None
    
    # Technical indicators (calculated on demand)
    rsi_14: Optional[float] = None
    sma_20: Optional[float] = None
    sma_50: Optional[float] = None
    ema_12: Optional[float] = None
    ema_26: Optional[float] = None
    macd: Optional[float] = None
    stoch_k: Optional[float] = None
    
    @property
    def price(self) -> float:
        """Current price (close)"""
        return self.close
    
    @property
    def mid_price(self) -> Optional[float]:
        """Mid price between bid/ask"""
        if self.bid and self.ask:
            return (self.bid + self.ask) / 2
        return self.close

class MarketDataProvider:
    """
    Enhanced market data provider with technical indicator support.
    Manages historical data and real-time updates.
    """
    
    def __init__(self, logger: FrameworkLogger):
        self.logger = logger
        self.indicator_engine = TechnicalIndicatorEngine(logger)
        self._price_history: Dict[str, List[EnhancedMarketData]] = {}
        self._current_data: Dict[str, EnhancedMarketData] = {}
        
    def update_market_data(self, symbol: str, data: EnhancedMarketData) -> None:
        """Update market data for a symbol"""
        # Store current data
        self._current_data[symbol] = data
        
        # Add to history
        if symbol not in self._price_history:
            self._price_history[symbol] = []
        
        self._price_history[symbol].append(data)
        
        # Keep only last 200 bars for performance
        if len(self._price_history[symbol]) > 200:
            self._price_history[symbol] = self._price_history[symbol][-200:]
        
        # Calculate technical indicators
        self._calculate_indicators(symbol)
    
    def get_current_data(self, symbol: str) -> Optional[EnhancedMarketData]:
        """Get current market data for symbol"""
        return self._current_data.get(symbol)
    
    def get_price_history(self, symbol: str, bars: int = 50) -> List[float]:
        """Get price history for technical analysis"""
        if symbol not in self._price_history:
            return []
        
        history = self._price_history[symbol]
        return [bar.close for bar in history[-bars:]]
    
    def _calculate_indicators(self, symbol: str) -> None:
        """Calculate technical indicators for symbol"""
        try:
            if symbol not in self._price_history or len(self._price_history[symbol]) < 20:
                return
            
            history = self._price_history[symbol]
            closes = [bar.close for bar in history]
            highs = [bar.high for bar in history]
            lows = [bar.low for bar in history]
            
            current_data = self._current_data[symbol]
            
            # Calculate common indicators
            if len(closes) >= 14:
                current_data.rsi_14 = self.indicator_engine.calculate_indicator(
                    TechnicalIndicator.RSI, closes, 14
                )
            
            if len(closes) >= 20:
                current_data.sma_20 = self.indicator_engine.calculate_indicator(
                    TechnicalIndicator.SMA, closes, 20
                )
            
            if len(closes) >= 50:
                current_data.sma_50 = self.indicator_engine.calculate_indicator(
                    TechnicalIndicator.SMA, closes, 50
                )
            
            if len(closes) >= 12:
                current_data.ema_12 = self.indicator_engine.calculate_indicator(
                    TechnicalIndicator.EMA, closes, 12
                )
                
            if len(closes) >= 26:
                current_data.ema_26 = self.indicator_engine.calculate_indicator(
                    TechnicalIndicator.EMA, closes, 26
                )
                
                current_data.macd = self.indicator_engine.calculate_indicator(
                    TechnicalIndicator.MACD, closes, fast_period=12, slow_period=26
                )
            
            if len(closes) >= 14:
                current_data.stoch_k = self.indicator_engine.calculate_indicator(
                    TechnicalIndicator.STOCH_K, closes, 14,
                    high_data=highs, low_data=lows
                )
            
        except Exception as e:
            self.logger.error(LogCategory.MARKET_DATA, 
                            f"Error calculating indicators for {symbol}",
                            error=str(e))

# =============================================================================
# ENHANCED DECISION EVALUATORS
# =============================================================================

class EnhancedStockDecisionEvaluator:
    """Enhanced stock decision evaluator with full field support"""
    
    def __init__(self, logger: FrameworkLogger, market_data_provider: MarketDataProvider):
        self.logger = logger
        self.market_data_provider = market_data_provider
    
    def evaluate(self, decision_config: Dict[str, Any], 
                context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate enhanced stock decision with full field support"""
        try:
            symbol = decision_config.get('symbol')
            price_field = decision_config.get('price_field', 'last_price')
            comparison = ComparisonOperator(decision_config.get('comparison'))
            value = float(decision_config.get('value'))
            value2 = decision_config.get('value2')
            
            # Get enhanced market data
            market_data = self.market_data_provider.get_current_data(symbol)
            if not market_data:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"No market data available for {symbol}"
                )
            
            # Extract field value with full support
            field_value = self._extract_field_value(market_data, price_field, context)
            if field_value is None:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Field {price_field} not available for {symbol}"
                )
            
            # Evaluate comparison
            if comparison == ComparisonOperator.BETWEEN and value2 is not None:
                result = ComparisonEvaluator.evaluate_comparison(
                    comparison, field_value, value, float(value2)
                )
                comparison_text = f"{field_value} between {value} and {value2}"
            else:
                result = ComparisonEvaluator.evaluate_comparison(
                    comparison, field_value, value
                )
                comparison_text = f"{field_value} {comparison.value} {value}"
            
            reasoning = f"Stock {symbol} {price_field}: {comparison_text} = {result}"
            
            return DetailedDecisionResult(
                DecisionResult.YES if result else DecisionResult.NO,
                confidence=1.0,
                reasoning=reasoning,
                evaluation_data={
                    'symbol': symbol,
                    'price_field': price_field,
                    'field_value': field_value,
                    'comparison': comparison.value,
                    'target_value': value,
                    'target_value2': value2
                }
            )
            
        except Exception as e:
            error_msg = f"Enhanced stock decision failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg)
            return DetailedDecisionResult(DecisionResult.ERROR, reasoning=error_msg)
    
    def _extract_field_value(self, market_data: EnhancedMarketData, 
                           field: str, context: DecisionContext) -> Optional[float]:
        """Extract field value with comprehensive support"""
        
        # Price fields
        if field in ['last_price', 'close_price']:
            return market_data.close
        elif field == 'open_price':
            return market_data.open
        elif field == 'high_price':
            return market_data.high
        elif field == 'low_price':
            return market_data.low
        elif field == 'bid_price':
            return market_data.bid or market_data.close
        elif field == 'ask_price':
            return market_data.ask or market_data.close
        elif field == 'mid_price':
            return market_data.mid_price
        elif field == 'volume':
            return float(market_data.volume)
        elif field == 'iv_rank':
            return market_data.iv_rank
        
        # Price change calculations
        elif field == 'change':
            history = self.market_data_provider.get_price_history(market_data.symbol, 2)
            if len(history) >= 2:
                return history[-1] - history[-2]
            return 0.0
        elif field == 'change_percent':
            history = self.market_data_provider.get_price_history(market_data.symbol, 2)
            if len(history) >= 2 and history[-2] != 0:
                return ((history[-1] - history[-2]) / history[-2]) * 100
            return 0.0
        
        # Technical indicators
        elif field == 'rsi':
            return market_data.rsi_14
        elif field == 'sma_20':
            return market_data.sma_20
        elif field == 'sma_50':
            return market_data.sma_50
        elif field == 'ema_12':
            return market_data.ema_12
        elif field == 'macd':
            return market_data.macd
        elif field == 'stoch_k':
            return market_data.stoch_k
        
        # Advanced calculations
        elif field == 'volatility_ratio':
            # Ratio of current IV to historical volatility
            if market_data.volatility and market_data.iv_rank:
                return market_data.volatility / (market_data.iv_rank / 100)
            return None
        
        else:
            self.logger.warning(LogCategory.DECISION_FLOW, 
                              f"Unknown stock field: {field}")
            return None

# =============================================================================
# ENHANCED DECISION ENGINE
# =============================================================================

class EnhancedDecisionEngine:
    """
    Phase 2 Enhanced Decision Engine with full Option Alpha support.
    Features comprehensive decision evaluation, caching, and optimization.
    """
    
    def __init__(self, logger: FrameworkLogger, state_manager):
        self.logger = logger
        self.state_manager = state_manager
        
        # Initialize market data provider
        self.market_data_provider = MarketDataProvider(logger)
        
        # Initialize enhanced evaluators
        self.stock_evaluator = EnhancedStockDecisionEvaluator(logger, self.market_data_provider)
        
        # Decision cache for performance
        self._decision_cache: Dict[str, Tuple[DetailedDecisionResult, datetime]] = {}
        self._cache_ttl_seconds = 60  # 1 minute cache
        
        # Performance tracking
        self._evaluation_count = 0
        self._cache_hits = 0
        
        # Thread pool for parallel evaluation
        self._thread_pool = ThreadPoolExecutor(max_workers=4)
        
        self.logger.info(LogCategory.SYSTEM, "Enhanced Decision Engine initialized")
    
    def update_market_data(self, symbol: str, data: EnhancedMarketData) -> None:
        """Update market data for decision evaluation"""
        self.market_data_provider.update_market_data(symbol, data)
        
        # Clear cache for affected symbol
        self._clear_symbol_cache(symbol)
    
    def evaluate_decision(self, decision_config: Dict[str, Any], 
                         context: Optional[DecisionContext] = None) -> DetailedDecisionResult:
        """
        Evaluate decision with enhanced capabilities and caching.
        
        Args:
            decision_config: Decision configuration
            context: Decision context (created if None)
            
        Returns:
            DetailedDecisionResult with comprehensive evaluation
        """
        try:
            self._evaluation_count += 1
            
            # Generate cache key
            cache_key = self._generate_cache_key(decision_config, context)
            
            # Check cache first
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self._cache_hits += 1
                self.logger.debug(LogCategory.DECISION_FLOW, "Using cached decision result")
                return cached_result
            
            # Create context if needed
            if context is None:
                context = self._create_enhanced_context()
            
            # Handle grouped decisions
            if 'logic_operator' in decision_config:
                result = self._evaluate_grouped_decision(decision_config, context)
            else:
                result = self._evaluate_single_decision(decision_config, context)
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Log evaluation
            self.logger.debug(LogCategory.DECISION_FLOW, "Decision evaluated",
                            recipe_type=decision_config.get('recipe_type'),
                            result=result.result.value,
                            confidence=result.confidence)
            
            return result
            
        except Exception as e:
            error_msg = f"Enhanced decision evaluation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg)
            return DetailedDecisionResult(DecisionResult.ERROR, reasoning=error_msg)
    
    def _evaluate_single_decision(self, decision_config: Dict[str, Any], 
                                 context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate single decision with enhanced evaluators"""
        recipe_type = decision_config.get('recipe_type')
        
        if recipe_type == 'stock':
            return self.stock_evaluator.evaluate(decision_config, context)
        elif recipe_type == 'indicator':
            return self._evaluate_indicator_decision(decision_config, context)
        elif recipe_type == 'position':
            return self._evaluate_position_decision(decision_config, context)
        elif recipe_type == 'bot':
            return self._evaluate_bot_decision(decision_config, context)
        elif recipe_type == 'general':
            return self._evaluate_general_decision(decision_config, context)
        else:
            return DetailedDecisionResult(
                DecisionResult.ERROR,
                reasoning=f"Unknown recipe type: {recipe_type}"
            )
    
    def _evaluate_indicator_decision(self, decision_config: Dict[str, Any], 
                                   context: DecisionContext) -> DetailedDecisionResult:
        """Enhanced indicator decision evaluation"""
        try:
            symbol = decision_config.get('symbol')
            indicator_name = decision_config.get('indicator')
            period = decision_config.get('indicator_period', 14)
            
            # Get market data
            market_data = self.market_data_provider.get_current_data(symbol)
            if not market_data:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"No market data for {symbol}"
                )
            
            # Get indicator value
            try:
                indicator_type = TechnicalIndicator(indicator_name)
            except ValueError:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Unknown indicator: {indicator_name}"
                )
            
            # Get pre-calculated indicator or calculate on demand
            indicator_value = self._get_indicator_value(market_data, indicator_type, period)
            
            if indicator_value is None:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Could not calculate {indicator_name} for {symbol}"
                )
            
            # Evaluate comparison
            if 'indicator_signal' in decision_config:
                # Signal-based evaluation
                target_signal = decision_config['indicator_signal']
                current_signal = self._get_indicator_signal(indicator_type, indicator_value)
                result = current_signal == target_signal
                reasoning = f"{symbol} {indicator_name} signal: {current_signal} (target: {target_signal})"
            else:
                # Numeric comparison
                comparison = ComparisonOperator(decision_config.get('comparison'))
                target_value = float(decision_config.get('value'))
                target_value2 = decision_config.get('value2')
                
                if comparison == ComparisonOperator.BETWEEN and target_value2:
                    result = ComparisonEvaluator.evaluate_comparison(
                        comparison, indicator_value, target_value, float(target_value2)
                    )
                    reasoning = f"{symbol} {indicator_name}({period}) = {indicator_value:.2f} between {target_value} and {target_value2}"
                else:
                    result = ComparisonEvaluator.evaluate_comparison(
                        comparison, indicator_value, target_value
                    )
                    reasoning = f"{symbol} {indicator_name}({period}) = {indicator_value:.2f} {comparison.value} {target_value}"
            
            return DetailedDecisionResult(
                DecisionResult.YES if result else DecisionResult.NO,
                confidence=0.9,  # High confidence for technical indicators
                reasoning=reasoning,
                evaluation_data={
                    'symbol': symbol,
                    'indicator': indicator_name,
                    'period': period,
                    'indicator_value': indicator_value
                }
            )
            
        except Exception as e:
            error_msg = f"Indicator decision failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg)
            return DetailedDecisionResult(DecisionResult.ERROR, reasoning=error_msg)
    
    def _get_indicator_signal(self, indicator_type: TechnicalIndicator, 
                             value: float) -> str:
        """Convert indicator value to buy/sell/neutral signal"""
        if indicator_type == TechnicalIndicator.RSI:
            if value < 30:
                return 'buy'  # Oversold
            elif value > 70:
                return 'sell'  # Overbought
            else:
                return 'neutral'
        elif indicator_type == TechnicalIndicator.STOCH_K:
            if value < 20:
                return 'buy'  # Oversold
            elif value > 80:
                return 'sell'  # Overbought
            else:
                return 'neutral'
        elif indicator_type == TechnicalIndicator.CCI:
            if value < -100:
                return 'buy'  # Oversold
            elif value > 100:
                return 'sell'  # Overbought
            else:
                return 'neutral'
        elif indicator_type == TechnicalIndicator.WILLIAMS_R:
            if value < -80:
                return 'buy'  # Oversold
            elif value > -20:
                return 'sell'  # Overbought
            else:
                return 'neutral'
        else:
            return 'neutral'
    
    def _evaluate_position_decision(self, decision_config: Dict[str, Any], 
                                  context: DecisionContext) -> DetailedDecisionResult:
        """Enhanced position decision evaluation"""
        try:
            position_ref = decision_config.get('position_reference', 'current')
            position_field = decision_config.get('position_field')
            
            # Get position
            if position_ref == 'current':
                positions = context.get_open_positions()
                if not positions:
                    return DetailedDecisionResult(
                        DecisionResult.NO,
                        reasoning="No open positions to evaluate"
                    )
                position = positions[-1]  # Most recent
            else:
                position = next((p for p in context.positions if p.id == position_ref), None)
                if not position:
                    return DetailedDecisionResult(
                        DecisionResult.ERROR,
                        reasoning=f"Position {position_ref} not found"
                    )
            
            # Extract field value
            field_value = self._extract_position_field(position, position_field)
            if field_value is None:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Cannot extract field {position_field}"
                )
            
            # Evaluate comparison
            comparison = ComparisonOperator(decision_config.get('comparison'))
            target_value = float(decision_config.get('value'))
            target_value2 = decision_config.get('value2')
            
            if comparison == ComparisonOperator.BETWEEN and target_value2:
                result = ComparisonEvaluator.evaluate_comparison(
                    comparison, field_value, target_value, float(target_value2)
                )
                reasoning = f"Position {position.symbol} {position_field} ({field_value}) between {target_value} and {target_value2}"
            else:
                result = ComparisonEvaluator.evaluate_comparison(
                    comparison, field_value, target_value
                )
                reasoning = f"Position {position.symbol} {position_field} ({field_value}) {comparison.value} {target_value}"
            
            return DetailedDecisionResult(
                DecisionResult.YES if result else DecisionResult.NO,
                confidence=0.95,
                reasoning=reasoning,
                evaluation_data={
                    'position_id': position.id,
                    'symbol': position.symbol,
                    'field': position_field,
                    'field_value': field_value
                }
            )
            
        except Exception as e:
            error_msg = f"Position decision failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg)
            return DetailedDecisionResult(DecisionResult.ERROR, reasoning=error_msg)
    
    def _extract_position_field(self, position: Position, field: str) -> Optional[float]:
        """Extract position field value with comprehensive support"""
        
        # Basic P&L fields
        if field == 'unrealized_pnl':
            return position.unrealized_pnl
        elif field == 'realized_pnl':
            return position.realized_pnl
        elif field == 'total_pnl':
            return position.total_pnl
        elif field == 'return_percent':
            return position.return_percentage
        
        # Position details
        elif field == 'quantity':
            return float(position.quantity)
        elif field == 'entry_price':
            return position.entry_price
        elif field == 'current_price':
            return position.current_price
        elif field == 'days_open':
            return float(position.days_open)
        
        # Advanced calculations
        elif field == 'pl_per_contract':
            if position.quantity != 0:
                return position.total_pnl / abs(position.quantity)
            return 0.0
        elif field == 'return_on_risk_percent':
            # Return on risk calculation
            risk = position.entry_price * abs(position.quantity)
            if risk > 0:
                return (position.total_pnl / risk) * 100
            return 0.0
        
        # Greeks (for options positions)
        elif field == 'delta':
            return position.portfolio_delta
        elif field == 'gamma':
            return position.portfolio_gamma
        elif field == 'theta':
            return position.portfolio_theta
        elif field == 'vega':
            return position.portfolio_vega
        
        # Risk metrics
        elif field == 'max_risk':
            # Maximum possible loss
            if hasattr(position, 'legs') and position.legs:
                # Multi-leg position risk calculation
                max_loss = 0.0
                for leg in position.legs:
                    if leg.side == 'long':
                        max_loss += leg.entry_price * leg.quantity * 100
                return max_loss
            else:
                # Simple position
                return position.entry_price * abs(position.quantity)
        
        else:
            self.logger.warning(LogCategory.DECISION_FLOW, 
                              f"Unknown position field: {field}")
            return None
    
    def _evaluate_bot_decision(self, decision_config: Dict[str, Any], 
                             context: DecisionContext) -> DetailedDecisionResult:
        """Enhanced bot decision evaluation"""
        try:
            bot_field = decision_config.get('bot_field', 'open_positions')
            comparison = ComparisonOperator(decision_config.get('comparison'))
            target_value = float(decision_config.get('value'))
            target_value2 = decision_config.get('value2')
            
            # Extract bot field value
            field_value = self._extract_bot_field(context, bot_field)
            if field_value is None:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Cannot extract bot field: {bot_field}"
                )
            
            # Evaluate comparison
            if comparison == ComparisonOperator.BETWEEN and target_value2:
                result = ComparisonEvaluator.evaluate_comparison(
                    comparison, field_value, target_value, float(target_value2)
                )
                reasoning = f"Bot {bot_field} ({field_value}) between {target_value} and {target_value2}"
            else:
                result = ComparisonEvaluator.evaluate_comparison(
                    comparison, field_value, target_value
                )
                reasoning = f"Bot {bot_field} ({field_value}) {comparison.value} {target_value}"
            
            return DetailedDecisionResult(
                DecisionResult.YES if result else DecisionResult.NO,
                confidence=1.0,
                reasoning=reasoning,
                evaluation_data={
                    'bot_field': bot_field,
                    'field_value': field_value,
                    'target_value': target_value
                }
            )
            
        except Exception as e:
            error_msg = f"Bot decision failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg)
            return DetailedDecisionResult(DecisionResult.ERROR, reasoning=error_msg)
    
    def _extract_bot_field(self, context: DecisionContext, field: str) -> Optional[float]:
        """Extract bot-level metrics with comprehensive support"""
        
        if field == 'open_positions':
            return float(len(context.get_open_positions()))
        elif field == 'total_positions':
            return float(len(context.positions))
        elif field == 'total_pnl':
            return sum(p.total_pnl for p in context.positions)
        elif field == 'unrealized_pnl':
            return sum(p.unrealized_pnl for p in context.get_open_positions())
        elif field == 'realized_pnl':
            closed_positions = [p for p in context.positions if p.state == 'closed']
            return sum(p.realized_pnl for p in closed_positions)
        elif field == 'day_pnl':
            # P&L for positions opened today
            today = datetime.now().date()
            today_positions = [p for p in context.positions 
                             if p.opened_at.date() == today]
            return sum(p.total_pnl for p in today_positions)
        elif field == 'available_capital':
            return float(context.bot_stats.get('available_capital', 0))
        elif field == 'capital_used':
            # Calculate capital currently used
            open_positions = context.get_open_positions()
            return sum(p.entry_price * abs(p.quantity) for p in open_positions)
        elif field == 'win_rate':
            # Calculate win rate from closed positions
            closed_positions = [p for p in context.positions if p.state == 'closed']
            if closed_positions:
                winning_positions = [p for p in closed_positions if p.realized_pnl > 0]
                return (len(winning_positions) / len(closed_positions)) * 100
            return 0.0
        else:
            # Try to get from bot_stats directly
            value = context.bot_stats.get(field)
            return float(value) if value is not None else None
    
    def _evaluate_general_decision(self, decision_config: Dict[str, Any], 
                                 context: DecisionContext) -> DetailedDecisionResult:
        """Enhanced general decision evaluation"""
        try:
            condition_type = decision_config.get('condition_type', 'market_time')
            comparison = ComparisonOperator(decision_config.get('comparison'))
            value = decision_config.get('value')
            value2 = decision_config.get('value2')
            
            if condition_type == 'market_time':
                current_value = self._get_market_time_value()
                target_value = self._parse_time_value(value)
                comparison_text = f"Market time {current_value:.2f} {comparison.value} {target_value:.2f}"
                
            elif condition_type == 'vix_level':
                vix_data = self.market_data_provider.get_current_data('VIX')
                if not vix_data:
                    return DetailedDecisionResult(
                        DecisionResult.ERROR,
                        reasoning="VIX data not available"
                    )
                current_value = vix_data.close
                target_value = float(value)
                comparison_text = f"VIX {current_value:.2f} {comparison.value} {target_value}"
                
            elif condition_type == 'day_of_week':
                current_value = float(datetime.now().weekday())  # 0=Monday
                target_value = self._parse_day_of_week(value)
                comparison_text = f"Day of week {current_value} {comparison.value} {target_value}"
                
            elif condition_type == 'market_regime':
                # Market regime detection
                current_value = self._detect_market_regime()
                target_value = float(value)
                comparison_text = f"Market regime {current_value} {comparison.value} {target_value}"
                
            elif condition_type == 'volatility_environment':
                # Volatility environment detection
                current_value = self._detect_volatility_environment()
                target_value = float(value)
                comparison_text = f"Volatility environment {current_value} {comparison.value} {target_value}"
                
            else:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Unknown condition type: {condition_type}"
                )
            
            # Evaluate comparison
            if comparison == ComparisonOperator.BETWEEN and value2:
                result = ComparisonEvaluator.evaluate_comparison(
                    comparison, current_value, target_value, float(value2)
                )
            else:
                result = ComparisonEvaluator.evaluate_comparison(
                    comparison, current_value, target_value
                )
            
            return DetailedDecisionResult(
                DecisionResult.YES if result else DecisionResult.NO,
                confidence=1.0,
                reasoning=comparison_text,
                evaluation_data={
                    'condition_type': condition_type,
                    'current_value': current_value,
                    'target_value': target_value
                }
            )
            
        except Exception as e:
            error_msg = f"General decision failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg)
            return DetailedDecisionResult(DecisionResult.ERROR, reasoning=error_msg)
    
    def _detect_market_regime(self) -> float:
        """Detect current market regime using technical analysis"""
        try:
            spy_data = self.market_data_provider.get_current_data('SPY')
            if not spy_data or not spy_data.sma_20 or not spy_data.sma_50:
                return 0.0  # Neutral
            
            # Simple regime detection based on moving averages
            if spy_data.close > spy_data.sma_20 > spy_data.sma_50:
                return 1.0  # Bull market
            elif spy_data.close < spy_data.sma_20 < spy_data.sma_50:
                return -1.0  # Bear market
            else:
                return 0.0  # Sideways/Neutral
                
        except Exception:
            return 0.0
    
    def _detect_volatility_environment(self) -> float:
        """Detect volatility environment using VIX"""
        try:
            vix_data = self.market_data_provider.get_current_data('VIX')
            if not vix_data:
                return 0.0
            
            vix_level = vix_data.close
            
            if vix_level < 15:
                return 1.0  # Low volatility
            elif vix_level > 25:
                return 3.0  # High volatility
            else:
                return 2.0  # Normal volatility
                
        except Exception:
            return 0.0
    
    def _get_market_time_value(self) -> float:
        """Get current market time as decimal hours"""
        now = datetime.now()
        return now.hour + (now.minute / 60.0)
    
    def _parse_time_value(self, time_str: str) -> float:
        """Parse time string to decimal hours"""
        if isinstance(time_str, (int, float)):
            return float(time_str)
        
        time_str = str(time_str).replace(':', '')
        if len(time_str) == 4:
            hours = int(time_str[:2])
            minutes = int(time_str[2:])
            return hours + (minutes / 60.0)
        return float(time_str)
    
    def _parse_day_of_week(self, day_str: str) -> float:
        """Parse day of week to number"""
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2,
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        return float(day_map.get(str(day_str).lower(), 0))
    
    def _evaluate_grouped_decision(self, decision_config: Dict[str, Any], 
                                 context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate grouped decisions with AND/OR logic"""
        try:
            logic_operator = decision_config.get('logic_operator', 'and')
            grouped_decisions = decision_config.get('grouped_decisions', [])
            
            if not grouped_decisions:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning="No grouped decisions provided"
                )
            
            # Evaluate sub-decisions (potentially in parallel)
            if len(grouped_decisions) > 1 and self._thread_pool:
                # Parallel evaluation for performance
                futures = []
                for sub_decision in grouped_decisions:
                    future = self._thread_pool.submit(
                        self._evaluate_single_decision, sub_decision, context
                    )
                    futures.append(future)
                
                results = []
                for future in futures:
                    try:
                        result = future.result(timeout=5)  # 5 second timeout
                        results.append(result)
                    except Exception as e:
                        self.logger.error(LogCategory.DECISION_FLOW, 
                                        "Parallel decision evaluation failed", error=str(e))
                        results.append(DetailedDecisionResult(
                            DecisionResult.ERROR, 
                            reasoning=f"Parallel evaluation failed: {str(e)}"
                        ))
            else:
                # Sequential evaluation
                results = []
                for sub_decision in grouped_decisions:
                    result = self._evaluate_single_decision(sub_decision, context)
                    results.append(result)
            
            # Check for errors
            error_results = [r for r in results if r.result == DecisionResult.ERROR]
            if error_results:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Sub-decision errors: {[r.reasoning for r in error_results]}"
                )
            
            # Apply logic operator
            if logic_operator.lower() == 'and':
                final_result = all(r.result == DecisionResult.YES for r in results)
                operator_desc = "AND"
            elif logic_operator.lower() == 'or':
                final_result = any(r.result == DecisionResult.YES for r in results)
                operator_desc = "OR"
            else:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Unknown logic operator: {logic_operator}"
                )
            
            # Build comprehensive reasoning
            reasoning_parts = [f"({i+1}) {r.reasoning}" for i, r in enumerate(results)]
            reasoning = f"Grouped ({operator_desc}): " + f" {operator_desc} ".join(reasoning_parts)
            
            # Calculate confidence (weighted average)
            confidence = sum(r.confidence for r in results) / len(results)
            
            return DetailedDecisionResult(
                DecisionResult.YES if final_result else DecisionResult.NO,
                confidence=confidence,
                reasoning=reasoning,
                evaluation_data={
                    'logic_operator': logic_operator,
                    'sub_decisions_count': len(results),
                    'sub_results': [r.result.value for r in results],
                    'sub_confidences': [r.confidence for r in results]
                }
            )
            
        except Exception as e:
            error_msg = f"Grouped decision evaluation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg)
            return DetailedDecisionResult(DecisionResult.ERROR, reasoning=error_msg)
    
    # =============================================================================
    # CACHING AND OPTIMIZATION
    # =============================================================================
    
    def _generate_cache_key(self, decision_config: Dict[str, Any], 
                          context: Optional[DecisionContext]) -> str:
        """Generate cache key for decision"""
        key_elements = {
            'config': decision_config,
            'timestamp_minute': datetime.now().strftime('%Y%m%d_%H%M'),
            'positions_count': len(context.positions) if context else 0
        }
        
        key_str = json.dumps(key_elements, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[DetailedDecisionResult]:
        """Get cached decision result if valid"""
        if cache_key in self._decision_cache:
            result, cached_time = self._decision_cache[cache_key]
            
            # Check if cache is still valid
            age_seconds = (datetime.now() - cached_time).total_seconds()
            if age_seconds < self._cache_ttl_seconds:
                return result
            else:
                # Remove expired cache entry
                del self._decision_cache[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: DetailedDecisionResult) -> None:
        """Cache decision result"""
        self._decision_cache[cache_key] = (result, datetime.now())
        
        # Clean up old cache entries periodically
        if len(self._decision_cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self) -> None:
        """Remove expired cache entries"""
        current_time = datetime.now()
        expired_keys = []
        
        for key, (result, cached_time) in self._decision_cache.items():
            age_seconds = (current_time - cached_time).total_seconds()
            if age_seconds > self._cache_ttl_seconds:
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._decision_cache[key]
        
        self.logger.debug(LogCategory.DECISION_FLOW, "Cache cleanup completed",
                        removed_entries=len(expired_keys))
    
    def _clear_symbol_cache(self, symbol: str) -> None:
        """Clear cache entries related to a specific symbol"""
        keys_to_remove = []
        
        for key in self._decision_cache:
            # Simple check if symbol is in the cache key
            if symbol in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._decision_cache[key]
    
    def _create_enhanced_context(self) -> DecisionContext:
        """Create enhanced decision context with current state"""
        try:
            # Get positions from state manager
            positions = self.state_manager.get_positions()
            
            # Create market data dictionary
            market_data = {}
            for symbol in ['SPY', 'QQQ', 'IWM', 'VIX']:
                data = self.market_data_provider.get_current_data(symbol)
                if data:
                    # Convert to basic MarketData for compatibility
                    market_data[symbol] = MarketData(
                        symbol=symbol,
                        timestamp=data.timestamp,
                        price=data.close,
                        bid=data.bid,
                        ask=data.ask,
                        volume=data.volume,
                        iv_rank=data.iv_rank
                    )
            
            # Bot statistics
            open_positions = [p for p in positions if p.state == 'open']
            bot_stats = {
                'total_positions': len(positions),
                'open_positions': len(open_positions),
                'total_pnl': sum(p.total_pnl for p in positions),
                'available_capital': 100000  # Default available capital
            }
            
            return DecisionContext(
                timestamp=datetime.now(),
                market_data=market_data,
                positions=positions,
                bot_stats=bot_stats,
                market_state={
                    'regime': self._detect_market_regime(),
                    'volatility': self._detect_volatility_environment()
                }
            )
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, "Failed to create enhanced context",
                            error=str(e))
            # Return minimal context
            return DecisionContext(
                timestamp=datetime.now(),
                market_data={},
                positions=[],
                bot_stats={},
                market_state={}
            )
    
    # =============================================================================
    # PERFORMANCE AND ANALYTICS
    # =============================================================================
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get decision engine performance statistics"""
        cache_hit_rate = (self._cache_hits / self._evaluation_count * 100) if self._evaluation_count > 0 else 0
        
        return {
            'total_evaluations': self._evaluation_count,
            'cache_hits': self._cache_hits,
            'cache_hit_rate': cache_hit_rate,
            'cache_size': len(self._decision_cache),
            'cache_ttl_seconds': self._cache_ttl_seconds
        }
    
    def clear_cache(self) -> None:
        """Clear all cached decision results"""
        self._decision_cache.clear()
        self.logger.info(LogCategory.DECISION_FLOW, "Decision cache cleared")
    
    def shutdown(self) -> None:
        """Shutdown decision engine and cleanup resources"""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
        self.clear_cache()
        self.logger.info(LogCategory.SYSTEM, "Enhanced Decision Engine shutdown completed")

# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_enhanced_decision_engine(logger: FrameworkLogger, state_manager) -> EnhancedDecisionEngine:
    """Factory function to create enhanced decision engine"""
    return EnhancedDecisionEngine(logger, state_manager)_indicator_value(self, market_data: EnhancedMarketData, 
                           indicator_type: TechnicalIndicator, period: int) -> Optional[float]:
        """Get indicator value (pre-calculated or on-demand)"""
        
        # Check for pre-calculated values
        if indicator_type == TechnicalIndicator.RSI and period == 14:
            return market_data.rsi_14
        elif indicator_type == TechnicalIndicator.SMA and period == 20:
            return market_data.sma_20
        elif indicator_type == TechnicalIndicator.SMA and period == 50:
            return market_data.sma_50
        elif indicator_type == TechnicalIndicator.EMA and period == 12:
            return market_data.ema_12
        elif indicator_type == TechnicalIndicator.EMA and period == 26:
            return market_data.ema_26
        elif indicator_type == TechnicalIndicator.MACD:
            return market_data.macd
        elif indicator_type == TechnicalIndicator.STOCH_K:
            return market_data.stoch_k
        
        # Calculate on demand
        price_history = self.market_data_provider.get_price_history(market_data.symbol, period + 10)
        if len(price_history) < period:
            return None
            
        return self.market_data_provider.indicator_engine.calculate_indicator(
            indicator_type, price_history, period
        )
    
    def _get