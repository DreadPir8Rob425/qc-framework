# Option Alpha Framework - Analytics CSV Handler
# Separate module for analytics and performance reporting

import csv
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import math

# Optional pandas import for advanced analytics
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class AnalyticsCSVHandler:
    """
    Handles analytics storage and performance calculation using CSV files.
    Provides both basic (no dependencies) and advanced (pandas) analytics.
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.analytics_dir = data_dir / "analytics"
        self.analytics_dir.mkdir(exist_ok=True)
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for analytics handler"""
        logger = logging.getLogger(f"{__name__}.AnalyticsCSVHandler")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def store_performance_metrics(self, metrics: Dict[str, Any], timestamp: Optional[datetime] = None) -> None:
        """
        Store performance metrics to CSV.
        
        Args:
            metrics: Dictionary of performance metrics
            timestamp: Optional timestamp (defaults to now)
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Prepare metrics record
            metrics_record = {
                'timestamp': timestamp.isoformat(),
                'total_return': metrics.get('total_return', 0.0),
                'total_pnl': metrics.get('total_pnl', 0.0),
                'realized_pnl': metrics.get('realized_pnl', 0.0),
                'unrealized_pnl': metrics.get('unrealized_pnl', 0.0),
                'win_rate': metrics.get('win_rate', 0.0),
                'total_trades': metrics.get('total_trades', 0),
                'winning_trades': metrics.get('winning_trades', 0),
                'losing_trades': metrics.get('losing_trades', 0),
                'average_win': metrics.get('average_win', 0.0),
                'average_loss': metrics.get('average_loss', 0.0),
                'max_drawdown': metrics.get('max_drawdown', 0.0),
                'sharpe_ratio': metrics.get('sharpe_ratio', 0.0),
                'additional_data': json.dumps(metrics.get('additional_data', {}))
            }
            
            # Write to performance CSV
            csv_file = self.analytics_dir / "performance_metrics.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=metrics_record.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(metrics_record)
            
            self._logger.debug("Performance metrics stored")
            
        except Exception as e:
            self._logger.error(f"Failed to store performance metrics: {e}")
    
    def store_trade_analytics(self, trade_data: Dict[str, Any]) -> None:
        """
        Store individual trade analytics.
        
        Args:
            trade_data: Dictionary containing trade analysis data
        """
        try:
            # Prepare trade analytics record
            analytics_record = {
                'timestamp': datetime.now().isoformat(),
                'trade_id': trade_data.get('trade_id', ''),
                'symbol': trade_data.get('symbol', ''),
                'strategy': trade_data.get('strategy', ''),
                'entry_time': trade_data.get('entry_time', ''),
                'exit_time': trade_data.get('exit_time', ''),
                'hold_time_minutes': trade_data.get('hold_time_minutes', 0),
                'entry_price': trade_data.get('entry_price', 0.0),
                'exit_price': trade_data.get('exit_price', 0.0),
                'pnl': trade_data.get('pnl', 0.0),
                'pnl_percent': trade_data.get('pnl_percent', 0.0),
                'quantity': trade_data.get('quantity', 0),
                'fees': trade_data.get('fees', 0.0),
                'market_conditions': json.dumps(trade_data.get('market_conditions', {})),
                'exit_reason': trade_data.get('exit_reason', ''),
                'additional_data': json.dumps(trade_data.get('additional_data', {}))
            }
            
            # Write to trade analytics CSV
            csv_file = self.analytics_dir / "trade_analytics.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=analytics_record.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(analytics_record)
            
            self._logger.debug(f"Trade analytics stored: {trade_data.get('trade_id', 'unknown')}")
            
        except Exception as e:
            self._logger.error(f"Failed to store trade analytics: {e}")
    
    def calculate_basic_metrics(self, trades_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Calculate basic performance metrics without pandas dependency.
        
        Args:
            trades_file: Optional path to trades CSV file
            
        Returns:
            Dictionary with basic performance metrics
        """
        try:
            if trades_file is None:
                trades_file = self.data_dir / "trades" / "trades.csv"
            
            if not trades_file.exists():
                return {'error': 'No trades file found'}
            
            # Read trades data
            trades = []
            with open(trades_file, 'r') as f:
                reader = csv.DictReader(f)
                trades = list(reader)
            
            if not trades:
                return {'error': 'No trades found'}
            
            # Calculate basic metrics
            total_pnl = sum(float(trade.get('pnl', 0)) for trade in trades)
            total_trades = len(trades)
            winning_trades = [trade for trade in trades if float(trade.get('pnl', 0)) > 0]
            losing_trades = [trade for trade in trades if float(trade.get('pnl', 0)) < 0]
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            average_win = sum(float(trade.get('pnl', 0)) for trade in winning_trades) / len(winning_trades) if winning_trades else 0
            average_loss = sum(float(trade.get('pnl', 0)) for trade in losing_trades) / len(losing_trades) if losing_trades else 0
            
            profit_factor = abs(average_win * len(winning_trades) / (average_loss * len(losing_trades))) if losing_trades and average_loss != 0 else float('inf')
            
            # Calculate drawdown (simplified)
            running_pnl = 0
            peak = 0
            max_drawdown = 0
            
            for trade in trades:
                running_pnl += float(trade.get('pnl', 0))
                if running_pnl > peak:
                    peak = running_pnl
                drawdown = peak - running_pnl
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return {
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate,
                'average_win': average_win,
                'average_loss': average_loss,
                'profit_factor': profit_factor,
                'max_drawdown': max_drawdown,
                'calculation_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            self._logger.error(f"Failed to calculate basic metrics: {e}")
            return {'error': str(e)}
    
    def calculate_advanced_metrics(self, trades_file: Optional[Path] = None) -> Dict[str, Any]:
        """
        Calculate advanced performance metrics using pandas (if available).
        
        Args:
            trades_file: Optional path to trades CSV file
            
        Returns:
            Dictionary with advanced performance metrics
        """
        if not PANDAS_AVAILABLE:
            self._logger.warning("Pandas not available. Using basic metrics instead.")
            return self.calculate_basic_metrics(trades_file)
        
        try:
            if trades_file is None:
                trades_file = self.data_dir / "trades" / "trades.csv"
            
            if not trades_file.exists():
                return {'error': 'No trades file found'}
            
            # Read trades with pandas
            df = pd.read_csv(trades_file)
            
            if df.empty:
                return {'error': 'No trades found'}
            
            # Ensure pnl column is numeric
            df['pnl'] = pd.to_numeric(df['pnl'], errors='coerce').fillna(0)
            
            # Calculate advanced metrics
            total_pnl = df['pnl'].sum()
            total_trades = len(df)
            winning_trades = len(df[df['pnl'] > 0])
            losing_trades = len(df[df['pnl'] < 0])
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            
            # Calculate returns-based metrics
            returns = df['pnl'].values
            cumulative_returns = returns.cumsum()
            
            # Sharpe ratio (simplified - assuming daily returns)
            if len(returns) > 1:
                sharpe_ratio = returns.mean() / returns.std() * math.sqrt(252) if returns.std() != 0 else 0
            else:
                sharpe_ratio = 0
            
            # Maximum drawdown
            peak = cumulative_returns.expanding().max()
            drawdown = cumulative_returns - peak
            max_drawdown = drawdown.min()
            
            # Sortino ratio (downside deviation)
            negative_returns = returns[returns < 0]
            if len(negative_returns) > 1:
                downside_deviation = negative_returns.std()
                sortino_ratio = returns.mean() / downside_deviation * math.sqrt(252) if downside_deviation != 0 else 0
            else:
                sortino_ratio = 0
            
            # Calmar ratio
            calmar_ratio = (returns.mean() * 252) / abs(max_drawdown) if max_drawdown != 0 else 0
            
            # Additional statistics
            average_win = df[df['pnl'] > 0]['pnl'].mean() if winning_trades > 0 else 0
            average_loss = df[df['pnl'] < 0]['pnl'].mean() if losing_trades > 0 else 0
            
            profit_factor = abs((average_win * winning_trades) / (average_loss * losing_trades)) if losing_trades > 0 and average_loss != 0 else float('inf')
            
            return {
                'total_pnl': total_pnl,
                'total_trades': total_trades,
                'winning_trades': winning_trades,
                'losing_trades': losing_trades,
                'win_rate': win_rate,
                'average_win': average_win,
                'average_loss': average_loss,
                'profit_factor': profit_factor,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'sortino_ratio': sortino_ratio,
                'calmar_ratio': calmar_ratio,
                'total_return_percent': (total_pnl / abs(df['pnl'].iloc[0])) * 100 if len(df) > 0 and df['pnl'].iloc[0] != 0 else 0,
                'calculation_time': datetime.now().isoformat(),
                'pandas_version': pd.__version__
            }
            
        except Exception as e:
            self._logger.error(f"Failed to calculate advanced metrics: {e}")
            return {'error': str(e)}
    
    def generate_performance_report(self, output_file: Optional[Path] = None) -> Path:
        """
        Generate a comprehensive performance report.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to generated report file
        """
        try:
            if output_file is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = self.analytics_dir / f"performance_report_{timestamp}.json"
            
            # Calculate metrics
            basic_metrics = self.calculate_basic_metrics()
            advanced_metrics = self.calculate_advanced_metrics() if PANDAS_AVAILABLE else {}
            
            # Generate report
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'pandas_available': PANDAS_AVAILABLE,
                'basic_metrics': basic_metrics,
                'advanced_metrics': advanced_metrics if PANDAS_AVAILABLE else None,
                'data_sources': {
                    'trades_file': str(self.data_dir / "trades" / "trades.csv"),
                    'positions_file': str(self.data_dir / "positions" / "positions.csv"),
                    'analytics_dir': str(self.analytics_dir)
                }
            }
            
            # Save report
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            
            self._logger.info(f"Performance report generated: {output_file}")
            return output_file
            
        except Exception as e:
            self._logger.error(f"Failed to generate performance report: {e}")
            raise
    
    def store_market_conditions(self, conditions: Dict[str, Any], timestamp: Optional[datetime] = None) -> None:
        """
        Store market conditions data for later analysis.
        
        Args:
            conditions: Dictionary of market condition data
            timestamp: Optional timestamp (defaults to now)
        """
        try:
            if timestamp is None:
                timestamp = datetime.now()
            
            # Prepare market conditions record
            conditions_record = {
                'timestamp': timestamp.isoformat(),
                'vix': conditions.get('vix', 0.0),
                'spy_price': conditions.get('spy_price', 0.0),
                'market_regime': conditions.get('market_regime', ''),
                'iv_environment': conditions.get('iv_environment', ''),
                'additional_data': json.dumps(conditions.get('additional_data', {}))
            }
            
            # Write to market conditions CSV
            csv_file = self.analytics_dir / "market_conditions.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=conditions_record.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(conditions_record)
            
            self._logger.debug("Market conditions stored")
            
        except Exception as e:
            self._logger.error(f"Failed to store market conditions: {e}")