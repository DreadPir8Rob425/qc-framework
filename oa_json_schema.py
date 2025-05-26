# Option Alpha Bot Configuration JSON Schema
# Defines and validates complete bot configuration structure

import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

try:
    import jsonschema
    from jsonschema import validate, ValidationError
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False

from oa_enums import *
from oa_constants import ValidationRules

# =============================================================================
# CONFIGURATION DATA STRUCTURES
# =============================================================================

@dataclass
class BotConfiguration:
    """Bot configuration data structure"""
    name: str
    account: str
    safeguards: Dict[str, Any]
    scan_speed: str
    symbols: Dict[str, Any]
    automations: List[Dict[str, Any]]
    group: Optional[str] = None
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'BotConfiguration':
        """Create BotConfiguration from dictionary"""
        return cls(
            name=config_dict['name'],
            account=config_dict['account'],
            safeguards=config_dict['safeguards'],
            scan_speed=config_dict.get('scan_speed', '15_minutes'),
            symbols=config_dict.get('symbols', {}),
            automations=config_dict.get('automations', []),
            group=config_dict.get('group')
        )

@dataclass 
class AutomationConfiguration:
    """Automation configuration structure"""
    name: str
    trigger: Dict[str, Any]
    actions: List[Dict[str, Any]]
    description: Optional[str] = None

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
            "description": "Unique name for the bot",
            "maxLength": ValidationRules.MAX_BOT_NAME_LENGTH
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
                    "minimum": ValidationRules.MIN_CAPITAL_ALLOCATION,
                    "maximum": ValidationRules.MAX_CAPITAL_ALLOCATION,
                    "description": "Total capital allocated to bot for opening new positions"
                },
                "daily_positions": {
                    "type": "integer", 
                    "minimum": 0,
                    "maximum": ValidationRules.MAX_DAILY_POSITIONS,
                    "description": "Maximum positions that can be opened in a single day"
                },
                "position_limit": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": ValidationRules.MAX_TOTAL_POSITIONS, 
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
                    "items": {"type": "string", "maxLength": ValidationRules.MAX_SYMBOL_LENGTH},
                    "maxItems": ValidationRules.MAX_SYMBOLS_PER_BOT,
                    "description": "List of symbols (if static)"
                }
            }
        },
        "automations": {
            "type": "array",
            "description": "List of automations for this bot",
            "maxItems": ValidationRules.MAX_AUTOMATIONS_PER_BOT,
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
                    "maxItems": ValidationRules.MAX_ACTIONS_PER_AUTOMATION,
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
                    "pattern": "^\\d{2}/\\d{2}/\\d{4}$",
                    "description": "Date for date triggers (mm/dd/yyyy)"
                },
                "market_time": {
                    "type": "string",
                    "pattern": "^(0?[9]|1[0-5]):[0-5][0-9](am|pm)$",
                    "description": "Market time EST (9:35am to 3:55pm)"
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
                "yes_path": {
                    "type": "array",
                    "description": "Actions to execute if decision is true",
                    "items": {"$ref": "#/definitions/action"}
                },
                "no_path": {
                    "type": "array", 
                    "description": "Actions to execute if decision is false",
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
                "symbol": {"type": "string"},
                "comparison": {
                    "enum": ["greater_than", "greater_than_or_equal", "less_than", 
                            "less_than_or_equal", "equal_to", "above", "below", "between"]
                },
                "value": {"type": "number"},
                "value2": {"type": "number", "description": "Second value for 'between' comparisons"}
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
                "position_size": {"$ref": "#/definitions/position_size_config"},
                "exit_options": {"$ref": "#/definitions/exit_options"}
            }
        },
        "expiration_config": {
            "type": "object",
            "properties": {
                "type": {
                    "enum": ["exact_days", "at_least_days", "exactly_days", "between_days", "on_or_after"]
                },
                "days": {"type": "integer", "minimum": ValidationRules.MIN_EXPIRATION_DAYS, "maximum": ValidationRules.MAX_EXPIRATION_DAYS},
                "days_end": {"type": "integer", "minimum": ValidationRules.MIN_EXPIRATION_DAYS, "maximum": ValidationRules.MAX_EXPIRATION_DAYS},
                "series": {"enum": ["any_series", "only_monthlys"]}
            }
        },
        "position_size_config": {
            "type": "object",
            "required": ["type"],
            "properties": {
                "type": {
                    "enum": ["contracts", "risk_amount", "percent_allocation"]
                },
                "contracts": {"type": "integer", "minimum": 1},
                "risk_amount": {"type": "number", "minimum": 0},
                "percent": {"type": "number", "minimum": 0, "maximum": 100}
            }
        },
        "exit_options": {
            "type": "object",
            "description": "Automated exit criteria checked during market hours",
            "properties": {
                "profit_taking": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "percent": {"type": "number", "minimum": 0},
                        "basis": {"enum": ["credit", "debit"]}
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
                "expiration": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "time_before": {"type": "integer", "minimum": 1},
                        "time_unit": {"enum": ["minutes", "hours", "days"]}
                    }
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
            if JSONSCHEMA_AVAILABLE:
                validate(instance=config, schema=self.schema)
            else:
                # Basic validation without jsonschema
                errors.extend(self._basic_validation(config))
            
            # Additional custom validations beyond JSON schema
            errors.extend(self._validate_business_rules(config))
            
            return len(errors) == 0, errors
            
        except ValidationError as e if JSONSCHEMA_AVAILABLE else Exception as e:
            errors.append(f"Schema validation error: {str(e)}")
            return False, errors
    
    def _basic_validation(self, config: Dict[str, Any]) -> List[str]:
        """Basic validation when jsonschema is not available"""
        errors = []
        
        # Check required fields
        required_fields = ['name', 'account', 'safeguards', 'automations']
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate safeguards
        if 'safeguards' in config:
            safeguards = config['safeguards']
            required_safeguards = ['capital_allocation', 'daily_positions', 'position_limit']
            for field in required_safeguards:
                if field not in safeguards:
                    errors.append(f"Missing required safeguard: {field}")
        
        return errors
    
    def _validate_business_rules(self, config: Dict[str, Any]) -> List[str]:
        """
        Validate business logic rules that can't be expressed in JSON schema.
        """
        errors = []
        
        # Validate safeguards make sense
        safeguards = config.get('safeguards', {})
        daily_positions = safeguards.get('daily_positions', 0)
        position_limit = safeguards.get('position_limit', 0)
        
        if daily_positions > position_limit:
            errors.append("Daily positions limit cannot exceed total position limit")
        
        # Validate automation triggers
        for i, automation in enumerate(config.get('automations', [])):
            trigger = automation.get('trigger', {})
            trigger_type = trigger.get('type')
            
            if trigger_type == 'continuous' and 'automation_type' not in trigger:
                errors.append(f"Automation {i}: Continuous triggers require automation_type")
        
        return errors

# =============================================================================
# CONFIGURATION LOADER CLASS
# =============================================================================

class OABotConfigLoader:
    """
    Loads and validates Option Alpha bot configurations from JSON files.
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
        """Load and validate a bot configuration from dictionary."""
        is_valid, errors = self.validator.validate_config(config_dict)
        
        if not is_valid:
            error_msg = f"Configuration validation failed for {config_name}:\n"
            error_msg += "\n".join(f"  - {error}" for error in errors)
            raise ValueError(error_msg)
        
        return config_dict
    
    def get_config_summary(self, config: Dict[str, Any]) -> str:
        """Generate a human-readable summary of a bot configuration."""
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