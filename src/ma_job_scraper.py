"""
M&A Job Scraper Module
Specialized web scraping and API integration for M&A job opportunities
"""
import requests
import time
import json
from typing import List, Dict, Optional, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import re
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.logging import logger
from src.utils.chrome_utils import init_browser

@dataclass
class MAJobListing:
    """Data structure for M&A job listings"""
    title: str
    company: str
    location: str
    description: str
    url: str
    salary_range: Optional[str]
    posted_date: Optional[str]
    job_type: str
    experience_level: str
    source: str
    ma_relevance_score: float = 0.0

class MAJobScraper:
    """Advanced job scraper specialized for M&A opportunities"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.target_location = "Rockville Centre, NY"
        self.search_radius = 25  # miles
        self.driver = None
        
        # M&A-specific search terms
        self.ma_keywords = [
            "M&A", "Mergers and Acquisitions", "Investment Banking",
            "Corporate Finance", "Private Equity", "Deal Advisory",
            "Transaction Services", "Business Development",
            "Corporate Development", "Leveraged Buyout", "LBO"
        ]
        
        # Target companies in M&A space
        self.target_companies = {
            'bulge_bracket': [
                'Goldman Sachs', 'JPMorgan Chase', 'Morgan Stanley',
                'Bank of America', 'Citigroup', 'Barclays', 'Credit Suisse'
            ],
            'boutique': [
                'Evercore', 'Moelis & Company', 'Lazard', 'Centerview Partners',
                'Perella Weinberg Partners', 'Greenhill & Co', 'Rothschild'
            ],
            'consulting': [
                'McKinsey & Company', 'Bain & Company', 'Boston Consulting Group',
                'Deloitte', 'PwC', 'EY', 'KPMG'
            ],
            'private_equity': [
                'Blackstone', 'KKR', 'Carlyle Group', 'Apollo Global Management',
                'TPG', 'Warburg Pincus', 'Bain Capital'
            ]
        }

    def initialize_driver(self):
        """Initialize Selenium WebDriver"""
        if not self.driver:
            self.driver = init_browser()
            logger.info("Selenium WebDriver initialized for M&A job scraping")

    def scrape_linkedin_jobs(self, keywords: List[str], location: str) -> List[MAJobListing]:
        """Scrape M&A jobs from LinkedIn"""
        jobs = []
        self.initialize_driver()
        
        try:
            for keyword in keywords:
                search_url = f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}&distance=25"
                self.driver.get(search_url)
                time.sleep(3)
                
                # Scroll to load more jobs
                for _ in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                # Extract job listings
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".job-search-card")
                
                for card in job_cards[:20]:  # Limit to first 20 results per keyword
                    try:
                        title = card.find_element(By.CSS_SELECTOR, ".base-search-card__title").text
                        company = card.find_element(By.CSS_SELECTOR, ".base-search-card__subtitle").text
                        location_elem = card.find_element(By.CSS_SELECTOR, ".job-search-card__location")
                        job_location = location_elem.text if location_elem else ""
                        
                        # Get job URL
                        link_elem = card.find_element(By.CSS_SELECTOR, ".base-card__full-link")
                        job_url = link_elem.get_attribute("href")
                        
                        # Get job description (requires clicking into job)
                        description = self._get_linkedin_job_description(job_url)
                        
                        # Calculate M&A relevance score
                        relevance_score = self._calculate_ma_relevance(title, description, company)
                        
                        if relevance_score >= 60:  # Only include relevant M&A jobs
                            job = MAJobListing(
                                title=title,
                                company=company,
                                location=job_location,
                                description=description,
                                url=job_url,
                                salary_range=None,
                                posted_date=None,
                                job_type="Full-time",
                                experience_level="Mid-Senior",
                                source="LinkedIn",
                                ma_relevance_score=relevance_score
                            )
                            jobs.append(job)
                            
                    except Exception as e:
                        logger.warning(f"Error extracting LinkedIn job: {e}")
                        continue
                
                time.sleep(2)  # Rate limiting
                
        except Exception as e:
            logger.error(f"Error scraping LinkedIn jobs: {e}")
        
        logger.info(f"Scraped {len(jobs)} M&A-relevant jobs from LinkedIn")
        return jobs

    def scrape_indeed_jobs(self, keywords: List[str], location: str) -> List[MAJobListing]:
        """Scrape M&A jobs from Indeed"""
        jobs = []
        
        for keyword in keywords:
            try:
                # Indeed search URL
                search_url = f"https://www.indeed.com/jobs?q={keyword}&l={location}&radius=25"
                
                response = requests.get(search_url, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    job_cards = soup.find_all('div', class_='job_seen_beacon')
                    
                    for card in job_cards[:15]:  # Limit results
                        try:
                            title_elem = card.find('h2', class_='jobTitle')
                            if not title_elem:
                                continue
                                
                            title = title_elem.get_text(strip=True)
                            
                            company_elem = card.find('span', class_='companyName')
                            company = company_elem.get_text(strip=True) if company_elem else ""
                            
                            location_elem = card.find('div', class_='companyLocation')
                            job_location = location_elem.get_text(strip=True) if location_elem else ""
                            
                            # Get job URL
                            link_elem = title_elem.find('a')
                            job_url = f"https://www.indeed.com{link_elem['href']}" if link_elem else ""
                            
                            # Get job description
                            description = self._get_indeed_job_description(job_url)
                            
                            # Calculate M&A relevance
                            relevance_score = self._calculate_ma_relevance(title, description, company)
                            
                            if relevance_score >= 60:
                                job = MAJobListing(
                                    title=title,
                                    company=company,
                                    location=job_location,
                                    description=description,
                                    url=job_url,
                                    salary_range=None,
                                    posted_date=None,
                                    job_type="Full-time",
                                    experience_level="Mid-Senior",
                                    source="Indeed",
                                    ma_relevance_score=relevance_score
                                )
                                jobs.append(job)
                                
                        except Exception as e:
                            logger.warning(f"Error extracting Indeed job: {e}")
                            continue
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error scraping Indeed for keyword '{keyword}': {e}")
        
        logger.info(f"Scraped {len(jobs)} M&A-relevant jobs from Indeed")
        return jobs

    def scrape_glassdoor_jobs(self, keywords: List[str], location: str) -> List[MAJobListing]:
        """Scrape M&A jobs from Glassdoor"""
        jobs = []
        self.initialize_driver()
        
        try:
            for keyword in keywords:
                search_url = f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keyword}&locT=C&locId=1132348&radius=25"
                self.driver.get(search_url)
                time.sleep(3)
                
                # Handle potential popups
                try:
                    close_button = self.driver.find_element(By.CSS_SELECTOR, "[data-test='modal-close']")
                    close_button.click()
                    time.sleep(1)
                except:
                    pass
                
                # Extract job listings
                job_cards = self.driver.find_elements(By.CSS_SELECTOR, "[data-test='job-listing']")
                
                for card in job_cards[:10]:  # Limit results
                    try:
                        title_elem = card.find_element(By.CSS_SELECTOR, "[data-test='job-title']")
                        title = title_elem.text
                        
                        company_elem = card.find_element(By.CSS_SELECTOR, "[data-test='employer-name']")
                        company = company_elem.text
                        
                        location_elem = card.find_element(By.CSS_SELECTOR, "[data-test='job-location']")
                        job_location = location_elem.text
                        
                        # Get job URL
                        job_url = title_elem.get_attribute("href")
                        
                        # Get description (simplified for demo)
                        description = f"M&A role at {company} in {job_location}"
                        
                        # Calculate relevance
                        relevance_score = self._calculate_ma_relevance(title, description, company)
                        
                        if relevance_score >= 60:
                            job = MAJobListing(
                                title=title,
                                company=company,
                                location=job_location,
                                description=description,
                                url=job_url,
                                salary_range=None,
                                posted_date=None,
                                job_type="Full-time",
                                experience_level="Mid-Senior",
                                source="Glassdoor",
                                ma_relevance_score=relevance_score
                            )
                            jobs.append(job)
                            
                    except Exception as e:
                        logger.warning(f"Error extracting Glassdoor job: {e}")
                        continue
                
                time.sleep(2)
                
        except Exception as e:
            logger.error(f"Error scraping Glassdoor jobs: {e}")
        
        logger.info(f"Scraped {len(jobs)} M&A-relevant jobs from Glassdoor")
        return jobs

    def _get_linkedin_job_description(self, job_url: str) -> str:
        """Get detailed job description from LinkedIn job page"""
        try:
            self.driver.get(job_url)
            time.sleep(2)
            
            # Try to find job description
            description_elem = self.driver.find_element(By.CSS_SELECTOR, ".show-more-less-html__markup")
            return description_elem.text
            
        except Exception as e:
            logger.warning(f"Could not get LinkedIn job description: {e}")
            return ""

    def _get_indeed_job_description(self, job_url: str) -> str:
        """Get detailed job description from Indeed job page"""
        try:
            response = requests.get(job_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                desc_elem = soup.find('div', class_='jobsearch-jobDescriptionText')
                return desc_elem.get_text(strip=True) if desc_elem else ""
                
        except Exception as e:
            logger.warning(f"Could not get Indeed job description: {e}")
            
        return ""

    def _calculate_ma_relevance(self, title: str, description: str, company: str) -> float:
        """Calculate M&A relevance score for a job listing"""
        score = 0.0
        title_lower = title.lower()
        desc_lower = description.lower()
        company_lower = company.lower()
        
        # Title scoring (40% weight)
        ma_title_keywords = ['m&a', 'merger', 'acquisition', 'investment banking', 'corporate finance', 'private equity']
        for keyword in ma_title_keywords:
            if keyword in title_lower:
                score += 10
        
        # Description scoring (40% weight)
        ma_desc_keywords = [
            'due diligence', 'financial modeling', 'valuation', 'dcf', 'lbo',
            'leveraged buyout', 'deal', 'transaction', 'synergy', 'integration'
        ]
        for keyword in ma_desc_keywords:
            if keyword in desc_lower:
                score += 4
        
        # Company scoring (20% weight)
        for category, companies in self.target_companies.items():
            for target_company in companies:
                if target_company.lower() in company_lower:
                    score += 20
                    break
        
        return min(score, 100)  # Cap at 100

    def get_all_ma_jobs(self) -> List[MAJobListing]:
        """Aggregate M&A jobs from all sources"""
        all_jobs = []
        location = f"{self.target_location}, NY"
        
        # Scrape from multiple sources
        linkedin_jobs = self.scrape_linkedin_jobs(self.ma_keywords[:3], location)  # Limit keywords to avoid rate limiting
        indeed_jobs = self.scrape_indeed_jobs(self.ma_keywords[:3], location)
        glassdoor_jobs = self.scrape_glassdoor_jobs(self.ma_keywords[:2], location)
        
        all_jobs.extend(linkedin_jobs)
        all_jobs.extend(indeed_jobs)
        all_jobs.extend(glassdoor_jobs)
        
        # Remove duplicates based on title and company
        unique_jobs = []
        seen = set()
        
        for job in all_jobs:
            job_key = (job.title.lower(), job.company.lower())
            if job_key not in seen:
                seen.add(job_key)
                unique_jobs.append(job)
        
        # Sort by M&A relevance score
        unique_jobs.sort(key=lambda x: x.ma_relevance_score, reverse=True)
        
        logger.info(f"Found {len(unique_jobs)} unique M&A job opportunities")
        return unique_jobs

    def save_jobs_to_json(self, jobs: List[MAJobListing], filename: str = "ma_jobs.json"):
        """Save job listings to JSON file"""
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                'title': job.title,
                'company': job.company,
                'location': job.location,
                'description': job.description,
                'url': job.url,
                'salary_range': job.salary_range,
                'posted_date': job.posted_date,
                'job_type': job.job_type,
                'experience_level': job.experience_level,
                'source': job.source,
                'ma_relevance_score': job.ma_relevance_score,
                'scraped_at': datetime.now().isoformat()
            })
        
        with open(f"data_folder/output/{filename}", 'w') as f:
            json.dump(jobs_data, f, indent=2)
        
        logger.info(f"Saved {len(jobs)} M&A jobs to {filename}")

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            self.driver.quit()
            logger.info("WebDriver closed")