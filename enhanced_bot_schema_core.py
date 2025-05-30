# Enhanced Option Alpha Bot Schema - Core JSON Schema Definition
# Complete JSON schema based on Option Alpha documentation and bot-schema-prompt.txt

import json
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enhanced_bot_schema_enums import *
from decision_recipe_enums import *
from position_configuration_enums import *

# =============================================================================
# ENHANCED BOT SCHEMA - CORE STRUCTURE
# =============================================================================

ENHANCED_OA_BOT_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "$id": "https://optionalpha.com/schemas/enhanced-bot-config.json",
    "title": "Enhanced Option Alpha Bot Configuration",
    "description": "Complete configuration schema for Option Alpha trading bots with comprehensive decision recipes and position management",
    "type": "object",
    "required": ["name", "account", "safeguards", "automations"],
    "properties": {
        "name": {
            "type": "string",
            "description": "Unique name for the bot",
            "maxLength": 100,
            "minLength": 1
        },
        "account": {
            "type": "string", 
            "description": "Account ID - can be paper account or broker account identifier"
        },
        "group": {
            "type": "string",
            "description": "Optional group assignment for visual categorization and reporting",
            "maxLength": 50
        },
        "safeguards": {
            "$ref": "#/definitions/safeguards"
        },
        "scan_speed": {
            "enum": [item.value for item in ScanSpeed],
            "default": ScanSpeed.FIFTEEN_MINUTES.value,
            "description": "How frequently scanner and monitor automations run when market is open"
        },
        "symbols": {
            "$ref": "#/definitions/symbols_config"
        },
        "automations": {
            "type": "array",
            "description": "List of automations for this bot",
            "items": {
                "$ref": "#/definitions/automation"
            },
            "minItems": 1,
            "maxItems": 50
        }
    },
    "definitions": {
        # =============================================================================
        # SAFEGUARDS DEFINITION
        # =============================================================================
        "safeguards": {
            "type": "object",
            "description": "Risk management and position limits for the bot",
            "required": ["capital_allocation", "daily_positions", "position_limit"],
            "properties": {
                "capital_allocation": {
                    "type": "number",
                    "minimum": ValidationLimits.MIN_CAPITAL_ALLOCATION,
                    "maximum": ValidationLimits.MAX_CAPITAL_ALLOCATION,
                    "description": "Total capital allocated to bot for opening new positions. Only prevents opening new positions, not closing at a loss."
                },
                "daily_positions": {
                    "type": "integer", 
                    "minimum": 0,
                    "maximum": ValidationLimits.MAX_DAILY_POSITIONS,
                    "description": "Maximum positions that can be opened in a single day"
                },
                "position_limit": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": ValidationLimits.MAX_TOTAL_POSITIONS,
                    "description": "Maximum number of positions that can be open simultaneously"
                },
                "daytrading_allowed": {
                    "type": "boolean",
                    "default": False,
                    "description": "Whether positions can be opened and closed same day to avoid pattern day trader requirements"
                }
            }
        },

        # =============================================================================
        # SYMBOLS CONFIGURATION
        # =============================================================================
        "symbols_config": {
            "type": "object",
            "description": "Symbol configuration for bot scanning - static list or dynamic selection",
            "properties": {
                "type": {
                    "enum": [item.value for item in SymbolListType],
                    "description": "Whether symbols are statically defined or dynamically selected"
                },
                "list": {
                    "type": "array",
                    "items": {"type": "string", "maxLength": ValidationLimits.MAX_SYMBOL_LENGTH},
                    "description": "Static list of symbols (required if type is 'static')",
                    "maxItems": ValidationLimits.MAX_SYMBOLS_PER_BOT
                },
                "dynamic_config": {
                    "$ref": "#/definitions/dynamic_symbol_config",
                    "description": "Dynamic symbol selection configuration (required if type is 'dynamic')"  
                }
            },
            "if": {"properties": {"type": {"const": SymbolListType.STATIC.value}}},
            "then": {"required": ["list"]},
            "else": {"required": ["dynamic_config"]}
        },

        "dynamic_symbol_config": {
            "type": "object",
            "description": "Configuration for dynamic symbol selection with filtering and sorting",
            "properties": {
                "filters": {
                    "type": "array",
                    "items": {"$ref": "#/definitions/symbol_filter"},
                    "description": "Filters to apply for symbol selection"
                },
                "sort": {
                    "type": "array", 
                    "items": {"$ref": "#/definitions/symbol_sort"},
                    "description": "Sorting criteria for selected symbols"
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": ValidationLimits.MAX_SYMBOLS_PER_BOT,
                    "description": "Maximum number of symbols to select"
                },
                "exclude": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Symbols to exclude from dynamic selection"
                }
            }
        },

        "symbol_filter": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {"enum": [item.value for item in SymbolFilterType]},
                "operator": {"enum": [item.value for item in ComparisonOperator]},
                "value": {"type": ["number", "string"]},
                "value2": {"type": ["number", "string"]}
            }
        },

        "symbol_sort": {
            "type": "object",
            "required": ["field"],
            "properties": {
                "field": {"enum": [item.value for item in SymbolSortField]},
                "direction": {
                    "enum": [item.value for item in SortDirection],
                    "default": SortDirection.DESCENDING.value
                }
            }
        },

        # =============================================================================
        # AUTOMATION DEFINITION
        # =============================================================================
        "automation": {
            "type": "object",
            "required": ["name", "trigger", "actions"],
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Name of the automation",
                    "maxLength": 100
                },
                "description": {
                    "type": "string",
                    "description": "Optional description of automation purpose",
                    "maxLength": 500
                },
                "trigger": {
                    "$ref": "#/definitions/trigger"
                },
                "actions": {
                    "type": "array",
                    "description": "Ordered list of actions to perform when triggered",
                    "items": {"$ref": "#/definitions/action"},
                    "minItems": 1,
                    "maxItems": ValidationLimits.MAX_ACTIONS_PER_AUTOMATION
                }
            }
        },

        # =============================================================================
        # TRIGGER DEFINITIONS
        # =============================================================================
        "trigger": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {"enum": [item.value for item in TriggerType]}
            },
            "allOf": [
                {
                    "if": {"properties": {"type": {"const": TriggerType.CONTINUOUS.value}}},
                    "then": {
                        "required": ["automation_type"],
                        "properties": {
                            "automation_type": {
                                "enum": [item.value for item in AutomationType],
                                "description": "Scanner runs if under position limits, Monitor runs if has open positions"
                            }
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"const": TriggerType.DATE.value}}},
                    "then": {
                        "required": ["date"],
                        "properties": {
                            "date": {
                                "type": "string",
                                "format": "date",
                                "description": "Target date (mm/dd/yyyy format)"
                            },
                            "market_time": {
                                "type": "string",
                                "pattern": "^(0?[9]|1[0-5]):[0-5][0-9](am|pm)$",
                                "description": "Market time EST (9:35am to 3:55pm)"
                            }
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"const": TriggerType.RECURRING.value}}},
                    "then": {
                        "required": ["recurring_config"],
                        "properties": {
                            "recurring_config": {"$ref": "#/definitions/recurring_config"}
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"enum": [TriggerType.MARKET_OPEN.value, TriggerType.MARKET_CLOSE.value]}}},
                    "then": {
                        "properties": {
                            "days_to_run": {
                                "type": "array",
                                "items": {"enum": [item.value for item in DayOfWeek]},
                                "description": "Days of week to run this trigger"
                            }
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"enum": [TriggerType.POSITION_OPENED.value, TriggerType.POSITION_CLOSED.value]}}},
                    "then": {
                        "properties": {
                            "position_type": {
                                "enum": [item.value for item in PositionType] + ["any"],
                                "default": "any",
                                "description": "Type of position that triggers this automation"
                            }
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"const": TriggerType.WEBHOOK.value}}},
                    "then": {
                        "required": ["webhook_id"],
                        "properties": {
                            "webhook_id": {
                                "type": "string",
                                "description": "ID of the webhook to listen for"
                            },
                            "always_on": {
                                "type": "boolean",
                                "default": False,
                                "description": "Keep webhook trigger always active"
                            }
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"const": TriggerType.MANUAL_BUTTON.value}}},
                    "then": {
                        "properties": {
                            "button_text": {
                                "type": "string",
                                "description": "Text displayed on the manual trigger button",
                                "maxLength": 50
                            },
                            "button_icon": {
                                "type": "string", 
                                "description": "Icon for the manual trigger button"
                            }
                        }
                    }
                }
            ]
        },

        "recurring_config": {
            "type": "object",
            "required": ["start", "repeat_every", "repeat_unit"],
            "properties": {
                "start": {
                    "type": "string",
                    "format": "date",
                    "description": "Start date for recurring schedule"
                },
                "repeat_every": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Repeat interval (e.g., every 2 weeks)"
                },
                "repeat_unit": {
                    "enum": [item.value for item in RepeatUnit],
                    "description": "Unit for repeat interval"
                },
                "on_the": {
                    "type": "string",
                    "description": "Specific day specification (e.g., '26th', '4th Monday', 'Last Monday')"
                },
                "market_time": {
                    "type": "string",
                    "pattern": "^(0?[9]|1[0-5]):[0-5][0-9](am|pm)$",
                    "description": "Market time EST for execution"
                },
                "end": {
                    "oneOf": [
                        {"type": "null"},
                        {"type": "string", "format": "date"}
                    ],
                    "description": "End date for recurring schedule (null for no end)"
                },
                "market_holidays": {
                    "enum": [item.value for item in MarketHolidayAction],
                    "default": MarketHolidayAction.SKIP.value,
                    "description": "How to handle market holidays"
                }
            }
        },

        # =============================================================================
        # ACTION DEFINITIONS
        # =============================================================================
        "action": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {"enum": [item.value for item in ActionType]}
            },
            "allOf": [
                {
                    "if": {"properties": {"type": {"enum": [ActionType.DECISION.value, ActionType.CONDITIONAL.value]}}},
                    "then": {
                        "required": ["decision"],
                        "properties": {
                            "decision": {"$ref": "#/definitions/decision"},
                            "yes_path": {
                                "type": "array",
                                "items": {"$ref": "#/definitions/action"},
                                "description": "Actions to execute if decision is true"
                            },
                            "no_path": {
                                "type": "array",
                                "items": {"$ref": "#/definitions/action"},
                                "description": "Actions to execute if decision is false (not used for conditionals)"
                            }
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"const": ActionType.OPEN_POSITION.value}}},
                    "then": {
                        "required": ["position"],
                        "properties": {
                            "position": {"$ref": "#/definitions/position_config"}
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"const": ActionType.CLOSE_POSITION.value}}},
                    "then": {
                        "required": ["close_config"],
                        "properties": {
                            "close_config": {"$ref": "#/definitions/close_config"}
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"const": ActionType.UPDATE_EXIT_OPTIONS.value}}},
                    "then": {
                        "required": ["position_reference", "exit_options"],
                        "properties": {
                            "position_reference": {
                                "type": "string",
                                "description": "Reference to position to update"
                            },
                            "position_type": {
                                "enum": ["credit", "debit", "equity"],
                                "description": "Type of position for exit option context"
                            },
                            "exit_options": {"$ref": "#/definitions/exit_options"}
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"const": ActionType.NOTIFICATION.value}}},
                    "then": {
                        "required": ["message"],
                        "properties": {
                            "message": {
                                "type": "string",
                                "description": "Notification message to send",
                                "maxLength": 1000
                            }
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"enum": [
                        ActionType.TAG_BOT.value, ActionType.TAG_POSITION.value, ActionType.TAG_SYMBOL.value,
                        ActionType.UNTAG_BOT.value, ActionType.UNTAG_POSITION.value, ActionType.UNTAG_SYMBOL.value
                    ]}}},
                    "then": {
                        "required": ["tags"],
                        "properties": {
                            "tags": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "maxLength": ValidationLimits.MAX_TAG_LENGTH
                                },
                                "maxItems": ValidationLimits.MAX_TAGS_PER_ITEM,
                                "description": "Tags to add/remove"
                            },
                            "symbol": {
                                "type": "string",
                                "description": "Symbol for symbol-specific tag operations"
                            },
                            "position_reference": {
                                "type": "string", 
                                "description": "Position reference for position-specific tag operations"
                            }
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"enum": [
                        ActionType.RESET_BOT_TAGS.value, ActionType.RESET_POSITION_TAGS.value, ActionType.RESET_SYMBOL_TAGS.value
                    ]}}},
                    "then": {
                        "properties": {
                            "tags": {
                                "type": "array",
                                "items": {
                                    "type": "string",
                                    "maxLength": ValidationLimits.MAX_TAG_LENGTH
                                },
                                "maxItems": ValidationLimits.MAX_TAGS_PER_ITEM,
                                "description": "New tags to set (if empty, removes all tags)"
                            },
                            "symbol": {
                                "type": "string",
                                "description": "Symbol for symbol-specific reset operations"
                            },
                            "position_reference": {
                                "type": "string",
                                "description": "Position reference for position-specific reset operations"
                            }
                        }
                    }
                },
                {
                    "if": {"properties": {"type": {"enum": [
                        ActionType.LOOP_POSITIONS.value, ActionType.LOOP_SYMBOLS.value, ActionType.LOOP_BOT_SYMBOLS.value
                    ]}}},
                    "then": {
                        "required": ["loop_config", "loop_actions"],
                        "properties": {
                            "loop_config": {"$ref": "#/definitions/loop_config"},
                            "loop_actions": {
                                "type": "array",
                                "items": {"$ref": "#/definitions/action"},
                                "description": "Actions to execute for each loop iteration"
                            }
                        }
                    }
                }
            ]
        },

        "loop_config": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "Filter by specific symbol (for position loops)"
                },
                "position_type": {
                    "enum": [item.value for item in PositionType] + ["any"],
                    "default": "any",
                    "description": "Filter by position type"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags"
                },
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of symbols to loop through (for symbol loops)"
                }
            }
        }
    }
}

# =============================================================================
# CONSTANTS FOR VALIDATION
# =============================================================================

class ValidationLimits:
    """Validation limits for enhanced schema"""
    
    # Capital Limits
    MIN_CAPITAL_ALLOCATION = 100
    MAX_CAPITAL_ALLOCATION = 10_000_000
    
    # Position Limits  
    MAX_DAILY_POSITIONS = 100
    MAX_TOTAL_POSITIONS = 500
    MAX_ACTIONS_PER_AUTOMATION = 100
    
    # Symbol Limits
    MAX_SYMBOLS_PER_BOT = 1000
    MAX_SYMBOL_LENGTH = 10
    
    # Tag Limits
    MAX_TAGS_PER_ITEM = 20
    MAX_TAG_LENGTH = 50
    
    # Time Limits
    MAX_EXPIRATION_DAYS = 365
    MIN_EXPIRATION_DAYS = 0
    
    # Price Limits
    MAX_STRIKE_PRICE = 10000
    MIN_STRIKE_PRICE = 0.01
    MAX_PREMIUM = 1000
    MIN_PREMIUM = 0.01

# =============================================================================
# SCHEMA COMPONENT UTILITY FUNCTIONS
# =============================================================================

def get_schema_component(component_name: str) -> Dict[str, Any]:
    """Get a specific component from the schema"""
    return ENHANCED_OA_BOT_SCHEMA["definitions"].get(component_name, {})

def validate_schema_component(component_name: str, data: Dict[str, Any]) -> List[str]:
    """Basic validation of a schema component"""
    # This would implement JSON schema validation
    # For now, return empty list (no errors)
    return []

def get_required_fields(component_name: str) -> List[str]:
    """Get required fields for a schema component"""
    component = get_schema_component(component_name)
    return component.get("required", [])

def get_enum_values_for_field(component_name: str, field_name: str) -> List[str]:
    """Get enum values for a specific field in a component"""
    component = get_schema_component(component_name)
    properties = component.get("properties", {})
    field = properties.get(field_name, {})
    return field.get("enum", [])