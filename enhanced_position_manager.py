# Option Alpha Framework - Enhanced Position Manager (FIXED)
# Fixed version with proper JSON serialization and P&L calculation

import logging
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import uuid
from oa_framework_enums import PositionState, PositionType, LogCategory, ErrorCode
from oa_logging import FrameworkLogger
from oa_data_structures import Position, OptionLeg, TradeRecord

class PositionManager:
    """
    Enhanced position manager that integrates with SQLite StateManager.
    Handles all position lifecycle management and trade recording.
    """
    
    def __init__(self, state_manager, logger: Optional[FrameworkLogger] = None):
        self.state_manager = state_manager
        self.logger = logger or FrameworkLogger("PositionManager")
        self._positions_cache: Dict[str, Position] = {}
        self._cache_dirty = True
        
    def open_position(self, position_config: Dict[str, Any], bot_name: Optional[str] = None) -> Optional[Position]:
        """
        Open a new position based on configuration.
        
        Args:
            position_config: Configuration dictionary for the position
            bot_name: Name of bot opening the position
            
        Returns:
            Position object if successful, None otherwise
        """
        try:
            # Create position from config
            position = self._create_position_from_config(position_config, bot_name)
            
            # Validate position
            if position is None:
                self.logger.error(LogCategory.TRADE_EXECUTION, "Position creation failed",
                            config=position_config)
                return None
                
            validation_errors = self._validate_position(position)
            if validation_errors:
                self.logger.error(LogCategory.TRADE_EXECUTION, "Position validation failed",
                                errors=validation_errors)
                return None
            
            # Store position in SQLite
            self.state_manager.store_position(position)
            
            # Update cache
            self._positions_cache[position.id] = position
            
            # Log trade record
            self._log_trade_record(position, "OPEN", bot_name)
            
            self.logger.info(LogCategory.TRADE_EXECUTION, "Position opened",
                           position_id=position.id, symbol=position.symbol,
                           position_type=position.position_type, bot_name=bot_name)
            
            return position
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Failed to open position",
                            error=str(e), config=position_config)
            return None
    
    def _create_position_from_config(self, config: Dict[str, Any], bot_name: Optional[str] = None) -> Optional[Position]:
        """Create Position object from configuration"""
        
        try:
            # Ensure we have a valid position type
            strategy_type = config.get('strategy_type', 'long_call')
            if isinstance(strategy_type, str):
                try:
                    position_type = PositionType(strategy_type)
                except ValueError:
                    position_type = PositionType.LONG_CALL  # Default fallback
            else:
                position_type = strategy_type
            
            # Create position with proper defaults
            position = Position(
                id=str(uuid.uuid4()),
                symbol=config.get('symbol', 'SPY'),
                position_type=position_type.value,
                state="open",
                opened_at=datetime.now(),
                quantity=config.get('quantity', 1),
                entry_price=float(config.get('entry_price', 100.0)),
                current_price=float(config.get('entry_price', 100.0)),
                tags=config.get('tags', []),
                automation_source=bot_name
            )
            
            return position
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, f"Failed to create position from config: {e}")
            return None
    
    def _validate_position(self, position: Position) -> List[str]:
        """Validate position data"""
        errors = []
        
        if not position.symbol:
            errors.append("Position must have a symbol")
        
        if position.quantity == 0:
            errors.append("Position quantity cannot be zero")
        
        if position.entry_price < 0:
            errors.append("Entry price cannot be negative")
        
        return errors
    
    
    
    def close_position(self, position_id: str, close_config: Optional[Dict[str, Any]] = None,
                    exit_reason: str = "Manual", bot_name: Optional[str] = None) -> bool:
        """
        Close an existing position - FIXED VERSION.
        
        Args:
            position_id: ID of position to close
            close_config: Configuration for closing (price, partial quantity, etc.)
            exit_reason: Reason for closing
            bot_name: Name of bot closing the position
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get position
            position = self.get_position_by_id(position_id)
            if not position:
                self.logger.warning(LogCategory.TRADE_EXECUTION, "Position not found for close",
                                position_id=position_id)
                return False
            
            # FIXED: Check if position is actually open using proper comparison
            current_state = position.state
            if hasattr(current_state, 'value'):
                state_value = current_state
            else:
                state_value = str(current_state)
                
            if state_value.lower() != 'open':
                self.logger.warning(LogCategory.TRADE_EXECUTION, "Position not open",
                                position_id=position_id, state=state_value)
                return False
            
            # Process close configuration
            if close_config:
                exit_price = close_config.get('exit_price', position.current_price)
            else:
                exit_price = position.current_price
            
            # Close the position using the Position method
            position.close_position(exit_price, exit_reason)
            
            # Calculate final P&L
            position.realized_pnl = (exit_price - position.entry_price) * position.quantity
            position.unrealized_pnl = 0.0
            
            # Update in SQLite
            self.state_manager.store_position(position)
            
            # Update cache
            self._positions_cache[position.id] = position
            
            # Log trade record
            self._log_trade_record(position, "CLOSE", bot_name, exit_price)
            
            self.logger.info(LogCategory.TRADE_EXECUTION, "Position closed",
                        position_id=position_id, exit_price=exit_price,
                        realized_pnl=position.realized_pnl, exit_reason=exit_reason)
            
            return True
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Failed to close position",
                            position_id=position_id, error=str(e))
            return False
        
    
    def update_position_prices(self, market_data: Dict[str, Any]) -> None:
        """
        Update current prices for all open positions - COMPREHENSIVE FIX.
        
        Args:
            market_data: Dictionary with symbol -> price mappings or MarketData objects
        """
        try:
            open_positions = self.get_open_positions()
            updated_count = 0
            
            for position in open_positions:
                try:
                    updated = False
                    
                    # Update underlying price if available
                    if position.symbol in market_data:
                        market_info = market_data[position.symbol]
                        
                        # Handle both MarketData objects and simple price values
                        new_price = None
                        if hasattr(market_info, 'price'):
                            # MarketData object
                            new_price = float(market_info.price)
                        elif isinstance(market_info, (int, float)):
                            # Simple price value
                            new_price = float(market_info)
                        elif isinstance(market_info, dict) and 'price' in market_info:
                            # Dictionary with price key
                            new_price = float(market_info['price'])
                        
                        if new_price is not None and new_price != position.current_price:
                            position.current_price = new_price
                            updated = True
                    
                    # Recalculate P&L if prices updated
                    if updated:
                        self._recalculate_position_pnl(position)
                        
                        # Update in SQLite and cache (with error handling)
                        try:
                            self.state_manager.store_position(position)
                            self._positions_cache[position.id] = position
                            updated_count += 1
                        except Exception as store_error:
                            self.logger.error(LogCategory.MARKET_DATA, "Failed to store updated position",
                                            position_id=position.id, error=str(store_error))
                            
                except Exception as pos_error:
                    self.logger.error(LogCategory.MARKET_DATA, "Failed to update individual position",
                                    position_id=position.id, error=str(pos_error))
                    continue
            
            if updated_count > 0:
                self.logger.debug(LogCategory.MARKET_DATA, "Position prices updated",
                                positions_updated=updated_count, total_open=len(open_positions))
                                
        except Exception as e:
            self.logger.error(LogCategory.MARKET_DATA, "Failed to update position prices",
                            error=str(e))
    
    
    
    def _recalculate_position_pnl(self, position: Position) -> None:
        """Recalculate position P&L based on current prices - COMPREHENSIVE FIX"""
        try:
            if hasattr(position, 'legs') and position.legs:
                # Multi-leg position P&L
                total_unrealized = 0.0
                for leg in position.legs:
                    # Calculate leg P&L properly without MarketData objects
                    price_diff = leg.current_price - leg.entry_price
                    if leg.side == 'short':
                        price_diff = -price_diff  # Invert for short positions
                    leg_pnl = price_diff * leg.quantity * 100  # Options are per 100 shares
                    total_unrealized += leg_pnl
                position.unrealized_pnl = total_unrealized
            else:
                # Simple position P&L - FIXED: Only use numeric values
                if isinstance(position.current_price, (int, float)) and isinstance(position.entry_price, (int, float)):
                    price_diff = float(position.current_price) - float(position.entry_price)
                    position.unrealized_pnl = price_diff * position.quantity
                else:
                    self.logger.warning(LogCategory.TRADE_EXECUTION, "Invalid price types for P&L calculation",
                                    position_id=position.id, 
                                    current_price_type=type(position.current_price).__name__,
                                    entry_price_type=type(position.entry_price).__name__)
                    position.unrealized_pnl = 0.0
                    
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Failed to recalculate P&L",
                            position_id=position.id, error=str(e))
            # Set to zero on error to prevent cascading issues
            position.unrealized_pnl = 0.0
            
            
    
    def get_position_by_id(self, position_id: str) -> Optional[Position]:
        """
        Get specific position by ID.
        
        Args:
            position_id: Position ID to retrieve
            
        Returns:
            Position object if found, None otherwise
        """
        try:
            # Check cache first
            if position_id in self._positions_cache and not self._cache_dirty:
                return self._positions_cache[position_id]
            
            # Get from SQLite
            positions = self.state_manager.get_positions()
            for position in positions:
                if position.id == position_id:
                    self._positions_cache[position_id] = position
                    return position
            
            return None
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to get position by ID",
                            position_id=position_id, error=str(e))
            return None
    
    def get_positions(self, state: Optional[str] = None, symbol: Optional[str] = None,
                     bot_name: Optional[str] = None) -> List[Position]:
        """
        Get positions with optional filters.
        
        Args:
            state: Filter by position state
            symbol: Filter by symbol
            bot_name: Filter by bot name
            
        Returns:
            List of Position objects
        """
        try:
            # Get from SQLite
            state_enum = None
            state_enum = None
            if state:
                try:
                    state_enum = PositionState(state)
                except ValueError:
                    # If invalid state string, try to match existing states
                    for pos_state in PositionState:
                        if pos_state.value.lower() == state.lower():
                            state_enum = pos_state
                            break
                    
            positions = self.state_manager.get_positions(
                state=state_enum,
                symbol=symbol
            )
            
            # Additional filtering by bot name if needed
            if bot_name:
                positions = [p for p in positions if getattr(p, 'automation_source', None) == bot_name]
            
            # Update cache
            for position in positions:
                self._positions_cache[position.id] = position
            
            self._cache_dirty = False
            
            return positions
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to get positions",
                            error=str(e))
            return []
    
    def get_open_positions(self, symbol: Optional[str] = None, bot_name: Optional[str] = None) -> List[Position]:
        """Get all open positions with optional filters"""
        return self.get_positions(state="open", symbol=symbol, bot_name=bot_name)
    
    def get_closed_positions(self, symbol: Optional[str] = None, bot_name: Optional[str] = None) -> List[Position]:
        """Get all closed positions with optional filters"""
        return self.get_positions(state="closed", symbol=symbol, bot_name=bot_name)
    
    def get_positions_by_symbol(self, symbol: str, bot_name: Optional[str] = None) -> List[Position]:
        """Get all positions for a specific symbol"""
        return self.get_positions(symbol=symbol, bot_name=bot_name)
    
    def _log_trade_record(self, position: Position, action: str, bot_name: Optional[str] = None,
                         price: Optional[float] = None) -> None:
        """Log trade record to cold state storage"""
        try:
            trade_record = {
                'trade_id': f"T_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{position.id[:8]}",
                'timestamp': datetime.now().isoformat(),
                'position_id': position.id,
                'symbol': position.symbol,
                'action': action,
                'position_type': position.position_type if hasattr(position.position_type, 'value') else str(position.position_type),
                'quantity': position.quantity,
                'price': price or (position.exit_price if action == "CLOSE" else position.entry_price),
                'pnl': position.realized_pnl if action == "CLOSE" else 0.0,
                'bot_name': bot_name,
                'tags': position.tags
            }
            
            # Store in cold state with safe serialization
            self.state_manager.store_cold_state(
                trade_record,
                'trade_records',
                ['trades', bot_name or 'unknown_bot', position.symbol]
            )
            
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Failed to log trade record",
                            position_id=position.id, error=str(e))
    
    def get_portfolio_summary(self, bot_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get portfolio summary statistics.
        
        Args:
            bot_name: Filter by specific bot (optional)
            
        Returns:
            Dictionary with portfolio summary
        """
        try:
            open_positions = self.get_open_positions(bot_name=bot_name)
            closed_positions = self.get_closed_positions(bot_name=bot_name)
            
            # Calculate summary metrics
            total_unrealized_pnl = sum(p.unrealized_pnl for p in open_positions)
            total_realized_pnl = sum(p.realized_pnl for p in closed_positions)
            
            # Calculate exposure
            total_exposure = sum(abs(p.entry_price * p.quantity) for p in open_positions)
            
            # Get unique symbols
            symbols = set(p.symbol for p in open_positions + closed_positions)
            
            # Calculate win rate from closed positions
            profitable_trades = [p for p in closed_positions if p.realized_pnl > 0]
            win_rate = (len(profitable_trades) / len(closed_positions) * 100) if closed_positions else 0
            
            summary = {
                'timestamp': datetime.now().isoformat(),
                'bot_name': bot_name,
                'open_positions': len(open_positions),
                'closed_positions': len(closed_positions),
                'total_positions': len(open_positions) + len(closed_positions),
                'total_unrealized_pnl': total_unrealized_pnl,
                'total_realized_pnl': total_realized_pnl,
                'total_pnl': total_unrealized_pnl + total_realized_pnl,
                'total_exposure': total_exposure,
                'unique_symbols': len(symbols),
                'symbols': list(symbols),
                'win_rate': win_rate,
                'profitable_trades': len(profitable_trades),
                'losing_trades': len(closed_positions) - len(profitable_trades)
            }
            
            # Add position breakdown by type
            position_types = {}
            for position in open_positions + closed_positions:
                pos_type = position.position_type if hasattr(position.position_type, 'value') else str(position.position_type)
                if pos_type not in position_types:
                    position_types[pos_type] = {'count': 0, 'pnl': 0.0}
                position_types[pos_type]['count'] += 1
                position_types[pos_type]['pnl'] += position.total_pnl
            
            summary['position_breakdown'] = position_types
            
            return summary
            
        except Exception as e:
            self.logger.error(LogCategory.PERFORMANCE, "Failed to generate portfolio summary",
                            error=str(e))
            return {}
    
    def export_positions_to_csv(self, export_path: Path, include_legs: bool = True) -> bool:
        """
        Export all positions to CSV file.
        
        Args:
            export_path: Path for the CSV file
            include_legs: Whether to include option leg details
            
        Returns:
            True if successful, False otherwise
        """
        try:
            positions = self.get_positions()
            if not positions:
                self.logger.warning(LogCategory.SYSTEM, "No positions to export")
                return False
            
            # Prepare CSV data
            csv_data = []
            for position in positions:
                row = {
                    'position_id': position.id,
                    'symbol': position.symbol,
                    'position_type': position.position_type if hasattr(position.position_type, 'value') else str(position.position_type),
                    'state': position.state if hasattr(position.state, 'value') else str(position.state),
                    'quantity': position.quantity,
                    'entry_price': position.entry_price,
                    'current_price': position.current_price,
                    'unrealized_pnl': position.unrealized_pnl,
                    'realized_pnl': position.realized_pnl,
                    'total_pnl': position.total_pnl,
                    'opened_at': position.opened_at.isoformat(),
                    'closed_at': position.closed_at.isoformat() if position.closed_at else '',
                    'days_open': position.days_open,
                    'tags': json.dumps(position.tags),
                    'bot_name': getattr(position, 'automation_source', ''),
                    'exit_reason': getattr(position, 'exit_reason', '')
                }
                
                # Add leg information if requested
                if include_legs and hasattr(position, 'legs') and position.legs:
                    row['leg_count'] = len(position.legs)
                    leg_details = []
                    for leg in position.legs:
                        leg_details.append({
                            'type': leg.option_type,
                            'side': leg.side,
                            'strike': leg.strike,
                            'expiration': leg.expiration.isoformat(),
                            'quantity': leg.quantity,
                            'entry_price': leg.entry_price,
                            'current_price': leg.current_price
                        })
                    row['leg_details'] = json.dumps(leg_details)
                else:
                    row['leg_count'] = 0
                    row['leg_details'] = '[]'
                
                csv_data.append(row)
            
            # Write to CSV
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                if csv_data:
                    writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
                    writer.writeheader()
                    writer.writerows(csv_data)
            
            self.logger.info(LogCategory.SYSTEM, "Positions exported to CSV",
                           file_path=str(export_path), positions_count=len(csv_data))
            
            return True
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to export positions to CSV",
                            export_path=str(export_path), error=str(e))
            return False
    
    def cleanup_old_positions(self, days_to_keep: int = 365) -> Dict[str, Union[int, str]]:
        """
        Clean up old closed positions from storage.
        
        Args:
            days_to_keep: Number of days to keep closed positions
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            # This would require implementing a delete method in StateManager
            # For now, just return statistics
            closed_positions = self.get_closed_positions()
            old_positions = [p for p in closed_positions if p.closed_at and p.closed_at < cutoff_date]
            
            self.logger.info(LogCategory.SYSTEM, "Position cleanup analysis",
                           total_closed=len(closed_positions),
                           old_positions=len(old_positions),
                           cutoff_date=cutoff_date.isoformat())
            
            return {
                'total_closed_positions': len(closed_positions),
                'old_positions_found': len(old_positions),
                'cutoff_date': cutoff_date.isoformat(),
                'positions_deleted': 0  # Would be implemented with actual delete functionality
            }
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to cleanup old positions",
                            error=str(e))
            return {}
    
    def invalidate_cache(self) -> None:
        """Invalidate position cache to force reload from SQLite"""
        self._positions_cache.clear()
        self._cache_dirty = True

# =============================================================================
# FACTORY FUNCTION
# =============================================================================

def create_position_manager(state_manager, logger: Optional[FrameworkLogger] = None) -> PositionManager:
    """
    Factory function to create position manager.
    
    Args:
        state_manager: StateManager instance
        logger: Optional logger instance
        
    Returns:
        PositionManager instance
    """
    return PositionManager(state_manager, logger)