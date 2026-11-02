"""Lightweight in-memory sliding window rate limiter with no external dependencies."""
import time
from collections import defaultdict
from fastapi import Request, HTTPException

class InMemoryRateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def check(self, request: Request):
        # Identify client by IP
        client_ip = request.client.host if request.client else '127.0.0.1'
        now = time.time()
        
        # Clean timestamps older than window
        timestamps = self.requests[client_ip]
        cutoff = now - self.window_seconds
        while timestamps and timestamps[0] < cutoff:
            timestamps.pop(0)
            
        if len(timestamps) >= self.max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Quá nhiều yêu cầu. Giới hạn tối đa {self.max_requests} yêu cầu mỗi phút. Vui lòng thử lại sau."
            )
            
        timestamps.append(now)

limiter = InMemoryRateLimiter(max_requests=60, window_seconds=60)
