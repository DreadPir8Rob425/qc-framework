#!/usr/bin/env python3
# Option Alpha Framework - Validation Script
# Quick validation to check if all modules can be imported correctly

import sys
import importlib
from pathlib import Path

def validate_module_imports():
    """Validate that all framework modules can be imported"""
    
    modules_to_test = [
        'oa_framework_enums',
        'oa_constants', 
        'oa_logging',
        'oa_data_structures',
        'oa_state_manager',
        'oa_event_system',
        'enhanced_position_manager',
        'analytics_handler',
        'enhanced_decision_engine',
        'market_data_integration',
        'oa_config_generator',
        'oa_bot_framework',
        'strategy_execution_engine'
    ]
    
    results = {}
    
    print("🔍 Validating Framework Module Imports")
    print("=" * 50)
    
    for module_name in modules_to_test:
        try:
            # Try to import the module
            module = importlib.import_module(module_name)
            results[module_name] = {
                'status': 'SUCCESS',
                'error': None,
                'has_classes': len([attr for attr in dir(module) if not attr.startswith('_')]) > 0
            }
            print(f"✅ {module_name}: OK")
            
        except ImportError as e:
            results[module_name] = {
                'status': 'IMPORT_ERROR',
                'error': str(e),
                'has_classes': False
            }
            print(f"❌ {module_name}: Import Error - {str(e)}")
            
        except Exception as e:
            results[module_name] = {
                'status': 'OTHER_ERROR', 
                'error': str(e),
                'has_classes': False
            }
            print(f"⚠️  {module_name}: Other Error - {str(e)}")
    
    print("\n" + "=" * 50)
    
    # Summary
    successful = sum(1 for r in results.values() if r['status'] == 'SUCCESS')
    total = len(results)
    
    print(f"📊 SUMMARY: {successful}/{total} modules imported successfully")
    
    if successful == total:
        print("🎉 All modules are working correctly!")
        return True
    else:
        print("❌ Some modules have issues that need to be resolved")
        
        # Show details of failed modules
        failed_modules = [name for name, result in results.items() 
                         if result['status'] != 'SUCCESS']
        
        print(f"\n🔧 Failed modules ({len(failed_modules)}):")
        for module_name in failed_modules:
            result = results[module_name]
            print(f"   - {module_name}: {result['status']} - {result['error']}")
        
        return False

def test_basic_functionality():
    """Test basic functionality of key components"""
    
    print("\n🧪 Testing Basic Functionality")
    print("=" * 50)
    
    try:
        # Test enums
        from oa_framework_enums import LogLevel, LogCategory, DecisionResult
        print("✅ Enums: OK")
        
        # Test logging
        from oa_logging import FrameworkLogger
        logger = FrameworkLogger("TestLogger")
        logger.info(LogCategory.SYSTEM, "Test message")
        print("✅ Logging: OK")
        
        # Test data structures
        from oa_data_structures import create_test_market_data, create_test_position
        market_data = create_test_market_data()
        position = create_test_position()
        print("✅ Data Structures: OK")
        
        # Test state manager
        from oa_state_manager import create_state_manager
        state_manager = create_state_manager(":memory:")  # In-memory SQLite
        state_manager.set_hot_state("test", {"value": 123})
        test_value = state_manager.get_hot_state("test")
        assert test_value["value"] == 123
        print("✅ State Manager: OK")
        
        # Test config generator
        from oa_config_generator import OABotConfigGenerator
        generator = OABotConfigGenerator()
        config = generator.generate_simple_long_call_bot()
        assert isinstance(config, dict)
        assert 'name' in config
        print("✅ Config Generator: OK")
        
        # Test decision engine
        from enhanced_decision_engine import create_enhanced_decision_engine
        decision_engine = create_enhanced_decision_engine(logger, state_manager)
        print("✅ Decision Engine: OK")
        
        # Test position manager
        from enhanced_position_manager import create_position_manager
        position_manager = create_position_manager(state_manager, logger)
        print("✅ Position Manager: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Basic functionality test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_integration():
    """Test integration between components"""
    
    print("\n🔗 Testing Component Integration")
    print("=" * 50)
    
    try:
        from oa_logging import FrameworkLogger
        from oa_framework_enums import LogCategory
        from oa_state_manager import create_state_manager
        from oa_config_generator import OABotConfigGenerator
        from oa_bot_framework import OABot
        
        # Create components
        logger = FrameworkLogger("IntegrationTest")
        state_manager = create_state_manager(":memory:")
        
        # Generate bot config
        generator = OABotConfigGenerator()
        config = generator.generate_simple_long_call_bot()
        
        # Create bot
        bot = OABot(config)
        
        # Test bot lifecycle
        bot.start()
        status = bot.get_status()
        assert status.name == config['name']
        bot.stop()
        
        print("✅ Bot Integration: OK")
        
        # Test market data integration
        from market_data_integration import create_market_data_manager
        from oa_event_system import EventBus
        
        event_bus = EventBus()
        market_data_manager = create_market_data_manager(logger, event_bus)
        market_state = market_data_manager.get_current_market_state()
        assert isinstance(market_state, dict)
        
        print("✅ Market Data Integration: OK")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main validation function"""
    
    print("🚀 Option Alpha Framework Validation")
    print("=" * 60)
    
    # Step 1: Check module imports
    imports_ok = validate_module_imports()
    
    if not imports_ok:
        print("\n❌ Cannot proceed to functionality tests due to import errors")
        return False
    
    # Step 2: Test basic functionality  
    functionality_ok = test_basic_functionality()
    
    if not functionality_ok:
        print("\n❌ Cannot proceed to integration tests due to functionality errors")
        return False
    
    # Step 3: Test integration
    integration_ok = test_integration()
    
    print("\n" + "=" * 60)
    
    if imports_ok and functionality_ok and integration_ok:
        print("🎉 VALIDATION PASSED: Framework is ready for use!")
        print("✅ All modules import correctly")
        print("✅ Basic functionality working")
        print("✅ Component integration working")
        print("\nNext steps:")
        print("- Run final_framework_demo.py for complete demonstration")
        print("- Create your first bot configuration")
        print("- Start backtesting!")
        return True
    else:
        print("❌ VALIDATION FAILED: Issues need to be resolved")
        print("\nPlease fix the issues above before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)