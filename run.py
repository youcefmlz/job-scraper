#!/usr/bin/env python3
"""
Job Scraper - Run Script

This script provides an easy way to run the Job Scraper application.
"""

import uvicorn
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.database import create_tables


def main():
    """Main entry point for the application"""
    
    # Create database tables
    print("Initializing database...")
    create_tables()
    print("Database initialized successfully!")
    
    # Start the application
    print(f"Starting Job Scraper on {settings.host}:{settings.port}")
    print(f"API Documentation: http://{settings.host}:{settings.port}/docs")
    print(f"Health Check: http://{settings.host}:{settings.port}/health")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )


if __name__ == "__main__":
    main() 