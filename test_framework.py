#!/usr/bin/env python3
"""
Option Alpha Framework - Test Suite
Tests the modular framework components and validates functionality
"""

import sys
import json
import tempfile
import os
from datetime import datetime
import traceback
from pathlib import Path

# Test imports to catch any issues early
try:
    from oa_constants import FrameworkConstants, SystemDefaults, ValidationRules
    from oa_enums import *
    from oa_json_schema import OABotConfigLoader, OABotConfigValidator, BotConfiguration
    from oa_config_generator import OABotConfigGenerator
    from csv_state_manager import CSVStateManager
    from oa_bot_framework import OABot, create_bot_from_template, FrameworkLogger
    
    print("✅ All framework imports successful")
    
except ImportError as e:
    print(f"❌ Import Error: {e}")
    print("Make sure all framework files are in the same directory")
    sys.exit(1)

class FrameworkTester:
    """Test suite for the modular framework components"""
    
    def __init__(self):
        self.test_results = []
        self.temp_files = []
        self.temp_dirs = []
    
    def run_test(self, test_name: str, test_func) -> bool:
        """Run a single test and record results"""
        print(f"\n🧪 Testing: {test_name}")
        try:
            test_func()
            print(f"✅ {test_name}: PASSED")
            self.test_results.append((test_name, True, None))
            return True
        except Exception as e:
            print(f"❌ {test_name}: FAILED - {str(e)}")
            self.test_results.append((test_name, False, str(e)))
            return False
    
    def test_constants_and_enums(self):
        """Test constants and enums modules"""
        # Test constants access
        assert FrameworkConstants.VERSION == "1.0.0"
        assert FrameworkConstants.FRAMEWORK_NAME == "OA-QC Framework"
        assert SystemDefaults.MAX_LOG_ENTRIES == 10000
        assert ValidationRules.MAX_BOT_NAME_LENGTH == 100
        
        # Test enums
        assert ScanSpeed.FIVE_MINUTES.value == "5_minutes"
        assert PositionType.IRON_CONDOR.value == "iron_condor"
        assert LogLevel.INFO.value == "info"
        assert BotState.RUNNING.value == "running"
        
        # Test enum validation
        speed = EnumValidator.validate_scan_speed("1_minute")
        assert speed == ScanSpeed.ONE_MINUTE
        
        # Test error messages
        msg = ErrorMessages.get_message(ErrorCode.MISSING_REQUIRED_FIELD, field="symbol")
        assert "symbol" in msg
    
    def test_config_validation(self):
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
        
        # Save to temporary file
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
    
    def test_config_generation(self):
        """Test configuration generation"""
        generator = OABotConfigGenerator()
        
        # Test different generators
        configs = [
            generator.generate_simple_long_call_bot(),
            generator.generate_iron_condor_bot(),
            generator.generate_0dte_samurai_bot(),
            generator.generate_simple_put_selling_bot(),
            generator.generate_comprehensive_bot()
        ]
        
        for i, config in enumerate(configs):
            assert 'name' in config
            assert 'safeguards' in config
            assert 'automations' in config
            assert isinstance(config['automations'], list)
            assert len(config['automations']) > 0
            
            # Validate each generated config
            validator = OABotConfigValidator()
            is_valid, errors = validator.validate_config(config)
            assert is_valid, f"Generated config {i} failed validation: {errors}"
    
    def test_csv_state_manager(self):
        """Test CSV state management"""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='oa_test_')
        self.temp_dirs.append(temp_dir)
        
        state_manager = CSVStateManager(data_dir=temp_dir)
        
        # Test hot state
        test_data = {"test": "hot_state", "value": 123}
        state_manager.set_hot_state("test_hot", test_data)
        retrieved = state_manager.get_hot_state("test_hot")
        assert retrieved == test_data
        
        # Test warm state
        session_data = {"session_id": "test_123", "started": datetime.now().isoformat()}
        state_manager.set_warm_state("session_test", session_data)
        retrieved_session = state_manager.get_warm_state("session_test")
        assert retrieved_session['session_id'] == session_data['session_id']
        
        # Test position storage
        position_data = {
            'id': 'test_pos_001',
            'symbol': 'SPY',
            'position_type': 'long_call',
            'state': 'open',
            'quantity': 1,
            'entry_price': 450.0,
            'current_price': 450.0,
            'unrealized_pnl': 0.0,
            'realized_pnl': 0.0,
            'opened_at': datetime.now().isoformat(),
            'tags': ['test']
        }
        
        state_manager.store_position(position_data)
        positions = state_manager.get_positions(symbol="SPY")
        assert len(positions) >= 1
        assert positions[0]['symbol'] == "SPY"
        
        # Test trade logging
        state_manager.log_trade({
            'symbol': 'SPY',
            'action': 'OPEN',
            'position_type': 'long_call',
            'quantity': 1,
            'price': 450.0,
            'bot_name': 'Test Bot'
        })
        
        # Test analytics storage
        state_manager.store_analytics({
            'total_return': 15.5,
            'sharpe_ratio': 1.2,
            'max_drawdown': -5.2
        }, "performance")
        
        # Test summary generation
        summary = state_manager.generate_summary_report()
        assert 'backtest_id' in summary
        assert 'data_files' in summary
    
    def test_framework_logger(self):
        """Test framework logging"""
        logger = FrameworkLogger("TestLogger")
        
        # Test different log levels
        logger.debug(LogCategory.SYSTEM, "Debug message", test=True)
        logger.info(LogCategory.TRADE_EXECUTION, "Info message", symbol="SPY")
        logger.warning(LogCategory.DECISION_FLOW, "Warning message")
        logger.error(LogCategory.MARKET_DATA, "Error message", error_code=404)
        
        # Test log retrieval
        all_logs = logger.get_logs_for_csv()
        assert len(all_logs) >= 4
        
        # Verify log structure
        for log in all_logs:
            assert 'timestamp' in log
            assert 'level' in log
            assert 'category' in log
            assert 'message' in log
            assert 'data' in log
    
    def test_bot_integration(self):
        """Test full bot integration"""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='oa_bot_test_')
        self.temp_dirs.append(temp_dir)
        
        # Create bot from template
        bot = create_bot_from_template('simple_call', data_dir=temp_dir)
        assert bot.config.name == "Simple SPY Long Call Bot"
        assert bot.state == BotState.STOPPED
        
        # Start bot
        bot.start()
        assert bot.state == BotState.RUNNING
        
        # Test bot status
        status = bot.get_status()
        assert status['name'] == bot.config.name
        assert status['state'] == 'running'
        assert 'automations' in status
        assert 'positions' in status
        assert 'backtest_id' in status
        
        # Test automation processing
        if bot.config.automations:
            automation_name = bot.config.automations[0]['name']
            success = bot.process_automation(automation_name)
            assert success, f"Automation {automation_name} should process successfully"
        
        # Test simulation
        simulation_results = bot.run_backtest_simulation(steps=3)
        assert 'steps_completed' in simulation_results
        assert simulation_results['steps_completed'] == 3
        
        # Stop bot
        bot.stop()
        assert bot.state == BotState.STOPPED
        
        # Test finalization
        result = bot.finalize_backtest(upload_to_s3=False)
        assert 'backtest_id' in result
        assert 'summary' in result
    
    def test_factory_functions(self):
        """Test factory functions"""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='oa_factory_test_')
        self.temp_dirs.append(temp_dir)
        
        # Test template creation
        templates = ['simple_call', 'iron_condor', '0dte_samurai', 'put_selling', 'comprehensive']
        
        for template_name in templates:
            bot = create_bot_from_template(template_name, data_dir=temp_dir)
            assert bot is not None
            assert bot.config.name is not None
            assert len(bot.config.automations) > 0
        
        # Test invalid template
        try:
            create_bot_from_template('invalid_template')
            assert False, "Should raise ValueError for invalid template"
        except ValueError:
            pass  # Expected
    
    def cleanup(self):
        """Clean up temporary files and directories"""
        # Clean up temporary files
        for temp_file in self.temp_files:
            try:
                if os.path.exists(temp_file):
                    os.unlink(temp_file)
            except:
                pass
        
        # Clean up temporary directories
        for temp_dir in self.temp_dirs:
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
            except:
                pass
    
    def run_all_tests(self) -> bool:
        """Run all framework tests"""
        print("🚀 Starting Option Alpha Framework Test Suite")
        print("=" * 70)
        
        tests = [
            ("Constants and Enums", self.test_constants_and_enums),
            ("Config Validation", self.test_config_validation),
            ("Config Loading", self.test_config_loading),
            ("Config Generation", self.test_config_generation),
            ("CSV State Manager", self.test_csv_state_manager),
            ("Framework Logger", self.test_framework_logger),
            ("Bot Integration", self.test_bot_integration),
            ("Factory Functions", self.test_factory_functions)
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            if self.run_test(test_name, test_func):
                passed += 1
            else:
                failed += 1
        
        # Clean up
        self.cleanup()
        
        # Print summary
        print("\n" + "=" * 70)
        print("📊 TEST SUMMARY")
        print("=" * 70)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/(passed+failed)*100):.1f}%")
        
        if failed > 0:
            print(f"\n❌ FAILED TESTS:")
            for test_name, success, error in self.test_results:
                if not success:
                    print(f"   • {test_name}: {error}")
        
        if failed == 0:
            print("\n🎉 ALL TESTS PASSED!")
            print("✅ Modular framework components working correctly")
            print("✅ CSV data export and state management functional")
            print("✅ Bot lifecycle and automation processing operational")
            print("✅ Ready for Phase 1: QuantConnect Integration")
            print("\n🚀 Framework is production-ready for backtesting!")
        else:
            print(f"\n