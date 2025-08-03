#!/usr/bin/env python3
"""
Job Scraper - Test Setup Script

This script tests the basic functionality of the Job Scraper to ensure everything is working correctly.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_imports():
    """Test that all required modules can be imported"""
    print("Testing imports...")
    
    try:
        from app.config import settings
        print("✓ Config imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import config: {e}")
        return False
    
    try:
        from app.database import create_tables, get_db
        print("✓ Database modules imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import database modules: {e}")
        return False
    
    try:
        from app.models import JobSearchRequest, UserCreate
        print("✓ Models imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import models: {e}")
        return False
    
    try:
        from app.services.job_service import JobService
        print("✓ Job service imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import job service: {e}")
        return False
    
    try:
        from app.scrapers.scraper_factory import ScraperFactory
        print("✓ Scraper factory imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import scraper factory: {e}")
        return False
    
    return True


def test_database():
    """Test database connection and table creation"""
    print("\nTesting database...")
    
    try:
        from app.database import create_tables, engine
        from sqlalchemy import text
        create_tables()
        print("✓ Database tables created successfully")
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            print("✓ Database connection successful")
        
        return True
    except Exception as e:
        print(f"✗ Database test failed: {e}")
        return False


def test_config():
    """Test configuration loading"""
    print("\nTesting configuration...")
    
    try:
        from app.config import settings
        
        # Check required settings
        required_settings = [
            'database_url',
            'secret_key',
            'host',
            'port',
            'scrape_interval_minutes'
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                print(f"✓ {setting} configured")
            else:
                print(f"✗ {setting} not configured")
                return False
        
        print("✓ Configuration loaded successfully")
        return True
    except Exception as e:
        print(f"✗ Configuration test failed: {e}")
        return False


def test_scrapers():
    """Test scraper initialization"""
    print("\nTesting scrapers...")
    
    try:
        from app.scrapers.scraper_factory import ScraperFactory
        
        factory = ScraperFactory()
        available_scrapers = factory.get_available_scrapers()
        
        if available_scrapers:
            print(f"✓ {len(available_scrapers)} scrapers available: {', '.join(available_scrapers)}")
        else:
            print("⚠️  No scrapers available (check configuration)")
        
        return True
    except Exception as e:
        print(f"✗ Scraper test failed: {e}")
        return False


def test_services():
    """Test service initialization"""
    print("\nTesting services...")
    
    try:
        from app.services.job_service import JobService
        from app.services.notification_service import NotificationService
        
        job_service = JobService()
        notification_service = NotificationService()
        
        print("✓ Services initialized successfully")
        return True
    except Exception as e:
        print(f"✗ Service test failed: {e}")
        return False


def test_api_routes():
    """Test API route registration"""
    print("\nTesting API routes...")
    
    try:
        from app.main import app
        
        # Check if routes are registered
        routes = [route.path for route in app.routes]
        
        expected_routes = [
            '/',
            '/health',
            '/docs',
            '/openapi.json'
        ]
        
        for route in expected_routes:
            if route in routes:
                print(f"✓ Route {route} registered")
            else:
                print(f"✗ Route {route} not found")
        
        print("✓ API routes registered successfully")
        return True
    except Exception as e:
        print(f"✗ API route test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("🧪 Job Scraper Setup Test")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Configuration Test", test_config),
        ("Database Test", test_database),
        ("Scraper Test", test_scrapers),
        ("Service Test", test_services),
        ("API Routes Test", test_api_routes)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"✗ {test_name} failed")
    
    print("\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("✅ All tests passed! The Job Scraper is ready to use.")
        print("\nTo start the application:")
        print("python run.py")
    else:
        print("❌ Some tests failed. Please check the configuration and dependencies.")
        print("\nCommon issues:")
        print("1. Make sure all dependencies are installed: pip install -r requirements.txt")
        print("2. Check your .env file configuration")
        print("3. Ensure you have a valid Firecrawl API key")
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 