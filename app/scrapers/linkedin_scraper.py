from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup
import re
from datetime import datetime
from app.scrapers.base_scraper import BaseScraper
from app.models import JobSearchRequest


class LinkedInScraper(BaseScraper):
    """LinkedIn job scraper using Firecrawl"""
    
    def get_site_name(self) -> str:
        return "linkedin"
    
    def get_base_url(self) -> str:
        return "https://www.linkedin.com"
    
    def build_search_url(self, search_request: JobSearchRequest) -> str:
        """Build LinkedIn job search URL"""
        base_url = "https://www.linkedin.com/jobs/search"
        
        # Build search parameters
        params = {}
        
        # Keywords
        if search_request.keywords:
            keywords = " ".join(search_request.keywords)
            params['keywords'] = keywords
        
        # Location
        if search_request.location:
            params['location'] = search_request.location
        
        # Job type filters
        if search_request.job_type.value != "any":
            if search_request.job_type.value == "remote":
                params['f_WT'] = "2"  # Remote work filter
            elif search_request.job_type.value == "hybrid":
                params['f_WT'] = "3"  # Hybrid work filter
            elif search_request.job_type.value == "onsite":
                params['f_WT'] = "1"  # On-site work filter
        
        # Experience level
        if search_request.experience_level.value != "any":
            if search_request.experience_level.value == "entry":
                params['f_E'] = "1"  # Entry level
            elif search_request.experience_level.value == "mid":
                params['f_E'] = "2"  # Associate
            elif search_request.experience_level.value == "senior":
                params['f_E'] = "3"  # Mid-Senior level
        
        # Salary range (LinkedIn doesn't have direct salary filters in URL)
        # We'll filter this after scraping
        
        # Build URL
        if params:
            query_string = urlencode(params)
            return f"{base_url}?{query_string}"
        
        return base_url
    
    def extract_job_listings(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract job listings from LinkedIn HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        job_listings = []
        
        # LinkedIn job cards
        job_cards = soup.find_all('div', class_=re.compile(r'job-card|job-search-card'))
        
        for card in job_cards:
            try:
                job_data = self.extract_job_card_data(card)
                if job_data:
                    job_listings.append(job_data)
            except Exception as e:
                continue
        
        return job_listings
    
    def extract_job_card_data(self, card) -> Optional[Dict[str, Any]]:
        """Extract data from a LinkedIn job card"""
        try:
            # Job title
            title_elem = card.find('h3') or card.find('a', class_=re.compile(r'title'))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Company name
            company_elem = card.find('h4') or card.find('span', class_=re.compile(r'company'))
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Location
            location_elem = card.find('span', class_=re.compile(r'location'))
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Job URL
            link_elem = card.find('a', href=True)
            job_url = link_elem['href'] if link_elem else ""
            if job_url and not job_url.startswith('http'):
                job_url = f"https://www.linkedin.com{job_url}"
            
            # Posted date
            date_elem = card.find('time') or card.find('span', class_=re.compile(r'time'))
            posted_date = None
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                posted_date = self.parse_date(date_text)
            
            # Salary (LinkedIn doesn't show salary in cards often)
            salary_elem = card.find('span', class_=re.compile(r'salary'))
            salary_text = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Job type
            job_type_elem = card.find('span', class_=re.compile(r'work-type'))
            job_type_text = job_type_elem.get_text(strip=True) if job_type_elem else ""
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'job_url': job_url,
                'posted_date': posted_date,
                'salary_text': salary_text,
                'job_type_text': job_type_text,
                'raw_html': str(card)
            }
            
        except Exception as e:
            return None
    
    def parse_job_details(self, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse individual job details"""
        title = job_data.get('title', '')
        company = job_data.get('company', '')
        location = job_data.get('location', '')
        job_url = job_data.get('job_url', '')
        posted_date = job_data.get('posted_date')
        salary_text = job_data.get('salary_text', '')
        job_type_text = job_data.get('job_type_text', '')
        
        # Extract salary range
        salary_min, salary_max = self.extract_salary_range(salary_text)
        
        # Determine job type
        job_type = self.determine_job_type(title, job_type_text)
        
        # Determine experience level
        experience_level = self.determine_experience_level(title, '')
        
        # Generate external ID
        external_id = f"linkedin_{hash(f'{title}_{company}_{location}')}"
        
        # For LinkedIn, we need to scrape the individual job page for full details
        # This would require additional Firecrawl calls for each job
        # For now, we'll use the card data
        
        return {
            'external_id': external_id,
            'title': title,
            'company': company,
            'location': location,
            'job_type': job_type,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_currency': 'USD',
            'description': '',  # Would need to scrape individual job page
            'requirements': [],
            'skills': [],
            'experience_level': experience_level,
            'application_url': job_url,
            'source_site': 'linkedin',
            'posted_date': posted_date,
            'scraped_at': datetime.utcnow(),
            'is_active': True,
            'job_metadata': {
                'job_type_text': job_type_text,
                'salary_text': salary_text,
                'raw_html': job_data.get('raw_html', '')
            }
        }
    
    def parse_date(self, date_text: str) -> Optional[datetime]:
        """Parse LinkedIn date format"""
        if not date_text:
            return None
        
        # LinkedIn uses relative dates like "2 days ago", "1 week ago"
        import re
        
        # Extract number and unit
        match = re.search(r'(\d+)\s*(day|week|month|hour)s?\s*ago', date_text.lower())
        if match:
            number = int(match.group(1))
            unit = match.group(2)
            
            from datetime import timedelta
            now = datetime.utcnow()
            
            if unit == 'hour':
                return now - timedelta(hours=number)
            elif unit == 'day':
                return now - timedelta(days=number)
            elif unit == 'week':
                return now - timedelta(weeks=number)
            elif unit == 'month':
                return now - timedelta(days=number*30)
        
        return None 