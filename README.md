# Job Scraper - Automated Job Search Monitor

An automated job search monitoring tool that continuously scans multiple job listing websites for new positions matching user-defined criteria. Built with FastAPI and Firecrawl for powerful web scraping capabilities.

## Features

- **Multi-site Job Scraping**: Supports LinkedIn, Indeed, Glassdoor, Monster, Dice, and CareerBuilder
- **Automated Monitoring**: Continuous scraping with configurable intervals
- **Smart Filtering**: Filter by keywords, location, job type, experience level, and salary range
- **Email Notifications**: Beautiful HTML email notifications for new job matches
- **Search Profiles**: Create and manage multiple search profiles per user
- **RESTful API**: Complete API for integration with frontend applications
- **Database Storage**: SQLite/PostgreSQL support with job deduplication
- **Statistics & Analytics**: Track scraping performance and job statistics

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Scraping**: Firecrawl 2.16.3 for reliable web scraping
- **Database**: SQLite (default) / PostgreSQL
- **Email**: SMTP with HTML templates
- **Scheduling**: Python schedule library
- **Parsing**: BeautifulSoup for HTML parsing

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd job-scraper
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Copy the example environment file and configure your settings:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
# Database Configuration
DATABASE_URL=sqlite:///./job_scraper.db

# Email Configuration (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=your-email@gmail.com

# Firecrawl Configuration
FIRECRAWL_API_KEY=your-firecrawl-api-key

# Application Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
HOST=0.0.0.0
PORT=8000

# Scraping Settings
SCRAPE_INTERVAL_MINUTES=30
MAX_RETRIES=3
REQUEST_DELAY_SECONDS=2

# Job Sites Configuration
LINKEDIN_ENABLED=true
INDEED_ENABLED=false
GLASSDOOR_ENABLED=false
MONSTER_ENABLED=false
DICE_ENABLED=false
CAREERBUILDER_ENABLED=false
```

### 5. Run the Application

**Option 1: Using the run script**
```bash
python run.py
```

**Option 2: Direct module execution**
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

### 6. Verify Setup

Test that everything is working:
```bash
python test_setup.py
```

## API Documentation

Once running, visit:
- **Interactive API Docs**: http://localhost:8000/docs
- **Alternative API Docs**: http://localhost:8000/redoc

## Usage Examples

### 1. Create a User

```bash
curl -X POST "http://localhost:8000/api/v1/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "name": "John Doe"
  }'
```

### 2. Create a Search Profile

```bash
curl -X POST "http://localhost:8000/api/v1/users/1/profiles" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python Developer",
    "keywords": ["python", "django", "fastapi"],
    "location": "San Francisco",
    "job_type": "remote",
    "experience_level": "mid",
    "salary_min": 80000,
    "salary_max": 150000
  }'
```

### 3. Search for Jobs

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/search" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["python", "developer"],
    "location": "San Francisco",
    "job_type": "remote",
    "experience_level": "mid",
    "salary_min": 80000,
    "salary_max": 150000,
    "limit": 20,
    "offset": 0
  }'
```

### 4. Manually Trigger Scraping

```bash
curl -X POST "http://localhost:8000/api/v1/jobs/scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "keywords": ["python", "developer"],
    "location": "San Francisco",
    "job_type": "remote",
    "experience_level": "mid"
  }'
```

### 5. Get Job Statistics

```bash
curl "http://localhost:8000/api/v1/jobs/statistics/summary"
```

### 6. Try the Example Script

```bash
python examples/basic_usage.py
```

## Project Structure

```
job-scraper/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database models and setup
│   ├── models.py               # Pydantic models
│   ├── scheduler.py            # Automated job scheduler
│   ├── api/
│   │   ├── __init__.py
│   │   ├── jobs.py             # Job-related API endpoints
│   │   └── users.py            # User-related API endpoints
│   ├── scrapers/
│   │   ├── __init__.py
│   │   ├── base_scraper.py     # Base scraper class
│   │   ├── linkedin_scraper.py # LinkedIn scraper
│   │   ├── indeed_scraper.py   # Indeed scraper
│   │   └── scraper_factory.py  # Scraper factory
│   └── services/
│       ├── __init__.py
│       ├── job_service.py      # Job business logic
│       └── notification_service.py # Email notifications
├── requirements.txt
├── env.example
├── run.py                      # Easy startup script
├── test_setup.py               # Setup verification
├── scripts/
│   └── setup.py                # Automated setup script
├── examples/
│   └── basic_usage.py          # Usage examples
└── README.md
```

## Database Schema

### Users
- `id`: Primary key
- `email`: User email (unique)
- `name`: User name
- `created_at`: Account creation timestamp
- `is_active`: Account status

### Search Profiles
- `id`: Primary key
- `user_id`: Foreign key to users
- `name`: Profile name
- `keywords`: List of search keywords
- `location`: Preferred location
- `job_type`: remote/hybrid/onsite/any
- `experience_level`: entry/mid/senior/any
- `salary_min/max`: Salary range
- `is_active`: Profile status

### Job Listings
- `id`: Primary key
- `external_id`: Unique ID from job site
- `title`: Job title
- `company`: Company name
- `location`: Job location
- `job_type`: remote/hybrid/onsite
- `salary_min/max`: Salary range
- `description`: Job description
- `requirements`: List of requirements
- `skills`: List of required skills
- `application_url`: Apply link
- `source_site`: Job site (linkedin/indeed/etc)
- `posted_date`: When job was posted
- `scraped_at`: When we scraped it
- `job_metadata`: Additional site-specific data

### Notifications
- `id`: Primary key
- `user_id`: Foreign key to users
- `job_listing_id`: Foreign key to job listings
- `search_profile_id`: Foreign key to search profiles
- `notification_type`: email/webhook
- `status`: sent/failed/pending
- `sent_at`: Notification timestamp

## Configuration Options

### Scraping Settings
- `SCRAPE_INTERVAL_MINUTES`: How often to run automated scraping (default: 30)
- `MAX_RETRIES`: Maximum retry attempts for failed scrapes (default: 3)
- `REQUEST_DELAY_SECONDS`: Delay between requests to avoid rate limiting (default: 2)

### Job Sites
**Currently Enabled:**
- `LINKEDIN_ENABLED`: LinkedIn scraping (default: true)

**Available but Disabled by Default:**
- `INDEED_ENABLED`: Indeed scraping (default: false)
- `GLASSDOOR_ENABLED`: Glassdoor scraping (default: false)
- `MONSTER_ENABLED`: Monster scraping (default: false)
- `DICE_ENABLED`: Dice scraping (default: false)
- `CAREERBUILDER_ENABLED`: CareerBuilder scraping (default: false)

**To enable additional sites, update your .env file:**
```env
INDEED_ENABLED=true
GLASSDOOR_ENABLED=true
# etc.
```

### Email Configuration
Configure SMTP settings for email notifications:
- `SMTP_SERVER`: SMTP server (e.g., smtp.gmail.com)
- `SMTP_PORT`: SMTP port (usually 587 for TLS)
- `SMTP_USERNAME`: Your email address
- `SMTP_PASSWORD`: App password (not regular password)
- `FROM_EMAIL`: Sender email address

## Advanced Features

### Custom Scrapers
To add support for new job sites:

1. Create a new scraper class in `app/scrapers/`
2. Extend `BaseScraper` and implement required methods
3. Add the scraper to `ScraperFactory`
4. Update configuration settings

### Email Templates
Customize email notifications by modifying the HTML templates in `NotificationService`.

<!-- ### Database Migrations
For production, use Alembic for database migrations:

```bash
# Initialize Alembic
alembic init alembic

# Create a migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head
``` -->

<!-- ## Monitoring and Logging

The application includes comprehensive logging:
- Scraping performance metrics
- Error tracking and reporting
- Database operation logs
- Email notification status

Check logs for:
- Scraping success/failure rates
- Database performance
- Email delivery status
- System health metrics -->

<!-- ## Production Deployment

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Using Docker Compose

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://user:password@db/job_scraper
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=job_scraper
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
``` -->


## License

This project is licensed under the MIT License.
