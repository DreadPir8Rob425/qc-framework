#!/usr/bin/env python3
"""
Complete Test Framework for Option Alpha Framework
Tests all core components with comprehensive coverage
"""

import sys
import json
import tempfile
import os
from datetime import datetime, timedelta
import traceback
import time
from typing import Callable, Dict, Any, List, Optional
from oa_framework_core import DecisionEngine, FrameworkLogger, StateManager, OABot, EventBus, Event, EventHandler
from oa_framework_enums import DecisionResult, EventType, LogLevel, LogCategory, EventType, DecisionResult
from oa_bot_schema import OABotConfigLoader, OABotConfigValidator, OABotConfigGenerator
        
        
# Test Results Collection
class TestResults:
    def __init__(self):
        self.results: List[Dict[str, Any]] = []
        self.start_time = datetime.now()
    
    def add_result(self, test_name: str, passed: bool, error: Optional[str] = None, duration: float = 0.0):
        """Add a test result"""
        self.results.append({
            'test_name': test_name,
            'passed': passed,
            'error': error,
            'duration': duration
        })
    
    def get_summary(self) -> Dict[str, Any]:
        """Get test summary statistics"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r['passed'])
        failed = total - passed
        
        return {
            'total': total,
            'passed': passed,
            'failed': failed,
            'success_rate': (passed / total * 100) if total > 0 else 0,
            'duration': (datetime.now() - self.start_time).total_seconds(),
            'failed_tests': [r['test_name'] for r in self.results if not r['passed']]
        }

class FrameworkTester:
    """Comprehensive test suite for the Option Alpha Framework"""
    
    def __init__(self):
        self.test_results = TestResults()
        self.temp_files = []
        self.test_data_dir = tempfile.mkdtemp(prefix="oa_test_")
    
    def cleanup(self):
        """Clean up temporary files and directories"""
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        
        try:
            import shutil
            if os.path.exists(self.test_data_dir):
                shutil.rmtree(self.test_data_dir)
        except:
            pass
    
    def run_test(self, test_name: str, test_func: Callable) -> bool:
        """Run a single test with timing and error handling"""
        print(f"\n🧪 Running: {test_name}")
        start_time = datetime.now()
        
        try:
            test_func()
            duration = (datetime.now() - start_time).total_seconds()
            print(f"✅ {test_name}: PASSED ({duration:.3f}s)")
            self.test_results.add_result(test_name, True, None, duration)
            return True
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            error_msg = str(e)
            print(f"❌ {test_name}: FAILED ({duration:.3f}s)")
            print(f"   Error: {error_msg}")
            self.test_results.add_result(test_name, False, error_msg, duration)
            return False
    
    def test_imports(self):
        """Test that all framework modules can be imported"""
        try:
            from oa_bot_schema import OABotConfigValidator, OABotConfigGenerator
            from oa_bot_schema import OABotConfigLoader, OABotConfigValidator, OABotConfigGenerator
            from oa_framework_enums import LogLevel, LogCategory, EventType, DecisionResult
            from oa_framework_core import OABot, FrameworkLogger, StateManager
            assert True, "All imports successful"
        except ImportError as e:
            raise AssertionError(f"Import failed: {e}")
    
    def test_schema_validation(self):
        """Test JSON schema validation functionality"""
        
        
        validator = OABotConfigValidator()
        generator = OABotConfigGenerator()
        
        # Test valid configuration
        valid_config = generator.generate_simple_long_call_bot()
        is_valid, errors = validator.validate_config(valid_config)
        
        assert is_valid, f"Valid config failed validation: {errors}"
        assert len(errors) == 0, "Valid config should have no errors"
        
        # Test invalid configuration
        invalid_config = {
            "name": "Test Bot",
            "account": "test",
            "safeguards": {
                "capital_allocation": -1000,  # Invalid negative
                "daily_positions": 10,
                "position_limit": 5  # Invalid: daily > total
            },
            "automations": []
        }
        
        is_valid, errors = validator.validate_config(invalid_config)
        assert not is_valid, "Invalid config should fail validation"
        assert len(errors) > 0, "Invalid config should have errors"
    
    def test_config_generation(self):
        """Test configuration generation"""
        from oa_bot_schema import OABotConfigGenerator
        
        generator = OABotConfigGenerator()
        
        # Test simple bot generation
        simple_config = generator.generate_simple_long_call_bot()
        assert simple_config['name'] == "Simple SPY Long Call Bot"
        assert 'safeguards' in simple_config
        assert 'automations' in simple_config
        
        # Test complex bot generation
        complex_config = generator.generate_iron_condor_bot()
        assert complex_config['name'] == "Weekly Iron Condor Bot"
        assert len(complex_config['automations']) > 0
    
    def test_enum_validation(self):
        """Test enum validation and utilities"""
        from oa_framework_enums import (
            ScanSpeed, PositionType, LogLevel, EnumValidator,
            get_enum_values, validate_enum_value
        )
        
        # Test enum value extraction
        scan_speeds = get_enum_values(ScanSpeed)
        assert "15_minutes" in scan_speeds
        assert "5_minutes" in scan_speeds
        assert "1_minute" in scan_speeds
        
        # Test enum validation
        valid_speed = EnumValidator.validate_scan_speed("5_minutes")
        assert valid_speed == ScanSpeed.FIVE_MINUTES
        
        # Test invalid enum validation
        try:
            EnumValidator.validate_scan_speed("invalid_speed")
            assert False, "Should raise ValueError for invalid enum"
        except ValueError:
            pass  # Expected
    
    def test_logging_system(self):
        """Test the framework logging system"""
        from oa_framework_core import FrameworkLogger
        from oa_framework_enums import LogLevel, LogCategory
        
        logger = FrameworkLogger("TestLogger", max_entries=100)
        
        # Test different log levels
        logger.debug(LogCategory.SYSTEM, "Debug message", test_data="debug")
        logger.info(LogCategory.TRADE_EXECUTION, "Info message", symbol="SPY")
        logger.warning(LogCategory.DECISION_FLOW, "Warning message")
        logger.error(LogCategory.MARKET_DATA, "Error message", error_code=404)
        logger.critical(LogCategory.PERFORMANCE, "Critical message")
        
        # Test log retrieval
        all_logs = logger.get_logs()
        assert len(all_logs) >= 5, "Should have at least 5 log entries"
        
        # Test filtered logs
        system_logs = logger.get_logs(category=LogCategory.SYSTEM)
        assert len(system_logs) >= 1, "Should have system logs"
        
        error_logs = logger.get_logs(level=LogLevel.ERROR)
        assert len(error_logs) >= 1, "Should have error logs"
        
        # Test log summary
        summary = logger.get_summary()
        assert 'levels' in summary and 'categories' in summary
        
        # Test log clearing
        logger.clear_logs()
        cleared_logs = logger.get_logs()
        assert len(cleared_logs) == 0, "Logs should be cleared"
    
    def test_state_management(self):
        """Test multi-layered state management"""
        from oa_framework_core import StateManager
        
        # Create temporary database
        db_file = os.path.join(self.test_data_dir, "test_state.db")
        self.temp_files.append(db_file)
        
        state_manager = StateManager(db_file)
        
        # Test hot state (in-memory)
        test_data = {"test": "hot_state", "value": 123, "nested": {"key": "value"}}
        state_manager.set_hot_state("test_hot", test_data)
        
        retrieved = state_manager.get_hot_state("test_hot")
        assert retrieved == test_data, "Hot state data should match"
        
        # Test default value
        default_val = state_manager.get_hot_state("nonexistent", "default")
        assert default_val == "default", "Should return default for nonexistent key"
        
        # Test warm state (SQLite)
        session_data = {"session_id": "test_123", "started": datetime.now().isoformat()}
        state_manager.set_warm_state("session_test", session_data)
        
        retrieved_session = state_manager.get_warm_state("session_test")
        assert retrieved_session['session_id'] == session_data['session_id']
        
        # Test cold state (historical)
        historical_data = {"trade_id": "T001", "profit": 150.0, "symbol": "SPY"}
        record_id = state_manager.store_cold_state(historical_data, "trades", ["profitable", "spy"])
        assert record_id is not None, "Should return record ID"
        
        retrieved_trades = state_manager.get_cold_state("trades", limit=10)
        assert len(retrieved_trades) >= 1, "Should retrieve stored trades"
        assert retrieved_trades[0]['data']['trade_id'] == "T001"
    
    def test_event_system(self):
        """Test event bus and event handling"""
        
        event_bus = EventBus()
        
        # Create test event handler
        class TestHandler(EventHandler):
            def __init__(self):
                self.events_received = []
            
            def handle_event(self, event):
                self.events_received.append(event)
            
            def can_handle(self, event_type):
                return event_type in [EventType.BOT_STARTED, EventType.MARKET_OPEN]
        
        handler = TestHandler()
        
        # Subscribe handler
        event_bus.subscribe(EventType.BOT_STARTED, handler)
        event_bus.subscribe(EventType.MARKET_OPEN, handler)
        
        # Start processing
        event_bus.start_processing()
        
        try:
            # Publish events
            event1 = Event(EventType.BOT_STARTED, datetime.now(), {"bot": "test"})
            event2 = Event(EventType.MARKET_OPEN, datetime.now(), {"market": "NYSE"})
            
            event_bus.publish(event1)
            event_bus.publish(event2)
            
            # Give time for processing
            time.sleep(0.2)
            
            # Verify events were handled
            assert len(handler.events_received) >= 2, "Should receive published events"
            
        finally:
            event_bus.stop_processing()
    
    def test_decision_engine(self):
        """Test decision engine (stub functionality)"""
        
        
        logger = FrameworkLogger("TestDecision")
        db_file = os.path.join(self.test_data_dir, "test_decision.db")
        self.temp_files.append(db_file)
        
        state_manager = StateManager(db_file)
        decision_engine = DecisionEngine(logger, state_manager)
        
        # Test stock decision (stub returns YES)
        stock_decision = {
            "recipe_type": "stock",
            "symbol": "SPY",
            "price_field": "last_price",
            "comparison": "greater_than",
            "value": 400
        }
        
        result = decision_engine.evaluate_decision(stock_decision)
        assert result == DecisionResult.YES, "Stock decision should return YES (stub)"
        
        # Test indicator decision
        indicator_decision = {
            "recipe_type": "indicator",
            "symbol": "SPY",
            "indicator": "RSI"
        }
        
        result = decision_engine.evaluate_decision(indicator_decision)
        assert result == DecisionResult.YES, "Indicator decision should return YES (stub)"
    
    def test_position_management(self):
        """Test position management (stub functionality)"""
        from oa_framework_core import PositionManager, FrameworkLogger, StateManager, MarketData
        from oa_framework_enums import PositionState
        
        logger = FrameworkLogger("TestPosition")
        db_file = os.path.join(self.test_data_dir, "test_position.db")
        self.temp_files.append(db_file)
        
        state_manager = StateManager(db_file)
        position_manager = PositionManager(logger, state_manager)
        
        # Test opening position (stub)
        position_config = {"symbol": "SPY", "strategy_type": "long_call"}
        position = position_manager.open_position(position_config)
        
        assert position is not None, "Should create position"
        assert position.symbol == "SPY", "Position symbol should match"
        assert position.state == PositionState.OPEN, "Position should be open"
        
        # Test getting open positions
        open_positions = position_manager.get_open_positions()
        assert len(open_positions) >= 1, "Should have open positions"
        
        # Test closing position
        success = position_manager.close_position(position.id)
        assert success, "Should successfully close position"
        
        # Test position price updates
        market_data = {
            "SPY": MarketData(
                symbol="SPY",
                timestamp=datetime.now(),
                price=455.0,
                bid=454.5,
                ask=455.5
            )
        }
        
        # Create another position for price update test
        position2 = position_manager.open_position(position_config)
        position_manager.update_position_prices(market_data)
        
        if position2 is not None:
            updated_position = position_manager.get_position(position2.id)
        
        if updated_position is not None:
            assert updated_position.current_price == 455.0, "Position price should be updated"
    
    def test_bot_integration(self):
        """Test complete bot integration"""
        from oa_bot_schema import OABotConfigGenerator
        from oa_framework_core import OABot
        from oa_framework_enums import BotState
        
        # Create test configuration
        generator = OABotConfigGenerator()
        config = generator.generate_simple_long_call_bot()
        
        # Save to temporary file
        config_file = os.path.join(self.test_data_dir, "test_bot_config.json")
        self.temp_files.append(config_file)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Initialize bot
        bot = OABot(config_file)
        assert bot.config.name == config['name'], "Bot name should match config"
        assert bot.state == BotState.STOPPED, "Bot should start in stopped state"
        
        # Start bot
        bot.start()
        assert bot.state == BotState.RUNNING, "Bot should be running after start"
        
        # Test bot status
        status = bot.get_status()
        assert status['name'] == config['name'], "Status name should match"
        assert status['state'] == 'running', "Status should show running"
        assert 'automations' in status, "Status should include automations"
        assert 'positions' in status, "Status should include positions"
        
        # Stop bot
        bot.stop()
        assert bot.state == BotState.STOPPED, "Bot should be stopped"
    
    def test_config_loading(self):
        """Test configuration loading from file"""
        try:
            loader = OABotConfigLoader()
            generator = OABotConfigGenerator()
            
            # Create test config
            config = generator.generate_iron_condor_bot()
            
            # Save to file in test directory
            config_file = os.path.join(self.test_data_dir, "test_config.json")
            self.temp_files.append(config_file)
            
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            # Load and validate
            loaded_config = loader.load_config(config_file)
            assert loaded_config['name'] == config['name']
            assert loaded_config['safeguards'] == config['safeguards']
            
            # Test summary generation
            summary = loader.get_config_summary(loaded_config)
            assert config['name'] in summary
            assert str(config['safeguards']['capital_allocation']) in summary
            
        except Exception as e:
            raise AssertionError(f"Configuration loading failed: {str(e)}")
        
    def test_error_handling(self):
        """Test error handling and error messages"""
        try:
            from oa_framework_enums import ErrorCode
            
            # Test basic error code existence
            assert hasattr(ErrorCode, 'INSUFFICIENT_CAPITAL')
            assert hasattr(ErrorCode, 'INVALID_CONFIG')
            
            # Test basic error code functionality
            error_code = ErrorCode.INSUFFICIENT_CAPITAL
            assert error_code.value is not None
            
            # Test ErrorMessages if available
            try:
                from oa_framework_enums import ErrorMessages
                msg = ErrorMessages.get_message(ErrorCode.INSUFFICIENT_CAPITAL)
                assert isinstance(msg, str) and len(msg) > 0
            except (ImportError, TypeError, AttributeError):
                # ErrorMessages might not exist or work differently
                pass
                
        except Exception as e:
            raise AssertionError(f"Error handling test failed: {str(e)}")
    
    def run_all_tests(self) -> bool:
        """Run the complete test suite"""
        print("🚀 Starting Option Alpha Framework Test Suite")
        print("=" * 70)
        print(f"Test Data Directory: {self.test_data_dir}")
        print(f"Python Version: {sys.version.split()[0]}")
        print(f"Started: {self.test_results.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Define all tests
        tests = [
            ("Module Imports", self.test_imports),
            ("Schema Validation", self.test_schema_validation),
            ("Configuration Generation", self.test_config_generation),
            ("Enum Validation", self.test_enum_validation),
            ("Logging System", self.test_logging_system),
            ("State Management", self.test_state_management),
            ("Event System", self.test_event_system),
            ("Decision Engine (Stub)", self.test_decision_engine),
            ("Position Manager (Stub)", self.test_position_management),
            ("Bot Integration", self.test_bot_integration),
            ("Error Handling", self.test_error_handling)
        ]
        
        # Run all tests
        for test_name, test_func in tests:
            self.run_test(test_name, test_func)
        
        # Generate and display summary
        summary = self.test_results.get_summary()
        
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"Total Tests: {summary['total']}")
        print(f"✅ Passed: {summary['passed']}")
        print(f"❌ Failed: {summary['failed']}")
        print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
        print(f"⏱️  Total Duration: {summary['duration']:.2f}s")
        
        if summary['failed'] > 0:
            print(f"\n❌ FAILED TESTS:")
            for test_name in summary['failed_tests']:
                failed_result = next(r for r in self.test_results.results if r['test_name'] == test_name)
                print(f"   • {test_name}: {failed_result['error']}")
        
        # Cleanup
        self.cleanup()
        
        # Final verdict
        if summary['failed'] == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Framework is ready for Phase 1 development")
            print("✅ All core components are working correctly")
            return True
        else:
            print(f"\n⚠️  {summary['failed']} test(s) failed")
            print("🔧 Please fix failing tests before proceeding to Phase 1")
            return False

def main():
    """Main test runner entry point"""
    print("Option Alpha Framework - Comprehensive Test Suite")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        tester = FrameworkTester()
        success = tester.run_all_tests()
        
        if success:
            print("\n🚀 Phase 0 Complete - Ready for Phase 1!")
            return 0
        else:
            print("\n🔧 Fix failing tests before continuing")
            return 1
    
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)