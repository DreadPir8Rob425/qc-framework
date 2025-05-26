# Option Alpha Framework - Core Enums 
# Type-safe enums for framework consistency

from enum import Enum
from typing import List

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
# OPTION ALPHA CONFIGURATION ENUMS
# =============================================================================

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

class AutomationType(Enum):
    """Types of automations"""
    SCANNER = "scanner"  # Only runs if bot is under position limits
    MONITOR = "monitor"  # Only runs if bot has open positions

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

class SmartPricing(Enum):
    """SmartPricing options for order execution"""
    NORMAL = "normal"
    FAST = "fast"
    PATIENT = "patient"
    OFF = "off"
    MARKET = "market"

class OptionSide(Enum):
    """Option position sides"""
    LONG = "long"
    SHORT = "short"

class DecisionType(Enum):
    """Types of decision recipes"""
    STOCK = "stock"
    INDICATOR = "indicator"
    POSITION = "position"
    BOT = "bot"
    OPPORTUNITY = "opportunity"
    GENERAL = "general"

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

# =============================================================================
# ERROR HANDLING ENUMS
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
        ErrorCode.SYMBOL_NOT_FOUND: "Symbol not found: {symbol}",
        
        ErrorCode.INSUFFICIENT_CAPITAL: "Insufficient capital for trade. Required: {required}, Available: {available}",
        ErrorCode.POSITION_LIMIT_EXCEEDED: "Position limit exceeded. Current: {current}, Limit: {limit}",
        ErrorCode.ORDER_REJECTED: "Order rejected by broker: {reason}",
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
# UTILITY FUNCTIONS
# =============================================================================

def get_enum_values(enum_class) -> List[str]:
    """Get all values from an enum class"""
    return [item.value for item in enum_class]

def validate_enum_value(enum_class, value):
    """Validate that a value exists in an enum"""
    try:
        return enum_class(value)
    except ValueError:
        valid_values = get_enum_values(enum_class)
        raise ValueError(f"Invalid {enum_class.__name__} value: {value}. Valid values: {valid_values}")

class EnumValidator:
    """Helper class for validating enum values in configurations"""
    
    @staticmethod
    def validate_scan_speed(value: str) -> ScanSpeed:
        """Validate scan speed value"""
        return validate_enum_value(ScanSpeed, value)
    
    @staticmethod
    def validate_position_type(value: str) -> PositionType:
        """Validate position type value"""
        return validate_enum_value(PositionType, value)
    
    @staticmethod
    def validate_smart_pricing(value: str) -> SmartPricing:
        """Validate smart pricing value"""
        return validate_enum_value(SmartPricing, value)