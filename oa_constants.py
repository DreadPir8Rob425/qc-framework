# Option Alpha Framework - Constants and Configuration
# Core constants used throughout the framework

from typing import Dict, Any

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
    CSV_FILE_EXTENSION = ".csv"
    
    # Default file names
    DEFAULT_CONFIG_FILE = "bot_config.json"
    DEFAULT_LOG_FILE = "oa_framework.log"
    DEFAULT_DATABASE_FILE = "oa_framework.db"
    DEFAULT_DATA_DIR = "backtest_data"
    
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

class SystemDefaults:
    """Default values used throughout the system"""
    
    # Logging defaults
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