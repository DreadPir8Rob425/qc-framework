# Option Alpha Framework - Event System
# Publisher/Subscriber event system for framework components

import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import uuid
import time

from oa_framework_enums import *
from oa_data_structures import Event
from oa_logging import FrameworkLogger, LogCategory, LogLevel



# =============================================================================
# EVENT HANDLER INTERFACE
# =============================================================================

class EventHandler(ABC):
    """Abstract base class for event handlers"""
    
    def __init__(self, name: Optional[str] = None):
        self.name = name or self.__class__.__name__
        self.handler_id = str(uuid.uuid4())
        self._enabled = True
        self._processed_count = 0
        self._error_count = 0
        self._last_processed = None
    
    @abstractmethod
    def handle_event(self, event: Event) -> None:
        """Handle an event - must be implemented by subclasses"""
        pass
    
    @abstractmethod
    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler can process the event type"""
        pass
    
    def enable(self) -> None:
        """Enable the event handler"""
        self._enabled = True
    
    def disable(self) -> None:
        """Disable the event handler"""
        self._enabled = False
    
    @property
    def is_enabled(self) -> bool:
        """Check if handler is enabled"""
        return self._enabled
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get handler statistics"""
        return {
            'name': self.name,
            'handler_id': self.handler_id,
            'enabled': self._enabled,
            'processed_count': self._processed_count,
            'error_count': self._error_count,
            'last_processed': self._last_processed.isoformat() if self._last_processed else None
        }
    
    def _record_processing(self, success: bool = True) -> None:
        """Record event processing statistics"""
        self._processed_count += 1
        self._last_processed = datetime.now()
        if not success:
            self._error_count += 1

# =============================================================================
# SPECIALIZED EVENT HANDLERS
# =============================================================================

class FunctionHandler(EventHandler):
    """Event handler that wraps a function"""
    
    def __init__(self, event_types: List[EventType], handler_func: Callable[[Event], None], 
                 name: Optional[str] = None):
        super().__init__(name)
        self.event_types = set(event_types)
        self.handler_func = handler_func
    
    def handle_event(self, event: Event) -> None:
        """Handle event by calling the wrapped function"""
        if not self._enabled:
            return
        
        try:
            self.handler_func(event)
            self._record_processing(True)
        except Exception as e:
            self._record_processing(False)
            raise
    
    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler can process the event type"""
        return event_type in self.event_types

class ConditionalHandler(EventHandler):
    """Event handler that only processes events meeting certain conditions"""
    
    def __init__(self, event_types: List[EventType], handler_func: Callable[[Event], None],
                 condition_func: Callable[[Event], bool], name: Optional[str] = None):
        super().__init__(name)
        self.event_types = set(event_types)
        self.handler_func = handler_func
        self.condition_func = condition_func
    
    def handle_event(self, event: Event) -> None:
        """Handle event if condition is met"""
        if not self._enabled:
            return
        
        try:
            if self.condition_func(event):
                self.handler_func(event)
            self._record_processing(True)
        except Exception as e:
            self._record_processing(False)
            raise
    
    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler can process the event type"""
        return event_type in self.event_types

class LoggingHandler(EventHandler):
    """Event handler that logs events"""
    
    def __init__(self, logger: FrameworkLogger, event_types: Optional[List[EventType]] = None,
                 log_level: LogLevel = LogLevel.INFO):
        super().__init__("LoggingHandler")
        self.logger = logger
        self.event_types = set(event_types) if event_types else set(EventType)
        self.log_level = log_level
    
    def handle_event(self, event: Event) -> None:
        """Log the event"""
        if not self._enabled:
            return
        
        try:
            self.logger.log(
                self.log_level,
                LogCategory.SYSTEM,
                f"Event: {event.event_type}",
                source=event.source,
                event_data=event.data
            )
            self._record_processing(True)
        except Exception as e:
            self._record_processing(False)
            raise
    
    def can_handle(self, event_type: EventType) -> bool:
        """Check if this handler can process the event type"""
        return EventType(event_type) in self.event_types

# =============================================================================
# EVENT BUS
# =============================================================================

class EventBus:
    """Central event bus for publishing and subscribing to events"""
    
    def __init__(self, max_queue_size: int = 10000, max_workers: int = 5):
        self.max_queue_size = max_queue_size
        self.max_workers = max_workers
        
        # Handler storage
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._all_handlers: Dict[str, EventHandler] = {}
        
        # Event processing
        self._event_queue = queue.PriorityQueue(maxsize=max_queue_size)
        self._processing = False
        self._worker_threads: List[threading.Thread] = []
        
        # Statistics
        self._events_published = 0
        self._events_processed = 0
        self._events_dropped = 0
        self._start_time = datetime.now()
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Logging
        self.logger = FrameworkLogger("EventBus")
        
        self.logger.info(LogCategory.SYSTEM, "Event bus initialized",
                        max_queue_size=max_queue_size, max_workers=max_workers)
    
    def _process_events(self) -> None:
        """Process events from the queue"""
        while self._processing:
            try:
                # Get event from queue with timeout
                priority, timestamp, event = self._event_queue.get(timeout=1)
                
                # Convert event_type string to EventType enum if needed
                if isinstance(event.event_type, str):
                    event_type = EventType(event.event_type)
                else:
                    event_type = event.event_type
                
                # Dispatch the event
                self._dispatch_event(event, event_type)
                
                # Mark task as done
                self._event_queue.task_done()
                
                # Update statistics
                with self._lock:
                    self._events_processed += 1
                    
            except queue.Empty:
                # Timeout occurred, continue loop
                continue
            except Exception as e:
                self.logger.error(LogCategory.SYSTEM, "Error processing event", error=str(e))
                continue

    def _dispatch_event(self, event: Event, event_type: EventType) -> None:
        """Dispatch event to appropriate handlers"""
        if isinstance(event_type, str):
            try:
                from oa_framework_enums import EventType
                event_type = EventType(event_type)
            except ValueError:
                self.logger.error(LogCategory.SYSTEM, f"Unknown event type string: {event_type}")
                return
        
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                if handler.can_handle(event_type):
                    handler.handle_event(event)
            except Exception as e:
                self.logger.error(LogCategory.SYSTEM, f"Error in handler {handler.name}: {str(e)}")
            
    def subscribe(self, event_type: EventType, handler: EventHandler) -> str:
        """Subscribe a handler to an event type"""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            
            self._handlers[event_type].append(handler)
            self._all_handlers[handler.handler_id] = handler
            
            self.logger.debug(LogCategory.SYSTEM, "Handler subscribed",
                            event_type=event_type.value, handler_name=handler.name)
            
            return handler.handler_id
    
    def unsubscribe(self, event_type: EventType, handler_id: str) -> bool:
        """Unsubscribe a handler from an event type"""
        with self._lock:
            if event_type in self._handlers:
                handlers = self._handlers[event_type]
                for i, handler in enumerate(handlers):
                    if handler.handler_id == handler_id:
                        handlers.pop(i)
                        self._all_handlers.pop(handler_id, None)
                        
                        self.logger.debug(LogCategory.SYSTEM, "Handler unsubscribed",
                                        event_type=event_type.value, handler_id=handler_id)
                        return True
            
            return False
    
    def subscribe_function(self, event_types: List[EventType], 
                          handler_func: Callable[[Event], None],
                          name: Optional[str] = None) -> str:
        """Subscribe a function to handle events"""
        handler = FunctionHandler(event_types, handler_func, name)
        
        # Subscribe to all specified event types
        for event_type in event_types:
            self.subscribe(event_type, handler)
        
        return handler.handler_id
    
    def subscribe_conditional(self, event_types: List[EventType],
                            handler_func: Callable[[Event], None],
                            condition_func: Callable[[Event], bool],
                            name: Optional[str] = None) -> str:
        """Subscribe a conditional handler"""
        handler = ConditionalHandler(event_types, handler_func, condition_func, name)
        
        # Subscribe to all specified event types
        for event_type in event_types:
            self.subscribe(event_type, handler)
        
        return handler.handler_id
    
    def publish(self, event: Event) -> bool:
        """Publish an event to the bus"""
        try:
            # Create priority queue item (lower number = higher priority)
            priority = -event.priority if hasattr(event, 'priority') else 0
            queue_item = (priority, time.time(), event)
            
            # Try to add to queue
            self._event_queue.put_nowait(queue_item)
            
            with self._lock:
                self._events_published += 1
            
            self.logger.debug(LogCategory.SYSTEM, "Event published",
                            event_type=event.event_type, source=event.source)
            
            return True
            
        except queue.Full:
            with self._lock:
                self._events_dropped += 1
            
            self.logger.warning(LogCategory.SYSTEM, "Event queue full, dropping event",
                              event_type=event.event_type)
            return False
        
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to publish event",
                            event_type=event.event_type, error=str(e))
            return False
    
    def publish_sync(self, event: Event) -> None:
        """Publish and process an event synchronously"""
        try:
            event_type = EventType(event.event_type)
            self._dispatch_event(event, event_type)
            
            with self._lock:
                self._events_published += 1
                self._events_processed += 1
            
        except Exception as e:
            self.logger.error(LogCategory.SYSTEM, "Failed to process sync event",
                            event_type=event.event_type, error=str(e))
            raise
    
    def start_processing(self) -> None:
        """Start background event processing"""
        if self._processing:
            return
        
        self._processing = True
        
        # Start worker threads
        for i in range(self.max_workers):
            thread = threading.Thread(
                target=self._process_events,
                name=f"EventWorker-{i}",
                daemon=True
            )
            thread.start()
            self._worker_threads.append(thread)
        
        self.logger.info(LogCategory.SYSTEM, "Event processing started",
                        worker_count=len(self._worker_threads))
    
    def stop_processing(self, timeout: float = 5.0) -> None:
        """Stop background event processing"""
        if not self._processing:
            return