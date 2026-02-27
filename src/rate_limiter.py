import time
from functools import wraps

class RateLimiter:
    def __init__(self, max_calls=10, period=60):
        """
        max_calls: Maximum API calls allowed
        period: Time period in seconds (default 60 = 1 minute)
        """
        self.max_calls = max_calls
        self.period = period
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if we're at the rate limit"""
        now = time.time()
        
        # Remove old calls outside the time window
        self.calls = [call_time for call_time in self.calls 
                     if now - call_time < self.period]
        
        # If at limit, wait
        if len(self.calls) >= self.max_calls:
            sleep_time = self.period - (now - self.calls[0]) + 1
            print(f"⏳ Rate limit reached. Waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
            self.calls = []
        
        # Record this call
        self.calls.append(now)

# Create global rate limiter
api_limiter = RateLimiter(max_calls=9, period=60)  # Stay under 10/min

def rate_limited(func):
    """Decorator to rate limit API calls"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_limiter.wait_if_needed()
        return func(*args, **kwargs)
    return wrapper