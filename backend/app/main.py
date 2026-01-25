"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient 

from app.config import settings
from app.api.v1.router import api_router
from app.api.deps import set_mongo_client 

# Create FastAPI app
app = FastAPI(
    title="Odyssey-7 Game API",
    description="AI-powered narrative game backend",
    version="0.1.0",
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize connections on startup."""
    print("[Startup] Initializing MongoDB connection...")
    
    # Initialize MongoDB client
    mongo_client = AsyncIOMotorClient(settings.mongodb_uri)
    set_mongo_client(mongo_client)
    
    # Test connection
    try:
        await mongo_client.admin.command('ping')
        print(f"[Startup] MongoDB connected: {settings.mongodb_uri}")
    except Exception as e:
        print(f"[Startup] MongoDB connection failed: {e}")
        raise
    
    print("[Startup] Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    print("[Shutdown] Closing connections...")
    # MongoDB client cleanup happens automatically
    print("[Shutdown] Shutdown complete")


# Include API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "Odyssey-7 API is running",
        "environment": settings.app_env,
        "debug": settings.debug
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Odyssey-7 Game API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/health"
    }