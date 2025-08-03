from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "sqlite:///./job_scraper.db"
    
    # Email Configuration
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    from_email: Optional[str] = None
    
    # Firecrawl Configuration
    firecrawl_api_key: Optional[str] = None
    
    # Application Settings
    secret_key: str = "your-secret-key-change-this-in-production"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Scraping Settings
    scrape_interval_minutes: int = 30
    max_retries: int = 3
    request_delay_seconds: int = 2
    
    # Job Sites Configuration
    linkedin_enabled: bool = True
    indeed_enabled: bool = False
    glassdoor_enabled: bool = False
    monster_enabled: bool = False
    dice_enabled: bool = False
    careerbuilder_enabled: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings() 