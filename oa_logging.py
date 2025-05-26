# Option Alpha Framework - Logging System
# Custom logging system with categorization and QuantConnect compatibility

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, TextIO
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path

# =============================================================================
# LOGGING ENUMS AND CONSTANTS
# =============================================================================

class LogLevel(Enum):
    """Logging levels for the framework"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogCategory(Enum):
    """Categories for organizing log messages"""
    TRADE_EXECUTION = "TRADE_EXECUTION"
    DECISION_FLOW = "DECISION_FLOW"
    MARKET_DATA = "MARKET_DATA"
    PERFORMANCE = "PERFORMANCE"
    SYSTEM = "SYSTEM"
    DEBUG = "DEBUG"
    AUTOMATION = "AUTOMATION"
    RISK_MANAGEMENT = "RISK_MANAGEMENT"

# =============================================================================
# LOG ENTRY STRUCTURE
# =============================================================================

@dataclass
class LogEntry:
    """Represents a single log entry"""
    timestamp: datetime
    level: LogLevel
    category: LogCategory
    message: str
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    thread_id: Optional[int] = None
    
    def __post_init__(self):
        """Set thread ID if not provided"""
        if self.thread_id is None:
            self.thread_id = threading.get_ident()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert log entry to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'level': self.level.value,
            'category': self.category.value,
            'message': self.message,
            'data': self.data,
            'source': self.source,
            'thread_id': self.thread_id
        }
    
    def to_json(self) -> str:
        """Convert log entry to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogEntry':
        """Create log entry from dictionary"""
        return cls(
            timestamp=datetime.fromisoformat(data['timestamp']),
            level=LogLevel(data['level']),
            category=LogCategory(data['category']),
            message=data['message'],
            data=data.get('data', {}),
            source=data.get('source'),
            thread_id=data.get('thread_id')
        )

# =============================================================================
# LOG FORMATTERS
# =============================================================================

class LogFormatter:
    """Base class for log formatters"""
    
    def format(self, entry: LogEntry) -> str:
        """Format a log entry"""
        raise NotImplementedError

class StandardFormatter(LogFormatter):
    """Standard text formatter for log entries"""
    
    def __init__(self, include_thread: bool = False, include_data: bool = True):
        self.include_thread = include_thread
        self.include_data = include_data
    
    def format(self, entry: LogEntry) -> str:
        """Format log entry as standard text"""
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        
        parts = [
            timestamp,
            entry.level.value,
            entry.category.value,
            entry.message
        ]
        
        if self.include_thread:
            parts.insert(-1, f"[{entry.thread_id}]")
        
        if entry.source:
            parts.insert(-1, f"({entry.source})")
        
        formatted = " | ".join(parts)
        
        if self.include_data and entry.data:
            formatted += f" | Data: {json.dumps(entry.data)}"
        
        return formatted

class JSONFormatter(LogFormatter):
    """JSON formatter for log entries"""
    
    def format(self, entry: LogEntry) -> str:
        """Format log entry as JSON"""
        return entry.to_json()

class CompactFormatter(LogFormatter):
    """Compact formatter for space-constrained environments"""
    
    def format(self, entry: LogEntry) -> str:
        """Format log entry in compact format"""
        timestamp = entry.timestamp.strftime("%H:%M:%S")
        level = entry.level.value[0]  # First letter only
        category = entry.category.value[:4]  # First 4 letters
        
        formatted = f"{timestamp} {level} {category} {entry.message}"
        
        if entry.data:
            # Only include first data item for compactness
            first_key = next(iter(entry.data.keys()))
            formatted += f" ({first_key}={entry.data[first_key]})"
        
        return formatted

# =============================================================================
# LOG HANDLERS
# =============================================================================

class LogHandler:
    """Base class for log handlers"""
    
    def __init__(self, formatter: LogFormatter = None):
        self.formatter = formatter or StandardFormatter()
    
    def emit(self, entry: LogEntry) -> None:
        """Emit a log entry"""
        raise NotImplementedError
    
    def close(self) -> None:
        """Close the handler"""
        pass

class MemoryHandler(LogHandler):
    """Handler that stores log entries in memory"""
    
    def __init__(self, max_entries: int = 10000, formatter: LogFormatter = None):
        super().__init__(formatter)
        self.max_entries = max_entries
        self.entries: List[LogEntry] = []
        self._lock = threading.Lock()
    
    def emit(self, entry: LogEntry) -> None:
        """Store log entry in memory"""
        with self._lock:
            self.entries.append(entry)
            
            # Maintain max entries limit
            if len(self.entries) > self.max_entries:
                self.entries = self.entries[-self.max_entries:]
    
    def get_entries(self, level: Optional[LogLevel] = None,
                   category: Optional[LogCategory] = None,
                   limit: Optional[int] = None,
                   since: Optional[datetime] = None) -> List[LogEntry]:
        """Get log entries with optional filtering"""
        with self._lock:
            filtered = list(self.entries)
            
            if level:
                filtered = [e for e in filtered if e.level == level]
            
            if category:
                filtered = [e for e in filtered if e.category == category]
            
            if since:
                filtered = [e for e in filtered if e.timestamp >= since]
            
            if limit:
                filtered = filtered[-limit:]
            
            return filtered
    
    def clear(self) -> None:
        """Clear all log entries"""
        with self._lock:
            self.entries.clear()

class FileHandler(LogHandler):
    """Handler that writes log entries to a file"""
    
    def __init__(self, filepath: str, formatter: LogFormatter = None, 
                 max_size_mb: float = 100, backup_count: int = 5):
        super().__init__(formatter)
        self.filepath = Path(filepath)
        self.max_size_bytes = int(max_size_mb * 1024 * 1024)
        self.backup_count = backup_count
        self._file: Optional[TextIO] = None
        self._lock = threading.Lock()
        
        # Create directory if it doesn't exist
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Open file for writing
        self._open_file()
    
    def _open_file(self) -> None:
        """Open the log file for writing"""
        self._file = open(self.filepath, 'a', encoding='utf-8')
    
    def _rotate_file(self) -> None:
        """Rotate the log file if it exceeds max size"""
        if not self.filepath.exists():
            return
        
        if self.filepath.stat().st_size < self.max_size_bytes:
            return
        
        # Close current file
        if self._file:
            self._file.close()
        
        # Rotate backup files
        for i in range(self.backup_count - 1, 0, -1):
            old_file = self.filepath.with_suffix(f'.{i}')
            new_file = self.filepath.with_suffix(f'.{i + 1}')
            
            if old_file.exists():
                if new_file.exists():
                    new_file.unlink()
                old_file.rename(new_file)
        
        # Move current file to .1
        backup_file = self.filepath.with_suffix('.1')
        if backup_file.exists():
            backup_file.unlink()
        self.filepath.rename(backup_file)
        
        # Reopen file
        self._open_file()
    
    def emit(self, entry: LogEntry) -> None:
        """Write log entry to file"""
        with self._lock:
            if self._file:
                formatted = self.formatter.format(entry)
                self._file.write(formatted + '\n')
                self._file.flush()
                
                # Check if rotation is needed
                self._rotate_file()
    
    def close(self) -> None:
        """Close the file handler"""
        with self._lock:
            if self._file:
                self._file.close()
                self._file = None

class ConsoleHandler(LogHandler):
    """Handler that writes log entries to console"""
    
    def __init__(self, formatter: LogFormatter = None, min_level: LogLevel = LogLevel.INFO):
        super().__init__(formatter)
        self.min_level = min_level
    
    def emit(self, entry: LogEntry) -> None:
        """Write log entry to console"""
        # Only emit if entry level is at or above minimum level
        level_order = {
            LogLevel.DEBUG: 0,
            LogLevel.INFO: 1,
            LogLevel.WARNING: 2,
            LogLevel.ERROR: 3,
            LogLevel.CRITICAL: 4
        }
        
        if level_order[entry.level] >= level_order[self.min_level]:
            formatted = self.formatter.format(entry)
            print(formatted)

# =============================================================================
# MAIN LOGGER CLASS
# =============================================================================

class FrameworkLogger:
    """
    Main logging class for the Option Alpha Framework.
    Supports multiple handlers and provides categorized logging.
    """
    
    def __init__(self, name: str = "OAFramework", handlers: List[LogHandler] = None):
        self.name = name
        self.handlers: List[LogHandler] = handlers or []
        self._lock = threading.Lock()
        
        # Add default memory handler if no handlers provided
        if not self.handlers:
            self.handlers.append(MemoryHandler())
        
        # Set up standard Python logger as fallback
        self._setup_standard_logger()
    
    def _setup_standard_logger(self) -> None:
        """Setup standard Python logger as fallback"""
        self._standard_logger = logging.getLogger(self.name)
        if not self._standard_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._standard_logger.addHandler(handler)
            self._standard_logger.setLevel(logging.INFO)
    
    def add_handler(self, handler: LogHandler) -> None:
        """Add a log handler"""
        with self._lock:
            self.handlers.append(handler)
    
    def remove_handler(self, handler: LogHandler) -> None:
        """Remove a log handler"""
        with self._lock:
            if handler in self.handlers:
                self.handlers.remove(handler)
                handler.close()
    
    def log(self, level: LogLevel, category: LogCategory, message: str, 
            source: Optional[str] = None, **kwargs) -> None:
        """Log a message with specified level and category"""
        
        entry = LogEntry(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            data=kwargs,
            source=source or self.name
        )
        
        # Emit to all handlers
        with self._lock:
            for handler in self.handlers:
                try:
                    handler.emit(entry)
                except Exception as e:
                    # Fallback to standard logger if handler fails
                    self._standard_logger.error(f"Handler failed: {e}")
        
        # Also log to standard logger for compatibility
        self._log_to_standard(level, category, message, **kwargs)
    
    def _log_to_standard(self, level: LogLevel, category: LogCategory, 
                        message: str, **kwargs) -> None:
        """Log to standard Python logger"""
        formatted_message = f"[{category.value}] {message}"
        if kwargs:
            formatted_message += f" | {kwargs}"
        
        if level == LogLevel.DEBUG:
            self._standard_logger.debug(formatted_message)
        elif level == LogLevel.INFO:
            self._standard_logger.info(formatted_message)
        elif level == LogLevel.WARNING:
            self._standard_logger.warning(formatted_message)
        elif level == LogLevel.ERROR:
            self._standard_logger.error(formatted_message)
        elif level == LogLevel.CRITICAL:
            self._standard_logger.critical(formatted_message)
    
    # Convenience methods for different log levels
    def debug(self, category: LogCategory, message: str, **kwargs) -> None:
        """Log debug message"""
        self.log(LogLevel.DEBUG, category, message, **kwargs)
    
    def info(self, category: LogCategory, message: str, **kwargs) -> None:
        """Log info message"""
        self.log(LogLevel.INFO, category, message, **kwargs)
    
    def warning(self, category: LogCategory, message: str, **kwargs) -> None:
        """Log warning message"""
        self.log(LogLevel.WARNING, category, message, **kwargs)
    
    def error(self, category: LogCategory, message: str, **kwargs) -> None:
        """Log error message"""
        self.log(LogLevel.ERROR, category, message, **kwargs)
    
    def critical(self, category: LogCategory, message: str, **kwargs) -> None:
        """Log critical message"""
        self.log(LogLevel.CRITICAL, category, message, **kwargs)
    
    # Methods for retrieving logs (from memory handler)
    def get_logs(self, level: Optional[LogLevel] = None,
                category: Optional[LogCategory] = None,
                limit: Optional[int] = None,
                since: Optional[datetime] = None) -> List[LogEntry]:
        """Get log entries from memory handler"""
        memory_handlers = [h for h in self.handlers if isinstance(h, MemoryHandler)]
        if memory_handlers:
            return memory_handlers[0].get_entries(level, category, limit, since)
        return []
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of log entries"""
        entries = self.get_logs()
        
        summary = {
            'total_entries': len(entries),
            'levels': {},
            'categories': {},
            'recent_errors': [],
            'time_range': {}
        }
        
        if entries:
            # Count by level and category
            for entry in entries:
                level_key = entry.level.value
                category_key = entry.category.value
                
                summary['levels'][level_key] = summary['levels'].get(level_key, 0) + 1
                summary['categories'][category_key] = summary['categories'].get(category_key, 0) + 1
            
            # Get recent errors
            error_entries = [e for e in entries if e.level in [LogLevel.ERROR, LogLevel.CRITICAL]]
            summary['recent_errors'] = [
                {'timestamp': e.timestamp.isoformat(), 'message': e.message}
                for e in error_entries[-5:]  # Last 5 errors
            ]
            
            # Time range
            summary['time_range'] = {
                'oldest': entries[0].timestamp.isoformat(),
                'newest': entries[-1].timestamp.isoformat()
            }
        
        return summary
    
    def clear_logs(self) -> None:
        """Clear all log entries from memory handlers"""
        memory_handlers = [h for h in self.handlers if isinstance(h, MemoryHandler)]
        for handler in memory_handlers:
            handler.clear()
    
    def close(self) -> None:
        """Close all handlers"""
        with self._lock:
            for handler in self.handlers:
                handler.close()
            self.handlers.clear()

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_file_logger(name: str, log_dir: str = "logs") -> FrameworkLogger:
    """Create a logger that writes to file"""
    log_file = Path(log_dir) / f"{name}.log"
    
    handlers = [
        MemoryHandler(max_entries=1000),
        FileHandler(str(log_file), StandardFormatter()),
        ConsoleHandler(CompactFormatter(), LogLevel.INFO)
    ]
    
    return FrameworkLogger(name,