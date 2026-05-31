import time
import threading
import sys
from logger_utils import get_logger

logger = get_logger("Timer", subdir="main")


class TimerDisplay:
    """Timer with live display + pause/resume support for user confirmation."""
    
    def __init__(self):
        self.reset()
    
    def start(self):
        """Start the timer and background display thread."""
        self.reset()
        self.start_time = time.time()
        self.is_running = True
        self.is_paused = False
        self.paused_time = None
        self.total_paused = 0.0
        
        self._thread = threading.Thread(target=self._update_timer, daemon=True)
        self._thread.start()
        logger.debug("Timer started with live display")
    
    def pause(self):
        """Pause timer (for user confirmation)."""
        if not self.is_paused and self.start_time is not None:
            self.paused_time = time.time()
            self.is_paused = True
            logger.debug("Timer paused")
    
    def resume(self):
        """Resume timer after pause."""
        if self.is_paused and self.paused_time is not None:
            paused_duration = time.time() - self.paused_time
            self.total_paused += paused_duration
            self.is_paused = False
            self.paused_time = None
            logger.debug("Timer resumed")
    
    def stop(self) -> float:
        """Stop timer, return total elapsed time (excluding paused time)."""
        if self.start_time is None:
            return 0.0
        
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        
        end_time = time.time()
        elapsed = end_time - self.start_time - self.total_paused
        
        if self.is_paused and self.paused_time:
            elapsed -= (end_time - self.paused_time)
        
        total_time = max(0.0, elapsed)
        self.reset()
        return total_time
    
    def _update_timer(self):
        """Background thread: Update live timer display."""
        while self.is_running:
            if self.is_paused:
                time.sleep(0.1)
                continue
                
            elapsed = time.time() - self.start_time - self.total_paused
            sys.stdout.write(f"\r⏳ Thinking... {elapsed:.1f}s")
            sys.stdout.flush()
            time.sleep(0.1)
    
    def reset(self):
        """Reset all timer states."""
        self.start_time = None
        self.is_running = False
        self.is_paused = False
        self.paused_time = None
        self.total_paused = 0.0
        self._thread = None