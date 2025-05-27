# Option Alpha Framework - Decision Engine Main
# Main decision engine class with caching, analysis, and testing capabilities

import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

from oa_framework_enums import (
    DecisionType, DecisionResult, LogCategory
)
from oa_logging import FrameworkLogger
from oa_data_structures import MarketData
from decision_core import DecisionContext, DetailedDecisionResult
from decision_evaluators import (
    StockDecisionEvaluator, IndicatorDecisionEvaluator,
    PositionDecisionEvaluator, BotDecisionEvaluator,
    GeneralDecisionEvaluator
)

# =============================================================================
# MAIN DECISION ENGINE
# =============================================================================

class DecisionEngine:
    """
    Complete decision evaluation engine for Option Alpha decision recipes.
    Supports all decision types with caching, analysis, and testing capabilities.
    """
    
    def __init__(self, logger: FrameworkLogger, state_manager):
        self.logger = logger
        self.state_manager = state_manager
        
        # Initialize evaluators
        self.evaluators = {
            DecisionType.STOCK: StockDecisionEvaluator(logger),
            DecisionType.INDICATOR: IndicatorDecisionEvaluator(logger),
            DecisionType.POSITION: PositionDecisionEvaluator(logger),
            DecisionType.BOT: BotDecisionEvaluator(logger),
            DecisionType.GENERAL: GeneralDecisionEvaluator(logger)
        }
        
        # Cache for repeated evaluations
        self._evaluation_cache = {}
        self._cache_ttl = 60  # seconds
    
    def evaluate_decision(self, decision_config: Dict[str, Any], 
                         context: Optional[DecisionContext] = None) -> DecisionResult:
        """
        Evaluate a decision and return simple result for backward compatibility
        """
        detailed_result = self.evaluate_decision_detailed(decision_config, context)
        return detailed_result.result
    
    def evaluate_decision_detailed(self, decision_config: Dict[str, Any], 
                                 context: Optional[DecisionContext] = None) -> DetailedDecisionResult:
        """
        Evaluate a decision with detailed results and reasoning
        
        Args:
            decision_config: Decision configuration dictionary
            context: Decision context (created if None)
            
        Returns:
            DetailedDecisionResult with result, confidence, and reasoning
        """
        try:
            # Create context if not provided
            if context is None:
                context = self._create_default_context()
            
            # Handle grouped decisions (AND/OR logic)
            if 'logic_operator' in decision_config:
                return self._evaluate_grouped_decision(decision_config, context)
            
            # Get decision type
            recipe_type_str = decision_config.get('recipe_type')
            if not recipe_type_str:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning="Missing recipe_type in decision configuration"
                )
            
            try:
                recipe_type = DecisionType(recipe_type_str)
            except ValueError:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"Unknown recipe type: {recipe_type_str}"
                )
            
            # Check cache first
            cache_key = self._generate_cache_key(decision_config, context)
            cached_result = self._get_cached_result(cache_key)
            if cached_result:
                self.logger.debug(LogCategory.DECISION_FLOW, "Using cached decision result")
                return cached_result
            
            # Get appropriate evaluator
            evaluator = self.evaluators.get(recipe_type)
            if not evaluator:
                return DetailedDecisionResult(
                    DecisionResult.ERROR,
                    reasoning=f"No evaluator available for {recipe_type.value}"
                )
            
            # Evaluate decision
            result = evaluator.evaluate(decision_config, context)
            
            # Cache result
            self._cache_result(cache_key, result)
            
            # Log decision
            self.logger.info(LogCategory.DECISION_FLOW, "Decision evaluated",
                           recipe_type=recipe_type.value,
                           result=result.result.value,
                           confidence=result.confidence)
            
            # Store in state for analysis
            self._store_decision_record(decision_config, result, context)
            
            return result
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, "Decision evaluation failed",
                            error=str(e), config=decision_config)
            return DetailedDecisionResult(
                DecisionResult.ERROR,
                reasoning=f"Unexpected error in decision evaluation: {str(e)}"
            )
    
    def _evaluate_grouped_decision(self, decision_config: Dict[str, Any], 
                                 context: DecisionContext) -> DetailedDecisionResult:
        """Evaluate grouped decisions with AND/OR logic"""
        logic_operator = decision_config.get('logic_operator', 'and')
        grouped_decisions = decision_config.get('grouped_decisions', [])
        
        if not grouped_decisions:
            return DetailedDecisionResult(
                DecisionResult.ERROR,
                reasoning="No grouped_decisions provided"
            )
        
        results = []
        reasoning_parts = []
        
        for i, sub_decision in enumerate(grouped_decisions):
            result = self.evaluate_decision_detailed(sub_decision, context)
            results.append(result)
            reasoning_parts.append(f"({i+1}) {result.reasoning}")
        
        # Apply logic operator
        if logic_operator == 'and':
            final_result = all(r.result == DecisionResult.YES for r in results)
            logic_desc = "ALL"
        elif logic_operator == 'or':
            final_result = any(r.result == DecisionResult.YES for r in results)
            logic_desc = "ANY"
        else:
            return DetailedDecisionResult(
                DecisionResult.ERROR,
                reasoning=f"Unknown logic operator: {logic_operator}"
            )
        
        # Check for errors in sub-decisions
        if any(r.result == DecisionResult.ERROR for r in results):
            error_reasons = [r.reasoning for r in results if r.result == DecisionResult.ERROR]
            return DetailedDecisionResult(
                DecisionResult.ERROR,
                reasoning=f"Sub-decision errors: {'; '.join(error_reasons)}"
            )
        
        decision_result = DecisionResult.YES if final_result else DecisionResult.NO
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence for r in results) / len(results)
        
        reasoning = f"{logic_desc} of {len(results)} conditions: " + "; ".join(reasoning_parts)
        
        return DetailedDecisionResult(
            decision_result,
            confidence=avg_confidence,
            reasoning=reasoning,
            evaluation_data={
                'logic_operator': logic_operator,
                'sub_results': [r.result.value for r in results],
                'sub_confidences': [r.confidence for r in results]
            }
        )
    
    def _create_default_context(self) -> DecisionContext:
        """Create default decision context from current state"""
        try:
            # Get positions from state manager
            positions = self.state_manager.get_positions()
            
            # Create minimal market data (in real implementation, get from market data provider)
            market_data = {
                'SPY': MarketData('SPY', datetime.now(), 450.0, 449.5, 450.5, 1000000, 25.0),
                'QQQ': MarketData('QQQ', datetime.now(), 380.0, 379.5, 380.5, 800000, 30.0),
                'VIX': MarketData('VIX', datetime.now(), 18.5, 18.0, 19.0, 50000)
            }
            
            # Get bot stats
            bot_stats = {
                'total_positions': len(positions),
                'open_positions': len([p for p in positions if p.is_open]),
                'total_pnl': sum(p.total_pnl for p in positions),
                'available_capital': 10000
            }
            
            return DecisionContext(
                timestamp=datetime.now(),
                market_data=market_data,
                positions=positions,
                bot_stats=bot_stats,
                market_state={'regime': 'normal', 'volatility': 'low'}
            )
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, "Failed to create decision context",
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
    # CACHING METHODS
    # =============================================================================
    
    def _generate_cache_key(self, decision_config: Dict[str, Any], 
                          context: DecisionContext) -> str:
        """Generate cache key for decision result"""
        key_elements = {
            'config': decision_config,
            'timestamp_minute': context.timestamp.strftime('%Y%m%d_%H%M'),
            'market_data_keys': list(context.market_data.keys())
        }
        
        key_str = json.dumps(key_elements, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cached_result(self, cache_key: str) -> Optional[DetailedDecisionResult]:
        """Get cached decision result if still valid"""
        if cache_key in self._evaluation_cache:
            cached_entry = self._evaluation_cache[cache_key]
            
            if (datetime.now() - cached_entry['timestamp']).seconds < self._cache_ttl:
                return cached_entry['result']
            else:
                del self._evaluation_cache[cache_key]
        
        return None
    
    def _cache_result(self, cache_key: str, result: DetailedDecisionResult) -> None:
        """Cache decision result"""
        self._evaluation_cache[cache_key] = {
            'timestamp': datetime.now(),
            'result': result
        }
        
        if len(self._evaluation_cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self) -> None:
        """Remove expired cache entries"""
        current_time = datetime.now()
        expired_keys = [
            key for key, entry in self._evaluation_cache.items()
            if (current_time - entry['timestamp']).seconds > self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._evaluation_cache[key]
        
        self.logger.debug(LogCategory.DECISION_FLOW, "Cache cleanup completed",
                        removed_entries=len(expired_keys))
    
    def _store_decision_record(self, decision_config: Dict[str, Any], 
                             result: DetailedDecisionResult, 
                             context: DecisionContext) -> None:
        """Store decision record for analysis and debugging"""
        try:
            decision_record = {
                'timestamp': context.timestamp.isoformat(),
                'recipe_type': decision_config.get('recipe_type'),
                'decision_config': decision_config,
                'result': result.result.value,
                'confidence': result.confidence,
                'reasoning': result.reasoning,
                'evaluation_data': result.evaluation_data,
                'market_context': {
                    'symbols': list(context.market_data.keys()),
                    'position_count': len(context.positions)
                }
            }
            
            self.state_manager.store_cold_state(
                decision_record,
                'decision_evaluations',
                ['decisions', decision_config.get('recipe_type', 'unknown')]
            )
            
        except Exception as e:
            self.logger.warning(LogCategory.DECISION_FLOW, "Failed to store decision record",
                              error=str(e))
    
    # =============================================================================
    # ANALYSIS AND UTILITIES
    # =============================================================================
    
    def get_decision_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get statistics about recent decision evaluations"""
        try:
            since_time = datetime.now() - timedelta(hours=time_window_hours)
            
            decision_records = self.state_manager.get_cold_state(
                'decision_evaluations',
                limit=1000,
                start_date=since_time
            )
            
            if not decision_records:
                return {'total_decisions': 0}
            
            stats = {
                'total_decisions': len(decision_records),
                'time_window_hours': time_window_hours,
                'results_breakdown': {},
                'recipe_type_breakdown': {},
                'average_confidence': 0.0,
                'error_rate': 0.0
            }
            
            total_confidence = 0
            error_count = 0
            
            for record in decision_records:
                data = record['data']
                
                result = data.get('result', 'unknown')
                stats['results_breakdown'][result] = stats['results_breakdown'].get(result, 0) + 1
                
                recipe_type = data.get('recipe_type', 'unknown')
                stats['recipe_type_breakdown'][recipe_type] = stats['recipe_type_breakdown'].get(recipe_type, 0) + 1
                
                confidence = data.get('confidence', 0)
                total_confidence += confidence
                
                if result == 'error':
                    error_count += 1
            
            if len(decision_records) > 0:
                stats['average_confidence'] = total_confidence / len(decision_records)
                stats['error_rate'] = (error_count / len(decision_records)) * 100
            
            return stats
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, "Failed to get decision statistics",
                            error=str(e))
            return {'error': str(e)}
    
    def test_decision_config(self, decision_config: Dict[str, Any], 
                           test_scenarios: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Test a decision configuration against various scenarios"""
        if test_scenarios is None:
            test_scenarios = self._generate_default_test_scenarios()
        
        test_results = {
            'decision_config': decision_config,
            'total_scenarios': len(test_scenarios),
            'scenario_results': [],
            'summary': {
                'yes_count': 0,
                'no_count': 0,
                'error_count': 0,
                'average_confidence': 0.0
            }
        }
        
        total_confidence = 0
        
        for i, scenario in enumerate(test_scenarios):
            try:
                context = self._create_test_context(scenario)
                result = self.evaluate_decision_detailed(decision_config, context)
                
                scenario_result = {
                    'scenario_id': i,
                    'scenario_description': scenario.get('description', f'Scenario {i}'),
                    'result': result.result.value,
                    'confidence': result.confidence,
                    'reasoning': result.reasoning
                }
                
                test_results['scenario_results'].append(scenario_result)
                
                if result.result == DecisionResult.YES:
                    test_results['summary']['yes_count'] += 1
                elif result.result == DecisionResult.NO:
                    test_results['summary']['no_count'] += 1
                else:
                    test_results['summary']['error_count'] += 1
                
                total_confidence += result.confidence
                
            except Exception as e:
                test_results['scenario_results'].append({
                    'scenario_id': i,
                    'result': 'error',
                    'error': str(e)
                })
                test_results['summary']['error_count'] += 1
        
        if len(test_scenarios) > 0:
            test_results['summary']['average_confidence'] = total_confidence / len(test_scenarios)
        
        return test_results
    
    def _generate_default_test_scenarios(self) -> List[Dict[str, Any]]:
        """Generate default test scenarios for decision testing"""
        return [
            {
                'description': 'Bull market - SPY at 460',
                'market_data': {
                    'SPY': {'price': 460.0, 'iv_rank': 20.0},
                    'VIX': {'price': 15.0}
                },
                'positions': [],
                'bot_stats': {'open_positions': 0, 'total_pnl': 0}
            },
            {
                'description': 'Bear market - SPY at 420',
                'market_data': {
                    'SPY': {'price': 420.0, 'iv_rank': 60.0},
                    'VIX': {'price': 25.0}
                },
                'positions': [],
                'bot_stats': {'open_positions': 0, 'total_pnl': 0}
            },
            {
                'description': 'High volatility - VIX at 35',
                'market_data': {
                    'SPY': {'price': 440.0, 'iv_rank': 80.0},
                    'VIX': {'price': 35.0}
                },
                'positions': [],
                'bot_stats': {'open_positions': 2, 'total_pnl': -500}
            }
        ]
    
    def _create_test_context(self, scenario: Dict[str, Any]) -> DecisionContext:
        """Create decision context from test scenario"""
        market_data = {}
        for symbol, data in scenario.get('market_data', {}).items():
            market_data[symbol] = MarketData(
                symbol=symbol,
                timestamp=datetime.now(),
                price=data.get('price', 100.0),
                bid=data.get('price', 100.0) - 0.05,
                ask=data.get('price', 100.0) + 0.05,
                volume=data.get('volume', 100000),
                iv_rank=data.get('iv_rank', 50.0)
            )
        
        return DecisionContext(
            timestamp=datetime.now(),
            market_data=market_data,
            positions=scenario.get('positions', []),
            bot_stats=scenario.get('bot_stats', {}),
            market_state=scenario.get('market_state', {})
        )
    
    def clear_cache(self) -> None:
        """Clear all cached decision results"""
        self._evaluation_cache.clear()
        self.logger.info(LogCategory.DECISION_FLOW, "Decision cache cleared")
    
    def get_supported_recipe_types(self) -> List[str]:
        """Get list of supported decision recipe types"""
        return [recipe_type.value for recipe_type in self.evaluators.keys()]


# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_decision_engine(logger: FrameworkLogger, state_manager) -> DecisionEngine:
    """Factory function to create decision engine"""
    return DecisionEngine(logger, state_manager)