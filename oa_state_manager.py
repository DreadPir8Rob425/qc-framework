# Option Alpha Framework - State Management System
# Multi-layered state management with hot/warm/cold storage

import sqlite3
import json
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import uuid
from contextlib import contextmanager

from oa_data_structures import Position, TradeRecord, PortfolioSnapshot
from oa_logging import FrameworkLogger, LogCategory, LogLevel

# =============================================================================
# STATE MANAGEMENT CONSTANTS
# =============================================================================

class StateConstants:
    DEFAULT_DATABASE_FILE = "oa_framework.db"
    DEFAULT_MAX_HOT_ENTRIES = 1000
    DEFAULT_CONNECTION_TIMEOUT = 30
    DEFAULT_QUERY_TIMEOUT = 60
    VACUUM_INTERVAL_HOURS = 24

# =============================================================================
# MULTI-LAYERED STATE MANAGER
# =============================================================================

class StateManager:
    """
    Multi-layered state management system:
    - Hot State: In-memory for real-time decisions (current positions, prices)
    - Warm State: SQLite for session data (daily P&L, automation status)
    - Cold State: SQLite for historical data (completed trades, analytics)
    """
    
    def __init__(self, db_path: str = None, max_hot_entries: int = None):
        self.db_path = Path(db_path or StateConstants.DEFAULT_DATABASE_FILE)
        self.max_hot_entries = max_hot_entries or StateConstants.DEFAULT_MAX_HOT_ENTRIES
        
        # Hot state storage (in-memory)
        self._hot_state: Dict[str, Any] = {}
        self._hot_state_timestamps: Dict[str, datetime] = {}
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        
        # Initialize logger
        self.logger = FrameworkLogger("StateManager")
        
        # Initialize database
        self._init_database()
        
        # Track last vacuum time
        self._last_vacuum = datetime.now()
        
        self.logger.info(LogCategory.SYSTEM, "State manager initialized", 
                        db_path=str(self.db_path))
    
    def _init_database(self) -> None:
        """Initialize SQLite database with required tables"""
        try:
            # Create directory if it doesn't exist
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Warm state table for session data
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS warm_state (
                        key TEXT PRIMARY KEY,
                        value TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        category TEXT NOT NULL DEFAULT 'default',
                        expires_at REAL
                    )
                ''')
                
                # Cold state table for historical data
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS cold_state (
                        id TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        timestamp REAL NOT NULL,
                        category TEXT NOT NULL,
                        tags TEXT,
                        metadata TEXT
                    )
                ''')
                
                # Positions table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS positions (
                        id TEXT PRIMARY KEY,
                        symbol TEXT NOT NULL,
                        position_type TEXT NOT NULL,
                        state TEXT NOT NULL,
                        data TEXT NOT NULL,
                        opened_at REAL NOT NULL,
                        closed_at REAL,
                        tags TEXT,
                        bot_name TEXT,
                        automation_name TEXT
                    )
                ''')
                
                # Trades table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS trades (
                        trade_id TEXT PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        symbol TEXT NOT NULL,
                        action TEXT NOT NULL,
                        position_type TEXT NOT NULL,
                        quantity INTEGER NOT NULL,
                        price REAL NOT NULL,
                        fees REAL DEFAULT 0,
                        pnl REAL DEFAULT 0,
                        position_id TEXT,
                        bot_name TEXT,
                        automation_name TEXT,
                        tags TEXT
                    )
                ''')
                
                # Portfolio snapshots table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS portfolio_snapshots (
                        id TEXT PRIMARY KEY,
                        timestamp REAL NOT NULL,
                        total_value REAL NOT NULL,
                        cash_balance REAL NOT NULL,
                        positions_value REAL NOT NULL,
                        open_positions INTEGER NOT NULL,
                        pnl_today REAL NOT NULL,
                        pnl_all_time REAL NOT NULL,
                        portfolio_delta REAL DEFAULT 0,
                        portfolio_gamma REAL DEFAULT 0,
                        portfolio_theta REAL DEFAULT 0,
                        portfolio_vega REAL DEFAULT 0,
                        max_risk REAL DEFAULT 0,
                        additional_data TEXT
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_warm_state_category ON warm_state(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_warm_state_timestamp ON warm_state(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cold_state_category ON cold_state(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cold_state_timestamp ON cold_state(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_state ON positions(state)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_portfolio_snapshots_timestamp ON portfolio_snapshots(timestamp)')
                
                conn.commit()
                
            self.logger.info(LogCategory.SYSTEM, "Database initialized successfully")
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to initialize database", 
                            error=str(e), db_path=str(self.db_path))
            raise
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper error handling"""
        conn = None
        try:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=StateConstants.DEFAULT_CONNECTION_TIMEOUT,
                check_same_thread=False
            )
            conn.execute('PRAGMA journal_mode=WAL')  # Better for concurrent access
            conn.execute('PRAGMA synchronous=NORMAL')  # Good balance of safety and speed
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(LogCategory.SYSTEM, "Database connection error", error=str(e))
            raise
        finally:
            if conn:
                conn.close()
    
    # =============================================================================
    # HOT STATE METHODS (In-Memory)
    # =============================================================================
    
    def set_hot_state(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """Set hot state value with optional TTL"""
        with self._lock:
            self._hot_state[key] = value
            self._hot_state_timestamps[key] = datetime.now()
            
            # Set expiration if TTL provided
            if ttl_seconds:
                expires_at = datetime.now() + timedelta(seconds=ttl_seconds)
                self._hot_state[f"_ttl_{key}"] = expires_at
            
            # Cleanup old entries if over limit
            self._cleanup_hot_state()
    
    def get_hot_state(self, key: str, default: Any = None) -> Any:
        """Get hot state value with TTL check"""
        with self._lock:
            # Check if key has TTL and is expired
            ttl_key = f"_ttl_{key}"
            if ttl_key in self._hot_state:
                if datetime.now() > self._hot_state[ttl_key]:
                    # Expired, remove both value and TTL
                    self._hot_state.pop(key, None)
                    self._hot_state.pop(ttl_key, None)
                    self._hot_state_timestamps.pop(key, None)
                    return default
            
            return self._hot_state.get(key, default)
    
    def delete_hot_state(self, key: str) -> bool:
        """Delete hot state key"""
        with self._lock:
            deleted = key in self._hot_state
            self._hot_state.pop(key, None)
            self._hot_state_timestamps.pop(key, None)
            self._hot_state.pop(f"_ttl_{key}", None)
            return deleted
    
    def clear_hot_state(self) -> None:
        """Clear all hot state"""
        with self._lock:
            self._hot_state.clear()
            self._hot_state_timestamps.clear()
    
    def get_hot_state_keys(self) -> List[str]:
        """Get all hot state keys (excluding TTL keys)"""
        with self._lock:
            return [k for k in self._hot_state.keys() if not k.startswith("_ttl_")]
    
    def _cleanup_hot_state(self) -> None:
        """Clean up old hot state entries"""
        if len(self._hot_state) <= self.max_hot_entries:
            return
        
        # Sort by timestamp and keep only the most recent entries
        sorted_keys = sorted(
            self._hot_state_timestamps.items(),
            key=lambda x: x[1]
        )
        
        # Remove oldest entries
        entries_to_remove = len(sorted_keys) - self.max_hot_entries
        for key, _ in sorted_keys[:entries_to_remove]:
            if not key.startswith("_ttl_"):  # Don't count TTL keys in cleanup
                self._hot_state.pop(key, None)
                self._hot_state_timestamps.pop(key, None)
                self._hot_state.pop(f"_ttl_{key}", None)
    
    # =============================================================================
    # WARM STATE METHODS (SQLite Session Data)
    # =============================================================================
    
    def set_warm_state(self, key: str, value: Any, category: str = 'session', 
                      expires_in_hours: Optional[int] = None) -> None:
        """Set warm state value in SQLite"""
        try:
            expires_at = None
            if expires_in_hours:
                expires_at = (datetime.now() + timedelta(hours=expires_in_hours)).timestamp()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO warm_state 
                    (key, value, timestamp, category, expires_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    key, 
                    json.dumps(value), 
                    datetime.now().timestamp(), 
                    category,
                    expires_at
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to set warm state", 
                            key=key, error=str(e))
    
    def get_warm_state(self, key: str, default: Any = None) -> Any:
        """Get warm state value from SQLite"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT value, expires_at FROM warm_state 
                    WHERE key = ?
                ''', (key,))
                result = cursor.fetchone()
                
                if result:
                    value_json, expires_at = result
                    
                    # Check expiration
                    if expires_at and datetime.now().timestamp() > expires_at:
                        # Expired, delete and return default
                        cursor.execute('DELETE FROM warm_state WHERE key = ?', (key,))
                        conn.commit()
                        return default
                    
                    return json.loads(value_json)
                
                return default
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to get warm state", 
                            key=key, error=str(e))
            return default
    
    def delete_warm_state(self, key: str) -> bool:
        """Delete warm state key"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM warm_state WHERE key = ?', (key,))
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to delete warm state", 
                            key=key, error=str(e))
            return False
    
    def get_warm_state_by_category(self, category: str) -> Dict[str, Any]:
        """Get all warm state entries for a category"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT key, value FROM warm_state 
                    WHERE category = ? AND (expires_at IS NULL OR expires_at > ?)
                    ORDER BY timestamp DESC
                ''', (category, datetime.now().timestamp()))
                
                results = {}
                for row in cursor.fetchall():
                    key, value_json = row
                    results[key] = json.loads(value_json)
                
                return results
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to get warm state by category", 
                            category=category, error=str(e))
            return {}
    
    # =============================================================================
    # COLD STATE METHODS (Historical Data)
    # =============================================================================
    
    def store_cold_state(self, data: Dict[str, Any], category: str, 
                        tags: Optional[List[str]] = None, metadata: Dict[str, Any] = None) -> str:
        """Store cold state data (historical)"""
        record_id = str(uuid.uuid4())
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO cold_state (id, data, timestamp, category, tags, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    record_id,
                    json.dumps(data),
                    datetime.now().timestamp(),
                    category,
                    json.dumps(tags or []),
                    json.dumps(metadata or {})
                ))
                conn.commit()
            
            return record_id
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to store cold state", 
                            category=category, error=str(e))
            raise
    
    def get_cold_state(self, category: str, limit: int = 100, 
                      start_date: Optional[datetime] = None,
                      end_date: Optional[datetime] = None,
                      tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Get cold state data by category with filtering"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = '''
                    SELECT id, data, timestamp, tags, metadata 
                    FROM cold_state 
                    WHERE category = ?
                '''
                params = [category]
                
                if start_date:
                    query += ' AND timestamp >= ?'
                    params.append(str(start_date.timestamp()))
                
                if end_date:
                    query += ' AND timestamp <= ?'
                    params.append(str(end_date.timestamp()))
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(str(limit))
                
                cursor.execute(query, params)
                results = []
                
                for row in cursor.fetchall():
                    record_id, data_json, timestamp, tags_json, metadata_json = row
                    
                    record_tags = json.loads(tags_json)
                    
                    # Filter by tags if specified
                    if tags and not any(tag in record_tags for tag in tags):
                        continue
                    
                    results.append({
                        'id': record_id,
                        'data': json.loads(data_json),
                        'timestamp': datetime.fromtimestamp(timestamp),
                        'tags': record_tags,
                        'metadata': json.loads(metadata_json)
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to get cold state", 
                            category=category, error=str(e))
            return []
    
    def delete_cold_state(self, record_id: str) -> bool:
        """Delete cold state record by ID"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM cold_state WHERE id = ?', (record_id,))
                deleted = cursor.rowcount > 0
                conn.commit()
                return deleted
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to delete cold state", 
                            record_id=record_id, error=str(e))
            return False
    
    # =============================================================================
    # POSITION MANAGEMENT
    # =============================================================================
    
    def store_position(self, position: Position) -> None:
        """Store position in database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Prepare position data
                position_data = {
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': position.current_price,
                    'unrealized_pnl': position.unrealized_pnl,
                    'realized_pnl': position.realized_pnl,
                    'exit_price': position.exit_price,
                    'exit_reason': position.exit_reason,
                    'legs': [
                        {
                            'option_type': leg.option_type,
                            'side': leg.side,
                            'strike': leg.strike,
                            'expiration': leg.expiration.isoformat(),
                            'quantity': leg.quantity,
                            'entry_price': leg.entry_price,
                            'current_price': leg.current_price,
                            'delta': leg.delta,
                            'gamma': leg.gamma,
                            'theta': leg.theta,
                            'vega': leg.vega,
                            'rho': leg.rho
                        }
                        for leg in position.legs
                    ]
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO positions 
                    (id, symbol, position_type, state, data, opened_at, closed_at, 
                     tags, bot_name, automation_name)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    position.id,
                    position.symbol,
                    position.position_type,
                    position.state,
                    json.dumps(position_data),
                    position.opened_at.timestamp(),
                    position.closed_at.timestamp() if position.closed_at else None,
                    json.dumps(position.tags),
                    getattr(position, 'bot_name', None),
                    position.automation_source
                ))
                
                conn.commit()
                
            self.logger.debug(LogCategory.SYSTEM, "Position stored", 
                            position_id=position.id, symbol=position.symbol)
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to store position", 
                            position_id=position.id, error=str(e))
            raise
    
    def get_positions(self, state: Optional[str] = None, 
                     symbol: Optional[str] = None,
                     bot_name: Optional[str] = None,
                     limit: int = 1000) -> List[Position]:
        """Get positions from database with filtering"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM positions WHERE 1=1'
                params = []
                
                if state:
                    query += ' AND state = ?'
                    params.append(state)
                
                if symbol:
                    query += ' AND symbol = ?'
                    params.append(symbol)
                
                if bot_name:
                    query += ' AND bot_name = ?'
                    params.append(bot_name)
                
                query += ' ORDER BY opened_at DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                positions = []
                
                for row in cursor.fetchall():
                    (pos_id, symbol, pos_type, state, data_json, opened_at, 
                     closed_at, tags_json, bot_name, automation_name) = row
                    
                    data = json.loads(data_json)
                    
                    # Reconstruct position object
                    if symbol is not None and state is not None:
                        position = Position(
                            id=pos_id,
                            symbol=symbol,
                            position_type=pos_type,
                            state=state,
                            opened_at=datetime.fromtimestamp(opened_at),
                            quantity=data['quantity'],
                            entry_price=data['entry_price'],
                            current_price=data['current_price'],
                            unrealized_pnl=data['unrealized_pnl'],
                            realized_pnl=data['realized_pnl'],
                            closed_at=datetime.fromtimestamp(closed_at) if closed_at else None,
                            exit_price=data.get('exit_price'),
                            exit_reason=data.get('exit_reason'),
                            tags=json.loads(tags_json),
                            automation_source=automation_name
                        )
                        
                    # Reconstruct legs if present
                    for leg_data in data.get('legs', []):
                        from oa_data_structures import OptionLeg
                        leg = OptionLeg(
                            option_type=leg_data['option_type'],
                            side=leg_data['side'],
                            strike=leg_data['strike'],
                            expiration=datetime.fromisoformat(leg_data['expiration']),
                            quantity=leg_data['quantity'],
                            entry_price=leg_data['entry_price'],
                            current_price=leg_data['current_price'],
                            delta=leg_data['delta'],
                            gamma=leg_data['gamma'],
                            theta=leg_data['theta'],
                            vega=leg_data['vega'],
                            rho=leg_data['rho']
                        )
                        position.add_leg(leg)
                    
                    positions.append(position)
                
                return positions
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to get positions", error=str(e))
            return []
    
    def get_position_by_id(self, position_id: str) -> Optional[Position]:
        """Get specific position by ID"""
        positions = self.get_positions()
        for position in positions:
            if position.id == position_id:
                return position
        return None
    
    # =============================================================================
    # TRADE RECORDING
    # =============================================================================
    
    def record_trade(self, trade: TradeRecord) -> None:
        """Record a trade in the database"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO trades 
                    (trade_id, timestamp, symbol, action, position_type, quantity, 
                     price, fees, pnl, position_id, bot_name, automation_name, tags)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    trade.trade_id,
                    trade.timestamp.timestamp(),
                    trade.symbol,
                    trade.action,
                    trade.position_type,
                    trade.quantity,
                    trade.price,
                    trade.fees,
                    trade.pnl,
                    trade.position_id,
                    trade.bot_name,
                    trade.automation_name,
                    json.dumps(trade.tags)
                ))
                conn.commit()
                
            self.logger.debug(LogCategory.TRADE_EXECUTION, "Trade recorded", 
                            trade_id=trade.trade_id, symbol=trade.symbol)
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Failed to record trade", 
                            trade_id=trade.trade_id, error=str(e))
            raise
    
    def get_trades(self, symbol: Optional[str] = None, 
                  bot_name: Optional[str] = None,
                  start_date: Optional[datetime] = None,
                  end_date: Optional[datetime] = None,
                  limit: int = 1000) -> List[TradeRecord]:
        """Get trades with filtering"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM trades WHERE 1=1'
                params = []
                
                if symbol is not None:
                    query += ' AND symbol = ?'
                    params.append(symbol)
                
                if bot_name:
                    query += ' AND bot_name = ?'
                    params.append(bot_name)
                
                if start_date:
                    query += ' AND timestamp >= ?'
                    params.append(start_date.timestamp())
                
                if end_date:
                    query += ' AND timestamp <= ?'
                    params.append(end_date.timestamp())
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                trades = []
                
                for row in cursor.fetchall():
                    (trade_id, timestamp, symbol, action, position_type, quantity,
                     price, fees, pnl, position_id, bot_name, automation_name, tags_json) = row
                    
                    if symbol is not None:
                        trade = TradeRecord(
                            trade_id=trade_id,
                            timestamp=datetime.fromtimestamp(timestamp),
                            symbol=symbol,
                            action=action,
                            position_type=position_type,
                            quantity=quantity,
                            price=price,
                            fees=fees,
                            pnl=pnl,
                            position_id=position_id,
                            bot_name=bot_name,
                            automation_name=automation_name,
                            tags=json.loads(tags_json)
                        )
                        trades.append(trade)
                
                return trades
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to get trades", error=str(e))
            return []
    
    # =============================================================================
    # PORTFOLIO SNAPSHOTS
    # =============================================================================
    
    def store_portfolio_snapshot(self, snapshot: PortfolioSnapshot) -> None:
        """Store portfolio snapshot"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                additional_data = {
                    'buying_power_used': getattr(snapshot, 'buying_power_used', 0)
                }
                
                cursor.execute('''
                    INSERT INTO portfolio_snapshots 
                    (id, timestamp, total_value, cash_balance, positions_value, 
                     open_positions, pnl_today, pnl_all_time, portfolio_delta, 
                     portfolio_gamma, portfolio_theta, portfolio_vega, max_risk, additional_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    str(uuid.uuid4()),
                    snapshot.timestamp.timestamp(),
                    snapshot.total_value,
                    snapshot.cash_balance,
                    snapshot.positions_value,
                    snapshot.open_positions,
                    snapshot.total_pnl_today,
                    snapshot.total_pnl_all_time,
                    snapshot.portfolio_delta,
                    snapshot.portfolio_gamma,
                    snapshot.portfolio_theta,
                    snapshot.portfolio_vega,
                    snapshot.max_risk,
                    json.dumps(additional_data)
                ))
                conn.commit()
                
        except Exception as e:
            self.logger.error(LogCategory.PERFORMANCE, "Failed to store portfolio snapshot", 
                            error=str(e))
            raise
    
    def get_portfolio_snapshots(self, start_date: Optional[datetime] = None,
                               end_date: Optional[datetime] = None,
                               limit: int = 1000) -> List[PortfolioSnapshot]:
        """Get portfolio snapshots with filtering"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM portfolio_snapshots WHERE 1=1'
                params = []
                
                if start_date:
                    query += ' AND timestamp >= ?'
                    params.append(start_date.timestamp())
                
                if end_date:
                    query += ' AND timestamp <= ?'
                    params.append(end_date.timestamp())
                
                query += ' ORDER BY timestamp DESC LIMIT ?'
                params.append(limit)
                
                cursor.execute(query, params)
                snapshots = []
                
                for row in cursor.fetchall():
                    (snap_id, timestamp, total_value, cash_balance, positions_value,
                     open_positions, pnl_today, pnl_all_time, portfolio_delta,
                     portfolio_gamma, portfolio_theta, portfolio_vega, max_risk, additional_data_json) = row
                    
                    additional_data = json.loads(additional_data_json)
                    
                    snapshot = PortfolioSnapshot(
                        timestamp=datetime.fromtimestamp(timestamp),
                        total_value=total_value,
                        cash_balance=cash_balance,
                        positions_value=positions_value,
                        open_positions=open_positions,
                        total_pnl_today=pnl_today,
                        total_pnl_all_time=pnl_all_time,
                        portfolio_delta=portfolio_delta,
                        portfolio_gamma=portfolio_gamma,
                        portfolio_theta=portfolio_theta,
                        portfolio_vega=portfolio_vega,
                        max_risk=max_risk,
                        buying_power_used=additional_data.get('buying_power_used', 0)
                    )
                    snapshots.append(snapshot)
                
                return snapshots
                
        except Exception as e:
            self.logger.error(LogCategory.PERFORMANCE, "Failed to get portfolio snapshots", 
                            error=str(e))
            return []
    
    # =============================================================================
    # MAINTENANCE AND UTILITIES
    # =============================================================================
    
    def vacuum_database(self) -> None:
        """Vacuum database to reclaim space and optimize performance"""
        try:
            with self._get_connection() as conn:
                conn.execute('VACUUM')
                conn.commit()
            
            self._last_vacuum = datetime.now()
            self.logger.info(LogCategory.SYSTEM, "Database vacuumed successfully")
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to vacuum database", error=str(e))
    
    def cleanup_expired_entries(self) -> None:
        """Clean up expired entries from all tables"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Clean up expired warm state entries
                cursor.execute('''
                    DELETE FROM warm_state 
                    WHERE expires_at IS NOT NULL AND expires_at < ?
                ''', (datetime.now().timestamp(),))
                
                warm_deleted = cursor.rowcount
                
                # Clean up old cold state entries (older than 1 year by default)
                one_year_ago = datetime.now() - timedelta(days=365)
                cursor.execute('''
                    DELETE FROM cold_state 
                    WHERE timestamp < ? AND category != 'permanent'
                ''', (one_year_ago.timestamp(),))
                
                cold_deleted = cursor.rowcount
                
                # Clean up old portfolio snapshots (keep only last 10,000)
                cursor.execute('''
                    DELETE FROM portfolio_snapshots 
                    WHERE id NOT IN (
                        SELECT id FROM portfolio_snapshots 
                        ORDER BY timestamp DESC LIMIT 10000
                    )
                ''')
                
                snapshots_deleted = cursor.rowcount
                
                conn.commit()
                
                self.logger.info(LogCategory.SYSTEM, "Cleanup completed", 
                               warm_deleted=warm_deleted, cold_deleted=cold_deleted,
                               snapshots_deleted=snapshots_deleted)
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to cleanup expired entries", 
                            error=str(e))
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                tables = ['warm_state', 'cold_state', 'positions', 'trades', 'portfolio_snapshots']
                for table in tables:
                    cursor.execute(f'SELECT COUNT(*) FROM {table}')
                    stats[f'{table}_count'] = cursor.fetchone()[0]
                
                # Database file size
                stats['database_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)
                
                # Hot state statistics
                with self._lock:
                    stats['hot_state_count'] = len(self._hot_state)
                    stats['hot_state_memory_mb'] = len(str(self._hot_state)) / (1024 * 1024)
                
                return stats
                
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to get database stats", 
                            error=str(e))
            return {}
    
    def close(self) -> None:
        """Close state manager and clean up resources"""
        try:
            # Check if vacuum is needed
            if datetime.now() - self._last_vacuum > timedelta(hours=StateConstants.VACUUM_INTERVAL_HOURS):
                self.vacuum_database()
            
            # Clean up expired entries
            self.cleanup_expired_entries()
            
            # Clear hot state
            self.clear_hot_state()
            
            self.logger.info(LogCategory.SYSTEM, "State manager closed successfully")
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Error closing state manager", error=str(e))

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def create_memory_state_manager() -> StateManager:
    """Create a state manager that uses in-memory database"""
    return StateManager(":memory:")

def create_test_state_manager() -> StateManager:
    """Create a state manager for testing with temporary database"""
    import tempfile
    db_file = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    return StateManager(db_file.name)

# =============================================================================
# DEMONSTRATION
# =============================================================================

def demonstrate_state_management():
    """Demonstrate state management capabilities"""
    print("Option Alpha Framework - State Management Demo")
    print("=" * 60)
    
    # Create test state manager
    state_manager = create_test_state_manager()
    
    try:
        # Test hot state
        print("Testing Hot State (In-Memory):")
        state_manager.set_hot_state("current_price", {"SPY": 450.25, "QQQ": 380.15})
        state_manager.set_hot_state("temp_data", "expires_soon", ttl_seconds=2)
        
        price_data = state_manager.get_hot_state("current_price")
        print(f"  ✓ Hot state retrieved: {price_data}")
        
        import time
        time.sleep(3)  # Wait for TTL expiration
        expired_data = state_manager.get_hot_state("temp_data", "DEFAULT")
        print(f"  ✓ TTL working: {expired_data}")
        
        # Test warm state
        print("\nTesting Warm State (SQLite Session):")
        session_data = {"bot_name": "TestBot", "started_at": datetime.now().isoformat()}
        state_manager.set_warm_state("session_info", session_data, "bot_session")
        
        retrieved_session = state_manager.get_warm_state("session_info")
        print(f"  ✓ Warm state retrieved: {retrieved_session['bot_name']}")
        
        # Test cold state
        print("\nTesting Cold State (Historical Data):")
        trade_data = {"symbol": "SPY", "action": "BUY", "quantity": 100, "pnl": 150.0}
        record_id = state_manager.store_cold_state(trade_data, "completed_trades", 
                                                 ["profitable", "spy"])
        print(f"  ✓ Cold state stored: {record_id}")
        
        historical_trades = state_manager.get_cold_state("completed_trades", limit=5)
        print(f"  ✓ Retrieved {len(historical_trades)} historical records")
        
        # Test position storage
        print("\nTesting Position Storage:")
        from oa_data_structures import create_test_position
        position = create_test_position("SPY", "long_call")
        state_manager.store_position(position)
        
        retrieved_positions = state_manager.get_positions(symbol="SPY")
        print(f"  ✓ Position stored and retrieved: {len(retrieved_positions)} positions")
        
        # Test trade recording
        print("\nTesting Trade Recording:")
        from oa_data_structures import TradeRecord
        trade = TradeRecord(
            trade_id="T001",
            timestamp=datetime.now(),
            symbol="SPY",
            action="OPEN",
            position_type="long_call",
            quantity=1,
            price=450.0,
            pnl=25.0
        )
        state_manager.record_trade(trade)
        
        trades = state_manager.get_trades(symbol="SPY")
        print(f"  ✓ Trade recorded: {len(trades)} trades found")
        
        # Test portfolio snapshots
        print("\nTesting Portfolio Snapshots:")
        from oa_data_structures import PortfolioSnapshot
        snapshot = PortfolioSnapshot(
            timestamp=datetime.now(),
            total_value=50000.0,
            cash_balance=45000.0,
            positions_value=5000.0,
            open_positions=1,
            total_pnl_today=150.0,
            total_pnl_all_time=2500.0
        )
        state_manager.store_portfolio_snapshot(snapshot)
        
        snapshots = state_manager.get_portfolio_snapshots(limit=5)
        print(f"  ✓ Portfolio snapshot stored: {len(snapshots)} snapshots")
        
        # Test database statistics
        print("\nDatabase Statistics:")
        stats = state_manager.get_database_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("✅ State management demonstration completed successfully!")
        
    finally:
        state_manager.close()

if __name__ == "__main__":
    demonstrate_state_management()