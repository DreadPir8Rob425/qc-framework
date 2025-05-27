# Option Alpha Framework - Decision Evaluators
# Individual evaluator classes for each decision recipe type

from datetime import datetime
from typing import Dict, List, Any, Optional, Union, Sequence
import random
from oa_framework_enums import (
    DecisionResult, ComparisonOperator, TechnicalIndicator, LogCategory
)
from oa_logging import FrameworkLogger
from oa_data_structures import MarketData, Position
from decision_core import (
    DecisionContext, DetailedDecisionResult, ComparisonEvaluator, 
    BaseDecisionEvaluator
)

# =============================================================================
# TECHNICAL INDICATOR CALCULATOR
# =============================================================================

class TechnicalIndicatorCalculator:
    """Calculator for technical indicators used in decisions"""
    
    
    @staticmethod
    def calculate_sma(prices: Sequence[Union[int, float]], period: int) -> Optional[float]:
        """Calculate Simple Moving Average"""
        if len(prices) < period:
            raise ValueError(f"Not enough data points. Need {period}, got {len(prices)}")
        
        recent_prices = prices[-period:]
        return sum(float(price) for price in recent_prices) / period

    @staticmethod
    def calculate_rsi(prices: Sequence[Union[int, float]], period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index"""
        if len(prices) < period + 1:
            raise ValueError(f"Not enough data points. Need {period + 1}, got {len(prices)}")
        
        # Calculate price changes
        changes = [float(prices[i]) - float(prices[i-1]) for i in range(1, len(prices))]
        
        # Separate gains and losses
        gains = [change if change > 0 else 0 for change in changes]
        losses = [-change if change < 0 else 0 for change in changes]
        
        # Calculate average gains and losses
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        # Calculate RSI
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_ema(prices: Sequence[Union[int, float]], period: int) -> Optional[float]:
        """Calculate Exponential Moving Average"""
        if len(prices) < period:
            return None
        
        multiplier = 2 / (period + 1)
        ema = prices[0]
        
        for price in prices[1:]:
            ema = (price * multiplier) + (ema * (1 - multiplier))
        
        return ema
    
    @staticmethod
    def get_indicator_signal(indicator_value: float, indicator_type: TechnicalIndicator) -> str:
        """Get buy/sell/neutral signal from indicator value"""
        if indicator_type == TechnicalIndicator.RSI:
            if indicator_value < 30:
                return 'buy'  # Oversold
            elif indicator_value > 70:
                return 'sell'  # Overbought
            else:
                return 'neutral'
        
        return 'neutral'  # Default for unimplemented indicators

# =============================================================================
# STOCK DECISION EVALUATOR
# =============================================================================

class StockDecisionEvaluator(BaseDecisionEvaluator):
    """Evaluator for stock-based decisions"""
    
    def evaluate(self, decision_config: Dict[str, Any], context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate stock-based decision"""
        try:
            # Extract required configuration values
            symbol = self._extract_config_value(decision_config, 'symbol')
            price_field = self._extract_config_value(decision_config, 'price_field', default='last_price')
            comparison = ComparisonOperator(self._extract_config_value(decision_config, 'comparison'))
            value = float(self._extract_config_value(decision_config, 'value'))
            
            # Validate symbol has market data
            market_data = self._validate_symbol_data(symbol, context)
            
            # Extract price value from market data
            price_value = self._extract_price_field(price_field, market_data)
            
            if price_value is None:
                return self._create_error_result(
                    f"Price field '{price_field}' is not available for symbol {symbol}"
                )
                
            # Handle BETWEEN comparison that requires value2
            if comparison == ComparisonOperator.BETWEEN:
                value2 = self._extract_config_value(decision_config, 'value2', required=True)
                if value2 is None:
                    return self._create_error_result("BETWEEN comparison requires 'value2' parameter")
                value2 = float(value2)
                result = ComparisonEvaluator.evaluate_comparison(comparison, price_value, value, value2)
                comparison_text = f"{price_value} between {value} and {value2}"
            else:
                result = ComparisonEvaluator.evaluate_comparison(comparison, price_value, value)
                comparison_text = ComparisonEvaluator.compare_to_string(comparison, price_value, value)
            
            # Create reasoning text
            reasoning = f"Stock {symbol} {price_field}: {comparison_text} = {result}"
            
            # Log the decision
            self.logger.debug(LogCategory.DECISION_FLOW, reasoning, 
                            symbol=symbol, price_value=price_value, result=result)
            
            # Return success result
            return self._create_success_result(
                result=result,
                reasoning=reasoning,
                evaluation_data={
                    'symbol': symbol,
                    'price_field': price_field,
                    'price_value': price_value,
                    'comparison': comparison.value,
                    'target_value': value,
                    'comparison_text': comparison_text
                }
            )
            
        except Exception as e:
            # Always return an error result instead of letting exceptions propagate
            error_msg = f"Stock decision evaluation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg, 
                            config=decision_config, error=str(e))
            return self._create_error_result(error_msg)
    
    def _extract_price_field(self, field: str, market_data: MarketData) -> Optional[float]:
        """Extract specific price field from market data"""
        field_mapping = {
            'last_price': market_data.price,
            'bid_price': market_data.bid,
            'ask_price': market_data.ask,
            'mid_price': market_data.mid_price,
            'volume': market_data.volume,
            'iv_rank': market_data.iv_rank
        }
        
        return field_mapping.get(field, market_data.price)

# =============================================================================
# INDICATOR DECISION EVALUATOR
# =============================================================================

class IndicatorDecisionEvaluator(BaseDecisionEvaluator):
    """Evaluator for technical indicator decisions"""
    
    def __init__(self, logger: FrameworkLogger):
        super().__init__(logger)
        self.calculator = TechnicalIndicatorCalculator()
    
    def evaluate(self, decision_config: Dict[str, Any], context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate indicator-based decision"""
        try:
            symbol = self._extract_config_value(decision_config, 'symbol')
            indicator_type = TechnicalIndicator(decision_config.get('indicator'))
            period = decision_config.get('indicator_period', 14)
            
            market_data = self._validate_symbol_data(symbol, context)
            
            # Get historical prices (simulated for demo)
            if not market_data is None:
                historical_prices = self._get_simulated_price_history(market_data.price, period + 5)
            
            # Calculate indicator value
            indicator_value = self._calculate_indicator(indicator_type, historical_prices, period)
            
            if indicator_value is None:
                return self._create_error_result(f"Cannot calculate {indicator_type.value}")
            
            # Check comparison type
            if 'indicator_signal' in decision_config:
                # Signal-based comparison
                target_signal = decision_config['indicator_signal']
                current_signal = self.calculator.get_indicator_signal(indicator_value, indicator_type)
                
                result = current_signal == target_signal
                reasoning = f"{symbol} {indicator_type.value} signal: {current_signal} (target: {target_signal})"
            
            else:
                # Numeric comparison
                comparison = ComparisonOperator(decision_config.get('comparison'))
                target_value = decision_config.get('value')
                target_value2 = decision_config.get('value2')
                
                if target_value is None:
                    return self._create_error_result("Comparison requires 'value' parameter")
                
                
                result = ComparisonEvaluator.evaluate_comparison(
                    comparison, indicator_value, target_value, target_value2
                )
                
                reasoning = f"{symbol} {indicator_type.value} = {indicator_value:.2f} {comparison.value} {target_value}"
            
            self.logger.debug(LogCategory.DECISION_FLOW, "Indicator decision evaluated",
                            symbol=symbol, indicator=indicator_type.value, result=result)
            
            return self._create_success_result(
                result, reasoning, 0.85,
                {
                    'symbol': symbol,
                    'indicator': indicator_type.value,
                    'indicator_value': indicator_value,
                    'period': period
                }
            )
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, "Indicator decision failed", error=str(e))
            return self._create_error_result(f"Indicator decision error: {str(e)}")
    
    def _get_simulated_price_history(self, current_price: float, length: int) -> List[float]:
        """Generate simulated price history for demonstration"""
        prices = []
        price = current_price * 0.98  # Start slightly below current
        
        for _ in range(length):
            change_percent = random.uniform(-0.02, 0.025)
            price *= (1 + change_percent)
            prices.append(price)
        
        return prices
    
    def _calculate_indicator(self, indicator_type: TechnicalIndicator, 
                           prices: List[float], period: int) -> Optional[float]:
        """Calculate specific technical indicator"""
        if indicator_type == TechnicalIndicator.RSI:
            return self.calculator.calculate_rsi(prices, period)
        elif indicator_type == TechnicalIndicator.SMA:
            return self.calculator.calculate_sma(prices, period)
        elif indicator_type == TechnicalIndicator.EMA:
            return self.calculator.calculate_ema(prices, period)
        
        self.logger.warning(LogCategory.DECISION_FLOW, "Unsupported indicator",
                          indicator=indicator_type.value)
        return None

# =============================================================================
# POSITION DECISION EVALUATOR
# =============================================================================

class PositionDecisionEvaluator(BaseDecisionEvaluator):
    """Evaluator for position-based decisions"""
    
    def evaluate(self, decision_config: Dict[str, Any], context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate position-based decision"""
        try:
            position_ref = decision_config.get('position_reference', 'current')
            position_field = self._extract_config_value(decision_config, 'position_field')
            
            # Get relevant position
            if position_ref == 'current':
                positions = context.get_open_positions()
                if not positions:
                    return self._create_success_result(False, "No open positions to evaluate")
                position = positions[-1]  # Most recent
            else:
                position = next((p for p in context.positions if p.id == position_ref), None)
                if not position:
                    return self._create_error_result(f"Position {position_ref} not found")
            
            # Extract field value
            field_value = self._extract_position_field(position, position_field)
            if field_value is None:
                return self._create_error_result(f"Cannot extract {position_field}")
            
            # Evaluate comparison
            comparison = ComparisonOperator(decision_config.get('comparison'))
            target_value = decision_config.get('value')
            target_value2 = decision_config.get('value2')
            
            if target_value is None:
                    return self._create_error_result("Comparison requires 'value' parameter")
                
            result = ComparisonEvaluator.evaluate_comparison(
                comparison, field_value, target_value, target_value2
            )
            
            reasoning = f"Position {position.symbol} {position_field} ({field_value}) {comparison.value} {target_value}"
            
            self.logger.debug(LogCategory.DECISION_FLOW, "Position decision evaluated",
                            position_id=position.id, result=result)
            
            return self._create_success_result(
                result, reasoning, 0.95,
                {
                    'position_id': position.id,
                    'symbol': position.symbol,
                    'field': position_field,
                    'field_value': field_value
                }
            )
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, "Position decision failed", error=str(e))
            return self._create_error_result(f"Position decision error: {str(e)}")
    
    def _extract_position_field(self, position: Position, field: str) -> Optional[float]:
        """Extract specific field from position"""
        field_mapping = {
            'unrealized_pnl': position.unrealized_pnl,
            'realized_pnl': position.realized_pnl,
            'total_pnl': position.total_pnl,
            'quantity': position.quantity,
            'entry_price': position.entry_price,
            'current_price': position.current_price,
            'days_open': position.days_open,
            'return_percentage': position.return_percentage,
        }
        
        return field_mapping.get(field)

# =============================================================================
# BOT DECISION EVALUATOR
# =============================================================================

class BotDecisionEvaluator(BaseDecisionEvaluator):
    """Evaluator for bot-level decisions"""
    
    def evaluate(self, decision_config: Dict[str, Any], context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate bot-level decision"""
        try:
            bot_field = decision_config.get('bot_field', 'open_positions')
            
            # Extract bot metric
            field_value = self._extract_bot_field(context, bot_field)
            if field_value is None:
                return self._create_error_result(f"Cannot extract bot field: {bot_field}")
            
            # Evaluate comparison
            comparison = ComparisonOperator(decision_config.get('comparison'))
            target_value = decision_config.get('value')
            target_value2 = decision_config.get('value2')
            
            if target_value is None:
                return self._create_error_result("Comparison requires 'value' parameter")
                
                
            result = ComparisonEvaluator.evaluate_comparison(
                comparison, field_value, target_value, target_value2
            )
            
            reasoning = f"Bot {bot_field} ({field_value}) {comparison.value} {target_value}"
            
            self.logger.debug(LogCategory.DECISION_FLOW, "Bot decision evaluated",
                            field=bot_field, result=result)
            
            return self._create_success_result(
                result, reasoning, 1.0,
                {
                    'bot_field': bot_field,
                    'field_value': field_value,
                    'target_value': target_value
                }
            )
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, "Bot decision failed", error=str(e))
            return self._create_error_result(f"Bot decision error: {str(e)}")
    
    def _extract_bot_field(self, context: DecisionContext, field: str) -> Optional[float]:
        """Extract bot-level metrics"""
        if field == 'open_positions':
            return len(context.get_open_positions())
        elif field == 'total_positions':
            return len(context.positions)
        elif field == 'total_pnl':
            return sum(p.total_pnl for p in context.positions)
        elif field == 'unrealized_pnl':
            return sum(p.unrealized_pnl for p in context.get_open_positions())
        elif field in context.bot_stats:
            return context.bot_stats[field]
        
        return None

# =============================================================================
# GENERAL DECISION EVALUATOR
# =============================================================================

class GeneralDecisionEvaluator(BaseDecisionEvaluator):
    """Evaluator for general decisions (time, market conditions, etc.)"""
    
    def evaluate(self, decision_config: Dict[str, Any], context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate general decision"""
        try:
            condition_type = decision_config.get('condition_type', 'market_time')
            
            if condition_type == 'market_time':
                return self._evaluate_time_condition(decision_config, context)
            elif condition_type == 'market_day':
                return self._evaluate_day_condition(decision_config, context)
            elif condition_type == 'vix_level':
                return self._evaluate_vix_condition(decision_config, context)
            
            # Default to YES for unimplemented conditions
            return self._create_success_result(
                True, f"General condition {condition_type} evaluated as YES (stub)", 0.5
            )
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, "General decision failed", error=str(e))
            return self._create_error_result(f"General decision error: {str(e)}")
    
    def _evaluate_time_condition(self, decision_config: Dict[str, Any], 
                               context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate time-based conditions"""
        comparison = ComparisonOperator(decision_config.get('comparison'))
        target_time = decision_config.get('value')
        
        current_time = context.timestamp.strftime('%H:%M')
        
        if target_time is None:
            return self._create_error_result("Target time is required for time comparison")

        if comparison in [ComparisonOperator.ABOVE, ComparisonOperator.GREATER_THAN]:
            result = current_time > target_time
        elif comparison in [ComparisonOperator.BELOW, ComparisonOperator.LESS_THAN]:
            result = current_time < target_time
        elif comparison == ComparisonOperator.EQUAL_TO:
            result = current_time == target_time
        else:
            result = True
        
        reasoning = f"Current time {current_time} {comparison.value} {target_time}"
        
        return self._create_success_result(result, reasoning, 1.0)
    
    def _evaluate_day_condition(self, decision_config: Dict[str, Any], 
                              context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate day-based conditions"""
        target_day = decision_config.get('value')
        current_day = context.timestamp.strftime('%A')
        
        result = current_day == target_day
        reasoning = f"Current day {current_day}, target: {target_day}"
        
        return self._create_success_result(result, reasoning, 1.0)
    
    def _evaluate_vix_condition(self, decision_config: Dict[str, Any], 
                              context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate VIX-based conditions"""
        vix_data = context.get_market_data('VIX')
        if not vix_data:
            return self._create_error_result("VIX data not available")
        
        comparison = ComparisonOperator(decision_config.get('comparison'))
        target_value = decision_config.get('value')
        
        if target_value is None:
            return self._create_error_result("BETWEEN comparison requires 'value' parameter")
        
        result = ComparisonEvaluator.evaluate_comparison(
            comparison, vix_data.price, target_value
        )
        
        reasoning = f"VIX {vix_data.price} {comparison.value} {target_value}"
        
        return self._create_success_result(result, reasoning, 0.9)