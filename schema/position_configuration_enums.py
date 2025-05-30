# Enhanced Option Alpha Bot Schema - Position Configuration Enums
# All enums related to position configuration, sizing, pricing, and management

from enum import Enum

# =============================================================================
# EXPIRATION CONFIGURATION ENUMS
# =============================================================================

class ExpirationType(Enum):
    """Types of expiration selection"""
    EXACTLY_DAYS = "exactly_days"
    AT_LEAST_DAYS = "at_least_days"
    EXACTLY_DAYS_ALT = "exactly"  # Alternative form
    BETWEEN_DAYS = "between_days"
    ON_OR_AFTER = "on_or_after"
    SAME_AS_POSITION = "same_as_position"

# =============================================================================
# STRIKE SELECTION ENUMS
# =============================================================================

class StrikeSelectionType(Enum):
    """Types of strike selection methods"""
    DELTA = "delta"
    STRIKE_PRICE = "strike_price"
    PRICE_TARGET = "price_target"
    RELATIVE_UNDERLYING = "relative_underlying"
    RELATIVE_LEG = "relative_leg"
    STD_DEV = "std_dev"
    EXPECTED_MOVE = "expected_move"
    SAME_STRIKE = "same_strike"
    MATCH_SPREAD_WIDTH = "match_spread_width"

class DeltaRange(Enum):
    """Common delta ranges for strike selection"""
    DEEP_ITM = 0.8
    ITM = 0.6
    ATM = 0.5
    OTM = 0.3
    DEEP_OTM = 0.1

class ExpectedMoveDirection(Enum):
    """Expected move directions"""
    UP = "up"
    DOWN = "down"

# =============================================================================
# POSITION SIZING ENUMS
# =============================================================================

class PositionSizeType(Enum):
    """Types of position sizing methods"""
    CONTRACTS = "contracts"
    RISK_AMOUNT = "risk_amount"
    PERCENT_ALLOCATION = "percent_allocation"
    PERCENT_WITH_MAX = "percent_with_max"
    SAME_AS_POSITION = "same_as_position"
    PROGRESSIVE_RISK = "progressive_risk"

class CapitalBaseType(Enum):
    """Base types for percentage calculations"""
    ALLOCATION = "allocation"
    AVAILABLE_CAPITAL = "available_capital"
    NET_LIQUID = "net_liquid"

class ProgressiveRiskType(Enum):
    """Progressive risk adjustment types"""
    INCREASE = "increase"
    DOUBLE = "double"

class ProgressiveRiskTrigger(Enum):
    """Progressive risk triggers"""
    WIN = "win"
    CONSECUTIVE_WINS = "consecutive_wins"
    LOSS = "loss"
    CONSECUTIVE_LOSSES = "consecutive_losses"

# =============================================================================
# EXIT OPTIONS ENUMS
# =============================================================================

class ExitBasis(Enum):
    """Basis for profit/loss calculations"""
    CREDIT = "credit"
    DEBIT = "debit"

class TrailingStopCondition(Enum):
    """Trailing stop disable conditions"""
    RETURN_THRESHOLD = "return_threshold"
    PULLBACK_THRESHOLD = "pullback_threshold"

class TouchDirection(Enum):
    """Touch direction from ITM"""
    FROM_ITM = "from_itm"
    FROM_OTM = "from_otm"

# =============================================================================
# ENTRY CRITERIA ENUMS
# =============================================================================

class EntryCriteriaType(Enum):
    """Types of entry criteria filters"""
    BOT_HAS_CAPITAL = "bot_has_capital"
    MAX_OPEN_POSITIONS = "max_open_positions"
    MAX_DAILY_POSITIONS = "max_daily_positions"
    MAX_SYMBOL_POSITIONS = "max_symbol_positions"
    NO_IDENTICAL_LEG = "no_identical_leg"
    VIX_RANGE = "vix_range"
    IV_RANK_RANGE = "iv_rank_range"

# =============================================================================
# POSITION CRITERIA ENUMS
# =============================================================================

class PositionCriteriaType(Enum):
    """Types of position criteria filters (opportunity-specific)"""
    # Price and Spread Filters
    MAX_BID_ASK_SPREAD = "max_bid_ask_spread"
    PRICE_RANGE = "price_range"
    SPREAD_RANGE = "spread_range"
    
    # Risk and Probability Filters
    MIN_OTM_PERCENT = "min_otm_percent"
    MIN_ALPHA = "min_alpha"
    MIN_EV_PER_CONTRACT = "min_ev_per_contract"
    MIN_REWARD_RISK = "min_reward_risk"
    REWARD_RISK_FAVORABLE = "reward_risk_favorable"
    MIN_PROB_PROFIT = "min_prob_profit"
    MIN_PROB_MAX_PROFIT = "min_prob_max_profit"
    MIN_PROB_MAX_LOSS = "min_prob_max_loss"
    MIN_MAX_PROFIT = "min_max_profit"
    MAX_MAX_LOSS = "max_max_loss"
    
    # Event-based Filters
    BEFORE_EARNINGS = "before_earnings"
    BEFORE_FOMC = "before_fomc"
    BEFORE_EX_DIVIDEND = "before_ex_dividend"

# =============================================================================
# CLOSE POSITION ENUMS
# =============================================================================

class CloseQuantityType(Enum):
    """Types of close quantity specifications"""
    PERCENT = "percent"
    CONTRACTS = "contracts"
    SHARES = "shares"

class CloseOptionType(Enum):
    """Close position option types"""
    DISCARD_OTM_LONG_LEGS = "discard_otm_long_legs"

# =============================================================================
# SYMBOL FILTERING ENUMS
# =============================================================================

class SymbolFilterType(Enum):
    """Types of symbol filters for dynamic selection"""
    MARKET_CAP = "market_cap"
    VOLUME = "volume"
    PRICE = "price"
    IV_RANK = "iv_rank"
    SECTOR = "sector"
    INDUSTRY = "industry"
    BETA = "beta"
    EARNINGS_DATE = "earnings_date"
    EX_DIVIDEND_DATE = "ex_dividend_date"
    OPTIONS_VOLUME = "options_volume"
    OPEN_INTEREST = "open_interest"

class SymbolSortField(Enum):
    """Fields for sorting symbols"""
    MARKET_CAP = "market_cap"
    VOLUME = "volume"
    PRICE = "price"
    IV_RANK = "iv_rank"
    BETA = "beta"
    PERFORMANCE_1D = "performance_1d"
    PERFORMANCE_5D = "performance_5d"
    PERFORMANCE_1M = "performance_1m"
    OPTIONS_VOLUME = "options_volume"
    ALPHABETICAL = "alphabetical"

class MarketCapSize(Enum):
    """Market capitalization categories"""
    MEGA_CAP = "mega_cap"       # >$200B
    LARGE_CAP = "large_cap"     # $10B-$200B
    MID_CAP = "mid_cap"         # $2B-$10B
    SMALL_CAP = "small_cap"     # $300M-$2B
    MICRO_CAP = "micro_cap"     # <$300M

class SectorType(Enum):
    """Market sectors"""
    TECHNOLOGY = "technology"
    HEALTHCARE = "healthcare"
    FINANCIALS = "financials"
    CONSUMER_DISCRETIONARY = "consumer_discretionary"
    CONSUMER_STAPLES = "consumer_staples"
    INDUSTRIALS = "industrials"
    ENERGY = "energy"
    UTILITIES = "utilities"
    MATERIALS = "materials"
    REAL_ESTATE = "real_estate"
    COMMUNICATION_SERVICES = "communication_services"

# =============================================================================
# TAG MANAGEMENT ENUMS
# =============================================================================

class TagActionType(Enum):
    """Types of tag actions"""
    ADD = "add"
    REMOVE = "remove"
    RESET = "reset"

class TagTargetType(Enum):
    """Tag target types"""
    BOT = "bot"
    POSITION = "position"
    SYMBOL = "symbol"

# =============================================================================
# LOOP CONFIGURATION ENUMS
# =============================================================================

class LoopType(Enum):
    """Types of loops in automations"""
    POSITIONS = "positions"
    SYMBOLS = "symbols"
    BOT_SYMBOLS = "bot_symbols"

# =============================================================================
# VALIDATION CONSTANTS
# =============================================================================

class ValidationLimits:
    """Validation limits for various configuration values"""
    
    # Position Limits
    MAX_POSITION_SIZE_CONTRACTS = 1000
    MAX_POSITION_SIZE_PERCENT = 100
    MAX_RISK_AMOUNT = 1000000
    
    # Time Limits
    MAX_EXPIRATION_DAYS = 365
    MIN_EXPIRATION_DAYS = 0
    MAX_DTE = 365
    MIN_DTE = 0
    
    # Price Limits
    MAX_STRIKE_PRICE = 10000
    MIN_STRIKE_PRICE = 0.01
    MAX_PREMIUM = 1000
    MIN_PREMIUM = 0.01
    
    # Greeks Limits
    MAX_DELTA = 1.0
    MIN_DELTA = -1.0
    MAX_GAMMA = 10.0
    MAX_VEGA = 100.0
    MIN_VEGA = 0.0
    
    # Probability Limits
    MAX_PROBABILITY = 100.0
    MIN_PROBABILITY = 0.0
    
    # Percentage Limits
    MAX_PERCENTAGE = 1000.0  # For some calculations that can exceed 100%
    MIN_PERCENTAGE = -1000.0
    
    # Tag Limits
    MAX_TAGS_PER_ITEM = 20
    MAX_TAG_LENGTH = 50
    
    # Symbol Limits
    MAX_SYMBOLS_PER_BOT = 1000
    MAX_SYMBOL_LENGTH = 10

# =============================================================================
# UTILITY MAPPING FUNCTIONS
# =============================================================================

def get_position_type_legs(position_type: PositionType) -> dict:
    """Get the required legs for a position type"""
    leg_configs = {
        PositionType.LONG_EQUITY: {},
        PositionType.LONG_CALL: {"long_call": True},
        PositionType.LONG_PUT: {"long_put": True},
        PositionType.LONG_CALL_SPREAD: {"long_call": True, "short_call": True},
        PositionType.LONG_PUT_SPREAD: {"long_put": True, "short_put": True},
        PositionType.SHORT_CALL_SPREAD: {"long_call": True, "short_call": True},
        PositionType.SHORT_PUT_SPREAD: {"long_put": True, "short_put": True},
        PositionType.IRON_CONDOR: {"long_call": True, "short_call": True, "long_put": True, "short_put": True},
        PositionType.IRON_BUTTERFLY: {"long_call": True, "short_call": True, "long_put": True, "short_put": True}
    }
    return leg_configs.get(position_type, {})

def get_default_exit_options() -> dict:
    """Get default exit options configuration"""
    return {
        "profit_taking": {"enabled": False, "percent": 50, "basis": ExitBasis.DEBIT.value},
        "price_target": {"enabled": False, "amount": 0, "direction": "or_higher"},
        "stop_loss": {"enabled": False, "percent": 50, "basis": ExitBasis.DEBIT.value},
        "trailing_stop": {"enabled": False, "activate_at_percent": 25, "pullback_percent": 10},
        "touch": {"enabled": False, "amount": 0, "from_itm": True},
        "expiration": {"enabled": False, "time_before": 1, "time_unit": TimeUnit.DAYS.value},
        "earnings": {"enabled": False, "days_before": 1},
        "additional_options": {
            "avoid_pdt": False,
            "max_bid_ask_spread": None
        }
    }

def get_common_delta_ranges() -> dict:
    """Get common delta ranges for strike selection"""
    return {
        "deep_itm": {"min": 0.8, "max": 1.0},
        "itm": {"min": 0.6, "max": 0.8},
        "atm": {"min": 0.4, "max": 0.6},
        "otm": {"min": 0.2, "max": 0.4},
        "deep_otm": {"min": 0.0, "max": 0.2}
    }