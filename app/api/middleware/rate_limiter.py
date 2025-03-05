# app/api/middleware/rate_limiter.py
import time
from typing import Dict, Tuple, List, Optional
import logging
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("job_tracker.api.middleware.rate_limiter")

class RateLimiter(BaseHTTPMiddleware):
    def __init__(
        self, 
        app, 
        auth_limit: int = 5,      # 5 requests per minute for auth endpoints
        general_limit: int = 60,  # 60 requests per minute for other endpoints
        window: int = 60          # 1 minute window
    ):
        super().__init__(app)
        self.auth_limit = auth_limit
        self.general_limit = general_limit
        self.window = window
        self.auth_requests: Dict[str, List[float]] = {}
        self.general_requests: Dict[str, List[float]] = {}
        
        logger.info(f"Rate limiter initialized: {auth_limit} auth requests, {general_limit} general requests per {window} seconds")
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host if request.client else "unknown"
        path = request.url.path
        
        # Determine if this is an auth endpoint
        is_auth_endpoint = path.startswith("/api/auth/login") or path.startswith("/api/auth/register")
        limit = self.auth_limit if is_auth_endpoint else self.general_limit
        storage = self.auth_requests if is_auth_endpoint else self.general_requests
        
        # Check rate limit
        now = time.time()
        
        if client_ip not in storage:
            storage[client_ip] = []
        
        # Remove timestamps outside the window
        storage[client_ip] = [ts for ts in storage[client_ip] if now - ts < self.window]
        
        # Check if rate limit exceeded
        if len(storage[client_ip]) >= limit:
            endpoint_type = "authentication" if is_auth_endpoint else "API"
            logger.warning(f"Rate limit exceeded for {endpoint_type} endpoint by {client_ip}")
            
            # Calculate seconds to wait before next request
            oldest_request = min(storage[client_ip])
            wait_time = int(self.window - (now - oldest_request))
            
            return HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Please try again in {wait_time} seconds."
            ).response(request)
        
        # Add current timestamp
        storage[client_ip].append(now)
        
        # Process the request
        response = await call_next(request)
        return response
