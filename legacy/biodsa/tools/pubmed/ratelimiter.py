import time
import threading
from collections import deque

class RateLimiter:
    """Thread-safe rate limiter to control API request frequency."""
    
    def __init__(self, max_requests_per_second: float = 3.0):
        self.max_requests_per_second = max_requests_per_second
        self.min_interval = 1.0 / max_requests_per_second
        self.last_request_times = deque()
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if necessary to respect the rate limit."""
        with self.lock:
            now = time.time()
            
            # Remove old request times (older than 1 second)
            while self.last_request_times and now - self.last_request_times[0] >= 1.0:
                self.last_request_times.popleft()
            
            # If we've made too many requests in the last second, wait
            if len(self.last_request_times) >= self.max_requests_per_second:
                sleep_time = 1.0 - (now - self.last_request_times[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    now = time.time()
                    # Clean up old times again after waiting
                    while self.last_request_times and now - self.last_request_times[0] >= 1.0:
                        self.last_request_times.popleft()
            
            # Record this request time
            self.last_request_times.append(now)