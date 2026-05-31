import time
import threading
import sys
class TimerDisplay:
    """Dynamic timer display for command-line applications."""
    
    def __init__(self):
        self.start_time = None
        self.is_running = False
        self.stop_event = threading.Event()
    
    def start(self):
        """Start the timer."""
        self.start_time = time.time()
        self.is_running = True
        self.stop_event.clear()
        
        thread = threading.Thread(target=self._update_timer, daemon=True)
        thread.start()
    
    def _update_timer(self):
        """Update the timer display in the background."""
        while self.is_running and not self.stop_event.is_set():
            elapsed = time.time() - self.start_time
            # \r returns the cursor to the start of the line, allowing us to overwrite it
            sys.stdout.write(f"\r⏳ Thinking... {elapsed:.1f}s")
            sys.stdout.flush()
            time.sleep(0.1)
    
    def stop(self):
        """Stop the timer and return the total elapsed time."""
        self.is_running = False
        self.stop_event.set()
        time.sleep(0.2)
        elapsed = time.time() - self.start_time
        
        # Clear the line and move to the next line
        sys.stdout.write("\r" + " " * 40 + "\r")
        sys.stdout.flush()
        
        return elapsed