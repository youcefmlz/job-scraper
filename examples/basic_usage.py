#!/usr/bin/env python3
"""
Job Scraper - Basic Usage Example

This script demonstrates how to use the Job Scraper API for common operations.
"""

import requests
import json
import time
from typing import Dict, Any


class JobScraperClient:
    """Simple client for the Job Scraper API"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
    
    def create_user(self, email: str, name: str) -> Dict[str, Any]:
        """Create a new user"""
        url = f"{self.base_url}/api/v1/users/"
        data = {
            "email": email,
            "name": name
        }
        response = self.session.post(url, json=data)
        response.raise_for_status()
        return response.json()
    
    def create_search_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a search profile for a user"""
        url = f"{self.base_url}/api/v1/users/{user_id}/profiles"
        response = self.session.post(url, json=profile_data)
        response.raise_for_status()
        return response.json()
    
    def search_jobs(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Search for jobs"""
        url = f"{self.base_url}/api/v1/jobs/search"
        response = self.session.post(url, json=search_data)
        response.raise_for_status()
        return response.json()
    
    def scrape_jobs(self, search_data: Dict[str, Any]) -> Dict[str, Any]:
        """Manually trigger job scraping"""
        url = f"{self.base_url}/api/v1/jobs/scrape"
        response = self.session.post(url, json=search_data)
        response.raise_for_status()
        return response.json()
    
    def get_job_statistics(self) -> Dict[str, Any]:
        """Get job statistics"""
        url = f"{self.base_url}/api/v1/jobs/statistics/summary"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_recent_jobs(self, limit: int = 10) -> Dict[str, Any]:
        """Get recent jobs"""
        url = f"{self.base_url}/api/v1/jobs/recent?limit={limit}"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get application health status"""
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        response.raise_for_status()
        return response.json()


def main():
    """Demonstrate basic usage of the Job Scraper API"""
    print("🚀 Job Scraper - Basic Usage Example")
    print("=" * 50)
    
    # Initialize client
    client = JobScraperClient()
    
    try:
        # Check if the API is running
        print("1. Checking API health...")
        health = client.get_health_status()
        print(f"✓ API Status: {health['status']}")
        print(f"✓ Scheduler Running: {health['scheduler_running']}")
        
        # Get job statistics
        print("\n2. Getting job statistics...")
        stats = client.get_job_statistics()
        print(f"✓ Total Jobs: {stats.get('total_jobs', 0)}")
        print(f"✓ Jobs by Site: {stats.get('jobs_by_site', {})}")
        print(f"✓ Recent Jobs (24h): {stats.get('recent_jobs_24h', 0)}")
        
        # Create a user
        print("\n3. Creating a test user...")
        user_data = {
            "email": "test@example.com",
            "name": "Test User"
        }
        user = client.create_user(**user_data)
        print(f"✓ User created with ID: {user['id']}")
        
        # Create a search profile
        print("\n4. Creating a search profile...")
        profile_data = {
            "name": "Python Developer",
            "keywords": ["python", "django", "fastapi"],
            "location": "San Francisco",
            "job_type": "remote",
            "experience_level": "mid",
            "salary_min": 80000,
            "salary_max": 150000
        }
        profile = client.create_search_profile(user['id'], profile_data)
        print(f"✓ Profile created with ID: {profile['id']}")
        
        # Search for jobs
        print("\n5. Searching for jobs...")
        search_data = {
            "keywords": ["python", "developer"],
            "location": "San Francisco",
            "job_type": "remote",
            "experience_level": "mid",
            "salary_min": 80000,
            "salary_max": 150000,
            "limit": 5,
            "offset": 0
        }
        jobs = client.search_jobs(search_data)
        print(f"✓ Found {len(jobs)} jobs")
        
        if jobs:
            print("Sample jobs:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"  {i}. {job['title']} at {job['company']} ({job['location']})")
        
        # Manually trigger scraping
        print("\n6. Triggering manual job scraping...")
        scrape_data = {
            "keywords": ["python", "developer"],
            "location": "San Francisco",
            "job_type": "remote",
            "experience_level": "mid"
        }
        scrape_result = client.scrape_jobs(scrape_data)
        print(f"✓ Scraping completed")
        print(f"  - Jobs found: {scrape_result['total_jobs_found']}")
        print(f"  - New jobs: {scrape_result['total_jobs_new']}")
        print(f"  - Updated jobs: {scrape_result['total_jobs_updated']}")
        print(f"  - Sites scraped: {', '.join(scrape_result['sites_scraped'])}")
        
        # Get recent jobs
        print("\n7. Getting recent jobs...")
        recent_jobs = client.get_recent_jobs(limit=3)
        print(f"✓ Found {len(recent_jobs)} recent jobs")
        
        if recent_jobs:
            print("Recent jobs:")
            for i, job in enumerate(recent_jobs, 1):
                print(f"  {i}. {job['title']} at {job['company']}")
                print(f"     Location: {job['location']}")
                print(f"     Source: {job['source_site']}")
                print(f"     Posted: {job['posted_date']}")
                print()
        
        print("✅ All operations completed successfully!")
        print("\nNext steps:")
        print("1. Check the API documentation at http://localhost:8000/docs")
        print("2. Explore more endpoints and features")
        print("3. Set up automated scraping with search profiles")
        print("4. Configure email notifications")
        
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to the API. Make sure the server is running:")
        print("   python run.py")
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        print(f"Response: {e.response.text}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")


if __name__ == "__main__":
    main() 