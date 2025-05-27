# Option Alpha Framework - Phase 1: Simple Strategy Decision Engine
# Implements basic decision evaluators for simple long call/put strategies

from datetime import datetime
from typing import Dict, List, Any, Optional
from oa_framework_enums import LogCategory, DecisionResult
from decision_core import BaseDecisionEvaluator, DetailedDecisionResult, DecisionContext, ComparisonEvaluator, ComparisonOperator
from oa_data_structures import Position, MarketData

# =============================================================================
# STOCK DECISION EVALUATOR
# =============================================================================

class StockDecisionEvaluator(BaseDecisionEvaluator):
    """
    Evaluates stock-based decisions for Option Alpha strategies.
    Handles price comparisons, price movements, and basic stock metrics.
    """
    
    def evaluate(self, decision_config: Dict[str, Any], 
                context: DecisionContext) -> DetailedDecisionResult:
        """
        Evaluate stock decision
        
        Args:
            decision_config: Stock decision configuration
            context: Decision context with market data
            
        Returns:
            DetailedDecisionResult with evaluation outcome
        """
        try:
            # Extract required config values
            symbol = self._extract_config_value(decision_config, 'symbol')
            price_field = decision_config.get('price_field', 'last_price')
            comparison = self._extract_config_value(decision_config, 'comparison')
            value = self._extract_config_value(decision_config, 'value')
            value2 = decision_config.get('value2')  # For 'between' comparisons
            
            # Validate symbol has market data
            market_data = self._validate_symbol_data(symbol, context)
            
            # Get the current value for comparison
            current_value = self._get_price_field_value(market_data, price_field, context)
            
            # Convert comparison string to enum
            comparison_op = ComparisonOperator(comparison)
            
            # Perform comparison
            result = ComparisonEvaluator.evaluate_comparison(comparison_op, current_value, value, value2)
            
            # Create detailed result
            comparison_str = ComparisonEvaluator.compare_to_string(comparison_op, current_value, value, value2)
            reasoning = f"Stock {symbol} {price_field}: {comparison_str}"
            
            evaluation_data = {
                'symbol': symbol,
                'price_field': price_field,
                'current_value': current_value,
                'comparison': comparison,
                'target_value': value,
                'target_value2': value2,
                'market_price': market_data.price,
                'timestamp': market_data.timestamp.isoformat()
            }
            
            self.logger.debug(LogCategory.DECISION_FLOW, "Stock decision evaluated",
                            symbol=symbol, result=result, reasoning=reasoning)
            
            return self._create_success_result(result, reasoning, 1.0, evaluation_data)
            
        except Exception as e:
            error_msg = f"Stock decision evaluation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg, 
                            config=decision_config)
            return self._create_error_result(error_msg)
    
    def _get_price_field_value(self, market_data: MarketData, price_field: str, 
                              context: DecisionContext) -> float:
        """Extract the requested price field value from market data"""
        
        field_mapping = {
            'last_price': market_data.price,
            'ask_price': market_data.ask or market_data.price,
            'bid_price': market_data.bid or market_data.price,
            'mid_price': market_data.mid_price or market_data.price,
            'bid_ask_spread': market_data.spread or 0.0,
            'close_price': market_data.price,  # Simplified - would need historical data
            'open_price': market_data.price,   # Simplified - would need historical data
            'high_price': market_data.price,   # Simplified - would need historical data
            'low_price': market_data.price,    # Simplified - would need historical data
            'volume': float(market_data.volume or 0),
            'iv_rank': market_data.iv_rank or 0.0
        }
        
        if price_field not in field_mapping:
            raise ValueError(f"Unsupported price field: {price_field}")
        
        value = field_mapping[price_field]
        if value is None:
            raise ValueError(f"Price field {price_field} not available for {market_data.symbol}")
        
        return float(value)

# =============================================================================
# INDICATOR DECISION EVALUATOR  
# =============================================================================

class IndicatorDecisionEvaluator(BaseDecisionEvaluator):
    """
    Evaluates technical indicator decisions.
    Simplified implementation for Phase 1 - supports basic RSI/momentum indicators.
    """
    
    def evaluate(self, decision_config: Dict[str, Any], 
                context: DecisionContext) -> DetailedDecisionResult:
        """
        Evaluate indicator decision (simplified for Phase 1)
        
        Args:
            decision_config: Indicator decision configuration  
            context: Decision context
            
        Returns:
            DetailedDecisionResult with evaluation outcome
        """
        try:
            # Extract config values
            symbol = self._extract_config_value(decision_config, 'symbol')
            indicator = decision_config.get('indicator', 'RSI')
            comparison = self._extract_config_value(decision_config, 'comparison')
            value = self._extract_config_value(decision_config, 'value')
            value2 = decision_config.get('value2')
            
            # Validate market data exists
            market_data = self._validate_symbol_data(symbol, context)
            
            # Calculate indicator value (simplified for Phase 1)
            indicator_value = self._calculate_simple_indicator(indicator, market_data, context)
            
            # Perform comparison
            comparison_op = ComparisonOperator(comparison)
            result = ComparisonEvaluator.evaluate_comparison(comparison_op, indicator_value, value, value2)
            
            # Create result
            comparison_str = ComparisonEvaluator.compare_to_string(comparison_op, indicator_value, value, value2)
            reasoning = f"Indicator {indicator} for {symbol}: {comparison_str}"
            
            evaluation_data = {
                'symbol': symbol,
                'indicator': indicator,
                'indicator_value': indicator_value,
                'comparison': comparison,
                'target_value': value,
                'target_value2': value2
            }
            
            self.logger.debug(LogCategory.DECISION_FLOW, "Indicator decision evaluated",
                            symbol=symbol, indicator=indicator, result=result)
            
            return self._create_success_result(result, reasoning, 0.8, evaluation_data)  # Lower confidence for simplified indicators
            
        except Exception as e:
            error_msg = f"Indicator decision evaluation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg, config=decision_config)
            return self._create_error_result(error_msg)
    
    def _calculate_simple_indicator(self, indicator: str, market_data: MarketData, 
                                   context: DecisionContext) -> float:
        """
        Calculate simplified indicator values for Phase 1.
        In a full implementation, this would use proper technical analysis libraries.
        """
        
        # For Phase 1, we'll use simplified/mock indicator calculations
        # In Phase 2, we'll implement proper technical indicators
        
        if indicator == 'RSI':
            # Simplified RSI based on price relative to a baseline
            # Real RSI would need historical price data
            baseline_price = 450.0  # SPY baseline for demo
            if market_data.symbol == 'SPY':
                price_ratio = market_data.price / baseline_price
                # Normalize to RSI-like range (0-100)
                if price_ratio > 1.0:
                    return min(50 + (price_ratio - 1.0) * 100, 100)
                else:
                    return max(50 - (1.0 - price_ratio) * 100, 0)
            else:
                # Default RSI value for other symbols
                return 50.0
                
        elif indicator == 'Momentum':
            # Simple momentum based on IV rank as proxy
            return market_data.iv_rank or 50.0
            
        elif indicator in ['SMA', 'EMA']:
            # Moving averages - return current price for now
            return market_data.price
            
        elif indicator == 'VIX':
            # VIX level - use IV rank as proxy
            return market_data.iv_rank or 15.0
            
        else:
            # Default indicator value
            self.logger.warning(LogCategory.DECISION_FLOW, "Unsupported indicator, using default", 
                              indicator=indicator)
            return 50.0

# =============================================================================
# BOT DECISION EVALUATOR
# =============================================================================

class BotDecisionEvaluator(BaseDecisionEvaluator):
    """
    Evaluates bot-level decisions like capital limits, position counts, etc.
    """
    
    def evaluate(self, decision_config: Dict[str, Any], 
                context: DecisionContext) -> DetailedDecisionResult:
        """
        Evaluate bot decision
        
        Args:
            decision_config: Bot decision configuration
            context: Decision context with bot stats
            
        Returns:
            DetailedDecisionResult with evaluation outcome
        """
        try:
            # Extract config values
            bot_field = decision_config.get('bot_field', 'open_positions')
            comparison = self._extract_config_value(decision_config, 'comparison')
            value = self._extract_config_value(decision_config, 'value')
            value2 = decision_config.get('value2')
            
            # Get current bot field value
            current_value = self._get_bot_field_value(bot_field, context)
            
            # Perform comparison
            comparison_op = ComparisonOperator(comparison)
            result = ComparisonEvaluator.evaluate_comparison(comparison_op, current_value, value, value2)
            
            # Create result
            comparison_str = ComparisonEvaluator.compare_to_string(comparison_op, current_value, value, value2)
            reasoning = f"Bot {bot_field}: {comparison_str}"
            
            evaluation_data = {
                'bot_field': bot_field,
                'current_value': current_value,
                'comparison': comparison,
                'target_value': value,
                'target_value2': value2,
                'bot_stats': context.bot_stats
            }
            
            self.logger.debug(LogCategory.DECISION_FLOW, "Bot decision evaluated",
                            bot_field=bot_field, result=result, reasoning=reasoning)
            
            return self._create_success_result(result, reasoning, 1.0, evaluation_data)
            
        except Exception as e:
            error_msg = f"Bot decision evaluation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg, config=decision_config)
            return self._create_error_result(error_msg)
    
    def _get_bot_field_value(self, bot_field: str, context: DecisionContext) -> float:
        """Extract bot field value from context"""
        
        # Map bot fields to context values
        if bot_field == 'open_positions':
            return float(len(context.get_open_positions()))
        elif bot_field == 'total_positions':
            return float(len(context.positions))
        elif bot_field == 'available_capital':
            return float(context.bot_stats.get('available_capital', 0))
        elif bot_field == 'total_pnl':
            return float(context.bot_stats.get('total_pnl', 0))
        elif bot_field == 'day_pnl':
            return float(context.bot_stats.get('day_pnl', 0))
        else:
            # Try to get from bot_stats directly
            value = context.bot_stats.get(bot_field, 0)
            return float(value)

# =============================================================================
# GENERAL DECISION EVALUATOR
# =============================================================================

class GeneralDecisionEvaluator(BaseDecisionEvaluator):
    """
    Evaluates general decisions like time, market conditions, etc.
    """
    
    def evaluate(self, decision_config: Dict[str, Any], 
                context: DecisionContext) -> DetailedDecisionResult:
        """
        Evaluate general decision
        
        Args:
            decision_config: General decision configuration
            context: Decision context
            
        Returns:
            DetailedDecisionResult with evaluation outcome
        """
        try:
            condition_type = decision_config.get('condition_type', 'market_time')
            comparison = self._extract_config_value(decision_config, 'comparison')
            value = decision_config.get('value')
            if value is None:
                raise ValueError(f"'value' cannot be None")
            
            # Evaluate based on condition type
            if condition_type == 'market_time':
                current_value = self._get_market_time_value()
                target_value = self._parse_time_value(value)
            elif condition_type == 'vix_level':
                # Use VIX from market data if available
                vix_data = context.market_data.get('VIX')
                current_value = vix_data.price if vix_data else 15.0
                target_value = float(value)
            elif condition_type == 'day_of_week':
                current_value = datetime.now().weekday()  # 0=Monday, 6=Sunday
                target_value = self._parse_day_of_week(value)
            else:
                raise ValueError(f"Unsupported condition type: {condition_type}")
            
            # Perform comparison
            comparison_op = ComparisonOperator(comparison)
            result = ComparisonEvaluator.evaluate_comparison(comparison_op, current_value, target_value)
            
            # Create result
            comparison_str = ComparisonEvaluator.compare_to_string(comparison_op, current_value, target_value)
            reasoning = f"General condition {condition_type}: {comparison_str}"
            
            evaluation_data = {
                'condition_type': condition_type,
                'current_value': current_value,
                'comparison': comparison,
                'target_value': target_value
            }
            
            self.logger.debug(LogCategory.DECISION_FLOW, "General decision evaluated",
                            condition_type=condition_type, result=result)
            
            return self._create_success_result(result, reasoning, 1.0, evaluation_data)
            
        except Exception as e:
            error_msg = f"General decision evaluation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg, config=decision_config)
            return self._create_error_result(error_msg)
    
    def _get_market_time_value(self) -> float:
        """Get current market time as decimal hours (e.g., 10:30 = 10.5)"""
        now = datetime.now()
        return now.hour + (now.minute / 60.0)
    
    def _parse_time_value(self, time_str: str) -> float:
        """Parse time string to decimal hours"""
        if isinstance(time_str, (int, float)):
            return float(time_str)
        
        # Parse time strings like "10:30", "1030", etc.
        time_str = str(time_str).replace(':', '')
        if len(time_str) == 4:
            hours = int(time_str[:2])
            minutes = int(time_str[2:])
            return hours + (minutes / 60.0)
        elif len(time_str) == 3:
            hours = int(time_str[0])
            minutes = int(time_str[1:])
            return hours + (minutes / 60.0)
        else:
            return float(time_str)
    
    def _parse_day_of_week(self, day_str: str) -> float:
        """Parse day of week string to number (0=Monday)"""
        day_map = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 
            'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6
        }
        return float(day_map.get(day_str.lower(), 0))

# =============================================================================
# MAIN DECISION ENGINE
# =============================================================================

class SimpleStrategyDecisionEngine:
    """
    Main decision engine for Phase 1 simple strategies.
    Routes decisions to appropriate evaluators.
    """
    
    def __init__(self, logger):
        self.logger = logger
        
        # Initialize evaluators
        self.evaluators = {
            'stock': StockDecisionEvaluator(logger),
            'indicator': IndicatorDecisionEvaluator(logger),
            'bot': BotDecisionEvaluator(logger),
            'general': GeneralDecisionEvaluator(logger)
        }
        
        self.logger.info(LogCategory.SYSTEM, "Simple strategy decision engine initialized",
                        evaluators=list(self.evaluators.keys()))
    
    def evaluate_decision(self, decision_config: Dict[str, Any], 
                         context: DecisionContext) -> DetailedDecisionResult:
        """
        Evaluate a decision using the appropriate evaluator
        
        Args:
            decision_config: Decision configuration dictionary
            context: Decision context with market data and positions
            
        Returns:
            DetailedDecisionResult with evaluation outcome
        """
        try:
            # Get recipe type
            recipe_type = decision_config.get('recipe_type')
            if not recipe_type:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning="Missing recipe_type in decision config"
                )
            
            # Handle grouped decisions (AND/OR logic)
            if 'logic_operator' in decision_config:
                return self._evaluate_grouped_decision(decision_config, context)
            
            # Get appropriate evaluator
            evaluator = self.evaluators.get(recipe_type)
            if not evaluator:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"No evaluator for recipe type: {recipe_type}"
                )
            
            # Evaluate decision
            result = evaluator.evaluate(decision_config, context)
            
            self.logger.debug(LogCategory.DECISION_FLOW, "Decision evaluation completed",
                            recipe_type=recipe_type, result=result.result.value)
            
            return result
            
        except Exception as e:
            error_msg = f"Decision evaluation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg, config=decision_config)
            return DetailedDecisionResult(DecisionResult.ERROR, reasoning=error_msg)
    
    def _evaluate_grouped_decision(self, decision_config: Dict[str, Any], 
                                  context: DecisionContext) -> DetailedDecisionResult:
        """
        Evaluate grouped decisions with AND/OR logic
        
        Args:
            decision_config: Grouped decision configuration
            context: Decision context
            
        Returns:
            DetailedDecisionResult with evaluation outcome
        """
        try:
            logic_operator = decision_config.get('logic_operator', 'and')
            grouped_decisions = decision_config.get('grouped_decisions', [])
            
            if not grouped_decisions:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning="No grouped_decisions provided"
                )
            
            results = []
            reasoning_parts = []
            
            # Evaluate each sub-decision
            for i, sub_decision in enumerate(grouped_decisions):
                sub_result = self.evaluate_decision(sub_decision, context)
                results.append(sub_result)
                reasoning_parts.append(f"({i+1}) {sub_result.reasoning or 'No reason'}")
            
            # Apply logic operator
            if logic_operator.lower() == 'and':
                final_result = all(r.is_yes for r in results)
                operator_desc = "AND"
            elif logic_operator.lower() == 'or':
                final_result = any(r.is_yes for r in results)
                operator_desc = "OR"
            else:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Unknown logic operator: {logic_operator}"
                )
            
            # Build reasoning
            reasoning = f"Grouped decision ({operator_desc}): " + f" {operator_desc} ".join(reasoning_parts)
            
            # Calculate confidence (average of sub-decisions)
            confidence = sum(r.confidence for r in results) / len(results) if results else 0.0
            
            evaluation_data = {
                'logic_operator': logic_operator,
                'sub_decisions_count': len(results),
                'sub_results': [r.result.value for r in results],
                'sub_confidences': [r.confidence for r in results]
            }
            
            return DetailedDecisionResult(
                DecisionResult.YES if final_result else DecisionResult.NO,
                confidence=confidence,
                reasoning=reasoning,
                evaluation_data=evaluation_data
            )
            
        except Exception as e:
            error_msg = f"Grouped decision evaluation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg)
            return DetailedDecisionResult(DecisionResult.ERROR, reasoning=error_msg)

# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_simple_strategy_decision_engine(logger) -> SimpleStrategyDecisionEngine:
    """
    Factory function to create simple strategy decision engine
    
    Args:
        logger: Framework logger instance
        
    Returns:
        SimpleStrategyDecisionEngine instance
    """
    return SimpleStrategyDecisionEngine(logger)

# =============================================================================
# TESTING AND DEMONSTRATION
# =============================================================================

def test_simple_strategy_decisions():
    """Test simple strategy decision engine with various scenarios"""
    print("=" * 60)
    print("Simple Strategy Decision Engine - Phase 1 Testing")
    print("=" * 60)
    
    # Import required components
    from oa_logging import FrameworkLogger
    from decision_core import create_test_context
    
    # Setup
    logger = FrameworkLogger("DecisionEngineTest")
    engine = create_simple_strategy_decision_engine(logger)
    context = create_test_context(['SPY', 'QQQ', 'VIX'])
    
    # Test cases
    test_cases = [
        {
            'name': 'Stock Price Above 400',
            'config': {
                "recipe_type": "stock",
                "symbol": "SPY",
                "price_field": "last_price",
                "comparison": "greater_than",
                "value": 400
            }
        },
        {
            'name': 'RSI Oversold',
            'config': {
                "recipe_type": "indicator",
                "symbol": "SPY",
                "indicator": "RSI",
                "comparison": "less_than",
                "value": 30
            }
        },
        {
            'name': 'Bot Under Position Limit',
            'config': {
                "recipe_type": "bot",
                "bot_field": "open_positions",
                "comparison": "less_than",
                "value": 5
            }
        },
        {
            'name': 'Market Time After 10 AM',
            'config': {
                "recipe_type": "general",
                "condition_type": "market_time",
                "comparison": "greater_than",
                "value": "10:00"
            }
        },
        {
            'name': 'Grouped Decision (AND)',
            'config': {
                "logic_operator": "and",
                "grouped_decisions": [
                    {
                        "recipe_type": "stock",
                        "symbol": "SPY",
                        "price_field": "last_price",
                        "comparison": "greater_than",
                        "value": 400
                    },
                    {
                        "recipe_type": "bot",
                        "bot_field": "open_positions",
                        "comparison": "less_than",
                        "value": 5
                    }
                ]
            }
        }
    ]
    
    # Run tests
    print(f"\nTesting with SPY price: ${context.market_data['SPY'].price}")
    print(f"Bot open positions: {len(context.get_open_positions())}")
    print(f"Current time: {datetime.now().strftime('%H:%M')}")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. Testing: {test_case['name']}")
        
        result = engine.evaluate_decision(test_case['config'], context)
        
        status = "✓" if result.result == DecisionResult.YES else "✗" if result.result == DecisionResult.NO else "!"
        print(f"   {status} Result: {result.result.value}")
        print(f"   Confidence: {result.confidence:.2f}")
        print(f"   Reasoning: {result.reasoning}")
        
        if result.is_error:
            print(f"   ERROR: Check decision configuration")
        
        print()
    
    print("=" * 60)
    print("✅ Simple Strategy Decision Engine Testing Complete!")
    print("✅ Ready for position management integration")
    print("=" * 60)

if __name__ == "__main__":
    test_simple_strategy_decisions()