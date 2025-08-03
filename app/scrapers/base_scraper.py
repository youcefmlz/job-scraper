from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
from firecrawl import FirecrawlApp
from app.config import settings
from app.models import JobSearchRequest

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all job site scrapers using Firecrawl"""
    
    def __init__(self):
        self.firecrawl = FirecrawlApp(api_key=settings.firecrawl_api_key)
        self.site_name = self.get_site_name()
        self.base_url = self.get_base_url()
        
    @abstractmethod
    def get_site_name(self) -> str:
        """Return the name of the job site"""
        pass
    
    @abstractmethod
    def get_base_url(self) -> str:
        """Return the base URL of the job site"""
        pass
    
    @abstractmethod
    def build_search_url(self, search_request: JobSearchRequest) -> str:
        """Build the search URL with parameters"""
        pass
    
    @abstractmethod
    def extract_job_listings(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract job listings from HTML content"""
        pass
    
    @abstractmethod
    def parse_job_details(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual job details"""
        pass
    
    def scrape_jobs(self, search_request: JobSearchRequest) -> List[Dict[str, Any]]:
        """Main method to scrape jobs from the site"""
        try:
            # Build search URL
            search_url = self.build_search_url(search_request)
            logger.info(f"Scraping {self.site_name} with URL: {search_url}")
            
            # Use Firecrawl to scrape the page
            response = self.firecrawl.scrape_url(
                url=search_url,
                wait_for=".job-listing, .job-card, [data-testid*='job'], .search-result",
                wait_for_timeout=10000
            )
            
            if not response or not response.get('html'):
                logger.warning(f"No content received from {self.site_name}")
                return []
            
            # Extract job listings from HTML
            job_listings = self.extract_job_listings(response['html'])
            logger.info(f"Found {len(job_listings)} jobs on {self.site_name}")
            
            # Parse each job's details
            parsed_jobs = []
            for job_data in job_listings:
                try:
                    parsed_job = self.parse_job_details(job_data)
                    if parsed_job:
                        parsed_jobs.append(parsed_job)
                except Exception as e:
                    logger.error(f"Error parsing job on {self.site_name}: {e}")
                    continue
            
            return parsed_jobs
            
        except Exception as e:
            logger.error(f"Error scraping {self.site_name}: {e}")
            return []
    
    def extract_salary_range(self, salary_text: str) -> tuple[Optional[float], Optional[float]]:
        """Extract salary range from text"""
        if not salary_text:
            return None, None
        
        # Common salary patterns
        import re
        
        # Remove common words and symbols
        cleaned = re.sub(r'[^\d\-\$\,\.]', '', salary_text)
        
        # Look for ranges like "50,000-75,000" or "$50k-$75k"
        range_pattern = r'(\d+(?:,\d+)?(?:k)?)\s*-\s*(\d+(?:,\d+)?(?:k)?)'
        match = re.search(range_pattern, cleaned)
        
        if match:
            min_salary = self.parse_salary_value(match.group(1))
            max_salary = self.parse_salary_value(match.group(2))
            return min_salary, max_salary
        
        # Look for single values
        single_pattern = r'(\d+(?:,\d+)?(?:k)?)'
        match = re.search(single_pattern, cleaned)
        
        if match:
            salary = self.parse_salary_value(match.group(1))
            return salary, salary
        
        return None, None
    
    def parse_salary_value(self, value: str) -> Optional[float]:
        """Parse salary value from string"""
        if not value:
            return None
        
        # Remove commas and convert k to thousands
        cleaned = value.replace(',', '')
        if 'k' in cleaned.lower():
            cleaned = cleaned.lower().replace('k', '')
            return float(cleaned) * 1000
        else:
            return float(cleaned)
    
    def extract_skills_and_requirements(self, description: str) -> tuple[List[str], List[str]]:
        """Extract skills and requirements from job description"""
        if not description:
            return [], []
        
        # Common skill keywords
        skill_keywords = [
            'python', 'javascript', 'java', 'react', 'angular', 'vue', 'node.js',
            'sql', 'mongodb', 'postgresql', 'aws', 'docker', 'kubernetes',
            'machine learning', 'ai', 'data science', 'devops', 'agile',
            'scrum', 'git', 'jenkins', 'ci/cd', 'microservices', 'api',
            'html', 'css', 'typescript', 'php', 'ruby', 'go', 'rust',
            'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy'
        ]
        
        # Common requirement keywords
        requirement_keywords = [
            'bachelor', 'master', 'phd', 'degree', 'certification',
            'experience', 'years', 'senior', 'junior', 'entry level',
            'leadership', 'management', 'team', 'communication',
            'problem solving', 'analytical', 'creative', 'detail-oriented'
        ]
        
        description_lower = description.lower()
        
        skills = []
        requirements = []
        
        # Extract skills
        for skill in skill_keywords:
            if skill in description_lower:
                skills.append(skill.title())
        
        # Extract requirements
        for req in requirement_keywords:
            if req in description_lower:
                requirements.append(req.title())
        
        return list(set(skills)), list(set(requirements))
    
    def determine_job_type(self, title: str, description: str) -> Optional[str]:
        """Determine if job is remote, hybrid, or onsite"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['remote', 'work from home', 'wfh']):
            return 'remote'
        elif any(word in text for word in ['hybrid', 'partially remote']):
            return 'hybrid'
        elif any(word in text for word in ['onsite', 'in-office', 'in person']):
            return 'onsite'
        
        return None
    
    def determine_experience_level(self, title: str, description: str) -> Optional[str]:
        """Determine experience level from title and description"""
        text = f"{title} {description}".lower()
        
        if any(word in text for word in ['senior', 'lead', 'principal', 'staff']):
            return 'senior'
        elif any(word in text for word in ['mid', 'intermediate', 'experienced']):
            return 'mid'
        elif any(word in text for word in ['junior', 'entry', 'associate', 'graduate']):
            return 'entry'
        
        return None 