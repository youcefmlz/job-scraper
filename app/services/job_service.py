from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from datetime import datetime, timedelta
import logging
from app.database import JobListing, ScrapingLog
from app.models import JobSearchRequest, JobListingResponse
from app.scrapers.scraper_factory import ScraperFactory

logger = logging.getLogger(__name__)


class JobService:
    """Service for managing job listings"""
    
    def __init__(self):
        self.scraper_factory = ScraperFactory()
    
    def scrape_and_store_jobs(self, db: Session, search_request: JobSearchRequest, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Scrape jobs from all sites and store them in the database"""
        start_time = datetime.utcnow()
        total_jobs_found = 0
        total_jobs_new = 0
        total_jobs_updated = 0
        errors = []
        
        # Scrape from all sites
        scraping_results = self.scraper_factory.scrape_all_sites(search_request)
        
        for site_name, jobs in scraping_results.items():
            try:
                site_jobs_found = len(jobs)
                site_jobs_new = 0
                site_jobs_updated = 0
                
                for job_data in jobs:
                    try:
                        # Check if job already exists
                        existing_job = db.query(JobListing).filter(
                            JobListing.external_id == job_data['external_id']
                        ).first()
                        
                        if existing_job:
                            # Update existing job
                            self._update_job_listing(existing_job, job_data)
                            site_jobs_updated += 1
                        else:
                            # Create new job
                            new_job = self._create_job_listing(job_data)
                            db.add(new_job)
                            site_jobs_new += 1
                    
                    except Exception as e:
                        logger.error(f"Error processing job from {site_name}: {e}")
                        errors.append(f"{site_name}: {str(e)}")
                        continue
                
                # Log scraping results for this site
                scraping_log = ScrapingLog(
                    source_site=site_name,
                    search_terms={
                        'keywords': search_request.keywords,
                        'location': search_request.location,
                        'job_type': search_request.job_type.value,
                        'experience_level': search_request.experience_level.value,
                        'salary_min': search_request.salary_min,
                        'salary_max': search_request.salary_max
                    },
                    jobs_found=site_jobs_found,
                    jobs_new=site_jobs_new,
                    jobs_updated=site_jobs_updated,
                    errors='; '.join(errors) if errors else None,
                    started_at=start_time,
                    completed_at=datetime.utcnow()
                )
                db.add(scraping_log)
                
                total_jobs_found += site_jobs_found
                total_jobs_new += site_jobs_new
                total_jobs_updated += site_jobs_updated
                
            except Exception as e:
                logger.error(f"Error processing {site_name}: {e}")
                errors.append(f"{site_name}: {str(e)}")
                continue
        
        # Commit all changes
        db.commit()
        
        return {
            'total_jobs_found': total_jobs_found,
            'total_jobs_new': total_jobs_new,
            'total_jobs_updated': total_jobs_updated,
            'errors': errors,
            'sites_scraped': list(scraping_results.keys())
        }
    
    def _create_job_listing(self, job_data: Dict[str, Any]) -> JobListing:
        """Create a new job listing from scraped data"""
        return JobListing(
            external_id=job_data['external_id'],
            title=job_data['title'],
            company=job_data['company'],
            location=job_data['location'],
            job_type=job_data.get('job_type'),
            salary_min=job_data.get('salary_min'),
            salary_max=job_data.get('salary_max'),
            salary_currency=job_data.get('salary_currency', 'USD'),
            description=job_data.get('description', ''),
            requirements=job_data.get('requirements', []),
            skills=job_data.get('skills', []),
            experience_level=job_data.get('experience_level'),
            application_url=job_data.get('application_url', ''),
            source_site=job_data['source_site'],
            posted_date=job_data.get('posted_date'),
            scraped_at=job_data.get('scraped_at', datetime.utcnow()),
            is_active=True,
            job_metadata=job_data.get('job_metadata', {})
        )
    
    def _update_job_listing(self, job: JobListing, job_data: Dict[str, Any]):
        """Update an existing job listing with new data"""
        job.title = job_data['title']
        job.company = job_data['company']
        job.location = job_data['location']
        job.job_type = job_data.get('job_type', job.job_type)
        job.salary_min = job_data.get('salary_min', job.salary_min)
        job.salary_max = job_data.get('salary_max', job.salary_max)
        job.description = job_data.get('description', job.description)
        job.requirements = job_data.get('requirements', job.requirements)
        job.skills = job_data.get('skills', job.skills)
        job.experience_level = job_data.get('experience_level', job.experience_level)
        job.application_url = job_data.get('application_url', job.application_url)
        job.posted_date = job_data.get('posted_date', job.posted_date)
        job.scraped_at = datetime.utcnow()
        job.job_metadata = job_data.get('job_metadata', job.job_metadata)
    
    def search_jobs(self, db: Session, search_request: JobSearchRequest) -> List[JobListingResponse]:
        """Search for jobs in the database based on criteria"""
        query = db.query(JobListing).filter(JobListing.is_active == True)
        
        # Filter by keywords (search in title, description, company)
        if search_request.keywords:
            keyword_filters = []
            for keyword in search_request.keywords:
                keyword_filter = or_(
                    JobListing.title.ilike(f'%{keyword}%'),
                    JobListing.description.ilike(f'%{keyword}%'),
                    JobListing.company.ilike(f'%{keyword}%')
                )
                keyword_filters.append(keyword_filter)
            query = query.filter(or_(*keyword_filters))
        
        # Filter by location
        if search_request.location:
            query = query.filter(JobListing.location.ilike(f'%{search_request.location}%'))
        
        # Filter by job type
        if search_request.job_type.value != "any":
            query = query.filter(JobListing.job_type == search_request.job_type.value)
        
        # Filter by experience level
        if search_request.experience_level.value != "any":
            query = query.filter(JobListing.experience_level == search_request.experience_level.value)
        
        # Filter by salary range
        if search_request.salary_min:
            query = query.filter(JobListing.salary_max >= search_request.salary_min)
        if search_request.salary_max:
            query = query.filter(JobListing.salary_min <= search_request.salary_max)
        
        # Order by most recent
        query = query.order_by(desc(JobListing.scraped_at))
        
        # Apply pagination
        query = query.offset(search_request.offset).limit(search_request.limit)
        
        jobs = query.all()
        return [JobListingResponse.from_orm(job) for job in jobs]
    
    def get_job_by_id(self, db: Session, job_id: int) -> Optional[JobListingResponse]:
        """Get a specific job by ID"""
        job = db.query(JobListing).filter(JobListing.id == job_id).first()
        return JobListingResponse.from_orm(job) if job else None
    
    def get_recent_jobs(self, db: Session, limit: int = 50) -> List[JobListingResponse]:
        """Get most recent jobs"""
        jobs = db.query(JobListing).filter(
            JobListing.is_active == True
        ).order_by(desc(JobListing.scraped_at)).limit(limit).all()
        
        return [JobListingResponse.from_orm(job) for job in jobs]
    
    def get_jobs_by_site(self, db: Session, site_name: str, limit: int = 50) -> List[JobListingResponse]:
        """Get jobs from a specific site"""
        jobs = db.query(JobListing).filter(
            and_(
                JobListing.is_active == True,
                JobListing.source_site == site_name
            )
        ).order_by(desc(JobListing.scraped_at)).limit(limit).all()
        
        return [JobListingResponse.from_orm(job) for job in jobs]
    
    def get_jobs_by_company(self, db: Session, company: str, limit: int = 50) -> List[JobListingResponse]:
        """Get jobs from a specific company"""
        jobs = db.query(JobListing).filter(
            and_(
                JobListing.is_active == True,
                JobListing.company.ilike(f'%{company}%')
            )
        ).order_by(desc(JobListing.scraped_at)).limit(limit).all()
        
        return [JobListingResponse.from_orm(job) for job in jobs]
    
    def get_job_statistics(self, db: Session) -> Dict[str, Any]:
        """Get job statistics"""
        total_jobs = db.query(JobListing).filter(JobListing.is_active == True).count()
        
        # Jobs by site
        jobs_by_site = db.query(JobListing.source_site, db.func.count(JobListing.id)).filter(
            JobListing.is_active == True
        ).group_by(JobListing.source_site).all()
        
        # Jobs by job type
        jobs_by_type = db.query(JobListing.job_type, db.func.count(JobListing.id)).filter(
            and_(
                JobListing.is_active == True,
                JobListing.job_type.isnot(None)
            )
        ).group_by(JobListing.job_type).all()
        
        # Recent jobs (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_jobs = db.query(JobListing).filter(
            and_(
                JobListing.is_active == True,
                JobListing.scraped_at >= yesterday
            )
        ).count()
        
        return {
            'total_jobs': total_jobs,
            'jobs_by_site': dict(jobs_by_site),
            'jobs_by_type': dict(jobs_by_type),
            'recent_jobs_24h': recent_jobs
        } 