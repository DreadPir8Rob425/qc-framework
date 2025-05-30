# Enhanced Option Alpha Bot Schema - Core Enums
# Comprehensive enums based on Option Alpha documentation and bot-schema-prompt.txt

from enum import Enum
from typing import List, Dict, Any

# =============================================================================
# CORE FRAMEWORK ENUMS
# =============================================================================

class ScanSpeed(Enum):
    """Automation scan speed - how frequently scanner and monitor automations run"""
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
    """Types of continuous automations"""
    SCANNER = "scanner"  # Only runs if bot is under position limits
    MONITOR = "monitor"  # Only runs if bot has open positions

class ActionType(Enum):
    """Types of actions in automations"""
    DECISION = "decision"
    CONDITIONAL = "conditional"
    OPEN_POSITION = "open_position"
    CLOSE_POSITION = "close_position"
    UPDATE_EXIT_OPTIONS = "update_exit_options"
    NOTIFICATION = "notification"
    TAG_BOT = "tag_bot"
    TAG_POSITION = "tag_position"
    TAG_SYMBOL = "tag_symbol"
    UNTAG_BOT = "untag_bot"
    UNTAG_POSITION = "untag_position"
    UNTAG_SYMBOL = "untag_symbol"
    RESET_BOT_TAGS = "reset_bot_tags"
    RESET_POSITION_TAGS = "reset_position_tags"
    RESET_SYMBOL_TAGS = "reset_symbol_tags"
    LOOP_POSITIONS = "loop_positions"
    LOOP_SYMBOLS = "loop_symbols"
    LOOP_BOT_SYMBOLS = "loop_bot_symbols"

# =============================================================================
# POSITION AND STRATEGY ENUMS
# =============================================================================

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

class PositionStatus(Enum):
    """Position status options"""
    ANY = "any"
    OPEN = "open"
    OPENING = "opening"
    CLOSING = "closing"
    CLOSED = "closed"
    ERROR = "error"

class OptionType(Enum):
    """Option types"""
    CALL = "call"
    PUT = "put"

class OptionSide(Enum):
    """Option position sides"""
    LONG = "long"
    SHORT = "short"

class ExpirationSeries(Enum):
    """Option expiration series"""
    ANY_SERIES = "any_series"
    ONLY_MONTHLYS = "only_monthlys"

# =============================================================================
# COMPARISON AND SELECTION ENUMS
# =============================================================================

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
    IS = "is"
    IS_NOT = "is_not"

class SelectionType(Enum):
    """Selection type for strike/price selection"""
    EXACTLY = "exactly"
    OR_CLOSEST = "or_closest"
    OR_HIGHER = "or_higher"
    OR_LOWER = "or_lower"

class DirectionType(Enum):
    """Direction types for various comparisons"""
    ABOVE = "above"
    BELOW = "below"
    UP = "up"
    DOWN = "down"
    INCREASED = "increased"
    DECREASED = "decreased"
    OR_MORE = "or_more"
    OR_LESS = "or_less"
    OR_HIGHER = "or_higher"
    OR_LOWER = "or_lower"

# =============================================================================
# SMART PRICING AND ORDER ENUMS
# =============================================================================

class SmartPricing(Enum):
    """SmartPricing options for order execution"""
    NORMAL = "normal"
    FAST = "fast"
    PATIENT = "patient"
    OFF = "off" 
    MARKET = "market"

class PriceType(Enum):
    """Price types for final price options"""
    BID_ASK_SPREAD_PERCENT = "bid_ask_spread_percent"
    SLIPPAGE_AMOUNT = "slippage_amount"
    TYPICAL_SLIPPAGE_PERCENT = "typical_slippage_percent"
    FIXED_PRICE = "fixed_price"

# =============================================================================
# TIME AND DATE ENUMS
# =============================================================================

class TimeFrame(Enum):
    """Time frame references"""
    INTRADAY = "intraday"
    MARKET_DAYS = "market_days"
    CALENDAR_DAYS = "calendar_days"

class TimeUnit(Enum):
    """Time units for various settings"""
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"

class RepeatUnit(Enum):
    """Repeat units for recurring triggers"""
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"

class DayOfWeek(Enum):
    """Days of the week"""
    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"

class MarketHolidayAction(Enum):
    """Actions for market holidays in recurring triggers"""
    RUN_DAY_BEFORE = "run_day_before"
    RUN_DAY_AFTER = "run_day_after"
    SKIP = "skip"

class EarningsTime(Enum):
    """Earnings announcement timing"""
    BEFORE_OPEN = "before_open"
    AFTER_CLOSE = "after_close"

# =============================================================================
# SYMBOL AND SECURITY ENUMS
# =============================================================================

class SymbolType(Enum):
    """Security types"""
    STOCK = "stock"
    ETF = "ETF"
    INDEX = "index"

class LiquidityScore(Enum):
    """Option Alpha liquidity scoring (1-5)"""
    LOW = 1
    AVERAGE = 2
    GOOD = 3
    VERY_GOOD = 4
    BEST = 5

# =============================================================================
# MARKET EVENT ENUMS
# =============================================================================

class MarketEvent(Enum):
    """Economic events that can trigger decisions"""
    FOMC_MEETING = "FOMC_Meeting"
    CPI_RELEASE = "CPI_Release"
    NONFARM_PAYROLLS = "Nonfarm_payrolls"

class VIXType(Enum):
    """VIX-related symbols"""
    VIX = "VIX"
    VIX1D = "VIX1D"
    VIX9D = "VIX9D"
    VIX3M = "VIX3M"
    VIX6M = "VIX6M"
    VVIX = "VVIX"

# =============================================================================
# PRICE REFERENCE ENUMS
# =============================================================================

class PriceReference(Enum):
    """Price reference points"""
    OPEN = "open"
    HIGH = "high"
    LOW = "low"
    CLOSE = "close"
    LAST = "last"
    BID = "bid"
    ASK = "ask"
    MID = "mid"
    PREVIOUS_CLOSE = "previous_close"
    TODAYS_OPEN = "todays_open"

# =============================================================================
# SYMBOL MANAGEMENT ENUMS
# =============================================================================

class SymbolListType(Enum):
    """Types of symbol lists"""
    STATIC = "static"
    DYNAMIC = "dynamic"

class SortDirection(Enum):
    """Sort direction for dynamic symbol selection"""
    ASCENDING = "ascending"
    DESCENDING = "descending"

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_enum_values(enum_class) -> List[str]:
    """Get all values from an enum class"""
    return [item.value for item in enum_class]

def get_enum_names(enum_class) -> List[str]:  
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