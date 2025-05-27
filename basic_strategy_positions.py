# Option Alpha Framework - Phase 1: Basic Strategy Position Management
# Implements position creation and management for simple long call/put strategies

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
import uuid

from oa_framework_enums import PositionType, PositionState, LogCategory
from oa_data_structures import Position, OptionLeg, MarketData, BotSafeguards
from oa_logging import FrameworkLogger

# =============================================================================
# POSITION FACTORY FOR SIMPLE STRATEGIES
# =============================================================================

class SimpleStrategyPositionFactory:
    """
    Factory class for creating positions for simple Option Alpha strategies.
    Handles long calls, long puts, and basic position configuration.
    """
    
    def __init__(self, logger: FrameworkLogger):
        self.logger = logger
        
        # Position type mapping
        self.strategy_types = {
            'equity': self._create_equity_position,
            'long_call': self._create_long_call_position,
            'long_put': self._create_long_put_position,
            'long_call_spread': self._create_long_call_spread_position,
            'long_put_spread': self._create_long_put_spread_position
        }
    
    def create_position(self, position_config: Dict[str, Any], 
                       market_data: Optional[Dict[str, MarketData]] = None,
                       bot_name: Optional[str] = None) -> Optional[Position]:
        """
        Create a position based on configuration
        
        Args:
            position_config: Position configuration from automation
            market_data: Current market data for pricing
            bot_name: Name of bot creating the position
            
        Returns:
            Position object if successful, None otherwise
        """
        try:
            strategy_type = position_config.get('strategy_type', 'long_call')
            symbol = position_config.get('symbol', 'SPY')
            
            # Get factory method
            factory_method = self.strategy_types.get(strategy_type)
            if not factory_method:
                raise ValueError(f"Unsupported strategy type: {strategy_type}")
            
            # Create position using appropriate factory method
            position = factory_method(position_config, market_data, bot_name)
            
            if position:
                self.logger.info(LogCategory.TRADE_EXECUTION, "Position created",
                               position_id=position.id, strategy_type=strategy_type,
                               symbol=symbol, bot_name=bot_name)
            
            return position
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Failed to create position",
                            error=str(e), config=position_config)
            return None
    
    def _create_equity_position(self, config: Dict[str, Any], 
                              market_data: Optional[Dict[str, MarketData]],
                              bot_name: Optional[str]) -> Position:
        """Create simple equity position"""
        symbol = config.get('symbol', 'SPY')
        quantity = self._calculate_position_size(config, market_data)
        
        # Get current price from market data
        current_price = self._get_current_price(symbol, market_data)
        
        position = Position(
            id=str(uuid.uuid4()),
            symbol=symbol,
            position_type=PositionType.LONG_EQUITY,
            state=PositionState.OPEN,
            opened_at=datetime.now(),
            quantity=quantity,
            entry_price=current_price,
            current_price=current_price,
            automation_source=bot_name,
            tags=config.get('tags', [])
        )
        
        return position
    
    def _create_long_call_position(self, config: Dict[str, Any], 
                                 market_data: Optional[Dict[str, MarketData]],
                                 bot_name: Optional[str]) -> Position:
        """Create long call position"""
        symbol = config.get('symbol', 'SPY')
        quantity = self._calculate_position_size(config, market_data)
        
        # Get expiration and strike from config
        expiration_date = self._calculate_expiration(config)
        strike_price = self._calculate_strike_price(config, market_data, 'call')
        
        # Estimate option price (simplified for Phase 1)
        option_price = self._estimate_option_price(symbol, strike_price, expiration_date, 'call', market_data)
        
        # Create the position
        position = Position(
            id=str(uuid.uuid4()),
            symbol=symbol,
            position_type=PositionType.LONG_CALL,
            state=PositionState.OPEN,
            opened_at=datetime.now(),
            quantity=quantity,
            entry_price=option_price,
            current_price=option_price,
            automation_source=bot_name,
            tags=config.get('tags', [])
        )
        
        # Add option leg
        call_leg = OptionLeg(
            option_type='call',
            side='long',
            strike=strike_price,
            expiration=expiration_date,
            quantity=quantity,
            entry_price=option_price,
            current_price=option_price
        )
        position.add_leg(call_leg)
        
        return position
    
    def _create_long_put_position(self, config: Dict[str, Any], 
                                market_data: Optional[Dict[str, MarketData]],
                                bot_name: Optional[str]) -> Position:
        """Create long put position"""
        symbol = config.get('symbol', 'SPY')
        quantity = self._calculate_position_size(config, market_data)
        
        # Get expiration and strike from config
        expiration_date = self._calculate_expiration(config)
        strike_price = self._calculate_strike_price(config, market_data, 'put')
        
        # Estimate option price (simplified for Phase 1)
        option_price = self._estimate_option_price(symbol, strike_price, expiration_date, 'put', market_data)
        
        # Create the position
        position = Position(
            id=str(uuid.uuid4()),
            symbol=symbol,
            position_type=PositionType.LONG_PUT,
            state=PositionState.OPEN,
            opened_at=datetime.now(),
            quantity=quantity,
            entry_price=option_price,
            current_price=option_price,
            automation_source=bot_name,
            tags=config.get('tags', [])
        )
        
        # Add option leg
        put_leg = OptionLeg(
            option_type='put',
            side='long',
            strike=strike_price,
            expiration=expiration_date,
            quantity=quantity,
            entry_price=option_price,
            current_price=option_price
        )
        position.add_leg(put_leg)
        
        return position
    
    def _create_long_call_spread_position(self, config: Dict[str, Any], 
                                        market_data: Optional[Dict[str, MarketData]],
                                        bot_name: Optional[str]) -> Position:
        """Create long call spread position (Phase 1 - simplified)"""
        symbol = config.get('symbol', 'SPY')
        quantity = self._calculate_position_size(config, market_data)
        
        # Get expiration
        expiration_date = self._calculate_expiration(config)
        
        # Calculate strikes (simplified - 10 points apart)
        underlying_price = self._get_current_price(symbol, market_data)
        long_strike = underlying_price + 5  # ATM + 5
        short_strike = underlying_price + 15  # ATM + 15
        
        # Estimate spread price
        long_price = self._estimate_option_price(symbol, long_strike, expiration_date, 'call', market_data)
        short_price = self._estimate_option_price(symbol, short_strike, expiration_date, 'call', market_data)
        spread_price = long_price - short_price
        
        # Create position
        position = Position(
            id=str(uuid.uuid4()),
            symbol=symbol,
            position_type=PositionType.LONG_CALL_SPREAD,
            state=PositionState.OPEN,
            opened_at=datetime.now(),
            quantity=quantity,
            entry_price=spread_price,
            current_price=spread_price,
            automation_source=bot_name,
            tags=config.get('tags', [])
        )
        
        # Add legs
        long_leg = OptionLeg(
            option_type='call',
            side='long',
            strike=long_strike,
            expiration=expiration_date,
            quantity=quantity,
            entry_price=long_price,
            current_price=long_price
        )
        
        short_leg = OptionLeg(
            option_type='call',
            side='short',
            strike=short_strike,
            expiration=expiration_date,
            quantity=quantity,
            entry_price=short_price,
            current_price=short_price
        )
        
        position.add_leg(long_leg)
        position.add_leg(short_leg)
        
        return position
    
    def _create_long_put_spread_position(self, config: Dict[str, Any], 
                                       market_data: Optional[Dict[str, MarketData]],
                                       bot_name: Optional[str]) -> Position:
        """Create long put spread position (Phase 1 - simplified)"""
        symbol = config.get('symbol', 'SPY')
        quantity = self._calculate_position_size(config, market_data)
        
        # Get expiration
        expiration_date = self._calculate_expiration(config)
        
        # Calculate strikes (simplified - 10 points apart)
        underlying_price = self._get_current_price(symbol, market_data)
        long_strike = underlying_price - 5   # ATM - 5
        short_strike = underlying_price - 15  # ATM - 15
        
        # Estimate spread price
        long_price = self._estimate_option_price(symbol, long_strike, expiration_date, 'put', market_data)
        short_price = self._estimate_option_price(symbol, short_strike, expiration_date, 'put', market_data)
        spread_price = long_price - short_price
        
        # Create position
        position = Position(
            id=str(uuid.uuid4()),
            symbol=symbol,
            position_type=PositionType.LONG_PUT_SPREAD,
            state=PositionState.OPEN,
            opened_at=datetime.now(),
            quantity=quantity,
            entry_price=spread_price,
            current_price=spread_price,
            automation_source=bot_name,
            tags=config.get('tags', [])
        )
        
        # Add legs
        long_leg = OptionLeg(
            option_type='put',
            side='long',
            strike=long_strike,
            expiration=expiration_date,
            quantity=quantity,
            entry_price=long_price,
            current_price=long_price
        )
        
        short_leg = OptionLeg(
            option_type='put',
            side='short',
            strike=short_strike,
            expiration=expiration_date,
            quantity=quantity,
            entry_price=short_price,
            current_price=short_price
        )
        
        position.add_leg(long_leg)
        position.add_leg(short_leg)
        
        return position
    
    def _calculate_position_size(self, config: Dict[str, Any], 
                               market_data: Optional[Dict[str, MarketData]]) -> int:
        """Calculate position size based on configuration"""
        position_size_config = config.get('position_size', {})
        size_type = position_size_config.get('type', 'contracts')
        
        if size_type == 'contracts':
            return position_size_config.get('contracts', 1)
        elif size_type == 'percent_allocation':
            # For Phase 1, simplified to fixed contracts
            # In later phases, this would calculate based on actual capital
            percent = position_size_config.get('percent', 5)
            # Simplified: assume $10k account, 5% = $500, option ~$100 = 5 contracts
            return max(1, int(percent / 5))
        elif size_type == 'risk_amount':
            # For Phase 1, convert risk amount to contracts
            risk_amount = position_size_config.get('risk_amount', 100)
            # Simplified: assume $100 per contract
            return max(1, int(risk_amount / 100))
        else:
            return 1
    
    def _calculate_expiration(self, config: Dict[str, Any]) -> datetime:
        """Calculate expiration date based on configuration"""
        expiration_config = config.get('expiration', {})
        exp_type = expiration_config.get('type', 'between_days')
        
        if exp_type == 'exact_days':
            days = expiration_config.get('days', 30)
            return datetime.now() + timedelta(days=days)
        elif exp_type == 'between_days':
            days = expiration_config.get('days', 30)
            days_end = expiration_config.get('days_end', 45)
            # For Phase 1, use middle of range
            avg_days = (days + days_end) / 2
            return datetime.now() + timedelta(days=avg_days)
        elif exp_type == 'at_least_days':
            days = expiration_config.get('days', 30)
            # Add some buffer
            return datetime.now() + timedelta(days=days + 5)
        else:
            # Default to 30 days
            return datetime.now() + timedelta(days=30)
    
    def _calculate_strike_price(self, config: Dict[str, Any], 
                              market_data: Optional[Dict[str, MarketData]],
                              option_type: str) -> float:
        """Calculate strike price based on configuration (simplified for Phase 1)"""
        symbol = config.get('symbol', 'SPY')
        current_price = self._get_current_price(symbol, market_data)
        
        # For Phase 1, use simplified strike selection
        # Later phases will implement delta-based selection
        
        if option_type == 'call':
            # Slightly OTM call
            return current_price + 5.0
        else:  # put
            # Slightly OTM put
            return current_price - 5.0
    
    def _get_current_price(self, symbol: str, 
                          market_data: Optional[Dict[str, MarketData]]) -> float:
        """Get current price for symbol"""
        if market_data and symbol in market_data:
            return market_data[symbol].price
        else:
            # Default prices for common symbols
            defaults = {
                'SPY': 450.0,
                'QQQ': 380.0,
                'IWM': 200.0,
                'VIX': 18.0
            }
            return defaults.get(symbol, 100.0)
    
    def _estimate_option_price(self, symbol: str, strike: float, expiration: datetime,
                             option_type: str, market_data: Optional[Dict[str, MarketData]]) -> float:
        """Estimate option price (simplified for Phase 1)"""
        underlying_price = self._get_current_price(symbol, market_data)
        days_to_exp = (expiration - datetime.now()).days
        
        # Very simplified option pricing
        # In later phases, this would use proper Black-Scholes or market data
        
        if option_type == 'call':
            intrinsic = max(0, underlying_price - strike)
        else:  # put
            intrinsic = max(0, strike - underlying_price)
        
        # Simple time value estimation
        time_value = max(1.0, days_to_exp * 0.1)
        
        return intrinsic + time_value

# =============================================================================
# BASIC EXIT CRITERIA EVALUATOR
# =============================================================================

class BasicExitCriteriaEvaluator:
    """
    Evaluates basic exit criteria for simple strategies.
    Handles profit taking, stop loss, and time-based exits.
    """
    
    def __init__(self, logger: FrameworkLogger):
        self.logger = logger
    
    def should_exit_position(self, position: Position, 
                           exit_options: Dict[str, Any],
                           market_data: Optional[Dict[str, MarketData]] = None) -> Dict[str, Any]:
        """
        Evaluate if a position should be exited based on exit criteria
        
        Args:
            position: Position to evaluate
            exit_options: Exit options configuration
            market_data: Current market data
            
        Returns:
            Dictionary with exit decision and reason
        """
        try:
            # Update position price if market data available
            if market_data and position.symbol in market_data:
                self._update_position_price(position, market_data[position.symbol])
            
            # Check each exit criterion
            exit_checks = [
                self._check_profit_taking,
                self._check_stop_loss,
                self._check_time_based_exit,
                self._check_expiration_exit
            ]
            
            for check_func in exit_checks:
                exit_result = check_func(position, exit_options)
                if exit_result['should_exit']:
                    self.logger.info(LogCategory.TRADE_EXECUTION, "Exit criteria met",
                                   position_id=position.id, reason=exit_result['reason'])
                    return exit_result
            
            # No exit criteria met
            return {
                'should_exit': False,
                'reason': 'No exit criteria met',
                'exit_price': position.current_price
            }
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Exit evaluation failed",
                            position_id=position.id, error=str(e))
            return {
                'should_exit': False,
                'reason': f'Exit evaluation error: {str(e)}',
                'exit_price': position.current_price
            }
    
    def _update_position_price(self, position: Position, market_data: MarketData) -> None:
        """Update position current price based on market data"""
        # For simple positions, use underlying price change as proxy
        # In later phases, this would use actual option prices
        
        if not position.legs:
            # Equity position
            position.current_price = market_data.price
            position.unrealized_pnl = (market_data.price - position.entry_price) * position.quantity
        else:
            # Option position - simplified price update
            price_change_pct = (market_data.price / position.entry_price) - 1
            
            # Estimate new option price based on underlying movement
            for leg in position.legs:
                # Simplified: assume delta of 0.5 for price updates
                delta = 0.5 if leg.option_type == 'call' else -0.5
                if leg.side == 'short':
                    delta *= -1
                
                price_change = market_data.price - position.entry_price
                leg.current_price = max(0.01, leg.entry_price + (price_change * delta))
            
            # Update position price and P&L
            if len(position.legs) == 1:
                position.current_price = position.legs[0].current_price
                position.unrealized_pnl = position.legs[0].unrealized_pnl
            else:
                # Multi-leg position
                total_value = sum(leg.market_value for leg in position.legs)
                position.unrealized_pnl = total_value - (position.entry_price * position.quantity * 100)
    
    def _check_profit_taking(self, position: Position, exit_options: Dict[str, Any]) -> Dict[str, Any]:
        """Check profit taking exit criterion"""
        profit_config = exit_options.get('profit_taking', {})
        if not profit_config.get('enabled', False):
            return {'should_exit': False, 'reason': 'Profit taking disabled'}
        
        target_percent = profit_config.get('percent', 50)
        basis = profit_config.get('basis', 'debit')
        
        # Calculate profit percentage
        if basis == 'debit':
            # For debit spreads/long options
            profit_pct = (position.unrealized_pnl / (position.entry_price * position.quantity)) * 100
        else:
            # For credit spreads (simplified for Phase 1)
            profit_pct = (position.unrealized_pnl / (position.entry_price * position.quantity)) * 100
        
        if profit_pct >= target_percent:
            return {
                'should_exit': True,
                'reason': f'Profit target hit: {profit_pct:.1f}% >= {target_percent}%',
                'exit_price': position.current_price
            }
        
        return {'should_exit': False, 'reason': f'Profit {profit_pct:.1f}% < target {target_percent}%'}
    
    def _check_stop_loss(self, position: Position, exit_options: Dict[str, Any]) -> Dict[str, Any]:
        """Check stop loss exit criterion"""
        stop_loss_config = exit_options.get('stop_loss', {})
        if not stop_loss_config.get('enabled', False):
            return {'should_exit': False, 'reason': 'Stop loss disabled'}
        
        loss_percent = stop_loss_config.get('percent', 50)
        basis = stop_loss_config.get('basis', 'debit')
        
        # Calculate loss percentage
        if basis == 'debit':
            loss_pct = abs(position.unrealized_pnl / (position.entry_price * position.quantity)) * 100
        else:
            loss_pct = abs(position.unrealized_pnl / (position.entry_price * position.quantity)) * 100
        
        if position.unrealized_pnl < 0 and loss_pct >= loss_percent:
            return {
                'should_exit': True,
                'reason': f'Stop loss hit: {loss_pct:.1f}% >= {loss_percent}%',
                'exit_price': position.current_price
            }
        
        return {'should_exit': False, 'reason': f'Loss {loss_pct:.1f}% < stop {loss_percent}%'}
    
    def _check_time_based_exit(self, position: Position, exit_options: Dict[str, Any]) -> Dict[str, Any]:
        """Check time-based exit criteria"""
        # Check if position has been open too long
        days_open = position.days_open
        
        # Simple time-based exit: close after 60 days
        max_days = 60
        
        if days_open >= max_days:
            return {
                'should_exit': True,
                'reason': f'Time-based exit: {days_open} days >= {max_days} days',
                'exit_price': position.current_price
            }
        
        return {'should_exit': False, 'reason': f'Days open {days_open} < max {max_days}'}
    
    def _check_expiration_exit(self, position: Position, exit_options: Dict[str, Any]) -> Dict[str, Any]:
        """Check expiration-based exit criteria"""
        expiration_config = exit_options.get('expiration', {})
        if not expiration_config.get('enabled', False):
            return {'should_exit': False, 'reason': 'Expiration exit disabled'}
        
        time_before = expiration_config.get('time_before', 7)
        time_unit = expiration_config.get('time_unit', 'days')
        
        # Check option legs for expiration
        for leg in position.legs:
            if time_unit == 'days':
                days_to_exp = (leg.expiration - datetime.now()).days
                if days_to_exp <= time_before:
                    return {
                        'should_exit': True,
                        'reason': f'Expiration exit: {days_to_exp} days until expiration',
                        'exit_price': position.current_price
                    }
        
        return {'should_exit': False, 'reason': 'Expiration criteria not met'}

# =============================================================================
# BASIC STRATEGY MANAGER
# =============================================================================

class BasicStrategyManager:
    """
    Manages basic strategies for Phase 1.
    Coordinates position creation, monitoring, and exit evaluation.
    """
    
    def __init__(self, state_manager, logger: FrameworkLogger):
        self.state_manager = state_manager
        self.logger = logger
        self.position_factory = SimpleStrategyPositionFactory(logger)
        self.exit_evaluator = BasicExitCriteriaEvaluator(logger)
        
        self.logger.info(LogCategory.SYSTEM, "Basic strategy manager initialized")
    
    def execute_open_position_action(self, action_config: Dict[str, Any],
                                   market_data: Optional[Dict[str, MarketData]] = None,
                                   bot_name: Optional[str] = None) -> Optional[Position]:
        """
        Execute open position action from automation
        
        Args:
            action_config: Open position action configuration
            market_data: Current market data
            bot_name: Name of bot executing action
            
        Returns:
            Created position or None if failed
        """
        try:
            position_config = action_config.get('position', {})
            
            # Create position using factory
            position = self.position_factory.create_position(
                position_config, market_data, bot_name
            )
            
            if position:
                # Store position in state manager
                self.state_manager.store_position(position)
                
                self.logger.info(LogCategory.TRADE_EXECUTION, "Position opened",
                               position_id=position.id, symbol=position.symbol,
                               strategy_type=position.position_type, bot_name=bot_name)
            
            return position
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Failed to open position",
                            error=str(e), action_config=action_config)
            return None
    
    def monitor_positions(self, bot_name: Optional[str] = None,
                        market_data: Optional[Dict[str, MarketData]] = None) -> List[Dict[str, Any]]:
        """
        Monitor open positions and evaluate exit criteria
        
        Args:
            bot_name: Filter positions by bot name
            market_data: Current market data for price updates
            
        Returns:
            List of exit recommendations
        """
        try:
            # Get open positions
            open_positions = self.state_manager.get_positions(
                state=PositionState.OPEN
            )
            
            # Filter by bot name if specified
            if bot_name:
                open_positions = [p for p in open_positions 
                                if getattr(p, 'automation_source', None) == bot_name]
            
            exit_recommendations = []
            
            # Evaluate each position
            for position in open_positions:
                # Get exit options (simplified - would come from position config)
                exit_options = self._get_default_exit_options()
                
                # Evaluate exit criteria
                exit_result = self.exit_evaluator.should_exit_position(
                    position, exit_options, market_data
                )
                
                if exit_result['should_exit']:
                    exit_recommendations.append({
                        'position': position,
                        'exit_result': exit_result
                    })
            
            if exit_recommendations:
                self.logger.info(LogCategory.TRADE_EXECUTION, "Exit recommendations generated",
                               count=len(exit_recommendations))
            
            return exit_recommendations
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Position monitoring failed",
                            error=str(e))
            return []
    
    def close_position(self, position: Position, exit_reason: str = "Manual",
                      exit_price: Optional[float] = None) -> bool:
        """
        Close a position
        
        Args:
            position: Position to close
            exit_reason: Reason for closing
            exit_price: Exit price (uses current price if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Close the position
            position.close_position(exit_price, exit_reason)
            
            # Update in state manager
            self.state_manager.store_position(position)
            
            self.logger.info(LogCategory.TRADE_EXECUTION, "Position closed",
                           position_id=position.id, exit_reason=exit_reason,
                           realized_pnl=position.realized_pnl)
            
            return True
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Failed to close position",
                            position_id=position.id, error=str(e))
            return False
    
    def _get_default_exit_options(self) -> Dict[str, Any]:
        """Get default exit options for Phase 1"""
        return {
            'profit_taking': {
                'enabled': True,
                'percent': 50,
                'basis': 'debit'
            },
            'stop_loss': {
                'enabled': True,
                'percent': 50,
                'basis': 'debit'
            },
            'expiration': {
                'enabled': True,
                'time_before': 7,
                'time_unit': 'days'
            }
        }

# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_basic_strategy_manager(state_manager, logger: FrameworkLogger) -> BasicStrategyManager:
    """
    Factory function to create basic strategy manager
    
    Args:
        state_manager: State manager instance
        logger: Framework logger
        
    Returns:
        BasicStrategyManager instance
    """
    return BasicStrategyManager(state_manager, logger)

# =============================================================================
# TESTING AND DEMONSTRATION
# =============================================================================

def test_basic_strategy_positions():
    """Test basic strategy position management"""
    print("=" * 60)
    print("Basic Strategy Position Management - Phase 1 Testing")
    print("=" * 60)
    
    # Import required components
    from oa_logging import FrameworkLogger
    from oa_state_manager import create_state_manager
    from decision_core import create_test_context
    
    # Setup
    logger = FrameworkLogger("PositionTest")
    state_manager = create_state_manager()
    strategy_manager = create_basic_strategy_manager(state_manager, logger)
    
    # Create test market data
    test_context = create_test_context(['SPY', 'QQQ'])
    market_data = test_context.market_data
    
    print(f"Testing with SPY @ ${market_data['SPY'].price}")
    print(f"Testing with QQQ @ ${market_data['QQQ'].price}")
    print()
    
    # Test position configurations
    test_positions = [
        {
            'name': 'Long Call SPY',
            'config': {
                'position': {
                    'strategy_type': 'long_call',
                    'symbol': 'SPY',
                    'expiration': {'type': 'between_days', 'days': 30, 'days_end': 45},
                    'position_size': {'type': 'contracts', 'contracts': 2},
                    'tags': ['bullish', 'spy']
                }
            }
        },
        {
            'name': 'Long Put QQQ',
            'config': {
                'position': {
                    'strategy_type': 'long_put',
                    'symbol': 'QQQ',
                    'expiration': {'type': 'exact_days', 'days': 21},
                    'position_size': {'type': 'percent_allocation', 'percent': 10},
                    'tags': ['bearish', 'qqq']
                }
            }
        },
        {
            'name': 'Long Call Spread SPY',
            'config': {
                'position': {
                    'strategy_type': 'long_call_spread',
                    'symbol': 'SPY',
                    'expiration': {'type': 'between_days', 'days': 14, 'days_end': 21},
                    'position_size': {'type': 'contracts', 'contracts': 1},
                    'tags': ['spread', 'bullish']
                }
            }
        }
    ]
    
    created_positions = []
    
    # Test position creation
    print("1. Testing Position Creation:")
    for i, test_pos in enumerate(test_positions, 1):
        print(f"   {i}. Creating: {test_pos['name']}")
        
        position = strategy_manager.execute_open_position_action(
            test_pos['config'], market_data, "TestBot"
        )
        
        if position:
            print(f"      ✓ Created position {position.id[:8]}")
            print(f"        Symbol: {position.symbol}")
            print(f"        Type: {position.position_type}")
            print(f"        Quantity: {position.quantity}")
            print(f"        Entry Price: ${position.entry_price:.2f}")
            print(f"        Legs: {len(position.legs)}")
            created_positions.append(position)
        else:
            print(f"      ✗ Failed to create position")
        print()
    
    # Test position monitoring
    print("2. Testing Position Monitoring:")
    recommendations = strategy_manager.monitor_positions("TestBot", market_data)
    print(f"   Exit recommendations: {len(recommendations)}")
    
    if recommendations:
        for rec in recommendations:
            pos = rec['position']
            result = rec['exit_result']
            print(f"   - Position {pos.id[:8]}: {result['reason']}")
    else:
        print("   No exit criteria met (expected for new positions)")
    
    print()
    
    # Test manual position close
    if created_positions:
        print("3. Testing Position Close:")
        test_position = created_positions[0]
        print(f"   Closing position {test_position.id[:8]}")
        
        success = strategy_manager.close_position(
            test_position, "Test close", test_position.current_price * 1.1
        )
        
        if success:
            print(f"   ✓ Position closed successfully")
            print(f"     Realized P&L: ${test_position.realized_pnl:.2f}")
            print(f"     Days open: {test_position.days_open}")
        else:
            print(f"   ✗ Failed to close position")
    
    print()
    print("=" * 60)
    print("✅ Basic Strategy Position Management Testing Complete!")
    print("✅ Ready for integration with decision engine")
    print("=" * 60)

if __name__ == "__main__":
    test_basic_strategy_positions()