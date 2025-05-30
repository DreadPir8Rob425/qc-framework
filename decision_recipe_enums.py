# Enhanced Option Alpha Bot Schema - Decision Recipe Enums
# All field enums for different decision recipe types

from enum import Enum

# =============================================================================
# DECISION RECIPE TYPES
# =============================================================================

class DecisionType(Enum):
    """Types of decision recipes"""
    STOCK = "stock"
    INDICATOR = "indicator"  
    POSITION = "position"
    BOT = "bot"
    OPPORTUNITY = "opportunity"
    GENERAL = "general"

# =============================================================================
# STOCK DECISION FIELD ENUMS
# =============================================================================

class StockPriceField(Enum):
    """Stock price fields for decision recipes"""
    ASK_PRICE = "ask_price"
    BID_PRICE = "bid_price"
    BID_ASK_SPREAD = "bid_ask_spread"
    CHANGE = "change"
    CHANGE_PERCENT = "change_percent"
    CHANGE_AS_STD_DEV = "change_as_std_dev"
    CLOSE_PRICE = "close_price"
    GAP = "gap"
    GAP_PERCENT = "gap_percent"
    HIGH_PRICE = "high_price"
    IV_RANK = "iv_rank"
    LAST_PRICE = "last_price"
    LOW_PRICE = "low_price"
    MID_PRICE = "mid_price"
    NVRP = "nvrp"
    OPEN_PRICE = "open_price"
    STD_DEV = "std_dev"
    VOLATILITY_RATIO = "volatility_ratio"
    VOLUME = "volume"
    EXPECTED_MOVE = "expected_move"
    TRADING_RANGE = "trading_range"

# =============================================================================
# TECHNICAL INDICATOR ENUMS
# =============================================================================

class TechnicalIndicator(Enum):
    """Technical indicators supported by Option Alpha"""
    # Oscillators
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
    
    # Moving Averages
    SMA = "SMA"
    EMA = "EMA"
    TRIMA = "TRIMA"
    KAMA = "KAMA"
    
    # Other Indicators  
    ATR = "ATR"
    BOP = "BOP"
    CMO = "CMO"
    DX = "DX"
    ROC = "ROC"
    BBANDS = "BBANDS"
    STOCH = "STOCH"

class IndicatorPeriod(Enum):
    """Common indicator periods"""
    PERIOD_5 = 5
    PERIOD_7 = 7
    PERIOD_9 = 9
    PERIOD_10 = 10
    PERIOD_14 = 14
    PERIOD_20 = 20
    PERIOD_30 = 30
    PERIOD_50 = 50
    PERIOD_60 = 60
    PERIOD_70 = 70
    PERIOD_80 = 80
    PERIOD_90 = 90
    PERIOD_100 = 100
    PERIOD_200 = 200

class IndicatorSignal(Enum):
    """Indicator signal types"""
    BUY = "buy"
    NEUTRAL = "neutral"
    SELL = "sell"

class MovingAverageType(Enum):
    """Moving average types"""
    SMA = "SMA"
    EMA = "EMA"
    TRIMA = "TRIMA"
    KAMA = "KAMA"

class BollingerBandLine(Enum):
    """Bollinger Band line types"""
    LOWER_BAND = "lower_band"
    MIDDLE_BAND = "middle_band"
    UPPER_BAND = "upper_band"

class MACDLine(Enum):
    """MACD line types"""
    SIGNAL = "signal"
    ZERO = "zero"

# =============================================================================
# POSITION DECISION FIELD ENUMS
# =============================================================================

class PositionField(Enum):
    """Position fields for decision recipes"""
    # P&L Fields
    ALPHA = "alpha"
    OPEN_PL = "open_pl"
    PL_PER_CONTRACT = "pl_per_contract"
    RETURN_PERCENT = "return_percent"
    RETURN_ON_RISK_PERCENT = "return_on_risk_percent"
    
    # Price Fields
    ASK_PRICE = "ask_price"
    BID_PRICE = "bid_price"
    BID_ASK_SPREAD = "bid_ask_spread"
    MID_PRICE = "mid_price"
    MARKET_VALUE = "market_value"
    TRADE_PRICE = "trade_price"
    UNDERLYING_PRICE = "underlying_price"
    UNDERLYING_PRICE_AT_OPEN = "underlying_price_at_open"
    
    # Greeks
    DELTA = "delta"
    GAMMA = "gamma"
    THETA = "theta"
    VEGA = "vega"
    BETA_WEIGHT = "beta_weight"
    
    # Risk Metrics
    EV = "ev"
    EV_PER_CONTRACT = "ev_per_contract"
    PROB_OF_PROFIT = "prob_of_profit"
    PROB_OF_MAX_PROFIT = "prob_of_max_profit"
    PROB_OF_MAX_LOSS = "prob_of_max_loss"
    REWARD_RISK = "reward_risk"
    RISK = "risk"
    
    # Position Details
    QUANTITY = "quantity"
    DAYS_OPEN = "days_open"
    DTE = "dte"
    SPREAD_WIDTH = "spread_width"
    MAINTENANCE = "maintenance"

class PositionLegField(Enum):
    """Position leg fields for decision recipes"""
    ASK_PRICE = "ask_price"
    BID_PRICE = "bid_price"
    BID_ASK_SPREAD = "bid_ask_spread"
    CHANCE_OF_ITM = "chance_of_itm"
    CHANGE = "change"
    CHANGE_PERCENT = "change_percent"
    CLOSE_PRICE = "close_price"
    DELTA = "delta"
    EXTRINSIC_VALUE = "extrinsic_value"
    GAMMA = "gamma"
    HIGH_PRICE = "high_price"
    INTRINSIC_VALUE = "intrinsic_value"
    LOW_PRICE = "low_price"
    MID_PRICE = "mid_price"
    OPEN_INTEREST = "open_interest"
    OPEN_PRICE = "open_price"
    OTM_AMOUNT = "otm_amount"
    THETA = "theta"
    VEGA = "vega"
    VOLUME = "volume"

# =============================================================================
# BOT DECISION FIELD ENUMS
# =============================================================================

class BotField(Enum):
    """Bot fields for decision recipes"""
    # Capital and Risk
    ALLOCATION = "allocation"
    AVAILABLE_CAPITAL = "available_capital"
    BETA_WEIGHT = "beta_weight"
    BETA_EXPOSURE = "beta_exposure"
    CAPITAL_AT_RISK = "capital_at_risk"
    MAINTENANCE = "maintenance"
    NET_LIQUID = "net_liquid"
    
    # P&L Fields
    DAY_PL = "day_pl"
    DAY_PL_PERCENT = "day_pl_percent"
    OPEN_PL = "open_pl"
    OPEN_PL_PERCENT = "open_pl_percent"
    TOTAL_PL = "total_pl"
    TOTAL_PL_PERCENT = "total_pl_percent"
    ODTE_PL_TOTAL = "odte_pl_total"
    ODTE_PL_OPEN = "odte_pl_open"
    ODTE_PL_CLOSED = "odte_pl_closed"
    
    # Statistics
    STREAK = "streak"
    WIN_RATE = "win_rate"
    TOTAL_DELTA = "total_delta"

class BotActionType(Enum):
    """Bot action types for decision recipes"""
    OPENED = "opened"
    CLOSED = "closed"

class BotTimeframe(Enum):
    """Bot timeframes for decision recipes"""
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"

# =============================================================================
# OPPORTUNITY DECISION FIELD ENUMS  
# =============================================================================

class OpportunityField(Enum):
    """Opportunity fields for decision recipes"""
    # Risk/Reward Metrics
    ALPHA = "alpha"
    REWARD_RISK = "reward_risk"
    EV = "ev"
    PROBABILITY_OF_PROFIT = "probability_of_profit"
    PROBABILITY_OF_MAX_PROFIT = "probability_of_max_profit"
    PROBABILITY_OF_MAX_LOSS = "probability_of_max_loss"
    
    # Price Fields
    ASK_PRICE = "ask_price"
    BID_PRICE = "bid_price"
    BID_ASK_SPREAD = "bid_ask_spread"
    MID_PRICE = "mid_price"
    
    # Greeks
    CHANGE = "change"
    DELTA = "delta"
    GAMMA = "gamma"
    THETA = "theta"
    VEGA = "vega"
    
    # Other Metrics
    NVRP = "nvrp"

class OpportunityLegField(Enum):
    """Opportunity leg fields for decision recipes"""
    ASK_PRICE = "ask_price"
    BID_PRICE = "bid_price"
    BID_ASK_SPREAD = "bid_ask_spread"
    CHANGE = "change"
    CHANGE_PERCENT = "change_percent"
    CLOSE_PRICE = "close_price"
    DELTA = "delta"
    EXTRINSIC_VALUE = "extrinsic_value"
    GAMMA = "gamma"
    HIGH_PRICE = "high_price"
    INTRINSIC_VALUE = "intrinsic_value"
    LOW_PRICE = "low_price"
    MID_PRICE = "mid_price"
    OPEN_INTEREST = "open_interest"
    OPEN_PRICE = "open_price"
    OTM_AMOUNT = "otm_amount"
    VEGA = "vega"
    VOLUME = "volume"

# =============================================================================
# GENERAL DECISION FIELD ENUMS
# =============================================================================

class GeneralConditionType(Enum):
    """General condition types for decision recipes"""
    MARKET_TIME = "market_time"
    MARKET_CLOSE_TIME = "market_close_time"
    MARKET_CLOSE_MINUTES = "market_close_minutes"
    DATE = "date"
    DAY_OF_WEEK = "day_of_week"
    ECONOMIC_EVENT = "economic_event"
    SWITCH_STATE = "switch_state"

class MarketCloseTime(Enum):
    """Market close times"""
    FOUR_PM = "4:00PM"
    ONE_PM = "1:00PM"

class SwitchState(Enum):
    """Switch states for general decisions"""
    ON = "on"
    OFF = "off"

# =============================================================================
# EXIT REASON ENUMS
# =============================================================================

class ExitReason(Enum):
    """Exit reasons for position closing"""
    ANY_REASON = "any_reason"
    ANY_EXIT_OPTION = "any_exit_option"
    PROFIT_TAKING = "profit_taking"
    PRICE_TARGET = "price_target"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    TOUCH = "touch"
    EARNINGS = "earnings"
    EXPIRATION = "expiration"

# =============================================================================
# MONEYNESS ENUMS
# =============================================================================

class Moneyness(Enum):
    """Option moneyness classifications"""
    OUT_OF_THE_MONEY = "out_of_the_money"
    IN_THE_MONEY = "in_the_money"

class BreakevenType(Enum):
    """Breakeven price types"""
    ANY = "any"
    CALL = "call"
    PUT = "put"

class StrikeType(Enum):
    """Strike price types"""
    BREAKEVEN = "breakeven"
    SHORT_STRIKE = "short_strike"
    LONG_STRIKE = "long_strike"

class LocationType(Enum):
    """Location relative to strikes/breakevens"""
    INSIDE = "inside"
    BEYOND = "beyond"