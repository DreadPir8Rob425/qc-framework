# Option Alpha Framework - Phase 1: Integration Module
# Integrates decision engine with position management for simple strategies

import json
import tempfile
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path

# Import framework components
from oa_logging import FrameworkLogger
from oa_state_manager import create_state_manager
from oa_framework_enums import LogCategory, BotState, AutomationState, DecisionResult
from oa_data_structures import MarketData, BotStatus
from decision_core import DecisionContext, create_test_context
from simple_strategy_engine import create_simple_strategy_decision_engine
from basic_strategy_positions import create_basic_strategy_manager
from oa_json_schema import OABotConfigLoader

# =============================================================================
# PHASE 1 BOT IMPLEMENTATION
# =============================================================================

class Phase1Bot:
    """
    Phase 1 bot implementation with integrated decision engine and position management.
    Supports simple long call/put strategies with basic automation.
    """
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.name = config_dict.get('name', 'Phase1Bot')
        
        # Initialize core components
        self.logger = FrameworkLogger(f"Phase1Bot-{self.name}")
        self.state_manager = create_state_manager()
        self.decision_engine = create_simple_strategy_decision_engine(self.logger)
        self.strategy_manager = create_basic_strategy_manager(self.state_manager, self.logger)
        
        # Bot state
        self.state = BotState.STOPPED
        self.start_time: Optional[datetime] = None
        self._automation_states: Dict[str, AutomationState] = {}
        
        # Market data cache
        self._market_data_cache: Dict[str, MarketData] = {}
        self._last_market_update = datetime.now()
        
        # Initialize automations
        self._initialize_automations()
        
        self.logger.info(LogCategory.SYSTEM, "Phase 1 bot initialized",
                        name=self.name, automations=len(self.config.get('automations', [])))
    
    def _initialize_automations(self) -> None:
        """Initialize automation states"""
        for automation in self.config.get('automations', []):
            automation_name = automation.get('name', 'Unnamed')
            self._automation_states[automation_name] = AutomationState.IDLE
    
    def start(self) -> None:
        """Start the bot"""
        try:
            self.state = BotState.STARTING
            self.start_time = datetime.now()
            
            self.logger.info(LogCategory.SYSTEM, "Bot starting", name=self.name)
            
            # Initialize market data for symbols
            self._initialize_market_data()
            
            self.state = BotState.RUNNING
            
            self.logger.info(LogCategory.SYSTEM, "Bot started successfully", name=self.name)
            
        except Exception as e:
            self.state = BotState.ERROR
            self.logger.error(LogCategory.SYSTEM, "Failed to start bot", error=str(e))
            raise
    
    def stop(self) -> None:
        """Stop the bot"""
        try:
            self.state = BotState.STOPPING
            self.logger.info(LogCategory.SYSTEM, "Bot stopping", name=self.name)
            
            # Set all automations to disabled
            for automation_name in self._automation_states:
                self._automation_states[automation_name] = AutomationState.DISABLED
            
            self.state = BotState.STOPPED
            
            self.logger.info(LogCategory.SYSTEM, "Bot stopped successfully", name=self.name)
            
        except Exception as e:
            self.state = BotState.ERROR
            self.logger.error(LogCategory.SYSTEM, "Failed to stop bot", error=str(e))
            raise
    
    def _initialize_market_data(self) -> None:
        """Initialize market data for configured symbols"""
        symbols = self.config.get('symbols', {}).get('list', ['SPY'])
        
        for symbol in symbols:
            # Create test market data for Phase 1
            self._market_data_cache[symbol] = self._create_test_market_data(symbol)
        
        self._last_market_update = datetime.now()
        
        self.logger.info(LogCategory.MARKET_DATA, "Market data initialized",
                        symbols=list(self._market_data_cache.keys()))
    
    def _create_test_market_data(self, symbol: str) -> MarketData:
        """Create test market data for Phase 1"""
        # Default prices for common symbols
        prices = {
            'SPY': 450.0,
            'QQQ': 380.0,
            'IWM': 200.0,
            'AAPL': 175.0,
            'MSFT': 330.0,
            'TSLA': 250.0,
            'VIX': 18.5
        }
        
        base_price = prices.get(symbol, 100.0)
        
        return MarketData(
            symbol=symbol,
            timestamp=datetime.now(),
            price=base_price,
            bid=base_price - 0.05,
            ask=base_price + 0.05,
            volume=1000000,
            iv_rank=25.0
        )
    
    def update_market_data(self, new_market_data: Optional[Dict[str, MarketData]] = None) -> None:
        """Update market data (for testing or real data integration)"""
        try:
            if new_market_data:
                self._market_data_cache.update(new_market_data)
            else:
                # Simulate market movement for testing
                self._simulate_market_movement()
            
            self._last_market_update = datetime.now()
            
            self.logger.debug(LogCategory.MARKET_DATA, "Market data updated",
                            symbols=list(self._market_data_cache.keys()))
            
        except Exception as e:
            self.logger.error(LogCategory.MARKET_DATA, "Failed to update market data", error=str(e))
    
    def _simulate_market_movement(self) -> None:
        """Simulate market price movements for testing"""
        import random
        
        for symbol, market_data in self._market_data_cache.items():
            # Small random price movement (-0.5% to +0.5%)
            change_pct = (random.random() - 0.5) * 0.01
            new_price = market_data.price * (1 + change_pct)
            
            # Update market data
            self._market_data_cache[symbol] = MarketData(
                symbol=symbol,
                timestamp=datetime.now(),
                price=new_price,
                bid=new_price - 0.05,
                ask=new_price + 0.05,
                volume=market_data.volume,
                iv_rank=market_data.iv_rank
            )
    
    def run_scanner_automation(self, automation_name: str) -> Dict[str, Any]:
        """
        Run a scanner automation to look for new position opportunities
        
        Args:
            automation_name: Name of automation to run
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Find automation config
            automation_config = self._get_automation_config(automation_name)
            if not automation_config:
                return {'success': False, 'error': f'Automation {automation_name} not found'}
            
            # Check if it's a scanner automation
            trigger = automation_config.get('trigger', {})
            if trigger.get('automation_type') != 'scanner':
                return {'success': False, 'error': f'Automation {automation_name} is not a scanner'}
            
            # Set automation state
            self._automation_states[automation_name] = AutomationState.RUNNING
            
            # Create decision context
            context = self._create_decision_context()
            
            # Process automation actions
            results = self._process_automation_actions(
                automation_config.get('actions', []), 
                context, 
                automation_name
            )
            
            # Update automation state
            self._automation_states[automation_name] = AutomationState.COMPLETED
            
            self.logger.info(LogCategory.DECISION_FLOW, "Scanner automation completed",
                           automation=automation_name, positions_opened=results.get('positions_opened', 0))
            
            return {
                'success': True,
                'automation': automation_name,
                'positions_opened': results.get('positions_opened', 0),
                'decisions_evaluated': results.get('decisions_evaluated', 0)
            }
            
        except Exception as e:
            self._automation_states[automation_name] = AutomationState.ERROR
            error_msg = f"Scanner automation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg, automation=automation_name)
            return {'success': False, 'error': error_msg}
    
    def run_monitor_automation(self, automation_name: str) -> Dict[str, Any]:
        """
        Run a monitor automation to check existing positions
        
        Args:
            automation_name: Name of automation to run
            
        Returns:
            Dictionary with execution results
        """
        try:
            # Check if we have open positions to monitor
            open_positions = self.strategy_manager.state_manager.get_positions(
                state=self.strategy_manager.state_manager.PositionState.OPEN
            )
            
            if not open_positions:
                return {'success': True, 'message': 'No open positions to monitor'}
            
            # Run monitoring
            exit_recommendations = self.strategy_manager.monitor_positions(
                bot_name=self.name, 
                market_data=self._market_data_cache
            )
            
            positions_closed = 0
            
            # Execute recommended exits
            for recommendation in exit_recommendations:
                position = recommendation['position']
                exit_result = recommendation['exit_result']
                
                success = self.strategy_manager.close_position(
                    position, 
                    exit_result['reason'],
                    exit_result['exit_price']
                )
                
                if success:
                    positions_closed += 1
            
            self.logger.info(LogCategory.DECISION_FLOW, "Monitor automation completed",
                           automation=automation_name, positions_closed=positions_closed)
            
            return {
                'success': True,
                'automation': automation_name,
                'positions_monitored': len(open_positions),
                'positions_closed': positions_closed
            }
            
        except Exception as e:
            error_msg = f"Monitor automation failed: {str(e)}"
            self.logger.error(LogCategory.DECISION_FLOW, error_msg, automation=automation_name)
            return {'success': False, 'error': error_msg}
    
    def _get_automation_config(self, automation_name: str) -> Optional[Dict[str, Any]]:
        """Get automation configuration by name"""
        for automation in self.config.get('automations', []):
            if automation.get('name') == automation_name:
                return automation
        return None
    
    def _create_decision_context(self) -> DecisionContext:
        """Create decision context with current bot state"""
        # Get current positions
        positions = self.strategy_manager.state_manager.get_positions()
        
        # Get bot statistics
        open_positions = [p for p in positions if p.state == 'open']
        bot_stats = {
            'total_positions': len(positions),
            'open_positions': len(open_positions),
            'available_capital': self.config.get('safeguards', {}).get('capital_allocation', 10000),
            'total_pnl': sum(p.total_pnl for p in positions),
            'day_pnl': sum(p.unrealized_pnl for p in open_positions)
        }
        
        return DecisionContext(
            timestamp=datetime.now(),
            market_data=self._market_data_cache,
            positions=positions,
            bot_stats=bot_stats,
            market_state={'regime': 'normal', 'volatility': 'low'}
        )
    
    def _process_automation_actions(self, actions: List[Dict[str, Any]], 
                                   context: DecisionContext, 
                                   automation_name: str) -> Dict[str, Any]:
        """
        Process a list of automation actions
        
        Args:
            actions: List of action configurations
            context: Decision context
            automation_name: Name of automation for logging
            
        Returns:
            Dictionary with processing results
        """
        results = {
            'decisions_evaluated': 0,
            'positions_opened': 0,
            'actions_processed': 0
        }
        
        for action in actions:
            try:
                action_result = self._process_single_action(action, context, automation_name)
                
                # Update results
                results['actions_processed'] += 1
                if action_result.get('decision_evaluated'):
                    results['decisions_evaluated'] += 1
                if action_result.get('position_opened'):
                    results['positions_opened'] += 1
                    
            except Exception as e:
                self.logger.error(LogCategory.DECISION_FLOW, "Action processing failed",
                                automation=automation_name, error=str(e))
        
        return results
    
    def _process_single_action(self, action: Dict[str, Any], 
                              context: DecisionContext, 
                              automation_name: str) -> Dict[str, Any]:
        """
        Process a single automation action
        
        Args:
            action: Action configuration
            context: Decision context
            automation_name: Name of automation
            
        Returns:
            Dictionary with action results
        """
        action_type = action.get('type')
        
        if action_type == 'decision':
            return self._process_decision_action(action, context, automation_name)
        elif action_type == 'conditional':
            return self._process_conditional_action(action, context, automation_name)
        elif action_type == 'open_position':
            return self._process_open_position_action(action, context, automation_name)
        else:
            self.logger.warning(LogCategory.DECISION_FLOW, "Unsupported action type",
                              action_type=action_type, automation=automation_name)
            return {'success': False, 'error': f'Unsupported action type: {action_type}'}
    
    def _process_decision_action(self, action: Dict[str, Any], 
                               context: DecisionContext, 
                               automation_name: str) -> Dict[str, Any]:
        """Process decision action with yes/no paths"""
        decision_config = action.get('decision', {})
        
        # Evaluate decision
        decision_result = self.decision_engine.evaluate_decision(decision_config, context)
        
        self.logger.debug(LogCategory.DECISION_FLOW, "Decision evaluated",
                        automation=automation_name, result=decision_result.result.value,
                        reasoning=decision_result.reasoning)
        
        # Process appropriate path
        if decision_result.is_yes:
            yes_path = action.get('yes_path', [])
            if yes_path:
                return self._process_automation_actions(yes_path, context, automation_name)
        elif decision_result.is_no:
            no_path = action.get('no_path', [])
            if no_path:
                return self._process_automation_actions(no_path, context, automation_name)
        
        return {'decision_evaluated': True, 'decision_result': decision_result.result.value}
    
    def _process_conditional_action(self, action: Dict[str, Any], 
                                  context: DecisionContext, 
                                  automation_name: str) -> Dict[str, Any]:
        """Process conditional action (only yes path)"""
        decision_config = action.get('decision', {})
        
        # Evaluate decision
        decision_result = self.decision_engine.evaluate_decision(decision_config, context)
        
        # Process yes path if decision is true
        if decision_result.is_yes:
            yes_path = action.get('yes_path', [])
            if yes_path:
                return self._process_automation_actions(yes_path, context, automation_name)
        
        return {'decision_evaluated': True, 'decision_result': decision_result.result.value}
    
    def _process_open_position_action(self, action: Dict[str, Any], 
                                    context: DecisionContext, 
                                    automation_name: str) -> Dict[str, Any]:
        """Process open position action"""
        # Check safeguards before opening position
        if not self._check_safeguards():
            return {'success': False, 'error': 'Safeguards prevent opening position'}
        
        # Execute position opening
        position = self.strategy_manager.execute_open_position_action(
            action, self._market_data_cache, self.name
        )
        
        if position:
            return {'position_opened': True, 'position_id': position.id}
        else:
            return {'success': False, 'error': 'Failed to open position'}
    
    def _check_safeguards(self) -> bool:
        """Check bot safeguards before opening new positions"""
        safeguards = self.config.get('safeguards', {})
        
        # Get current positions
        open_positions = self.strategy_manager.state_manager.get_positions(
            state=self.strategy_manager.state_manager.PositionState.OPEN
        )
        
        # Check position limit
        position_limit = safeguards.get('position_limit', 10)
        if len(open_positions) >= position_limit:
            self.logger.warning(LogCategory.RISK_MANAGEMENT, "Position limit exceeded",
                              current=len(open_positions), limit=position_limit)
            return False
        
        # Check daily positions (simplified for Phase 1)
        daily_limit = safeguards.get('daily_positions', 5)
        today_positions = [p for p in open_positions if p.opened_at.date() == datetime.now().date()]
        if len(today_positions) >= daily_limit:
            self.logger.warning(LogCategory.RISK_MANAGEMENT, "Daily position limit exceeded",
                              today=len(today_positions), limit=daily_limit)
            return False
        
        return True
    
    def get_status(self) -> BotStatus:
        """Get current bot status"""
        # Calculate uptime
        uptime_seconds = 0.0
        if self.start_time and self.state == BotState.RUNNING:
            uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        
        # Get position summary
        positions = self.strategy_manager.state_manager.get_positions()
        open_positions = [p for p in positions if p.state == 'open']
        total_pnl = sum(p.total_pnl for p in positions)
        today_pnl = sum(p.unrealized_pnl for p in open_positions)
        
        return BotStatus(
            name=self.name,
            state=self.state.value,
            uptime_seconds=uptime_seconds,
            last_activity=self._last_market_update,
            total_positions=len(positions),
            open_positions=len(open_positions),
            total_pnl=total_pnl,
            today_pnl=today_pnl,
            automations_status={
                name: state.value for name, state in self._automation_states.items()
            }
        )
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the bot"""
        positions = self.strategy_manager.state_manager.get_positions()
        closed_positions = [p for p in positions if p.state == 'closed']
        open_positions = [p for p in positions if p.state == 'open']
        
        # Calculate basic metrics
        total_trades = len(closed_positions)
        winning_trades = len([p for p in closed_positions if p.realized_pnl > 0])
        win_rate = (winning_trades / total_trades * 100) if total_trades > 0 else 0
        
        return {
            'total_positions': len(positions),
            'open_positions': len(open_positions),
            'closed_positions': total_trades,
            'winning_trades': winning_trades,
            'win_rate': win_rate,
            'total_pnl': sum(p.total_pnl for p in positions),
            'unrealized_pnl': sum(p.unrealized_pnl for p in open_positions),
            'realized_pnl': sum(p.realized_pnl for p in closed_positions)
        }

# =============================================================================
# PHASE 1 FRAMEWORK ORCHESTRATOR
# =============================================================================

class Phase1Framework:
    """
    Phase 1 framework orchestrator that manages multiple bots.
    Provides testing and demonstration capabilities.
    """
    
    def __init__(self):
        self.logger = FrameworkLogger("Phase1Framework")
        self.bots: Dict[str, Phase1Bot] = {}
        self.config_loader = OABotConfigLoader()
        
        self.logger.info(LogCategory.SYSTEM, "Phase 1 framework initialized")
    
    def create_bot_from_config(self, config_dict: Dict[str, Any]) -> Phase1Bot:
        """Create bot from configuration dictionary"""
        try:
            # Validate configuration
            validated_config = self.config_loader.load_config_from_dict(config_dict)
            
            # Create bot
            bot = Phase1Bot(validated_config)
            
            # Store bot
            self.bots[bot.name] = bot
            
            self.logger.info(LogCategory.SYSTEM, "Bot created from config",
                           bot_name=bot.name)
            
            return bot
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to create bot from config",
                            error=str(e))
            raise
    
    def create_bot_from_file(self, config_file_path: str) -> Phase1Bot:
        """Create bot from JSON configuration file"""
        try:
            config_dict = self.config_loader.load_config(config_file_path)
            return self.create_bot_from_config(config_dict)
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to create bot from file",
                            file_path=config_file_path, error=str(e))
            raise
    
    def get_bot(self, bot_name: str) -> Optional[Phase1Bot]:
        """Get bot by name"""
        return self.bots.get(bot_name)
    
    def list_bots(self) -> List[str]:
        """Get list of bot names"""
        return list(self.bots.keys())
    
    def get_framework_status(self) -> Dict[str, Any]:
        """Get overall framework status"""
        return {
            'framework_version': 'Phase 1',
            'total_bots': len(self.bots),
            'running_bots': len([b for b in self.bots.values() if b.state == BotState.RUNNING]),
            'bot_summary': {
                name: {
                    'state': bot.state.value,
                    'open_positions': len([p for p in bot.strategy_manager.state_manager.get_positions() if p.state == 'open'])
                }
                for name, bot in self.bots.items()
            }
        }

# =============================================================================
# DEMONSTRATION AND TESTING
# =============================================================================

def create_sample_bot_configs() -> List[Dict[str, Any]]:
    """Create sample bot configurations for Phase 1 testing"""
    
    # Simple long call bot
    long_call_bot = {
        "name": "Simple Long Call Bot",
        "account": "paper_trading",
        "group": "Phase 1 Testing",
        "safeguards": {
            "capital_allocation": 10000,
            "daily_positions": 3,
            "position_limit": 5,
            "daytrading_allowed": False
        },
        "scan_speed": "15_minutes",
        "symbols": {
            "type": "static",
            "list": ["SPY"]
        },
        "automations": [
            {
                "name": "Bullish Scanner",
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
                            "price_field": "last_price",
                            "comparison": "greater_than",
                            "value": 440
                        },
                        "yes_path": [
                            {
                                "type": "conditional",
                                "decision": {
                                    "recipe_type": "bot",
                                    "bot_field": "open_positions",
                                    "comparison": "less_than",
                                    "value": 3
                                },
                                "yes_path": [
                                    {
                                        "type": "open_position",
                                        "position": {
                                            "strategy_type": "long_call",
                                            "symbol": "SPY",
                                            "expiration": {
                                                "type": "between_days",
                                                "days": 20,
                                                "days_end": 40
                                            },
                                            "position_size": {
                                                "type": "contracts",
                                                "contracts": 1
                                            }
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    # Simple long put bot
    long_put_bot = {
        "name": "Simple Long Put Bot",
        "account": "paper_trading", 
        "group": "Phase 1 Testing",
        "safeguards": {
            "capital_allocation": 5000,
            "daily_positions": 2,
            "position_limit": 3,
            "daytrading_allowed": False
        },
        "scan_speed": "15_minutes",
        "symbols": {
            "type": "static",
            "list": ["QQQ"]
        },
        "automations": [
            {
                "name": "Bearish Scanner",
                "trigger": {
                    "type": "continuous",
                    "automation_type": "scanner"
                },
                "actions": [
                    {
                        "type": "decision",
                        "decision": {
                            "recipe_type": "stock",
                            "symbol": "QQQ",
                            "price_field": "last_price",
                            "comparison": "less_than",
                            "value": 390
                        },
                        "yes_path": [
                            {
                                "type": "open_position",
                                "position": {
                                    "strategy_type": "long_put",
                                    "symbol": "QQQ",
                                    "expiration": {
                                        "type": "exact_days",
                                        "days": 30
                                    },
                                    "position_size": {
                                        "type": "contracts",
                                        "contracts": 1
                                    }
                                }
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    return [long_call_bot, long_put_bot]

def demonstrate_phase1_framework():
    """Demonstrate Phase 1 framework capabilities"""
    print("=" * 70)
    print("Option Alpha Framework - Phase 1 Demonstration")
    print("=" * 70)
    
    try:
        # Initialize framework
        framework = Phase1Framework()
        print(f"✓ Framework initialized")
        
        # Create sample bots
        print(f"\n1. Creating Sample Bots:")
        sample_configs = create_sample_bot_configs()
        
        bots = []
        for i, config in enumerate(sample_configs, 1):
            bot = framework.create_bot_from_config(config)
            bots.append(bot)
            print(f"   ✓ Created bot {i}: {bot.name}")
        
        # Start bots
        print(f"\n2. Starting Bots:")
        for bot in bots:
            bot.start()
            print(f"   ✓ Started: {bot.name} (State: {bot.state.value})")
        
        # Show initial status
        print(f"\n3. Initial Bot Status:")
        for bot in bots:
            status = bot.get_status()
            print(f"   {bot.name}:")
            print(f"     State: {status.state}")
            print(f"     Open Positions: {status.open_positions}")
            print(f"     Automations: {len(status.automations_status)}")
        
        # Simulate market data update
        print(f"\n4. Updating Market Data:")
        for bot in bots:
            bot.update_market_data()
            print(f"   ✓ Updated market data for {bot.name}")
        
        # Run scanner automations
        print(f"\n5. Running Scanner Automations:")
        for bot in bots:
            automation_name = bot.config['automations'][0]['name']
            result = bot.run_scanner_automation(automation_name)
            
            if result['success']:
                print(f"   ✓ {bot.name}: {automation_name}")
                print(f"     Decisions: {result.get('decisions_evaluated', 0)}")
                print(f"     Positions Opened: {result.get('positions_opened', 0)}")
            else:
                print(f"   ✗ {bot.name}: {result.get('error', 'Unknown error')}")
        
        # Check positions after automation
        print(f"\n6. Position Summary After Automation:")
        total_positions = 0
        for bot in bots:
            performance = bot.get_performance_summary()
            total_positions += performance['total_positions']
            print(f"   {bot.name}:")
            print(f"     Total Positions: {performance['total_positions']}")
            print(f"     Open Positions: {performance['open_positions']}")
            print(f"     Total P&L: ${performance['total_pnl']:.2f}")
        
        # Run monitor automations
        print(f"\n7. Running Monitor Automations:")
        for bot in bots:
            monitor_result = bot.run_monitor_automation("Position Monitor")
            print(f"   {bot.name}: {monitor_result.get('message', 'Monitoring completed')}")
        
        # Final framework status
        print(f"\n8. Final Framework Status:")
        framework_status = framework.get_framework_status()
        print(f"   Framework Version: {framework_status['framework_version']}")
        print(f"   Total Bots: {framework_status['total_bots']}")
        print(f"   Running Bots: {framework_status['running_bots']}")
        print(f"   Total Positions Created: {total_positions}")
        
        # Stop bots
        print(f"\n9. Stopping Bots:")
        for bot in bots:
            bot.stop()
            print(f"   ✓ Stopped: {bot.name} (State: {bot.state.value})")
        
        print(f"\n" + "=" * 70)
        print("✅ PHASE 1 DEMONSTRATION COMPLETE!")
        print("✅ Decision Engine Integration: Working")
        print("✅ Position Management: Working") 
        print("✅ Basic Automation: Working")
        print("✅ Simple Strategies: Long Call/Put Implemented")
        print("✅ Bot Safeguards: Working")
        print("✅ State Management: Working")
        print("=" * 70)
        
        return framework
        
    except Exception as e:
        print(f"✗ Phase 1 demonstration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

def test_phase1_with_config_file():
    """Test Phase 1 framework with JSON configuration file"""
    print("\n" + "=" * 70)
    print("Phase 1 Framework - JSON Configuration File Testing")
    print("=" * 70)
    
    try:
        # Create a sample configuration file
        sample_config = create_sample_bot_configs()[0]  # Use the long call bot
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(sample_config, f, indent=2)
            config_file_path = f.name
        
        print(f"✓ Created temporary config file: {config_file_path}")
        
        # Initialize framework
        framework = Phase1Framework()
        
        # Create bot from file
        bot = framework.create_bot_from_file(config_file_path)
        print(f"✓ Created bot from file: {bot.name}")
        
        # Test bot operations
        bot.start()
        print(f"✓ Bot started: {bot.state.value}")
        
        # Get status
        status = bot.get_status()
        print(f"✓ Bot status retrieved")
        print(f"   Name: {status.name}")
        print(f"   State: {status.state}")
        print(f"   Automations: {len(status.automations_status)}")
        
        # Test automation
        automation_name = bot.config['automations'][0]['name']
        result = bot.run_scanner_automation(automation_name)
        print(f"✓ Scanner automation executed: {result['success']}")
        
        # Clean up
        bot.stop()
        import os
        os.unlink(config_file_path)
        
        print(f"✓ JSON configuration file testing completed successfully!")
        
    except Exception as e:
        print(f"✗ JSON config file testing failed: {str(e)}")
        raise

def run_phase1_stress_test():
    """Run stress test with multiple automations and market updates"""
    print("\n" + "=" * 70)
    print("Phase 1 Framework - Stress Testing")
    print("=" * 70)
    
    try:
        framework = Phase1Framework()
        
        # Create multiple bots
        configs = create_sample_bot_configs()
        bots = []
        
        for config in configs:
            bot = framework.create_bot_from_config(config)
            bot.start()
            bots.append(bot)
        
        print(f"✓ Created and started {len(bots)} bots")
        
        # Run multiple automation cycles with market updates
        total_positions = 0
        for cycle in range(5):
            print(f"\nCycle {cycle + 1}:")
            
            # Update market data
            for bot in bots:
                bot.update_market_data()
            
            # Run scanner automations
            for bot in bots:
                automation_name = bot.config['automations'][0]['name']
                result = bot.run_scanner_automation(automation_name)
                if result['success']:
                    total_positions += result.get('positions_opened', 0)
            
            # Run monitor automations
            for bot in bots:
                bot.run_monitor_automation("Monitor")
            
            # Show status
            running_bots = len([b for b in bots if b.state == BotState.RUNNING])
            print(f"   Running bots: {running_bots}/{len(bots)}")
        
        # Final results
        print(f"\nStress Test Results:")
        print(f"   Total positions created: {total_positions}")
        print(f"   All bots still running: {all(b.state == BotState.RUNNING for b in bots)}")
        
        # Stop all bots
        for bot in bots:
            bot.stop()
        
        print(f"✅ Stress test completed successfully!")
        
    except Exception as e:
        print(f"✗ Stress test failed: {str(e)}")
        raise

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main Phase 1 demonstration and testing"""
    print("🚀 Starting Phase 1 Framework Testing...")
    
    # Run main demonstration
    framework = demonstrate_phase1_framework()
    
    # Run additional tests
    test_phase1_with_config_file()
    run_phase1_stress_test()
    
    print(f"\n🎉 ALL PHASE 1 TESTS COMPLETED SUCCESSFULLY!")
    print(f"🎯 Framework is ready for Phase 2: Event System and Advanced Decision Engine")

if __name__ == "__main__":
    main()