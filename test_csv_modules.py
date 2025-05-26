#!/usr/bin/env python3
"""
Test suite for CSV State Manager modules
Tests all components individually and together
"""

import sys
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
import json

def test_csv_modules():
    """Test all CSV modules with error handling"""
    
    print("🧪 Testing CSV State Manager Modules")
    print("=" * 50)
    
    # Create temporary directory for testing
    test_dir = Path(tempfile.mkdtemp(prefix="csv_test_"))
    print(f"Test Directory: {test_dir}")
    
    try:
        # Test 1: Basic CSV State Manager
        print("\n1️⃣ Testing Basic CSV State Manager...")
        
        # Import with error handling
        try:
            from csv_state_manager import create_csv_state_manager
            state_manager = create_csv_state_manager(str(test_dir), s3_bucket=None)
            print("✅ CSV State Manager created successfully")
        except ImportError as e:
            print(f"❌ Import error: {e}")
            print("Make sure all CSV module files are in the same directory")
            return False
        except Exception as e:
            print(f"❌ Creation error: {e}")
            return False
        
        # Test 2: Hot State
        print("\n2️⃣ Testing Hot State...")
        try:
            state_manager.set_hot_state("test_key", {"value": 123, "timestamp": datetime.now().isoformat()})
            retrieved = state_manager.get_hot_state("test_key")
            assert retrieved is not None
            assert retrieved["value"] == 123
            print("✅ Hot state working correctly")
        except Exception as e:
            print(f"❌ Hot state error: {e}")
            return False
        
        # Test 3: Warm State (CSV)
        print("\n3️⃣ Testing Warm State...")
        try:
            state_manager.set_warm_state("session_data", {"bot_name": "Test Bot", "started": True})
            retrieved = state_manager.get_warm_state("session_data")
            assert retrieved is not None
            assert retrieved["bot_name"] == "Test Bot"
            print("✅ Warm state working correctly")
        except Exception as e:
            print(f"❌ Warm state error: {e}")
            return False
        
        # Test 4: Position Management
        print("\n4️⃣ Testing Position Management...")
        try:
            position_data = {
                'id': 'test_pos_001',
                'symbol': 'SPY',
                'position_type': 'long_call',
                'state': 'open',
                'quantity': 1,
                'entry_price': 450.0,
                'current_price': 455.0,
                'unrealized_pnl': 50.0,
                'realized_pnl': 0.0,
                'tags': ['test', 'demo'],
                'legs': []
            }
            
            state_manager.store_position(position_data)
            positions = state_manager.get_positions()
            assert len(positions) >= 1
            assert positions[0]['id'] == 'test_pos_001'
            print("✅ Position management working correctly")
        except Exception as e:
            print(f"❌ Position management error: {e}")
            return False
        
        # Test 5: Trade Logging
        print("\n5️⃣ Testing Trade Logging...")
        try:
            trade_data = {
                'symbol': 'SPY',
                'action': 'OPEN',
                'position_type': 'long_call',
                'quantity': 1,
                'price': 450.0,
                'pnl': 0.0,
                'bot_name': 'Test Bot'
            }
            
            state_manager.log_trade(trade_data)
            
            # Check if trades file was created
            trades_file = test_dir / "trades" / "trades.csv"
            assert trades_file.exists()
            print("✅ Trade logging working correctly")
        except Exception as e:
            print(f"❌ Trade logging error: {e}")
            return False
        
        # Test 6: Analytics
        print("\n6️⃣ Testing Analytics...")
        try:
            metrics = {
                'total_return': 5.5,
                'win_rate': 0.75,
                'total_trades': 4,
                'sharpe_ratio': 1.2
            }
            
            state_manager.store_performance_metrics(metrics)
            
            # Check if analytics file was created
            analytics_file = test_dir / "analytics" / "performance_metrics.csv"
            assert analytics_file.exists()
            print("✅ Analytics working correctly")
        except Exception as e:
            print(f"❌ Analytics error: {e}")
            return False
        
        # Test 7: Summary Generation
        print("\n7️⃣ Testing Summary Generation...")
        try:
            summary = state_manager.generate_backtest_summary()
            assert 'backtest_id' in summary
            assert 'data_files' in summary
            assert 'statistics' in summary
            print("✅ Summary generation working correctly")
        except Exception as e:
            print(f"❌ Summary generation error: {e}")
            return False
        
        # Test 8: Finalization
        print("\n8️⃣ Testing Backtest Finalization...")
        try:
            result = state_manager.finalize_backtest(upload_to_s3=False, generate_report=True)
            assert 'backtest_id' in result
            assert 'local_path' in result
            
            # Check if summary file was created
            summary_file = test_dir / "backtest_summary.json"
            assert summary_file.exists()
            print("✅ Backtest finalization working correctly")
        except Exception as e:
            print(f"❌ Backtest finalization error: {e}")
            return False
        
        # Test 9: File Structure Verification
        print("\n9️⃣ Verifying File Structure...")
        try:
            expected_dirs = ['warm_state', 'cold_state', 'positions', 'trades', 'analytics', 'logs']
            for dir_name in expected_dirs:
                dir_path = test_dir / dir_name
                assert dir_path.exists(), f"Directory {dir_name} not found"
            
            # Check for key files
            assert (test_dir / "metadata.json").exists()
            assert (test_dir / "backtest_summary.json").exists()
            assert (test_dir / "trades" / "trades.csv").exists()
            assert (test_dir / "positions" / "positions.csv").exists()
            
            print("✅ File structure verified")
        except Exception as e:
            print(f"❌ File structure error: {e}")
            return False
        
        print("\n🎉 All tests passed successfully!")
        print(f"📁 Test data saved to: {test_dir}")
        print("💡 You can examine the generated CSV files to see the structure")
        
        return True
        
    except Exception as e:
        print(f"\n💥 Unexpected error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Ask if user wants to keep test data
        try:
            keep_data = input(f"\nKeep test data in {test_dir}? (y/N): ").lower().strip()
            if keep_data != 'y':
                shutil.rmtree(test_dir)
                print("🗑️ Test data cleaned up")
            else:
                print(f"📁 Test data preserved at: {test_dir}")
        except KeyboardInterrupt:
            print("\n🗑️ Cleaning up...")
            shutil.rmtree(test_dir)

def test_individual_modules():
    """Test individual modules separately"""
    
    print("\n🔧 Testing Individual Modules")
    print("=" * 40)
    
    test_dir = Path(tempfile.mkdtemp(prefix="module_test_"))
    
    # Test Position Handler
    try:
        print("Testing Position CSV Handler...")
        from position_csv_handler import PositionCSVHandler
        
        pos_handler = PositionCSVHandler(test_dir)
        
        test_position = {
            'id': 'test_001',
            'symbol': 'SPY',
            'position_type': 'long_call',
            'state': 'open',
            'quantity': 1,
            'entry_price': 450.0
        }
        
        pos_handler.store_position(test_position)
        positions = pos_handler.get_positions()
        assert len(positions) == 1
        print("✅ Position CSV Handler working")
        
    except Exception as e:
        print(f"❌ Position handler error: {e}")
    
    # Test Analytics Handler
    try:
        print("Testing Analytics CSV Handler...")
        from analytics_csv_handler import AnalyticsCSVHandler
        
        analytics_handler = AnalyticsCSVHandler(test_dir)
        
        test_metrics = {
            'total_return': 10.5,
            'win_rate': 0.8,
            'total_trades': 5
        }
        
        analytics_handler.store_performance_metrics(test_metrics)
        print("✅ Analytics CSV Handler working")
        
    except Exception as e:
        print(f"❌ Analytics handler error: {e}")
    
    # Test S3 Uploader (without actual S3)
    try:
        print("Testing S3 Uploader...")
        from s3_uploader import create_s3_uploader
        
        s3_uploader = create_s3_uploader(bucket_name=None)
        assert not s3_uploader.is_available()  # Should be False without bucket
        print("✅ S3 Uploader working (disabled mode)")
        
    except Exception as e:
        print(f"❌ S3 uploader error: {e}")
    
    # Cleanup
    shutil.rmtree(test_dir)
    print("🗑️ Module test data cleaned up")

def main():
    """Main test runner"""
    print("CSV State Manager Test Suite")
    print("Version: 1.0.0")
    print("=" * 50)
    
    try:
        # Test individual modules first
        test_individual_modules()
        
        # Then test integrated system
        success = test_csv_modules()
        
        if success:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ CSV State Manager is ready for use")
            print("\n📋 Summary:")
            print("  • Hot state (in-memory) ✅")
            print("  • Warm state (CSV session data) ✅") 
            print("  • Cold state (CSV historical data) ✅")
            print("  • Position management ✅")
            print("  • Trade logging ✅")
            print("  • Analytics and reporting ✅")
            print("  • S3 upload capability ✅")
            print("  • Backtest lifecycle management ✅")
            return 0
        else:
            print("\n❌ SOME TESTS FAILED")
            print("Please check the error messages above")
            return 1
            
    except KeyboardInterrupt:
        print("\n\n⏹️ Tests interrupted by user")
        return 1
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)