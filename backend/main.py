"""
SkillNavigator Backend - FastAPI Main Entry Point
AI-Powered Multi-Agent Job Application Platform
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import List

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from database.db_connection import Database
from agents.simple_supervisor_agent import SimpleSupervisorAgent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global supervisor agent instance
supervisor_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global supervisor_agent
    
    # Startup
    logger.info("Starting SkillNavigator backend...")
    
    # Initialize database
    try:
        database = Database()
        await database.initialize()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    # Initialize supervisor agent (using Windows-compatible HTTP-based version)
    supervisor_agent = None
    try:
        supervisor_agent = SimpleSupervisorAgent()
        await supervisor_agent.initialize()
        logger.info("Simple supervisor agent initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize supervisor agent: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down SkillNavigator backend...")
    if supervisor_agent:
        await supervisor_agent.cleanup()


# Create FastAPI application
app = FastAPI(
    title="SkillNavigator API",
    description="AI-Powered Multi-Agent Job Application Platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# CORS configuration - Allow all origins for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Include routers with safe imports
try:
    from routes import jobs
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])
    logger.info("Jobs router loaded successfully")
except ImportError as e:
    logger.warning(f"Jobs router not available: {e}")

try:
    from routes import tracker
    app.include_router(tracker.router, prefix="/api/tracker", tags=["tracker"])
    logger.info("Tracker router loaded successfully")
except ImportError as e:
    logger.warning(f"Tracker router not available: {e}")

try:
    from routes import user
    app.include_router(user.router, prefix="/api/user", tags=["user"])
    logger.info("User router loaded successfully")
except ImportError as e:
    logger.warning(f"User router not available: {e}")

try:
    from routes import supervisor
    app.include_router(supervisor.router)  # No prefix needed, already defined in router
    logger.info("Supervisor router loaded successfully")
except ImportError as e:
    logger.warning(f"Supervisor router not available: {e}")

try:
    from routes import auto_apply
    app.include_router(auto_apply.router, prefix="/api/auto-apply", tags=["auto-apply"])
    logger.info("Auto-apply router loaded successfully")
except ImportError as e:
    logger.warning(f"Auto-apply router not available: {e}")

# Serve static files (only if directory exists)
try:
    if os.path.exists("../public"):
        app.mount("/static", StaticFiles(directory="../public"), name="static")
        logger.info("Static files mounted successfully")
    else:
        logger.info("Public directory not found - skipping static file serving")
except Exception as e:
    logger.warning(f"Could not mount static files: {e}")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "SkillNavigator API",
        "version": "1.0.0",
        "description": "AI-Powered Multi-Agent Job Application Platform",
        "docs": "/docs",
        "status": "running"
    }

@app.head("/")
async def root_head():
    """HEAD request handler for deployment health checks"""
    return {}


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check database connection
        database = Database()
        db_status = await database.health_check()
        
        # Check supervisor agent
        agent_status = supervisor_agent is not None and supervisor_agent.is_healthy()
        
        return {
            "status": "healthy" if db_status and agent_status else "unhealthy",
            "database": "connected" if db_status else "disconnected",
            "supervisor_agent": "running" if agent_status else "stopped",
            "timestamp": "2025-01-01T00:00:00Z"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unavailable")


@app.get("/api/status")
async def get_system_status():
    """Get detailed system status"""
    if not supervisor_agent:
        raise HTTPException(status_code=503, detail="Supervisor agent not initialized")
    
    try:
        status = await supervisor_agent.get_system_status()
        return status
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


@app.post("/api/trigger-job-search")
async def trigger_job_search(search_params: dict):
    """Trigger manual job search via supervisor agent"""
    if not supervisor_agent:
        raise HTTPException(status_code=503, detail="Supervisor agent not initialized")
    
    try:
        result = await supervisor_agent.trigger_job_search(search_params)
        return result
    except Exception as e:
        logger.error(f"Failed to trigger job search: {e}")
        raise HTTPException(status_code=500, detail="Failed to trigger job search")


@app.post("/api/start-auto-mode")
async def start_auto_mode():
    """Start automated job search mode"""
    if not supervisor_agent:
        raise HTTPException(status_code=503, detail="Supervisor agent not initialized")
    
    try:
        result = await supervisor_agent.start_auto_mode()
        return {"message": "Auto mode started successfully", "result": result}
    except Exception as e:
        logger.error(f"Failed to start auto mode: {e}")
        raise HTTPException(status_code=500, detail="Failed to start auto mode")


@app.post("/api/stop-auto-mode")
async def stop_auto_mode():
    """Stop automated job search mode"""
    if not supervisor_agent:
        raise HTTPException(status_code=503, detail="Supervisor agent not initialized")
    
    try:
        result = await supervisor_agent.stop_auto_mode()
        return {"message": "Auto mode stopped successfully", "result": result}
    except Exception as e:
        logger.error(f"Failed to stop auto mode: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop auto mode")


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={"error": "Endpoint not found", "path": str(request.url.path)}
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Custom 500 handler"""
    from fastapi.responses import JSONResponse
    logger.error(f"Internal server error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "detail": str(exc)}
    )


if __name__ == "__main__":
    # Production/Development server
    host = os.getenv("HOST", "0.0.0.0")  # Default to 0.0.0.0 for deployment
    port = int(os.getenv("PORT", 8000))
    debug = os.getenv("DEBUG", "false").lower() == "true"  # Default to false for production
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=debug,
        log_level=os.getenv("LOG_LEVEL", "info").lower()
    )
