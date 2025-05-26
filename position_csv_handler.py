# Option Alpha Framework - Position CSV Handler
# Separate module for position-related CSV operations

import csv
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import asdict

# Import framework components - using relative imports to avoid circular dependencies
try:
    from oa_framework_enums import PositionState, PositionType, QCOptionRight, OptionSide
except ImportError:
    # Fallback if enums not available - define minimal types
    class PositionState:
        OPEN = "open"
        CLOSED = "closed"
        PENDING_OPEN = "pending_open"
        PENDING_CLOSE = "pending_close"

class PositionCSVHandler:
    """
    Handles position storage and retrieval using CSV files.
    Separated from main state manager for better organization.
    """
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.positions_dir = data_dir / "positions"
        self.positions_dir.mkdir(exist_ok=True)
        self._logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for position handler"""
        logger = logging.getLogger(f"{__name__}.PositionCSVHandler")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def store_position(self, position_data: Dict[str, Any]) -> None:
        """
        Store position in CSV file.
        
        Args:
            position_data: Dictionary containing position information
        """
        try:
            # Ensure position has required fields with defaults
            required_fields = {
                'id': position_data.get('id', ''),
                'symbol': position_data.get('symbol', ''),
                'position_type': position_data.get('position_type', ''),
                'state': position_data.get('state', ''),
                'quantity': position_data.get('quantity', 0),
                'entry_price': position_data.get('entry_price', 0.0),
                'current_price': position_data.get('current_price', 0.0),
                'unrealized_pnl': position_data.get('unrealized_pnl', 0.0),
                'realized_pnl': position_data.get('realized_pnl', 0.0),
                'opened_at': position_data.get('opened_at', datetime.now().isoformat()),
                'closed_at': position_data.get('closed_at', ''),
                'tags': json.dumps(position_data.get('tags', [])),
                'legs': json.dumps(position_data.get('legs', []))
            }
            
            # Handle datetime objects
            if isinstance(required_fields['opened_at'], datetime):
                required_fields['opened_at'] = required_fields['opened_at'].isoformat()
            
            if required_fields['closed_at'] and isinstance(required_fields['closed_at'], datetime):
                required_fields['closed_at'] = required_fields['closed_at'].isoformat()
            
            # Write to positions CSV
            csv_file = self.positions_dir / "positions.csv"
            file_exists = csv_file.exists()
            
            with open(csv_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=required_fields.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(required_fields)
            
            self._logger.debug(f"Position stored: {required_fields['id']}")
            
        except Exception as e:
            self._logger.error(f"Failed to store position: {e}")
            raise
    
    def get_positions(self, state: Optional[str] = None, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get positions from CSV with optional filters.
        
        Args:
            state: Filter by position state (optional)
            symbol: Filter by symbol (optional)
            
        Returns:
            List of position dictionaries
        """
        try:
            csv_file = self.positions_dir / "positions.csv"
            if not csv_file.exists():
                return []
            
            positions = []
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    # Apply filters
                    if state and row['state'] != state:
                        continue
                    if symbol and row['symbol'] != symbol:
                        continue
                    
                    # Convert string fields back to appropriate types
                    position = {
                        'id': row['id'],
                        'symbol': row['symbol'],
                        'position_type': row['position_type'],
                        'state': row['state'],
                        'quantity': int(row['quantity']) if row['quantity'] else 0,
                        'entry_price': float(row['entry_price']) if row['entry_price'] else 0.0,
                        'current_price': float(row['current_price']) if row['current_price'] else 0.0,
                        'unrealized_pnl': float(row['unrealized_pnl']) if row['unrealized_pnl'] else 0.0,
                        'realized_pnl': float(row['realized_pnl']) if row['realized_pnl'] else 0.0,
                        'opened_at': datetime.fromisoformat(row['opened_at']) if row['opened_at'] else None,
                        'closed_at': datetime.fromisoformat(row['closed_at']) if row['closed_at'] else None,
                        'tags': json.loads(row['tags']) if row['tags'] else [],
                        'legs': json.loads(row['legs']) if row['legs'] else []
                    }
                    positions.append(position)
            
            return positions
            
        except Exception as e:
            self._logger.error(f"Failed to get positions: {e}")
            return []
    
    def get_position_by_id(self, position_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific position by ID.
        
        Args:
            position_id: Position ID to search for
            
        Returns:
            Position dictionary if found, None otherwise
        """
        try:
            positions = self.get_positions()
            for position in positions:
                if position['id'] == position_id:
                    return position
            return None
            
        except Exception as e:
            self._logger.error(f"Failed to get position by ID {position_id}: {e}")
            return None
    
    def update_position(self, position_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing position in CSV.
        Note: This is inefficient for large datasets but works for backtesting.
        
        Args:
            position_id: ID of position to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            csv_file = self.positions_dir / "positions.csv"
            if not csv_file.exists():
                return False
            
            # Read all positions
            positions = []
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                positions = list(reader)
            
            # Find and update the position
            position_found = False
            for position in positions:
                if position['id'] == position_id:
                    # Update fields
                    for key, value in updates.items():
                        if key in position:
                            if isinstance(value, datetime):
                                position[key] = value.isoformat()
                            elif isinstance(value, (list, dict)):
                                position[key] = json.dumps(value)
                            else:
                                position[key] = str(value)
                    position_found = True
                    break
            
            if not position_found:
                self._logger.warning(f"Position {position_id} not found for update")
                return False
            
            # Write back all positions
            with open(csv_file, 'w', newline='') as f:
                if positions:
                    writer = csv.DictWriter(f, fieldnames=positions[0].keys())
                    writer.writeheader()
                    writer.writerows(positions)
            
            self._logger.debug(f"Position updated: {position_id}")
            return True
            
        except Exception as e:
            self._logger.error(f"Failed to update position {position_id}: {e}")
            return False
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        return self.get_positions(state="open")
    
    def get_closed_positions(self) -> List[Dict[str, Any]]:
        """Get all closed positions"""
        return self.get_positions(state="closed")
    
    def get_positions_by_symbol(self, symbol: str) -> List[Dict[str, Any]]:
        """Get all positions for a specific symbol"""
        return self.get_positions(symbol=symbol)
    
    def get_position_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for all positions.
        
        Returns:
            Dictionary with position summary statistics
        """
        try:
            positions = self.get_positions()
            
            if not positions:
                return {
                    'total_positions': 0,
                    'open_positions': 0,
                    'closed_positions': 0,
                    'total_unrealized_pnl': 0.0,
                    'total_realized_pnl': 0.0,
                    'symbols': []
                }
            
            open_count = len([p for p in positions if p['state'] == 'open'])
            closed_count = len([p for p in positions if p['state'] == 'closed'])
            
            total_unrealized = sum(p['unrealized_pnl'] for p in positions)
            total_realized = sum(p['realized_pnl'] for p in positions)
            
            symbols = list(set(p['symbol'] for p in positions if p['symbol']))
            
            return {
                'total_positions': len(positions),
                'open_positions': open_count,
                'closed_positions': closed_count,
                'total_unrealized_pnl': total_unrealized,
                'total_realized_pnl': total_realized,
                'total_pnl': total_unrealized + total_realized,
                'symbols': symbols,
                'unique_symbols': len(symbols)
            }
            
        except Exception as e:
            self._logger.error(f"Failed to get position summary: {e}")
            return {'error': str(e)}
    
    def export_positions_to_json(self, output_file: Optional[Path] = None) -> Path:
        """
        Export all positions to JSON format for easier analysis.
        
        Args:
            output_file: Optional output file path
            
        Returns:
            Path to exported JSON file
        """
        try:
            if output_file is None:
                output_file = self.positions_dir / "positions_export.json"
            
            positions = self.get_positions()
            
            # Convert datetime objects to ISO format for JSON serialization
            for position in positions:
                if position.get('opened_at') and isinstance(position['opened_at'], datetime):
                    position['opened_at'] = position['opened_at'].isoformat()
                if position.get('closed_at') and isinstance(position['closed_at'], datetime):
                    position['closed_at'] = position['closed_at'].isoformat()
            
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'total_positions': len(positions),
                'summary': self.get_position_summary(),
                'positions': positions
            }
            
            with open(output_file, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            self._logger.info(f"Positions exported to: {output_file}")
            return output_file
            
        except Exception as e:
            self._logger.error(f"Failed to export positions: {e}")
            raise