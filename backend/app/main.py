from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router

# Initialize FastAPI app
app = FastAPI(
    title="Odyssey-7 API",
    description="AI-powered space survival game backend for Google Gemini Hackathon",
    version="0.1.0",
    debug=settings.debug,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # TODO: Initialize MongoDB connection
    # from app.db.mongodb import init_mongodb
    # await init_mongodb(settings.mongodb_uri, settings.mongodb_db_name)

    # TODO: Initialize Redis connection
    # from app.db.redis_cache import init_redis
    # await init_redis(settings.redis_url)

    # TODO: Initialize dependencies (GameLoop, StateManager, GeminiClient)
    # from app.api.deps import init_dependencies
    # from app.db.mongodb import get_database
    # from app.db.redis_cache import get_redis
    # db = await get_database()
    # redis_cache = await get_redis()
    # await init_dependencies(db, redis_cache, settings.gemini_api_key)

    pass


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    # TODO: Close MongoDB connection
    # from app.db.mongodb import close_mongodb
    # await close_mongodb()

    # TODO: Close Redis connection
    # from app.db.redis_cache import close_redis
    # await close_redis()

    # TODO: Cleanup dependencies
    # from app.api.deps import cleanup_dependencies
    # await cleanup_dependencies()

    pass


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.

    Returns basic API information.
    """
    return {
        "message": "Odyssey-7 API",
        "status": "online",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.

    Returns API health status and environment info.
    """
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "debug": settings.debug
        # TODO: Add database health check
        # TODO: Add Redis health check
        # TODO: Add Gemini API health check
    }


# Include v1 API router
app.include_router(
    api_router,
    prefix="/api/v1"
)
