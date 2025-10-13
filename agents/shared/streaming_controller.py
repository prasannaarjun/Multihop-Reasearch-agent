"""
Streaming Controller for managing streaming operations with stop/pause functionality.
"""

import threading
import time
from typing import Optional, Generator, Any
import logging

logger = logging.getLogger(__name__)


class StreamingController:
    """Controller for managing streaming operations with stop/pause functionality."""
    
    def __init__(self):
        self.stop_flag = threading.Event()
        self.pause_flag = threading.Event()
        self.is_paused = False
        self.request_id: Optional[str] = None
        # Owner of this request (user id); used for authorization on stop
        self.owner_user_id: Optional[int] = None
    
    def stop(self):
        """Stop the streaming operation."""
        self.stop_flag.set()
        logger.debug(f"Streaming stopped for request {self.request_id}")
    
    def pause(self):
        """Pause the streaming operation."""
        self.pause_flag.set()
        self.is_paused = True
        logger.debug(f"Streaming paused for request {self.request_id}")
    
    def resume(self):
        """Resume the streaming operation."""
        self.pause_flag.clear()
        self.is_paused = False
        logger.debug(f"Streaming resumed for request {self.request_id}")
    
    def reset(self):
        """Reset all flags for new operation."""
        self.stop_flag.clear()
        self.pause_flag.clear()
        self.is_paused = False
        self.request_id = None
        logger.debug("Streaming controller reset")
    
    def is_stopped(self) -> bool:
        """Check if streaming is stopped."""
        return self.stop_flag.is_set()
    
    def is_paused(self) -> bool:
        """Check if streaming is paused."""
        return self.pause_flag.is_set()


def streaming_generator_with_control(base_generator: Generator[str, None, None], 
                                   controller: StreamingController) -> Generator[str, None, None]:
    """
    Wrapper generator that adds stop/pause control to any streaming generator.
    
    Args:
        base_generator: The base streaming generator
        controller: StreamingController instance
        
    Yields:
        Chunks from base generator with stop/pause control
    """
    try:
        for chunk in base_generator:
            # Check for stop signal
            if controller.is_stopped():
                logger.debug(f"Streaming stopped for request {controller.request_id}")
                break
            
            # Handle pause/resume
            while controller.is_paused() and not controller.is_stopped():
                time.sleep(0.1)  # Small delay while paused
            
            # Check for stop signal after pause
            if controller.is_stopped():
                logger.debug(f"Streaming stopped after pause for request {controller.request_id}")
                break
            
            yield chunk
            
    except Exception as e:
        logger.error(f"Error in streaming generator: {e}")
        yield f"Error: {str(e)}"
    finally:
        logger.debug(f"Streaming generator completed for request {controller.request_id}")


class StreamingManager:
    """Global manager for streaming controllers."""
    
    def __init__(self):
        self.controllers: dict[str, StreamingController] = {}
        self._lock = threading.Lock()
    
    def create_controller(self, request_id: str) -> StreamingController:
        """Create a new streaming controller for a request."""
        with self._lock:
            controller = StreamingController()
            controller.request_id = request_id
            self.controllers[request_id] = controller
            logger.debug(f"Created streaming controller for request {request_id}")
            return controller
    
    def get_controller(self, request_id: str) -> Optional[StreamingController]:
        """Get a streaming controller by request ID."""
        with self._lock:
            return self.controllers.get(request_id)
    
    def stop_controller(self, request_id: str) -> bool:
        """Stop a streaming controller by request ID."""
        with self._lock:
            controller = self.controllers.get(request_id)
            if controller:
                controller.stop()
                logger.debug(f"Stopped streaming controller for request {request_id}")
                return True
            return False
    
    def pause_controller(self, request_id: str) -> bool:
        """Pause a streaming controller by request ID."""
        with self._lock:
            controller = self.controllers.get(request_id)
            if controller:
                controller.pause()
                logger.debug(f"Paused streaming controller for request {request_id}")
                return True
            return False
    
    def resume_controller(self, request_id: str) -> bool:
        """Resume a streaming controller by request ID."""
        with self._lock:
            controller = self.controllers.get(request_id)
            if controller:
                controller.resume()
                logger.debug(f"Resumed streaming controller for request {request_id}")
                return True
            return False
    
    def remove_controller(self, request_id: str) -> bool:
        """Remove a streaming controller by request ID."""
        with self._lock:
            if request_id in self.controllers:
                del self.controllers[request_id]
                logger.debug(f"Removed streaming controller for request {request_id}")
                return True
            return False
    
    def cleanup_expired_controllers(self, max_age_seconds: int = 300):
        """Clean up controllers that have been inactive for too long."""
        with self._lock:
            current_time = time.time()
            expired_controllers = []
            
            for request_id, controller in self.controllers.items():
                # This is a simple cleanup - in production you might want to track creation time
                if controller.is_stopped():
                    expired_controllers.append(request_id)
            
            for request_id in expired_controllers:
                del self.controllers[request_id]
                logger.debug(f"Cleaned up expired controller for request {request_id}")


# Global streaming manager instance
streaming_manager = StreamingManager()
