# Option Alpha Framework - Phase 2: Strategy Execution Engine
# Automated strategy execution with decision-driven trading logic

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import json

from oa_framework_enums import (
    EventType, LogCategory, AutomationState, PositionState, 
    DecisionResult, TriggerType, ActionType
)
from oa_logging import FrameworkLogger
from oa_data_structures import Event, Position
from enhanced_decision_engine import EnhancedDecisionEngine, DetailedDecisionResult
from decision_core import DecisionContext
from market_data_integration import MarketDataManager, EnhancedMarketData

# =============================================================================
# AUTOMATION EXECUTION STATES
# =============================================================================

class ExecutionResult(Enum):
    """Results of automation execution"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    PARTIAL = "partial"

@dataclass
class AutomationExecutionResult:
    """Result of automation execution with detailed information"""
    automation_name: str
    execution_id: str
    result: ExecutionResult
    timestamp: datetime
    duration_ms: float
    actions_attempted: int
    actions_successful: int
    positions_opened: int = 0
    positions_closed: int = 0
    decisions_evaluated: int = 0
    error_message: Optional[str] = None
    execution_details: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate of actions"""
        if self.actions_attempted == 0:
            return 0.0
        return self.actions_successful / self.actions_attempted

# =============================================================================
# ACTION PROCESSORS
# =============================================================================

class ActionProcessor:
    """Base class for processing different types of actions"""
    
    def __init__(self, logger: FrameworkLogger):
        self.logger = logger
    
    def process_action(self, action_config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process an action and return result.
        
        Returns:
            Tuple of (success, message, result_data)
        """
        raise NotImplementedError("Subclasses must implement process_action")

class DecisionActionProcessor(ActionProcessor):
    """Processes decision and conditional actions"""
    
    def __init__(self, logger: FrameworkLogger, decision_engine: EnhancedDecisionEngine):
        super().__init__(logger)
        self.decision_engine = decision_engine
    
    def process_action(self, action_config: Dict[str, Any], 
                      context: Dict[str, Any]) -> Tuple[bool