from typing import List, Dict, Any, Optional
from urllib.parse import urlencode, quote
from bs4 import BeautifulSoup
import re
from datetime import datetime
from app.scrapers.base_scraper import BaseScraper
from app.models import JobSearchRequest


class IndeedScraper(BaseScraper):
    """Indeed job scraper using Firecrawl"""
    
    def get_site_name(self) -> str:
        return "indeed"
    
    def get_base_url(self) -> str:
        return "https://www.indeed.com"
    
    def build_search_url(self, search_request: JobSearchRequest) -> str:
        """Build Indeed job search URL"""
        base_url = "https://www.indeed.com/jobs"
        
        # Build search parameters
        params = {}
        
        # Keywords
        if search_request.keywords:
            keywords = " ".join(search_request.keywords)
            params['q'] = keywords
        
        # Location
        if search_request.location:
            params['l'] = search_request.location
        
        # Job type filters
        if search_request.job_type.value != "any":
            if search_request.job_type.value == "remote":
                params['remotejob'] = "1"
            elif search_request.job_type.value == "hybrid":
                params['remotejob'] = "2"  # Hybrid
            elif search_request.job_type.value == "onsite":
                params['remotejob'] = "0"  # On-site
        
        # Experience level
        if search_request.experience_level.value != "any":
            if search_request.experience_level.value == "entry":
                params['explvl'] = "ENTRY_LEVEL"
            elif search_request.experience_level.value == "mid":
                params['explvl'] = "MID_LEVEL"
            elif search_request.experience_level.value == "senior":
                params['explvl'] = "SENIOR_LEVEL"
        
        # Salary range
        if search_request.salary_min or search_request.salary_max:
            if search_request.salary_min:
                params['salary_min'] = str(int(search_request.salary_min))
            if search_request.salary_max:
                params['salary_max'] = str(int(search_request.salary_max))
        
        # Build URL
        if params:
            query_string = urlencode(params)
            return f"{base_url}?{query_string}"
        
        return base_url
    
    def extract_job_listings(self, html_content: str) -> List[Dict[str, Any]]:
        """Extract job listings from Indeed HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        job_listings = []
        
        # Indeed job cards
        job_cards = soup.find_all('div', class_=re.compile(r'job_seen_beacon|jobsearch-ResultsList'))
        
        for card in job_cards:
            try:
                job_data = self.extract_job_card_data(card)
                if job_data:
                    job_listings.append(job_data)
            except Exception as e:
                continue
        
        return job_listings
    
    def extract_job_card_data(self, card) -> Optional[Dict[str, Any]]:
        """Extract data from an Indeed job card"""
        try:
            # Job title
            title_elem = card.find('h2') or card.find('a', class_=re.compile(r'title'))
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Company name
            company_elem = card.find('span', class_=re.compile(r'company')) or card.find('div', class_=re.compile(r'company'))
            company = company_elem.get_text(strip=True) if company_elem else ""
            
            # Location
            location_elem = card.find('div', class_=re.compile(r'location')) or card.find('span', class_=re.compile(r'location'))
            location = location_elem.get_text(strip=True) if location_elem else ""
            
            # Job URL
            link_elem = card.find('a', href=True)
            job_url = link_elem['href'] if link_elem else ""
            if job_url and not job_url.startswith('http'):
                job_url = f"https://www.indeed.com{job_url}"
            
            # Posted date
            date_elem = card.find('span', class_=re.compile(r'date')) or card.find('div', class_=re.compile(r'date'))
            posted_date = None
            if date_elem:
                date_text = date_elem.get_text(strip=True)
                posted_date = self.parse_date(date_text)
            
            # Salary
            salary_elem = card.find('div', class_=re.compile(r'salary')) or card.find('span', class_=re.compile(r'salary'))
            salary_text = salary_elem.get_text(strip=True) if salary_elem else ""
            
            # Job type
            job_type_elem = card.find('div', class_=re.compile(r'remote')) or card.find('span', class_=re.compile(r'remote'))
            job_type_text = job_type_elem.get_text(strip=True) if job_type_elem else ""
            
            # Job description snippet
            desc_elem = card.find('div', class_=re.compile(r'summary')) or card.find('span', class_=re.compile(r'summary'))
            description = desc_elem.get_text(strip=True) if desc_elem else ""
            
            return {
                'title': title,
                'company': company,
                'location': location,
                'job_url': job_url,
                'posted_date': posted_date,
                'salary_text': salary_text,
                'job_type_text': job_type_text,
                'description': description,
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
        description = job_data.get('description', '')
        
        # Extract salary range
        salary_min, salary_max = self.extract_salary_range(salary_text)
        
        # Determine job type
        job_type = self.determine_job_type(title, job_type_text)
        
        # Determine experience level
        experience_level = self.determine_experience_level(title, description)
        
        # Extract skills and requirements
        skills, requirements = self.extract_skills_and_requirements(description)
        
        # Generate external ID
        external_id = f"indeed_{hash(f'{title}_{company}_{location}')}"
        
        return {
            'external_id': external_id,
            'title': title,
            'company': company,
            'location': location,
            'job_type': job_type,
            'salary_min': salary_min,
            'salary_max': salary_max,
            'salary_currency': 'USD',
            'description': description,
            'requirements': requirements,
            'skills': skills,
            'experience_level': experience_level,
            'application_url': job_url,
            'source_site': 'indeed',
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
        """Parse Indeed date format"""
        if not date_text:
            return None
        
        # Indeed uses relative dates like "2 days ago", "1 week ago"
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