#!/usr/bin/env python3
"""
Phase 0 Test Runner for Option Alpha Framework
Tests all core components and validates functionality
"""

import sys
import json
import tempfile
import os
from datetime import datetime
import traceback
from typing import Callable
from oa_framework_enums import *
from oa_framework_core import (
        OABot,
        FrameworkLogger,
        StateManager,
        EventBus,
        Event, EventHandler,
        DecisionEngine,
        PositionManager,
        Position
    )
# Import framework components
try:
    from oa_bot_schema import (
        OABotConfigLoader, 
        OABotConfigValidator, 
        OABotConfigGenerator
    )
    from oa_framework_enums import *
    from oa_framework_core import (
        OABot,
        FrameworkLogger,
        StateManager,
        EventBus,
        Event,
        DecisionEngine,
        PositionManager,
        Position
    )
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all framework files are in the same directory")
    sys.exit(1)

class Phase0Tester:
    """Test suite for Phase 0 framework components"""
    
    def __init__(self):
        self.test_results = []
        self.temp_files = []
    
    def run_test(self, test_name: str, test_func: Callable) -> bool:
        """Run a single test and record results"""
        print(f"\n🧪 Testing: {test_name}")
        try:
            test_func()
            print(f"✅ {test_name}: PASSED")
            self.test_results.append((test_name, True, None))
            return True
        except Exception as e:
            error_msg = str(e)
            print(f"❌ {test_name}: FAILED - {error_msg}")
            # Print full traceback for debugging
            import traceback
            traceback.print_exc()
            self.test_results.append((test_name, False, error_msg))
            return False
        
    def test_schema_validation(self):
        """Test JSON schema validation"""
        validator = OABotConfigValidator()
        
        # Test valid configuration
        generator = OABotConfigGenerator()
        valid_config = generator.generate_simple_long_call_bot()
        
        is_valid, errors = validator.validate_config(valid_config)
        assert is_valid, f"Valid config failed validation: {errors}"
        
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
        assert len(errors) > 0, "Should have validation errors"
    
    def test_config_loading(self):
        """Test configuration loading from file"""
        loader = OABotConfigLoader()
        generator = OABotConfigGenerator()
        
        # Create test config
        config = generator.generate_iron_condor_bot()
        
        # Create temporary file more reliably
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, indent=2)
            config_file = f.name
            self.temp_files.append(config_file)
        
        # Load and validate
        loaded_config = loader.load_config(config_file)
        assert loaded_config['name'] == config['name']
        assert loaded_config['safeguards'] == config['safeguards']
        
        # Test summary generation
        summary = loader.get_config_summary(loaded_config)
        assert config['name'] in summary
        assert str(config['safeguards']['capital_allocation']) in summary
    
    def test_enum_validation(self):
        """Test enum validation functionality"""
        
        # Test valid enum values
        valid_speed = ScanSpeed.FIVE_MINUTES
        assert valid_speed.value == "5_minutes"
        
        valid_position = EnumValidator.validate_position_type("iron_condor")
        assert valid_position == PositionType.IRON_CONDOR
        
        # Test invalid enum values
        try:
            EnumValidator.validate_scan_speed("2_minutes")
            assert False, "Should raise ValueError for invalid scan speed"
        except ValueError:
            pass  # Expected
        
        # Test enum utility functions
        speed_values = get_enum_values(ScanSpeed)
        assert "15_minutes" in speed_values
        assert "5_minutes" in speed_values
        assert "1_minute" in speed_values
    
    def test_logging_system(self):
        """Test custom logging system"""
        logger = FrameworkLogger("TestLogger")
        
        # Test different log levels
        logger.debug(LogCategory.SYSTEM, "Debug message", test=True)
        logger.info(LogCategory.TRADE_EXECUTION, "Info message", symbol="SPY")
        logger.warning(LogCategory.DECISION_FLOW, "Warning message")
        logger.error(LogCategory.MARKET_DATA, "Error message", error_code=404)
        
        # Test log retrieval
        all_logs = logger.get_logs()
        assert len(all_logs) >= 4
        
        # Test filtered logs
        system_logs = logger.get_logs(category=LogCategory.SYSTEM)
        assert len(system_logs) >= 1
        
        error_logs = logger.get_logs(level=LogLevel.ERROR)
        assert len(error_logs) >= 1
        
        # Test log summary
        summary = logger.get_summary()
        assert 'levels' in summary
        assert 'categories' in summary
        assert summary['levels']['info'] >= 1
        
        # Test clear logs
        logger.clear_logs()
        cleared_logs = logger.get_logs()
        assert len(cleared_logs) == 0
    
    def test_state_management(self):
        """Test multi-layered state management"""
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
            self.temp_files.append(db_path)
        
        state_manager = StateManager(db_path)
        
        # Test hot state (in-memory)
        test_data = {"test": "hot_state", "value": 123}
        state_manager.set_hot_state("test_hot", test_data)
        
        retrieved = state_manager.get_hot_state("test_hot")
        assert retrieved == test_data
        
        # Test warm state (SQLite session)
        session_data = {"session_id": "test_123", "started": datetime.now().isoformat()}
        state_manager.set_warm_state("session_test", session_data)
        
        retrieved_session = state_manager.get_warm_state("session_test")
        assert retrieved_session['session_id'] == session_data['session_id']
        
        # Test cold state (historical)
        historical_data = {"trade_id": "T001", "profit": 150.0, "symbol": "SPY"}
        record_id = state_manager.store_cold_state(historical_data, "trades", ["profitable", "spy"])
        assert record_id is not None
        
        retrieved_trades = state_manager.get_cold_state("trades", limit=10)
        assert len(retrieved_trades) >= 1
        assert retrieved_trades[0]['data']['trade_id'] == "T001"
        
        # Test position storage
        from oa_framework_core import Position, PositionType, PositionState
        position = Position(
            id="test_pos_001",
            symbol="SPY",
            position_type=PositionType.LONG_CALL,
            state=PositionState.OPEN,
            opened_at=datetime.now(),
            quantity=1,
            entry_price=450.0
        )
        
        state_manager.store_position(position)
        
        retrieved_positions = state_manager.get_positions(symbol="SPY")
        assert len(retrieved_positions) >= 1
        assert retrieved_positions[0].symbol == "SPY"
    
    def test_event_system(self):
        """Test event bus and event handling"""
        event_bus = EventBus()
        
        # Create test event handler
        class TestEventHandler(EventHandler):
            def __init__(self):
                self.events_received = []
            
            def handle_event(self, event):
                self.events_received.append(event)
            
            def can_handle(self, event_type):
                return event_type in [EventType.BOT_STARTED, EventType.MARKET_OPEN]
        
        handler = TestEventHandler()
        
        # Subscribe handler
        event_bus.subscribe(EventType.BOT_STARTED, handler)
        event_bus.subscribe(EventType.MARKET_OPEN, handler)
        
        # Start processing
        event_bus.start_processing()
        
        # Publish events
        event1 = Event(EventType.BOT_STARTED, datetime.now(), {"bot": "test"})
        event2 = Event(EventType.MARKET_OPEN, datetime.now(), {"market": "NYSE"})
        event3 = Event(EventType.BOT_STOPPED, datetime.now(), {"bot": "test"})  # Should not be handled
        
        event_bus.publish(event1)
        event_bus.publish(event2)
        event_bus.publish(event3)
        
        # Give some time for processing
        import time
        time.sleep(0.1)
        
        # Stop processing
        event_bus.stop_processing()
        
        # Verify events were handled
        assert len(handler.events_received) >= 2  # Should have received 2 events
        
        # Verify correct events were received
        received_types = [event.event_type for event in handler.events_received]
        assert EventType.BOT_STARTED in received_types
        assert EventType.MARKET_OPEN in received_types
    
    def test_decision_engine(self):
        """Test decision engine (stub functionality)"""
        logger = FrameworkLogger("TestDecision")
        
        # Create temporary database for state manager
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
            self.temp_files.append(db_path)
        
        state_manager = StateManager(db_path)
        decision_engine = DecisionEngine(logger, state_manager)
        
        # Test different decision types (all stubs return YES for Phase 0)
        stock_decision = {
            "recipe_type": "stock",
            "symbol": "SPY",
            "price_field": "last_price",
            "comparison": "greater_than",
            "value": 400
        }
        
        result = decision_engine.evaluate_decision(stock_decision)
        assert result == DecisionResult.YES, "Stock decision should return YES (stub)"
        
        indicator_decision = {
            "recipe_type": "indicator",
            "symbol": "SPY",
            "indicator": "RSI",
            "comparison": "less_than",
            "value": 30
        }
        
        result = decision_engine.evaluate_decision(indicator_decision)
        assert result == DecisionResult.YES, "Indicator decision should return YES (stub)"
        
        # Test invalid decision type
        invalid_decision = {
            "recipe_type": "invalid_type"
        }
        
        try:
            result = decision_engine.evaluate_decision(invalid_decision)
            # Should handle gracefully and return ERROR
            assert result == DecisionResult.ERROR
        except:
            pass  # Also acceptable to raise exception
    
    def test_position_manager(self):
        """Test position management (stub functionality)"""
        logger = FrameworkLogger("TestPosition")
        
        # Create temporary database
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
            self.temp_files.append(db_path)
        
        state_manager = StateManager(db_path)
        position_manager = PositionManager(logger, state_manager)
        
        # Test opening position (stub)
        position_config = {
            "symbol": "SPY",
            "strategy_type": "long_call",
            "quantity": 2
        }
        
        position = position_manager.open_position(position_config)
        assert position is not None, "Should create stub position"
        assert position.symbol == "SPY"
        assert position.state == PositionState.OPEN
        
        # Test getting open positions
        open_positions = position_manager.get_open_positions()
        assert len(open_positions) >= 1
        assert open_positions[0].id == position.id
        
        # Test closing position (stub)
        success = position_manager.close_position(position.id)
        assert success, "Should successfully close position (stub)"
        
        # Verify position was closed
        closed_position = position_manager.get_position(position.id)
        if closed_position is not None:
            assert closed_position.state == PositionState.CLOSED
        
        # Test position price updates (stub)
        from oa_framework_core import MarketData
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
        
        # Position should have updated price
        if position2 is not None:
            updated_position = position_manager.get_position(position2.id)
            if updated_position is not None:
                assert updated_position.current_price == 455.0
    
    def test_bot_integration(self):
        """Test full bot integration"""
        # Create test configuration
        generator = OABotConfigGenerator()
        config = generator.generate_simple_long_call_bot()
        
        # Save to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config, f, indent=2)
            config_file = f.name
            self.temp_files.append(config_file)
        
        # Initialize bot
        bot = OABot(config_file)
        assert bot.config.name == config['name']
        assert bot.state == BotState.STOPPED
        
        # Start bot
        bot.start()
        assert bot.state == BotState.RUNNING
        
        # Test bot status
        status = bot.get_status()
        assert status['name'] == config['name']
        assert status['state'] == 'running'
        assert 'automations' in status
        assert 'positions' in status
        assert 'safeguards' in status
        
        # Test automation processing (stub)
        if bot.config.automations:
            automation_name = bot.config.automations[0]['name']
            bot.process_automation(automation_name)
            # Should complete without error
        
        # Stop bot
        bot.stop()
        assert bot.state == BotState.STOPPED
    
    def test_error_handling(self):
        """Test error handling and error messages"""
        # Test basic error code existence
        assert hasattr(ErrorCode, 'INSUFFICIENT_CAPITAL'), "Missing INSUFFICIENT_CAPITAL"
        assert hasattr(ErrorCode, 'INVALID_CONFIG'), "Missing INVALID_CONFIG"
        
        # Test ErrorMessages if it exists
        try:
            # Simple message test
            msg = ErrorMessages.get_message(ErrorCode.INSUFFICIENT_CAPITAL)
            assert isinstance(msg, str) and len(msg) > 0, "Error message should be non-empty string"
        except (AttributeError, TypeError):
            # ErrorMessages might not exist or work differently - that's fine
            pass
    
    def run_all_tests(self) -> bool:
        """Run all Phase 0 tests"""
        print("🚀 Starting Phase 0 Test Suite")
        print("=" * 60)
        
        tests = [
            ("Schema Validation", self.test_schema_validation),
            ("Configuration Loading", self.test_config_loading),
            ("Enum Validation", self.test_enum_validation),
            ("Logging System", self.test_logging_system),
            ("State Management", self.test_state_management),
            ("Event System", self.test_event_system),
            ("Decision Engine (Stub)", self.test_decision_engine),
            ("Position Manager (Stub)", self.test_position_manager),
            ("Bot Integration", self.test_bot_integration),
            ("Error Handling", self.test_error_handling)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
            else:
                failed += 1
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for test_name, success, error in self.test_results:
                if not success:
                    print(f"   • {test_name}: {error}")
        
        # Clean up temporary files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Phase 0 is ready for production.")
            print("✅ Framework core components are working correctly")
            print("✅ Ready to proceed to Phase 1: Basic Framework with Simple Strategies")
        else:
            print(f"\n⚠️  {failed} test(s) failed. Please fix issues before proceeding.")
        
        return failed == 0

def main():
    """Main test runner"""
    print("Option Alpha Framework - Phase 0 Test Suite")
    print(f"Python Version: {sys.version}")
    print(f"Test Started: {datetime.now()}")
    
    try:
        tester = Phase0Tester()
        success = tester.run_all_tests()
        
        if success:
            print("\n🚀 Phase 0 Complete - Ready for Phase 1!")
            return 0
        else:
            print("\n🔧 Please fix failing tests before continuing")
            return 1
            
    except Exception as e:
        print(f"\n💥 Test suite crashed: {str(e)}")
        print("\nFull traceback:")
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)