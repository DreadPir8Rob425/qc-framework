#!/usr/bin/env python3
"""
Option Alpha Framework - State Manager Usage Examples
Demonstrates how to use the enhanced StateManager with CSV export and S3 functionality
"""

import os
import json
from datetime import datetime, timedelta
from oa_state_manager import StateManager, create_state_manager, create_state_manager_with_s3


def basic_state_management_example():
    """Demonstrate basic state management operations"""
    print("=" * 60)
    print("Basic State Management Example")
    print("=" * 60)
    
    # Create state manager
    state_manager = create_state_manager("example_state.db")
    
    # Hot State (in-memory, fast access)
    print("\n1. Hot State Operations:")
    state_manager.set_hot_state("current_spy_price", 450.25)
    state_manager.set_hot_state("market_regime", "bullish")
    state_manager.set_hot_state("vix_level", 18.5)
    
    current_price = state_manager.get_hot_state("current_spy_price")
    print(f"   Current SPY Price: ${current_price}")
    print(f"   Market Regime: {state_manager.get_hot_state('market_regime')}")
    
    # Warm State (SQLite, persisted between sessions)
    print("\n2. Warm State Operations:")
    session_data = {
        "bot_start_time": datetime.now().isoformat(),
        "positions_opened_today": 3,
        "daily_pnl": 245.50
    }
    state_manager.set_warm_state("daily_session", session_data)
    
    # Cold State (historical data)
    print("\n3. Cold State Operations:")
    trade_record = {
        "symbol": "SPY",
        "strategy": "iron_condor",
        "entry_date": "2025-01-15",
        "exit_date": "2025-01-20",
        "pnl": 125.00,
        "dte_at_entry": 30,
        "iv_rank_at_entry": 45
    }
    
    record_id = state_manager.store_cold_state(
        trade_record, 
        "completed_trades", 
        ["profitable", "spy", "iron_condor"]
    )
    print(f"   Stored trade record: {record_id}")
    
    # Retrieve cold state data
    recent_trades = state_manager.get_cold_state("completed_trades", limit=5)
    print(f"   Retrieved {len(recent_trades)} recent trades")
    
    return state_manager


def csv_export_example(state_manager):
    """Demonstrate CSV export functionality"""
    print("\n" + "=" * 60)
    print("CSV Export Example")
    print("=" * 60)
    
    # Get database statistics
    print("\n1. Database Statistics:")
    stats = state_manager.get_database_stats()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Export to CSV files
    print("\n2. Exporting to CSV...")
    export_dir = "csv_exports"
    exported_files = state_manager.export_to_csv(export_dir, include_hot_state=True)
    
    print("   Exported files:")
    for table_name, file_path in exported_files.items():
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"     {table_name}: {file_path} ({file_size} bytes)")
    
    # Create compressed export
    print("\n3. Creating compressed export...")
    zip_file = state_manager.create_compressed_export("compressed_exports")
    zip_size = os.path.getsize(zip_file)
    print(f"   Compressed export: {zip_file} ({zip_size} bytes)")
    
    return exported_files


def s3_export_example(state_manager):
    """Demonstrate S3 export functionality (configuration only)"""
    print("\n" + "=" * 60)
    print("S3 Export Configuration Example")
    print("=" * 60)
    
    print("""
To configure S3 exports, you would:

1. Configure AWS credentials:
   state_manager.configure_s3_export(
       bucket_name='my-backtesting-results',
       aws_access_key_id='YOUR_ACCESS_KEY',      # Optional if using IAM
       aws_secret_access_key='YOUR_SECRET_KEY',  # Optional if using IAM
       region_name='us-east-1'
   )

2. Export and upload in one step:
   s3_urls = state_manager.export_and_upload_to_s3(
       s3_prefix='backtest_results/2025-01-15'
   )

3. Or export first, then upload:
   local_files = state_manager.export_to_csv('exports')
   s3_urls = state_manager.upload_to_s3(local_files, 'my_results/2025-01-15')

The uploaded files will be available at:
   s3://my-backtesting-results/my_results/2025-01-15/warm_state.csv
   s3://my-backtesting-results/my_results/2025-01-15/cold_state.csv
   s3://my-backtesting-results/my_results/2025-01-15/positions.csv
   s3://my-backtesting-results/my_results/2025-01-15/positions_summary.csv
   s3://my-backtesting-results/my_results/2025-01-15/hot_state.csv
   s3://my-backtesting-results/my_results/2025-01-15/export_manifest.json
""")


def factory_methods_example():
    """Demonstrate factory methods for creating state managers"""
    print("\n" + "=" * 60)
    print("Factory Methods Example")
    print("=" * 60)
    
    print("\n1. Basic state manager:")
    basic_sm = create_state_manager("basic_example.db")
    print(f"   Created: {type(basic_sm).__name__}")
    
    print("\n2. State manager with S3 configuration:")
    print("   # This would configure S3 if credentials were provided")
    print("   s3_sm = create_state_manager_with_s3(")
    print("       db_path='s3_example.db',")
    print("       s3_bucket='my-bucket',")
    print("       aws_access_key='key',")
    print("       aws_secret_key='secret'")
    print("   )")


def maintenance_operations_example(state_manager):
    """Demonstrate maintenance operations"""
    print("\n" + "=" * 60)
    print("Maintenance Operations Example")
    print("=" * 60)
    
    print("\n1. Database cleanup (remove old data):")
    deleted_counts = state_manager.cleanup_old_data(days_to_keep=30)
    print(f"   Deleted records: {deleted_counts}")
    
    print("\n2. Database backup:")
    backup_path = f"backups/state_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    success = state_manager.backup_database(backup_path)
    print(f"   Backup {'successful' if success else 'failed'}: {backup_path}")
    
    print("\n3. Database vacuum (optimize):")
    vacuum_success = state_manager.vacuum_database()
    print(f"   Vacuum {'successful' if vacuum_success else 'failed'}")


def performance_comparison_info():
    """Information about performance characteristics"""
    print("\n" + "=" * 60)
    print("Performance Characteristics")
    print("=" * 60)
    
    print("""
SQLite vs CSV Performance:

📊 SQLite Advantages:
   • Query Performance: 10-100x faster for complex queries
   • Concurrent Access: Thread-safe with locking
   • Memory Efficiency: Doesn't load entire dataset
   • ACID Transactions: Data integrity guaranteed
   • Indexes: Fast lookups by symbol, date, etc.

📈 When SQLite is Better:
   • Backtests with >10K positions
   • Real-time position lookups during trading
   • Complex filtering and aggregation
   • Multiple threads accessing data simultaneously

💾 CSV Export Benefits:
   • Human-readable for analysis
   • Excel compatibility
   • Easy S3 upload
   • Simple data sharing
   • No database corruption risk

🎯 Recommended Approach:
   1. Use SQLite during backtesting (performance)
   2. Export to CSV at completion (analysis/storage)
   3. Upload CSV to S3 for long-term storage
   4. Keep SQLite for active strategy development

🔍 File Size Estimates:
   • 1K positions: SQLite ~500KB, CSV ~800KB
   • 10K positions: SQLite ~5MB, CSV ~8MB  
   • 100K positions: SQLite ~50MB, CSV ~80MB
""")


def main():
    """Run all examples"""
    print("Option Alpha Framework - Enhanced State Manager Examples")
    print(f"Timestamp: {datetime.now()}")
    
    try:
        # Basic operations
        state_manager = basic_state_management_example()
        
        # CSV export
        exported_files = csv_export_example(state_manager)
        
        # S3 configuration info
        s3_export_example(state_manager)
        
        # Factory methods
        factory_methods_example() 
        
        # Maintenance operations
        maintenance_operations_example(state_manager)
        
        # Performance info
        performance_comparison_info()
        
        print("\n" + "=" * 60)
        print("✅ All Examples Completed Successfully!")
        print("=" * 60)
        print("\n📋 Next Steps:")
        print("1. Install optional dependencies: pip install pandas boto3")
        print("2. Configure AWS credentials for S3 export")
        print("3. Integrate with your QuantConnect backtesting algorithm")
        print("4. Set up automated S3 uploads after backtest completion")
        
    except Exception as e:
        print(f"\n❌ Example failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()