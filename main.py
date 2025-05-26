# Option Alpha Framework - Core Enums and Constants
# Defines all enums used throughout the framework for type safety and consistency

from enum import Enum, auto
from typing import Dict, Any

# =============================================================================
# QUANTCONNECT INTEGRATION ENUMS
# =============================================================================

class QCResolution(Enum):
    """QuantConnect data resolution options"""
    TICK = "tick"
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAILY = "daily"

class QCOrderType(Enum):
    """QuantConnect order types"""
    MARKET = "market"
    LIMIT = "limit"
    STOP_MARKET = "stop_market"
    STOP_LIMIT = "stop_limit"
    MARKET_ON_OPEN = "market_on_open"
    MARKET_ON_CLOSE = "market_on_close"

class QCOptionRight(Enum):
    """QuantConnect option rights"""
    CALL = "call"
    PUT = "put"

class QCOptionStyle(Enum):
    """QuantConnect option styles"""
    AMERICAN = "american"
    EUROPEAN = "european"

# =============================================================================
# OPTION ALPHA FRAMEWORK ENUMS
# =============================================================================

class LogLevel(Enum):
    """Logging levels for the framework"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class LogCategory(Enum):
    """Categories for organizing log messages"""
    TRADE_EXECUTION = "trade_execution"
    DECISION_FLOW = "decision_flow"
    MARKET_DATA = "market_data"
    PERFORMANCE = "performance"
    SYSTEM = "system"
    DEBUG = "debug"

class EventType(Enum):
    """Types of events in the event-driven system"""
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    DATA_UPDATE = "data_update"
    TIME_TRIGGER = "time_trigger"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    PROFIT_TARGET_HIT = "profit_target_hit"
    STOP_LOSS_HIT = "stop_loss_hit"
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    ERROR_OCCURRED = "error_occurred"
    LIMIT_BREACHED = "limit_breached"

class DecisionResult(Enum):
    """Results from decision evaluation"""
    YES = "yes"
    NO = "no"
    ERROR = "error"
    
class AutomationState(Enum):
    """States of automation execution"""
    IDLE = "idle"
    RUNNING = "running" 
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    DISABLED = "disabled"

class PositionState(Enum):
    """States of position lifecycle"""
    PENDING_OPEN = "pending_open"
    OPEN = "open"
    PENDING_CLOSE = "pending_close"
    CLOSED = "closed"
    ERROR = "error"
    CANCELLED = "cancelled"

class BotState(Enum):
    """Overall bot states"""
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"
    SUSPENDED = "suspended"

# =============================================================================
# MARKET DATA AND OPTIONS ENUMS
# =============================================================================

class MarketRegime(Enum):
    """Market regime classification"""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    TRENDING = "trending"
    RANGING = "ranging"

class VolatilityEnvironment(Enum):
    """Volatility environment classification"""
    LOW_IV = "low_iv"
    NORMAL_IV = "normal_iv"
    HIGH_IV = "high_iv"
    VERY_HIGH_IV = "very_high_iv"
    IV_CONTRACTION = "iv_contraction"
    IV_EXPANSION = "iv_expansion"

class OptionMoneyness(Enum):
    """Option moneyness classification"""
    DEEP_ITM = "deep_itm"
    ITM = "itm"
    ATM = "atm"
    OTM = "otm"
    DEEP_OTM = "deep_otm"

class Greeks(Enum):
    """Option Greeks"""
    DELTA = "delta"
    GAMMA = "gamma"
    THETA = "theta"
    VEGA = "vega"
    RHO = "rho"

# =============================================================================
# PERFORMANCE AND ANALYTICS ENUMS
# =============================================================================

class PerformanceMetric(Enum):
    """Performance metrics tracked by the system"""
    TOTAL_RETURN = "total_return"
    ANNUALIZED_RETURN = "annualized_return"
    SHARPE_RATIO = "sharpe_ratio"
    SORTINO_RATIO = "sortino_ratio"
    MAX_DRAWDOWN = "max_drawdown"
    WIN_RATE = "win_rate"
    PROFIT_FACTOR = "profit_factor"
    AVERAGE_WIN = "average_win"
    AVERAGE_LOSS = "average_loss"
    CALMAR_RATIO = "calmar_ratio"
    BETA = "beta"
    ALPHA = "alpha"
    VOLATILITY = "volatility"
    VAR = "var"  # Value at Risk
    CVAR = "cvar"  # Conditional Value at Risk

class AnalysisTimeframe(Enum):
    """Timeframes for performance analysis"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    SINCE_INCEPTION = "since_inception"

class BenchmarkType(Enum):
    """Benchmark options for comparison"""
    SPY = "SPY"
    QQQ = "QQQ"
    IWM = "IWM"
    VTI = "VTI"
    TREASURY_3M = "^IRX"
    TREASURY_10Y = "^TNX"
    CUSTOM = "custom"

# =============================================================================
# RISK MANAGEMENT ENUMS
# =============================================================================

class RiskLevel(Enum):
    """Risk level classifications"""
    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"

class RiskMetric(Enum):
    """Risk metrics to monitor"""
    PORTFOLIO_DELTA = "portfolio_delta"
    PORTFOLIO_GAMMA = "portfolio_gamma"
    PORTFOLIO_THETA = "portfolio_theta"
    PORTFOLIO_VEGA = "portfolio_vega"
    CONCENTRATION_RISK = "concentration_risk"
    CORRELATION_RISK = "correlation_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    PIN_RISK = "pin_risk"
    ASSIGNMENT_RISK = "assignment_risk"

class AlertLevel(Enum):
    """Alert levels for risk monitoring"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

# =============================================================================
# SYSTEM CONFIGURATION CONSTANTS
# =============================================================================

class SystemDefaults:
    """Default values used throughout the system"""
    
    # Logging defaults
    DEFAULT_LOG_LEVEL = LogLevel.INFO
    MAX_LOG_ENTRIES = 10000
    LOG_ROTATION_SIZE_MB = 100
    
    # Market hours (Eastern Time)
    MARKET_OPEN_TIME = "09:30:00"
    MARKET_CLOSE_TIME = "16:00:00"
    
    # Options-specific defaults
    DEFAULT_OPTION_EXPIRATION_DAYS = 30
    MIN_OPTION_VOLUME = 10
    MIN_OPEN_INTEREST = 100
    MAX_BID_ASK_SPREAD_PCT = 5.0
    
    # Risk management defaults
    DEFAULT_POSITION_SIZE_PCT = 2.0
    MAX_POSITION_SIZE_PCT = 10.0
    DEFAULT_STOP_LOSS_PCT = 50.0
    DEFAULT_PROFIT_TARGET_PCT = 50.0
    
    # Database defaults
    DB_CONNECTION_TIMEOUT = 30
    DB_QUERY_TIMEOUT = 60
    MAX_DB_CONNECTIONS = 10
    
    # Event processing defaults
    MAX_EVENT_QUEUE_SIZE = 1000
    EVENT_PROCESSING_TIMEOUT = 5.0
    
    # Performance monitoring defaults
    PERFORMANCE_UPDATE_FREQUENCY = 60  # seconds
    ANALYTICS_LOOKBACK_DAYS = 252
    
    # Market data defaults
    DATA_STALENESS_THRESHOLD = 300  # seconds
    MAX_SYMBOLS_PER_REQUEST = 100

class ValidationRules:
    """Validation rules and limits"""
    
    # Bot configuration limits
    MAX_BOT_NAME_LENGTH = 100
    MAX_AUTOMATIONS_PER_BOT = 50
    MAX_ACTIONS_PER_AUTOMATION = 100
    MAX_NESTED_DECISION_DEPTH = 10
    
    # Position limits
    MIN_CAPITAL_ALLOCATION = 100
    MAX_CAPITAL_ALLOCATION = 10_000_000
    MAX_DAILY_POSITIONS = 100
    MAX_TOTAL_POSITIONS = 500
    
    # Symbol limits
    MAX_SYMBOLS_PER_BOT = 1000
    MAX_SYMBOL_LENGTH = 10
    
    # Tag limits
    MAX_TAGS_PER_ITEM = 20
    MAX_TAG_LENGTH = 50
    
    # Time limits
    MAX_EXPIRATION_DAYS = 365
    MIN_EXPIRATION_DAYS = 0
    
    # Price limits
    MAX_STRIKE_PRICE = 10000
    MIN_