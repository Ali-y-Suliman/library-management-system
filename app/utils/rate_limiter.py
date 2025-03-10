import time
from typing import Dict
from fastapi import Request, HTTPException, status
from app.core.config import settings

# Simple in-memory rate limiter
# For production, use Redis or similar for distributed rate limiting


class RateLimiter:
    def __init__(self, requests_per_minute: int = settings.RATE_LIMIT_PER_MINUTE):
        self.requests_per_minute = requests_per_minute
        # IP -> timestamp -> count
        self.requests: Dict[str, Dict[float, int]] = {}

    def is_rate_limited(self, request: Request) -> bool:
        """Check if the request should be rate limited."""
        current_time = time.time()
        ip = request.client.host

        # Initialize if this is a new IP
        if ip not in self.requests:
            self.requests[ip] = {}

        # Clean up old entries (older than 1 minute)
        self.requests[ip] = {ts: count for ts, count in self.requests[ip].items()
                             if current_time - ts < 60}

        # Calculate current request count in the last minute
        request_count = sum(self.requests[ip].values())

        # Rate limit check
        if request_count >= self.requests_per_minute:
            return True

        # Record this request
        if current_time in self.requests[ip]:
            self.requests[ip][current_time] += 1
        else:
            self.requests[ip][current_time] = 1

        return False


rate_limiter = RateLimiter()


async def rate_limit_dependency(request: Request):
    """Dependency to check rate limiting for each request."""
    if rate_limiter.is_rate_limited(request):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    return True
