# Option Alpha Bot Configuration JSON Schema
# This schema defines the complete structure for Option Alpha bot configurations
# Based on OA documentation and recipes provided

import json
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import jsonschema
from jsonschema import validate, ValidationError

# =============================================================================
# ENUMS - Based on Option Alpha Configuration Options
# =============================================================================

class ScanSpeed(Enum):
    """Automation scan speed determines how frequently scanner and monitor automations run"""
    FIFTEEN_MINUTES = "15_minutes"
    FIVE_MINUTES = "5_minutes" 
    ONE_MINUTE = "1_minute"

class TriggerType(Enum):
    """Types of automation triggers"""
    CONTINUOUS = "continuous"
    DATE = "date"
    RECURRING = "recurring"
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    WEBHOOK = "webhook"
    MANUAL_BUTTON = "manual_button"

class AutomationType(Enum):
    """Types of automations"""
    SCANNER = "scanner"  # Only runs if bot is under position limits
    MONITOR = "monitor"  # Only runs if bot has open positions

class ComparisonOperator(Enum):
    """Comparison operators for decision recipes"""
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    EQUAL_TO = "equal_to"
    ABOVE = "above"
    BELOW = "below"
    BETWEEN = "between"

class PositionType(Enum):
    """Types of positions supported by Option Alpha"""
    LONG_EQUITY = "long_equity"
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    LONG_CALL_SPREAD = "long_call_spread"
    LONG_PUT_SPREAD = "long_put_spread"
    SHORT_CALL_SPREAD = "short_call_spread"
    SHORT_PUT_SPREAD = "short_put_spread"
    IRON_CONDOR = "iron_condor"
    IRON_BUTTERFLY = "iron_butterfly"

class PositionStatus(Enum):
    """Position status options"""
    ANY = "any"
    OPEN = "open"
    OPENING = "opening"
    CLOSING = "closing"
    ERROR = "error"

class SmartPricing(Enum):
    """SmartPricing options for order execution"""
    NORMAL = "normal"
    FAST = "fast"
    PATIENT = "patient"
    OFF = "off"
    MARKET = "market"

class OptionType(Enum):
    """Option types"""
    CALL = "call"
    PUT = "put"

class OptionSide(Enum):
    """Option position sides"""
    LONG = "long"
    SHORT = "short"

class ExpirationSeries(Enum):
    """Option expiration series"""
    ANY_SERIES = "any_series"
    ONLY_MONTHLYS = "only_monthlys"

class TimeFrame(Enum):
    """Time frame references"""
    INTRADAY = "intraday"
    MARKET_DAYS = "market_days"
    CALENDAR_DAYS = "calendar_days"

class TechnicalIndicator(Enum):
    """Technical indicators supported by Option Alpha"""
    RSI = "RSI"
    STOCH_K = "Stoch_K"
    CCI = "CCI"
    ADX = "ADX"  
    MOMENTUM = "Momentum"
    MACD = "MACD"
    STOCH_RSI = "Stoch_RSI"
    WILLIAMS_R = "Williams_R"
    ULTIMATE = "Ultimate"
    MFI = "MFI"
    CHANDE = "Chande"
    SMA = "SMA"
    EMA = "EMA"
    TRIMA = "TRIMA"
    KAMA = "KAMA"
    ATR = "ATR"
    BOP = "BOP"
    CMO = "CMO"
    DX = "DX"
    ROC = "ROC"

class VIXType(Enum):
    """VIX-related symbols"""
    VIX = "VIX"
    VIX1D = "VIX1D"
    VIX9D = "VIX9D"
    VIX3M = "VIX3M"
    VIX6M = "VIX6M"
    VVIX = "VVIX"

class PriceReference(Enum):
    """Price reference points"""
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    LAST = "last"
    BID = "bid"
    ASK = "ask"
    MID = "mid"

class MovingAverageType(Enum):
    """Moving average types"""
    SMA = "SMA"
    EMA = "EMA"
    TRIMA = "TRIMA"
    KAMA = "KAMA"

class EarningsTime(Enum):
    """Earnings announcement timing"""
    BEFORE_OPEN = "before_open"
    AFTER_CLOSE = "after_close"

class SymbolType(Enum):
    """Security types"""
    STOCK = "stock"
    ETF = "ETF"
    INDEX = "index"

class LiquidityScore(Enum):
    """Option Alpha liquidity scoring"""
    LOW = 1
    AVERAGE = 2
    GOOD = 3
    VERY_GOOD = 4
    BEST = 5

class MarketEvent(Enum):
    """Economic events that can trigger decisions"""
    FOMC_MEETING = "FOMC_Meeting"
    CPI_RELEASE = "CPI_Release"  
    NONFARM_PAYROLLS = "Nonfarm_payrolls"

class DayOfWeek(Enum):
    """Days of the week"""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"

class ActionType(Enum):
    """Types of actions in automations"""
    DECISION = "decision"
    CONDITIONAL = "conditional"
    OPEN_POSITION = "open_position"
    CLOSE_POSITION = "close_position"
    UPDATE_EXIT_OPTIONS = "update_exit_options"
    NOTIFICATION = "notification"
    TAG_BOT = "tag_bot"
    TAG_POSITION = "tag_position"
    TAG_SYMBOL = "tag_symbol"
    LOOP_POSITIONS = "loop_positions"
    LOOP_SYMBOLS = "loop_symbols"

class DecisionType(Enum):
    """Types of decision recipes"""
    STOCK = "stock"
    INDICATOR = "indicator"
    POSITION = "position"
    BOT = "bot"
    OPPORTUNITY = "opportunity"
    GENERAL = "general"

# =============================================================================
# JSON SCHEMA DEFINITION
# =============================================================================

OA_BOT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Option Alpha Bot Configuration",
    "description": "Complete configuration schema for Option Alpha trading bots",
    "type": "object",
    "required": ["name", "account", "safeguards", "automations"],
    "properties": {
        "name": {
            "type": "string",
            "description": "Unique name for the bot"
        },
        "account": {
            "type": "string", 
            "description": "Account ID - can be paper account or broker account"
        },
        "group": {
            "type": "string",
            "description": "Optional group assignment for visual categorization and reporting"
        },
        "safeguards": {
            "type": "object",
            "description": "Risk management and position limits",
            "required": ["capital_allocation", "daily_positions", "position_limit"],
            "properties": {
                "capital_allocation": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Total capital allocated to bot for opening new positions"
                },
                "daily_positions": {
                    "type": "integer", 
                    "minimum": 0,
                    "description": "Maximum positions that can be opened in a single day"
                },
                "position_limit": {
                    "type": "integer",
                    "minimum": 0, 
                    "description": "Maximum number of positions that can be open simultaneously"
                },
                "daytrading_allowed": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether positions can be opened and closed same day"
                }
            }
        },
        "scan_speed": {
            "enum": ["15_minutes", "5_minutes", "1_minute"],
            "default": "15_minutes",
            "description": "How frequently scanner and monitor automations run"
        },
        "symbols": {
            "type": "object",
            "description": "Symbol configuration for bot scanning",
            "properties": {
                "type": {
                    "enum": ["static", "dynamic"],
                    "description": "Whether symbols are statically defined or dynamically selected"
                },
                "list": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of symbols (if static)"
                },
                "filters": {
                    "type": "array",
                    "description": "Dynamic symbol selection filters (if dynamic)",
                    "items": {
                        "type": "object"
                        # Filter schema would be defined here for dynamic symbol selection
                    }
                }
            }
        },
        "automations": {
            "type": "array",
            "description": "List of automations for this bot",
            "items": {
                "$ref": "#/definitions/automation"
            }
        }
    },
    "definitions": {
        "automation": {
            "type": "object",
            "required": ["name", "trigger", "actions"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the automation"
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of automation purpose"
                },
                "trigger": {
                    "$ref": "#/definitions/trigger"
                },
                "actions": {
                    "type": "array",
                    "description": "Ordered list of actions to perform",
                    "items": {
                        "$ref": "#/definitions/action"
                    }
                }
            }
        },
        "trigger": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "enum": ["continuous", "date", "recurring", "market_open", "market_close", 
                            "position_opened", "position_closed", "webhook", "manual_button"]
                },
                "automation_type": {
                    "enum": ["scanner", "monitor"],
                    "description": "Required for continuous triggers"
                },
                "date": {
                    "type": "string",
                    "format": "date",
                    "description": "Date for date triggers (mm/dd/yyyy)"
                },
                "market_time": {
                    "type": "string",
                    "pattern": "^(0?[9]|1[0-5]):[0-5][0-9](am|pm)$",
                    "description": "Market time EST (9:35am to 3:55pm)"
                },
                "recurring": {
                    "type": "object",
                    "description": "Recurring schedule configuration",
                    "properties": {
                        "start": {"type": "string", "format": "date"},
                        "repeat_every": {"type": "integer", "minimum": 1},
                        "repeat_unit": {"enum": ["day", "week", "month", "year"]},
                        "end": {
                            "oneOf": [
                                {"type": "null"},
                                {"type": "string", "format": "date"}
                            ]
                        },
                        "market_holidays": {
                            "enum": ["run_day_before", "run_day_after", "skip"]
                        }
                    }
                },
                "days_to_run": {
                    "type": "array",
                    "items": {
                        "enum": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "description": "Days for market open/close triggers"
                },
                "position_type": {
                    "enum": ["any", "long_equity", "long_call", "long_call_spread", 
                            "long_put", "long_put_spread", "short_call_spread", 
                            "iron_butterfly", "iron_condor"],
                    "description": "Position type for position opened/closed triggers"
                },
                "webhook_id": {
                    "type": "string",
                    "description": "Webhook ID for webhook triggers"
                },
                "always_on": {
                    "type": "boolean",
                    "description": "Keep webhook trigger always active"
                },
                "button_text": {
                    "type": "string",
                    "description": "Text for manual button triggers"
                },
                "button_icon": {
                    "type": "string", 
                    "description": "Icon for manual button triggers"
                }
            }
        },
        "action": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "enum": ["decision", "conditional", "open_position", "close_position",
                            "update_exit_options", "notification", "tag_bot", "tag_position", 
                            "tag_symbol", "loop_positions", "loop_symbols"]
                },
                "decision": {
                    "$ref": "#/definitions/decision",
                    "description": "Decision configuration (for decision/conditional actions)"
                },
                "position": {
                    "$ref": "#/definitions/position_config", 
                    "description": "Position configuration (for open_position actions)"
                },
                "close_config": {
                    "$ref": "#/definitions/close_config",
                    "description": "Close configuration (for close_position actions)"
                },
                "exit_options": {
                    "$ref": "#/definitions/exit_options",
                    "description": "Exit options (for update_exit_options actions)"
                },
                "notification": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"}
                    }
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to add/remove"
                },
                "loop_config": {
                    "type": "object",
                    "description": "Loop configuration",
                    "properties": {
                        "symbol": {"type": "string"},
                        "position_type": {
                            "enum": ["any", "long_equity", "long_call", "long_call_spread",
                                    "long_put", "long_put_spread", "short_call_spread",
                                    "short_put_spread", "iron_butterfly", "iron_condor"]
                        },
                        "tags": {
                            "type": "array", 
                            "items": {"type": "string"}
                        },
                        "symbols": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    }
                },
                "yes_path": {
                    "type": "array",
                    "description": "Actions to execute if decision is true",
                    "items": {"$ref": "#/definitions/action"}
                },
                "no_path": {
                    "type": "array", 
                    "description": "Actions to execute if decision is false (not used for conditionals)",
                    "items": {"$ref": "#/definitions/action"}
                }
            }
        },
        "decision": {
            "type": "object",
            "required": ["recipe_type"],
            "properties": {
                "recipe_type": {
                    "enum": ["stock", "indicator", "position", "bot", "opportunity", "general"]
                },
                "logic_operator": {
                    "enum": ["and", "or"],
                    "description": "For grouped decisions"
                },
                "grouped_decisions": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/decision"},
                    "description": "Sub-decisions for grouped logic"
                },
                # Stock decision recipes
                "symbol": {"type": "string"},
                "price_field": {
                    "enum": ["ask_price", "bid_price", "bid_ask_spread", "change", "change_percent",
                            "change_as_std_dev", "close_price", "gap", "gap_percent", "high_price",
                            "iv_rank", "last_price", "low_price", "mid_price", "nvrp", "open_price",
                            "std_dev", "volatility_ratio", "volume"]
                },
                "comparison": {
                    "enum": ["greater_than", "greater_than_or_equal", "less_than", 
                            "less_than_or_equal", "equal_to", "above", "below", "between"]
                },
                "value": {"type": "number"},
                "value2": {"type": "number", "description": "Second value for 'between' comparisons"},
                "reference_point": {
                    "enum": ["previous_close", "todays_open", "open", "close", "high", "low"]
                },
                "time_frame": {
                    "enum": ["intraday", "market_days_ago"]
                },
                "days_ago": {"type": "integer", "minimum": 0},
                # Technical indicator decisions
                "indicator": {
                    "enum": ["RSI", "Stoch_K", "CCI", "ADX", "Momentum", "MACD", "Stoch_RSI",
                            "Williams_R", "Ultimate", "MFI", "Chande", "SMA", "EMA", "TRIMA", "KAMA"]
                },
                "indicator_period": {"type": "integer", "minimum": 1},
                "indicator_signal": {
                    "enum": ["buy", "neutral", "sell"]
                },
                # Position decisions
                "position_reference": {"type": "string"},
                "position_field": {
                    "enum": ["alpha", "ask_price", "beta_weight", "bid_price", "bid_ask_spread",
                            "days_open", "dte", "delta", "ev", "ev_per_contract", "gamma",
                            "maintenance", "mid_price", "market_value", "open_pl", "pl_per_contract",
                            "prob_of_profit", "prob_of_max_profit", "prob_of_max_loss", "quantity",
                            "return_percent", "return_on_risk_percent", "reward_risk", "risk",
                            "spread_width", "theta", "trade_price", "underlying_price",
                            "underlying_price_at_open", "vega"]
                },
                # Additional fields for various decision types would continue here...
                # This is a simplified version - the full schema would include all recipe variations
            }
        },
        "position_config": {
            "type": "object",
            "required": ["strategy_type", "symbol"],
            "properties": {
                "strategy_type": {
                    "enum": ["equity", "long_call", "long_put", "long_call_spread", 
                            "long_put_spread", "short_call_spread", "short_put_spread",
                            "iron_condor", "iron_butterfly"]
                },
                "symbol": {"type": "string"},
                "expiration": {"$ref": "#/definitions/expiration_config"},
                "legs": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/leg_config"}
                },
                "position_size": {"$ref": "#/definitions/position_size_config"},
                "price_config": {"$ref": "#/definitions/price_config"},
                "exit_options": {"$ref": "#/definitions/exit_options"},
                "entry_criteria": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/entry_criteria"}
                },
                "position_criteria": {
                    "type": "array", 
                    "items": {"$ref": "#/definitions/position_criteria"}
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        },
        "expiration_config": {
            "type": "object",
            "properties": {
                "type": {
                    "enum": ["exact_days", "at_least_days", "exactly_days", "between_days", "on_or_after"]
                },
                "days": {"type": "integer", "minimum": 0},
                "days_end": {"type": "integer", "minimum": 0},
                "series": {"enum": ["any_series", "only_monthlys"]},
                "date": {"type": "string", "format": "date"},
                "same_as_position": {"type": "string"}
            }
        },
        "leg_config": {
            "type": "object",
            "required": ["option_type", "side", "strike_config"],
            "properties": {
                "option_type": {"enum": ["call", "put"]},
                "side": {"enum": ["long", "short"]},
                "strike_config": {
                    "type": "object",
                    "properties": {
                        "type": {
                            "enum": ["delta", "strike_price", "price_target", "relative_underlying",
                                    "relative_leg", "std_dev", "expected_move", "same_strike", "match_spread_width"]
                        },
                        "value": {"type": "number"},
                        "delta_range": {
                            "type": "object",
                            "properties": {
                                "min": {"type": "number", "minimum": -1, "maximum": 1},
                                "max": {"type": "number", "minimum": -1, "maximum": 1}
                            }
                        },
                        "selection": {"enum": ["exactly", "or_closest", "or_higher", "or_lower"]},
                        "reference_leg": {"type": "string"},
                        "reference_position": {"type": "string"}
                    }
                }
            }
        },
        "position_size_config": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "enum": ["contracts", "risk_amount", "percent_allocation", "percent_with_max", 
                            "same_as_position", "progressive_risk"]
                },
                "contracts": {"type": "integer", "minimum": 1},
                "risk_amount": {"type": "number", "minimum": 0},
                "percent": {"type": "number", "minimum": 0, "maximum": 100},
                "base_type": {"enum": ["allocation", "available_capital", "net_liquid"]},
                "max_amount": {"type": "number", "minimum": 0},
                "reference_position": {"type": "string"},
                "progressive_config": {
                    "type": "object",
                    "properties": {
                        "start_amount": {"type": "number", "minimum": 0},
                        "end_amount": {"type": "number", "minimum": 0},
                        "increment_amount": {"type": "number", "minimum": 0},
                        "increment_type": {"enum": ["increase", "double"]},
                        "trigger": {"enum": ["win", "consecutive_wins", "loss", "consecutive_losses"]},
                        "trigger_count": {"type": "integer", "minimum": 1}
                    }
                }
            }
        },
        "price_config": {
            "type": "object",
            "properties": {
                "smart_pricing": {"enum": ["normal", "fast", "patient", "off", "market"]},
                "final_price_options": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "enum": ["bid_ask_spread_percent", "slippage_amount", 
                                        "typical_slippage_percent", "fixed_price"]
                            },
                            "value": {"type": "number"}
                        }
                    }
                }
            }
        },
        "exit_options": {
            "type": "object",
            "description": "Automated exit criteria checked every minute during market hours",
            "properties": {
                "profit_taking": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "percent": {"type": "number", "minimum": 0},
                        "basis": {"enum": ["credit", "debit"]}
                    }
                },
                "price_target": {
                    "type": "object", 
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "amount": {"type": "number"},
                        "direction": {"enum": ["or_lower", "or_higher"]}
                    }
                },
                "stop_loss": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "percent": {"type": "number", "minimum": 0},
                        "basis": {"enum": ["credit", "debit"]}
                    }
                },
                "trailing_stop": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "activate_at_percent": {"type": "number", "minimum": 0},
                        "pullback_percent": {"type": "number", "minimum": 0},
                        "disable_conditions": {
                            "type": "object",
                            "properties": {
                                "return_threshold": {"type": "number"},
                                "pullback_threshold": {"type": "number"}
                            }
                        }
                    }
                },
                "touch": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "amount": {"type": "number"},
                        "from_itm": {"type": "boolean"}
                    }
                },
                "expiration": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "time_before": {"type": "integer", "minimum": 1},
                        "time_unit": {"enum": ["minutes", "hours", "days"]}
                    }
                },
                "earnings": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "days_before": {"type": "integer", "minimum": 1}
                    }
                },
                "additional_options": {
                    "type": "object",
                    "properties": {
                        "avoid_pdt": {"type": "boolean", "description": "Wait at least 1 day to avoid PDT"},
                        "max_bid_ask_spread": {"type": "number", "description": "Disable exits if spread exceeds amount"}
                    }
                }
            }
        },
        "entry_criteria": {
            "type": "object",
            "description": "Filters to allow/prevent opening positions",
            "properties": {
                "type": {
                    "enum": ["bot_has_capital", "max_open_positions", "max_daily_positions", 
                            "max_symbol_positions", "no_identical_leg", "vix_range", "iv_rank_range"]
                },
                "value": {"type": "number"},
                "value2": {"type": "number"},
                "symbol": {"type": "string"}
            }
        },
        "position_criteria": {
            "type": "object", 
            "description": "Opportunity-specific filters",
            "properties": {
                "type": {
                    "enum": ["max_bid_ask_spread", "price_range", "spread_range", "min_otm_percent",
                            "before_earnings", "before_fomc", "before_ex_dividend", "min_alpha",
                            "min_ev_per_contract", "min_reward_risk", "reward_risk_favorable",
                            "min_prob_profit", "min_prob_max_profit", "min_prob_max_loss",
                            "min_max_profit", "max_max_loss"]
                },
                "value": {"type": "number"},
                "value2": {"type": "number"}
            }
        },
        "close_config": {
            "type": "object",
            "required": ["position", "price_config"],
            "properties": {
                "position": {"type": "string"},
                "price_config": {"$ref": "#/definitions/price_config"},
                "quantity": {
                    "type": "object",
                    "properties": {
                        "type": {"enum": ["percent", "contracts", "shares"]},
                        "amount": {"type": "number", "minimum": 0}
                    }
                },
                "memo": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "discard_otm_long_legs": {
                    "type": "boolean",
                    "description": "Discard expiring OTM long legs with no bid price"
                }
            }
        }
    }
}

# =============================================================================
# CONFIGURATION VALIDATION CLASS
# =============================================================================

class OABotConfigValidator:
    """
    Validates Option Alpha bot configuration JSON against the schema.
    Provides detailed error messages for configuration issues.
    """
    
    def __init__(self):
        self.schema = OA_BOT_SCHEMA
        
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        Validate a bot configuration against the schema.
        
        Args:
            config: Dictionary containing bot configuration
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        try:
            validate(instance=config, schema=self.schema)
            
            # Additional custom validations beyond JSON schema
            errors.extend(self._validate_business_rules(config))
            
            return len(errors) == 0, errors
            
        except ValidationError as e:
            errors.append(f"Schema validation error: {e.message}")
            if e.path:
                errors.append(f"Error path: {' -> '.join(str(p) for p in e.path)}")
            return False, errors
        except Exception as e:
            errors.append(f"Unexpected validation error: {str(e)}")
            return False, errors
    
    def _validate_business_rules(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate business logic rules that can't be expressed in JSON schema.
        
        Args:
            config: Bot configuration dictionary
            
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Validate safeguards make sense
        safeguards = config.get('safeguards', {})
        if safeguards.get('daily_positions', 0) > safeguards.get('position_limit', 0):
            errors.append("Daily positions limit cannot exceed total position limit")
        
        # Validate automation triggers
        for i, automation in enumerate(config.get('automations', [])):
            trigger = automation.get('trigger', {})
            trigger_type = trigger.get('type')
            
            if trigger_type == 'continuous' and 'automation_type' not in trigger:
                errors.append(f"Automation {i}: Continuous triggers require automation_type")
            
            if trigger_type == 'recurring' and 'recurring' not in trigger:
                errors.append(f"Automation {i}: Recurring triggers require recurring configuration")
            
            # Validate action sequences
            errors.extend(self._validate_automation_actions(automation, i))
        
        return errors
    
    def _validate_automation_actions(self, automation: Dict[str, Any], automation_index: int) -> List[str]:
        """
        Validate the action sequences within an automation.
        
        Args:
            automation: Automation configuration
            automation_index: Index of automation for error reporting
            
        Returns:
            List of validation errors
        """
        errors = []
        actions = automation.get('actions', [])
        
        for i, action in enumerate(actions):
            action_type = action.get('type')
            
            # Validate decision actions have proper structure
            if action_type in ['decision', 'conditional']:
                if 'decision' not in action:
                    errors.append(f"Automation {automation_index}, Action {i}: {action_type} requires decision configuration")
                
                # Decisions need yes path, conditionals don't need no path
                if action_type == 'decision' and 'yes_path' not in action:
                    errors.append(f"Automation {automation_index}, Action {i}: Decision requires yes_path")
            
            # Validate position actions have required configs
            elif action_type == 'open_position':
                if 'position' not in action:
                    errors.append(f"Automation {automation_index}, Action {i}: open_position requires position configuration")
            
            elif action_type == 'close_position':
                if 'close_config' not in action:
                    errors.append(f"Automation {automation_index}, Action {i}: close_position requires close_config")
        
        return errors

# =============================================================================
# CONFIGURATION LOADER CLASS
# =============================================================================

class OABotConfigLoader:
    """
    Loads and validates Option Alpha bot configurations from JSON files.
    Provides easy interface for loading different bot strategies.
    """
    
    def __init__(self):
        self.validator = OABotConfigValidator()
        self.loaded_configs = {}
    
    def load_config(self, file_path: str) -> Dict[str, Any]:
        """
        Load and validate a bot configuration from JSON file.
        
        Args:
            file_path: Path to JSON configuration file
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If JSON is malformed
        """
        try:
            with open(file_path, 'r') as f:
                config = json.load(f)
            
            # Validate the configuration
            is_valid, errors = self.validator.validate_config(config)
            
            if not is_valid:
                error_msg = f"Configuration validation failed for {file_path}:\n"
                error_msg += "\n".join(f"  - {error}" for error in errors)
                raise ValueError(error_msg)
            
            # Cache the loaded config
            self.loaded_configs[file_path] = config
            
            return config
            
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {file_path}")
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Invalid JSON in {file_path}: {e.msg}", e.doc, e.pos)
    
    def load_config_from_dict(self, config_dict: Dict[str, Any], config_name: str = "unnamed") -> Dict[str, Any]:
        """
        Load and validate a bot configuration from dictionary.
        
        Args:
            config_dict: Configuration dictionary
            config_name: Name for error reporting
            
        Returns:
            Validated configuration dictionary
            
        Raises:
            ValueError: If configuration is invalid
        """
        is_valid, errors = self.validator.validate_config(config_dict)
        
        if not is_valid:
            error_msg = f"Configuration validation failed for {config_name}:\n"
            error_msg += "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_msg)
        
        return config_dict
    
    def get_config_summary(self, config: Dict[str, Any]) -> str:
        """
        Generate a human-readable summary of a bot configuration.
        
        Args:
            config: Bot configuration dictionary
            
        Returns:
            Summary string
        """
        summary = []
        summary.append(f"Bot Name: {config['name']}")
        summary.append(f"Account: {config['account']}")
        
        if 'group' in config:
            summary.append(f"Group: {config['group']}")
        
        # Safeguards summary
        safeguards = config['safeguards']
        summary.append(f"Capital Allocation: ${safeguards['capital_allocation']:,.2f}")
        summary.append(f"Position Limits: {safeguards['daily_positions']}/day, {safeguards['position_limit']} total")
        summary.append(f"Day Trading: {'Allowed' if safeguards.get('daytrading_allowed', False) else 'Not Allowed'}")
        
        # Scan speed
        scan_speed = config.get('scan_speed', '15_minutes').replace('_', ' ')
        summary.append(f"Scan Speed: Every {scan_speed}")
        
        # Automations summary
        automations = config.get('automations', [])
        summary.append(f"Automations: {len(automations)}")
        
        for i, automation in enumerate(automations):
            trigger_type = automation['trigger']['type']
            action_count = len(automation.get('actions', []))
            summary.append(f"  {i+1}. {automation['name']} - {trigger_type} trigger, {action_count} actions")
        
        return "\n".join(summary)

# =============================================================================
# SAMPLE CONFIGURATION GENERATOR
# =============================================================================

class OABotConfigGenerator:
    """
    Generates sample bot configurations for testing and examples.
    Helps users understand the schema structure.
    """
    
    @staticmethod
    def generate_simple_long_call_bot() -> Dict[str, Any]:
        """Generate a simple bot that buys calls on SPY."""
        return {
            "name": "Simple SPY Long Call Bot",
            "account": "paper_trading",
            "group": "Test Strategies",
            "safeguards": {
                "capital_allocation": 10000,
                "daily_positions": 3,
                "position_limit": 10,
                "daytrading_allowed": False
            },
            "scan_speed": "15_minutes",
            "symbols": {
                "type": "static",
                "list": ["SPY"]
            },
            "automations": [
                {
                    "name": "Buy SPY Calls Scanner",
                    "description": "Scan for long call opportunities on SPY",
                    "trigger": {
                        "type": "continuous",
                        "automation_type": "scanner"
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "stock",
                                "symbol": "SPY",
                                "price_field": "last_price",
                                "comparison": "greater_than",
                                "value": 400
                            },
                            "yes_path": [
                                {
                                    "type": "open_position",
                                    "position": {
                                        "strategy_type": "long_call",
                                        "symbol": "SPY",
                                        "expiration": {
                                            "type": "between_days",
                                            "days": 30,
                                            "days_end": 45,
                                            "series": "any_series"
                                        },
                                        "legs": [
                                            {
                                                "option_type": "call",
                                                "side": "long",
                                                "strike_config": {
                                                    "type": "delta",
                                                    "delta_range": {"min": 0.3, "max": 0.7},
                                                    "selection": "or_closest"
                                                }
                                            }
                                        ],
                                        "position_size": {
                                            "type": "percent_allocation",
                                            "percent": 5,
                                            "base_type": "allocation"
                                        },
                                        "price_config": {
                                            "smart_pricing": "normal"
                                        },
                                        "exit_options": {
                                            "profit_taking": {
                                                "enabled": True,
                                                "percent": 50,
                                                "basis": "debit"
                                            },
                                            "stop_loss": {
                                                "enabled": True,
                                                "percent": 50,
                                                "basis": "debit"
                                            },
                                            "expiration": {
                                                "enabled": True,
                                                "time_before": 7,
                                                "time_unit": "days"
                                            }
                                        },
                                        "entry_criteria": [
                                            {
                                                "type": "bot_has_capital"
                                            },
                                            {
                                                "type": "max_open_positions",
                                                "value": 5
                                            }
                                        ],
                                        "position_criteria": [
                                            {
                                                "type": "max_bid_ask_spread",
                                                "value": 0.10
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
    
    @staticmethod
    def generate_iron_condor_bot() -> Dict[str, Any]:
        """Generate a more complex bot that trades iron condors."""
        return {
            "name": "Weekly Iron Condor Bot",
            "account": "live_trading_001",
            "group": "Income Strategies",
            "safeguards": {
                "capital_allocation": 50000,
                "daily_positions": 2,
                "position_limit": 8,
                "daytrading_allowed": False
            },
            "scan_speed": "5_minutes",
            "symbols": {
                "type": "static",
                "list": ["SPY", "QQQ", "IWM"]
            },
            "automations": [
                {
                    "name": "Iron Condor Scanner",
                    "description": "Scan for iron condor opportunities with high IV",
                    "trigger": {
                        "type": "continuous",
                        "automation_type": "scanner"
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "stock",
                                "symbol": "SPY",  # Would use custom input in real implementation
                                "price_field": "iv_rank",
                                "comparison": "greater_than",
                                "value": 30
                            },
                            "yes_path": [
                                {
                                    "type": "decision",
                                    "decision": {
                                        "recipe_type": "indicator",
                                        "symbol": "SPY",
                                        "indicator": "RSI",
                                        "indicator_period": 14,
                                        "comparison": "between",
                                        "value": 40,
                                        "value2": 60
                                    },
                                    "yes_path": [
                                        {
                                            "type": "open_position",
                                            "position": {
                                                "strategy_type": "iron_condor",
                                                "symbol": "SPY",
                                                "expiration": {
                                                    "type": "between_days",
                                                    "days": 7,
                                                    "days_end": 14,
                                                    "series": "any_series"
                                                },
                                                "legs": [
                                                    {
                                                        "option_type": "put",
                                                        "side": "long",
                                                        "strike_config": {
                                                            "type": "delta",
                                                            "delta_range": {"min": -0.15, "max": -0.05},
                                                            "selection": "or_closest"
                                                        }
                                                    },
                                                    {
                                                        "option_type": "put", 
                                                        "side": "short",
                                                        "strike_config": {
                                                            "type": "delta",
                                                            "delta_range": {"min": -0.25, "max": -0.15},
                                                            "selection": "or_closest"
                                                        }
                                                    },
                                                    {
                                                        "option_type": "call",
                                                        "side": "short", 
                                                        "strike_config": {
                                                            "type": "delta",
                                                            "delta_range": {"min": 0.15, "max": 0.25},
                                                            "selection": "or_closest"
                                                        }
                                                    },
                                                    {
                                                        "option_type": "call",
                                                        "side": "long",
                                                        "strike_config": {
                                                            "type": "delta", 
                                                            "delta_range": {"min": 0.05, "max": 0.15},
                                                            "selection": "or_closest"
                                                        }
                                                    }
                                                ],
                                                "position_size": {
                                                    "type": "percent_allocation",
                                                    "percent": 10,
                                                    "base_type": "allocation"
                                                },
                                                "price_config": {
                                                    "smart_pricing": "normal",
                                                    "final_price_options": [
                                                        {
                                                            "type": "bid_ask_spread_percent",
                                                            "value": 50
                                                        }
                                                    ]
                                                },
                                                "exit_options": {
                                                    "profit_taking": {
                                                        "enabled": True,
                                                        "percent": 25,
                                                        "basis": "credit"
                                                    },
                                                    "stop_loss": {
                                                        "enabled": True,
                                                        "percent": 200,
                                                        "basis": "credit"
                                                    },
                                                    "expiration": {
                                                        "enabled": True,
                                                        "time_before": 1,
                                                        "time_unit": "days"
                                                    }
                                                },
                                                "entry_criteria": [
                                                    {
                                                        "type": "bot_has_capital"
                                                    },
                                                    {
                                                        "type": "max_symbol_positions",
                                                        "symbol": "SPY",
                                                        "value": 2
                                                    }
                                                ],
                                                "position_criteria": [
                                                    {
                                                        "type": "min_reward_risk",
                                                        "value": 20
                                                    },
                                                    {
                                                        "type": "max_bid_ask_spread",
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

# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

def main():
    """
    Example usage of the OA Bot configuration system.
    Demonstrates loading, validation, and summary generation.
    """
    
    print("=" * 60)
    print("Option Alpha Bot Configuration System - Phase 0 Demo")
    print("=" * 60)
    
    # Initialize components
    loader = OABotConfigLoader()
    generator = OABotConfigGenerator()
    
    try:
        # Generate and validate sample configurations
        print("\n1. Generating Simple Long Call Bot Configuration...")
        simple_config = generator.generate_simple_long_call_bot()
        
        validated_simple = loader.load_config_from_dict(simple_config, "Simple Long Call Bot")
        print("✓ Simple bot configuration validated successfully!")
        
        print("\nConfiguration Summary:")
        print("-" * 30)
        print(loader.get_config_summary(validated_simple))
        
        print("\n" + "=" * 60)
        
        print("\n2. Generating Iron Condor Bot Configuration...")
        complex_config = generator.generate_iron_condor_bot()
        
        validated_complex = loader.load_config_from_dict(complex_config, "Iron Condor Bot")
        print("✓ Iron Condor bot configuration validated successfully!")
        
        print("\nConfiguration Summary:")
        print("-" * 30)
        print(loader.get_config_summary(validated_complex))
        
        print("\n" + "=" * 60)
        
        # Test validation with invalid config
        print("\n3. Testing Validation with Invalid Configuration...")
        invalid_config = {
            "name": "Invalid Bot",
            "account": "test",
            "safeguards": {
                "capital_allocation": -1000,  # Invalid: negative allocation
                "daily_positions": 10,
                "position_limit": 5  # Invalid: daily > total limit
            },
            "automations": []
        }
        
        try:
            loader.load_config_from_dict(invalid_config, "Invalid Bot")
            print("✗ Validation should have failed!")
        except ValueError as e:
            print("✓ Validation correctly rejected invalid configuration:")
            print(f"   {str(e)}")
        
        print("\n" + "=" * 60)
        print("Phase 0 Complete: JSON Schema and Configuration Loading ✓")
        print("Ready for Phase 1: Basic Framework Structure")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Error during demo: {str(e)}")
        raise

if __name__ == "__main__":
    main()