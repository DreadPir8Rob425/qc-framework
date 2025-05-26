# Option Alpha Framework - CSV-based State Manager with S3 Upload
# Modified to use CSV files instead of SQLite and upload to S3 after backtest

import csv
import json
import os
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import uuid
import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import pandas as pd
from pathlib import Path

# Import framework components
from oa_framework_enums import *

class CSVStateManager:
    """
    CSV-based state management system with S3 upload capability:
    - Hot State: In-memory for real-time decisions
    - Warm State: CSV files for session data  
    - Cold State: CSV files for historical data
    - S3 Upload: Copies all CSV files to S3 bucket after backtest
    """
    
    def __init__(self, data_dir: str = "backtest_data", s3_bucket: str = None, s3_prefix: str = "backtests"):
        self.data_dir = Path(data_dir)
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self._hot_state: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._logger = self._setup_logger()
        self._backtest_id = str(uuid.uuid4())
        self._backtest_start_time = datetime.now()
        
        # Create data directory structure
        self._init_directory_structure()
        
        # Initialize S3 client if bucket specified
        self._s3_client = None
        if s3_bucket:
            self._init_s3_client()
    
    def _setup_logger(self):
        """Setup logger for state manager"""
        import logging
        logger = logging.getLogger(f"{__name__}.CSVStateManager")
        return logger
    
    def _init_directory_structure(self):
        """Initialize directory structure for CSV files"""
        try:
            # Create main data directory
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for different data types
            (self.data_dir / "warm_state").mkdir(exist_ok=True)
            (self.data_dir / "cold_state").mkdir(exist_ok=True)
            (self.data_dir / "positions").mkdir(exist_ok=True)
            (self.data_dir / "trades").mkdir(exist_ok=True)
            (self.data_dir / "analytics").mkdir(exist_ok=True)
            (self.data_dir / "logs").mkdir(exist_ok=True)
            
            # Create metadata file
            metadata = {
                'backtest_id': self._backtest_id,
                'start_time': self._backtest_start_time.isoformat(),
                'framework_version': FrameworkConstants.VERSION,
                's3_bucket': self.s3_bucket,
                's3_prefix': self.s3_prefix
            }
            
            with open(self.data_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self._logger.info(f"CSV state management initialized: {self.data_dir}")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize directory structure: {e}")
            raise
    
    def _init_s3_client(self):
        """Initialize S3 client for uploading results"""
        try:
            self._s3_client = boto3.client('s3')
            # Test connection
            self._s3_client.head_bucket(Bucket=self.s3_bucket)
            self._logger.info(f"S3 client initialized for bucket: {self.s3_bucket}")
        except NoCredentialsError:
            self._logger.error("AWS credentials not found. S3 upload will be disabled.")
            self._s3_client = None
        except ClientError as e:
            self._logger.error(f"Failed to initialize S3 client: {e}")
            self._s3_client = None
        except Exception as e:
            self._logger.error(f"Unexpected error initializing S3: {e}")
            self._s3_client = None
    
    # =============================================================================
    # HOT STATE METHODS (In-Memory)
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
    
    # =============================================================================
    # WARM STATE METHODS (CSV Session Data)
    # =============================================================================
    
    def set_warm_state(self, key: str, value: Any, category: str = 'session') -> None:
        """Set warm state value (CSV file)"""
        try:
            # Prepare data for CSV
            data_row = {
                'key': key,
                'value': json.dumps(value) if not isinstance(value, (str, int, float)) else str(value),
                'timestamp': datetime.now().isoformat(),
                'category': category
            }
            
            # Write to CSV file
            csv_file = self.data_dir / "warm_state" / f"{category}_state.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['key', 'value', 'timestamp', 'category'])
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data_row)
            
        except Exception as e:
            self._logger.error(f"Failed to set warm state: {e}")
    
    def get_warm_state(self, key: str, default: Any = None, category: str = 'session') -> Any:
        """Get warm state value from CSV"""
        try:
            csv_file = self.data_dir / "warm_state" / f"{category}_state.csv"
            if not csv_file.exists():
                return default
            
            # Read CSV and find the most recent entry for the key
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                latest_entry = None
                
                for row in reader:
                    if row['key'] == key:
                        latest_entry = row
                
                if latest_entry:
                    try:
                        # Try to parse as JSON first
                        return json.loads(latest_entry['value'])
                    except json.JSONDecodeError:
                        # Return as string if not valid JSON
                        return latest_entry['value']
                
                return default
                
        except Exception as e:
            self._logger.error(f"Failed to get warm state: {e}")
            return default
    
    # =============================================================================
    # COLD STATE METHODS (CSV Historical Data)
    # =============================================================================
    
    def store_cold_state(self, data: Dict[str, Any], category: str, tags: List[str] = None) -> str:
        """Store cold state data (historical CSV)"""
        record_id = str(uuid.uuid4())
        tags_str = json.dumps(tags or [])
        
        try:
            # Prepare data for CSV
            data_row = {
                'id': record_id,
                'data': json.dumps(data),
                'timestamp': datetime.now().isoformat(),
                'category': category,
                'tags': tags_str
            }
            
            # Write to category-specific CSV file
            csv_file = self.data_dir / "cold_state" / f"{category}.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['id', 'data', 'timestamp', 'category', 'tags'])
                if not file_exists:
                    writer.writeheader()
                writer.writerow(data_row)
            
            return record_id
            
        except Exception as e:
            self._logger.error(f"Failed to store cold state: {e}")
            raise
    
    def get_cold_state(self, category: str, limit: int = 100, 
                       start_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get cold state data by category from CSV"""
        try:
            csv_file = self.data_dir / "cold_state" / f"{category}.csv"
            if not csv_file.exists():
                return []
            
            results = []
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    record_time = datetime.fromisoformat(row['timestamp'])
                    
                    # Apply date filter if specified
                    if start_date and record_time < start_date:
                        continue
                    
                    results.append({
                        'id': row['id'],
                        'data': json.loads(row['data']),
                        'timestamp': record_time,
                        'tags': json.loads(row['tags'])
                    })
            
            # Sort by timestamp (newest first) and apply limit
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            self._logger.error(f"Failed to get cold state: {e}")
            return []
    
    # =============================================================================
    # POSITION MANAGEMENT (CSV)
    # =============================================================================
    
    def store_position(self, position) -> None:
        """Store position in CSV file"""
        try:
            # Prepare position data for CSV
            position_data = {
                'id': position.id,
                'symbol': position.symbol,
                'position_type': position.position_type.value,
                'state': position.state.value,
                'quantity': position.quantity,
                'entry_price': position.entry_price,
                'current_price': position.current_price,
                'unrealized_pnl': position.unrealized_pnl,
                'realized_pnl': position.realized_pnl,
                'opened_at': position.opened_at.isoformat(),
                'closed_at': position.closed_at.isoformat() if position.closed_at else '',
                'tags': json.dumps(position.tags),
                'legs': json.dumps([
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
                ])
            }
            
            # Write to positions CSV
            csv_file = self.data_dir / "positions" / "positions.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=position_data.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(position_data)
            
            self._logger.info(f"Position stored: {position.id}")
            
        except Exception as e:
            self._logger.error(f"Failed to store position: {e}")
            raise
    
    def get_positions(self, state=None, symbol: Optional[str] = None) -> List:
        """Get positions from CSV with optional filters"""
        try:
            csv_file = self.data_dir / "positions" / "positions.csv"
            if not csv_file.exists():
                return []
            
            positions = []
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Apply filters
                    if state and row['state'] != state.value:
                        continue
                    if symbol and row['symbol'] != symbol:
                        continue
                    
                    # Reconstruct position object (simplified for demo)
                    # In practice, you'd import and reconstruct the full Position object
                    positions.append({
                        'id': row['id'],
                        'symbol': row['symbol'],
                        'position_type': row['position_type'],
                        'state': row['state'],
                        'quantity': int(row['quantity']),
                        'entry_price': float(row['entry_price']),
                        'current_price': float(row['current_price']),
                        'unrealized_pnl': float(row['unrealized_pnl']),
                        'realized_pnl': float(row['realized_pnl']),
                        'opened_at': datetime.fromisoformat(row['opened_at']),
                        'closed_at': datetime.fromisoformat(row['closed_at']) if row['closed_at'] else None,
                        'tags': json.loads(row['tags']),
                        'legs': json.loads(row['legs'])
                    })
            
            return positions
            
        except Exception as e:
            self._logger.error(f"Failed to get positions: {e}")
            return []
    
    # =============================================================================
    # TRADE LOGGING (CSV)
    # =============================================================================
    
    def log_trade(self, trade_data: Dict[str, Any]) -> None:
        """Log trade execution to CSV"""
        try:
            # Ensure trade has required fields
            trade_record = {
                'trade_id': trade_data.get('trade_id', str(uuid.uuid4())),
                'timestamp': datetime.now().isoformat(),
                'symbol': trade_data.get('symbol', ''),
                'action': trade_data.get('action', ''),  # OPEN/CLOSE
                'position_type': trade_data.get('position_type', ''),
                'quantity': trade_data.get('quantity', 0),
                'price': trade_data.get('price', 0.0),
                'fees': trade_data.get('fees', 0.0),
                'pnl': trade_data.get('pnl', 0.0),
                'bot_name': trade_data.get('bot_name', ''),
                'automation': trade_data.get('automation', ''),
                'additional_data': json.dumps(trade_data.get('additional_data', {}))
            }
            
            # Write to trades CSV
            csv_file = self.data_dir / "trades" / "trades.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=trade_record.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(trade_record)
                
        except Exception as e:
            self._logger.error(f"Failed to log trade: {e}")
    
    # =============================================================================
    # ANALYTICS AND METRICS (CSV)
    # =============================================================================
    
    def store_analytics(self, analytics_data: Dict[str, Any], category: str = "performance") -> None:
        """Store analytics data to CSV"""
        try:
            # Prepare analytics record
            analytics_record = {
                'timestamp': datetime.now().isoformat(),
                'category': category,
                'data': json.dumps(analytics_data)
            }
            
            # Write to analytics CSV
            csv_file = self.data_dir / "analytics" / f"{category}.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=analytics_record.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(analytics_record)
                
        except Exception as e:
            self._logger.error(f"Failed to store analytics: {e}")
    
    def log_framework_event(self, event_type: str, message: str, **kwargs) -> None:
        """Log framework events to CSV"""
        try:
            log_record = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'message': message,
                'data': json.dumps(kwargs)
            }
            
            csv_file = self.data_dir / "logs" / "framework_events.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=log_record.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(log_record)
                
        except Exception as e:
            self._logger.error(f"Failed to log framework event: {e}")
    
    # =============================================================================
    # S3 UPLOAD FUNCTIONALITY
    # =============================================================================
    
    def upload_to_s3(self, include_patterns: List[str] = None) -> bool:
        """
        Upload all CSV files and data to S3 bucket after backtest completion.
        
        Args:
            include_patterns: List of file patterns to include (e.g., ['*.csv', '*.json'])
                            If None, uploads all files
        
        Returns:
            True if successful, False otherwise
        """
        if not self._s3_client or not self.s3_bucket:
            self._logger.warning("S3 client not initialized or no bucket specified")
            return False
        
        try:
            # Update metadata with end time
            metadata_file = self.data_dir / "metadata.json"
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            
            metadata['end_time'] = datetime.now().isoformat()
            metadata['duration_minutes'] = (datetime.now() - self._backtest_start_time).total_seconds() / 60
            
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Create S3 key prefix with timestamp and backtest ID
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            s3_key_prefix = f"{self.s3_prefix}/{timestamp}_{self._backtest_id}"
            
            uploaded_files = 0
            total_size = 0
            
            # Walk through all files in data directory
            for file_path in self.data_dir.rglob('*'):
                if file_path.is_file():
                    # Apply include patterns if specified
                    if include_patterns:
                        if not any(file_path.match(pattern) for pattern in include_patterns):
                            continue
                    
                    # Calculate relative path for S3 key
                    relative_path = file_path.relative_to(self.data_dir)
                    s3_key = f"{s3_key_prefix}/{relative_path}"
                    
                    # Upload file
                    try:
                        file_size = file_path.stat().st_size
                        self._s3_client.upload_file(
                            str(file_path), 
                            self.s3_bucket, 
                            s3_key
                        )
                        
                        uploaded_files += 1
                        total_size += file_size
                        
                        self._logger.info(f"Uploaded: {relative_path} -> s3://{self.s3_bucket}/{s3_key}")
                        
                    except Exception as e:
                        self._logger.error(f"Failed to upload {file_path}: {e}")
                        continue
            
            # Log upload summary
            self._logger.info(f"S3 Upload completed: {uploaded_files} files, {total_size/1024/1024:.2f} MB")
            self._logger.info(f"S3 Location: s3://{self.s3_bucket}/{s3_key_prefix}/")
            
            # Store upload info in metadata
            upload_info = {
                'uploaded_files': uploaded_files,
                'total_size_mb': total_size / 1024 / 1024,
                's3_location': f"s3://{self.s3_bucket}/{s3_key_prefix}/",
                'upload_time': datetime.now().isoformat()
            }
            
            # Update metadata with upload info
            metadata['s3_upload'] = upload_info
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Upload updated metadata
            s3_metadata_key = f"{s3_key_prefix}/metadata.json"
            self._s3_client.upload_file(str(metadata_file), self.s3_bucket, s3_metadata_key)
            
            return True
            
        except Exception as e:
            self._logger.error(f"S3 upload failed: {e}")
            return False
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate a summary report of the backtest data"""
        try:
            summary = {
                'backtest_id': self._backtest_id,
                'start_time': self._backtest_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'data_files': {},
                'statistics': {}
            }
            
            # Count files and records in each category
            for category_dir in ['warm_state', 'cold_state', 'positions', 'trades', 'analytics', 'logs']:
                cat_path = self.data_dir / category_dir
                if cat_path.exists():
                    files = list(cat_path.glob('*.csv'))
                    summary['data_files'][category_dir] = {
                        'file_count': len(files),
                        'files': [f.name for f in files]
                    }
                    
                    # Count total records across all CSV files in category
                    total_records = 0
                    for csv_file in files:
                        try:
                            with open(csv_file, 'r') as f:
                                total_records += sum(1 for line in f) - 1  # Subtract header
                        except:
                            pass
                    
                    summary['data_files'][category_dir]['total_records'] = total_records
            
            # Generate basic statistics
            if (self.data_dir / "positions" / "positions.csv").exists():
                positions_df = pd.read_csv(self.data_dir / "positions" / "positions.csv")
                summary['statistics']['positions'] = {
                    'total_positions': len(positions_df),
                    'open_positions': len(positions_df[positions_df['state'] == 'open']),
                    'closed_positions': len(positions_df[positions_df['state'] == 'closed']),
                    'total_pnl': positions_df['realized_pnl'].sum() + positions_df['unrealized_pnl'].sum()
                }
            
            if (self.data_dir / "trades" / "trades.csv").exists():
                trades_df = pd.read_csv(self.data_dir / "trades" / "trades.csv")
                summary['statistics']['trades'] = {
                    'total_trades': len(trades_df),
                    'total_pnl': trades_df['pnl'].sum(),
                    'total_fees': trades_df['fees'].sum(),
                    'symbols_traded': trades_df['symbol'].nunique()
                }
            
            return summary
            
        except Exception as e:
            self._logger.error(f"Failed to generate summary report: {e}")
            return {'error': str(e)}
    
    def finalize_backtest(self, upload_to_s3: bool = True) -> Dict[str, Any]:
        """
        Finalize backtest by generating reports and optionally uploading to S3.
        Call this at the end of your backtest.
        
        Returns:
            Dictionary with summary information and S3 upload status
        """
        try:
            # Generate summary report
            summary = self.generate_summary_report()
            
            # Save summary report to file
            summary_file = self.data_dir / "backtest_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2)
            
            result = {
                'backtest_id': self._backtest_id,
                'summary': summary,
                'local_path': str(self.data_dir),
                's3_uploaded': False,
                's3_location': None
            }
            
            # Upload to S3 if requested and configured
            if upload_to_s3 and self.s3_bucket:
                success = self.upload_to_s3()
                result['s3_uploaded'] = success
                if success:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    result['s3_location'] = f"s3://{self.s3_bucket}/{self.s3_prefix}/{timestamp}_{self._backtest_id}/"
            
            self._logger.info(f"Backtest finalized: {self._backtest_id}")
            return result
            
        except Exception as e:
            self._logger.error(f"Failed to finalize backtest: {e}")
            return {'error': str(e)}


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

def demonstrate_csv_state_manager():
    """Demonstrate the CSV-based state manager functionality"""
    
    print("CSV State Manager with S3 Upload - Demonstration")
    print("=" * 60)
    
    # Initialize with S3 bucket (optional)
    state_manager = CSVStateManager(
        data_dir="demo_backtest_data",
        s3_bucket="your-backtest-results-bucket",  # Replace with your bucket
        s3_prefix="oa_framework_backtests"
    )
    
    print(f"✓ Initialized CSV State Manager")
    print(f"  Data Directory: {state_manager.data_dir}")
    print(f"  Backtest ID: {state_manager._backtest_id}")
    
    # Test hot state
    state_manager.set_hot_state("current_price", {"SPY": 450.25, "QQQ": 380.15})
    price_data = state_manager.get_hot_state("current_price")
    print(f"✓ Hot State Test: {price_data}")
    
    # Test warm state
    state_manager.set_warm_state("bot_config", {"name": "Test Bot", "capital": 10000})
    config_data = state_manager.get_warm_state("bot_config")
    print(f"✓ Warm State Test: {config_data}")
    
    # Test cold state
    trade_data = {"symbol": "SPY", "action": "BUY", "quantity": 100, "price": 450.0}
    record_id = state_manager.store_cold_state(trade_data, "trades", ["profitable", "spy"])
    print(f"✓ Cold State Test: Record ID {record_id}")
    
    # Test trade logging
    state_manager.log_trade({
        'symbol': 'SPY',
        'action': 'OPEN',
        'position_type': 'long_call',
        'quantity': 1,
        'price': 450.0,
        'bot_name': 'Demo Bot'
    })
    print("✓ Trade Logged")
    
    # Test analytics storage
    state_manager.store_analytics({
        'total_return': 15.5,
        'sharpe_ratio': 1.2,
        'max_drawdown': -5.2
    }, "performance")
    print("✓ Analytics Stored")
    
    # Generate summary
    summary = state_manager.generate_summary_report()
    print(f"✓ Summary Generated: {len(summary)} sections")
    
    # Finalize backtest (this will upload to S3 if configured)
    result = state_manager.finalize_backtest(upload_to_s3=True)
    print(f"✓ Backtest Finalized")
    print(f"  S3 Uploaded: {result['s3_uploaded']}")
    if result.get('s3_location'):
        print(f"  S3 Location: {result['s3_location']}")
    
    print("\n" + "=" * 60)
    print("CSV State Manager Demonstration Complete!")

if __name__ == "__main__":
    demonstrate_csv_state_manager()