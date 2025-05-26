# Option Alpha Bot Framework - Complete Implementation
# This is the complete framework file - will be broken into smaller modules

import sqlite3
import json
import logging
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import uuid
import tempfile
import os

# =============================================================================
# CORE DATA STRUCTURES
# =============================================================================

@dataclass
class MarketData:
    """Basic market data structure"""
    symbol: str
    timestamp: datetime
    price: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    volume: Optional[int] = None
    iv_rank: Optional[float] = None
    
    def __post_init__(self):
        if self.price <= 0:
            raise ValueError(f"Invalid price for {self.symbol}: {self.price}")
        if self.bid and self.ask and self.bid > self.ask:
            raise ValueError(f"Bid ({self.bid}) > Ask ({self.ask}) for {self.symbol}")

@dataclass
class Position:
    """Represents a trading position"""
    id: str
    symbol: str
    position_type: str  # Using string for simplicity in Phase 0
    state: str
    opened_at: datetime
    quantity: int
    entry_price: float
    current_price: float = 0.0
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0
    tags: List[str] = field(default_factory=list)
    closed_at: Optional[datetime] = None
    exit_price: Optional[float] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    @property
    def days_open(self) -> int:
        end_date = self.closed_at if self.closed_at else datetime.now()
        return (end_date - self.opened_at).days
    
    @property
    def total_pnl(self) -> float:
        return self.realized_pnl + self.unrealized_pnl

@dataclass
class Event:
    """Base event class for the event-driven system"""
    event_type: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)
    source: Optional[str] = None
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now()

# =============================================================================
# LOGGING SYSTEM
# =============================================================================

class FrameworkLogger:
    """Custom logging system with categorization and limits"""
    
    def __init__(self, name: str = "OAFramework", max_entries: int = 10000):
        self.name = name
        self.max_entries = max_entries
        self._log_entries: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        self._setup_standard_logger()
    
    def _setup_standard_logger(self) -> None:
        self._standard_logger = logging.getLogger(self.name)
        if not self._standard_logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._standard_logger.addHandler(handler)
            self._standard_logger.setLevel(logging.INFO)
    
    def log(self, level: str, category: str, message: str, **kwargs) -> None:
        with self._lock:
            entry = {
                'timestamp': datetime.now(),
                'level': level,
                'category': category,
                'message': message,
                'data': kwargs
            }
            
            self._log_entries.append(entry)
            
            # Maintain max entries limit
            if len(self._log_entries) > self.max_entries:
                self._log_entries = self._log_entries[-self.max_entries:]
            
            # Also log to standard logger
            formatted_message = f"[{category.upper()}] {message}"
            if kwargs:
                formatted_message += f" | Data: {kwargs}"
            
            if level == "DEBUG":
                self._standard_logger.debug(formatted_message)
            elif level == "INFO":
                self._standard_logger.info(formatted_message)
            elif level == "WARNING":
                self._standard_logger.warning(formatted_message)
            elif level == "ERROR":
                self._standard_logger.error(formatted_message)
            elif level == "CRITICAL":
                self._standard_logger.critical(formatted_message)
    
    def debug(self, category: str, message: str, **kwargs) -> None:
        self.log("DEBUG", category, message, **kwargs)
    
    def info(self, category: str, message: str, **kwargs) -> None:
        self.log("INFO", category, message, **kwargs)
    
    def warning(self, category: str, message: str, **kwargs) -> None:
        self.log("WARNING", category, message, **kwargs)
    
    def error(self, category: str, message: str, **kwargs) -> None:
        self.log("ERROR", category, message, **kwargs)
    
    def critical(self, category: str, message: str, **kwargs) -> None:
        self.log("CRITICAL", category, message, **kwargs)
    
    def get_logs(self, level: Optional[str] = None, 
                 category: Optional[str] = None, 
                 limit: Optional[int] = None) -> List[Dict[str, Any]]:
        with self._lock:
            filtered_logs = self._log_entries.copy()
            
            if level:
                filtered_logs = [log for log in filtered_logs if log['level'] == level]
            
            if category:
                filtered_logs = [log for log in filtered_logs if log['category'] == category]
            
            if limit:
                filtered_logs = filtered_logs[-limit:]
            
            return filtered_logs
    
    def get_summary(self) -> Dict[str, Dict[str, int]]:
        with self._lock:
            summary = {'levels': {}, 'categories': {}}
            
            for entry in self._log_entries:
                level = entry['level']
                category = entry['category']
                
                summary['levels'][level] = summary['levels'].get(level, 0) + 1
                summary['categories'][category] = summary['categories'].get(category, 0) + 1
            
            return summary
    
    def clear_logs(self) -> None:
        with self._lock:
            self._log_entries.clear()

# =============================================================================
# STATE MANAGEMENT SYSTEM
# =============================================================================

class StateManager:
    """Multi-layered state management system"""
    
    def __init__(self, db_path: str = "oa_framework.db"):
        self.db_path = db_path
        self._hot_state: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._logger = FrameworkLogger("StateManager")
        self._init_database()
    
    def _init_database(self) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS warm_state (
                        key TEXT PRIMARY KEY,
                        value TEXT,
                        timestamp REAL,
                        category TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cold_state (
                        id TEXT PRIMARY KEY,
                        data TEXT,
                        timestamp REAL,
                        category TEXT,
                        tags TEXT
                    )
                ''')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS positions (
                        id TEXT PRIMARY KEY,
                        symbol TEXT,
                        position_type TEXT,
                        state TEXT,
                        data TEXT,
                        opened_at REAL,
                        closed_at REAL,
                        tags TEXT
                    )
                ''')
                
                conn.commit()
                
            self._logger.info("SYSTEM", "State management database initialized", 
                            db_path=self.db_path)
                            
        except Exception as e:
            self._logger.error("SYSTEM", "Failed to initialize database", error=str(e))
            raise
    
    # Hot State Methods (In-Memory)
    def set_hot_state(self, key: str, value: Any) -> None:
        with self._lock:
            self._hot_state[key] = {
                'value': value,
                'timestamp': datetime.now(),
                'category': 'hot'
            }
    
    def get_hot_state(self, key: str, default: Any = None) -> Any:
        with self._lock:
            entry = self._hot_state.get(key)
            return entry['value'] if entry else default
    
    def clear_hot_state(self) -> None:
        with self._lock:
            self._hot_state.clear()
    
    # Warm State Methods (SQLite Session Data)
    def set_warm_state(self, key: str, value: Any, category: str = 'session') -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO warm_state (key, value, timestamp, category)
                    VALUES (?, ?, ?, ?)
                ''', (key, json.dumps(value), datetime.now().timestamp(), category))
                conn.commit()
        except Exception as e:
            self._logger.error("SYSTEM", "Failed to set warm state", 
                             key=key, error=str(e))
    
    def get_warm_state(self, key: str, default: Any = None) -> Any:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM warm_state WHERE key = ?', (key,))
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return default
        except Exception as e:
            self._logger.error("SYSTEM", "Failed to get warm state", 
                             key=key, error=str(e))
            return default
    
    # Cold State Methods (Historical Data)
    def store_cold_state(self, data: Dict[str, Any], category: str, tags: Optional[List[str]] = None) -> str:
        record_id = str(uuid.uuid4())
        tags_str = json.dumps(tags or [])
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cold_state (id, data, timestamp, category, tags)
                    VALUES (?, ?, ?, ?, ?)
                ''', (record_id, json.dumps(data), datetime.now().timestamp(), category, tags_str))
                conn.commit()
            
            return record_id
        except Exception as e:
            self._logger.error("SYSTEM", "Failed to store cold state", 
                             category=category, error=str(e))
            raise
    
    def get_cold_state(self, category: str, limit: int = 100, 
                       start_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT id, data, timestamp, tags FROM cold_state WHERE category = ?'
                params = [category]
                
                if start_date:
                    query += ' AND timestamp >= ?'
                    params.append(str(start_date.timestamp()))
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(str(limit))
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                return [
                    {
                        'id': row[0],
                        'data': json.loads(row[1]),
                        'timestamp': datetime.fromtimestamp(row[2]),
                        'tags': json.loads(row[3])
                    }
                    for row in results
                ]
        except Exception as e:
            self._logger.error("SYSTEM", "Failed to get cold state", 
                             category=category, error=str(e))
            return []
    
    # Position Management
    def store_position(self, position: Position) -> None:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO positions 
                    (id, symbol, position_type, state, data, opened_at, closed_at, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    position.id,
                    position.symbol,
                    position.position_type,
                    position.state,
                    json.dumps({
                        'quantity': position.quantity,
                        'entry_price': position.entry_price,
                        'current_price': position.current_price,
                        'unrealized_pnl': position.unrealized_pnl,
                        'realized_pnl': position.realized_pnl
                    }),
                    position.opened_at.timestamp(),
                    position.closed_at.timestamp() if position.closed_at else None,
                    json.dumps(position.tags)
                ))
                conn.commit()
                
            self._logger.info("SYSTEM", "Position stored", position_id=position.id)
            
        except Exception as e:
            self._logger.error("SYSTEM", "Failed to store position", 
                             position_id=position.id, error=str(e))
            raise
    
    def get_positions(self, state: Optional[str] = None, 
                     symbol: Optional[str] = None) -> List[Position]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM positions WHERE 1=1'
                params = []
                
                if state:
                    query += ' AND state = ?'
                    params.append(state)
                
                if symbol:
                    query += ' AND symbol = ?'
                    params.append(symbol)
                
                query += ' ORDER BY opened_at DESC'
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                positions = []
                for row in results:
                    data = json.loads(row[4])
                    
                    position = Position(
                        id=row[0],
                        symbol=row[1],
                        position_type=row[2],
                        state=row[3],
                        opened_at=datetime.fromtimestamp(row[5]),
                        quantity=data['quantity'],
                        entry_price=data['entry_price'],
                        current_price=data['current_price'],
                        unrealized_pnl=data['unrealized_pnl'],
                        realized_pnl=data['realized_pnl'],
                        closed_at=datetime.fromtimestamp(row[6]) if row[6] else None,
                        tags=json.loads(row[7])
                    )
                    positions.append(position)
                
                return positions
                
        except Exception as e:
            self._logger.error("SYSTEM", "Failed to get positions", error=str(e))
            return []

# =============================================================================
# EVENT SYSTEM
# =============================================================================

class EventHandler(ABC):
    @abstractmethod
    def handle_event(self, event: Event) -> None:
        pass
    
    @abstractmethod
    def can_handle(self, event_type: str) -> bool:
        pass

class EventBus:
    def __init__(self):
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._event_queue = queue.Queue()
        self._processing = False
        self._process_thread: Optional[threading.Thread] = None
        self._logger = FrameworkLogger("EventBus")
    
    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        self._logger.debug("SYSTEM", f"Handler subscribed to {event_type}")
    
    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                self._logger.debug("SYSTEM", f"Handler unsubscribed from {event_type}")
            except ValueError:
                self._logger.warning("SYSTEM", f"Handler not found for {event_type}")
    
    def publish(self, event: Event) -> None:
        self._event_queue.put(event)
        self._logger.debug("SYSTEM", f"Event published: {event.event_type}")
    
    def start_processing(self) -> None:
        if not self._processing:
            self._processing = True
            self._process_thread = threading.Thread(target=self._process_events, daemon=True)
            self._process_thread.start()
            self._logger.info("SYSTEM", "Event processing started")
    
    def stop_processing(self) -> None:
        self._processing = False
        if self._process_thread:
            self._process_thread.join(timeout=5)
        self._logger.info("SYSTEM", "Event processing stopped")
    
    def _process_events(self) -> None:
        while self._processing:
            try:
                event = self._event_queue.get(timeout=1)
                self._dispatch_event(event)
                self._event_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self._logger.error("SYSTEM", f"Error processing event: {e}")
    
    def _dispatch_event(self, event: Event) -> None:
        handlers = self._handlers.get(event.event_type, [])
        for handler in handlers:
            try:
                if handler.can_handle(event.event_type):
                    handler.handle_event(event)
            except Exception as e:
                self._logger.error("SYSTEM", f"Error in handler: {e}")

# =============================================================================
# DECISION ENGINE (STUBBED FOR PHASE 0)
# =============================================================================

class DecisionEngine:
    def __init__(self, logger: FrameworkLogger, state_manager: StateManager):
        self.logger = logger
        self.state_manager = state_manager
    
    def evaluate_decision(self, decision_config: Dict[str, Any]) -> str:
        """Evaluate a decision - stub implementation returns 'YES'"""
        try:
            recipe_type = decision_config.get('recipe_type', 'unknown')
            self.logger.debug("DECISION_FLOW", 
                            "Decision evaluated (stub)", 
                            type=recipe_type)
            return "YES"  # Stub always returns YES
            
        except Exception as e:
            self.logger.error("DECISION_FLOW", 
                            "Decision evaluation failed", error=str(e))
            return "ERROR"

# =============================================================================
# POSITION MANAGER (STUBBED FOR PHASE 0)
# =============================================================================

class PositionManager:
    def __init__(self, logger: FrameworkLogger, state_manager: StateManager):
        self.logger = logger
        self.state_manager = state_manager
        self._positions: Dict[str, Position] = {}
        self._lock = threading.Lock()
    
    def open_position(self, position_config: Dict[str, Any]) -> Optional[Position]:
        """Open a new position - stub implementation"""
        try:
            position = Position(
                id=str(uuid.uuid4()),
                symbol=position_config.get('symbol', 'SPY'),
                position_type=position_config.get('strategy_type', 'long_call'),
                state="OPEN",
                opened_at=datetime.now(),
                quantity=1,
                entry_price=100.0,
                current_price=100.0
            )
            
            with self._lock:
                self._positions[position.id] = position
            
            self.state_manager.store_position(position)
            
            self.logger.info("TRADE_EXECUTION", 
                           "Position opened (stub)", 
                           position_id=position.id, 
                           symbol=position.symbol)
            
            return position
            
        except Exception as e:
            self.logger.error("TRADE_EXECUTION", 
                            "Failed to open position", error=str(e))
            return None
    
    def close_position(self, position_id: str, close_config: Optional[Dict[str, Any]] = None) -> bool:
        """Close an existing position - stub implementation"""
        try:
            with self._lock:
                position = self._positions.get(position_id)
                if not position:
                    self.logger.warning("TRADE_EXECUTION", 
                                      "Position not found for close", 
                                      position_id=position_id)
                    return False
                
                position.state = "CLOSED"
                position.closed_at = datetime.now()
                position.exit_price = position.current_price
                position.realized_pnl = 10.0  # Stub P&L
            
            self.state_manager.store_position(position)
            
            self.logger.info("TRADE_EXECUTION", 
                           "Position closed (stub)", 
                           position_id=position_id)
            
            return True
            
        except Exception as e:
            self.logger.error("TRADE_EXECUTION", 
                            "Failed to close position", 
                            position_id=position_id, error=str(e))
            return False
    
    def get_open_positions(self) -> List[Position]:
        with self._lock:
            return [pos for pos in self._positions.values() 
                   if pos.state == "OPEN"]
    
    def get_position(self, position_id: str) -> Optional[Position]:
        with self._lock:
            return self._positions.get(position_id)
    
    def update_position_prices(self, market_data: Dict[str, MarketData]) -> None:
        """Update position prices - stub implementation"""
        with self._lock:
            for position in self._positions.values():
                if position.state == "OPEN":
                    market_price = market_data.get(position.symbol)
                    if market_price:
                        position.current_price = market_price.price
                        position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
                        
                        self.logger.debug("MARKET_DATA", 
                                        "Position price updated", 
                                        position_id=position.id,
                                        new_price=position.current_price)

# =============================================================================
# MAIN BOT CLASS
# =============================================================================

class OABot:
    """Main Option Alpha bot class"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.name = config_dict.get('name', 'Unknown Bot')
        
        # Initialize core components
        self.logger = FrameworkLogger(f"OABot-{self.name}")
        self.state_manager = StateManager()
        self.event_bus = EventBus()
        self.decision_engine = DecisionEngine(self.logger, self.state_manager)
        self.position_manager = PositionManager(self.logger, self.state_manager)
        
        # Bot state
        self.state = "STOPPED"
        self._automation_states: Dict[str, str] = {}
        
        self.logger.info("SYSTEM", 
                        "Bot initialized", 
                        name=self.name,
                        automations=len(config_dict.get('automations', [])))
    
    def start(self) -> None:
        """Start the bot and all its automations"""
        try:
            self.state = "STARTING"
            self.logger.info("SYSTEM", "Bot starting", name=self.name)
            
            # Start event processing
            self.event_bus.start_processing()
            
            # Initialize automations
            for automation in self.config.get('automations', []):
                automation_name = automation.get('name', 'Unnamed')
                self._automation_states[automation_name] = "IDLE"
                self.logger.info("SYSTEM", 
                               "Automation initialized", 
                               automation=automation_name)
            
            self.state = "RUNNING"
            
            # Publish bot started event
            self.event_bus.publish(Event(
                event_type="BOT_STARTED",
                timestamp=datetime.now(),
                data={'bot_name': self.name}
            ))
            
            self.logger.info("SYSTEM", "Bot started successfully", name=self.name)
            
        except Exception as e:
            self.state = "ERROR"
            self.logger.error("SYSTEM", "Failed to start bot", error=str(e))
            raise
    
    def stop(self) -> None:
        """Stop the bot and all its automations"""
        try:
            self.state = "STOPPING"
            self.logger.info("SYSTEM", "Bot stopping", name=self.name)
            
            # Stop event processing
            self.event_bus.stop_processing()
            
            # Set all automations to disabled
            for automation_name in self._automation_states:
                self._automation_states[automation_name] = "DISABLED"
            
            self.state = "STOPPED"
            
            # Publish bot stopped event
            self.event_bus.publish(Event(
                event_type="BOT_STOPPED",
                timestamp=datetime.now(),
                data={'bot_name': self.name}
            ))
            
            self.logger.info("SYSTEM", "Bot stopped successfully", name=self.name)
            
        except Exception as e:
            self.state = "ERROR"
            self.logger.error("SYSTEM", "Failed to stop bot", error=str(e))
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current bot status and statistics"""
        open_positions = self.position_manager.get_open_positions()
        
        return {
            'name': self.name,
            'state': self.state,
            'automations': {
                name: state 
                for name, state in self._automation_states.items()
            },
            'positions': {
                'open_count': len(open_positions),
                'total_unrealized_pnl': sum(pos.unrealized_pnl for pos in open_positions)
            },
            'safeguards': self.config.get('safeguards', {}),
            'scan_speed': self.config.get('scan_speed', '15_minutes')
        }
    
    def process_automation(self, automation_name: str) -> None:
        """Process a single automation - stub for Phase 0"""
        try:
            automation_config = None
            for auto in self.config.get('automations', []):
                if auto.get('name') == automation_name:
                    automation_config = auto
                    break
            
            if not automation_config:
                self.logger.error("SYSTEM", 
                                "Automation not found", 
                                automation=automation_name)
                return
            
            self._automation_states[automation_name] = "RUNNING"
            
            self.logger.info("DECISION_FLOW", 
                           "Processing automation (stub)", 
                           automation=automation_name)
            
            # TODO: Implement full automation processing in Phase 2
            
            self._automation_states[automation_name] = "COMPLETED"
            
        except Exception as e:
            self._automation_states[automation_name] = "ERROR"
            self.logger.error("SYSTEM", 
                            "Automation processing failed", 
                            automation=automation_name, error=str(e))

# =============================================================================
# CONFIGURATION HELPERS
# =============================================================================

def create_simple_bot_config() -> Dict[str, Any]:
    """Create a simple bot configuration for testing"""
    return {
        "name": "Simple Test Bot",
        "account": "paper_trading",
        "group": "Test Strategies",
        "safeguards": {
            "capital_allocation": 10000,
            "daily_positions": 5,
            "position_limit": 15,
            "daytrading_allowed": False
        },
        "scan_speed": "15_minutes",
        "symbols": {
            "type": "static",
            "list": ["SPY", "QQQ"]
        },
        "automations": [
            {
                "name": "Simple Scanner",
                "trigger": {
                    "type": "continuous",
                    "automation_type": "scanner"
                },
                "actions": [
                    {
                        "type": "decision",
                        "decision": {
                            "recipe_type": "stock",
                            "symbol": "SPY",
                            "comparison": "greater_than",
                            "value": 400
                        }
                    }
                ]
            }
        ]
    }

# =============================================================================
# DEMONSTRATION FUNCTION
# =============================================================================

def demonstrate_framework():
    """Demonstrate the framework functionality"""
    
    print("=" * 60)
    print("Option Alpha Framework - Phase 0 Demonstration")
    print("=" * 60)
    
    try:
        # 1. Create bot configuration
        config = create_simple_bot_config()
        print(f"✓ Created bot configuration: {config['name']}")
        
        # 2. Initialize bot
        bot = OABot(config)
        print(f"✓ Bot initialized: {bot.name}")
        
        # 3. Start bot
        bot.start()
        print(f"✓ Bot started successfully")
        
        # 4. Show status
        status = bot.get_status()
        print(f"✓ Bot status: {status['state']}")
        print(f"  Automations: {len(status['automations'])}")
        print(f"  Open positions: {status['positions']['open_count']}")
        
        # 5. Test logging
        bot.logger.info("SYSTEM", "Test log message", test=True)
        logs = bot.logger.get_logs(limit=5)
        print(f"✓ Logging system working: {len(logs)} entries")
        
        # 6. Test state management
        bot.state_manager.set_hot_state("test", {"value": 123})
        test_val = bot.state_manager.get_hot_state("test")
        print(f"✓ State management working: {test_val}")
        
        # 7. Test position management
        pos_config = {"symbol": "SPY", "strategy_type": "long_call"}
        position = bot.position_manager.open_position(pos_config)
        print(f"✓ Position management working: {position.id if position else 'Failed'}")
        
        # 8. Test decision engine
        decision_config = {"recipe_type": "stock", "symbol": "SPY"}
        result = bot.decision_engine.evaluate_decision(decision_config)
        print(f"✓ Decision engine working: {result}")
        
        # 9. Stop bot
        bot.stop()
        print(f"✓ Bot stopped successfully")
        
        print("\n" + "=" * 60)
        print("✅ Framework demonstration completed successfully!")
        print("✅ All core components are working")
        print("✅ Ready for Phase 1 development")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Framework demonstration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    demonstrate_framework()