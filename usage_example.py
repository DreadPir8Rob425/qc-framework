#!/usr/bin/env python3
"""
Option Alpha Framework - Usage Example
Demonstrates how to use the modular framework components
"""

import json
from pathlib import Path

# Import framework components
from oa_config_generator import OABotConfigGenerator
from oa_bot_framework import OABot, create_bot_from_template
from oa_json_schema import OABotConfigLoader

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
    
    print(f"✓ Created bot: {bot.config.name}")
    print(f"✓ Backtest ID: {bot.state_manager.get_backtest_id()}")
    print(f"✓ Automations: {len(bot.config.automations)}")
    
    # Start the bot
    bot.start()
    
    # Run a short simulation
    print("\nRunning 3-step simulation...")
    results = bot.run_backtest_simulation(steps=3)
    print(f"✓ Simulation completed: {results}")
    
    # Get status
    status = bot.get_status()
    print(f"✓ Open positions: {status['positions']['open_count']}")
    
    # Stop and finalize
    bot.stop()
    finalization = bot.finalize_backtest(upload_to_s3=False)
    print(f"✓ Results saved to: {finalization['local_path']}")
    
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
    bot = OABot(
        config_dict=custom_config,
        data_dir='custom_backtest_data'
    )
    
    print(f"✓ Created custom bot: {bot.config.name}")
    print(f"✓ Capital allocation: ${bot.config.safeguards['capital_allocation']:,}")
    print(f"✓ Scan speed: {bot.config.scan_speed}")
    
    # Start and run
    bot.start()
    
    # Process specific automation
    automation_name = bot.config.automations[1]['name']  # Call Buying Scanner
    success = bot.process_automation(automation_name)
    print(f"✓ Processed '{automation_name}': {success}")
    
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
    
    # Create bot from loaded config
    bot = OABot(config_path=str(config_file), data_dir='loaded_config_data')
    
    print(f"\n✓ Bot created from file: {bot.config.name}")
    
    # Clean up
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
    
    print("Running extended simulation for analysis...")
    results = bot.run_backtest_simulation(steps=8)
    
    # Get detailed status
    status = bot.get_status()
    print(f"\nBot Status:")
    print(f"  Name: {status['name']}")
    print(f"  State: {status['state']}")
    print(f"  Open Positions: {status['positions']['open_count']}")
    print(f"  Total P&L: ${status['positions']['total_unrealized_pnl']:.2f}")
    
    # Get position details
    positions = bot.state_manager.get_positions()
    print(f"\nPosition Details:")
    for i, pos in enumerate(positions[:5], 1):  # Show first 5
        print(f"  {i}. {pos['symbol']} {pos['position_type']} - ${pos['unrealized_pnl']:.2f} P&L")
    
    # Stop and get final results
    bot.stop()
    final_results = bot.finalize_backtest(upload_to_s3=False)
    
    print(f"\nBacktest Summary:")
    if 'summary' in final_results:
        summary = final_results['summary']
        if 'statistics' in summary:
            stats = summary['statistics']
            if 'positions' in stats:
                pos_stats = stats['positions']
                print(f"  Total Positions: {pos_stats.get('total_positions', 0)}")
                print(f"  Open Positions: {pos_stats.get('open_positions', 0)}")
                print(f"  Closed Positions: {pos_stats.get('closed_positions', 0)}")
                print(f"  Total P&L: ${pos_stats.get('total_pnl', 0):.2f}")
            
            if 'trades' in stats:
                trade_stats = stats['trades']
                print(f"  Total Trades: {trade_stats.get('total_trades', 0)}")
                print(f"  Symbols Traded: {trade_stats.get('symbols_traded', 0)}")
    
    print(f"  Data Location: {final_results['local_path']}")
    
    return final_results

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
        print("  ✓ CSV data export and state management")
        print("  ✓ Comprehensive result reporting")
        
        print(f"\n📊 Data Directories Created:")
        data_dirs = ['example_backtest_data', 'custom_backtest_data', 
                    'loaded_config_data', 'analysis_data']
        for dir_name in data_dirs:
            dir_path = Path(dir_name)
            if dir_path.exists():
                csv_files = list(dir_path.rglob('*.csv'))
                json_files = list(dir_path.rglob('*.json'))
                print(f"  📁 {dir_name}: {len(csv_files)} CSV files, {len(json_files)} JSON files")
        
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