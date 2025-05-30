# Integration Example - How to Use the Updated Framework
# This shows how to modify your existing code to use CSV state management with S3 upload

import json
from datetime import datetime

# Your existing imports
from .schema.oa_bot_schema import *
from oa_bot_framework import OABot  # This is now the updated version

def create_and_run_backtest():
    """
    Example of how to create and run a backtest with CSV logging and S3 upload
    """
    
    print("🚀 Starting Backtest with CSV State Management + S3 Upload")
    print("=" * 60)
    
    # 1. Generate or load your bot configuration (same as before)
    generator = OABotConfigGenerator()
    config = generator.generate_iron_condor_bot()  # or your custom config
    
    # Save config to file
    config_file = 'my_backtest_config.json'
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Config saved: {config_file}")
    
    # 2. Initialize bot with CSV state management and S3 upload
    # CHANGE: Now specify data directory and S3 settings
    bot = OABot(
        config_file,
        data_dir=f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",  # Unique directory
        s3_bucket="your-trading-backtests",  # Replace with your bucket name
        s3_prefix="option_alpha_backtests"   # S3 folder structure
    )
    
    print(f"✓ Bot initialized with CSV state management")
    print(f"  Data Directory: {bot.state_manager.data_dir}")
    print(f"  Backtest ID: {bot.state_manager._backtest_id}")
    
    # 3. Start the bot (same as before)
    bot.start()
    print("✓ Bot started - all events now logged to CSV")
    
    # 4. Run your backtest logic
    # This is where you'd normally run your QuantConnect algorithm
    # For demo, we'll simulate some trading activity
    
    print("\n📊 Simulating backtest activity...")
    
    # Simulate opening some positions
    for i in range(3):
        position_config = {
            "symbol": ["SPY", "QQQ", "IWM"][i],
            "strategy_type": "iron_condor",
            "quantity": 1,
            "bot_name": bot.config.name,
            "automation": f"Test Scanner {i+1}"
        }
        
        position = bot.position_manager.open_position(position_config)
        if position:
            print(f"  ✓ Opened position: {position.symbol} ({position.id[:8]}...)")
            
            # Simulate some price movement
            from oa_framework_core import MarketData
            market_data = {
                position.symbol: MarketData(
                    symbol=position.symbol,
                    timestamp=datetime.now(),
                    price=position.entry_price + (i * 2.5),  # Simulate price change
                    bid=position.entry_price + (i * 2.5) - 0.5,
                    ask=position.entry_price + (i * 2.5) + 0.5
                )
            }
            bot.position_manager.update_position_prices(market_data)
            
            # Close first position for P&L demonstration
            if i == 0:
                bot.position_manager.close_position(position.id, {
                    'bot_name': bot.config.name,
                    'automation': 'Profit Target'
                })
                print(f"  ✓ Closed position: {position.symbol}")
    
    # 5. Process some automations
    print("\n🤖 Processing automations...")
    for automation in bot.config.automations[:2]:  # Process first 2 automations
        automation_name = automation['name']
        bot.process_automation(automation_name)
        print(f"  ✓ Processed: {automation_name}")
    
    # 6. Get performance summary
    print("\n📈 Performance Summary:")
    performance = bot.get_performance_summary()
    for key, value in performance.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # 7. Finalize backtest and upload to S3
    print("\n☁️ Finalizing backtest and uploading to S3...")
    result = bot.finalize_backtest(upload_to_s3=True)
    
    print("✅ Backtest Complete!")
    print(f"  Backtest ID: {result['backtest_id']}")
    print(f"  Local Data: {result['local_path']}")
    print(f"  S3 Uploaded: {result['s3_uploaded']}")
    
    if result.get('s3_location'):
        print(f"  S3 Location: {result['s3_location']}")
        print("\n📁 Your backtest results are now available in S3:")
        print(f"    - positions.csv: All position data")
        print(f"    - trades.csv: Trade execution log")  
        print(f"    - analytics/: Performance metrics")
        print(f"    - logs/: Framework events")
        print(f"    - metadata.json: Backtest summary")
    
    return result

def modify_existing_quantconnect_algorithm():
    """
    Example of how to modify your existing QuantConnect algorithm to use CSV logging
    """
    
    print("\n🔧 How to Modify Your Existing QuantConnect Algorithm")
    print("=" * 60)
    
    example_code = '''
# In your QuantConnect algorithm file:

class MyOptionAlphaAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Your existing initialization code...
        
        # ADD: Initialize CSV state manager
        from csv_state_manager import CSVStateManager
        
        self.state_manager = CSVStateManager(
            data_dir=f"qc_backtest_{self.UtcTime.strftime('%Y%m%d_%H%M%S')}",
            s3_bucket="your-qc-backtests",
            s3_prefix="quantconnect_backtests"
        )
        
        self.Log("CSV State Manager initialized")
    
    def OnData(self, data):
        # Your existing trading logic...
        
        # ADD: Log market data updates
        for symbol, bar in data.Bars.items():
            self.state_manager.store_analytics({
                'symbol': str(symbol),
                'open': float(bar.Open),
                'high': float(bar.High), 
                'low': float(bar.Low),
                'close': float(bar.Close),
                'volume': int(bar.Volume)
            }, 'market_data')
    
    def OnOrderEvent(self, orderEvent):
        # Your existing order handling...
        
        # ADD: Log all trade executions
        if orderEvent.Status == OrderStatus.Filled:
            self.state_manager.log_trade({
                'trade_id': str(orderEvent.OrderId),
                'symbol': str(orderEvent.Symbol),
                'action': 'BUY' if orderEvent.Direction == OrderDirection.Buy else 'SELL',
                'quantity': int(orderEvent.FillQuantity),
                'price': float(orderEvent.FillPrice),
                'fees': float(orderEvent.OrderFee.Value.Amount),
                'timestamp': orderEvent.UtcTime.isoformat(),
                'bot_name': 'QuantConnect Algorithm',
                'additional_data': {
                    'order_type': str(orderEvent.OrderType),
                    'direction': str(orderEvent.Direction)
                }
            })
    
    def OnEndOfAlgorithm(self):
        # ADD: Finalize and upload to S3 when backtest completes
        try:
            result = self.state_manager.finalize_backtest(upload_to_s3=True)
            self.Log(f"Backtest finalized. S3 uploaded: {result.get('s3_uploaded')}")
            if result.get('s3_location'):
                self.Log(f"Results available at: {result['s3_location']}")
        except Exception as e:
            self.Log(f"Error finalizing backtest: {e}")
'''
    
    print(example_code)

def setup_aws_credentials():
    """
    Instructions for setting up AWS credentials for S3 upload
    """
    
    print("\n🔐 Setting Up AWS Credentials for S3 Upload")
    print("=" * 60)
    
    instructions = '''
To enable S3 upload functionality, you need to configure AWS credentials:

1. Create an S3 bucket for your backtest results:
   - Log into AWS Console
   - Go to S3 service
   - Create bucket (e.g., "your-trading-backtests")
   - Note the bucket name

2. Set up AWS credentials (choose one method):

   Method A - AWS Credentials File:
   Create ~/.aws/credentials file:
   
   [default]
   aws_access_key_id = YOUR_ACCESS_KEY
   aws_secret_access_key = YOUR_SECRET_KEY
   region = us-east-1

   Method B - Environment Variables:
   export AWS_ACCESS_KEY_ID=YOUR_ACCESS_KEY
   export AWS_SECRET_ACCESS_KEY=YOUR_SECRET_KEY
   export AWS_DEFAULT_REGION=us-east-1

   Method C - IAM Role (if running on EC2):
   Attach IAM role with S3 permissions to your EC2 instance

3. Required IAM permissions:
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow", 
         "Action": [
           "s3:PutObject",
           "s3:PutObjectAcl",
           "s3:GetObject",
           "s3:ListBucket"
         ],
         "Resource": [
           "arn:aws:s3:::your-backtest-bucket",
           "arn:aws:s3:::your-backtest-bucket/*"
         ]
       }
     ]
   }

4. Install required packages:
   pip install boto3 pandas

5. Test your setup:
   python -c "import boto3; print(boto3.client('s3').list_buckets())"
'''
    
    print(instructions)

if __name__ == "__main__":
    # Run the backtest example
    result = create_and_run_backtest()
    
    # Show integration examples
    modify_existing_quantconnect_algorithm()
    setup_aws_credentials()
    
    print("\n🎉 Integration Complete!")
    print("Your framework now supports:")
    print("  ✓ CSV-based state management")
    print("  ✓ Automatic S3 upload after backtests")  
    print("  ✓ Complete audit trail of all activities")
    print("  ✓ Performance analytics and reporting")
    print("  ✓ Easy integration with QuantConnect")