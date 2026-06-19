from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import logging

from api.routers import cities, network, analysis, routing, export
from api.middleware import RateLimitMiddleware, RequestLoggingMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("route-resilience")

app = FastAPI(
    title="Route Resilience API",
    description="ISRO Urban Infrastructure Resilience Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Middleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)

# Routers
app.include_router(cities.router, prefix="/api/v1/cities", tags=["Cities"])
app.include_router(network.router, prefix="/api/v1/network", tags=["Network"])
app.include_router(analysis.router, prefix="/api/v1/analysis", tags=["Analysis"])
app.include_router(routing.router, prefix="/api/v1/routing", tags=["Routing"])
app.include_router(export.router, prefix="/api/v1/export", tags=["Export"])

@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}

@app.get("/api/v1/")
async def api_root():
    return {"message": "Route Resilience API v1", "docs": "/docs"}
