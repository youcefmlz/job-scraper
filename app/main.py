from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging
import uvicorn
from app.config import settings
from app.database import create_tables
from app.api import jobs, users
from app.scheduler import JobScheduler
import threading
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = None
scheduler_thread = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting Job Scraper application...")
    
    # Create database tables
    create_tables()
    logger.info("Database tables created/verified")
    
    # Start scheduler in background thread
    global scheduler, scheduler_thread
    scheduler = JobScheduler()
    scheduler_thread = threading.Thread(target=scheduler.start, daemon=True)
    scheduler_thread.start()
    logger.info("Job scheduler started")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Job Scraper application...")
    if scheduler:
        scheduler.stop()
    if scheduler_thread and scheduler_thread.is_alive():
        scheduler_thread.join(timeout=5)
    logger.info("Application shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Job Scraper API",
    description="Automated job search monitoring tool using Firecrawl",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Job Scraper API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "scheduler_running": scheduler is not None and scheduler_thread and scheduler_thread.is_alive()
    }


@app.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status and next run times"""
    if not scheduler:
        raise HTTPException(status_code=503, detail="Scheduler not available")
    
    return {
        "scheduler_running": scheduler_thread and scheduler_thread.is_alive(),
        "next_run_times": scheduler.get_next_run_times()
    }


@app.post("/scheduler/start")
async def start_scheduler():
    """Manually start the scheduler"""
    global scheduler, scheduler_thread
    
    if scheduler_thread and scheduler_thread.is_alive():
        raise HTTPException(status_code=400, detail="Scheduler is already running")
    
    scheduler = JobScheduler()
    scheduler_thread = threading.Thread(target=scheduler.start, daemon=True)
    scheduler_thread.start()
    
    return {"message": "Scheduler started successfully"}


@app.post("/scheduler/stop")
async def stop_scheduler():
    """Manually stop the scheduler"""
    global scheduler, scheduler_thread
    
    if not scheduler or not scheduler_thread or not scheduler_thread.is_alive():
        raise HTTPException(status_code=400, detail="Scheduler is not running")
    
    scheduler.stop()
    scheduler_thread.join(timeout=5)
    
    return {"message": "Scheduler stopped successfully"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    ) 