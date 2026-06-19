import time
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, Response
from collections import defaultdict

logger = logging.getLogger("route-resilience.middleware")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        logger.info(f"Method: {request.method} | Path: {request.url.path} | "
                    f"Status: {response.status_code} | Time: {process_time*1000:.2f}ms")
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.client_records = defaultdict(list)

    async def dispatch(self, request: Request, call_next) -> Response:
        # Rate limit simulation
        client_ip = request.client.host if request.client else "unknown"
        
        # Skip health check from limiting
        if request.url.path == "/health":
            return await call_next(request)

        current_time = time.time()
        # Filter request timestamps in the last 60 seconds
        self.client_records[client_ip] = [t for t in self.client_records[client_ip] if current_time - t < 60]

        if len(self.client_records[client_ip]) >= self.requests_per_minute:
            return Response(
                content='{"detail": "Rate limit exceeded. Maximum 60 requests per minute allowed."}',
                status_code=429,
                media_type="application/json"
            )

        self.client_records[client_ip].append(current_time)
        return await call_next(request)
