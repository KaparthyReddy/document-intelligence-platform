from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import uvicorn

from config import settings
from database.mongodb import mongodb
from database.redis_cache import redis_client
from routes import register_routes

# Import ML models initialization
from models import initialize_models

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    
    print("🚀 Starting Document Intelligence Platform...")
    
    # Connect to databases
    print("📊 Connecting to MongoDB...")
    await mongodb.connect()
    
    print("🔴 Connecting to Redis...")
    await redis_client.connect()
    
    # Initialize ML models
    print("🤖 Loading ML models...")
    await initialize_models()
    
    print("✅ Application startup complete!")
    
    yield
    
    # Cleanup
    print("🔄 Shutting down...")
    await mongodb.close()
    await redis_client.close()
    print("✅ Shutdown complete!")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent document analysis with OCR, NER, and knowledge extraction",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if not settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Register routes
register_routes(app)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Document Intelligence Platform API",
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs"
    }

# Health check
@app.get("/health")
async def health_check():
    mongo_status = "connected" if mongodb.client else "disconnected"
    redis_status = "connected" if redis_client.is_connected else "disconnected"
    
    return {
        "status": "healthy",
        "mongodb": mongo_status,
        "redis": redis_status,
        "version": settings.APP_VERSION
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "error": str(exc) if settings.DEBUG else "An error occurred"
        }
    )

if __name__ == "__main__":
    print(f"""
    ╔══════════════════════════════════════════════════╗
    ║  Document Intelligence Platform - Backend API   ║
    ╚══════════════════════════════════════════════════╝
    
    📍 URL: http://{settings.HOST}:{settings.PORT}
    📚 Docs: http://{settings.HOST}:{settings.PORT}/docs
    🔧 Environment: {'Development' if settings.DEBUG else 'Production'}
    
    Press CTRL+C to stop
    """)
    
    uvicorn.run(
        "app:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
