from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.services.job_service import JobService
from app.models import JobSearchRequest, JobListingResponse
from app.scrapers.scraper_factory import ScraperFactory

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("/search", response_model=List[JobListingResponse])
async def search_jobs(
    search_request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """Search for jobs based on criteria"""
    job_service = JobService()
    jobs = job_service.search_jobs(db, search_request)
    return jobs


@router.get("/recent", response_model=List[JobListingResponse])
async def get_recent_jobs(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get most recent jobs"""
    job_service = JobService()
    jobs = job_service.get_recent_jobs(db, limit)
    return jobs


@router.get("/{job_id}", response_model=JobListingResponse)
async def get_job_by_id(
    job_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific job by ID"""
    job_service = JobService()
    job = job_service.get_job_by_id(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/site/{site_name}", response_model=List[JobListingResponse])
async def get_jobs_by_site(
    site_name: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get jobs from a specific site"""
    job_service = JobService()
    jobs = job_service.get_jobs_by_site(db, site_name, limit)
    return jobs


@router.get("/company/{company}", response_model=List[JobListingResponse])
async def get_jobs_by_company(
    company: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get jobs from a specific company"""
    job_service = JobService()
    jobs = job_service.get_jobs_by_company(db, company, limit)
    return jobs


@router.get("/statistics/summary")
async def get_job_statistics(db: Session = Depends(get_db)):
    """Get job statistics"""
    job_service = JobService()
    stats = job_service.get_job_statistics(db)
    return stats


@router.post("/scrape")
async def scrape_jobs(
    search_request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """Manually trigger job scraping"""
    job_service = JobService()
    result = job_service.scrape_and_store_jobs(db, search_request)
    return {
        "message": "Job scraping completed",
        "total_jobs_found": result['total_jobs_found'],
        "total_jobs_new": result['total_jobs_new'],
        "total_jobs_updated": result['total_jobs_updated'],
        "errors": result['errors'],
        "sites_scraped": result['sites_scraped']
    }


@router.get("/scrapers/status")
async def get_scraper_status():
    """Get status of all scrapers"""
    scraper_factory = ScraperFactory()
    return scraper_factory.get_scraper_status()


@router.get("/scrapers/available")
async def get_available_scrapers():
    """Get list of available scrapers"""
    scraper_factory = ScraperFactory()
    return {
        "available_scrapers": scraper_factory.get_available_scrapers()
    }


@router.post("/scrape/{site_name}")
async def scrape_specific_site(
    site_name: str,
    search_request: JobSearchRequest,
    db: Session = Depends(get_db)
):
    """Scrape jobs from a specific site"""
    scraper_factory = ScraperFactory()
    jobs = scraper_factory.scrape_specific_site(site_name, search_request)
    
    # Store jobs in database
    job_service = JobService()
    result = job_service.scrape_and_store_jobs(db, search_request)
    
    return {
        "message": f"Scraping completed for {site_name}",
        "jobs_found": len(jobs),
        "jobs_stored": result['total_jobs_new'],
        "jobs_updated": result['total_jobs_updated']
    } 