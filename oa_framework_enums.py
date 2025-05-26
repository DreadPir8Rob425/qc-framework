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
    RISK_MANAGEMENT = "risk_managenment"
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

class DecisionType(Enum):
    """Types of decision recipes"""
    STOCK = "stock"
    INDICATOR = "indicator"
    POSITION = "position"
    BOT = "bot"
    OPPORTUNITY = "opportunity"
    GENERAL = "general"
    
class DecisionResult(Enum):
    """Results from decision evaluation"""
    YES = "yes"
    NO = "no"
    ERROR = "error"
    
class AutomationType(Enum):
    """Types of automations"""
    SCANNER = "scanner"  # Only runs if bot is under position limits
    MONITOR = "monitor"  # Only runs if bot has open positions
    
class AutomationState(Enum):
    """States of automation execution"""
    IDLE = "idle"
    RUNNING = "running" 
    WAITING = "waiting"
    COMPLETED = "completed"
    ERROR = "error"
    DISABLED = "disabled"

class PositionType(Enum):
    """Types of positions supported by Option Alpha"""
    LONG_EQUITY = "long_equity"
    LONG_CALL = "long_call"
    LONG_PUT = "long_put"
    LONG_CALL_SPREAD = "long_call_spread"
    LONG_PUT_SPREAD = "long_put_spread"
    SHORT_CALL_SPREAD = "short_call_spread"
    SHORT_PUT_SPREAD = "short_put_spread"
    IRON_CONDOR = "iron_condor"
    IRON_BUTTERFLY = "iron_butterfly"
    
class ScanSpeed(Enum):
    """Automation scan speed determines how frequently scanner and monitor automations run"""
    FIFTEEN_MINUTES = "15_minutes"
    FIVE_MINUTES = "5_minutes" 
    ONE_MINUTE = "1_minute"

class TriggerType(Enum):
    """Types of automation triggers"""
    CONTINUOUS = "continuous"
    DATE = "date"
    RECURRING = "recurring"
    MARKET_OPEN = "market_open"
    MARKET_CLOSE = "market_close"
    POSITION_OPENED = "position_opened"
    POSITION_CLOSED = "position_closed"
    WEBHOOK = "webhook"
    MANUAL_BUTTON = "manual_button"

class SmartPricing(Enum):
    """SmartPricing options for order execution"""
    NORMAL = "normal"
    FAST = "fast"
    PATIENT = "patient"
    OFF = "off"
    MARKET = "market"

class ComparisonOperator(Enum):
    """Comparison operators for decision recipes"""
    GREATER_THAN = "greater_than"
    GREATER_THAN_OR_EQUAL = "greater_than_or_equal"
    LESS_THAN = "less_than"
    LESS_THAN_OR_EQUAL = "less_than_or_equal"
    EQUAL_TO = "equal_to"
    ABOVE = "above"
    BELOW = "below"
    BETWEEN = "between"
    
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
    
class OptionSide(Enum):
    """Option position sides"""
    LONG = "long"
    SHORT = "short"
    
class OptionType(Enum):
    """Option types"""
    CALL = "call"
    PUT = "put"


class ExpirationSeries(Enum):
    """Option expiration series"""
    ANY_SERIES = "any_series"
    ONLY_MONTHLYS = "only_monthlys"

class TimeFrame(Enum):
    """Time frame references"""
    INTRADAY = "intraday"
    MARKET_DAYS = "market_days"
    CALENDAR_DAYS = "calendar_days"

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
    MIN_STRIKE_PRICE = 0.01
    MAX_PREMIUM = 1000
    MIN_PREMIUM = 0.01
    
    # Greeks limits
    MAX_DELTA = 1.0
    MIN_DELTA = -1.0
    MAX_GAMMA = 10.0
    MAX_THETA = 0.0  # Theta should be negative for long positions
    MIN_THETA = -10.0
    MAX_VEGA = 100.0
    MIN_VEGA = 0.0
    
 
 
# =============================================================================
# TECHNICAL INDICATORS
# =============================================================================
class TechnicalIndicator(Enum):
    """Technical indicators supported by Option Alpha"""
    RSI = "RSI"
    STOCH_K = "Stoch_K"
    CCI = "CCI"
    ADX = "ADX"
    MOMENTUM = "Momentum"
    MACD = "MACD"
    STOCH_RSI = "Stoch_RSI"
    WILLIAMS_R = "Williams_R"
    ULTIMATE = "Ultimate"
    MFI = "MFI"
    CHANDE = "Chande"
    SMA = "SMA"
    EMA = "EMA"
    TRIMA = "TRIMA"
    KAMA = "KAMA"
    ATR = "ATR"
    BOP = "BOP"
    CMO = "CMO"
    DX = "DX"
    ROC = "ROC"

# =============================================================================
# ERROR CODES AND MESSAGES
# =============================================================================

class ErrorCode(Enum):
    """Standardized error codes for the framework"""
    
    # Configuration errors (1000-1999)
    INVALID_CONFIG = 1001
    MISSING_REQUIRED_FIELD = 1002
    INVALID_FIELD_VALUE = 1003
    VALIDATION_FAILED = 1004
    SCHEMA_ERROR = 1005
    
    # Market data errors (2000-2999)
    DATA_NOT_AVAILABLE = 2001
    STALE_DATA = 2002
    DATA_PROVIDER_ERROR = 2003
    SYMBOL_NOT_FOUND = 2004
    OPTION_CHAIN_ERROR = 2005
    
    # Trading errors (3000-3999)
    INSUFFICIENT_CAPITAL = 3001
    POSITION_LIMIT_EXCEEDED = 3002
    ORDER_REJECTED = 3003
    FILL_ERROR = 3004
    INVALID_ORDER = 3005
    BROKER_CONNECTION_ERROR = 3006
    
    # Decision engine errors (4000-4999)
    DECISION_EVALUATION_ERROR = 4001
    MISSING_DECISION_DATA = 4002
    INVALID_DECISION_LOGIC = 4003
    TIMEOUT_ERROR = 4004
    
    # System errors (5000-5999)
    DATABASE_ERROR = 5001
    LOGGING_ERROR = 5002
    EVENT_PROCESSING_ERROR = 5003
    MEMORY_ERROR = 5004
    THREAD_ERROR = 5005
    
    # Risk management errors (6000-6999)
    RISK_LIMIT_EXCEEDED = 6001
    INVALID_RISK_PARAMETERS = 6002
    CONCENTRATION_LIMIT_EXCEEDED = 6003
    
    # Performance errors (7000-7999)
    CALCULATION_ERROR = 7001
    INSUFFICIENT_DATA = 7002
    BENCHMARK_ERROR = 7003

class ErrorMessages:
    """Standardized error messages"""
    
    MESSAGES = {
        ErrorCode.INVALID_CONFIG: "Invalid bot configuration provided",
        ErrorCode.MISSING_REQUIRED_FIELD: "Required configuration field is missing: {field}",
        ErrorCode.INVALID_FIELD_VALUE: "Invalid value for field {field}: {value}",
        ErrorCode.VALIDATION_FAILED: "Configuration validation failed: {details}",
        ErrorCode.SCHEMA_ERROR: "JSON schema validation error: {error}",
        
        ErrorCode.DATA_NOT_AVAILABLE: "Market data not available for symbol: {symbol}",
        ErrorCode.STALE_DATA: "Market data is stale for symbol: {symbol}",
        ErrorCode.DATA_PROVIDER_ERROR: "Data provider error: {error}",
        ErrorCode.SYMBOL_NOT_FOUND: "Symbol not found: {symbol}",
        ErrorCode.OPTION_CHAIN_ERROR: "Error retrieving option chain for {symbol}: {error}",
        
        ErrorCode.INSUFFICIENT_CAPITAL: "Insufficient capital for trade. Required: {required}, Available: {available}",
        ErrorCode.POSITION_LIMIT_EXCEEDED: "Position limit exceeded. Current: {current}, Limit: {limit}",
        ErrorCode.ORDER_REJECTED: "Order rejected by broker: {reason}",
        ErrorCode.FILL_ERROR: "Error filling order: {error}",
        ErrorCode.INVALID_ORDER: "Invalid order parameters: {details}",
        ErrorCode.BROKER_CONNECTION_ERROR: "Broker connection error: {error}",
        
        ErrorCode.DECISION_EVALUATION_ERROR: "Error evaluating decision: {error}",
        ErrorCode.MISSING_DECISION_DATA: "Missing data required for decision: {data}",
        ErrorCode.INVALID_DECISION_LOGIC: "Invalid decision logic: {logic}",
        ErrorCode.TIMEOUT_ERROR: "Operation timed out after {timeout} seconds",
        
        ErrorCode.DATABASE_ERROR: "Database error: {error}",
        ErrorCode.LOGGING_ERROR: "Logging system error: {error}",
        ErrorCode.EVENT_PROCESSING_ERROR: "Event processing error: {error}",
        ErrorCode.MEMORY_ERROR: "Memory allocation error: {error}",
        ErrorCode.THREAD_ERROR: "Threading error: {error}",
        
        ErrorCode.RISK_LIMIT_EXCEEDED: "Risk limit exceeded: {limit_type}",
        ErrorCode.INVALID_RISK_PARAMETERS: "Invalid risk parameters: {parameters}",
        ErrorCode.CONCENTRATION_LIMIT_EXCEEDED: "Concentration limit exceeded for {symbol}",
        
        ErrorCode.CALCULATION_ERROR: "Error calculating {metric}: {error}",
        ErrorCode.INSUFFICIENT_DATA: "Insufficient data for calculation: {calculation}",
        ErrorCode.BENCHMARK_ERROR: "Benchmark calculation error: {error}"
    }
    
    @classmethod
    def get_message(cls, error_code: ErrorCode, **kwargs) -> str:
        """Get formatted error message for error code"""
        template = cls.MESSAGES.get(error_code, f"Unknown error: {error_code}")
        try:
            return template.format(**kwargs)
        except KeyError as e:
            return f"{template} (Missing parameter: {e})"

# =============================================================================
# FRAMEWORK CONSTANTS
# =============================================================================

class FrameworkConstants:
    """Framework-wide constants"""
    
    # Version information
    VERSION = "1.0.0"
    VERSION_MAJOR = 1
    VERSION_MINOR = 0
    VERSION_PATCH = 0
    
    # Framework identification
    FRAMEWORK_NAME = "OA-QC Framework"
    FRAMEWORK_DESCRIPTION = "Option Alpha QuantConnect Integration Framework"
    
    # File extensions
    CONFIG_FILE_EXTENSION = ".json"
    LOG_FILE_EXTENSION = ".log"
    DATA_FILE_EXTENSION = ".db"
    
    # Default file names
    DEFAULT_CONFIG_FILE = "bot_config.json"
    DEFAULT_LOG_FILE = "oa_framework.log"
    DEFAULT_DATABASE_FILE = "oa_framework.db"
    
    # Threading constants
    MAX_WORKER_THREADS = 10
    THREAD_POOL_TIMEOUT = 60
    
    # Caching constants
    DEFAULT_CACHE_TTL = 300  # 5 minutes
    MAX_CACHE_SIZE = 1000
    
    # Network constants
    DEFAULT_TIMEOUT = 30
    MAX_RETRIES = 3
    RETRY_DELAY = 1  # seconds
    
    # Precision constants
    PRICE_PRECISION = 4
    PERCENTAGE_PRECISION = 2
    GREEK_PRECISION = 4
    
    # Market constants
    TRADING_DAYS_PER_YEAR = 252
    HOURS_PER_TRADING_DAY = 6.5
    MINUTES_PER_TRADING_DAY = 390

# =============================================================================
# UTILITY FUNCTIONS FOR ENUMS
# =============================================================================

def get_enum_values(enum_class) -> list:
    """Get all values from an enum class"""
    return [item.value for item in enum_class]

def get_enum_names(enum_class) -> list:
    """Get all names from an enum class"""
    return [item.name for item in enum_class]

def validate_enum_value(enum_class, value):
    """Validate that a value exists in an enum"""
    try:
        return enum_class(value)
    except ValueError:
        valid_values = get_enum_values(enum_class)
        raise ValueError(f"Invalid {enum_class.__name__} value: {value}. Valid values: {valid_values}")

def enum_to_dict(enum_class) -> Dict[str, Any]:
    """Convert enum to dictionary mapping"""
    return {item.name: item.value for item in enum_class}

# =============================================================================
# ENUM VALIDATION HELPERS
# =============================================================================

class EnumValidator:
    """Helper class for validating enum values in configurations"""
    
    @staticmethod
    def validate_scan_speed(value: str) -> ScanSpeed:
        """Validate scan speed value"""
        return validate_enum_value(ScanSpeed, value)
    
    @staticmethod
    def validate_trigger_type(value: str) -> TriggerType:
        """Validate trigger type value"""
        return validate_enum_value(TriggerType, value)
    
    @staticmethod
    def validate_position_type(value: str) -> PositionType:
        """Validate position type value"""
        return validate_enum_value(PositionType, value)
    
    @staticmethod
    def validate_smart_pricing(value: str) -> SmartPricing:
        """Validate smart pricing value"""
        return validate_enum_value(SmartPricing, value)
    
    @staticmethod
    def validate_comparison_operator(value: str) -> ComparisonOperator:
        """Validate comparison operator value"""
        return validate_enum_value(ComparisonOperator, value)
    
    @staticmethod
    def validate_technical_indicator(value: str) -> TechnicalIndicator:
        """Validate technical indicator value"""
        return validate_enum_value(TechnicalIndicator, value)
    
    @staticmethod
    def validate_log_level(value: str) -> LogLevel:
        """Validate log level value"""
        return validate_enum_value(LogLevel, value)

# =============================================================================
# EXAMPLE USAGE
# =============================================================================

def demonstrate_enums():
    """Demonstrate usage of framework enums"""
    
    print("Framework Enums Demonstration")
    print("=" * 40)
    
    # Show scan speed options
    print("Available Scan Speeds:")
    for speed in ScanSpeed:
        print(f"  - {speed.name}: {speed.value}")
    
    print("\nAvailable Position Types:")
    for pos_type in PositionType:
        print(f"  - {pos_type.name}: {pos_type.value}")
    
    print("\nAvailable Technical Indicators:")
    for indicator in TechnicalIndicator:
        print(f"  - {indicator.name}: {indicator.value}")
    
    # Demonstrate validation
    print("\nValidation Examples:")
    try:
        valid_speed = EnumValidator.validate_scan_speed("5_minutes")
        print(f"✓ Valid scan speed: {valid_speed}")
    except ValueError as e:
        print(f"✗ {e}")
    
    try:
        invalid_speed = EnumValidator.validate_scan_speed("2_minutes")
        print(f"✓ Valid scan speed: {invalid_speed}")
    except ValueError as e:
        print(f"✗ {e}")
    
    # Show error message formatting
    print("\nError Message Examples:")
    msg1 = ErrorMessages.get_message(ErrorCode.MISSING_REQUIRED_FIELD, field="symbol")
    print(f"  - {msg1}")
    
    msg2 = ErrorMessages.get_message(ErrorCode.INSUFFICIENT_CAPITAL, required=1000, available=500)
    print(f"  - {msg2}")
    
    print("\nFramework Constants:")
    print(f"  - Version: {FrameworkConstants.VERSION}")
    print(f"  - Trading Days/Year: {FrameworkConstants.TRADING_DAYS_PER_YEAR}")
    print(f"  - Default Cache TTL: {FrameworkConstants.DEFAULT_CACHE_TTL}s")

if __name__ == "__main__":
    demonstrate_enums()