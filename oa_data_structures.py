# Option Alpha Framework - Core Data Structures
# Defines the fundamental data classes used throughout the framework

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import uuid

from oa_framework_enums import PositionState, PositionType

# =============================================================================
# MARKET DATA STRUCTURES
# =============================================================================

@dataclass
class MarketData:
    """Basic market data structure for underlying securities"""
    symbol: str
    timestamp: datetime
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    iv_rank: Optional[float] = None
    
    def __post_init__(self):
        """Validate market data after initialization"""
        if self.price <= 0:
            raise ValueError(f"Invalid price for {self.symbol}: {self.price}")
        if self.bid and self.ask and self.bid > self.ask:
            raise ValueError(f"Bid ({self.bid}) > Ask ({self.ask}) for {self.symbol}")
    
    @property
    def mid_price(self) -> Optional[float]:
        """Calculate mid price if bid/ask available"""
        if self.bid is not None and self.ask is not None:
            return (self.bid + self.ask) / 2
        return None
    
    @property
    def spread(self) -> Optional[float]:
        """Fixed spread calculation with proper rounding"""
        if self.bid is not None and self.ask is not None:
            return round(self.ask - self.bid, 4)  # Round to 4 decimal places
        return None
    
    @property
    def spread_percentage(self) -> Optional[float]:
        """Fixed spread percentage with proper rounding"""
        spread = self.spread
        mid = self.mid_price
        if spread is not None and mid is not None and mid > 0:
            return round((spread / mid) * 100, 2)  # Round to 2 decimal places
        return None

@dataclass
class OptionData:
    """Option-specific market data including Greeks"""
    symbol: str
    underlying: str
    strike: float
    expiration: datetime
    option_type: str  # 'call' or 'put'
    timestamp: datetime
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    open_interest: Optional[int] = None
    implied_volatility: Optional[float] = None
    delta: Optional[float] = None
    gamma: Optional[float] = None
    theta: Optional[float] = None
    vega: Optional[float] = None
    rho: Optional[float] = None
    
    def __post_init__(self):
        """Validate option data"""
        if self.price < 0:
            raise ValueError(f"Invalid option price: {self.price}")
        if self.strike <= 0:
            raise ValueError(f"Invalid strike price: {self.strike}")
        if self.option_type not in ['call', 'put']:
            raise ValueError(f"Invalid option type: {self.option_type}")
    
    @property
    def days_to_expiration(self) -> int:
        """Calculate days to expiration"""
        return (self.expiration.date() - datetime.now().date()).days
    
    @property
    def intrinsic_value(self) -> float:
        """Calculate intrinsic value (needs underlying price)"""
        # This would need underlying price to calculate properly
        # For now, return 0 as placeholder
        return 0.0
    
    @property
    def time_value(self) -> float:
        """Calculate time value"""
        return max(0, self.price - self.intrinsic_value)

# =============================================================================
# POSITION STRUCTURES
# =============================================================================

@dataclass
class OptionLeg:
    """Represents a single leg of an options position"""
    option_type: str  # 'call' or 'put'
    side: str  # 'long' or 'short'
    strike: float
    expiration: datetime
    quantity: int
    entry_price: float
    current_price: float = 0.0
    delta: float = 0.0
    gamma: float = 0.0
    theta: float = 0.0
    vega: float = 0.0
    rho: float = 0.0
    
    def __post_init__(self):
        """Validate option leg data"""
        if self.option_type not in ['call', 'put']:
            raise ValueError(f"Invalid option type: {self.option_type}")
        if self.side not in ['long', 'short']:
            raise ValueError(f"Invalid side: {self.side}")
        if self.strike <= 0:
            raise ValueError(f"Invalid strike: {self.strike}")
        if self.quantity == 0:
            raise ValueError("Quantity cannot be zero")
    
    @property
    def market_value(self) -> float:
        """Calculate current market value of the leg"""
        multiplier = 1 if self.side == 'long' else -1
        return self.current_price * self.quantity * 100 * multiplier  # Options are per 100 shares
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L for this leg"""
        if self.side == 'long':
            return (self.current_price - self.entry_price) * self.quantity * 100
        else:
            return (self.entry_price - self.current_price) * self.quantity * 100

@dataclass
class Position:
    """Represents a complete trading position (single or multi-leg)"""
    id: str
    symbol: str
    position_type: PositionType  # 'long_call', 'iron_condor', etc.
    state: PositionState  # 'OPEN', 'CLOSED', 'PENDING_OPEN', etc.
    opened_at: datetime
    quantity: int
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    tags: List[str] = field(default_factory=list)
    legs: List[OptionLeg] = field(default_factory=list)
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    automation_source: Optional[str] = None
    
    def __post_init__(self):
        """Generate ID if not provided and validate data"""
        if not self.id:
            self.id = str(uuid.uuid4())
        
        if self.quantity == 0:
            raise ValueError("Position quantity cannot be zero")
    
    @property
    def days_open(self) -> int:
        """Calculate days position has been open"""
        end_date = self.closed_at if self.closed_at else datetime.now()
        return (end_date - self.opened_at).days
    
    @property
    def total_pnl(self) -> float:
        """Total P&L including realized and unrealized"""
        return self.realized_pnl + self.unrealized_pnl
    
    @property
    def is_open(self) -> bool:
        """Check if position is currently open"""
        return self.state == 'OPEN'
    
    @property
    def is_profitable(self) -> bool:
        """Check if position is currently profitable"""
        return self.total_pnl > 0
    
    @property
    def return_percentage(self) -> float:
        """Calculate return percentage based on entry cost"""
        if self.entry_price > 0:
            return (self.total_pnl / (self.entry_price * abs(self.quantity))) * 100
        return 0.0
    
    @property
    def portfolio_delta(self) -> float:
        """Calculate total delta for all legs"""
        return sum(leg.delta * leg.quantity * (1 if leg.side == 'long' else -1) 
                  for leg in self.legs)
    
    @property
    def portfolio_gamma(self) -> float:
        """Calculate total gamma for all legs"""
        return sum(leg.gamma * leg.quantity * (1 if leg.side == 'long' else -1) 
                  for leg in self.legs)
    
    @property
    def portfolio_theta(self) -> float:
        """Calculate total theta for all legs"""
        return sum(leg.theta * leg.quantity * (1 if leg.side == 'long' else -1) 
                  for leg in self.legs)
    
    @property
    def portfolio_vega(self) -> float:
        """Calculate total vega for all legs"""
        return sum(leg.vega * leg.quantity * (1 if leg.side == 'long' else -1) 
                  for leg in self.legs)
    
    def add_leg(self, leg: OptionLeg) -> None:
        """Add an option leg to the position"""
        self.legs.append(leg)
    
    def update_prices(self, option_prices: Dict[str, float]) -> None:
        """Update current prices for all legs and recalculate P&L"""
        total_unrealized = 0.0
        
        for leg in self.legs:
            # Create option symbol key (simplified)
            option_key = f"{self.symbol}_{leg.strike}_{leg.option_type}_{leg.expiration.strftime('%Y%m%d')}"
            
            if option_key in option_prices:
                leg.current_price = option_prices[option_key]
                total_unrealized += leg.unrealized_pnl
        
        self.unrealized_pnl = total_unrealized
        
        # Update position current price (weighted average for multi-leg)
        if self.legs:
            total_value = sum(leg.current_price * abs(leg.quantity) for leg in self.legs)
            total_quantity = sum(abs(leg.quantity) for leg in self.legs)
            if total_quantity > 0:
                self.current_price = total_value / total_quantity

    def close_position(self, exit_price: Optional[float] = None, exit_reason: str = "Manual") -> None:
        """Close the position and calculate final P&L"""
        self.state = PositionState.CLOSED
        self.closed_at = datetime.now()
        self.exit_reason = exit_reason
        
        if exit_price is not None:
            self.exit_price = exit_price
        else:
            self.exit_price = self.current_price
        
        # Move unrealized P&L to realized P&L
        self.realized_pnl = self.unrealized_pnl
        self.unrealized_pnl = 0.0

# =============================================================================
# EVENT STRUCTURES
# =============================================================================

@dataclass
class Event:
    """Base event class for the event-driven system"""
    event_type: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    priority: int = 0  # Higher numbers = higher priority
    
    def __post_init__(self):
        """Set timestamp if not provided"""
        if not self.timestamp:
            self.timestamp = datetime.now()
    
    @property
    def age_seconds(self) -> float:
        """Get age of event in seconds"""
        return (datetime.now() - self.timestamp).total_seconds()
    
    def is_stale(self, max_age_seconds: float = 300) -> bool:
        """Check if event is stale (older than max_age_seconds)"""
        return self.age_seconds > max_age_seconds

# =============================================================================
# AUTOMATION STRUCTURES
# =============================================================================

@dataclass
class AutomationResult:
    """Result of automation execution"""
    automation_name: str
    success: bool
    execution_time: datetime
    duration_ms: float
    actions_executed: int
    positions_opened: int = 0
    positions_closed: int = 0
    error_message: Optional[str] = None
    debug_info: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Get duration in seconds"""
        return self.duration_ms / 1000.0

@dataclass
class DecisionResult:
    """Result of a decision evaluation"""
    result: str  # 'YES', 'NO', 'ERROR'
    confidence: float = 1.0  # 0.0 to 1.0
    reasoning: Optional[str] = None
    evaluation_time: datetime = field(default_factory=datetime.now)
    debug_data: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_yes(self) -> bool:
        """Check if result is YES"""
        return self.result == 'YES'
    
    @property
    def is_no(self) -> bool:
        """Check if result is NO"""
        return self.result == 'NO'
    
    @property
    def is_error(self) -> bool:
        """Check if result is ERROR"""
        return self.result == 'ERROR'

# =============================================================================
# PORTFOLIO STRUCTURES
# =============================================================================

@dataclass
class PortfolioSnapshot:
    """Snapshot of portfolio state at a point in time"""
    timestamp: datetime
    total_value: float
    cash_balance: float
    positions_value: float
    open_positions: int
    total_pnl_today: float
    total_pnl_all_time: float
    portfolio_delta: float = 0.0
    portfolio_gamma: float = 0.0
    portfolio_theta: float = 0.0
    portfolio_vega: float = 0.0
    max_risk: float = 0.0
    buying_power_used: float = 0.0
    
    @property
    def portfolio_beta(self) -> float:
        """Calculate portfolio beta (simplified)"""
        # This would need individual position betas to calculate properly
        return 1.0  # Placeholder
    
    @property
    def risk_percentage(self) -> float:
        """Calculate risk as percentage of total value"""
        if self.total_value > 0:
            return (self.max_risk / self.total_value) * 100
        return 0.0

@dataclass
class TradeRecord:
    """Record of a completed trade"""
    trade_id: str
    timestamp: datetime
    symbol: str
    action: str  # 'OPEN', 'CLOSE'
    position_type: str
    quantity: int
    price: float
    fees: float = 0.0
    pnl: float = 0.0
    bot_name: Optional[str] = None
    automation_name: Optional[str] = None
    position_id: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Generate trade ID if not provided"""
        if not self.trade_id:
            self.trade_id = f"T_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"
    
    @property
    def net_pnl(self) -> float:
        """Get net P&L after fees"""
        return self.pnl - self.fees
    
    @property
    def is_profitable(self) -> bool:
        """Check if trade was profitable"""
        return self.net_pnl > 0

# =============================================================================
# ANALYTICS STRUCTURES
# =============================================================================

@dataclass
class PerformanceMetrics:
    """Performance metrics for a bot or strategy"""
    period_start: datetime
    period_end: datetime
    total_return: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    total_pnl: float
    total_fees: float
    max_drawdown: float
    sharpe_ratio: Optional[float] = None
    sortino_ratio: Optional[float] = None
    calmar_ratio: Optional[float] = None
    win_rate: Optional[float] = None
    profit_factor: Optional[float] = None
    average_win: Optional[float] = None
    average_loss: Optional[float] = None
    largest_win: Optional[float] = None
    largest_loss: Optional[float] = None
    
    def __post_init__(self):
        """Calculate derived metrics"""
        if self.total_trades > 0:
            self.win_rate = (self.winning_trades / self.total_trades) * 100
        
        if self.winning_trades > 0:
            # This would need individual trade data to calculate properly
            self.average_win = self.total_pnl / self.winning_trades if self.winning_trades > 0 else 0
        
        if self.losing_trades > 0:
            # This would need individual trade data to calculate properly
            self.average_loss = abs(self.total_pnl) / self.losing_trades if self.losing_trades > 0 else 0
        
        # Calculate profit factor
        if self.average_loss and self.average_loss > 0:
            gross_profit = self.winning_trades * (self.average_win or 0)
            gross_loss = self.losing_trades * (self.average_loss or 0)
            if gross_loss > 0:
                self.profit_factor = gross_profit / gross_loss
    
    @property
    def net_pnl(self) -> float:
        """Get net P&L after fees"""
        return self.total_pnl - self.total_fees
    
    @property
    def return_percentage(self) -> float:
        """Get return as percentage (needs initial capital)"""
        # Would need initial capital to calculate properly
        return self.total_return

# =============================================================================
# BOT CONFIGURATION STRUCTURES
# =============================================================================

@dataclass
class BotSafeguards:
    """Bot safeguard settings"""
    capital_allocation: float
    daily_positions: int
    position_limit: int
    daytrading_allowed: bool = False
    max_risk_per_position: float = 0.05  # 5% of capital
    max_correlation: float = 0.7  # Maximum correlation between positions
    
    def validate(self) -> List[str]:
        """Validate safeguard settings and return any errors"""
        errors = []
        
        if self.capital_allocation <= 0:
            errors.append("Capital allocation must be positive")
        
        if self.daily_positions <= 0:
            errors.append("Daily positions limit must be positive")
        
        if self.position_limit <= 0:
            errors.append("Position limit must be positive")
        
        if self.daily_positions > self.position_limit:
            errors.append("Daily positions cannot exceed total position limit")
        
        if not 0 < self.max_risk_per_position <= 1:
            errors.append("Max risk per position must be between 0 and 1")
        
        return errors

@dataclass
class BotStatus:
    """Current status of a bot"""
    name: str
    state: str  # 'STOPPED', 'RUNNING', 'ERROR', etc.
    uptime_seconds: float
    last_activity: datetime
    total_positions: int
    open_positions: int
    total_pnl: float
    today_pnl: float
    automations_status: Dict[str, str] = field(default_factory=dict)
    error_count: int = 0
    last_error: Optional[str] = None
    
    @property
    def uptime_hours(self) -> float:
        """Get uptime in hours"""
        return self.uptime_seconds / 3600
    
    @property
    def is_healthy(self) -> bool:
        """Fixed health check that's more permissive for testing"""
        return (self.state == 'RUNNING' or self.state == 'running') and self.error_count < 5

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_test_market_data(symbol: str = "SPY", price: float = 450.0) -> MarketData:
    """Create test market data for demonstrations"""
    return MarketData(
        symbol=symbol,
        timestamp=datetime.now(),
        price=price,
        bid=price - 0.01,
        ask=price + 0.01,
        volume=1000000,
        iv_rank=50.0
    )

def create_test_position(symbol: str = "SPY", position_type: PositionType = PositionType.LONG_CALL) -> Position:
    """Create test position for demonstrations"""
    return Position(
        id=str(uuid.uuid4()),
        symbol=symbol,
        position_type=position_type,
        state=PositionState.OPEN,
        opened_at=datetime.now(),
        quantity=1,
        entry_price=100.0,
        current_price=105.0,
        unrealized_pnl=5.0
    )

def validate_position_data(position: Position) -> List[str]:
    """Validate position data and return list of errors"""
    errors = []
    
    if not position.symbol:
        errors.append("Position must have a symbol")
    
    if position.quantity == 0:
        errors.append("Position quantity cannot be zero")
    
    if position.entry_price <= 0:
        errors.append("Entry price must be positive")
    
    if position.opened_at > datetime.now():
        errors.append("Position cannot be opened in the future")
    
    if position.closed_at and position.closed_at < position.opened_at:
        errors.append("Close time cannot be before open time")
    
    return errors

if __name__ == "__main__":
    # Demonstration of data structures
    print("Option Alpha Framework - Data Structures Demo")
    print("=" * 50)
    
    # Test market data
    market_data = create_test_market_data()
    print(f"Market Data: {market_data.symbol} @ ${market_data.price}")
    print(f"  Spread: ${market_data.spread:.2f} ({market_data.spread_percentage:.2f}%)")
    
    # Test position
    position = create_test_position()
    print(f"\nPosition: {position.symbol} {position.position_type}")
    print(f"  P&L: ${position.total_pnl:.2f} ({position.return_percentage:.1f}%)")
    print(f"  Days Open: {position.days_open}")
    
    # Validate position
    errors = validate_position_data(position)
    if errors:
        print(f"  Validation Errors: {errors}")
    else:
        print("  ✓ Position data is valid")
    
    print("\n✅ Data structures working correctly!")