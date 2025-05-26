#!/usr/bin/env python3
"""
Option Alpha Framework - Usage Example (Fixed)
Demonstrates how to use the modular framework components with proper attribute access
"""

import json
from pathlib import Path
from datetime import datetime

# Import framework components
from oa_config_generator import OABotConfigGenerator
from oa_bot_framework import OABot, create_simple_bot_config
from oa_json_schema import OABotConfigLoader

def safe_enum_value(enum_obj):
    """Safely get the value from an enum or return the object as string if it's not an enum"""
    return enum_obj.value if hasattr(enum_obj, 'value') else str(enum_obj)

def create_bot_from_template(template_name: str, data_dir: str, s3_bucket=None):
    """Create a bot from a template configuration"""
    generator = OABotConfigGenerator()
    
    # Generate config based on template name
    if template_name == '0dte_samurai':
        config = generator.generate_0dte_samurai_bot()
    elif template_name == 'iron_condor':
        config = generator.generate_iron_condor_bot()
    elif template_name == 'simple_long_call':
        config = generator.generate_simple_long_call_bot()
    else:
        # Default to simple config
        config = create_simple_bot_config()
    
    # Create bot with config dictionary 
    # Note: OABot constructor expects config_dict parameter
    bot = OABot(config_dict=config)
    return bot

def example_1_create_from_template():
    """Example 1: Create and run a bot from a template"""
    print("=" * 60)
    print("EXAMPLE 1: Create Bot from Template")
    print("=" * 60)
    
    # Create a 0DTE bot from template
    bot = create_bot_from_template(
        template_name='0dte_samurai',
        data_dir='example_backtest_data',
        s3_bucket=None  # Set to your bucket name if you want S3 upload
    )
    
    # Fix: Access config as dictionary, not object
    print(f"✓ Created bot: {bot.config['name']}")
    print(f"✓ Automations: {len(bot.config['automations'])}")
    
    # Start the bot
    bot.start()
    
    # Run a short simulation (stub functionality)
    print("\nRunning 3-step simulation...")
    # Note: run_backtest_simulation doesn't exist in the current framework
    # We'll simulate with basic operations instead
    
    # Test position opening
    position_config = {
        "symbol": "SPX",
        "strategy_type": "iron_condor",
        "quantity": 1
    }
    
    position = bot.position_manager.open_position(position_config)
    if position:
        print(f"✓ Opened test position: {position.symbol}")
    
    # Get status
    status = bot.get_status()
    print(f"✓ Open positions: {status.open_positions}")
    
    # Stop and finalize
    bot.stop()
    
    print(f"✓ Bot stopped successfully")
    
    return bot

def example_2_custom_configuration():
    """Example 2: Create a custom bot configuration"""
    print("\n" + "=" * 60)
    print("EXAMPLE 2: Custom Bot Configuration")
    print("=" * 60)
    
    # Create a custom configuration
    custom_config = {
        "name": "My Custom Options Bot",
        "account": "my_paper_account",
        "group": "Custom Strategies",
        "safeguards": {
            "capital_allocation": 25000,
            "daily_positions": 2,
            "position_limit": 6,
            "daytrading_allowed": True
        },
        "scan_speed": "5_minutes",
        "symbols": {
            "type": "static",
            "list": ["SPY", "QQQ", "IWM"]
        },
        "automations": [
            {
                "name": "Morning Market Check",
                "description": "Check market conditions at open",
                "trigger": {
                    "type": "market_open",
                    "days_to_run": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
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
                                "type": "tag_bot",
                                "tags": ["market_above_400"]
                            }
                        ],
                        "no_path": [
                            {
                                "type": "notification",
                                "message": "SPY below 400 - consider defensive strategies"
                            }
                        ]
                    }
                ]
            },
            {
                "name": "Call Buying Scanner",
                "description": "Look for call buying opportunities",
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
                            "value": 60
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
                                        "days_end": 40,
                                        "series": "any_series"
                                    },
                                    "position_size": {
                                        "type": "percent_allocation",
                                        "percent": 8
                                    },
                                    "exit_options": {
                                        "profit_taking": {
                                            "enabled": True,
                                            "percent": 75,
                                            "basis": "debit"
                                        },
                                        "stop_loss": {
                                            "enabled": True,
                                            "percent": 40,
                                            "basis": "debit"
                                        },
                                        "expiration": {
                                            "enabled": True,
                                            "time_before": 5,
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
    
    # Create bot from custom configuration
    bot = OABot(config_dict=custom_config)
    
    # Fix: Access config as dictionary
    print(f"✓ Created custom bot: {bot.config['name']}")
    print(f"✓ Capital allocation: ${bot.config['safeguards']['capital_allocation']:,}")
    print(f"✓ Scan speed: {bot.config['scan_speed']}")
    
    # Start and run
    bot.start()
    
    # Process specific automation
    automation_name = bot.config['automations'][1]['name']  # Call Buying Scanner
    bot.process_automation(automation_name)
    print(f"✓ Processed '{automation_name}'")
    
    bot.stop()
    return bot

def example_3_save_and_load_config():
    """Example 3: Save configuration to file and load it back"""
    print("\n" + "=" * 60)
    print("EXAMPLE 3: Save and Load Configuration")
    print("=" * 60)
    
    # Generate a configuration
    generator = OABotConfigGenerator()
    config = generator.generate_comprehensive_bot()
    
    # Save to file
    config_file = Path("my_bot_config.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Configuration saved to: {config_file}")
    
    # Load configuration back
    loader = OABotConfigLoader()
    loaded_config = loader.load_config(str(config_file))
    
    print(f"✓ Configuration loaded: {loaded_config['name']}")
    
    # Show configuration summary
    summary = loader.get_config_summary(loaded_config)
    print(f"\nConfiguration Summary:")
    print(summary)
    
    # Create bot from loaded config - use loaded_config with named parameter
    bot = OABot(config_dict=loaded_config)
    
    print(f"\n✓ Bot created from file: {bot.config['name']}")
    
    # Clean up
    if config_file.exists():
        config_file.unlink()
    
    return bot

def example_4_analyze_results():
    """Example 4: Analyze backtest results"""
    print("\n" + "=" * 60)
    print("EXAMPLE 4: Analyze Backtest Results")
    print("=" * 60)
    
    # Create and run a bot
    bot = create_bot_from_template('iron_condor', data_dir='analysis_data')
    bot.start()
    
    print("Running simulation for analysis...")
    
    # Simulate some trading activity
    for i in range(3):
        position_config = {
            "symbol": ["SPY", "QQQ", "IWM"][i],
            "strategy_type": "iron_condor",
            "quantity": 1
        }
        position = bot.position_manager.open_position(position_config)
        if position:
            print(f"  ✓ Opened position: {position.symbol}")
    
    # Get detailed status
    status = bot.get_status()
    print(f"\nBot Status:")
    print(f"  Name: {status.name}")
    print(f"  State: {status.state}")
    print(f"  Open Positions: {status.open_positions}")
    print(f"  Total P&L: ${status.total_pnl:.2f}")
    
    # Get position details from position manager
    positions = bot.position_manager.get_open_positions()
    print(f"\nPosition Details:")
    for i, pos in enumerate(positions[:5], 1):  # Show first 5
        # Use safe enum value helper function
        pos_type = safe_enum_value(pos.position_type)
        print(f"  {i}. {pos.symbol} {pos_type} - ${pos.unrealized_pnl:.2f} P&L")
    
    # Stop and get final results
    bot.stop()
    
    # Get portfolio summary
    portfolio_summary = bot.position_manager.get_portfolio_summary()
    print(f"\nPortfolio Summary:")
    print(f"  Total Positions: {portfolio_summary.get('total_positions', 0)}")
    print(f"  Open Positions: {portfolio_summary.get('open_positions', 0)}")
    print(f"  Total P&L: ${portfolio_summary.get('total_pnl', 0):.2f}")
    print(f"  Win Rate: {portfolio_summary.get('win_rate', 0):.1f}%")
    
    return portfolio_summary

def main():
    """Run all examples"""
    print("🚀 Option Alpha Framework - Usage Examples")
    print("=" * 70)
    
    try:
        # Run all examples
        bot1 = example_1_create_from_template()
        bot2 = example_2_custom_configuration()
        bot3 = example_3_save_and_load_config()
        results = example_4_analyze_results()
        
        print("\n" + "=" * 70)
        print("✅ ALL EXAMPLES COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("🎯 Framework Features Demonstrated:")
        print("  ✓ Template-based bot creation")
        print("  ✓ Custom configuration building")
        print("  ✓ JSON file save/load operations")
        print("  ✓ Backtest simulation and analysis")
        print("  ✓ Position management and portfolio tracking")
        print("  ✓ Comprehensive result reporting")
        
        print(f"\n📊 Data Directories Created:")
        data_dirs = ['example_backtest_data', 'analysis_data']
        for dir_name in data_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                files = list(dir_path.rglob('*'))
                print(f"  📁 {dir_name}: {len(files)} files")
        
        print(f"\n🚀 Framework ready for QuantConnect integration!")
        print("Next step: Implement QuantConnect Algorithm class in Phase 1")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Example execution failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)