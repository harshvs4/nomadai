from services.cache_service import get_cache_service, initialize_cache_service
import logging
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import settings
from routers import travel, auth, user
from models.database import init_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# FastAPI startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database
    logger.info("Initializing application...")
    await init_db()
    logger.info("Database initialized")
    await initialize_cache_service()
    logger.info("Cache service initialized")
    
    yield
    
    # Shutdown: cleanup resources
    logger.info("Shutting down application...")
    # Get cache service and stop it
    cache_service = get_cache_service()
    await cache_service.stop()
    logger.info("Cache service stopped")

# Create FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="NomadAI: Intelligent Travel Planning API",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(user.router, prefix=f"{settings.API_V1_STR}/users", tags=["Users"])
app.include_router(travel.router, prefix=f"{settings.API_V1_STR}/travel", tags=["Travel"])

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Health check endpoint."""
    return {
        "status": "online",
        "name": settings.PROJECT_NAME,
        "message": "Welcome to the NomadAI Travel Planning API!",
        "docs": "/docs",
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)