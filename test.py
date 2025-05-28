#!/usr/bin/env python3
"""Quick test to verify the main fixes work"""

import tempfile
import os
from datetime import datetime

def test_position_management():
    """Test that position management works correctly"""
    try:
        # Test imports
        from oa_logging import FrameworkLogger
        from oa_state_manager import create_state_manager
        from enhanced_position_manager import create_position_manager
        from oa_data_structures import Position
        
        print("✓ All imports successful")
        
        # Create test database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            test_db = f.name
        
        # Setup components
        logger = FrameworkLogger("QuickTest")
        state_manager = create_state_manager(test_db)
        position_manager = create_position_manager(state_manager, logger)
        
        print("✓ Components created successfully")
        
        # Test position creation
        position_config = {
            "symbol": "SPY",
            "strategy_type": "long_call",
            "quantity": 1,
            "entry_price": 450.0,
            "tags": ["test"]
        }
        
        position = position_manager.open_position(position_config, "TestBot")
        
        if position:
            print(f"✓ Position created: {position.id[:8]} - {position.symbol}")
            
            # Test getting open positions
            open_positions = position_manager.get_open_positions()
            print(f"✓ Found {len(open_positions)} open positions")
            
            # Test position closing
            if position:
                success = position_manager.close_position(position.id, {"exit_price": 460.0}, "Test Close")
                if success:
                    print(f"✓ Position closed successfully")
                    
                    # Verify position is closed
                    closed_positions = position_manager.get_positions(state="closed")
                    print(f"✓ Found {len(closed_positions)} closed positions")
                else:
                    print("✗ Failed to close position")
                    return False
            
        else:
            print("✗ Failed to create position")
            return False
        
        # Cleanup
        # Cleanup - NEW (Windows-safe)
        try:
            # Ensure all connections are closed
            del state_manager
            del position_manager
            import time
            time.sleep(0.1)  # Brief pause for Windows to release file handles
            os.unlink(test_db)
            print("✓ Database cleanup completed")
        except Exception as cleanup_error:
            print(f"⚠️  Database cleanup skipped: {cleanup_error}")
            # This is not a critical error - the temp file will be cleaned up eventually
        print("✓ Test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Running quick position management test...")
    success = test_position_management()
    print(f"\nResult: {'PASS' if success else 'FAIL'}")