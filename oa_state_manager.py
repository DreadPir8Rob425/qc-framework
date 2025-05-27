# Option Alpha Framework - Enhanced State Management System
# Multi-layered state management with SQLite performance and CSV export capabilities

import sqlite3
import csv
import json
import threading
import uuid
import os
from enum import Enum
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from oa_framework_enums import LogCategory, PositionState, ErrorCode, OptionType
from oa_logging import FrameworkLogger
from pathlib import Path
import tempfile
import zipfile

# Optional dependencies for enhanced functionality
try:
    import boto3
    S3_AVAILABLE = True
except ImportError:
    S3_AVAILABLE = False
    boto3 = None

try:
    import pandas as pd
    if pd is not None:
        PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False
    pd = None

# Import framework components
from oa_framework_enums import *

# =============================================================================
# CUSTOM JSON ENCODER FOR FRAMEWORK ENUMS
# =============================================================================

class FrameworkJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles framework enums and objects"""
    
    def default(self, obj):
        # Handle all enum types
        if isinstance(obj, Enum):
            return obj.value
        
        # Handle datetime objects
        if isinstance(obj, datetime):
            return obj.isoformat()
        
        # Handle sets
        if isinstance(obj, set):
            return list(obj)
        
        # Let the base class handle other types
        return super().default(obj)
    
    
# =============================================================================
# ENHANCED STATE MANAGER WITH CSV EXPORT
# =============================================================================

class StateManager:
    """
    Multi-layered state management system with CSV export capabilities:
    - Hot State: In-memory for real-time decisions
    - Warm State: SQLite for session data (fast queries)
    - Cold State: SQLite for historical data (fast queries)
    - CSV Export: Export all data to CSV files for S3 upload
    """
    
    def __init__(self, db_path: str = FrameworkConstants.DEFAULT_DATABASE_FILE):
        self.db_path = db_path
        self._hot_state: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._logger = FrameworkLogger("StateManager")
        self._init_database()
        
        # CSV export configuration
        self.export_directory = "exports"
        self.s3_client = None
        self.s3_bucket = None
        
    def _init_database(self) -> None:
        """Initialize SQLite database for warm and cold state"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create tables for different state types
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
                
                # Add indexes for better query performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_warm_state_category ON warm_state(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cold_state_category ON cold_state(category)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_cold_state_timestamp ON cold_state(timestamp)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_symbol ON positions(symbol)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_state ON positions(state)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_positions_opened_at ON positions(opened_at)')
                
                conn.commit()
                
            self._logger.info(LogCategory.SYSTEM, "State management database initialized", 
                            db_path=self.db_path)
                            
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to initialize database", error=str(e))
            raise
    
    # =============================================================================
    # EXISTING STATE MANAGEMENT METHODS (Hot/Warm/Cold)
    # =============================================================================
    
    def set_hot_state(self, key: str, value: Any) -> None:
        """Set hot state value (in-memory)"""
        with self._lock:
            self._hot_state[key] = {
                'value': value,
                'timestamp': datetime.now(),
                'category': 'hot'
            }
    
    def get_hot_state(self, key: str, default: Any = None) -> Any:
        """Get hot state value"""
        with self._lock:
            entry = self._hot_state.get(key)
            return entry['value'] if entry else default
    
    def clear_hot_state(self) -> None:
        """Clear all hot state"""
        with self._lock:
            self._hot_state.clear()
    
    def set_warm_state(self, key: str, value: Any, category: str = 'session') -> None:
        """Set warm state value (SQLite)"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO warm_state (key, value, timestamp, category)
                    VALUES (?, ?, ?, ?)
                ''', (key, json.dumps(value), datetime.now().timestamp(), category))
                conn.commit()
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to set warm state", 
                             key=key, error=str(e))
    
    def get_warm_state(self, key: str, default: Any = None) -> Any:
        """Get warm state value"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT value FROM warm_state WHERE key = ?', (key,))
                result = cursor.fetchone()
                if result:
                    return json.loads(result[0])
                return default
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to get warm state", 
                             key=key, error=str(e))
            return default
    
    def store_cold_state(self, data: Dict[str, Any], category: str, tags: Optional[List[str]] = None) -> str:
        """Store cold state data (historical)"""
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
            self._logger.error(LogCategory.SYSTEM, "Failed to store cold state", 
                             storage_category=category, error=str(e))
            raise
    
    def get_cold_state(self, category: str, limit: int = 100, 
                       start_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get cold state data by category"""
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
            self._logger.error(LogCategory.SYSTEM, "Failed to get cold state", 
                             storage_category=category, error=str(e))
            return []
    
    def store_position(self, position) -> None:
        """Store position in database"""
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
                    position.position_type.value,
                    position.state.value,
                    json.dumps({
                        'quantity': position.quantity,
                        'entry_price': position.entry_price,
                        'current_price': position.current_price,
                        'unrealized_pnl': position.unrealized_pnl,
                        'realized_pnl': position.realized_pnl,
                        'exit_price': position.exit_price,
                        'legs': [
                            {
                                'option_type': leg.option_type.value,
                                'side': leg.side.value,
                                'strike': leg.strike,
                                'expiration': leg.expiration.isoformat(),
                                'quantity': leg.quantity,
                                'entry_price': leg.entry_price,
                                'current_price': leg.current_price,
                                'delta': leg.delta,
                                'gamma': leg.gamma,
                                'theta': leg.theta,
                                'vega': leg.vega
                            }
                            for leg in position.legs
                        ]
                    }),
                    position.opened_at.timestamp(),
                    position.closed_at.timestamp() if position.closed_at else None,
                    json.dumps(position.tags)
                ))
                conn.commit()
                
            self._logger.info(LogCategory.SYSTEM, "Position stored", position_id=position.id)
            
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to store position", 
                             position_id=position.id, error=str(e))
            raise
    
    def get_positions(self, state: Optional[PositionState] = None, 
                     symbol: Optional[str] = None) -> List:
        """Get positions from database with optional filters"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM positions WHERE 1=1'
                params = []
                
                if state:
                    query += ' AND state = ?'
                    params.append(state.value)
                
                if symbol:
                    query += ' AND symbol = ?'
                    params.append(symbol)
                
                query += ' ORDER BY opened_at DESC'
                
                cursor.execute(query, params)
                results = cursor.fetchall()
                
                # Import here to avoid circular imports
                from oa_framework_core import Position, OptionLeg
                
                positions = []
                for row in results:
                    data = json.loads(row[4])
                    
                    # Reconstruct legs
                    legs = []
                    for leg_data in data.get('legs', []):
                        leg = OptionLeg(
                            option_type=QCOptionRight(leg_data['option_type']),
                            side=OptionSide(leg_data['side']),
                            strike=leg_data['strike'],
                            expiration=datetime.fromisoformat(leg_data['expiration']),
                            quantity=leg_data['quantity'],
                            entry_price=leg_data['entry_price'],
                            current_price=leg_data['current_price'],
                            delta=leg_data['delta'],
                            gamma=leg_data['gamma'],
                            theta=leg_data['theta'],
                            vega=leg_data['vega']
                        )
                        legs.append(leg)
                    
                    position = Position(
                        id=row[0],
                        symbol=row[1],
                        position_type=PositionType(row[2]),
                        state=PositionState(row[3]),
                        opened_at=datetime.fromtimestamp(row[5]),
                        quantity=data['quantity'],
                        entry_price=data['entry_price'],
                        current_price=data['current_price'],
                        unrealized_pnl=data['unrealized_pnl'],
                        realized_pnl=data['realized_pnl'],
                        legs=legs,
                        closed_at=datetime.fromtimestamp(row[6]) if row[6] else None,
                        exit_price=data.get('exit_price'),
                        tags=json.loads(row[7])
                    )
                    positions.append(position)
                
                return positions
                
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to get positions", error=str(e))
            return []
    
    # =============================================================================
    # CSV EXPORT FUNCTIONALITY
    # =============================================================================
    
    def configure_s3_export(self, bucket_name: str, aws_access_key_id: Optional[str] = None, 
                           aws_secret_access_key: Optional[str] = None, region_name: str = 'us-east-1'):
        """
        Configure S3 credentials for CSV export
        
        Args:
            bucket_name: S3 bucket name
            aws_access_key_id: AWS access key (optional if using IAM roles)
            aws_secret_access_key: AWS secret key (optional if using IAM roles)
            region_name: AWS region name
        """
        if not S3_AVAILABLE:
            raise RuntimeError("boto3 library not available. Install with: pip install boto3")
        
        try:
            if boto3 is not None:
                if aws_access_key_id and aws_secret_access_key:
                    self.s3_client = boto3.client(
                        's3',
                        aws_access_key_id=aws_access_key_id,
                        aws_secret_access_key=aws_secret_access_key,
                        region_name=region_name
                    )
                else:
                    # Use default credentials (IAM role, ~/.aws/credentials, etc.)
                    self.s3_client = boto3.client('s3', region_name=region_name)
                
                self.s3_bucket = bucket_name
                
                self._logger.info(LogCategory.SYSTEM, "S3 configuration completed",  # type: ignore
                                bucket=bucket_name, region=region_name)
            else:
                self._logger.error(LogCategory.SYSTEM, "boto3 was None")
                
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to configure S3", error=str(e))
            raise
    
    def export_to_csv(self, export_dir: Optional[str] = None, include_hot_state: bool = True) -> Dict[str, str]:
        """
        Export all SQLite data to CSV files
        
        Args:
            export_dir: Directory to save CSV files (creates temp dir if None)
            include_hot_state: Whether to include hot state in export
            
        Returns:
            Dictionary mapping table names to CSV file paths
        """
        if export_dir is None:
            export_dir = tempfile.mkdtemp(prefix="oa_export_")
        
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        exported_files = {}
        
        try:
            # Export warm state
            warm_state_file = export_path / "warm_state.csv"
            self._export_warm_state_to_csv(warm_state_file)
            exported_files['warm_state'] = str(warm_state_file)
            
            # Export cold state  
            cold_state_file = export_path / "cold_state.csv"
            self._export_cold_state_to_csv(cold_state_file)
            exported_files['cold_state'] = str(cold_state_file)
            
            # Export positions
            positions_file = export_path / "positions.csv"
            self._export_positions_to_csv(positions_file)
            exported_files['positions'] = str(positions_file)
            
            # Export positions summary (flattened for analysis)
            positions_summary_file = export_path / "positions_summary.csv"
            self._export_positions_summary_to_csv(positions_summary_file)
            exported_files['positions_summary'] = str(positions_summary_file)
            
            # Export hot state if requested
            if include_hot_state:
                hot_state_file = export_path / "hot_state.csv"
                self._export_hot_state_to_csv(hot_state_file)
                exported_files['hot_state'] = str(hot_state_file)
            
            # Create export manifest
            manifest_file = export_path / "export_manifest.json"
            self._create_export_manifest(manifest_file, exported_files)
            exported_files['manifest'] = str(manifest_file)
            
            self._logger.info(LogCategory.SYSTEM, "CSV export completed", 
                            export_dir=export_dir, files_count=len(exported_files))
            
            return exported_files
            
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "CSV export failed", error=str(e))
            raise
    
    def _export_warm_state_to_csv(self, file_path: Path) -> None:
        """Export warm state table to CSV"""
        try:
            if PANDAS_AVAILABLE and pd is not None:
                # Use pandas for enhanced CSV export
                with sqlite3.connect(self.db_path) as conn:
                    df = pd.read_sql_query("SELECT * FROM warm_state ORDER BY timestamp DESC", conn)
                    
                    # Parse JSON values for better readability
                    if not df.empty:
                        df['value_parsed'] = df['value'].apply(lambda x: self._safe_json_loads(x))
                        df['timestamp_readable'] = pd.to_datetime(df['timestamp'], unit='s')
                    
                    df.to_csv(file_path, index=False)
            else:
                # Fallback to manual CSV export
                self._export_table_to_csv_manual("warm_state", file_path, 
                    ['key', 'value', 'timestamp', 'category'])
                
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to export warm state", error=str(e))
            # Create empty CSV with headers
            self._create_empty_csv(file_path, ['key', 'value', 'timestamp', 'category'])
    
    def _export_cold_state_to_csv(self, file_path: Path) -> None:
        """Export cold state table to CSV"""
        try:
            if PANDAS_AVAILABLE and pd is not None:
                # Use pandas for enhanced CSV export
                with sqlite3.connect(self.db_path) as conn:
                    df = pd.read_sql_query("SELECT * FROM cold_state ORDER BY timestamp DESC", conn)
                    
                    # Parse JSON data and tags for better readability
                    if not df.empty:
                        df['data_parsed'] = df['data'].apply(lambda x: self._safe_json_loads(x))
                        df['tags_parsed'] = df['tags'].apply(lambda x: self._safe_json_loads(x))
                        df['timestamp_readable'] = pd.to_datetime(df['timestamp'], unit='s')
                    
                    df.to_csv(file_path, index=False)
            else:
                # Fallback to manual CSV export
                self._export_table_to_csv_manual("cold_state", file_path,
                    ['id', 'data', 'timestamp', 'category', 'tags'])
                
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to export cold state", error=str(e))
            # Create empty CSV with headers
            self._create_empty_csv(file_path, ['id', 'data', 'timestamp', 'category', 'tags'])
    
    def _export_positions_to_csv(self, file_path: Path) -> None:
        """Export positions table to CSV (raw format)"""
        try:
            if PANDAS_AVAILABLE and pd is not None:
                # Use pandas for enhanced CSV export
                with sqlite3.connect(self.db_path) as conn:
                    df = pd.read_sql_query("SELECT * FROM positions ORDER BY opened_at DESC", conn)
                    
                    # Add readable timestamps
                    if not df.empty:
                        df['opened_at_readable'] = pd.to_datetime(df['opened_at'], unit='s')
                        df['closed_at_readable'] = pd.to_datetime(df['closed_at'], unit='s', errors='coerce')
                        df['tags_parsed'] = df['tags'].apply(lambda x: self._safe_json_loads(x))
                    
                    df.to_csv(file_path, index=False)
            else:
                # Fallback to manual CSV export
                self._export_table_to_csv_manual("positions", file_path,
                    ['id', 'symbol', 'position_type', 'state', 'data', 'opened_at', 'closed_at', 'tags'])
                
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to export positions", error=str(e))
            # Create empty CSV with headers
            self._create_empty_csv(file_path, ['id', 'symbol', 'position_type', 'state', 'data', 
                                'opened_at', 'closed_at', 'tags'])
    
 
    
    def _export_hot_state_to_csv(self, file_path: Path) -> None:
        """Export hot state to CSV"""
        try:
            with self._lock:
                hot_state_data = []
                for key, entry in self._hot_state.items():
                    hot_state_data.append({
                        'key': key,
                        'value': json.dumps(entry['value']),
                        'timestamp': entry['timestamp'].timestamp(),
                        'timestamp_readable': entry['timestamp'].isoformat(),
                        'category': entry['category']
                    })
                
                if PANDAS_AVAILABLE and pd is not None and hot_state_data:
                    df = pd.DataFrame(hot_state_data)
                    df.to_csv(file_path, index=False)
                else:
                    # Manual CSV writing
                    with open(file_path, 'w', newline='', encoding='utf-8') as f:
                        writer = csv.DictWriter(f, fieldnames=['key', 'value', 'timestamp', 'timestamp_readable', 'category'])
                        writer.writeheader()
                        if hot_state_data:
                            writer.writerows(hot_state_data)
                
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to export hot state", error=str(e))
            # Create empty CSV with headers
            self._create_empty_csv(file_path, ['key', 'value', 'timestamp', 'timestamp_readable', 'category'])
    
    def _export_table_to_csv_manual(self, table_name: str, file_path: Path, columns: List[str]) -> None:
        """Manual CSV export fallback when pandas is not available"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY timestamp DESC")
                rows = cursor.fetchall()
                
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(columns)
                    writer.writerows(rows)
                    
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, f"Failed to manually export {table_name}", error=str(e))
            self._create_empty_csv(file_path, columns)
    
    def _create_empty_csv(self, file_path: Path, columns: List[str]) -> None:
        """Create empty CSV file with headers"""
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(columns)
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to create empty CSV", error=str(e))
            # That's it - this method should end here
        
    def _export_positions_summary_to_csv(self, file_path: Path) -> None:
        """Export flattened positions data for analysis"""
        try:
            positions = self.get_positions()
            
            if not positions:
                # Create empty CSV with headers
                self._create_empty_csv(file_path, [
                    'position_id', 'symbol', 'position_type', 'state', 'quantity',
                    'entry_price', 'current_price', 'exit_price', 'unrealized_pnl', 'realized_pnl',
                    'total_pnl', 'opened_at', 'closed_at', 'days_open', 'tags',
                    'leg_count', 'leg_details'
                ])
                return
            
            summary_data = []  # ✅ Now summary_data is defined
            
            for position in positions:
                # Flatten leg data
                leg_details = []
                for leg in position.legs:
                    leg_details.append({
                        'type': leg.option_type.value,
                        'side': leg.side.value,
                        'strike': leg.strike,
                        'expiration': leg.expiration.isoformat(),
                        'delta': leg.delta,
                        'entry_price': leg.entry_price,
                        'current_price': leg.current_price
                    })
                
                summary_data.append({
                    'position_id': position.id,
                    'symbol': position.symbol,
                    'position_type': position.position_type.value,
                    'state': position.state.value,
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': position.current_price,
                    'exit_price': position.exit_price,
                    'unrealized_pnl': position.unrealized_pnl,
                    'realized_pnl': position.realized_pnl,
                    'total_pnl': position.total_pnl,
                    'opened_at': position.opened_at.isoformat(),
                    'closed_at': position.closed_at.isoformat() if position.closed_at else None,
                    'days_open': position.days_open,
                    'tags': json.dumps(position.tags),
                    'leg_count': len(position.legs),
                    'leg_details': json.dumps(leg_details)
                })
            
            # Write to CSV
            if PANDAS_AVAILABLE and pd is not None:
                df = pd.DataFrame(summary_data)
                df.to_csv(file_path, index=False)
            else:
                # Manual CSV writing fallback
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    if summary_data:
                        writer = csv.DictWriter(f, fieldnames=summary_data[0].keys())
                        writer.writeheader()
                        writer.writerows(summary_data)
            
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to export positions summary", error=str(e))
            # Create empty CSV with headers on error
            self._create_empty_csv(file_path, [
                'position_id', 'symbol', 'position_type', 'state', 'quantity',
                'entry_price', 'current_price', 'exit_price', 'unrealized_pnl', 'realized_pnl',
                'total_pnl', 'opened_at', 'closed_at', 'days_open', 'tags',
                'leg_count', 'leg_details'
            ])
    
    def _create_export_manifest(self, file_path: Path, exported_files: Dict[str, str]) -> None:
        """Create export manifest with metadata"""
        manifest = {
            'export_timestamp': datetime.now().isoformat(),
            'export_type': 'sqlite_to_csv',
            'framework_version': FrameworkConstants.VERSION,
            'database_path': self.db_path,
            'exported_files': exported_files,
            'file_info': {}
        }
        
        # Add file size information
        for table_name, file_path_str in exported_files.items():
            if table_name != 'manifest':  # Don't include self
                try:
                    file_size = os.path.getsize(file_path_str)
                    manifest['file_info'][table_name] = {
                        'file_size_bytes': file_size,
                        'file_path': file_path_str
                    }
                except Exception:
                    pass
        
        with open(file_path, 'w') as f:
            json.dump(manifest, f, indent=2)
    
    def upload_to_s3(self, local_files: Dict[str, str], s3_prefix: Optional[str] = None) -> Dict[str, str]:
        """
        Upload CSV files to S3
        
        Args:
            local_files: Dictionary of table_name -> local_file_path
            s3_prefix: S3 key prefix (folder structure)
            
        Returns:
            Dictionary mapping table names to S3 URLs
        """
        if not self.s3_client or not self.s3_bucket:
            raise RuntimeError("S3 not configured. Call configure_s3_export() first.")
        
        if s3_prefix is None:
            s3_prefix = f"oa_framework_exports/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
        
        uploaded_files = {}
        
        try:
            for table_name, local_file_path in local_files.items():
                if not os.path.exists(local_file_path):
                    self._logger.warning(LogCategory.SYSTEM, "File not found for upload", 
                                       file=local_file_path)
                    continue
                
                # Create S3 key
                file_name = os.path.basename(local_file_path)
                s3_key = f"{s3_prefix}/{file_name}"
                
                # Upload file
                self.s3_client.upload_file(local_file_path, self.s3_bucket, s3_key)
                
                # Generate S3 URL
                s3_url = f"s3://{self.s3_bucket}/{s3_key}"
                uploaded_files[table_name] = s3_url
                
                self._logger.info(LogCategory.SYSTEM, "File uploaded to S3", 
                                table=table_name, s3_url=s3_url)
            
            return uploaded_files
            
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "S3 upload failed", error=str(e))
            raise
    
    def export_and_upload_to_s3(self, s3_prefix: Optional[str] = None, cleanup_local: bool = True) -> Dict[str, str]:
        """
        Complete workflow: Export SQLite to CSV and upload to S3
        
        Args:
            s3_prefix: S3 key prefix
            cleanup_local: Whether to delete local CSV files after upload
            
        Returns:
            Dictionary mapping table names to S3 URLs
        """
        try:
            # Export to temporary directory
            with tempfile.TemporaryDirectory(prefix="oa_s3_export_") as temp_dir:
                # Export to CSV
                exported_files = self.export_to_csv(temp_dir, include_hot_state=True)
                
                # Upload to S3
                s3_urls = self.upload_to_s3(exported_files, s3_prefix)
                
                self._logger.info(LogCategory.SYSTEM, "Export and S3 upload completed", 
                                files_count=len(s3_urls))
                
                return s3_urls
                
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Export and S3 upload failed", error=str(e))
            raise
    
    def create_compressed_export(self, export_dir: Optional[str] = None) -> str:
        """
        Create a compressed ZIP file containing all exported CSV files
        
        Args:
            export_dir: Directory to save files (creates temp dir if None)
            
        Returns:
            Path to the created ZIP file
        """
        if export_dir is None:
            export_dir = tempfile.mkdtemp(prefix="oa_compressed_export_")
        
        export_path = Path(export_dir)
        export_path.mkdir(parents=True, exist_ok=True)
        
        try:
            # Export CSV files
            exported_files = self.export_to_csv(export_dir, include_hot_state=True)
            
            # Create ZIP file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f"oa_framework_export_{timestamp}.zip"
            zip_path = export_path / zip_filename
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for table_name, file_path in exported_files.items():
                    if os.path.exists(file_path):
                        # Add file to ZIP with just the filename (no directory structure)
                        zipf.write(file_path, os.path.basename(file_path))
            
            self._logger.info(LogCategory.SYSTEM, "Compressed export created", 
                            zip_file=str(zip_path))
            
            return str(zip_path)
            
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Compressed export failed", error=str(e))
            raise
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def _safe_json_loads(self, json_str: str) -> Any:
        """Safely parse JSON string, return original string if parsing fails"""
        try:
            return json.loads(json_str)
        except (json.JSONDecodeError, TypeError):
            return json_str
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the SQLite database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count records in each table
                cursor.execute("SELECT COUNT(*) FROM warm_state")
                stats['warm_state_count'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM cold_state")
                stats['cold_state_count'] = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM positions")
                stats['positions_count'] = cursor.fetchone()[0]
                
                # Get database file size
                stats['database_size_bytes'] = os.path.getsize(self.db_path)
                stats['database_path'] = self.db_path
                
                # Get hot state count
                with self._lock:
                    stats['hot_state_count'] = len(self._hot_state)
                
                # Get date ranges
                cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM cold_state")
                cold_range = cursor.fetchone()
                if cold_range[0] and cold_range[1]:
                    stats['cold_state_date_range'] = {
                        'earliest': datetime.fromtimestamp(cold_range[0]).isoformat(),
                        'latest': datetime.fromtimestamp(cold_range[1]).isoformat()
                    }
                
                cursor.execute("SELECT MIN(opened_at), MAX(opened_at) FROM positions")
                pos_range = cursor.fetchone()
                if pos_range[0] and pos_range[1]:
                    stats['positions_date_range'] = {
                        'earliest': datetime.fromtimestamp(pos_range[0]).isoformat(),
                        'latest': datetime.fromtimestamp(pos_range[1]).isoformat()
                    }
                
                return stats
                
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Failed to get database stats", error=str(e))
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Clean up old data from the database
        
        Args:
            days_to_keep: Number of days to keep (default 90)
            
        Returns:
            Dictionary with count of deleted records per table
        """
        cutoff_timestamp = (datetime.now() - timedelta(days=days_to_keep)).timestamp()
        deleted_counts = {}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Clean up old cold state records
                cursor.execute("DELETE FROM cold_state WHERE timestamp < ?", (cutoff_timestamp,))
                deleted_counts['cold_state'] = cursor.rowcount
                
                # Clean up old warm state records (keep more recent ones)
                warm_cutoff = (datetime.now() - timedelta(days=30)).timestamp()
                cursor.execute("DELETE FROM warm_state WHERE timestamp < ?", (warm_cutoff,))
                deleted_counts['warm_state'] = cursor.rowcount
                
                # Clean up closed positions older than retention period
                cursor.execute("""
                    DELETE FROM positions 
                    WHERE state = 'closed' AND closed_at < ?
                """, (cutoff_timestamp,))
                deleted_counts['positions'] = cursor.rowcount
                
                conn.commit()
                
                self._logger.info(LogCategory.SYSTEM, "Database cleanup completed", 
                                deleted_counts=deleted_counts)
                
                return deleted_counts
                
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Database cleanup failed", error=str(e))
            return {}
    
    def backup_database(self, backup_path: str) -> bool:
        """
        Create a backup of the SQLite database
        
        Args:
            backup_path: Path for the backup file
            
        Returns:
            True if backup successful, False otherwise
        """
        try:
            # Create backup directory if it doesn't exist
            backup_dir = os.path.dirname(backup_path)
            if backup_dir:
                os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup using SQLite's backup API
            with sqlite3.connect(self.db_path) as source:
                with sqlite3.connect(backup_path) as backup:
                    source.backup(backup)
            
            self._logger.info(LogCategory.SYSTEM, "Database backup created", 
                            backup_path=backup_path)
            return True
            
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Database backup failed", 
                             backup_path=backup_path, error=str(e))
            return False
    
    def vacuum_database(self) -> bool:
        """
        Vacuum the SQLite database to reclaim space and optimize performance
        
        Returns:
            True if vacuum successful, False otherwise
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("VACUUM")
                conn.commit()
            
            self._logger.info(LogCategory.SYSTEM, "Database vacuum completed")
            return True
            
        except Exception as e:
            self._logger.error(LogCategory.SYSTEM, "Database vacuum failed", error=str(e))
            return False


# =============================================================================
# CONVENIENCE FUNCTIONS AND FACTORY METHODS
# =============================================================================

def create_state_manager(db_path: Optional[str] = None) -> StateManager:
    """
    Factory function to create a StateManager instance
    
    Args:
        db_path: Path to SQLite database file
        
    Returns:
        StateManager instance
    """
    if db_path is None:
        db_path = FrameworkConstants.DEFAULT_DATABASE_FILE
    
    return StateManager(db_path)

def create_state_manager_with_s3(db_path: Optional[str] = None, s3_bucket: Optional[str] = None, 
                                 aws_access_key: Optional[str] = None, aws_secret_key: Optional[str] = None) -> StateManager:
    """
    Factory function to create a StateManager with S3 configuration
    
    Args:
        db_path: Path to SQLite database file
        s3_bucket: S3 bucket name for exports
        aws_access_key: AWS access key ID
        aws_secret_key: AWS secret access key
        
    Returns:
        StateManager instance configured for S3 uploads
    """
    state_manager = create_state_manager(db_path)
    
    if s3_bucket:
        state_manager.configure_s3_export(
            bucket_name=s3_bucket,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
    
    return state_manager

# =============================================================================
# SAFE JSON SERIALIZATION FUNCTIONS
# =============================================================================

def safe_json_dumps(obj, **kwargs):
    """Safely serialize objects to JSON, handling enums and other framework types"""
    return json.dumps(obj, cls=FrameworkJSONEncoder, **kwargs)

def prepare_for_json_storage(data):
    """Prepare data for JSON storage by converting enums to values"""
    if isinstance(data, dict):
        return {key: prepare_for_json_storage(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [prepare_for_json_storage(item) for item in data]
    elif isinstance(data, Enum):
        return data.value
    elif isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, set):
        return list(data)
    else:
        return data
    
# =============================================================================
# EXAMPLE USAGE AND TESTING
# =============================================================================

def demonstrate_csv_export():
    """Demonstrate CSV export functionality"""
    
    print("=" * 60)
    print("StateManager CSV Export Demonstration")
    print("=" * 60)
    
    try:
        # Create state manager
        state_manager = create_state_manager("demo_state.db")
        
        # Add some test data
        print("\n1. Adding test data...")
        
        # Hot state
        state_manager.set_hot_state("current_price_SPY", 450.25)
        state_manager.set_hot_state("market_regime", "bull_market")
        
        # Warm state
        state_manager.set_warm_state("daily_pnl", {"total": 1250.50, "trades": 5})
        state_manager.set_warm_state("bot_status", {"active": True, "last_scan": datetime.now().isoformat()})
        
        # Cold state
        trade_data = {
            "symbol": "SPY",
            "strategy": "iron_condor",
            "entry_price": 2.50,
            "exit_price": 1.25,
            "pnl": 125.0
        }
        state_manager.store_cold_state(trade_data, "completed_trades", ["profitable", "spy"])
        
        print("✓ Test data added successfully")
        
        # Get database statistics
        print("\n2. Database Statistics:")
        stats = state_manager.get_database_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Export to CSV
        print("\n3. Exporting to CSV...")
        export_dir = "csv_export_demo"
        exported_files = state_manager.export_to_csv(export_dir, include_hot_state=True)
        
        print("✓ CSV export completed")
        print("   Exported files:")
        for table_name, file_path in exported_files.items():
            file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
            print(f"     {table_name}: {file_path} ({file_size} bytes)")
        
        # Create compressed export
        print("\n4. Creating compressed export...")
        zip_file = state_manager.create_compressed_export("compressed_export_demo")
        zip_size = os.path.getsize(zip_file)
        print(f"✓ Compressed export created: {zip_file} ({zip_size} bytes)")
        
        # Demonstrate S3 configuration (without actual upload)
        print("\n5. S3 Configuration Demo...")
        print("   To configure S3:")
        print("   state_manager.configure_s3_export('my-bucket', 'access-key', 'secret-key')")
        print("   s3_urls = state_manager.export_and_upload_to_s3()")
        
        print("\n" + "=" * 60)
        print("CSV Export Demo Complete ✓")
        print("✓ SQLite performance for backtesting")
        print("✓ CSV export for S3 uploads and analysis")
        print("✓ Compressed exports for efficient storage")
        print("=" * 60)
        
    except Exception as e:
        print(f"✗ Demo failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    demonstrate_csv_export()