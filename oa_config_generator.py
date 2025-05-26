# Option Alpha Bot Configuration Generator
# Generates sample bot configurations for testing and examples

import json
from typing import Dict, Any

from oa_enums import *
from oa_constants import FrameworkConstants

class OABotConfigGenerator:
    """
    Generates sample bot configurations for testing and examples.
    Helps users understand the schema structure and create working configurations.
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
                                        "position_size": {
                                            "type": "percent_allocation",
                                            "percent": 5
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
                                        }
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
                                "symbol": "SPY",
                                "comparison": "greater_than",
                                "value": 30
                            },
                            "yes_path": [
                                {
                                    "type": "decision", 
                                    "decision": {
                                        "recipe_type": "indicator",
                                        "symbol": "SPY",
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
                                                "position_size": {
                                                    "type": "percent_allocation",
                                                    "percent": 10
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
                                                }
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
    
    @staticmethod 
    def generate_0dte_samurai_bot() -> Dict[str, Any]:
        """Generate a 0DTE bot similar to the Option Alpha example provided."""
        return {
            "name": "0DTE Samurai Bot", 
            "account": "paper_trading",
            "group": "0DTE Strategies",
            "safeguards": {
                "capital_allocation": 5000,
                "daily_positions": 3,
                "position_limit": 2,
                "daytrading_allowed": True
            },
            "scan_speed": "1_minute",
            "symbols": {
                "type": "static", 
                "list": ["SPX"]
            },
            "automations": [
                {
                    "name": "Morning Approval Process",
                    "description": "Check market conditions before trading",
                    "trigger": {
                        "type": "market_open",
                        "days_to_run": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "general",
                                "comparison": "greater_than",
                                "value": 20
                            },
                            "yes_path": [
                                {
                                    "type": "tag_bot",
                                    "tags": ["approval_granted"]
                                }
                            ],
                            "no_path": [
                                {
                                    "type": "tag_bot", 
                                    "tags": ["approval_denied"]
                                },
                                {
                                    "type": "notification",
                                    "message": "Trading approval denied due to market conditions"
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "Waterfall Scanner - Period 1",
                    "description": "First scan period with higher reward/risk requirements",
                    "trigger": {
                        "type": "continuous",
                        "automation_type": "scanner"
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "bot",
                                "comparison": "equal_to",
                                "value": 1
                            },
                            "yes_path": [
                                {
                                    "type": "conditional",
                                    "decision": {
                                        "recipe_type": "general",
                                        "comparison": "less_than",
                                        "value": 1230
                                    },
                                    "yes_path": [
                                        {
                                            "type": "decision",
                                            "decision": {
                                                "recipe_type": "opportunity",
                                                "comparison": "greater_than",
                                                "value": 45
                                            },
                                            "yes_path": [
                                                {
                                                    "type": "open_position",
                                                    "position": {
                                                        "strategy_type": "iron_condor",
                                                        "symbol": "SPX",
                                                        "expiration": {
                                                            "type": "exact_days",
                                                            "days": 0,
                                                            "series": "any_series"
                                                        },
                                                        "position_size": {
                                                            "type": "risk_amount",
                                                            "risk_amount": 625
                                                        },
                                                        "exit_options": {
                                                            "profit_taking": {
                                                                "enabled": True,
                                                                "percent": 35,
                                                                "basis": "credit"
                                                            },
                                                            "stop_loss": {
                                                                "enabled": True,
                                                                "percent": 50,
                                                                "basis": "credit"
                                                            },
                                                            "expiration": {
                                                                "enabled": True,
                                                                "time_before": 5,
                                                                "time_unit": "minutes"
                                                            }
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "Iron Butterfly Scanner",
                    "description": "Scan for Iron Butterfly opportunities", 
                    "trigger": {
                        "type": "continuous",
                        "automation_type": "scanner"
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "bot",
                                "comparison": "equal_to",
                                "value": 1
                            },
                            "yes_path": [
                                {
                                    "type": "conditional",
                                    "decision": {
                                        "recipe_type": "general", 
                                        "comparison": "greater_than",
                                        "value": 1330
                                    },
                                    "yes_path": [
                                        {
                                            "type": "decision",
                                            "decision": {
                                                "recipe_type": "opportunity",
                                                "comparison": "greater_than",
                                                "value": 1000
                                            },
                                            "yes_path": [
                                                {
                                                    "type": "open_position",
                                                    "position": {
                                                        "strategy_type": "iron_butterfly",
                                                        "symbol": "SPX",
                                                        "expiration": {
                                                            "type": "exact_days",
                                                            "days": 0,
                                                            "series": "any_series"
                                                        },
                                                        "position_size": {
                                                            "type": "risk_amount",
                                                            "risk_amount": 1250
                                                        },
                                                        "exit_options": {
                                                            "profit_taking": {
                                                                "enabled": True,
                                                                "percent": 35,
                                                                "basis": "credit"
                                                            },
                                                            "stop_loss": {
                                                                "enabled": True,
                                                                "percent": 50,
                                                                "basis": "credit"
                                                            },
                                                            "expiration": {
                                                                "enabled": True,
                                                                "time_before": 5,
                                                                "time_unit": "minutes"
                                                            }
                                                        }
                                                    }
                                                }
                                            ]
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "Position Tagging on Open",
                    "description": "Tag new positions with OTM percentage",
                    "trigger": {
                        "type": "position_opened",
                        "position_type": "any"
                    },
                    "actions": [
                        {
                            "type": "tag_position",
                            "tags": ["0dte", "otm_tagged"]
                        }
                    ]
                }
            ]
        }
    
    @staticmethod
    def generate_simple_put_selling_bot() -> Dict[str, Any]:
        """Generate a simple cash-secured put selling bot."""
        return {
            "name": "Cash Secured Put Bot",
            "account": "conservative_income",
            "group": "Income Generation",
            "safeguards": {
                "capital_allocation": 25000,
                "daily_positions": 1,
                "position_limit": 5,
                "daytrading_allowed": False
            },
            "scan_speed": "15_minutes",
            "symbols": {
                "type": "static",
                "list": ["SPY", "QQQ", "AAPL", "MSFT", "TSLA"]
            },
            "automations": [
                {
                    "name": "Put Selling Scanner",
                    "description": "Sell puts on high-quality stocks with good premium",
                    "trigger": {
                        "type": "continuous",
                        "automation_type": "scanner"
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "indicator",
                                "symbol": "SPY",
                                "comparison": "greater_than",
                                "value": 50
                            },
                            "yes_path": [
                                {
                                    "type": "decision",
                                    "decision": {
                                        "recipe_type": "stock",
                                        "symbol": "SPY",
                                        "comparison": "between",
                                        "value": 25,
                                        "value2": 75
                                    },
                                    "yes_path": [
                                        {
                                            "type": "open_position",
                                            "position": {
                                                "strategy_type": "short_put_spread",
                                                "symbol": "SPY",
                                                "expiration": {
                                                    "type": "between_days",
                                                    "days": 15,
                                                    "days_end": 45,
                                                    "series": "any_series"
                                                },
                                                "position_size": {
                                                    "type": "percent_allocation",
                                                    "percent": 20
                                                },
                                                "exit_options": {
                                                    "profit_taking": {
                                                        "enabled": True,
                                                        "percent": 50,
                                                        "basis": "credit"
                                                    },
                                                    "stop_loss": {
                                                        "enabled": True,
                                                        "percent": 150,
                                                        "basis": "credit"
                                                    },
                                                    "expiration": {
                                                        "enabled": True,
                                                        "time_before": 3,
                                                        "time_unit": "days"
                                                    }
                                                }
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
    
    @staticmethod
    def generate_comprehensive_bot() -> Dict[str, Any]:
        """Generate a more comprehensive bot with multiple automations."""
        return {
            "name": "Multi-Strategy Options Bot",
            "account": "advanced_trading",
            "group": "Advanced Strategies",
            "safeguards": {
                "capital_allocation": 100000,
                "daily_positions": 5,
                "position_limit": 20,
                "daytrading_allowed": True
            },
            "scan_speed": "5_minutes",
            "symbols": {
                "type": "static",
                "list": ["SPY", "QQQ", "IWM", "GLD", "TLT", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"]
            },
            "automations": [
                {
                    "name": "Market Open Scanner",
                    "description": "Scan for opportunities at market open",
                    "trigger": {
                        "type": "market_open",
                        "days_to_run": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "indicator",
                                "symbol": "SPY",
                                "comparison": "greater_than",
                                "value": 30
                            },
                            "yes_path": [
                                {
                                    "type": "tag_bot",
                                    "tags": ["high_volatility_regime"]
                                }
                            ],
                            "no_path": [
                                {
                                    "type": "tag_bot",
                                    "tags": ["low_volatility_regime"]
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "Iron Condor Strategy",
                    "description": "Trade iron condors in neutral markets",
                    "trigger": {
                        "type": "continuous",
                        "automation_type": "scanner"
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "bot",
                                "comparison": "equal_to",
                                "value": 0
                            },
                            "yes_path": [
                                {
                                    "type": "open_position",
                                    "position": {
                                        "strategy_type": "iron_condor",
                                        "symbol": "SPY",
                                        "expiration": {
                                            "type": "between_days",
                                            "days": 10,
                                            "days_end": 30,
                                            "series": "any_series"
                                        },
                                        "position_size": {
                                            "type": "percent_allocation",
                                            "percent": 5
                                        },
                                        "exit_options": {
                                            "profit_taking": {
                                                "enabled": True,
                                                "percent": 30,
                                                "basis": "credit"
                                            },
                                            "stop_loss": {
                                                "enabled": True,
                                                "percent": 100,
                                                "basis": "credit"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "Long Call Strategy",
                    "description": "Buy calls in bullish conditions",
                    "trigger": {
                        "type": "continuous",
                        "automation_type": "scanner"
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "indicator",
                                "symbol": "SPY",
                                "comparison": "greater_than",
                                "value": 70
                            },
                            "yes_path": [
                                {
                                    "type": "open_position",
                                    "position": {
                                        "strategy_type": "long_call",
                                        "symbol": "SPY",
                                        "expiration": {
                                            "type": "between_days",
                                            "days": 20,
                                            "days_end": 60,
                                            "series": "any_series"
                                        },
                                        "position_size": {
                                            "type": "percent_allocation", 
                                            "percent": 3
                                        },
                                        "exit_options": {
                                            "profit_taking": {
                                                "enabled": True,
                                                "percent": 100,
                                                "basis": "debit"
                                            },
                                            "stop_loss": {
                                                "enabled": True,
                                                "percent": 50,
                                                "basis": "debit"
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    ]
                },
                {
                    "name": "Position Monitor",
                    "description": "Monitor existing positions for adjustments",
                    "trigger": {
                        "type": "continuous",
                        "automation_type": "monitor"
                    },
                    "actions": [
                        {
                            "type": "decision",
                            "decision": {
                                "recipe_type": "position",
                                "comparison": "greater_than",
                                "value": 5
                            },
                            "yes_path": [
                                {
                                    "type": "notification",
                                    "message": "Position has been open for more than 5 days - consider review"
                                }
                            ]
                        }
                    ]
                }
            ]
        }

# =============================================================================
# USAGE EXAMPLE
# =============================================================================

def demonstrate_config_generation():
    """Demonstrate the configuration generation functionality."""
    print("=" * 60)
    print("Option Alpha Config Generator - Demonstration")
    print("=" * 60)
    
    generator = OABotConfigGenerator()
    
    # Generate different bot configurations
    configs = [
        ("Simple Long Call", generator.generate_simple_long_call_bot()),
        ("Iron Condor", generator.generate_iron_condor_bot()),
        ("0DTE Samurai", generator.generate_0dte_samurai_bot()),
        ("Put Selling", generator.generate_simple_put_selling_bot()),
        ("Multi-Strategy", generator.generate_comprehensive_bot())
    ]
    
    for name, config in configs:
        print(f"\n{name} Bot Configuration:")
        print(f"  Name: {config['name']}")
        print(f"  Capital: ${config['safeguards']['capital_allocation']:,}")
        print(f"  Automations: {len(config['automations'])}")
        print(f"  Symbols: {', '.join(config['symbols']['list'])}")
        
        # Show first automation as example
        if config['automations']:
            first_auto = config['automations'][0]
            print(f"  Sample Automation: {first_auto['name']}")
            print(f"    Trigger: {first_auto['trigger']['type']}")
            print(f"    Actions: {len(first_auto['actions'])}")
    
    print(f"\n✓ Generated {len(configs)} different bot configurations")
    print("Each configuration demonstrates different Option Alpha strategies")
    print("Configurations are ready for validation and use with the framework")

if __name__ == "__main__":
    demonstrate_config_generation()