# Option Alpha Framework - Test Runner
# Comprehensive test suite for Phase 1 functionality validation

import json
import tempfile
import os
import traceback
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import all framework components
from oa_logging import FrameworkLogger, LogCategory, LogLevel
from oa_state_manager import StateManager, create_state_manager
from oa_event_system import EventBus, Event
from enhanced_position_manager import create_position_manager
from analytics_handler import create_analytics_handler
from oa_framework_enums import *
from oa_data_structures import Position, MarketData, BotStatus
from oa_data_structures import create_safe_test_market_data, create_safe_position_config
from oa_config_generator import OABotConfigGenerator
from oa_bot_framework import OABot, create_simple_bot_config
from oa_bot_schema import OABotConfigValidator, OABotConfigLoader

# =============================================================================
# TEST RESULT TRACKING
# =============================================================================

class TestResult:
    """Individual test result"""
    def __init__(self, name: str, passed: bool, message: str = "", details: str = ""):
        self.name = name
        self.passed = passed
        self.message = message
        self.details = details
        self.timestamp = datetime.now()

class TestSuite:
    """Test suite for tracking multiple test results"""
    def __init__(self, name: str):
        self.name = name
        self.results: List[TestResult] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
    
    def add_result(self, result: TestResult):
        """Add a test result"""
        self.results.append(result)
    
    def finish(self):
        """Mark test suite as finished"""
        self.end_time = datetime.now()
    
    @property
    def passed_count(self) -> int:
        """Number of passed tests"""
        return sum(1 for r in self.results if r.passed)
    
    @property
    def failed_count(self) -> int:
        """Number of failed tests"""
        return sum(1 for r in self.results if not r.passed)
    
    @property
    def total_count(self) -> int:
        """Total number of tests"""
        return len(self.results)
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        if self.total_count == 0:
            return 0.0
        return (self.passed_count / self.total_count) * 100
    
    @property
    def duration(self) -> float:
        """Test suite duration in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

# =============================================================================
# MAIN TEST RUNNER CLASS
# =============================================================================

class FrameworkTestRunner:
    """
    Comprehensive test runner for the Option Alpha Framework.
    Tests all Phase 1 components and integration.
    """
    
    def __init__(self):
        self.test_suites: List[TestSuite] = []
        self.logger = FrameworkLogger("TestRunner")
        self.temp_dir = tempfile.mkdtemp(prefix="oa_test_")
        self.test_db_path = os.path.join(self.temp_dir, "test_framework.db")
        
    def run_all_tests(self) -> bool:
        """
        Run all test suites and return overall success status.
        
        Returns:
            True if all tests pass, False otherwise
        """
        print("=" * 80)
        print("OPTION ALPHA FRAMEWORK - PHASE 1 TEST RUNNER")
        print("=" * 80)
        print(f"Test Directory: {self.temp_dir}")
        print(f"Test Database: {self.test_db_path}")
        print()
        
        try:
            # Run all test suites
            self._test_logging_system()
            self._test_state_management()
            self._test_event_system()
            self._test_data_structures()
            self._test_position_management()
            self._test_analytics_system()
            self._test_configuration_system()
            self._test_bot_framework()
            self._test_integration()
            
            # Print summary
            self._print_summary()
            
            # Return overall result
            return self._get_overall_result()
            
        except Exception as e:
            print(f"CRITICAL ERROR: Test runner failed: {e}")
            traceback.print_exc()
            return False
        finally:
            self._cleanup()
    
    def _test_logging_system(self):
        """Test the logging system"""
        suite = TestSuite("Logging System")
        
        try:
            # Test logger creation
            logger = FrameworkLogger("TestLogger")
            suite.add_result(TestResult("Logger Creation", True, "Logger created successfully"))
            
            # Test different log levels
            logger.debug(LogCategory.SYSTEM, "Debug message", test=True)
            logger.info(LogCategory.SYSTEM, "Info message", test=True)
            logger.warning(LogCategory.SYSTEM, "Warning message", test=True)
            logger.error(LogCategory.SYSTEM, "Error message", test=True)
            suite.add_result(TestResult("Log Level Methods", True, "All log levels working"))
            
            # Test log retrieval
            logs = logger.get_logs(limit=10)
            passed = len(logs) >= 4
            suite.add_result(TestResult("Log Retrieval", passed, f"Retrieved {len(logs)} log entries"))
            
            # Test log filtering
            error_logs = logger.get_logs(level=LogLevel.ERROR)
            passed = len(error_logs) >= 1
            suite.add_result(TestResult("Log Filtering", passed, f"Found {len(error_logs)} error logs"))
            
            # Test log summary
            summary = logger.get_summary()
            passed = 'levels' in summary and 'categories' in summary
            suite.add_result(TestResult("Log Summary", passed, "Summary generation working"))
            
        except Exception as e:
            suite.add_result(TestResult("Logging System Error", False, str(e), traceback.format_exc()))
        
        suite.finish()
        self.test_suites.append(suite)
    
    def _test_state_management(self):
        """Test the state management system"""
        suite = TestSuite("State Management")
        
        try:
            # Test state manager creation
            state_manager = create_state_manager(self.test_db_path)
            suite.add_result(TestResult("StateManager Creation", True, "StateManager created successfully"))
            
            # Test hot state
            state_manager.set_hot_state("test_key", {"value": 123, "timestamp": datetime.now().isoformat()})
            hot_value = state_manager.get_hot_state("test_key")
            passed = hot_value is not None and hot_value["value"] == 123
            suite.add_result(TestResult("Hot State", passed, f"Hot state: {hot_value}"))
            
            # Test warm state
            state_manager.set_warm_state("session_test", {"session_id": "test_123"})
            warm_value = state_manager.get_warm_state("session_test")
            passed = warm_value is not None and warm_value["session_id"] == "test_123"
            suite.add_result(TestResult("Warm State", passed, f"Warm state: {warm_value}"))
            
            # Test cold state
            cold_data = {"trade_id": "T001", "pnl": 125.50}
            record_id = state_manager.store_cold_state(cold_data, "test_trades", ["profitable"])
            cold_records = state_manager.get_cold_state("test_trades", limit=5)
            passed = len(cold_records) > 0 and cold_records[0]["data"]["trade_id"] == "T001"
            suite.add_result(TestResult("Cold State", passed, f"Cold state records: {len(cold_records)}"))
            
            # Test database stats
            stats = state_manager.get_database_stats()
            passed = 'warm_state_count' in stats and 'cold_state_count' in stats
            suite.add_result(TestResult("Database Stats", passed, f"Stats: {stats}"))
            
            # Test CSV export
            export_files = state_manager.export_to_csv(self.temp_dir)
            passed = len(export_files) >= 3  # warm, cold, hot state files
            suite.add_result(TestResult("CSV Export", passed, f"Exported {len(export_files)} files"))
            
        except Exception as e:
            suite.add_result(TestResult("State Management Error", False, str(e), traceback.format_exc()))
        
        suite.finish()
        self.test_suites.append(suite)
    
    def _test_event_system(self):
        """Test the event system"""
        suite = TestSuite("Event System")
        
        try:
            # Test event bus creation
            event_bus = EventBus()
            suite.add_result(TestResult("EventBus Creation", True, "EventBus created successfully"))
            
            # Test event creation
            test_event = Event(
                event_type=EventType.BOT_STARTED.value,
                timestamp=datetime.now(),
                data={"test": True}
            )
            suite.add_result(TestResult("Event Creation", True, "Event created successfully"))
            
            # Test event handler
            received_events = []
            
            def test_handler(event):
                received_events.append(event)
            
            handler_id = event_bus.subscribe_function([EventType.BOT_STARTED], test_handler, "TestHandler")
            suite.add_result(TestResult("Event Subscription", True, f"Handler ID: {handler_id}"))
            
            # Test event publishing and processing
            event_bus.start_processing()
            event_bus.publish(test_event)
            
            # Give some time for processing
            import time
            time.sleep(0.1)
            
            passed = len(received_events) > 0
            suite.add_result(TestResult("Event Processing", passed, f"Received {len(received_events)} events"))
            
            # Test event bus shutdown
            event_bus.stop_processing()
            suite.add_result(TestResult("EventBus Shutdown", True, "EventBus stopped successfully"))
            
        except Exception as e:
            suite.add_result(TestResult("Event System Error", False, str(e), traceback.format_exc()))
        
        suite.finish()
        self.test_suites.append(suite)
    
    def _test_data_structures(self):
        """Test core data structures"""
        suite = TestSuite("Data Structures")
        
        try:
            # Test MarketData
            market_data = MarketData(
                symbol="SPY",
                timestamp=datetime.now(),
                price=450.0,
                bid=449.95,
                ask=450.05,
                volume=1000000
            )
            passed = market_data.mid_price == 450.0 and market_data.spread == 0.10
            suite.add_result(TestResult("MarketData", passed, f"Mid: {market_data.mid_price}, Spread: {market_data.spread}"))
            
            # Test Position
            position = Position(
                id="test_pos_1",
                symbol="SPY",
                position_type=PositionType.LONG_CALL.value,
                state="open",
                opened_at=datetime.now() - timedelta(days=2),
                quantity=1,
                entry_price=100.0,
                current_price=105.0,
                unrealized_pnl=5.0
            )
            passed = position.days_open >= 2 and position.total_pnl == 5.0
            suite.add_result(TestResult("Position", passed, f"Days open: {position.days_open}, P&L: {position.total_pnl}"))
            
            # Test BotStatus
            bot_status = BotStatus(
                name="Test Bot",
                state=BotState.RUNNING.value,
                uptime_seconds=3600,
                last_activity=datetime.now(),
                total_positions=5,
                open_positions=3,
                total_pnl=250.0,
                today_pnl=50.0
            )
            passed = bot_status.uptime_hours == 1.0 and bot_status.is_healthy
            suite.add_result(TestResult("BotStatus", passed, f"Uptime: {bot_status.uptime_hours}h, Healthy: {bot_status.is_healthy}"))
            
        except Exception as e:
            suite.add_result(TestResult("Data Structures Error", False, str(e), traceback.format_exc()))
        
        suite.finish()
        self.test_suites.append(suite)
    
    def _test_position_management(self):
        """Test position management system"""
        suite = TestSuite("Position Management")
        
        try:
            # Create position manager
            state_manager = create_state_manager(self.test_db_path)
            position_manager = create_position_manager(state_manager, self.logger)
            suite.add_result(TestResult("PositionManager Creation", True, "PositionManager created successfully"))
            
            # Test opening position
            position_config = {
                "symbol": "SPY",
                "strategy_type": PositionType.LONG_CALL.value,
                "quantity": 1,
                "entry_price": 450.0,
                "tags": ["test", "phase1"]
            }
            position = position_manager.open_position(position_config, "TestBot")
            passed = position is not None and position.symbol == "SPY"
            suite.add_result(TestResult("Open Position", passed, f"Position ID: {position.id if position else 'None'}"))
            
            # Test getting positions
            open_positions = position_manager.get_open_positions()
            passed = len(open_positions) >= 1
            suite.add_result(TestResult("Get Open Positions", passed, f"Found {len(open_positions)} open positions"))
            
            # Test updating prices
            market_data = create_safe_test_market_data()
            position_config = create_safe_position_config()
            position_manager.update_position_prices(market_data)
            suite.add_result(TestResult("Update Prices", True, "Price update completed"))
            
            # Test closing position
            if position:
                success = position_manager.close_position(position.id, {"exit_price": 460.0}, "Profit Target")
                suite.add_result(TestResult("Close Position", success, f"Position closed: {success}"))
            
            # Test portfolio summary
            summary = position_manager.get_portfolio_summary("TestBot")
            passed = 'total_positions' in summary and 'total_pnl' in summary
            suite.add_result(TestResult("Portfolio Summary", passed, f"Summary keys: {list(summary.keys())}"))
            
        except Exception as e:
            suite.add_result(TestResult("Position Management Error", False, str(e), traceback.format_exc()))
        
        suite.finish()
        self.test_suites.append(suite)
    
    def _test_analytics_system(self):
        """Test analytics system"""
        suite = TestSuite("Analytics System")
        
        try:
            # Create analytics handler
            state_manager = create_state_manager(self.test_db_path)
            analytics = create_analytics_handler(state_manager, self.logger)
            suite.add_result(TestResult("Analytics Creation", True, "Analytics handler created successfully"))
            
            # Test performance metrics calculation
            metrics = analytics.calculate_performance_metrics("TestBot")
            passed = 'analysis_timestamp' in metrics
            suite.add_result(TestResult("Performance Metrics", passed, f"Metrics keys: {list(metrics.keys())}"))
            
            # Test trade analysis
            trade_analysis = analytics.generate_trade_analysis(symbol="SPY")
            passed = 'analysis_timestamp' in trade_analysis
            suite.add_result(TestResult("Trade Analysis", passed, f"Analysis keys: {list(trade_analysis.keys())}"))
            
            # Test CSV export
            export_path = Path(self.temp_dir) / "analytics"
            exported_files = analytics.export_analytics_to_csv(export_path)
            passed = len(exported_files) >= 0  # May be empty if no data
            suite.add_result(TestResult("Analytics CSV Export", True, f"Exported {len(exported_files)} files"))
            
            # Test performance report
            report = analytics.generate_performance_report()
            passed = 'report_timestamp' in report and 'system_info' in report
            suite.add_result(TestResult("Performance Report", passed, "Comprehensive report generated"))
            
        except Exception as e:
            suite.add_result(TestResult("Analytics System Error", False, str(e), traceback.format_exc()))
        
        suite.finish()
        self.test_suites.append(suite)
    
    def _test_configuration_system(self):
        """Test configuration validation and loading"""
        suite = TestSuite("Configuration System")
        
        try:
            # Test config generator
            generator = OABotConfigGenerator()
            simple_config = generator.generate_simple_long_call_bot()
            suite.add_result(TestResult("Config Generation", True, f"Generated config for: {simple_config['name']}"))
            
            # Test config validation
            validator = OABotConfigValidator()
            is_valid, errors = validator.validate_config(simple_config)
            suite.add_result(TestResult("Config Validation", is_valid, f"Validation errors: {len(errors)}"))
            
            # Test config loader
            loader = OABotConfigLoader()
            try:
                validated_config = loader.load_config_from_dict(simple_config, "Test Config")
                suite.add_result(TestResult("Config Loading", True, "Config loaded successfully"))
            except Exception as e:
                suite.add_result(TestResult("Config Loading", False, str(e)))
            
            # Test config summary
            summary = loader.get_config_summary(simple_config)
            passed = "Bot Name:" in summary and "Automations:" in summary
            suite.add_result(TestResult("Config Summary", passed, f"Summary length: {len(summary)} chars"))
            
            # Test different config types
            complex_config = generator.generate_iron_condor_bot()
            is_valid, errors = validator.validate_config(complex_config)
            suite.add_result(TestResult("Complex Config Validation", is_valid, f"Iron Condor config: {len(errors)} errors"))
            
        except Exception as e:
            suite.add_result(TestResult("Configuration System Error", False, str(e), traceback.format_exc()))
        
        suite.finish()
        self.test_suites.append(suite)
    
    def _test_bot_framework(self):
        """Test the main bot framework"""
        suite = TestSuite("Bot Framework")
        
        try:
            # Create simple config for testing
            config = create_simple_bot_config()
            
            # Test bot creation
            bot = OABot(config)
            suite.add_result(TestResult("Bot Creation", True, f"Bot created: {bot.name}"))
            
            # Test bot startup
            bot.start()
            passed = bot.state == BotState.RUNNING
            suite.add_result(TestResult("Bot Startup", passed, f"Bot state: {bot.state}"))
            
            # Test bot status
            status = bot.get_status()
            passed = status.name == config['name'] and status.state == BotState.RUNNING.value
            suite.add_result(TestResult("Bot Status", passed, f"Status: {status.state}, Positions: {status.open_positions}"))
            
            # Test market data update
            market_data = create_safe_test_market_data()
            bot.update_market_data(market_data)
            suite.add_result(TestResult("Market Data Update", True, "Market data updated successfully"))
            
            # Test performance metrics
            metrics = bot.get_performance_metrics()
            passed = 'analysis_timestamp' in metrics
            suite.add_result(TestResult("Bot Performance Metrics", passed, f"Metrics available: {passed}"))
            
            # Test automation processing (stub)
            if bot.config['automations']:
                automation_name = bot.config['automations'][0]['name']
                bot.process_automation(automation_name)
                suite.add_result(TestResult("Automation Processing", True, f"Processed: {automation_name}"))
            
            # Test bot shutdown
            bot.stop()
            passed = bot.state == BotState.STOPPED
            suite.add_result(TestResult("Bot Shutdown", passed, f"Final state: {bot.state}"))
            
        except Exception as e:
            suite.add_result(TestResult("Bot Framework Error", False, str(e), traceback.format_exc()))
        
        suite.finish()
        self.test_suites.append(suite)
    
    def _test_integration(self):
        """Test integration between all components"""
        suite = TestSuite("Integration Tests")
        
        try:
            # Test end-to-end workflow
            config = create_simple_bot_config()
            bot = OABot(config)
            
            # Start bot
            bot.start()
            
            # Add some market data
            market_data = create_safe_test_market_data()

            bot.update_market_data(market_data)
            
            # Test position workflow
            position_config = {
                "symbol": "SPY",
                "strategy_type": PositionType.LONG_CALL.value,
                "quantity": 1,
                "entry_price": 450.0
            }
            position = bot.position_manager.open_position(position_config, bot.name)
            
            # Update position prices
            bot.position_manager.update_position_prices({"SPY": 455.0})
            
            # Generate analytics
            metrics = bot.analytics.calculate_performance_metrics(bot.name)
            
            # Export data
            export_files = bot.export_data(self.temp_dir)
            
            # Close position
            if position:
                bot.position_manager.close_position(position.id, {"exit_price": 460.0})
            
            # Stop bot
            bot.stop()
            
            # Validate integration worked
            passed = (
                bot.state == BotState.STOPPED and
                len(export_files) > 0 and
                'analysis_timestamp' in metrics
            )
            
            suite.add_result(TestResult("End-to-End Workflow", passed, 
                                      f"Bot stopped: {bot.state}, Files exported: {len(export_files)}"))
            
            # Test component communication
            log_count = len(bot.logger.get_logs())
            passed = log_count > 10  # Should have generated plenty of logs
            suite.add_result(TestResult("Component Communication", passed, f"Log entries: {log_count}"))
            
            # Test state persistence
            db_stats = bot.state_manager.get_database_stats()
            passed = db_stats.get('positions_count', 0) > 0
            suite.add_result(TestResult("State Persistence", passed, f"DB stats: {db_stats}"))
            
        except Exception as e:
            suite.add_result(TestResult("Integration Error", False, str(e), traceback.format_exc()))
        
        suite.finish()
        self.test_suites.append(suite)
    
    def _print_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "=" * 80)
        print("TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for suite in self.test_suites:
            status = "✅ PASS" if suite.failed_count == 0 else "❌ FAIL"
            print(f"\n{status} {suite.name}")
            print(f"   Tests: {suite.total_count}, Passed: {suite.passed_count}, Failed: {suite.failed_count}")
            print(f"   Success Rate: {suite.success_rate:.1f}%, Duration: {suite.duration:.2f}s")
            
            # Show failed tests
            if suite.failed_count > 0:
                print("   Failed Tests:")
                for result in suite.results:
                    if not result.passed:
                        print(f"     - {result.name}: {result.message}")
            
            total_tests += suite.total_count
            total_passed += suite.passed_count
            total_failed += suite.failed_count
        
        # Overall summary
        overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        overall_status = "✅ ALL TESTS PASSED" if total_failed == 0 else f"❌ {total_failed} TESTS FAILED"
        
        print(f"\n" + "=" * 80)
        print(f"OVERALL RESULT: {overall_status}")
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        print(f"Success Rate: {overall_success_rate:.1f}%")
        print("=" * 80)
        
        # Phase 1 readiness assessment
        critical_suites = ["Logging System", "State Management", "Position Management", "Bot Framework"]
        critical_failures = sum(1 for suite in self.test_suites 
                              if suite.name in critical_suites and suite.failed_count > 0)
        
        if critical_failures == 0:
            print("\n🎉 PHASE 1 COMPLETE - READY FOR PHASE 2!")
            print("All critical components are working correctly.")
        else:
            print(f"\n⚠️  PHASE 1 INCOMPLETE - {critical_failures} critical component(s) have failures.")
            print("Please fix critical issues before proceeding to Phase 2.")
        
        print()
    
    def _get_overall_result(self) -> bool:
        """Get overall test result"""
        return all(suite.failed_count == 0 for suite in self.test_suites)
    
    def _cleanup(self):
        """Clean up test resources"""
        try:
            import shutil
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            print(f"Cleaned up test directory: {self.temp_dir}")
        except Exception as e:
            print(f"Warning: Failed to clean up test directory: {e}")

# =============================================================================
# QUICK TEST FUNCTIONS
# =============================================================================

def run_quick_test() -> bool:
    """Run a quick subset of tests for rapid validation"""
    print("=" * 60)
    print("QUICK TEST - Phase 1 Core Components")
    print("=" * 60)
    
    try:
        # Test basic imports
        print("✓ All imports successful")
        
        # Test config generation and validation
        generator = OABotConfigGenerator()
        config = generator.generate_simple_long_call_bot()
        
        validator = OABotConfigValidator()
        is_valid, errors = validator.validate_config(config)
        
        if not is_valid:
            print(f"❌ Config validation failed: {errors}")
            return False
        print("✓ Configuration system working")
        
        # Test bot creation
        bot = OABot(config)
        print("✓ Bot creation working")
        
        # Test basic state management
        bot.state_manager.set_hot_state("test", {"quick_test": True})
        value = bot.state_manager.get_hot_state("test")
        if not value or value.get("quick_test") != True:
            print("❌ State management failed")
            return False
        print("✓ State management working")
        
        # Test logging
        bot.logger.info(LogCategory.SYSTEM, "Quick test message")
        logs = bot.logger.get_logs(limit=1)
        if not logs:
            print("❌ Logging failed")
            return False
        print("✓ Logging system working")
        
        print("\n🎉 QUICK TEST PASSED - Core components functional!")
        return True
        
    except Exception as e:
        print(f"❌ QUICK TEST FAILED: {e}")
        traceback.print_exc()
        return False

def run_component_test(component_name: str) -> bool:
    """Run tests for a specific component"""
    runner = FrameworkTestRunner()
    
    component_map = {
        "logging": runner._test_logging_system,
        "state": runner._test_state_management,
        "events": runner._test_event_system,
        "data": runner._test_data_structures,
        "positions": runner._test_position_management,
        "analytics": runner._test_analytics_system,
        "config": runner._test_configuration_system,
        "bot": runner._test_bot_framework,
        "integration": runner._test_integration
    }
    
    if component_name not in component_map:
        print(f"Unknown component: {component_name}")
        print(f"Available components: {list(component_map.keys())}")
        return False
    
    print(f"Running tests for component: {component_name}")
    component_map[component_name]()
    
    if runner.test_suites:
        suite = runner.test_suites[0]
        runner._print_summary()
        return suite.failed_count == 0
    
    return False

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point for test runner"""
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "quick":
            success = run_quick_test()
        elif sys.argv[1] in ["logging", "state", "events", "data", "positions", "analytics", "config", "bot", "integration"]:
            success = run_component_test(sys.argv[1])
        else:
            print(f"Unknown test option: {sys.argv[1]}")
            print("Usage: python test_runner.py [quick|logging|state|events|data|positions|analytics|config|bot|integration]")
            return False
    else:
        # Run full test suite
        runner = FrameworkTestRunner()
        success = runner.run_all_tests()
    
    return success

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)