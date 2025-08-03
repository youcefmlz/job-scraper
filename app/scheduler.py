import schedule
import time
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import get_db, SearchProfile, JobListing, User
from app.services.job_service import JobService
from app.services.notification_service import NotificationService
from app.models import JobSearchRequest, NotificationCreate
from app.config import settings

logger = logging.getLogger(__name__)


class JobScheduler:
    """Scheduler for automated job scraping and notifications"""
    
    def __init__(self):
        self.job_service = JobService()
        self.notification_service = NotificationService()
        self._setup_schedule()
    
    def _setup_schedule(self):
        """Setup scheduled tasks"""
        # Run job scraping every X minutes (configurable)
        schedule.every(settings.scrape_interval_minutes).minutes.do(self.run_job_scraping)
        
        # Run notification check every 5 minutes
        schedule.every(5).minutes.do(self.check_and_send_notifications)
        
        # Run cleanup every hour
        schedule.every().hour.do(self.cleanup_old_data)
        
        logger.info(f"Job scheduler initialized. Scraping interval: {settings.scrape_interval_minutes} minutes")
    
    def run_job_scraping(self):
        """Run job scraping for all active search profiles"""
        logger.info("Starting scheduled job scraping")
        
        try:
            db = next(get_db())
            
            # Get all active search profiles
            active_profiles = db.query(SearchProfile).filter(
                SearchProfile.is_active == True
            ).all()
            
            total_jobs_found = 0
            total_jobs_new = 0
            total_jobs_updated = 0
            
            for profile in active_profiles:
                try:
                    # Create search request from profile
                    search_request = JobSearchRequest(
                        keywords=profile.keywords,
                        location=profile.location,
                        job_type=profile.job_type,
                        experience_level=profile.experience_level,
                        salary_min=profile.salary_min,
                        salary_max=profile.salary_max
                    )
                    
                    # Scrape jobs for this profile
                    result = self.job_service.scrape_and_store_jobs(db, search_request, profile.user_id)
                    
                    total_jobs_found += result['total_jobs_found']
                    total_jobs_new += result['total_jobs_new']
                    total_jobs_updated += result['total_jobs_updated']
                    
                    logger.info(f"Profile '{profile.name}': {result['total_jobs_new']} new jobs, {result['total_jobs_updated']} updated")
                    
                except Exception as e:
                    logger.error(f"Error scraping jobs for profile '{profile.name}': {e}")
                    continue
            
            logger.info(f"Job scraping completed. Total: {total_jobs_found} found, {total_jobs_new} new, {total_jobs_updated} updated")
            
        except Exception as e:
            logger.error(f"Error in scheduled job scraping: {e}")
        finally:
            db.close()
    
    def check_and_send_notifications(self):
        """Check for new jobs and send notifications to users"""
        logger.info("Starting notification check")
        
        try:
            db = next(get_db())
            
            # Get all active search profiles
            active_profiles = db.query(SearchProfile).filter(
                SearchProfile.is_active == True
            ).all()
            
            notifications_sent = 0
            
            for profile in active_profiles:
                try:
                    # Get user for this profile
                    user = db.query(User).filter(User.id == profile.user_id).first()
                    if not user or not user.is_active:
                        continue
                    
                    # Find new jobs that match this profile
                    new_jobs = self._find_new_jobs_for_profile(db, profile)
                    
                    for job in new_jobs:
                        try:
                            # Create notification
                            notification_data = NotificationCreate(
                                user_id=profile.user_id,
                                job_listing_id=job.id,
                                search_profile_id=profile.id,
                                notification_type='email'
                            )
                            
                            # Send notification
                            success = self.notification_service.send_job_notification(db, notification_data)
                            if success:
                                notifications_sent += 1
                                logger.info(f"Notification sent to {user.email} for job {job.title}")
                            
                        except Exception as e:
                            logger.error(f"Error sending notification for job {job.id}: {e}")
                            continue
                
                except Exception as e:
                    logger.error(f"Error processing notifications for profile '{profile.name}': {e}")
                    continue
            
            logger.info(f"Notification check completed. {notifications_sent} notifications sent")
            
        except Exception as e:
            logger.error(f"Error in notification check: {e}")
        finally:
            db.close()
    
    def _find_new_jobs_for_profile(self, db: Session, profile: SearchProfile) -> list:
        """Find new jobs that match a search profile"""
        from sqlalchemy import and_, or_, desc
        
        # Get jobs from the last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        query = db.query(JobListing).filter(
            and_(
                JobListing.is_active == True,
                JobListing.scraped_at >= yesterday
            )
        )
        
        # Filter by keywords
        if profile.keywords:
            keyword_filters = []
            for keyword in profile.keywords:
                keyword_filter = or_(
                    JobListing.title.ilike(f'%{keyword}%'),
                    JobListing.description.ilike(f'%{keyword}%'),
                    JobListing.company.ilike(f'%{keyword}%')
                )
                keyword_filters.append(keyword_filter)
            query = query.filter(or_(*keyword_filters))
        
        # Filter by location
        if profile.location:
            query = query.filter(JobListing.location.ilike(f'%{profile.location}%'))
        
        # Filter by job type
        if profile.job_type and profile.job_type != "any":
            query = query.filter(JobListing.job_type == profile.job_type)
        
        # Filter by experience level
        if profile.experience_level and profile.experience_level != "any":
            query = query.filter(JobListing.experience_level == profile.experience_level)
        
        # Filter by salary range
        if profile.salary_min:
            query = query.filter(JobListing.salary_max >= profile.salary_min)
        if profile.salary_max:
            query = query.filter(JobListing.salary_min <= profile.salary_max)
        
        # Order by most recent
        query = query.order_by(desc(JobListing.scraped_at))
        
        return query.all()
    
    def cleanup_old_data(self):
        """Clean up old data to prevent database bloat"""
        logger.info("Starting data cleanup")
        
        try:
            db = next(get_db())
            
            # Remove old job listings (older than 90 days)
            ninety_days_ago = datetime.utcnow() - timedelta(days=90)
            old_jobs = db.query(JobListing).filter(
                JobListing.scraped_at < ninety_days_ago
            ).all()
            
            for job in old_jobs:
                db.delete(job)
            
            # Remove old notifications (older than 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            old_notifications = db.query(Notification).filter(
                Notification.sent_at < thirty_days_ago
            ).all()
            
            for notification in old_notifications:
                db.delete(notification)
            
            db.commit()
            
            logger.info(f"Cleanup completed. Removed {len(old_jobs)} old jobs and {len(old_notifications)} old notifications")
            
        except Exception as e:
            logger.error(f"Error in data cleanup: {e}")
        finally:
            db.close()
    
    def start(self):
        """Start the scheduler"""
        logger.info("Starting job scheduler")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
            except KeyboardInterrupt:
                logger.info("Scheduler stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in scheduler: {e}")
                time.sleep(60)  # Wait before retrying
    
    def stop(self):
        """Stop the scheduler"""
        logger.info("Stopping job scheduler")
        schedule.clear()
    
    def get_next_run_times(self) -> dict:
        """Get the next run times for scheduled tasks"""
        jobs = schedule.get_jobs()
        next_runs = {}
        
        for job in jobs:
            next_runs[job.job_func.__name__] = job.next_run
        
        return next_runs 