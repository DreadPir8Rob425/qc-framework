# Enhanced Option Alpha Bot Schema - Position Configuration Schemas
# Complete schemas for position opening, closing, and management

from typing import Dict, Any, List
from position_configuration_enums import *
from enhanced_bot_schema_enums import *

# =============================================================================
# POSITION CONFIGURATION SCHEMAS
# =============================================================================

POSITION_SCHEMAS = {
    # =============================================================================
    # MAIN POSITION CONFIGURATION
    # =============================================================================
    "position_config": {
        "type": "object",
        "required": ["strategy_type", "symbol"],
        "properties": {
            "strategy_type": {
                "enum": [item.value for item in PositionType],
                "description": "Type of position strategy to execute"
            },
            "symbol": {
                "type": "string",
                "maxLength": ValidationLimits.MAX_SYMBOL_LENGTH,
                "description": "Underlying symbol for the position"
            },
            "expiration": {
                "$ref": "#/definitions/expiration_config",
                "description": "Expiration configuration for options positions"
            },
            "legs": {
                "type": "array",
                "items": {"$ref": "#/definitions/leg_config"},
                "description": "Individual option legs for multi-leg strategies"
            },
            "position_size": {
                "$ref": "#/definitions/position_size_config",
                "description": "Position sizing configuration"
            },
            "price_config": {
                "$ref": "#/definitions/price_config",
                "description": "Pricing and execution configuration"
            },
            "exit_options": {
                "$ref": "#/definitions/exit_options",
                "description": "Automated exit criteria"
            },
            "entry_criteria": {
                "type": "array",
                "items": {"$ref": "#/definitions/entry_criteria"},
                "description": "Filters to allow/prevent opening positions"
            },
            "position_criteria": {
                "type": "array", 
                "items": {"$ref": "#/definitions/position_criteria"},
                "description": "Opportunity-specific filters"
            },
            "tags": {
                "type": "array",
                "items": {
                    "type": "string",
                    "maxLength": ValidationLimits.MAX_TAG_LENGTH
                },
                "maxItems": ValidationLimits.MAX_TAGS_PER_ITEM,
                "description": "Tags to apply to the position"
            }
        },
        # Dynamic requirements based on strategy type
        "allOf": [
            {
                "if": {"properties": {"strategy_type": {"enum": [
                    PositionType.LONG_CALL.value, PositionType.LONG_PUT.value
                ]}}},
                "then": {
                    "required": ["expiration"],
                    "properties": {
                        "legs": {
                            "minItems": 1,
                            "maxItems": 1
                        }
                    }
                }
            },
            {
                "if": {"properties": {"strategy_type": {"enum": [
                    PositionType.LONG_CALL_SPREAD.value, PositionType.LONG_PUT_SPREAD.value,
                    PositionType.SHORT_CALL_SPREAD.value, PositionType.SHORT_PUT_SPREAD.value
                ]}}},
                "then": {
                    "required": ["expiration"],
                    "properties": {
                        "legs": {
                            "minItems": 2,
                            "maxItems": 2
                        }
                    }
                }
            },
            {
                "if": {"properties": {"strategy_type": {"enum": [
                    PositionType.IRON_CONDOR.value, PositionType.IRON_BUTTERFLY.value
                ]}}},
                "then": {
                    "required": ["expiration"],
                    "properties": {
                        "legs": {
                            "minItems": 4,
                            "maxItems": 4
                        }
                    }
                }
            }
        ]
    },

    # =============================================================================
    # EXPIRATION CONFIGURATION
    # =============================================================================
    "expiration_config": {
        "type": "object",
        "required": ["type"],
        "properties": {
            "type": {
                "enum": [item.value for item in ExpirationType],
                "description": "Method for selecting expiration"
            },
            "days": {
                "type": "integer",
                "minimum": ValidationLimits.MIN_EXPIRATION_DAYS,
                "maximum": ValidationLimits.MAX_EXPIRATION_DAYS,
                "description": "Number of days for expiration selection"
            },
            "days_end": {
                "type": "integer",
                "minimum": ValidationLimits.MIN_EXPIRATION_DAYS,
                "maximum": ValidationLimits.MAX_EXPIRATION_DAYS,
                "description": "End range for 'between_days' expiration type"
            },
            "series": {
                "enum": [item.value for item in ExpirationSeries],
                "default": ExpirationSeries.ANY_SERIES.value,
                "description": "Expiration series preference"
            },
            "date": {
                "type": "string",
                "format": "date",
                "description": "Specific expiration date (for 'on_or_after' type)"
            },
            "same_as_position": {
                "type": "string",
                "description": "Position reference to match expiration (for 'same_as_position' type)"
            }
        },
        "allOf": [
            {
                "if": {"properties": {"type": {"const": ExpirationType.EXACTLY_DAYS.value}}},
                "then": {"required": ["days"]}
            },
            {
                "if": {"properties": {"type": {"const": ExpirationType.AT_LEAST_DAYS.value}}},
                "then": {"required": ["days"]}
            },
            {
                "if": {"properties": {"type": {"const": ExpirationType.BETWEEN_DAYS.value}}},
                "then": {"required": ["days", "days_end"]}
            },
            {
                "if": {"properties": {"type": {"const": ExpirationType.ON_OR_AFTER.value}}},
                "then": {"required": ["date"]}
            },
            {
                "if": {"properties": {"type": {"const": ExpirationType.SAME_AS_POSITION.value}}},
                "then": {"required": ["same_as_position"]}
            }
        ]
    },

    # =============================================================================
    # LEG CONFIGURATION
    # =============================================================================
    "leg_config": {
        "type": "object",
        "required": ["option_type", "side", "strike_config"],
        "properties": {
            "option_type": {
                "enum": [item.value for item in OptionType],
                "description": "Call or Put"
            },
            "side": {
                "enum": [item.value for item in OptionSide],
                "description": "Long or Short"
            },
            "strike_config": {
                "$ref": "#/definitions/strike_config",
                "description": "Strike price selection configuration"
            },
            "quantity": {
                "type": "integer",
                "minimum": 1,
                "maximum": ValidationLimits.MAX_POSITION_SIZE_CONTRACTS,
                "description": "Number of contracts for this leg"
            }
        }
    },

    # =============================================================================
    # STRIKE CONFIGURATION
    # =============================================================================
    "strike_config": {
        "type": "object",
        "required": ["type"],
        "properties": {
            "type": {
                "enum": [item.value for item in StrikeSelectionType],
                "description": "Method for selecting strike price"
            },
            "value": {
                "type": "number",
                "description": "Target value (delta, price, etc.)"
            },
            "delta_range": {
                "type": "object",
                "properties": {
                    "min": {
                        "type": "number",
                        "minimum": ValidationLimits.MIN_DELTA,
                        "maximum": ValidationLimits.MAX_DELTA
                    },
                    "max": {
                        "type": "number", 
                        "minimum": ValidationLimits.MIN_DELTA,
                        "maximum": ValidationLimits.MAX_DELTA
                    }
                },
                "description": "Delta range for delta-based strike selection"
            },
            "selection": {
                "enum": [item.value for item in SelectionType],
                "default": SelectionType.OR_CLOSEST.value,
                "description": "Selection method when exact target not available"
            },
            "price_type": {
                "enum": [item.value for item in PriceReference],
                "description": "Price type for price-based strike selection"
            },
            "relative_config": {
                "type": "object",
                "description": "Configuration for relative strike selection",
                "properties": {
                    "reference_type": {
                        "enum": ["underlying_price", "underlying_open", "leg", "position"]
                    },
                    "reference_leg": {
                        "type": "object",
                        "properties": {
                            "option_type": {"enum": [item.value for item in OptionType]},
                            "side": {"enum": [item.value for item in OptionSide]}
                        }
                    },
                    "reference_position": {"type": "string"},
                    "amount": {"type": "number"},
                    "amount_type": {"enum": ["dollar", "percent"]},
                    "direction": {"enum": [item.value for item in DirectionType]}
                }
            },
            "std_dev_config": {
                "type": "object",
                "description": "Standard deviation configuration",
                "properties": {
                    "std_devs": {"type": "number"},
                    "direction": {"enum": [item.value for item in DirectionType]},
                    "reference_price": {"enum": [item.value for item in PriceReference]}
                }
            },
            "expected_move_config": {
                "type": "object",
                "description": "Expected move configuration",
                "properties": {
                    "direction": {"enum": [item.value for item in ExpectedMoveDirection]},
                    "amount": {"type": "number"},
                    "amount_type": {"enum": ["dollar", "percent"]}
                }
            }
        },
        "allOf": [
            {
                "if": {"properties": {"type": {"const": StrikeSelectionType.DELTA.value}}},
                "then": {
                    "anyOf": [
                        {"required": ["value"]},
                        {"required": ["delta_range"]}
                    ]
                }
            },
            {
                "if": {"properties": {"type": {"enum": [
                    StrikeSelectionType.STRIKE_PRICE.value,
                    StrikeSelectionType.PRICE_TARGET.value
                ]}}},
                "then": {"required": ["value"]}
            },
            {
                "if": {"properties": {"type": {"enum": [
                    StrikeSelectionType.RELATIVE_UNDERLYING.value,
                    StrikeSelectionType.RELATIVE_LEG.value
                ]}}},
                "then": {"required": ["relative_config"]}
            },
            {
                "if": {"properties": {"type": {"const": StrikeSelectionType.STD_DEV.value}}},
                "then": {"required": ["std_dev_config"]}
            },
            {
                "if": {"properties": {"type": {"const": StrikeSelectionType.EXPECTED_MOVE.value}}},
                "then": {"required": ["expected_move_config"]}
            }
        ]
    },

    # =============================================================================
    # POSITION SIZE CONFIGURATION
    # =============================================================================
    "position_size_config": {
        "type": "object",
        "required": ["type"],
        "properties": {
            "type": {
                "enum": [item.value for item in PositionSizeType],
                "description": "Method for determining position size"
            },
            "contracts": {
                "type": "integer",
                "minimum": 1,
                "maximum": ValidationLimits.MAX_POSITION_SIZE_CONTRACTS,
                "description": "Fixed number of contracts"
            },
            "risk_amount": {
                "type": "number",
                "minimum": 0,
                "maximum": ValidationLimits.MAX_RISK_AMOUNT,
                "description": "Maximum risk amount in dollars"
            },
            "percent": {
                "type": "number",
                "minimum": 0,
                "maximum": ValidationLimits.MAX_POSITION_SIZE_PERCENT,
                "description": "Percentage of base amount"
            },
            "base_type": {
                "enum": [item.value for item in CapitalBaseType],
                "description": "Base for percentage calculations"
            },
            "max_amount": {
                "type": "number",
                "minimum": 0,
                "description": "Maximum amount for percent_with_max type"
            },
            "reference_position": {
                "type": "string",
                "description": "Position reference for same_as_position type"
            },
            "progressive_config": {
                "type": "object",
                "description": "Progressive risk configuration",
                "properties": {
                    "start_amount": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Starting risk amount"
                    },
                    "end_amount": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Maximum risk amount"
                    },
                    "increment_amount": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Amount to increment by"
                    },
                    "increment_type": {
                        "enum": [item.value for item in ProgressiveRiskType],
                        "description": "Type of increment (increase or double)"
                    },
                    "trigger": {
                        "enum": [item.value for item in ProgressiveRiskTrigger],
                        "description": "What triggers the progression"
                    },
                    "trigger_count": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Number of triggers needed for progression"
                    }
                }
            }
        },
        "allOf": [
            {
                "if": {"properties": {"type": {"const": PositionSizeType.CONTRACTS.value}}},
                "then": {"required": ["contracts"]}
            },
            {
                "if": {"properties": {"type": {"const": PositionSizeType.RISK_AMOUNT.value}}},
                "then": {"required": ["risk_amount"]}
            },
            {
                "if": {"properties": {"type": {"enum": [
                    PositionSizeType.PERCENT_ALLOCATION.value,
                    PositionSizeType.PERCENT_WITH_MAX.value
                ]}}},
                "then": {"required": ["percent", "base_type"]}
            },
            {
                "if": {"properties": {"type": {"const": PositionSizeType.PERCENT_WITH_MAX.value}}},
                "then": {"required": ["max_amount"]}
            },
            {
                "if": {"properties": {"type": {"const": PositionSizeType.SAME_AS_POSITION.value}}},
                "then": {"required": ["reference_position"]}
            },
            {
                "if": {"properties": {"type": {"const": PositionSizeType.PROGRESSIVE_RISK.value}}},
                "then": {"required": ["progressive_config"]}
            }
        ]
    },

    # =============================================================================
    # PRICE CONFIGURATION
    # =============================================================================
    "price_config": {
        "type": "object",
        "properties": {
            "smart_pricing": {
                "enum": [item.value for item in SmartPricing],
                "default": SmartPricing.NORMAL.value,
                "description": "SmartPricing execution method"
            },
            "final_price_options": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["type", "value"],
                    "properties": {
                        "type": {
                            "enum": [item.value for item in PriceType],
                            "description": "Type of price adjustment"
                        },
                        "value": {
                            "type": "number",
                            "description": "Value for the price adjustment"
                        }
                    }
                },
                "description": "Final price adjustment options (can select multiple)"
            }
        }
    },

    # =============================================================================
    # EXIT OPTIONS CONFIGURATION
    # =============================================================================
    "exit_options": {
        "type": "object",
        "description": "Automated exit criteria checked every minute during market hours",
        "properties": {
            "profit_taking": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": False},
                    "percent": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": ValidationLimits.MAX_PERCENTAGE,
                        "description": "Profit percentage threshold"
                    },
                    "basis": {
                        "enum": [item.value for item in ExitBasis],
                        "description": "Basis for profit calculation (credit/debit)"
                    }
                }
            },
            "price_target": {
                "type": "object", 
                "properties": {
                    "enabled": {"type": "boolean", "default": False},
                    "amount": {
                        "type": "number",
                        "description": "Target price amount"
                    },
                    "direction": {
                        "enum": [item.value for item in DirectionType],
                        "description": "Direction for price target (or_higher/or_lower)"
                    }
                }
            },
            "stop_loss": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": False},
                    "percent": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": ValidationLimits.MAX_PERCENTAGE,
                        "description": "Stop loss percentage"
                    },
                    "basis": {
                        "enum": [item.value for item in ExitBasis],
                        "description": "Basis for stop loss calculation"
                    }
                }
            },
            "trailing_stop": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": False},
                    "activate_at_percent": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Profit percent to activate trailing stop"
                    },
                    "pullback_percent": {
                        "type": "number", 
                        "minimum": 0,
                        "maximum": 100,
                        "description": "Pullback percent to trigger exit"
                    },
                    "disable_conditions": {
                        "type": "object",
                        "description": "Conditions to disable trailing stop",
                        "properties": {
                            "return_threshold": {
                                "type": "number",
                                "description": "Disable if return % less than this"
                            },
                            "pullback_threshold": {
                                "type": "number",
                                "description": "Disable if pullback more than this"
                            }
                        }
                    }
                }
            },
            "touch": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": False},
                    "amount": {
                        "type": "number",
                        "description": "Touch amount (positive or negative)"
                    },
                    "from_itm": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether touch amount is from ITM"
                    }
                }
            },
            "expiration": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": False},
                    "time_before": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Time before expiration to exit"
                    },
                    "time_unit": {
                        "enum": [item.value for item in TimeUnit],
                        "description": "Unit for time_before"
                    }
                }
            },
            "earnings": {
                "type": "object",
                "properties": {
                    "enabled": {"type": "boolean", "default": False},
                    "days_before": {
                        "type": "integer",
                        "minimum": 1,
                        "description": "Days before earnings to exit"
                    }
                }
            },
            "additional_options": {
                "type": "object",
                "description": "Additional exit option settings",
                "properties": {
                    "avoid_pdt": {
                        "type": "boolean",
                        "default": False,
                        "description": "Wait at least 1 day to avoid pattern day trading"
                    },
                    "max_bid_ask_spread": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Disable exits if bid/ask spread exceeds this amount"
                    }
                }
            }
        }
    },

    # =============================================================================
    # ENTRY CRITERIA CONFIGURATION
    # =============================================================================
    "entry_criteria": {
        "type": "object",
        "required": ["type"],
        "properties": {
            "type": {
                "enum": [item.value for item in EntryCriteriaType],
                "description": "Type of entry criteria filter"
            },
            "value": {
                "type": "number",
                "description": "Threshold value for criteria"
            },
            "value2": {
                "type": "number",
                "description": "Second value for range criteria"
            },
            "symbol": {
                "type": "string",
                "description": "Symbol for symbol-specific criteria"
            }
        },
        "allOf": [
            {
                "if": {"properties": {"type": {"enum": [
                    EntryCriteriaType.MAX_OPEN_POSITIONS.value,
                    EntryCriteriaType.MAX_DAILY_POSITIONS.value,
                    EntryCriteriaType.MAX_SYMBOL_POSITIONS.value
                ]}}},
                "then": {"required": ["value"]}
            },
            {
                "if": {"properties": {"type": {"enum": [
                    EntryCriteriaType.VIX_RANGE.value,
                    EntryCriteriaType.IV_RANK_RANGE.value
                ]}}},
                "then": {"required": ["value", "value2"]}
            },
            {
                "if": {"properties": {"type": {"const": EntryCriteriaType.MAX_SYMBOL_POSITIONS.value}}},
                "then": {"required": ["symbol"]}
            }
        ]
    },

    # =============================================================================
    # POSITION CRITERIA CONFIGURATION
    # =============================================================================
    "position_criteria": {
        "type": "object",
        "required": ["type"],
        "properties": {
            "type": {
                "enum": [item.value for item in PositionCriteriaType],
                "description": "Type of position criteria filter"
            },
            "value": {
                "type": "number",
                "description": "Threshold value for criteria"
            },
            "value2": {
                "type": "number",
                "description": "Second value for range criteria"
            }
        },
        "allOf": [
            {
                "if": {"properties": {"type": {"enum": [
                    PositionCriteriaType.PRICE_RANGE.value,
                    PositionCriteriaType.SPREAD_RANGE.value
                ]}}},
                "then": {"required": ["value", "value2"]}
            },
            {
                "if": {"properties": {"type": {"not": {"enum": [
                    PositionCriteriaType.BEFORE_EARNINGS.value,
                    PositionCriteriaType.BEFORE_FOMC.value,
                    PositionCriteriaType.BEFORE_EX_DIVIDEND.value,
                    PositionCriteriaType.REWARD_RISK_FAVORABLE.value
                ]}}}},
                "then": {"required": ["value"]}
            }
        ]
    },

    # =============================================================================
    # CLOSE POSITION CONFIGURATION
    # =============================================================================
    "close_config": {
        "type": "object",
        "required": ["position", "price_config"],
        "properties": {
            "position": {
                "type": "string",
                "description": "Position reference to close"
            },
            "price_config": {
                "$ref": "#/definitions/price_config",
                "description": "Pricing configuration for close order"
            },
            "quantity": {
                "type": "object",
                "description": "Quantity to close (partial close support)",
                "properties": {
                    "type": {
                        "enum": [item.value for item in CloseQuantityType],
                        "description": "Type of quantity specification"
                    },
                    "amount": {
                        "type": "number",
                        "minimum": 0,
                        "description": "Amount to close"
                    }
                }
            },
            "memo": {
                "type": "string",
                "maxLength": 500,
                "description": "Optional memo for the close order"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags to add to position after close"
            },
            "discard_otm_long_legs": {
                "type": "boolean",
                "default": False,
                "description": "Discard expiring OTM long legs with no bid price"
            }
        }
    }
}

# =============================================================================
# POSITION TEMPLATE GENERATORS
# =============================================================================

def create_position_template(strategy_type: PositionType) -> Dict[str, Any]:
    """Create a template position configuration for a given strategy type"""
    
    base_template = {
        "strategy_type": strategy_type.value,
        "symbol": "SPY",
        "position_size": {
            "type": PositionSizeType.PERCENT_ALLOCATION.value,
            "percent": 5,
            "base_type": CapitalBaseType.ALLOCATION.value
        },
        "price_config": {
            "smart_pricing": SmartPricing.NORMAL.value
        },
        "exit_options": get_default_exit_options(),
        "entry_criteria": [
            {"type": EntryCriteriaType.BOT_HAS_CAPITAL.value}
        ],
        "tags": []
    }
    
    # Add strategy-specific configurations
    if strategy_type == PositionType.LONG_EQUITY:
        # Equity doesn't need expiration or legs
        pass
    
    elif strategy_type in [PositionType.LONG_CALL, PositionType.LONG_PUT]:
        base_template.update({
            "expiration": {
                "type": ExpirationType.BETWEEN_DAYS.value,
                "days": 30,
                "days_end": 45,
                "series": ExpirationSeries.ANY_SERIES.value
            },
            "legs": [
                {
                    "option_type": OptionType.CALL.value if strategy_type == PositionType.LONG_CALL else OptionType.PUT.value,
                    "side": OptionSide.LONG.value,
                    "strike_config": {
                        "type": StrikeSelectionType.DELTA.value,
                        "delta_range": {"min": 0.3, "max": 0.7},
                        "selection": SelectionType.OR_CLOSEST.value
                    }
                }
            ]
        })
    
    elif strategy_type == PositionType.IRON_CONDOR:
        base_template.update({
            "expiration": {
                "type": ExpirationType.BETWEEN_DAYS.value,
                "days": 7,
                "days_end": 21,
                "series": ExpirationSeries.ANY_SERIES.value
            },
            "legs": [
                {
                    "option_type": OptionType.PUT.value,
                    "side": OptionSide.LONG.value,
                    "strike_config": {
                        "type": StrikeSelectionType.DELTA.value,
                        "delta_range": {"min": -0.15, "max": -0.05},
                        "selection": SelectionType.OR_CLOSEST.value
                    }
                },
                {
                    "option_type": OptionType.PUT.value,
                    "side": OptionSide.SHORT.value,
                    "strike_config": {
                        "type": StrikeSelectionType.DELTA.value,
                        "delta_range": {"min": -0.25, "max": -0.15},
                        "selection": SelectionType.OR_CLOSEST.value
                    }
                },
                {
                    "option_type": OptionType.CALL.value,
                    "side": OptionSide.SHORT.value,
                    "strike_config": {
                        "type": StrikeSelectionType.DELTA.value,
                        "delta_range": {"min": 0.15, "max": 0.25},
                        "selection": SelectionType.OR_CLOSEST.value
                    }
                },
                {
                    "option_type": OptionType.CALL.value,
                    "side": OptionSide.LONG.value,
                    "strike_config": {
                        "type": StrikeSelectionType.DELTA.value,
                        "delta_range": {"min": 0.05, "max": 0.15},
                        "selection": SelectionType.OR_CLOSEST.value
                    }
                }
            ]
        })
    
    # Add more strategy templates as needed
    
    return base_template

def get_required_legs_for_strategy(strategy_type: PositionType) -> List[Dict[str, Any]]:
    """Get the required leg configuration for a strategy type"""
    leg_requirements = {
        PositionType.LONG_EQUITY: [],
        PositionType.LONG_CALL: [
            {"option_type": OptionType.CALL.value, "side": OptionSide.LONG.value}
        ],
        PositionType.LONG_PUT: [
            {"option_type": OptionType.PUT.value, "side": OptionSide.LONG.value}
        ],
        PositionType.LONG_CALL_SPREAD: [
            {"option_type": OptionType.CALL.value, "side": OptionSide.LONG.value},
            {"option_type": OptionType.CALL.value, "side": OptionSide.SHORT.value}
        ],
        PositionType.LONG_PUT_SPREAD: [
            {"option_type": OptionType.PUT.value, "side": OptionSide.LONG.value},
            {"option_type": OptionType.PUT.value, "side": OptionSide.SHORT.value}
        ],
        PositionType.SHORT_CALL_SPREAD: [
            {"option_type": OptionType.CALL.value, "side": OptionSide.SHORT.value},
            {"option_type": OptionType.CALL.value, "side": OptionSide.LONG.value}
        ],
        PositionType.SHORT_PUT_SPREAD: [
            {"option_type": OptionType.PUT.value, "side": OptionSide.SHORT.value},
            {"option_type": OptionType.PUT.value, "side": OptionSide.LONG.value}
        ],
        PositionType.IRON_CONDOR: [
            {"option_type": OptionType.PUT.value, "side": OptionSide.LONG.value},
            {"option_type": OptionType.PUT.value, "side": OptionSide.SHORT.value},
            {"option_type": OptionType.CALL.value, "side": OptionSide.SHORT.value},
            {"option_type": OptionType.CALL.value, "side": OptionSide.LONG.value}
        ],
        PositionType.IRON_BUTTERFLY: [
            {"option_type": OptionType.PUT.value, "side": OptionSide.LONG.value},
            {"option_type": OptionType.PUT.value, "side": OptionSide.SHORT.value},
            {"option_type": OptionType.CALL.value, "side": OptionSide.SHORT.value},
            {"option_type": OptionType.CALL.value, "side": OptionSide.LONG.value}
        ]
    }
    
    return leg_requirements.get(strategy_type, [])

# =============================================================================
# VALIDATION UTILITIES
# =============================================================================

def validate_position_config(config: Dict[str, Any]) -> List[str]:
    """Validate a position configuration and return any errors"""
    errors = []
    
    strategy_type = config.get('strategy_type')
    if not strategy_type:
        errors.append("strategy_type is required")
        return errors
    
    try:
        strategy_enum = PositionType(strategy_type)
    except ValueError:
        errors.append(f"Invalid strategy_type: {strategy_type}")
        return errors
    
    # Validate legs for multi-leg strategies
    legs = config.get('legs', [])
    required_legs = get_required_legs_for_strategy(strategy_enum)
    
    if len(required_legs) > 0 and len(legs) != len(required_legs):
        errors.append(f"Strategy {strategy_type} requires exactly {len(required_legs)} legs, got {len(legs)}")
    
    # Validate expiration for options strategies
    if strategy_enum != PositionType.LONG_EQUITY and 'expiration' not in config:
        errors.append(f"Strategy {strategy_type} requires expiration configuration")
    
    return errors

# =============================================================================
# SCHEMA COMPONENT REFERENCES
# =============================================================================

# These components will be included in the main schema
POSITION_SCHEMA_COMPONENTS = POSITION_SCHEMAS