from typing import List, Dict, Any
from app.scrapers.linkedin_scraper import LinkedInScraper
from app.scrapers.indeed_scraper import IndeedScraper
from app.models import JobSearchRequest
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class ScraperFactory:
    """Factory for managing job scrapers"""
    
    def __init__(self):
        self.scrapers = {}
        self._initialize_scrapers()
    
    def _initialize_scrapers(self):
        """Initialize available scrapers based on configuration"""
        if settings.linkedin_enabled:
            self.scrapers['linkedin'] = LinkedInScraper()
        
        if settings.indeed_enabled:
            self.scrapers['indeed'] = IndeedScraper()
        
        # Add more scrapers as they are implemented
        # if settings.glassdoor_enabled:
        #     self.scrapers['glassdoor'] = GlassdoorScraper()
        # 
        # if settings.monster_enabled:
        #     self.scrapers['monster'] = MonsterScraper()
        # 
        # if settings.dice_enabled:
        #     self.scrapers['dice'] = DiceScraper()
        # 
        # if settings.careerbuilder_enabled:
        #     self.scrapers['careerbuilder'] = CareerBuilderScraper()
    
    def get_available_scrapers(self) -> List[str]:
        """Get list of available scraper names"""
        return list(self.scrapers.keys())
    
    def get_scraper(self, site_name: str):
        """Get a specific scraper by site name"""
        return self.scrapers.get(site_name.lower())
    
    def scrape_all_sites(self, search_request: JobSearchRequest) -> Dict[str, List[Dict[str, Any]]]:
        """Scrape jobs from all enabled sites"""
        results = {}
        
        for site_name, scraper in self.scrapers.items():
            try:
                logger.info(f"Starting scrape for {site_name}")
                jobs = scraper.scrape_jobs(search_request)
                results[site_name] = jobs
                logger.info(f"Completed scrape for {site_name}: {len(jobs)} jobs found")
            except Exception as e:
                logger.error(f"Error scraping {site_name}: {e}")
                results[site_name] = []
        
        return results
    
    def scrape_specific_site(self, site_name: str, search_request: JobSearchRequest) -> List[Dict[str, Any]]:
        """Scrape jobs from a specific site"""
        scraper = self.get_scraper(site_name)
        if not scraper:
            logger.error(f"Scraper not found for site: {site_name}")
            return []
        
        try:
            logger.info(f"Starting scrape for {site_name}")
            jobs = scraper.scrape_jobs(search_request)
            logger.info(f"Completed scrape for {site_name}: {len(jobs)} jobs found")
            return jobs
        except Exception as e:
            logger.error(f"Error scraping {site_name}: {e}")
            return []
    
    def get_scraper_status(self) -> Dict[str, bool]:
        """Get status of all scrapers"""
        return {
            'linkedin': settings.linkedin_enabled,
            'indeed': settings.indeed_enabled,
            'glassdoor': settings.glassdoor_enabled,
            'monster': settings.monster_enabled,
            'dice': settings.dice_enabled,
            'careerbuilder': settings.careerbuilder_enabled
        } 