#!/usr/bin/env python3
"""
Deployment-optimized main.py for SkillNavigator AI
Removes heavy ML dependencies for faster deployment
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global supervisor instance
supervisor_agent = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global supervisor_agent
    
    try:
        logger.info("Starting SkillNavigator backend...")
        
        # Initialize database
        from database.db_connection import Database
        database = Database()
        await database.initialize()
        logger.info("Database initialized successfully")
        
        # Initialize supervisor agent with simplified setup
        from agents.simple_supervisor_agent import SimpleSupervisorAgent
        supervisor_agent = SimpleSupervisorAgent()
        await supervisor_agent.initialize()
        logger.info("Simple supervisor agent initialized successfully")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        # Continue anyway for deployment
        yield
    finally:
        logger.info("Shutting down SkillNavigator backend...")
        if supervisor_agent:
            try:
                await supervisor_agent.cleanup()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")

# Create FastAPI app
app = FastAPI(
    title="SkillNavigator AI",
    description="AI-powered job application automation system",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment"""
    return {"status": "healthy", "message": "SkillNavigator AI is running"}

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Welcome to SkillNavigator AI",
        "version": "1.0.0",
        "status": "running"
    }

# Include routes
try:
    from routes import auth, jobs, tracker, supervisor
    
    app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
    app.include_router(jobs.router, prefix="/api/jobs", tags=["Jobs"])
    app.include_router(tracker.router, prefix="/api/tracker", tags=["Tracker"])
    app.include_router(supervisor.router, prefix="/api/supervisor", tags=["Supervisor"])
    
    logger.info("All routes loaded successfully")
    
except Exception as e:
    logger.error(f"Error loading routes: {e}")
    # Add minimal fallback routes
    
    @app.get("/api/jobs/")
    async def get_jobs():
        return {"jobs": [], "total": 0, "message": "System initializing"}
    
    @app.get("/api/supervisor/status")
    async def supervisor_status():
        return {
            "success": True,
            "auto_mode_enabled": False,
            "agents_status": {
                "scraper_agent": "initializing",
                "scoring_agent": "initializing",
                "autoapply_agent": "initializing"
            },
            "message": "System starting up"
        }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal server error", "detail": str(exc)}
    )

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "0.0.0.0")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level="info"
    )