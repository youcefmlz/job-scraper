import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime
import logging
from app.database import Notification, User, JobListing, SearchProfile
from app.models import NotificationCreate, NotificationResponse
from app.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing job notifications"""
    
    def __init__(self):
        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        self.smtp_username = settings.smtp_username
        self.smtp_password = settings.smtp_password
        self.from_email = settings.from_email
    
    def send_job_notification(self, db: Session, notification_data: NotificationCreate) -> bool:
        """Send a job notification to a user"""
        try:
            # Get user and job details
            user = db.query(User).filter(User.id == notification_data.user_id).first()
            job = db.query(JobListing).filter(JobListing.id == notification_data.job_listing_id).first()
            search_profile = db.query(SearchProfile).filter(SearchProfile.id == notification_data.search_profile_id).first()
            
            if not user or not job or not search_profile:
                logger.error(f"Missing data for notification: user={notification_data.user_id}, job={notification_data.job_listing_id}, profile={notification_data.search_profile_id}")
                return False
            
            # Create notification record
            notification = Notification(
                user_id=notification_data.user_id,
                job_listing_id=notification_data.job_listing_id,
                search_profile_id=notification_data.search_profile_id,
                notification_type=notification_data.notification_type.value,
                status='pending'
            )
            db.add(notification)
            db.commit()
            
            # Send email notification
            if notification_data.notification_type.value == 'email':
                success = self._send_email_notification(user, job, search_profile)
                if success:
                    notification.status = 'sent'
                else:
                    notification.status = 'failed'
                db.commit()
                return success
            
            return True
            
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
            return False
    
    def _send_email_notification(self, user: User, job: JobListing, search_profile: SearchProfile) -> bool:
        """Send email notification for a job match"""
        try:
            # Create email message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"New Job Match: {job.title} at {job.company}"
            msg['From'] = self.from_email
            msg['To'] = user.email
            
            # Create HTML content
            html_content = self._create_job_email_html(user, job, search_profile)
            text_content = self._create_job_email_text(user, job, search_profile)
            
            # Attach both HTML and text versions
            msg.attach(MIMEText(text_content, 'plain'))
            msg.attach(MIMEText(html_content, 'html'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email notification sent to {user.email} for job {job.id}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def _create_job_email_html(self, user: User, job: JobListing, search_profile: SearchProfile) -> str:
        """Create HTML email content"""
        salary_info = ""
        if job.salary_min and job.salary_max:
            salary_info = f"${job.salary_min:,.0f} - ${job.salary_max:,.0f}"
        elif job.salary_min:
            salary_info = f"${job.salary_min:,.0f}+"
        elif job.salary_max:
            salary_info = f"Up to ${job.salary_max:,.0f}"
        
        job_type_badge = ""
        if job.job_type:
            job_type_badge = f'<span style="background-color: #007bff; color: white; padding: 4px 8px; border-radius: 4px; font-size: 12px;">{job.job_type.title()}</span>'
        
        skills_html = ""
        if job.skills:
            skills_html = f'<p><strong>Skills:</strong> {", ".join(job.skills[:5])}</p>'
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .job-card {{ border: 1px solid #ddd; border-radius: 8px; padding: 20px; margin-bottom: 20px; }}
                .company {{ color: #666; font-size: 14px; }}
                .location {{ color: #666; font-size: 14px; }}
                .salary {{ color: #28a745; font-weight: bold; }}
                .description {{ margin-top: 15px; }}
                .cta-button {{ display: inline-block; background-color: #007bff; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-top: 15px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>New Job Match Found! 🎉</h2>
                    <p>Hi {user.name},</p>
                    <p>We found a new job that matches your search criteria in profile "<strong>{search_profile.name}</strong>".</p>
                </div>
                
                <div class="job-card">
                    <h3>{job.title}</h3>
                    <p class="company">{job.company}</p>
                    <p class="location">📍 {job.location}</p>
                    {f'<p class="salary">💰 {salary_info}</p>' if salary_info else ''}
                    {job_type_badge}
                    
                    <div class="description">
                        <p>{job.description[:300]}{"..." if len(job.description) > 300 else ""}</p>
                        {skills_html}
                    </div>
                    
                    <a href="{job.application_url}" class="cta-button" target="_blank">Apply Now</a>
                </div>
                
                <p style="font-size: 12px; color: #666;">
                    This job was found on {job.source_site.title()}. 
                    You can manage your search profiles in your dashboard.
                </p>
            </div>
        </body>
        </html>
        """
    
    def _create_job_email_text(self, user: User, job: JobListing, search_profile: SearchProfile) -> str:
        """Create text email content"""
        salary_info = ""
        if job.salary_min and job.salary_max:
            salary_info = f"${job.salary_min:,.0f} - ${job.salary_max:,.0f}"
        elif job.salary_min:
            salary_info = f"${job.salary_min:,.0f}+"
        elif job.salary_max:
            salary_info = f"Up to ${job.salary_max:,.0f}"
        
        return f"""
New Job Match Found!

Hi {user.name},

We found a new job that matches your search criteria in profile "{search_profile.name}".

Job Details:
- Title: {job.title}
- Company: {job.company}
- Location: {job.location}
{f"- Salary: {salary_info}" if salary_info else ""}
{f"- Type: {job.job_type.title()}" if job.job_type else ""}

Description:
{job.description[:200]}{"..." if len(job.description) > 200 else ""}

{f"Skills: {', '.join(job.skills[:5])}" if job.skills else ""}

Apply here: {job.application_url}

This job was found on {job.source_site.title()}.

Best regards,
Job Scraper Team
        """
    
    def get_user_notifications(self, db: Session, user_id: int, limit: int = 50) -> List[NotificationResponse]:
        """Get notifications for a user"""
        notifications = db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.sent_at.desc()).limit(limit).all()
        
        return [NotificationResponse.from_orm(notification) for notification in notifications]
    
    def mark_notification_read(self, db: Session, notification_id: int) -> bool:
        """Mark a notification as read"""
        try:
            notification = db.query(Notification).filter(Notification.id == notification_id).first()
            if notification:
                notification.status = 'read'
                db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def send_bulk_notifications(self, db: Session, notifications: List[NotificationCreate]) -> Dict[str, int]:
        """Send multiple notifications"""
        success_count = 0
        failure_count = 0
        
        for notification_data in notifications:
            success = self.send_job_notification(db, notification_data)
            if success:
                success_count += 1
            else:
                failure_count += 1
        
        return {
            'success_count': success_count,
            'failure_count': failure_count,
            'total_count': len(notifications)
        } 