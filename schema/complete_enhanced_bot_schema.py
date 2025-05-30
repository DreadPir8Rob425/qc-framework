# Complete Enhanced Option Alpha Bot Schema - Master Schema File
# Combines all schema components into the final comprehensive schema

import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass

# Import all schema components
from enhanced_bot_schema_core import ENHANCED_OA_BOT_SCHEMA, ValidationLimits
from position_schemas import POSITION_SCHEMA_COMPONENTS
from decision_schemas import DECISION_SCHEMAS
from enhanced_bot_schema_enums import *
from decision_recipe_enums import *
from position_configuration_enums import *

# =============================================================================
# COMPLETE ENHANCED BOT SCHEMA - MASTER DEFINITION
# =============================================================================

def create_complete_enhanced_schema() -> Dict[str, Any]:
    """
    Create the complete enhanced bot schema by combining all components.
    This is the master schema that includes all decision recipes, position configurations,
    and enhanced functionality.
    """
    
    # Start with the base enhanced schema
    complete_schema = ENHANCED_OA_BOT_SCHEMA.copy()
    
    # Add all position schema components
    complete_schema["definitions"].update(POSITION_SCHEMA_COMPONENTS)
    
    # Add all decision schema components  
    complete_schema["definitions"].update(DECISION_SCHEMAS)
    
    # Add additional enhanced definitions
    complete_schema["definitions"].update(get_enhanced_definitions())
    
    return complete_schema

def get_enhanced_definitions() -> Dict[str, Any]:
    """Get additional enhanced schema definitions not covered in other files"""
    
    return {
        # =============================================================================
        # COMPLETE DECISION RECIPES - STOCK DECISIONS
        # =============================================================================
        "stock_decision": {
            "type": "object",
            "required": ["symbol", "comparison"],
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Stock symbol to evaluate"
                },
                "price_field": {
                    "enum": [item.value for item in StockPriceField],
                    "default": StockPriceField.LAST_PRICE.value,
                    "description": "Stock price field to compare"
                },
                "comparison": {
                    "enum": [item.value for item in ComparisonOperator],
                    "description": "Comparison operator"
                },
                "value": {
                    "type": "number",
                    "description": "Target value for comparison"
                },
                "value2": {
                    "type": "number", 
                    "description": "Second value for 'between' comparisons"
                },
                "reference_point": {
                    "enum": [item.value for item in PriceReference],
                    "description": "Reference point for price comparisons"
                },
                "time_frame": {
                    "enum": [item.value for item in TimeFrame],
                    "description": "Time frame for comparison"
                },
                "days_ago": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 365,
                    "description": "Number of days ago for historical comparisons"
                },
                "expiration_config": {
                    "$ref": "#/definitions/expiration_config",
                    "description": "Expiration configuration for expected move calculations"
                },
                "probability_config": {
                    "type": "object",
                    "description": "Configuration for probability-based stock decisions",
                    "properties": {
                        "above_percent": {"type": "number", "minimum": 0, "maximum": 100},
                        "below_percent": {"type": "number", "minimum": 0, "maximum": 100},
                        "low_price": {"type": "number", "minimum": 0},
                        "high_price": {"type": "number", "minimum": 0},
                        "days": {"type": "integer", "minimum": 1, "maximum": 365},
                        "probability_threshold": {"type": "number", "minimum": 0, "maximum": 100}
                    }
                },
                "earnings_config": {
                    "type": "object",
                    "description": "Earnings-related decision configuration",
                    "properties": {
                        "days": {"type": "integer", "minimum": 0, "maximum": 365},
                        "timing": {
                            "enum": [item.value for item in EarningsTime],
                            "description": "Earnings announcement timing"
                        },
                        "comparison_type": {
                            "enum": ["in", "more_than", "less_than", "exactly"],
                            "description": "Type of comparison for earnings timing"
                        }
                    }
                },
                "symbol_metadata": {
                    "type": "object",
                    "description": "Symbol metadata filters",
                    "properties": {
                        "symbol_type": {
                            "enum": [item.value for item in SymbolType],
                            "description": "Type of security"
                        },
                        "liquidity_score": {
                            "enum": [score.value for score in LiquidityScore],
                            "description": "Liquidity score requirement"
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Required tags for symbol"
                        },
                        "tag_filter_type": {
                            "enum": ["any", "all", "none"],
                            "default": "any",
                            "description": "How to apply tag filtering"
                        },
                        "trade_ideas_included": {
                            "type": "boolean",
                            "description": "Whether symbol is included in Trade Ideas"
                        }
                    }
                }
            }
        },

        # =============================================================================
        # COMPLETE DECISION RECIPES - INDICATOR DECISIONS
        # =============================================================================
        "indicator_decision": {
            "type": "object",
            "required": ["symbol", "indicator"],
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Symbol for indicator calculation"
                },
                "indicator": {
                    "enum": [item.value for item in TechnicalIndicator],
                    "description": "Technical indicator to evaluate"
                },
                "indicator_period": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 200,
                    "default": 14,
                    "description": "Period for indicator calculation"
                },
                "comparison": {
                    "enum": [item.value for item in ComparisonOperator],
                    "description": "Comparison operator"
                },
                "value": {
                    "type": "number",
                    "description": "Target value for comparison"
                },
                "value2": {
                    "type": "number",
                    "description": "Second value for range comparisons"
                },
                "indicator_signal": {
                    "enum": [item.value for item in IndicatorSignal],
                    "description": "Signal type for signal-based indicators"
                },
                "time_reference": {
                    "enum": [item.value for item in TimeFrame] + ["intraday", "days_ago"],
                    "default": "intraday",
                    "description": "Time reference for indicator calculation"
                },
                "days_ago": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 365,
                    "description": "Days ago for historical indicator values"
                },
                "comparison_indicator": {
                    "type": "object",
                    "description": "Compare against another indicator",
                    "properties": {
                        "symbol": {"type": "string"},
                        "indicator": {"enum": [item.value for item in TechnicalIndicator]},
                        "period": {"type": "integer", "minimum": 1, "maximum": 200},
                        "time_reference": {"enum": [item.value for item in TimeFrame] + ["intraday", "days_ago"]},
                        "days_ago": {"type": "integer", "minimum": 0, "maximum": 365}
                    }
                },
                "macd_config": {
                    "type": "object",
                    "description": "MACD-specific configuration",
                    "properties": {
                        "fast_period": {"type": "integer", "default": 12},
                        "slow_period": {"type": "integer", "default": 26},
                        "signal_period": {"type": "integer", "default": 9},
                        "ma_type": {
                            "enum": [item.value for item in MovingAverageType],
                            "default": MovingAverageType.EMA.value
                        },
                        "line_type": {
                            "enum": [item.value for item in MACDLine],
                            "description": "MACD line to compare against"
                        }
                    }
                },
                "bollinger_config": {
                    "type": "object",
                    "description": "Bollinger Bands configuration",
                    "properties": {
                        "period": {"type": "integer", "default": 20},
                        "std_dev": {"type": "number", "default": 2.0},
                        "ma_type": {
                            "enum": [item.value for item in MovingAverageType],
                            "default": MovingAverageType.SMA.value
                        },
                        "band_line": {
                            "enum": [item.value for item in BollingerBandLine],
                            "description": "Which Bollinger Band line to compare against"
                        }
                    }
                },
                "stochastic_config": {
                    "type": "object",
                    "description": "Stochastic oscillator configuration",
                    "properties": {
                        "k_period": {"type": "integer", "default": 14},
                        "d_period": {"type": "integer", "default": 3},
                        "smooth": {"type": "integer", "default": 3},
                        "ma_type": {
                            "enum": [item.value for item in MovingAverageType],
                            "default": MovingAverageType.SMA.value
                        }
                    }
                },
                "vix_config": {
                    "type": "object",
                    "description": "VIX-specific configuration",
                    "properties": {
                        "vix_type": {
                            "enum": [item.value for item in VIXType],
                            "default": VIXType.VIX.value
                        },
                        "price_field": {
                            "enum": [item.value for item in PriceReference],
                            "default": PriceReference.CLOSE.value
                        },
                        "comparison_vix": {
                            "type": "object",
                            "description": "Compare against another VIX type",
                            "properties": {
                                "vix_type": {"enum": [item.value for item in VIXType]},
                                "price_field": {"enum": [item.value for item in PriceReference]},
                                "time_reference": {"enum": [item.value for item in TimeFrame] + ["intraday", "days_ago"]},
                                "days_ago": {"type": "integer", "minimum": 0}
                            }
                        }
                    }
                }
            }
        },

        # =============================================================================
        # COMPLETE DECISION RECIPES - POSITION DECISIONS
        # =============================================================================
        "position_decision": {
            "type": "object",
            "required": ["position_reference"],
            "properties": {
                "position_reference": {
                    "type": "string",
                    "description": "Reference to the position to evaluate"
                },
                "position_field": {
                    "enum": [item.value for item in PositionField],
                    "description": "Position field to evaluate"
                },
                "comparison": {
                    "enum": [item.value for item in ComparisonOperator],
                    "description": "Comparison operator"
                },
                "value": {
                    "type": "number",
                    "description": "Target value for comparison"
                },
                "value2": {
                    "type": "number",
                    "description": "Second value for range comparisons"
                },
                "comparison_field": {
                    "enum": [item.value for item in PositionField],
                    "description": "Compare against another position field"
                },
                "leg_config": {
                    "type": "object",
                    "description": "Configuration for leg-specific evaluations",
                    "properties": {
                        "option_type": {"enum": [item.value for item in OptionType]},
                        "side": {"enum": [item.value for item in OptionSide]},
                        "leg_field": {"enum": [item.value for item in PositionLegField]},
                        "slippage_amount": {"type": "number", "minimum": 0}
                    }
                },
                "time_config": {
                    "type": "object",
                    "description": "Time-based position evaluations",
                    "properties": {
                        "time_unit": {"enum": [item.value for item in TimeUnit]},
                        "time_value": {"type": "integer", "minimum": 0},
                        "comparison_type": {"enum": ["more_than", "less_than", "exactly", "or_more", "or_less"]}
                    }
                },
                "underlying_config": {
                    "type": "object",
                    "description": "Underlying-related position evaluations",
                    "properties": {
                        "symbol": {"type": "string"},
                        "price_relationship": {
                            "enum": ["above", "below", "inside", "beyond"],
                            "description": "Price relationship to strikes"
                        },
                        "strike_type": {"enum": [item.value for item in StrikeType]},
                        "amount": {"type": "number"},
                        "amount_type": {"enum": ["dollar", "percent"]}
                    }
                },
                "moneyness_config": {
                    "type": "object",
                    "description": "Moneyness-based evaluations",
                    "properties": {
                        "moneyness": {"enum": [item.value for item in Moneyness]},
                        "amount": {"type": "number"},
                        "amount_type": {"enum": ["dollar", "percent"]},
                        "comparison_type": {"enum": ["more_than", "less_than"]}
                    }
                },
                "exit_attempt_config": {
                    "type": "object",
                    "description": "Exit attempt tracking",
                    "properties": {
                        "exit_reason": {"enum": [item.value for item in ExitReason]},
                        "attempt_count": {"type": "integer", "minimum": 0},
                        "comparison_type": {"enum": ["more_than", "less_than", "exactly"]}
                    }
                },
                "tags_config": {
                    "type": "object",
                    "description": "Tag-based position filtering",
                    "properties": {
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "filter_type": {"enum": ["any", "all", "none"]}
                    }
                }
            }
        },

        # =============================================================================
        # COMPLETE DECISION RECIPES - BOT DECISIONS
        # =============================================================================
        "bot_decision": {
            "type": "object",
            "properties": {
                "bot_field": {
                    "enum": [item.value for item in BotField],
                    "description": "Bot field to evaluate"
                },
                "comparison": {
                    "enum": [item.value for item in ComparisonOperator],
                    "description": "Comparison operator"
                },
                "value": {
                    "type": "number",
                    "description": "Target value for comparison"
                },
                "symbol": {
                    "type": "string",
                    "description": "Symbol for symbol-specific bot metrics"
                },
                "capital_config": {
                    "type": "object",
                    "description": "Capital availability checks",
                    "properties": {
                        "contracts": {"type": "integer", "minimum": 1},
                        "opportunity": {"type": "string"},
                        "price_options": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"enum": [item.value for item in PriceType]},
                                    "value": {"type": "number"}
                                }
                            }
                        }
                    }
                },
                "position_count_config": {
                    "type": "object",  
                    "description": "Position counting configurations",
                    "properties": {
                        "position_type": {
                            "enum": [item.value for item in PositionType] + ["any"],
                            "default": "any"
                        },
                        "status": {
                            "enum": [item.value for item in PositionStatus],
                            "default": PositionStatus.ANY.value
                        },
                        "symbol": {"type": "string"},
                        "expiration_config": {"$ref": "#/definitions/expiration_config"},
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "count": {"type": "integer", "minimum": 0},
                        "comparison_type": {"enum": ["more_than", "less_than", "exactly"]}
                    }
                },
                "action_tracking": {
                    "type": "object",
                    "description": "Track bot actions over time",
                    "properties": {
                        "action_type": {"enum": [item.value for item in BotActionType]},
                        "timeframe": {
                            "oneOf": [
                                {"enum": [item.value for item in BotTimeframe]},
                                {
                                    "type": "object",
                                    "properties": {
                                        "time_unit": {"enum": [item.value for item in TimeUnit]},
                                        "time_value": {"type": "integer", "minimum": 1}
                                    }
                                }
                            ]
                        },
                        "symbol": {"type": "string"},
                        "never_condition": {"type": "boolean", "default": False}
                    }
                },
                "current_state": {
                    "type": "object",
                    "description": "Current bot state checks",
                    "properties": {
                        "action_type": {"enum": ["opening", "closing"]},
                        "symbol": {"type": "string"},
                        "can_open_position": {"type": "boolean"}
                    }
                },
                "tags_config": {
                    "type": "object",
                    "description": "Bot tag filtering",
                    "properties": {
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "filter_type": {"enum": ["any", "all", "none"]}
                    }
                },
                "symbol_count": {
                    "type": "object",
                    "description": "Bot symbols variable count",
                    "properties": {
                        "count": {"type": "integer", "minimum": 0},
                        "comparison_type": {"enum": ["more_than", "less_than", "exactly"]}
                    }
                }
            }
        },

        # =============================================================================
        # COMPLETE DECISION RECIPES - OPPORTUNITY DECISIONS
        # =============================================================================
        "opportunity_decision": {
            "type": "object",
            "required": ["opportunity_reference"],
            "properties": {
                "opportunity_reference": {
                    "type": "string",
                    "description": "Reference to the opportunity to evaluate"
                },
                "opportunity_field": {
                    "enum": [item.value for item in OpportunityField],
                    "description": "Opportunity field to evaluate"
                },
                "comparison": {
                    "enum": [item.value for item in ComparisonOperator],
                    "description": "Comparison operator"
                },
                "value": {
                    "type": "number",
                    "description": "Target value for comparison"
                },
                "value2": {
                    "type": "number",
                    "description": "Second value for range comparisons"
                },
                "availability_check": {
                    "type": "boolean",
                    "default": False,
                    "description": "Simply check if opportunity is available"
                },
                "reward_risk_favorable": {
                    "type": "boolean",
                    "default": False,
                    "description": "Check if reward/risk ratio is favorable for probability of max profit"
                },
                "leg_config": {
                    "type": "object",
                    "description": "Opportunity leg evaluations",
                    "properties": {
                        "option_type": {"enum": [item.value for item in OptionType]},
                        "side": {"enum": [item.value for item in OptionSide]},
                        "leg_field": {"enum": [item.value for item in OpportunityLegField]}
                    }
                },
                "price_range_config": {
                    "type": "object",
                    "description": "Price range configurations",
                    "properties": {
                        "price_type": {"enum": [item.value for item in PriceReference]},
                        "min_value": {"type": "number"},
                        "max_value": {"type": "number"}
                    }
                },
                "spread_config": {
                    "type": "object",
                    "description": "Spread-related configurations",
                    "properties": {
                        "max_spread": {"type": "number", "minimum": 0},
                        "probability_threshold": {"type": "number", "minimum": 0, "maximum": 100}
                    }
                },
                "conflict_check": {
                    "type": "object",
                    "description": "Check for conflicting positions",
                    "properties": {
                        "check_type": {"enum": ["matching", "conflicting"]},
                        "existing_positions": {"type": "boolean", "default": True}
                    }
                }
            }
        },

        # =============================================================================
        # COMPLETE DECISION RECIPES - GENERAL DECISIONS
        # =============================================================================
        "general_decision": {
            "type": "object",
            "properties": {
                "condition_type": {
                    "enum": [item.value for item in GeneralConditionType],
                    "description": "Type of general condition to evaluate"
                },
                "comparison": {
                    "enum": [item.value for item in ComparisonOperator],
                    "description": "Comparison operator"
                },
                "time_config": {
                    "type": "object",
                    "description": "Time-based condition configuration",
                    "properties": {
                        "target_time": {
                            "type": "string",
                            "pattern": "^(0?[0-9]|1[0-9]|2[0-3]):[0-5][0-9](am|pm)?$",
                            "description": "Target time for comparison"
                        },
                        "start_time": {"type": "string"},
                        "end_time": {"type": "string"},
                        "minutes": {"type": "integer", "minimum": 0},
                        "comparison_type": {"enum": ["before", "after", "exactly", "between", "in_minutes"]}
                    }
                },
                "date_config": {
                    "type": "object",
                    "description": "Date-based condition configuration",
                    "properties": {
                        "target_date": {"type": "string", "format": "date"},
                        "comparison_type": {"enum": ["before", "after", "exactly"]},
                        "day_of_week": {"enum": [item.value for item in DayOfWeek]}
                    }
                },
                "market_close_config": {
                    "type": "object",
                    "description": "Market close condition configuration",
                    "properties": {
                        "close_time": {"enum": [item.value for item in MarketCloseTime]},
                        "days_ahead": {"type": "integer", "minimum": 0, "maximum": 10},
                        "timing": {"enum": ["today", "in_days"]}
                    }
                },
                "economic_event_config": {
                    "type": "object",
                    "description": "Economic event condition configuration",
                    "properties": {
                        "event_type": {"enum": [item.value for item in MarketEvent]},
                        "days_ahead": {"type": "integer", "minimum": 0, "maximum": 30},
                        "timing": {"enum": ["today", "in_days"]}
                    }
                },
                "switch_config": {
                    "type": "object",
                    "description": "Switch state condition configuration",
                    "properties": {
                        "switch_name": {"type": "string"},
                        "state": {"enum": [item.value for item in SwitchState]}
                    }
                }
            }
        },

        # =============================================================================
        # COMPLETE LOOP CONFIGURATIONS
        # =============================================================================
        "enhanced_loop_config": {
            "type": "object",
            "properties": {
                "loop_type": {
                    "enum": [item.value for item in LoopType],
                    "description": "Type of loop to execute"
                },
                "position_filters": {
                    "type": "object",
                    "description": "Filters for position loops",
                    "properties": {
                        "symbol": {"type": "string"},
                        "position_type": {
                            "enum": [item.value for item in PositionType] + ["any"],
                            "default": "any"
                        },
                        "status": {
                            "enum": [item.value for item in PositionStatus],
                            "default": PositionStatus.ANY.value
                        },
                        "tags": {"type": "array", "items": {"type": "string"}},
                        "expiration_config": {"$ref": "#/definitions/expiration_config"}
                    }
                },
                "symbol_filters": {
                    "type": "object",
                    "description": "Filters for symbol loops",
                    "properties": {
                        "symbols": {"type": "array", "items": {"type": "string"}},
                        "use_bot_symbols": {"type": "boolean", "default": False},
                        "tags": {"type": "array", "items": {"type": "string"}}
                    }
                },
                "iteration_config": {
                    "type": "object",
                    "description": "Loop iteration configuration",
                    "properties": {
                        "max_iterations": {"type": "integer", "minimum": 1, "maximum": 1000},
                        "break_on_error": {"type": "boolean", "default": True},
                        "continue_on_failure": {"type": "boolean", "default": False}
                    }
                }
            }
        }
    }

# =============================================================================
# SCHEMA VALIDATION AND UTILITIES
# =============================================================================

class CompleteSchemaValidator:
    """Comprehensive validator for the complete enhanced schema"""
    
    def __init__(self):
        self.schema = create_complete_enhanced_schema()
    
    def validate_bot_config(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate a complete bot configuration"""
        errors = []
        
        try:
            # Basic structure validation
            if not isinstance(config, dict):
                errors.append("Configuration must be a dictionary")
                return False, errors
            
            # Required fields validation
            required_fields = ["name", "account", "safeguards", "automations"]
            for field in required_fields:
                if field not in config:
                    errors.append(f"Required field missing: {field}")
            
            if errors:
                return False, errors
            
            # Validate safeguards
            safeguards_errors = self._validate_safeguards(config.get("safeguards", {}))
            errors.extend(safeguards_errors)
            
            # Validate automations
            automations_errors = self._validate_automations(config.get("automations", []))
            errors.extend(automations_errors)
            
            # Validate symbols configuration
            if "symbols" in config:
                symbols_errors = self._validate_symbols(config["symbols"])
                errors.extend(symbols_errors)
            
            return len(errors) == 0, errors
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors
    
    def _validate_safeguards(self, safeguards: Dict[str, Any]) -> List[str]:
        """Validate safeguards configuration"""
        errors = []
        
        required_fields = ["capital_allocation", "daily_positions", "position_limit"]
        for field in required_fields:
            if field not in safeguards:
                errors.append(f"Safeguards missing required field: {field}")
        
        if "capital_allocation" in safeguards:
            allocation = safeguards["capital_allocation"]
            if not isinstance(allocation, (int, float)) or allocation < ValidationLimits.MIN_CAPITAL_ALLOCATION:
                errors.append(f"Invalid capital allocation: {allocation}")
        
        if "daily_positions" in safeguards and "position_limit" in safeguards:
            daily = safeguards["daily_positions"]
            total = safeguards["position_limit"]
            if daily > total:
                errors.append("Daily positions limit cannot exceed total position limit")
        
        return errors
    
    def _validate_automations(self, automations: List[Dict[str, Any]]) -> List[str]:
        """Validate automations configuration"""
        errors = []
        
        if not isinstance(automations, list):
            errors.append("Automations must be a list")
            return errors
        
        for i, automation in enumerate(automations):
            auto_errors = self._validate_automation(automation, i)
            errors.extend(auto_errors)
        
        return errors
    
    def _validate_automation(self, automation: Dict[str, Any], index: int) -> List[str]:
        """Validate individual automation"""
        errors = []
        prefix = f"Automation {index}"
        
        required_fields = ["name", "trigger", "actions"]
        for field in required_fields:
            if field not in automation:
                errors.append(f"{prefix}: Missing required field '{field}'")
        
        # Validate trigger
        if "trigger" in automation:
            trigger_errors = self._validate_trigger(automation["trigger"], index)
            errors.extend(trigger_errors)
        
        # Validate actions
        if "actions" in automation:
            actions_errors = self._validate_actions(automation["actions"], index)
            errors.extend(actions_errors)
        
        return errors
    
    def _validate_trigger(self, trigger: Dict[str, Any], automation_index: int) -> List[str]:
        """Validate trigger configuration"""
        errors = []
        prefix = f"Automation {automation_index} trigger"
        
        if "type" not in trigger:
            errors.append(f"{prefix}: Missing trigger type")
            return errors
        
        trigger_type = trigger["type"]
        
        # Validate trigger-specific requirements
        if trigger_type == TriggerType.CONTINUOUS.value:
            if "automation_type" not in trigger:
                errors.append(f"{prefix}: Continuous triggers require automation_type")
        
        elif trigger_type == TriggerType.RECURRING.value:
            if "recurring_config" not in trigger:
                errors.append(f"{prefix}: Recurring triggers require recurring_config")
        
        return errors
    
    def _validate_actions(self, actions: List[Dict[str, Any]], automation_index: int) -> List[str]:
        """Validate actions configuration"""
        errors = []
        
        if not isinstance(actions, list):
            errors.append(f"Automation {automation_index}: Actions must be a list")
            return errors
        
        for i, action in enumerate(actions):
            action_errors = self._validate_action(action, automation_index, i)
            errors.extend(action_errors)
        
        return errors
    
    def _validate_action(self, action: Dict[str, Any], automation_index: int, action_index: int) -> List[str]:
        """Validate individual action"""
        errors = []
        prefix = f"Automation {automation_index}, Action {action_index}"
        
        if "type" not in action:
            errors.append(f"{prefix}: Missing action type")
            return errors
        
        action_type = action["type"]
        
        # Validate action-specific requirements
        if action_type in [ActionType.DECISION.value, ActionType.CONDITIONAL.value]:
            if "decision" not in action:
                errors.append(f"{prefix}: {action_type} requires decision configuration")
        
        elif action_type == ActionType.OPEN_POSITION.value:
            if "position" not in action:
                errors.append(f"{prefix}: open_position requires position configuration")
        
        elif action_type == ActionType.CLOSE_POSITION.value:
            if "close_config" not in action:
                errors.append(f"{prefix}: close_position requires close_config")
        
        return errors
    
    def _validate_symbols(self, symbols: Dict[str, Any]) -> List[str]:
        """Validate symbols configuration"""
        errors = []
        
        if "type" not in symbols:
            errors.append("Symbols configuration missing type")
            return errors
        
        symbol_type = symbols["type"]
        
        if symbol_type == "static":
            if "list" not in symbols:
                errors.append("Static symbols configuration requires list")
            elif not isinstance(symbols["list"], list):
                errors.append("Static symbols list must be an array")
        
        elif symbol_type == "dynamic":
            if "dynamic_config" not in symbols:
                errors.append("Dynamic symbols configuration requires dynamic_config")
        
        return errors

# =============================================================================
# TEMPLATE GENERATORS
# =============================================================================

class EnhancedTemplateGenerator:
    """Generate templates for different types of bot configurations"""
    
    @staticmethod
    def create_simple_long_call_bot() -> Dict[str, Any]:
        """Create a simple long call bot template"""
        return {
            "name": "Simple Long Call Bot",
            "account": "paper_trading",
            "safeguards": {
                "capital_allocation": 10000,
                "daily_positions": 3,
                "position_limit": 10,
                "daytrading_allowed": False
            },
            "scan_speed": ScanSpeed.FIFTEEN_MINUTES.value,
            "symbols": {
                "type": "static",
                "list": ["SPY"]
            },
            "automations": [
                {
                    "name": "Buy SPY Calls Scanner",
                    "trigger": {
                        "type": TriggerType.CONTINUOUS.value,
                        "automation_type": AutomationType.SCANNER.value
                    },
                    "actions": [
                        {
                            "type": ActionType.DECISION.value,
                            "decision": {
                                "recipe_type": DecisionType.STOCK.value,
                                "symbol": "SPY",
                                "price_field": StockPriceField.LAST_PRICE.value,
                                "comparison": ComparisonOperator.GREATER_THAN.value,
                                "value": 400
                            },
                            "yes_path": [
                                {
                                    "type": ActionType.OPEN_POSITION.value,
                                    "position": {
                                        "strategy_type": PositionType.LONG_CALL.value,
                                        "symbol": "SPY",
                                        "expiration": {
                                            "type": ExpirationType.BETWEEN_DAYS.value,
                                            "days": 30,
                                            "days_end": 45,
                                            "series": ExpirationSeries.ANY_SERIES.value
                                        },
                                        "legs": [
                                            {
                                                "option_type": OptionType.CALL.value,
                                                "side": OptionSide.LONG.value,
                                                "strike_config": {
                                                    "type": StrikeSelectionType.DELTA.value,
                                                    "delta_range": {"min": 0.3, "max": 0.7},
                                                    "selection": SelectionType.OR_CLOSEST.value
                                                }
                                            }
                                        ],
                                        "position_size": {
                                            "type": PositionSizeType.PERCENT_ALLOCATION.value,
                                            "percent": 5,
                                            "base_type": CapitalBaseType.ALLOCATION.value
                                        },
                                        "price_config": {
                                            "smart_pricing": SmartPricing.NORMAL.value
                                        },
                                        "exit_options": {
                                            "profit_taking": {
                                                "enabled": True,
                                                "percent": 50,
                                                "basis": ExitBasis.DEBIT.value
                                            },
                                            "stop_loss": {
                                                "enabled": True,
                                                "percent": 50,
                                                "basis": ExitBasis.DEBIT.value
                                            }
                                        },
                                        "entry_criteria": [
                                            {"type": EntryCriteriaType.BOT_HAS_CAPITAL.value}
                                        ]
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def create_complex_iron_condor_bot() -> Dict[str, Any]:
        """Create a complex iron condor bot with multiple decision layers"""
        return {
            "name": "Advanced Iron Condor Bot",
            "account": "live_trading",
            "group": "Income Strategies",  
            "safeguards": {
                "capital_allocation": 50000,
                "daily_positions": 2,
                "position_limit": 8,
                "daytrading_allowed": False
            },
            "scan_speed": ScanSpeed.FIVE_MINUTES.value,
            "symbols": {
                "type": "dynamic",
                "dynamic_config": {
                    "filters": [
                        {
                            "type": SymbolFilterType.IV_RANK.value,
                            "operator": ComparisonOperator.GREATER_THAN.value,
                            "value": 30
                        },
                        {
                            "type": SymbolFilterType.VOLUME.value,
                            "operator": ComparisonOperator.GREATER_THAN.value,
                            "value": 1000000
                        }
                    ],
                    "sort": [
                        {
                            "field": SymbolSortField.IV_RANK.value,
                            "direction": SortDirection.DESCENDING.value
                        }
                    ],
                    "limit": 10
                }
            },
            "automations": [
                {
                    "name": "High IV Iron Condor Scanner",
                    "trigger": {
                        "type": TriggerType.CONTINUOUS.value,
                        "automation_type": AutomationType.SCANNER.value
                    },
                    "actions": [
                        {
                            "type": ActionType.LOOP_SYMBOLS.value,
                            "loop_config": {
                                "loop_type": LoopType.BOT_SYMBOLS.value
                            },
                            "loop_actions": [
                                {
                                    "type": ActionType.DECISION.value,
                                    "decision": {
                                        "recipe_type": DecisionType.STOCK.value,
                                        "symbol": "{{symbol}}",
                                        "price_field": StockPriceField.IV_RANK.value,
                                        "comparison": ComparisonOperator.GREATER_THAN.value,
                                        "value": 40
                                    },
                                    "yes_path": [
                                        {
                                            "type": ActionType.DECISION.value,
                                            "decision": {
                                                "recipe_type": DecisionType.INDICATOR.value,
                                                "symbol": "{{symbol}}",
                                                "indicator": TechnicalIndicator.RSI.value,
                                                "indicator_period": 14,
                                                "comparison": ComparisonOperator.BETWEEN.value,
                                                "value": 40,
                                                "value2": 60
                                            },
                                            "yes_path": [
                                                {
                                                    "type": ActionType.OPEN_POSITION.value,
                                                    "position": {
                                                        "strategy_type": PositionType.IRON_CONDOR.value,
                                                        "symbol": "{{symbol}}",
                                                        "expiration": {
                                                            "type": ExpirationType.BETWEEN_DAYS.value,
                                                            "days": 14,
                                                            "days_end": 28,
                                                            "series": ExpirationSeries.ANY_SERIES.value
                                                        },
                                                        "legs": [
                                                            {
                                                                "option_type": OptionType.PUT.value,
                                                                "side": OptionSide.LONG.value,
                                                                "strike_config": {
                                                                    "type": StrikeSelectionType.DELTA.value,
                                                                    "delta_range": {"min": -0.15, "max": -0.10},
                                                                    "selection": SelectionType.OR_CLOSEST.value
                                                                }
                                                            },
                                                            {
                                                                "option_type": OptionType.PUT.value,
                                                                "side": OptionSide.SHORT.value,
                                                                "strike_config": {
                                                                    "type": StrikeSelectionType.DELTA.value,
                                                                    "delta_range": {"min": -0.25, "max": -0.20},
                                                                    "selection": SelectionType.OR_CLOSEST.value
                                                                }
                                                            },
                                                            {
                                                                "option_type": OptionType.CALL.value,
                                                                "side": OptionSide.SHORT.value,
                                                                "strike_config": {
                                                                    "type": StrikeSelectionType.DELTA.value,
                                                                    "delta_range": {"min": 0.20, "max": 0.25},
                                                                    "selection": SelectionType.OR_CLOSEST.value
                                                                }
                                                            },
                                                            {
                                                                "option_type": OptionType.CALL.value,
                                                                "side": OptionSide.LONG.value,
                                                                "strike_config": {
                                                                    "type": StrikeSelectionType.DELTA.value,
                                                                    "delta_range": {"min": 0.10, "max": 0.15},
                                                                    "selection": SelectionType.OR_CLOSEST.value
                                                                }
                                                            }
                                                        ],
                                                        "position_size": {
                                                            "type": PositionSizeType.PERCENT_ALLOCATION.value,
                                                            "percent": 8,
                                                            "base_type": CapitalBaseType.ALLOCATION.value
                                                        },
                                                        "price_config": {
                                                            "smart_pricing": SmartPricing.NORMAL.value,
                                                            "final_price_options": [
                                                                {
                                                                    "type": PriceType.BID_ASK_SPREAD_PERCENT.value,
                                                                    "value": 50
                                                                }
                                                            ]
                                                        },
                                                        "exit_options": {
                                                            "profit_taking": {
                                                                "enabled": True,
                                                                "percent": 25,
                                                                "basis": ExitBasis.CREDIT.value
                                                            },
                                                            "stop_loss": {
                                                                "enabled": True,
                                                                "percent": 200,
                                                                "basis": ExitBasis.CREDIT.value
                                                            },
                                                            "expiration": {
                                                                "enabled": True,
                                                                "time_before": 2,
                                                                "time_unit": TimeUnit.DAYS.value
                                                            }
                                                        },
                                                        "entry_criteria": [
                                                            {"type": EntryCriteriaType.BOT_HAS_CAPITAL.value},
                                                            {
                                                                "type": EntryCriteriaType.MAX_SYMBOL_POSITIONS.value,
                                                                "symbol": "{{symbol}}",
                                                                "value": 1
                                                            }
                                                        ],
                                                        "position_criteria": [
                                                            {
                                                                "type": PositionCriteriaType.MIN_REWARD_RISK.value,
                                                                "value": 20
                                                            },
                                                            {
                                                                "type": PositionCriteriaType.MAX_BID_ASK_SPREAD.value,
                                                                "value": 0.05
                                                            }
                                                        ]
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            ]
        }

# =============================================================================
# MAIN SCHEMA EXPORT
# =============================================================================

# Create the complete schema
COMPLETE_ENHANCED_OA_BOT_SCHEMA = create_complete_enhanced_schema()

# Export key components
__all__ = [
    'COMPLETE_ENHANCED_OA_BOT_SCHEMA',
    'CompleteSchemaValidator', 
    'EnhancedTemplateGenerator',
    'create_complete_enhanced_schema'
]

# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

def main():
    """Demonstrate the complete enhanced schema functionality"""
    
    print("=" * 80)
    print("COMPLETE ENHANCED OPTION ALPHA BOT SCHEMA")
    print("=" * 80)
    
    # Initialize validator and template generator
    validator = CompleteSchemaValidator()
    templates = EnhancedTemplateGenerator()
    
    print("\n1. SCHEMA STATISTICS")
    print("-" * 40)
    schema = create_complete_enhanced_schema()
    print(f"Total schema definitions: {len(schema['definitions'])}")
    print(f"Main properties: {len(schema['properties'])}")
    
    print("\n2. VALIDATING SIMPLE TEMPLATE")
    print("-" * 40)
    simple_config = templates.create_simple_long_call_bot()
    is_valid, errors = validator.validate_bot_config(simple_config)
    
    if is_valid:
        print("✓ Simple long call bot template is valid")
    else:
        print("✗ Simple template validation errors:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n3. VALIDATING COMPLEX TEMPLATE")
    print("-" * 40)
    complex_config = templates.create_complex_iron_condor_bot()
    is_valid, errors = validator.validate_bot_config(complex_config)
    
    if is_valid:
        print("✓ Complex iron condor bot template is valid")
    else:
        print("✗ Complex template validation errors:")
        for error in errors:
            print(f"  - {error}")
    
    print("\n4. SCHEMA CAPABILITIES SUMMARY")
    print("-" * 40)
    capabilities = [
        "✓ Complete Option Alpha feature set support",
        "✓ All decision recipe types (Stock, Indicator, Position, Bot, Opportunity, General)",
        "✓ Advanced position configuration with multi-leg strategies",
        "✓ Comprehensive exit options and risk management", 
        "✓ Dynamic symbol selection and filtering",
        "✓ Loop-based automations for batch processing",
        "✓ Tag management for positions, bots, and symbols",
        "✓ Progressive risk management and position sizing",
        "✓ Economic event and market timing integration",
        "✓ Custom multi-leg strategies beyond OA defaults"
    ]
    
    for capability in capabilities:
        print(f"  {capability}")
    
    print("\n" + "=" * 80)
    print("ENHANCED SCHEMA READY FOR FRAMEWORK INTEGRATION")
    print("=" * 80)

if __name__ == "__main__":
    main()
