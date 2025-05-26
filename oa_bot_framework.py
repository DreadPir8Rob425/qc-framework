# Option Alpha Bot Framework - Main Integration Module
# Brings together all components for a complete OA bot framework

import logging
import json
import tempfile
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

# Import all framework components
from oa_constants import FrameworkConstants, SystemDefaults
from oa_enums import *
from oa_json_schema import OABotConfigLoader, BotConfiguration
from oa_config_generator import OABotConfigGenerator
from csv_state_manager import CSVStateManager

class FrameworkLogger:
    """
    Framework logging system with CSV output capability.
    Simplified version for Phase 0 - focuses on CSV export compatibility.
    """
    
    def __init__(self, name: str = "OAFramework", max_entries: int = SystemDefaults.MAX_LOG_ENTRIES):
        self.name = name
        self.max_entries = max_entries
        self._log_entries: List[Dict[str, Any]] = []
        self._setup_standard_logger()
    
    def _setup_standard_logger(self) -> None:
        """Setup standard Python logger"""
        self._standard_logger = logging.getLogger(self.name)
        if not self._standard_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self._standard_logger.addHandler(handler)
            self._standard_logger.setLevel(logging.INFO)
    
    def log(self, level: LogLevel, category: LogCategory, message: str, **kwargs) -> None:
        """Log a message with level and category"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'level': level.value,
            'category': category.value,
            'message': message,
            'data': json.dumps(kwargs) if kwargs else ''
        }
        
        self._log_entries.append(entry)
        
        # Maintain max entries limit
        if len(self._log_entries) > self.max_entries:
            self._log_entries = self._log_entries[-self.max_entries:]
        
        # Also log to standard logger
        self._log_to_standard(level, category, message, **kwargs)
    
    def _log_to_standard(self, level: LogLevel, category: LogCategory, message: str, **kwargs):
        """Log to standard Python logger"""
        formatted_message = f"[{category.value.upper()}] {message}"
        if kwargs:
            formatted_message += f" | Data: {kwargs}"
        
        if level == LogLevel.DEBUG:
            self._standard_logger.debug(formatted_message)
        elif level == LogLevel.INFO:
            self._standard_logger.info(formatted_message)
        elif level == LogLevel.WARNING:
            self._standard_logger.warning(formatted_message)
        elif level == LogLevel.ERROR:
            self._standard_logger.error(formatted_message)
        elif level == LogLevel.CRITICAL:
            self._standard_logger.critical(formatted_message)
    
    def info(self, category: LogCategory, message: str, **kwargs) -> None:
        """Log info message"""
        self.log(LogLevel.INFO, category, message, **kwargs)
    
    def warning(self, category: LogCategory, message: str, **kwargs) -> None:
        """Log warning message"""
        self.log(LogLevel.WARNING, category, message, **kwargs)
    
    def error(self, category: LogCategory, message: str, **kwargs) -> None:
        """Log error message"""
        self.log(LogLevel.ERROR, category, message, **kwargs)
    
    def debug(self, category: LogCategory, message: str, **kwargs) -> None:
        """Log debug message"""
        self.log(LogLevel.DEBUG, category, message, **kwargs)
    
    def get_logs_for_csv(self) -> List[Dict[str, Any]]:
        """Get logs formatted for CSV export"""
        return self._log_entries.copy()

class StubDecisionEngine:
    """
    Stub decision engine for Phase 0.
    All decisions return YES to allow testing of framework components.
    """
    
    def __init__(self, logger: FrameworkLogger):
        self.logger = logger
    
    def evaluate_decision(self, decision_config: Dict[str, Any]) -> DecisionResult:
        """
        Stub decision evaluation - always returns YES for Phase 0.
        """
        try:
            recipe_type = decision_config.get('recipe_type', 'unknown')
            self.logger.debug(LogCategory.DECISION_FLOW, 
                            f"Evaluating {recipe_type} decision (stub)", 
                            config=decision_config)
            
            # Phase 0: Always return YES to allow testing
            return DecisionResult.YES
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, 
                            "Decision evaluation failed", error=str(e))
            return DecisionResult.ERROR

class StubPositionManager:
    """
    Stub position manager for Phase 0.
    Creates fake positions to test framework functionality.
    """
    
    def __init__(self, logger: FrameworkLogger, state_manager: CSVStateManager):
        self.logger = logger
        self.state_manager = state_manager
        self._position_counter = 0
    
    def open_position(self, position_config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Stub position opening - creates fake position for testing.
        """
        try:
            self._position_counter += 1
            position_id = f"STUB_POS_{self._position_counter:04d}"
            
            # Create stub position data
            position_data = {
                'id': position_id,
                'symbol': position_config.get('symbol', 'SPY'),
                'position_type': position_config.get('strategy_type', 'long_call'),
                'state': 'open',
                'quantity': 1,
                'entry_price': 100.0,  # Stub price
                'current_price': 100.0,
                'unrealized_pnl': 0.0,
                'realized_pnl': 0.0,
                'opened_at': datetime.now().isoformat(),
                'tags': ['stub_position'],
                'legs': []  # Simplified for stub
            }
            
            # Store in state manager
            self.state_manager.store_position(position_data)
            
            self.logger.info(LogCategory.SYSTEM, "Bot starting", name=self.config.name)
            
            # Initialize automations
            for automation in self.config.automations:
                automation_name = automation.get('name', 'Unnamed')
                self._automation_states[automation_name] = AutomationState.IDLE
                self.logger.info(LogCategory.SYSTEM, 
                               "Automation initialized", 
                               automation=automation_name)
            
            # Log bot start to state manager
            self.state_manager.log_framework_event(
                "bot_started",
                f"Bot {self.config.name} started successfully",
                bot_name=self.config.name,
                automations=len(self.config.automations)
            )
            
            self.state = BotState.RUNNING
            self.logger.info(LogCategory.SYSTEM, "Bot started successfully", name=self.config.name)
            
        except Exception as e:
            self.state = BotState.ERROR
            self.logger.error(LogCategory.SYSTEM, "Failed to start bot", error=str(e))
            raise
    
    def stop(self) -> None:
        """Stop the bot and all its automations"""
        try:
            self.state = BotState.STOPPING
            self.logger.info(LogCategory.SYSTEM, "Bot stopping", name=self.config.name)
            
            # Set all automations to disabled
            for automation_name in self._automation_states:
                self._automation_states[automation_name] = AutomationState.DISABLED
            
            # Log bot stop to state manager
            self.state_manager.log_framework_event(
                "bot_stopped",
                f"Bot {self.config.name} stopped",
                bot_name=self.config.name
            )
            
            self.state = BotState.STOPPED
            self.logger.info(LogCategory.SYSTEM, "Bot stopped successfully", name=self.config.name)
            
        except Exception as e:
            self.state = BotState.ERROR
            self.logger.error(LogCategory.SYSTEM, "Failed to stop bot", error=str(e))
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status and statistics"""
        try:
            # Get position statistics
            open_positions = self.state_manager.get_positions(state='open')
            
            return {
                'name': self.config.name,
                'state': self.state.value,
                'backtest_id': self.state_manager.get_backtest_id(),
                'automations': {
                    name: state.value 
                    for name, state in self._automation_states.items()
                },
                'positions': {
                    'open_count': len(open_positions),
                    'total_unrealized_pnl': sum(pos.get('unrealized_pnl', 0) for pos in open_positions)
                },
                'safeguards': self.config.safeguards,
                'scan_speed': self.config.scan_speed,
                'data_directory': str(self.state_manager.get_data_directory())
            }
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to get bot status", error=str(e))
            return {'error': str(e)}
    
    def process_automation(self, automation_name: str) -> bool:
        """
        Process a single automation. This is a stub for Phase 0.
        """
        try:
            # Find automation config
            automation_config = None
            for auto in self.config.automations:
                if auto.get('name') == automation_name:
                    automation_config = auto
                    break
            
            if not automation_config:
                self.logger.error(LogCategory.SYSTEM, 
                                "Automation not found", 
                                automation=automation_name)
                return False
            
            self._automation_states[automation_name] = AutomationState.RUNNING
            
            self.logger.info(LogCategory.DECISION_FLOW, 
                           "Processing automation (stub)", 
                           automation=automation_name)
            
            # Stub automation processing
            success = self._process_actions(automation_config.get('actions', []))
            
            if success:
                self._automation_states[automation_name] = AutomationState.COMPLETED
            else:
                self._automation_states[automation_name] = AutomationState.ERROR
            
            return success
            
        except Exception as e:
            self._automation_states[automation_name] = AutomationState.ERROR
            self.logger.error(LogCategory.SYSTEM, 
                            "Automation processing failed", 
                            automation=automation_name, error=str(e))
            return False
    
    def _process_actions(self, actions: List[Dict[str, Any]]) -> bool:
        """
        Process a list of actions. Stub implementation for Phase 0.
        """
        try:
            for i, action in enumerate(actions):
                action_type = action.get('type')
                self.logger.debug(LogCategory.DECISION_FLOW, 
                                f"Processing action {i+1}: {action_type}")
                
                if action_type == 'decision':
                    # Evaluate decision and follow appropriate path
                    decision_result = self.decision_engine.evaluate_decision(action.get('decision', {}))
                    
                    if decision_result == DecisionResult.YES:
                        yes_actions = action.get('yes_path', [])
                        if yes_actions:
                            self._process_actions(yes_actions)
                    elif decision_result == DecisionResult.NO:
                        no_actions = action.get('no_path', [])
                        if no_actions:
                            self._process_actions(no_actions)
                
                elif action_type == 'open_position':
                    # Open position using stub position manager
                    position_config = action.get('position', {})
                    position = self.position_manager.open_position(position_config)
                    
                    if position:
                        # Log trade
                        self.state_manager.log_trade({
                            'symbol': position['symbol'],
                            'action': 'OPEN',
                            'position_type': position['position_type'],
                            'quantity': position['quantity'],
                            'price': position['entry_price'],
                            'bot_name': self.config.name
                        })
                
                elif action_type == 'notification':
                    # Log notification
                    message = action.get('message', 'No message provided')
                    self.logger.info(LogCategory.SYSTEM, f"Notification: {message}")
                
                elif action_type == 'tag_bot':
                    # Add tags to bot (store in warm state)
                    tags = action.get('tags', [])
                    self.state_manager.set_warm_state('bot_tags', tags, 'tags')
                    self.logger.info(LogCategory.SYSTEM, f"Bot tagged: {tags}")
            
            return True
            
        except Exception as e:
            self.logger.error(LogCategory.DECISION_FLOW, "Action processing failed", error=str(e))
            return False
    
    def run_backtest_simulation(self, steps: int = 10) -> Dict[str, Any]:
        """
        Run a simple backtest simulation for demonstration purposes.
        This simulates running automations multiple times.
        
        Args:
            steps: Number of simulation steps to run
            
        Returns:
            Dictionary with simulation results
        """
        try:
            self.logger.info(LogCategory.SYSTEM, 
                           f"Starting backtest simulation with {steps} steps")
            
            simulation_results = {
                'steps_completed': 0,
                'positions_opened': 0,
                'errors': 0,
                'automations_run': 0
            }
            
            for step in range(steps):
                self.logger.debug(LogCategory.SYSTEM, f"Simulation step {step + 1}")
                
                # Process each automation
                for automation in self.config.automations:
                    automation_name = automation.get('name')
                    try:
                        success = self.process_automation(automation_name)
                        if success:
                            simulation_results['automations_run'] += 1
                        else:
                            simulation_results['errors'] += 1
                    except Exception as e:
                        simulation_results['errors'] += 1
                        self.logger.error(LogCategory.SYSTEM, 
                                        f"Error in step {step + 1}", error=str(e))
                
                simulation_results['steps_completed'] = step + 1
            
            # Get final position count
            open_positions = self.state_manager.get_positions(state='open')
            simulation_results['positions_opened'] = len(open_positions)
            
            # Store simulation results
            self.state_manager.store_analytics(simulation_results, 'simulation')
            
            self.logger.info(LogCategory.PERFORMANCE, 
                           "Backtest simulation completed", 
                           **simulation_results)
            
            return simulation_results
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Simulation failed", error=str(e))
            return {'error': str(e)}
    
    def finalize_backtest(self, upload_to_s3: bool = True) -> Dict[str, Any]:
        """
        Finalize the backtest by exporting logs and uploading to S3.
        
        Args:
            upload_to_s3: Whether to upload results to S3
            
        Returns:
            Dictionary with finalization results
        """
        try:
            # Export logs to CSV
            log_entries = self.logger.get_logs_for_csv()
            if log_entries:
                # Store logs in state manager
                for entry in log_entries:
                    self.state_manager.log_framework_event(
                        entry['level'],
                        entry['message'],
                        category=entry['category'],
                        timestamp=entry['timestamp'],
                        data=entry['data']
                    )
            
            # Get final bot status
            final_status = self.get_status()
            self.state_manager.store_analytics(final_status, 'final_status')
            
            # Finalize through state manager
            result = self.state_manager.finalize_backtest(upload_to_s3=upload_to_s3)
            
            self.logger.info(LogCategory.SYSTEM, 
                           "Backtest finalized", 
                           backtest_id=result.get('backtest_id'),
                           s3_uploaded=result.get('s3_uploaded', False))
            
            return result
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Backtest finalization failed", error=str(e))
            return {'error': str(e)}

# =============================================================================
# FRAMEWORK FACTORY FUNCTIONS
# =============================================================================

def create_bot_from_config_file(config_path: str, data_dir: str = None, s3_bucket: str = None) -> OABot:
    """
    Factory function to create a bot from a configuration file.
    
    Args:
        config_path: Path to JSON configuration file
        data_dir: Directory for CSV data files
        s3_bucket: Optional S3 bucket for uploading results
        
    Returns:
        Configured OABot instance
    """
    return OABot(config_path=config_path, data_dir=data_dir, s3_bucket=s3_bucket)

def create_bot_from_template(template_name: str, data_dir: str = None, s3_bucket: str = None) -> OABot:
    """
    Factory function to create a bot from a predefined template.
    
    Args:
        template_name: Name of template ('simple_call', 'iron_condor', '0dte_samurai', etc.)
        data_dir: Directory for CSV data files  
        s3_bucket: Optional S3 bucket for uploading results
        
    Returns:
        Configured OABot instance
    """
    generator = OABotConfigGenerator()
    
    template_map = {
        'simple_call': generator.generate_simple_long_call_bot,
        'iron_condor': generator.generate_iron_condor_bot,
        '0dte_samurai': generator.generate_0dte_samurai_bot,
        'put_selling': generator.generate_simple_put_selling_bot,
        'comprehensive': generator.generate_comprehensive_bot
    }
    
    if template_name not in template_map:
        raise ValueError(f"Unknown template: {template_name}. Available: {list(template_map.keys())}")
    
    config = template_map[template_name]()
    return OABot(config_dict=config, data_dir=data_dir, s3_bucket=s3_bucket)

# =============================================================================
# DEMONSTRATION FUNCTION
# =============================================================================

def demonstrate_framework():
    """Demonstrate the complete framework functionality"""
    
    print("=" * 70)
    print("Option Alpha Bot Framework - Complete Demonstration")
    print("=" * 70)
    
    try:
        # 1. Create bot from template
        print("\n1. Creating bot from 0DTE Samurai template...")
        bot = create_bot_from_template('0dte_samurai', data_dir='demo_backtest')
        print(f"✓ Bot created: {bot.config.name}")
        print(f"   Backtest ID: {bot.state_manager.get_backtest_id()}")
        
        # 2. Start bot
        print("\n2. Starting bot...")
        bot.start()
        print("✓ Bot started successfully")
        
        # 3. Show bot status
        print("\n3. Bot Status:")
        status = bot.get_status()
        for key, value in status.items():
            if isinstance(value, dict):
                print(f"   {key}:")
                for sub_key, sub_value in value.items():
                    print(f"     {sub_key}: {sub_value}")
            else:
                print(f"   {key}: {value}")
        
        # 4. Run simulation
        print("\n4. Running backtest simulation...")
        simulation_results = bot.run_backtest_simulation(steps=5)
        print("✓ Simulation completed:")
        for key, value in simulation_results.items():
            print(f"   {key}: {value}")
        
        # 5. Process individual automation
        print("\n5. Testing individual automation...")
        if bot.config.automations:
            automation_name = bot.config.automations[0]['name']
            success = bot.process_automation(automation_name)
            print(f"✓ Automation '{automation_name}' processed: {success}")
        
        # 6. Check positions
        print("\n6. Position Summary:")
        positions = bot.state_manager.get_positions()
        print(f"   Total positions: {len(positions)}")
        for pos in positions[:3]:  # Show first 3
            print(f"   - {pos['id']}: {pos['symbol']} {pos['position_type']} ({pos['state']})")
        
        # 7. Stop bot
        print("\n7. Stopping bot...")
        bot.stop()
        print("✓ Bot stopped successfully")
        
        # 8. Finalize backtest
        print("\n8. Finalizing backtest...")
        finalization_result = bot.finalize_backtest(upload_to_s3=False)  # Don't upload for demo
        print("✓ Backtest finalized:")
        if 'summary' in finalization_result:
            summary = finalization_result['summary']
            print(f"   Duration: {summary.get('end_time', 'N/A')}")
            if 'statistics' in summary:
                stats = summary['statistics']
                print(f"   Positions: {stats.get('positions', {}).get('total_positions', 0)}")
                print(f"   Trades: {stats.get('trades', {}).get('total_trades', 0)}")
        
        print(f"   Local data: {finalization_result.get('local_path', 'N/A')}")
        
        print("\n" + "=" * 70)
        print("✅ FRAMEWORK DEMONSTRATION COMPLETE!")
        print("🎯 Phase 0: Core framework working correctly")
        print("📊 CSV data exported successfully")  
        print("🔧 Ready for Phase 1: QuantConnect integration")
        print("=" * 70)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Framework demonstration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = demonstrate_framework()
    if not success:
        exit(1)TRADE_EXECUTION, 
                           "Position opened (stub)", 
                           position_id=position_id, 
                           symbol=position_data['symbol'])
            
            return position_data
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, 
                            "Failed to open position", error=str(e))
            return None
    
    def close_position(self, position_id: str) -> bool:
        """
        Stub position closing.
        """
        try:
            # In a real implementation, we'd update the position in the state manager
            self.logger.info(LogCategory.TRADE_EXECUTION, 
                           "Position closed (stub)", 
                           position_id=position_id)
            return True
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, 
                            "Failed to close position", 
                            position_id=position_id, error=str(e))
            return False

class OABot:
    """
    Main Option Alpha bot class that orchestrates all components.
    This is the primary interface for creating and running OA bots.
    """
    
    def __init__(self, config_path: str = None, config_dict: Dict[str, Any] = None, 
                 data_dir: str = None, s3_bucket: str = None):
        """
        Initialize bot with configuration.
        
        Args:
            config_path: Path to JSON configuration file
            config_dict: Configuration dictionary (alternative to file)
            data_dir: Directory for CSV data files
            s3_bucket: Optional S3 bucket for uploading results
        """
        
        # Load and validate configuration
        self.config_loader = OABotConfigLoader()
        
        if config_path:
            self.config_dict = self.config_loader.load_config(config_path)
        elif config_dict:
            self.config_dict = self.config_loader.load_config_from_dict(config_dict, "provided_config")
        else:
            raise ValueError("Must provide either config_path or config_dict")
        
        self.config = BotConfiguration.from_dict(self.config_dict)
        
        # Initialize core components
        self.logger = FrameworkLogger(f"OABot-{self.config.name}")
        self.state_manager = CSVStateManager(data_dir=data_dir, s3_bucket=s3_bucket)
        self.decision_engine = StubDecisionEngine(self.logger)
        self.position_manager = StubPositionManager(self.logger, self.state_manager)
        
        # Bot state
        self.state = BotState.STOPPED
        self._automation_states: Dict[str, AutomationState] = {}
        
        self.logger.info(LogCategory.SYSTEM, 
                        "Bot initialized", 
                        name=self.config.name,
                        automations=len(self.config.automations),
                        backtest_id=self.state_manager.get_backtest_id())
    
    def start(self) -> None:
        """Start the bot and initialize automations"""
        try:
            self.state = BotState.STARTING
            self.logger.info(LogCategory.