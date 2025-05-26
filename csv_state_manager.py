# Option Alpha Framework - Complete CSV State Manager
# Main state manager that coordinates all CSV modules

import json
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import uuid

# Import our CSV handler modules
from s3_uploader import S3Uploader, create_s3_uploader
from position_csv_handler import PositionCSVHandler
from analytics_csv_handler import AnalyticsCSVHandler

# Framework imports
try:
    # Import framework components with fixed imports
    from oa_constants import FrameworkConstants, SystemDefaults
    from oa_enums import LogLevel, LogCategory, PositionState
except ImportError:
    # Fallback if framework enums not available
    class FrameworkConstants:
        VERSION = "1.0.0"

class CSVStateManager:
    """
    Complete CSV-based state management system that coordinates all modules:
    - Hot State: In-memory for real-time decisions
    - Warm State: CSV files for session data  
    - Cold State: CSV files for historical data
    - Position Management: Dedicated position handler
    - Analytics: Performance metrics and reporting
    - S3 Upload: Optional cloud backup functionality
    """
    
    def __init__(self, data_dir: str = "backtest_data", s3_bucket: Optional[str] = None, s3_prefix: str = "backtests"):
        self.data_dir = Path(data_dir)
        self.s3_bucket = s3_bucket
        self.s3_prefix = s3_prefix
        self._hot_state: Dict[str, Any] = {}
        self._lock = threading.Lock()
        self._logger = self._setup_logger()
        self._backtest_id = str(uuid.uuid4())
        self._backtest_start_time = datetime.now()
        
        # Initialize directory structure
        self._init_directory_structure()
        
        # Initialize module handlers
        self.s3_uploader = create_s3_uploader(s3_bucket, s3_prefix)
        self.position_handler = PositionCSVHandler(self.data_dir)
        self.analytics_handler = AnalyticsCSVHandler(self.data_dir)
        
        self._logger.info(f"CSV State Manager initialized with backtest ID: {self._backtest_id}")
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for state manager"""
        logger = logging.getLogger(f"{__name__}.CSVStateManager")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _init_directory_structure(self) -> None:
        """Initialize directory structure for CSV files"""
        try:
            # Create main data directory
            self.data_dir.mkdir(parents=True, exist_ok=True)
            
            # Create subdirectories for different data types
            directories = ["warm_state", "cold_state", "positions", "trades", "analytics", "logs"]
            for directory in directories:
                (self.data_dir / directory).mkdir(exist_ok=True)
            
            # Create metadata file
            metadata = {
                'backtest_id': self._backtest_id,
                'start_time': self._backtest_start_time.isoformat(),
                'framework_version': getattr(FrameworkConstants, 'VERSION', '1.0.0'),
                's3_bucket': self.s3_bucket,
                's3_prefix': self.s3_prefix
            }
            
            with open(self.data_dir / "metadata.json", 'w') as f:
                json.dump(metadata, f, indent=2)
            
            self._logger.info(f"Directory structure initialized: {self.data_dir}")
            
        except Exception as e:
            self._logger.error(f"Failed to initialize directory structure: {e}")
            raise
    
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
    # WARM AND COLD STATE METHODS (CSV Files)
    # =============================================================================
    
    def set_warm_state(self, key: str, value: Any, category: str = 'session') -> None:
        """Set warm state value (CSV file)"""
        try:
            import csv
            
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
            import csv
            
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
    
    def store_cold_state(self, data: Dict[str, Any], category: str, tags: Optional[List[str]] = None) -> str:
        """Store cold state data (historical CSV)"""
        record_id = str(uuid.uuid4())
        tags_list = tags if tags is not None else []
        tags_str = json.dumps(tags_list)
        
        try:
            import csv
            
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
            import csv
            
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
    # POSITION MANAGEMENT (Delegated to PositionCSVHandler)
    # =============================================================================
    
    def store_position(self, position_data: Dict[str, Any]) -> None:
        """Store position using position handler"""
        self.position_handler.store_position(position_data)
    
    def get_positions(self, state: Optional[str] = None, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get positions using position handler"""
        return self.position_handler.get_positions(state, symbol)
    
    def get_position_by_id(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get specific position by ID"""
        return self.position_handler.get_position_by_id(position_id)
    
    def update_position(self, position_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing position"""
        return self.position_handler.update_position(position_id, updates)
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        return self.position_handler.get_open_positions()
    
    def get_position_summary(self) -> Dict[str, Any]:
        """Get position summary statistics"""
        return self.position_handler.get_position_summary()
    
    # =============================================================================
    # TRADE LOGGING
    # =============================================================================
    
    def log_trade(self, trade_data: Dict[str, Any]) -> None:
        """Log trade execution to CSV"""
        try:
            import csv
            
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
    
    def log_framework_event(self, event_type: str, message: str, **kwargs) -> None:
        """Log framework events to CSV"""
        try:
            import csv
            
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
    # ANALYTICS (Delegated to AnalyticsCSVHandler)
    # =============================================================================
    
    def store_performance_metrics(self, metrics: Dict[str, Any], timestamp: Optional[datetime] = None) -> None:
        """Store performance metrics using analytics handler"""
        self.analytics_handler.store_performance_metrics(metrics, timestamp)
    
    def store_trade_analytics(self, trade_data: Dict[str, Any]) -> None:
        """Store trade analytics using analytics handler"""
        self.analytics_handler.store_trade_analytics(trade_data)
    
    def calculate_performance_metrics(self, use_advanced: bool = True) -> Dict[str, Any]:
        """Calculate performance metrics using analytics handler"""
        if use_advanced:
            return self.analytics_handler.calculate_advanced_metrics()
        else:
            return self.analytics_handler.calculate_basic_metrics()
    
    def generate_performance_report(self, output_file: Optional[Path] = None) -> Path:
        """Generate performance report using analytics handler"""
        return self.analytics_handler.generate_performance_report(output_file)
    
    def store_market_conditions(self, conditions: Dict[str, Any], timestamp: Optional[datetime] = None) -> None:
        """Store market conditions using analytics handler"""
        self.analytics_handler.store_market_conditions(conditions, timestamp)
    
    # =============================================================================
    # S3 UPLOAD (Delegated to S3Uploader)
    # =============================================================================
    
    def upload_to_s3(self, include_patterns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Upload all data to S3 using S3 uploader"""
        if not self.s3_uploader.is_available():
            return {
                'success': False,
                'error': 'S3 uploader not available',
                'uploaded_files': 0,
                'total_size_mb': 0
            }
        
        return self.s3_uploader.upload_directory(self.data_dir, self._backtest_id, include_patterns)
    
    # =============================================================================
    # BACKTEST LIFECYCLE MANAGEMENT
    # =============================================================================
    
    def generate_backtest_summary(self) -> Dict[str, Any]:
        """Generate comprehensive backtest summary"""
        try:
            # Get basic file statistics
            summary = {
                'backtest_id': self._backtest_id,
                'start_time': self._backtest_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'duration_minutes': (datetime.now() - self._backtest_start_time).total_seconds() / 60,
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
            
            # Add position statistics
            position_summary = self.get_position_summary()
            summary['statistics']['positions'] = position_summary
            
            # Add performance metrics
            try:
                performance_metrics = self.calculate_performance_metrics()
                summary['statistics']['performance'] = performance_metrics
            except Exception as e:
                summary['statistics']['performance'] = {'error': str(e)}
            
            return summary
            
        except Exception as e:
            self._logger.error(f"Failed to generate backtest summary: {e}")
            return {'error': str(e)}
    
    def finalize_backtest(self, upload_to_s3: bool = True, generate_report: bool = True) -> Dict[str, Any]:
        """
        Finalize backtest by generating reports and optionally uploading to S3.
        Call this at the end of your backtest.
        
        Args:
            upload_to_s3: Whether to upload results to S3
            generate_report: Whether to generate performance report
        
        Returns:
            Dictionary with finalization results
        """
        try:
            self._logger.info(f"Finalizing backtest: {self._backtest_id}")
            
            # Generate summary
            summary = self.generate_backtest_summary()
            
            # Save summary to file
            summary_file = self.data_dir / "backtest_summary.json"
            with open(summary_file, 'w') as f:
                json.dump(summary, f, indent=2, default=str)
            
            result = {
                'backtest_id': self._backtest_id,
                'summary': summary,
                'local_path': str(self.data_dir),
                'performance_report': None,
                's3_uploaded': False,
                's3_location': None
            }
            
            # Generate performance report if requested
            if generate_report:
                try:
                    report_file = self.generate_performance_report()
                    result['performance_report'] = str(report_file)
                    self._logger.info(f"Performance report generated: {report_file}")
                except Exception as e:
                    self._logger.error(f"Failed to generate performance report: {e}")
                    result['performance_report_error'] = str(e)
            
            # Upload to S3 if requested and available
            if upload_to_s3 and self.s3_uploader.is_available():
                upload_result = self.upload_to_s3()
                result['s3_uploaded'] = upload_result.get('success', False)
                result['s3_location'] = upload_result.get('s3_location')
                result['s3_upload_details'] = upload_result
                
                # Create upload manifest
                if upload_result.get('success'):
                    try:
                        manifest_file = self.s3_uploader.create_upload_manifest(upload_result, self.data_dir)
                        result['upload_manifest'] = str(manifest_file)
                    except Exception as e:
                        self._logger.error(f"Failed to create upload manifest: {e}")
            
            self._logger.info(f"Backtest finalized successfully: {self._backtest_id}")
            return result
            
        except Exception as e:
            self._logger.error(f"Failed to finalize backtest: {e}")
            return {
                'backtest_id': self._backtest_id,
                'error': str(e),
                'local_path': str(self.data_dir)
            }
    
    # =============================================================================
    # UTILITY METHODS
    # =============================================================================
    
    def get_backtest_metadata(self) -> Dict[str, Any]:
        """Get backtest metadata"""
        return {
            'backtest_id': self._backtest_id,
            'start_time': self._backtest_start_time,
            'data_dir': str(self.data_dir),
            's3_bucket': self.s3_bucket,
            's3_available': self.s3_uploader.is_available(),
            'framework_version': getattr(FrameworkConstants, 'VERSION', '1.0.0')
        }
    
    def cleanup_old_data(self, days_to_keep: int = 30) -> Dict[str, Any]:
        """
        Clean up old data files to save space.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Dictionary with cleanup results
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            files_removed = 0
            space_freed = 0
            
            # Only clean up specific directories, not the current backtest
            cleanup_dirs = ['cold_state', 'logs']
            
            for dir_name in cleanup_dirs:
                dir_path = self.data_dir / dir_name
                if dir_path.exists():
                    for file_path in dir_path.glob('*.csv'):
                        if file_path.stat().st_mtime < cutoff_date.timestamp():
                            file_size = file_path.stat().st_size
                            file_path.unlink()
                            files_removed += 1
                            space_freed += file_size
            
            space_freed_mb = space_freed / 1024 / 1024
            
            self._logger.info(f"Cleanup completed: {files_removed} files, {space_freed_mb:.2f} MB freed")
            
            return {
                'files_removed': files_removed,
                'space_freed_mb': space_freed_mb,
                'cutoff_date': cutoff_date.isoformat()
            }
            
        except Exception as e:
            self._logger.error(f"Failed to cleanup old data: {e}")
            return {'error': str(e)}


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_csv_state_manager(data_dir: str = "backtest_data", 
                            s3_bucket: Optional[str] = None, 
                            s3_prefix: str = "backtests") -> CSVStateManager:
    """
    Factory function to create CSV state manager with error handling.
    
    Args:
        data_dir: Directory for storing CSV files
        s3_bucket: Optional S3 bucket for uploads
        s3_prefix: S3 key prefix for uploads
        
    Returns:
        Configured CSVStateManager instance
    """
    try:
        return CSVStateManager(data_dir, s3_bucket, s3_prefix)
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create CSV state manager: {e}")
        raise


# =============================================================================
# USAGE EXAMPLE
# =============================================================================

if __name__ == "__main__":
    def demonstrate_csv_state_manager():
        """Demonstrate the complete CSV state manager functionality"""
        
        print("Complete CSV State Manager - Demonstration")
        print("=" * 60)
        
        # Initialize state manager
        state_manager = create_csv_state_manager(
            data_dir="demo_backtest_data",
            s3_bucket=None,  # Set to your bucket name for S3 testing
            s3_prefix="oa_framework_demos"
        )
        
        print(f"✓ Initialized CSV State Manager")
        print(f"  Data Directory: {state_manager.data_dir}")
        print(f"  Backtest ID: {state_manager._backtest_id}")
        print(f"  S3 Available: {state_manager.s3_uploader.is_available()}")
        
        # Test hot state
        state_manager.set_hot_state("current_prices", {"SPY": 450.25, "QQQ": 380.15})
        prices = state_manager.get_hot_state("current_prices")
        print(f"✓ Hot State: {prices}")
        
        # Test warm state
        state_manager.set_warm_state("bot_config", {"name": "Demo Bot", "capital": 10000})
        config = state_manager.get_warm_state("bot_config")
        print(f"✓ Warm State: {config}")
        
        # Test position management
        position_data = {
            'id': 'pos_001',
            'symbol': 'SPY',
            'position_type': 'long_call',
            'state': 'open',
            'quantity': 1,
            'entry_price': 450.0,
            'current_price': 455.0,
            'unrealized_pnl': 50.0,
            'tags': ['demo', 'profitable']
        }
        state_manager.store_position(position_data)
        print("✓ Position Stored")
        
        # Test trade logging
        state_manager.log_trade({
            'symbol': 'SPY',
            'action': 'OPEN',
            'position_type': 'long_call',
            'quantity': 1,
            'price': 450.0,
            'pnl': 0.0,
            'bot_name': 'Demo Bot'
        })
        print("✓ Trade Logged")
        
        # Test analytics
        state_manager.store_performance_metrics({
            'total_return': 5.5,
            'win_rate': 0.75,
            'total_trades': 4
        })
        print("✓ Performance Metrics Stored")
        
        # Generate summary
        summary = state_manager.generate_backtest_summary()
        print(f"✓ Backtest Summary Generated")
        print(f"  Total Files: {sum(cat['file_count'] for cat in summary['data_files'].values())}")
        
        # Finalize backtest
        result = state_manager.finalize_backtest(upload_to_s3=False)
        print(f"✓ Backtest Finalized")
        print(f"  Local Path: {result['local_path']}")
        if result.get('performance_report'):
            print(f"  Performance Report: {result['performance_report']}")
        
        print("\n" + "=" * 60)
        print("CSV State Manager Demonstration Complete!")
    
    demonstrate_csv_state_manager()