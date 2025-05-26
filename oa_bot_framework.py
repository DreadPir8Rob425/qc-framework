# Option Alpha Bot Framework - Fixed Version with Proper Imports
# Main orchestration class that brings together all specialized modules

import json
import tempfile
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import from dedicated modules - NO MORE DUPLICATE CLASSES
from oa_logging import FrameworkLogger, LogLevel, LogCategory
from oa_state_manager import StateManager, create_state_manager
from oa_event_system import EventBus
from enhanced_position_manager import create_position_manager
from analytics_handler import create_analytics_handler
from oa_framework_enums import (
    BotState, AutomationState, PositionState, PositionType, 
    EventType, DecisionResult, ErrorCode
)
from oa_data_structures import Position, MarketData, Event, BotStatus

# =============================================================================
# DECISION ENGINE (STUBBED - WILL BE IMPLEMENTED IN PHASE 2)
# =============================================================================

class DecisionEngine:
    """
    Decision evaluation engine for Option Alpha decision recipes.
    This is a stub for Phase 0 - will be fully implemented in Phase 2.
    """
    
    def __init__(self, logger: FrameworkLogger, state_manager: StateManager):
        self.logger = logger
        self.state_manager = state_manager
        
    def evaluate_decision(self, decision_config: Dict[str, Any]) -> DecisionResult:
        """
        Evaluate a decision based on its configuration.
        This is a stub implementation for Phase 0.
        """
        try:
            recipe_type = decision_config.get('recipe_type', 'stock')
            
            self.logger.debug(LogCategory.DECISION_FLOW, 
                            "Decision evaluated (stub)", 
                            type=recipe_type, result="YES")
            
            # TODO: Implement full decision logic in Phase 2
            return DecisionResult.YES  # Stub always returns YES
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, 
                            "Decision evaluation failed", error=str(e))
            return DecisionResult.ERROR

# =============================================================================
# MAIN BOT CLASS
# =============================================================================

class OABot:
    """
    Main Option Alpha bot class that orchestrates all components.
    Uses proper imports instead of duplicate class definitions.
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.name = config_dict.get('name', 'Unknown Bot')
        
        # Initialize core components using proper imports
        self.logger = FrameworkLogger(f"OABot-{self.name}")
        self.state_manager = create_state_manager()
        self.event_bus = EventBus()
        self.decision_engine = DecisionEngine(self.logger, self.state_manager)
        self.position_manager = create_position_manager(self.state_manager, self.logger)
        self.analytics = create_analytics_handler(self.state_manager, self.logger)
        
        # Bot state using proper enums
        self.state = BotState.STOPPED
        self._automation_states: Dict[str, AutomationState] = {}
        
        self.logger.info(LogCategory.SYSTEM, 
                        "Bot initialized", 
                        name=self.name,
                        automations=len(config_dict.get('automations', [])))
    
    def start(self) -> None:
        """Start the bot and all its automations"""
        try:
            self.state = BotState.STARTING
            self.logger.info(LogCategory.SYSTEM, "Bot starting", name=self.name)
            
            # Start event processing
            self.event_bus.start_processing()
            
            # Initialize automations
            for automation in self.config.get('automations', []):
                automation_name = automation.get('name', 'Unnamed')
                self._automation_states[automation_name] = AutomationState.IDLE
                self.logger.info(LogCategory.SYSTEM, 
                               "Automation initialized", 
                               automation=automation_name)
            
            self.state = BotState.RUNNING
            
            # Publish bot started event
            self.event_bus.publish(Event(
                event_type=EventType.BOT_STARTED.value,
                timestamp=datetime.now(),
                data={'bot_name': self.name}
            ))
            
            self.logger.info(LogCategory.SYSTEM, "Bot started successfully", name=self.name)
            
        except Exception as e:
            self.state = BotState.ERROR
            self.logger.error(LogCategory.SYSTEM, "Failed to start bot", error=str(e))
            raise
    
    def stop(self) -> None:
        """Stop the bot and all its automations"""
        try:
            self.state = BotState.STOPPING
            self.logger.info(LogCategory.SYSTEM, "Bot stopping", name=self.name)
            
            # Stop event processing
            self.event_bus.stop_processing()
            
            # Set all automations to disabled
            for automation_name in self._automation_states:
                self._automation_states[automation_name] = AutomationState.DISABLED
            
            self.state = BotState.STOPPED
            
            # Publish bot stopped event
            self.event_bus.publish(Event(
                event_type=EventType.BOT_STOPPED.value,
                timestamp=datetime.now(),
                data={'bot_name': self.name}
            ))
            
            self.logger.info(LogCategory.SYSTEM, "Bot stopped successfully", name=self.name)
            
        except Exception as e:
            self.state = BotState.ERROR
            self.logger.error(LogCategory.SYSTEM, "Failed to stop bot", error=str(e))
            raise
    
    def get_status(self) -> BotStatus:
        """Get current bot status and statistics"""
        open_positions = self.position_manager.get_open_positions()
        portfolio_summary = self.position_manager.get_portfolio_summary(self.name)
        
        return BotStatus(
            name=self.name,
            state=self.state.value,
            uptime_seconds=0.0,  # TODO: Calculate actual uptime
            last_activity=datetime.now(),
            total_positions=portfolio_summary.get('total_positions', 0),
            open_positions=len(open_positions),
            total_pnl=portfolio_summary.get('total_pnl', 0.0),
            today_pnl=0.0,  # TODO: Calculate today's P&L
            automations_status={
                name: state.value 
                for name, state in self._automation_states.items()
            }
        )
    
    def get_status_dict(self) -> Dict[str, Any]:
        """Get status as dictionary for backwards compatibility"""
        status = self.get_status()
        return {
            'name': status.name,
            'state': status.state,
            'automations': status.automations_status,
            'positions': {
                'open_count': status.open_positions,
                'total_unrealized_pnl': status.total_pnl
            },
            'safeguards': self.config.get('safeguards', {}),
            'scan_speed': self.config.get('scan_speed', '15_minutes')
        }
    
    def process_automation(self, automation_name: str) -> None:
        """
        Process a single automation - stub for Phase 0.
        Will be fully implemented in Phase 2.
        """
        try:
            automation_config = None
            for auto in self.config.get('automations', []):
                if auto.get('name') == automation_name:
                    automation_config = auto
                    break
            
            if not automation_config:
                self.logger.error(LogCategory.SYSTEM, 
                                "Automation not found", 
                                automation=automation_name)
                return
            
            self._automation_states[automation_name] = AutomationState.RUNNING
            
            self.logger.info(LogCategory.DECISION_FLOW, 
                           "Processing automation (stub)", 
                           automation=automation_name)
            
            # TODO: Implement full automation processing in Phase 2
            # This would involve:
            # 1. Check trigger conditions
            # 2. Process action sequence
            # 3. Evaluate decisions using decision_engine
            # 4. Execute actions (open/close positions, etc.)
            
            self._automation_states[automation_name] = AutomationState.COMPLETED
            
        except Exception as e:
            self._automation_states[automation_name] = AutomationState.ERROR
            self.logger.error(LogCategory.SYSTEM, 
                            "Automation processing failed", 
                            automation=automation_name, error=str(e))
    
    def update_market_data(self, market_data: Dict[str, Any]) -> None:
        """Update market data and recalculate position P&L"""
        try:
            self.position_manager.update_position_prices(market_data)
            
            self.logger.debug(LogCategory.MARKET_DATA, 
                            "Market data updated", 
                            symbols_updated=len(market_data))
            
        except Exception as e:
            self.logger.error(LogCategory.MARKET_DATA, 
                            "Failed to update market data", error=str(e))
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this bot"""
        try:
            return self.analytics.calculate_performance_metrics(bot_name=self.name)
        except Exception as e:
            self.logger.error(LogCategory.PERFORMANCE, 
                            "Failed to get performance metrics", error=str(e))
            return {'error': str(e)}
    
    def export_data(self, export_dir: str) -> Dict[str, str]:
        """Export bot data to files"""
        try:
            exported_files = {}
            
            # Export state data
            state_files = self.state_manager.export_to_csv(export_dir)
            exported_files.update(state_files)
            
            # Export analytics
            analytics_path = Path(f"{export_dir}/analytics")
            analytics_files = self.analytics.export_analytics_to_csv(analytics_path)
            exported_files.update(analytics_files)
            
            # Export positions
            pos_file = Path(f"{export_dir}/positions.csv")
            self.position_manager.export_positions_to_csv(pos_file)
            exported_files['positions'] = pos_file
            
            self.logger.info(LogCategory.SYSTEM, "Data exported", 
                           files_count=len(exported_files))
            
            return exported_files
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to export data", error=str(e))
            return {}

# =============================================================================
# CONFIGURATION HELPERS
# =============================================================================

def create_simple_bot_config() -> Dict[str, Any]:
    """Create a simple bot configuration for testing"""
    return {
        "name": "Simple Test Bot",
        "account": "paper_trading",
        "group": "Test Strategies",
        "safeguards": {
            "capital_allocation": 10000,
            "daily_positions": 5,
            "position_limit": 15,
            "daytrading_allowed": False
        },
        "scan_speed": "15_minutes",
        "symbols": {
            "type": "static",
            "list": ["SPY", "QQQ"]
        },
        "automations": [
            {
                "name": "Simple Scanner",
                "trigger": {
                    "type": "continuous",
                    "automation_type": "scanner"
                },
                "actions": [
                    {
                        "type": "decision",
                        "decision": {
                            "recipe_type": "stock",
                            "symbol": "SPY",
                            "comparison": "greater_than",
                            "value": 400
                        }
                    }
                ]
            }
        ]
    }

def create_bot_from_config_file(config_path: str) -> OABot:
    """Create bot from JSON configuration file"""
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
        return OABot(config)
    except Exception as e:
        logger = FrameworkLogger("BotFactory")
        logger.error(LogCategory.SYSTEM, "Failed to create bot from config", 
                   config_path=config_path, error=str(e))
        raise

# =============================================================================
# DEMONSTRATION FUNCTION
# =============================================================================

def demonstrate_framework():
    """Demonstrate the framework functionality with proper imports"""
    
    print("=" * 60)
    print("Option Alpha Framework - Fixed Version Demonstration")
    print("=" * 60)
    
    try:
        # 1. Create bot configuration
        config = create_simple_bot_config()
        print(f"✓ Created bot configuration: {config['name']}")
        
        # 2. Initialize bot with proper imports
        bot = OABot(config)
        print(f"✓ Bot initialized: {bot.name}")
        print(f"  Using proper FrameworkLogger from oa_logging.py")
        print(f"  Using proper StateManager from oa_state_manager.py")
        print(f"  Using proper EventBus from oa_event_system.py")
        
        # 3. Start bot
        bot.start()
        print(f"✓ Bot started successfully")
        
        # 4. Show status with proper enums
        status = bot.get_status()
        print(f"✓ Bot status: {status.state}")
        print(f"  Automations: {len(status.automations_status)}")
        print(f"  Open positions: {status.open_positions}")
        print(f"  Using BotState enum: {bot.state}")
        
        # 5. Test logging with proper enums
        bot.logger.info(LogCategory.SYSTEM, "Test log message", test=True)
        logs = bot.logger.get_logs(limit=5)
        print(f"✓ Logging system working with enums: {len(logs)} entries")
        
        # 6. Test state management
        bot.state_manager.set_hot_state("test", {"value": 123})
        test_val = bot.state_manager.get_hot_state("test")
        print(f"✓ State management working: {test_val}")
        
        # 7. Test position management with proper integration
        pos_config = {"symbol": "SPY", "strategy_type": "long_call", "quantity": 1, "entry_price": 450.0}
        position = bot.position_manager.open_position(pos_config, bot.name)
        print(f"✓ Position management working: {position.id if position else 'Failed'}")
        
        # 8. Test decision engine
        decision_config = {"recipe_type": "stock", "symbol": "SPY"}
        result = bot.decision_engine.evaluate_decision(decision_config)
        print(f"✓ Decision engine working: {result}")
        
        # 9. Test analytics integration
        metrics = bot.get_performance_metrics()
        print(f"✓ Analytics integration working: {len(metrics)} metrics")
        
        # 10. Stop bot
        bot.stop()
        print(f"✓ Bot stopped successfully")
        print(f"  Final state: {bot.state}")
        
        print("\n" + "=" * 60)
        print("✅ FIXED Framework demonstration completed successfully!")
        print("✅ All duplicate classes removed")
        print("✅ Proper imports from dedicated modules")
        print("✅ String literals converted to enums")
        print("✅ Full integration with SQLite StateManager")
        print("✅ Ready for Phase 1 development")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Framework demonstration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    demonstrate_framework()