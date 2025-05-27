# Option Alpha Framework - Decision Engine Core
# Core components and data structures for decision evaluation

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field

from oa_framework_enums import (
    DecisionResult, ComparisonOperator, LogCategory
)
from oa_data_structures import MarketData, Position

# =============================================================================
# DECISION CONTEXT AND RESULTS
# =============================================================================

@dataclass
class DecisionContext:
    """Context information available during decision evaluation"""
    timestamp: datetime
    market_data: Dict[str, MarketData]
    positions: List[Position]
    bot_stats: Dict[str, Any]
    market_state: Dict[str, Any]
    
    def get_market_data(self, symbol: str) -> Optional[MarketData]:
        """Get market data for a symbol"""
        return self.market_data.get(symbol)
    
    def get_positions_for_symbol(self, symbol: str) -> List[Position]:
        """Get all positions for a specific symbol"""
        return [p for p in self.positions if p.symbol == symbol]
    
    def get_open_positions(self) -> List[Position]:
        """Get all open positions"""
        return [p for p in self.positions if p.state == 'open']

@dataclass
class DetailedDecisionResult:
    """Detailed result of decision evaluation with reasoning"""
    result: DecisionResult
    confidence: float = 1.0
    reasoning: Optional[str] = None
    evaluation_data: Dict[str, Any] = field(default_factory=dict)
    calculation_details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_yes(self) -> bool:
        """Check if result is YES"""
        return self.result == DecisionResult.YES
    
    @property
    def is_no(self) -> bool:
        """Check if result is NO"""
        return self.result == DecisionResult.NO
    
    @property
    def is_error(self) -> bool:
        """Check if result is ERROR"""
        return self.result == DecisionResult.ERROR

# =============================================================================
# COMPARISON UTILITIES
# =============================================================================

class ComparisonEvaluator:
    """Utility class for evaluating comparison operations"""
    
    @staticmethod
    def evaluate_comparison(operator: ComparisonOperator, value1: float, 
                      value2: float, value3: Optional[float] = None) -> bool:
        """
        Evaluate comparison between values
        
        Args:
            operator: Comparison operator
            value1: Left side value
            value2: Right side value (or lower bound for BETWEEN)
            value3: Upper bound for BETWEEN operations
            
        Returns:
            Boolean result of comparison
        """
        try:
            if operator == ComparisonOperator.GREATER_THAN:
                return value1 > value2
            elif operator == ComparisonOperator.GREATER_THAN_OR_EQUAL:
                return value1 >= value2
            elif operator == ComparisonOperator.LESS_THAN:
                return value1 < value2
            elif operator == ComparisonOperator.LESS_THAN_OR_EQUAL:
                return value1 <= value2
            elif operator == ComparisonOperator.EQUAL_TO:
                return abs(value1 - value2) < 1e-6  # Float equality with tolerance
            elif operator == ComparisonOperator.ABOVE:
                return value1 > value2
            elif operator == ComparisonOperator.BELOW:
                return value1 < value2
            elif operator == ComparisonOperator.BETWEEN:
                if value3 is None:
                    raise ValueError("BETWEEN operator requires value3")
                return value2 <= value1 <= value3
            else:
                raise ValueError(f"Unknown comparison operator: {operator}")
                
        except Exception as e:
            raise ValueError(f"Comparison evaluation failed: {e}")
    
    @staticmethod
    def compare_to_string(operator: ComparisonOperator, value1: float, 
                         value2: float, value3: Optional[float] = None) -> str:
        """Generate human-readable comparison string"""
        if operator == ComparisonOperator.BETWEEN and value3 is not None:
            return f"{value1} between {value2} and {value3}"
        else:
            op_symbols = {
                ComparisonOperator.GREATER_THAN: ">",
                ComparisonOperator.GREATER_THAN_OR_EQUAL: ">=",
                ComparisonOperator.LESS_THAN: "<",
                ComparisonOperator.LESS_THAN_OR_EQUAL: "<=",
                ComparisonOperator.EQUAL_TO: "==",
                ComparisonOperator.ABOVE: ">",
                ComparisonOperator.BELOW: "<"
            }
            symbol = op_symbols.get(operator, operator.value)
            return f"{value1} {symbol} {value2}"

# =============================================================================
# DECISION EVALUATOR BASE CLASS
# =============================================================================

class BaseDecisionEvaluator:
    """Base class for all decision evaluators"""
    
    def __init__(self, logger):
        self.logger = logger
    
    def evaluate(self, decision_config: Dict[str, Any], 
                context: DecisionContext) -> DetailedDecisionResult:
        """
        Evaluate decision - must be implemented by subclasses
        
        Args:
            decision_config: Decision configuration dictionary
            context: Decision context with market data and positions
            
        Returns:
            DetailedDecisionResult with evaluation outcome
        """
        raise NotImplementedError("Subclasses must implement evaluate method")
    
    def _create_error_result(self, message: str) -> DetailedDecisionResult:
        """Helper to create error result"""
        return DetailedDecisionResult(
            DecisionResult.ERROR,
            confidence=0.0,
            reasoning=message
        )
    
    def _create_success_result(self, result: bool, reasoning: str, 
                             confidence: float = 1.0,
                             evaluation_data: Optional[Dict[str, Any]] = None) -> DetailedDecisionResult:
        """Helper to create success result"""
        return DetailedDecisionResult(
            DecisionResult.YES if result else DecisionResult.NO,
            confidence=confidence,
            reasoning=reasoning,
            evaluation_data=evaluation_data or {}
        )
    
    def _extract_config_value(self, config: Dict[str, Any], key: str, 
                            required: bool = True, default: Any = None) -> Any:
        """Helper to extract and validate config values"""
        if key not in config:
            if required:
                raise ValueError(f"Missing required config key: {key}")
            return default
        return config[key]
    
    def _validate_symbol_data(self, symbol: str, context: DecisionContext) -> MarketData:
        """Helper to validate symbol has market data"""
        market_data = context.get_market_data(symbol)
        if not market_data:
            raise ValueError(f"No market data available for symbol: {symbol}")
        return market_data

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_test_context(symbols: Optional[List[str]] = None) -> DecisionContext:
    """
    Create a test decision context for testing
    
    Args:
        symbols: List of symbols to include in market data
        
    Returns:
        DecisionContext with test data
    """
    if symbols is None:
        symbols = ['SPY', 'QQQ', 'VIX']
    
    market_data = {}
    for symbol in symbols:
        if symbol == 'VIX':
            price = 18.5
        elif symbol == 'SPY':
            price = 450.0
        elif symbol == 'QQQ':
            price = 380.0
        else:
            price = 100.0
            
        market_data[symbol] = MarketData(
            symbol=symbol,
            timestamp=datetime.now(),
            price=price,
            bid=price - 0.05,
            ask=price + 0.05,
            volume=100000,
            iv_rank=25.0
        )
    
    # Create test positions
    test_positions = []
    if len(symbols) > 1:
        from oa_framework_enums import PositionType, PositionState
        
        test_position = Position(
            id="test_position_1",
            symbol=symbols[0],
            position_type=PositionType.LONG_CALL,
            state=PositionState.OPEN,
            opened_at=datetime.now() - timedelta(days=2),
            quantity=1,
            entry_price=100.0,
            current_price=105.0,
            unrealized_pnl=5.0
        )
        test_positions.append(test_position)
    
    return DecisionContext(
        timestamp=datetime.now(),
        market_data=market_data,
        positions=test_positions,
        bot_stats={
            'total_positions': len(test_positions),
            'open_positions': len(test_positions),
            'total_pnl': sum(p.total_pnl for p in test_positions),
            'available_capital': 10000
        },
        market_state={'regime': 'normal', 'volatility': 'low'}
    )

def validate_decision_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate decision configuration and return list of errors
    
    Args:
        config: Decision configuration to validate
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    
    # Check for required recipe_type
    if 'recipe_type' not in config:
        errors.append("Missing required field: recipe_type")
        return errors  # Can't continue validation without recipe type
    
    recipe_type = config['recipe_type']
    
    # Validate based on recipe type
    if recipe_type == 'stock':
        if 'symbol' not in config:
            errors.append("Stock decisions require 'symbol' field")
        if 'comparison' not in config:
            errors.append("Stock decisions require 'comparison' field")
        if 'value' not in config:
            errors.append("Stock decisions require 'value' field")
    
    elif recipe_type == 'indicator':
        if 'symbol' not in config:
            errors.append("Indicator decisions require 'symbol' field")
        if 'indicator' not in config:
            errors.append("Indicator decisions require 'indicator' field")
    
    elif recipe_type == 'position':
        if 'position_field' not in config:
            errors.append("Position decisions require 'position_field' field")
    
    elif recipe_type == 'bot':
        if 'bot_field' not in config:
            errors.append("Bot decisions require 'bot_field' field")
    
    elif recipe_type == 'general':
        if 'condition_type' not in config:
            errors.append("General decisions require 'condition_type' field")
    
    # Validate grouped decisions
    if 'logic_operator' in config:
        if 'grouped_decisions' not in config:
            errors.append("Grouped decisions require 'grouped_decisions' field")
        elif not isinstance(config['grouped_decisions'], list):
            errors.append("grouped_decisions must be a list")
        elif len(config['grouped_decisions']) < 2:
            errors.append("grouped_decisions must contain at least 2 decisions")
    
    # Validate comparison operators
    if 'comparison' in config:
        try:
            ComparisonOperator(config['comparison'])
        except ValueError:
            errors.append(f"Invalid comparison operator: {config['comparison']}")
    
    return errors

# =============================================================================
# TESTING UTILITIES
# =============================================================================

def test_decision_config_examples() -> List[Dict[str, Any]]:
    """Return example decision configurations for testing"""
    return [
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
                "indicator_period": 14,
                "comparison": "less_than",
                "value": 30
            }
        },
        {
            'name': 'Position Profitable',
            'config': {
                "recipe_type": "position",
                "position_reference": "current",
                "position_field": "unrealized_pnl",
                "comparison": "greater_than",
                "value": 0
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
            'name': 'Bull Market and Low VIX',
            'config': {
                "logic_operator": "and",
                "grouped_decisions": [
                    {
                        "recipe_type": "stock",
                        "symbol": "SPY",
                        "price_field": "last_price",
                        "comparison": "greater_than",
                        "value": 440
                    },
                    {
                        "recipe_type": "general",
                        "condition_type": "vix_level",
                        "comparison": "less_than",
                        "value": 20
                    }
                ]
            }
        }
    ]

def demonstrate_decision_core():
    """Demonstrate core decision functionality"""
    print("=" * 50)
    print("Decision Engine Core - Demo")
    print("=" * 50)
    
    # Test comparison evaluator
    print("\n1. Testing Comparison Evaluator:")
    
    test_cases = [
        (ComparisonOperator.GREATER_THAN, 10, 5, None, True),
        (ComparisonOperator.LESS_THAN, 5, 10, None, True),
        (ComparisonOperator.BETWEEN, 7, 5, 10, True),
        (ComparisonOperator.BETWEEN, 15, 5, 10, False),
        (ComparisonOperator.EQUAL_TO, 5.0, 5.0, None, True)
    ]
    
    for op, val1, val2, val3, expected in test_cases:
        result = ComparisonEvaluator.evaluate_comparison(op, val1, val2, val3)
        status = "✓" if result == expected else "✗"
        comparison_str = ComparisonEvaluator.compare_to_string(op, val1, val2, val3)
        print(f"   {status} {comparison_str} = {result}")
    
    # Test context creation
    print("\n2. Testing Context Creation:")
    context = create_test_context(['SPY', 'QQQ', 'VIX'])
    print(f"   ✓ Created context with {len(context.market_data)} symbols")
    print(f"   ✓ Market data: {list(context.market_data.keys())}")
    print(f"   ✓ Positions: {len(context.positions)}")
    print(f"   ✓ Bot stats: {context.bot_stats}")
    
    # Test config validation
    print("\n3. Testing Config Validation:")
    test_configs = test_decision_config_examples()
    
    for example in test_configs[:3]:  # Test first 3
        errors = validate_decision_config(example['config'])
        status = "✓" if not errors else "✗"
        print(f"   {status} {example['name']}: {len(errors)} errors")
        if errors:
            for error in errors:
                print(f"      - {error}")
    
    print("\n✅ Decision Core Components Working!")

if __name__ == "__main__":
    demonstrate_decision_core()