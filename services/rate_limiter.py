# services/rate_limiter.py
import asyncio
import time
from functools import wraps

class RateLimiter:
    def __init__(self, max_calls=10, time_window=60):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def can_make_call(self):
        now = time.time()
        # Remove old calls outside time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        return len(self.calls) < self.max_calls
    
    def record_call(self):
        self.calls.append(time.time())

# Global rate limiter for Groq
groq_limiter = RateLimiter(max_calls=8, time_window=60)  # Conservative limit

async def groq_call_with_retry(client, messages, model="llama-3.1-8b-instant", max_retries=3):
    """Groq API call with automatic retry and rate limiting"""
    
    for attempt in range(max_retries):
        try:
            # Check rate limit
            if not groq_limiter.can_make_call():
                print(f"Rate limit reached, waiting 10 seconds...")
                await asyncio.sleep(10)
                continue
            
            # Make the call
            response = client.chat.completions.create(
                messages=messages,
                model=model,
                max_tokens=600,  # Reduced from 200-400
                temperature=0.1,
            )
            
            groq_limiter.record_call()
            return response.choices[0].message.content
            
        except Exception as e:
            error_str = str(e)
            if "rate_limit_exceeded" in error_str:
                # Extract wait time from error message
                import re
                wait_match = re.search(r'try again in (\d+\.?\d*)s', error_str)
                wait_time = float(wait_match.group(1)) if wait_match else 15
                
                print(f"Rate limit hit, waiting {wait_time + 2} seconds...")
                await asyncio.sleep(wait_time + 2)
                continue
            else:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    return f"Error after {max_retries} attempts: {str(e)}"
                await asyncio.sleep(2)
    
    return "Failed after all retry attempts"