# Option Alpha Framework - Enhanced Analytics Handler
# Integrated with SQLite StateManager for performance analytics

import logging
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from oa_framework_enums import LogCategory, PositionState, ErrorCode
import math

# Optional pandas import for advanced analytics
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from oa_framework_enums import LogCategory, ErrorCode, ErrorMessages
from oa_logging import FrameworkLogger

class AnalyticsHandler:
    """
    Enhanced analytics handler that works with SQLite StateManager.
    Provides both basic (no dependencies) and advanced (pandas) analytics.
    """
    
    def __init__(self, state_manager, logger: Optional[FrameworkLogger] = None):
        self.state_manager = state_manager
        self.logger = logger or FrameworkLogger("AnalyticsHandler")
        
    def calculate_performance_metrics(self, bot_name: Optional[str] = None, 
                                    start_date: Optional[datetime] = None,
                                    end_date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calculate comprehensive performance metrics from SQLite data.
        
        Args:
            bot_name: Filter by specific bot (optional)
            start_date: Start date for analysis (optional)
            end_date: End date for analysis (optional)
            
        Returns:
            Dictionary with performance metrics
        """
        try:
            # Get positions from SQLite
            positions = self.state_manager.get_positions()
            
            # Filter positions if needed
            if bot_name:
                positions = [p for p in positions if p.automation_source == bot_name]
            
            if start_date:
                positions = [p for p in positions if p.opened_at >= start_date]
                
            if end_date:
                positions = [p for p in positions if p.opened_at <= end_date]
            
            if not positions:
                return {'error': 'No positions found for analysis'}
            
            # Calculate basic metrics
            closed_positions = [p for p in positions if p.state == 'closed']
            open_positions = [p for p in positions if p.state == 'open']
            
            total_pnl = sum(p.realized_pnl for p in closed_positions) + sum(p.unrealized_pnl for p in open_positions)
            total_trades = len(closed_positions)
            winning_trades = [p for p in closed_positions if p.realized_pnl > 0]
            losing_trades = [p for p in closed_positions if p.realized_pnl < 0]
            
            win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
            
            average_win = sum(p.realized_pnl for p in winning_trades) / len(winning_trades) if winning_trades else 0
            average_loss = sum(p.realized_pnl for p in losing_trades) / len(losing_trades) if losing_trades else 0
            
            profit_factor = abs(average_win * len(winning_trades) / (average_loss * len(losing_trades))) if losing_trades and average_loss != 0 else float('inf')
            
            # Calculate drawdown
            returns = [p.realized_pnl for p in closed_positions]
            max_drawdown = self._calculate_max_drawdown(returns)
            
            # Calculate Sharpe ratio if we have enough data
            sharpe_ratio = self._calculate_sharpe_ratio(returns) if len(returns) > 1 else 0
            
            # Calculate additional metrics
            largest_win = max((p.realized_pnl for p in closed_positions), default=0)
            largest_loss = min((p.realized_pnl for p in closed_positions), default=0)
            
            # Average days in trade
            avg_days_open = sum(p.days_open for p in closed_positions) / len(closed_positions) if closed_positions else 0
            
            # Current exposure
            current_exposure = sum(abs(p.unrealized_pnl) for p in open_positions)
            
            metrics = {
                'analysis_timestamp': datetime.now().isoformat(),
                'period_start': start_date.isoformat() if start_date else None,
                'period_end': end_date.isoformat() if end_date else None,
                'bot_name': bot_name,
                
                # Position counts
                'total_positions': len(positions),
                'closed_positions': len(closed_positions),
                'open_positions': len(open_positions),
                
                # P&L metrics
                'total_pnl': total_pnl,
                'realized_pnl': sum(p.realized_pnl for p in closed_positions),
                'unrealized_pnl': sum(p.unrealized_pnl for p in open_positions),
                'current_exposure': current_exposure,
                
                # Trade statistics
                'total_trades': total_trades,
                'winning_trades': len(winning_trades),
                'losing_trades': len(losing_trades),
                'win_rate': win_rate * 100,  # Convert to percentage
                
                # Average metrics
                'average_win': average_win,
                'average_loss': average_loss,
                'profit_factor': profit_factor,
                'avg_days_in_trade': avg_days_open,
                
                # Risk metrics
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'largest_win': largest_win,
                'largest_loss': largest_loss,
                
                # Additional analysis
                'return_per_trade': total_pnl / total_trades if total_trades > 0 else 0,
                'win_loss_ratio': abs(average_win / average_loss) if average_loss != 0 else float('inf'),
            }
            
            # Store metrics in SQLite
            self.state_manager.store_cold_state(
                metrics, 
                'performance_analysis', 
                ['analytics', bot_name if bot_name else 'all_bots']
            )
            
            self.logger.info(LogCategory.PERFORMANCE, "Performance metrics calculated",
                           total_trades=total_trades, win_rate=f"{win_rate*100:.1f}%", 
                           total_pnl=f"${total_pnl:.2f}")
            
            return metrics
            
        except Exception as e:
            self.logger.error(LogCategory.PERFORMANCE, "Failed to calculate performance metrics", 
                            error=str(e))
            return {'error': str(e)}
    
    def _calculate_max_drawdown(self, returns: List[float]) -> float:
        """Calculate maximum drawdown from returns"""
        if not returns:
            return 0.0
            
        cumulative = 0
        peak = 0
        max_drawdown = 0
        
        for ret in returns:
            cumulative += ret
            if cumulative > peak:
                peak = cumulative
            drawdown = peak - cumulative
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return max_drawdown
    
    def _calculate_sharpe_ratio(self, returns: List[float], risk_free_rate: float = 0.02) -> float:
        """Calculate Sharpe ratio from returns"""
        if len(returns) < 2:
            return 0.0
        
        try:
            mean_return = sum(returns) / len(returns)
            std_dev = math.sqrt(sum((r - mean_return) ** 2 for r in returns) / (len(returns) - 1))
            
            if std_dev == 0:
                return 0.0
            
            # Annualize the Sharpe ratio (assuming daily returns)
            excess_return = mean_return - (risk_free_rate / 252)  # Daily risk-free rate
            return (excess_return / std_dev) * math.sqrt(252)
            
        except Exception as e:
            self.logger.warning(LogCategory.PERFORMANCE, "Error calculating Sharpe ratio", error=str(e))
            return 0.0
    
    def generate_trade_analysis(self, symbol: Optional[str] = None,
                              strategy_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate detailed trade analysis by symbol or strategy.
        
        Args:
            symbol: Filter by symbol (optional)
            strategy_type: Filter by strategy type (optional)
            
        Returns:
            Dictionary with trade analysis
        """
        try:
            positions = self.state_manager.get_positions()
            
            # Apply filters
            if symbol:
                positions = [p for p in positions if p.symbol == symbol]
            
            if strategy_type:
                positions = [p for p in positions if p.position_type == strategy_type]
            
            if not positions:
                return {'error': 'No positions found matching criteria'}
            
            # Analyze by symbol
            symbol_analysis = {}
            for pos in positions:
                if pos.symbol not in symbol_analysis:
                    symbol_analysis[pos.symbol] = {
                        'count': 0,
                        'total_pnl': 0,
                        'win_count': 0,
                        'strategies': set()
                    }
                
                symbol_analysis[pos.symbol]['count'] += 1
                symbol_analysis[pos.symbol]['total_pnl'] += pos.total_pnl
                symbol_analysis[pos.symbol]['strategies'].add(pos.position_type)
                
                if pos.total_pnl > 0:
                    symbol_analysis[pos.symbol]['win_count'] += 1
            
            # Convert sets to lists for JSON serialization
            for symbol_data in symbol_analysis.values():
                symbol_data['strategies'] = list(symbol_data['strategies'])
                symbol_data['win_rate'] = (symbol_data['win_count'] / symbol_data['count']) * 100
            
            # Analyze by strategy type
            strategy_analysis = {}
            for pos in positions:
                if pos.position_type not in strategy_analysis:
                    strategy_analysis[pos.position_type] = {
                        'count': 0,
                        'total_pnl': 0,
                        'win_count': 0,
                        'avg_days_open': 0
                    }
                
                strategy_analysis[pos.position_type]['count'] += 1
                strategy_analysis[pos.position_type]['total_pnl'] += pos.total_pnl
                strategy_analysis[pos.position_type]['avg_days_open'] += pos.days_open
                
                if pos.total_pnl > 0:
                    strategy_analysis[pos.position_type]['win_count'] += 1
            
            # Calculate averages
            for strategy_data in strategy_analysis.values():
                if strategy_data['count'] > 0:
                    strategy_data['win_rate'] = (strategy_data['win_count'] / strategy_data['count']) * 100
                    strategy_data['avg_days_open'] = strategy_data['avg_days_open'] / strategy_data['count']
                    strategy_data['avg_pnl_per_trade'] = strategy_data['total_pnl'] / strategy_data['count']
            
            analysis = {
                'analysis_timestamp': datetime.now().isoformat(),
                'filters': {
                    'symbol': symbol,
                    'strategy_type': strategy_type
                },
                'total_positions_analyzed': len(positions),
                'symbol_breakdown': symbol_analysis,
                'strategy_breakdown': strategy_analysis
            }
            
            # Store analysis in SQLite
            self.state_manager.store_cold_state(
                analysis,
                'trade_analysis',
                ['analytics', 'trade_breakdown', symbol or 'all_symbols']
            )
            
            return analysis
            
        except Exception as e:
            self.logger.error(LogCategory.PERFORMANCE, "Failed to generate trade analysis", 
                            error=str(e))
            return {'error': str(e)}
    
    def export_analytics_to_csv(self, export_dir: Path) -> Dict[str, str]:
        """
        Export analytics data to CSV files for external analysis.
        
        Args:
            export_dir: Directory to save CSV files
            
        Returns:
            Dictionary mapping analysis types to file paths
        """
        try:
            export_dir = Path(export_dir)
            export_dir.mkdir(parents=True, exist_ok=True)
            
            exported_files = {}
            
            # Export performance metrics
            perf_metrics = self.state_manager.get_cold_state('performance_analysis', limit=1000)
            if perf_metrics:
                perf_file = export_dir / "performance_metrics.csv"
                self._export_to_csv(perf_metrics, perf_file, 'performance_analysis')
                exported_files['performance_metrics'] = str(perf_file)
            
            # Export trade analysis
            trade_analysis = self.state_manager.get_cold_state('trade_analysis', limit=1000)
            if trade_analysis:
                trade_file = export_dir / "trade_analysis.csv"
                self._export_to_csv(trade_analysis, trade_file, 'trade_analysis')
                exported_files['trade_analysis'] = str(trade_file)
            
            # Export position summary
            positions = self.state_manager.get_positions()
            if positions:
                pos_file = export_dir / "positions_summary.csv"
                self._export_positions_to_csv(positions, pos_file)
                exported_files['positions_summary'] = str(pos_file)
            
            self.logger.info(LogCategory.SYSTEM, "Analytics exported to CSV",
                           files_exported=len(exported_files))
            
            return exported_files
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to export analytics to CSV",
                            error=str(e))
            return {}
    
    def _export_to_csv(self, data: List[Dict], file_path: Path, data_type: str) -> None:
        """Export list of dictionaries to CSV"""
        if not data:
            return
            
        try:
            # Flatten nested data structures
            flattened_data = []
            for item in data:
                flat_item = {
                    'timestamp': item['timestamp'].isoformat(),
                    'category': item.get('category', data_type),
                    'tags': json.dumps(item.get('tags', []))
                }
                
                # Flatten the nested data dictionary
                item_data = item.get('data', {})
                for key, value in item_data.items():
                    if isinstance(value, (dict, list)):
                        flat_item[key] = json.dumps(value)
                    else:
                        flat_item[key] = value
                
                flattened_data.append(flat_item)
            
            # Write to CSV
            if flattened_data:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=flattened_data[0].keys())
                    writer.writeheader()
                    writer.writerows(flattened_data)
                    
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, f"Failed to export {data_type} to CSV",
                            error=str(e))
    
    def _export_positions_to_csv(self, positions: List, file_path: Path) -> None:
        """Export positions to CSV with flattened structure"""
        if not positions:
            return
            
        try:
            csv_data = []
            for pos in positions:
                row = {
                    'position_id': pos.id,
                    'symbol': pos.symbol,
                    'position_type': pos.position_type.value if hasattr(pos.position_type, 'value') else pos.position_type,
                    'state': pos.state.value if hasattr(pos.state, 'value') else pos.state,
                    'quantity': pos.quantity,
                    'entry_price': pos.entry_price,
                    'current_price': pos.current_price,
                    'unrealized_pnl': pos.unrealized_pnl,
                    'realized_pnl': pos.realized_pnl,
                    'total_pnl': pos.total_pnl,
                    'opened_at': pos.opened_at.isoformat(),
                    'closed_at': pos.closed_at.isoformat() if pos.closed_at else '',
                    'days_open': pos.days_open,
                    'tags': json.dumps(pos.tags),
                    'leg_count': len(pos.legs) if hasattr(pos, 'legs') else 0
                }
                
                # Add exit information if available
                if hasattr(pos, 'exit_price') and pos.exit_price:
                    row['exit_price'] = pos.exit_price
                if hasattr(pos, 'exit_reason') and pos.exit_reason:
                    row['exit_reason'] = pos.exit_reason
                
                csv_data.append(row)
            
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if csv_data:
                    writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_data)
                    
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to export positions to CSV",
                            error=str(e))
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive performance report combining all analytics.
        
        Returns:
            Dictionary with complete performance report
        """
        try:
            # Get overall performance metrics
            overall_metrics = self.calculate_performance_metrics()
            
            # Get trade analysis
            trade_analysis = self.generate_trade_analysis()
            
            # Get recent activity (last 30 days)
            thirty_days_ago = datetime.now() - timedelta(days=30)
            recent_metrics = self.calculate_performance_metrics(start_date=thirty_days_ago)
            
            # Get position summary from state manager
            positions = self.state_manager.get_positions()
            open_positions = [p for p in positions if p.state == 'open']
            
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'report_type': 'comprehensive_performance',
                
                # Overall performance
                'overall_performance': overall_metrics,
                
                # Recent performance (30 days)
                'recent_performance': recent_metrics,
                
                # Trade breakdown
                'trade_analysis': trade_analysis,
                
                # Current status
                'current_status': {
                    'open_positions': len(open_positions),
                    'total_exposure': sum(abs(p.unrealized_pnl) for p in open_positions),
                    'unrealized_pnl': sum(p.unrealized_pnl for p in open_positions),
                },
                
                # System info
                'system_info': {
                    'pandas_available': PANDAS_AVAILABLE,
                    'total_data_points': len(positions),
                    'analysis_capabilities': [
                        'basic_metrics',
                        'sharpe_ratio',
                        'drawdown_analysis',
                        'trade_breakdown',
                    ]
                }
            }
            
            # Store comprehensive report
            self.state_manager.store_cold_state(
                report,
                'performance_report',
                ['analytics', 'comprehensive', 'report']
            )
            
            self.logger.info(LogCategory.PERFORMANCE, "Comprehensive performance report generated")
            
            return report
            
        except Exception as e:
            self.logger.error(LogCategory.PERFORMANCE, "Failed to generate performance report",
                            error=str(e))
            return {'error': str(e)}

# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_analytics_handler(state_manager, logger: Optional[FrameworkLogger] = None) -> AnalyticsHandler:
    """
    Factory function to create analytics handler.
    
    Args:
        state_manager: StateManager instance
        logger: Optional logger instance
        
    Returns:
        AnalyticsHandler instance
    """
    return AnalyticsHandler(state_manager, logger)