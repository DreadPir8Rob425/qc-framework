# Option Alpha Framework - Enhanced Position Manager
# Integrated with SQLite StateManager, replaces position_csv_handler functionality

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
    
    def _create_position_from_config(self, config: Dict[str, Any], bot_name: Optional[str] = None) -> Position:
        """Create Position object from configuration"""
        
        # Extract basic position info
        position = Position(
            id=str(uuid.uuid4()),
            symbol=config.get('symbol', ''),
            position_type=config.get('strategy_type', 'unknown'),
            state=PositionState.OPEN.value,
            opened_at=datetime.now(),
            quantity=config.get('quantity', 1),
            entry_price=config.get('entry_price', 0.0),
            current_price=config.get('entry_price', 0.0),
            tags=config.get('tags', []),
            automation_source=bot_name
        )
        
        # Add option legs if they exist
        legs_config = config.get('legs', [])
        for leg_config in legs_config:
            leg = OptionLeg(
                option_type=leg_config.get('option_type', 'call'),
                side=leg_config.get('side', 'long'),
                strike=leg_config.get('strike', 0.0),
                expiration=datetime.fromisoformat(leg_config.get('expiration', datetime.now().isoformat())),
                quantity=leg_config.get('quantity', 1),
                entry_price=leg_config.get('entry_price', 0.0),
                current_price=leg_config.get('entry_price', 0.0)
            )
            position.add_leg(leg)
        
        return position
    
    def _validate_position(self, position: Position) -> List[str]:
        """Validate position data"""
        errors = []
        
        if not position.symbol:
            errors.append("Position must have a symbol")
        
        if position.quantity == 0:
            errors.append("Position quantity cannot be zero")
        
        if position.entry_price < 0:
            errors.append("Entry price cannot be negative")
        
        # Add more validation as needed
        
        return errors
    
    def close_position(self, position_id: str, close_config: Optional[Dict[str, Any]] = None,
                      exit_reason: str = "Manual", bot_name: Optional[str] = None) -> bool:
        """
        Close an existing position.
        
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
            
            if position.state != PositionState.OPEN.value:
                self.logger.warning(LogCategory.TRADE_EXECUTION, "Position not open",
                                  position_id=position_id, state=position.state)
                return False
            
            # Process close configuration
            if close_config:
                exit_price = close_config.get('exit_price', position.current_price)
                quantity_to_close = close_config.get('quantity', position.quantity)
            else:
                exit_price = position.current_price
                quantity_to_close = position.quantity
            
            # Handle partial closes (simplified for now - full implementation would split position)
            if quantity_to_close < position.quantity:
                self.logger.info(LogCategory.TRADE_EXECUTION, "Partial close requested",
                               position_id=position_id, quantity_to_close=quantity_to_close,
                               total_quantity=position.quantity)
                # For now, close the entire position
                # TODO: Implement position splitting for partial closes
            
            # Close the position
            position.close_position(exit_price, exit_reason)
            
            # Calculate final P&L
            if position.legs:
                # Multi-leg position P&L calculation would go here
                position.realized_pnl = (exit_price - position.entry_price) * position.quantity
            else:
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
        Update current prices for all open positions.
        
        Args:
            market_data: Dictionary with symbol -> price mappings
        """
        try:
            open_positions = self.get_open_positions()
            
            for position in open_positions:
                updated = False
                
                # Update underlying price if available
                if position.symbol in market_data:
                    new_price = market_data[position.symbol]
                    if new_price != position.current_price:
                        position.current_price = new_price
                        updated = True
                
                # Update option leg prices if available
                if hasattr(position, 'legs') and position.legs:
                    for leg in position.legs:
                        # Create option symbol key for price lookup
                        option_key = f"{position.symbol}_{leg.strike}_{leg.option_type}_{leg.expiration.strftime('%Y%m%d')}"
                        if option_key in market_data:
                            new_leg_price = market_data[option_key]
                            if new_leg_price != leg.current_price:
                                leg.current_price = new_leg_price
                                updated = True
                
                # Recalculate P&L if prices updated
                if updated:
                    self._recalculate_position_pnl(position)
                    
                    # Update in SQLite and cache
                    self.state_manager.store_position(position)
                    self._positions_cache[position.id] = position
            
            if open_positions:
                self.logger.debug(LogCategory.MARKET_DATA, "Position prices updated",
                                positions_updated=len([p for p in open_positions if p.id in market_data]))
                                
        except Exception as e:
            self.logger.error(LogCategory.MARKET_DATA, "Failed to update position prices",
                            error=str(e))
    
    def _recalculate_position_pnl(self, position: Position) -> None:
        """Recalculate position P&L based on current prices"""
        try:
            if hasattr(position, 'legs') and position.legs:
                # Multi-leg position P&L
                total_unrealized = 0.0
                for leg in position.legs:
                    leg_pnl = leg.unrealized_pnl  # This property calculates based on current vs entry price
                    total_unrealized += leg_pnl
                position.unrealized_pnl = total_unrealized
            else:
                # Simple position P&L
                position.unrealized_pnl = (position.current_price - position.entry_price) * position.quantity
                
        except Exception as e:
            self.logger.error(LogCategory.TRADE_EXECUTION, "Failed to recalculate P&L",
                            position_id=position.id, error=str(e))
    
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
            positions = self.state_manager.get_positions(
                state=PositionState(state) if state else None,
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
        return self.get_positions(state=PositionState.OPEN.value, symbol=symbol, bot_name=bot_name)
    
    def get_closed_positions(self, symbol: Optional[str] = None, bot_name: Optional[str] = None) -> List[Position]:
        """Get all closed positions with optional filters"""
        return self.get_positions(state=PositionState.CLOSED.value, symbol=symbol, bot_name=bot_name)
    
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
                'position_type': position.position_type,
                'quantity': position.quantity,
                'price': price or (position.exit_price if action == "CLOSE" else position.entry_price),
                'pnl': position.realized_pnl if action == "CLOSE" else 0.0,
                'bot_name': bot_name,
                'tags': position.tags
            }
            
            # Store in cold state
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
                pos_type = position.position_type
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
                    'position_type': position.position_type,
                    'state': position.state,
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