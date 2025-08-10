"""
M&A Job Filter Module
Specialized filtering and prioritization for Mergers & Acquisitions job opportunities
"""
import re
from typing import List, Dict, Set
from dataclasses import dataclass
from src.logging import logger

@dataclass
class MAJobCriteria:
    """Criteria specific to M&A job filtering"""
    target_titles: Set[str]
    required_skills: Set[str]
    preferred_companies: Set[str]
    location_radius_miles: int
    salary_range: tuple
    experience_levels: Set[str]

class MAJobFilter:
    """Advanced filtering system for M&A job opportunities"""
    
    def __init__(self):
        self.ma_keywords = {
            'primary': {
                'mergers', 'acquisitions', 'm&a', 'merger', 'acquisition',
                'investment banking', 'corporate finance', 'private equity',
                'deal', 'transaction', 'due diligence', 'valuation'
            },
            'secondary': {
                'lbo', 'leveraged buyout', 'dcf', 'financial modeling',
                'pitch book', 'synergy', 'integration', 'divestiture',
                'restructuring', 'capital markets', 'equity research'
            },
            'skills': {
                'excel', 'bloomberg', 'powerpoint', 'financial analysis',
                'modeling', 'cfa', 'mba', 'accounting', 'finance'
            }
        }
        
        self.target_companies = {
            'bulge_bracket': {
                'goldman sachs', 'jpmorgan', 'morgan stanley', 'bank of america',
                'citigroup', 'barclays', 'credit suisse', 'deutsche bank'
            },
            'boutique': {
                'evercore', 'moelis', 'lazard', 'centerview', 'perella weinberg',
                'greenhill', 'rothschild', 'pjt partners', 'guggenheim'
            },
            'consulting': {
                'mckinsey', 'bain', 'bcg', 'deloitte', 'pwc', 'ey', 'kpmg'
            },
            'private_equity': {
                'blackstone', 'kkr', 'carlyle', 'apollo', 'tpg', 'warburg pincus'
            }
        }
        
        self.geographic_targets = {
            'primary': ['new york', 'manhattan', 'nyc', 'rockville centre'],
            'secondary': ['long island', 'brooklyn', 'queens', 'jersey city', 'stamford']
        }

    def calculate_ma_relevance_score(self, job_description: str, job_title: str) -> float:
        """Calculate relevance score for M&A positions (0-100)"""
        score = 0.0
        description_lower = job_description.lower()
        title_lower = job_title.lower()
        
        # Title scoring (40% weight)
        title_score = 0
        for keyword in self.ma_keywords['primary']:
            if keyword in title_lower:
                title_score += 10
        title_score = min(title_score, 40)
        
        # Description scoring (60% weight)
        desc_score = 0
        
        # Primary keywords (30 points max)
        primary_matches = sum(1 for kw in self.ma_keywords['primary'] if kw in description_lower)
        desc_score += min(primary_matches * 5, 30)
        
        # Secondary keywords (20 points max)
        secondary_matches = sum(1 for kw in self.ma_keywords['secondary'] if kw in description_lower)
        desc_score += min(secondary_matches * 3, 20)
        
        # Skills keywords (10 points max)
        skills_matches = sum(1 for kw in self.ma_keywords['skills'] if kw in description_lower)
        desc_score += min(skills_matches * 2, 10)
        
        total_score = title_score + desc_score
        logger.debug(f"M&A relevance score for '{job_title}': {total_score}")
        return total_score

    def is_target_company(self, company_name: str) -> bool:
        """Check if company is a target M&A employer"""
        company_lower = company_name.lower()
        
        for category, companies in self.target_companies.items():
            for target_company in companies:
                if target_company in company_lower:
                    logger.debug(f"Found target company: {company_name} ({category})")
                    return True
        return False

    def extract_salary_range(self, job_description: str) -> tuple:
        """Extract salary information from job description"""
        salary_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*)\s*-\s*\$(\d{1,3}(?:,\d{3})*)',
            r'(\d{1,3}(?:,\d{3})*)\s*-\s*(\d{1,3}(?:,\d{3})*)\s*k',
            r'\$(\d{1,3})k\s*-\s*\$(\d{1,3})k'
        ]
        
        for pattern in salary_patterns:
            match = re.search(pattern, job_description, re.IGNORECASE)
            if match:
                try:
                    low = int(match.group(1).replace(',', ''))
                    high = int(match.group(2).replace(',', ''))
                    if 'k' in pattern:
                        low *= 1000
                        high *= 1000
                    return (low, high)
                except ValueError:
                    continue
        
        return (0, 0)

    def filter_ma_jobs(self, jobs: List[Dict], min_score: float = 60.0) -> List[Dict]:
        """Filter and rank jobs based on M&A relevance"""
        filtered_jobs = []
        
        for job in jobs:
            try:
                # Calculate M&A relevance score
                score = self.calculate_ma_relevance_score(
                    job.get('description', ''),
                    job.get('title', '')
                )
                
                # Check if meets minimum score threshold
                if score >= min_score:
                    job['ma_score'] = score
                    job['is_target_company'] = self.is_target_company(job.get('company', ''))
                    job['salary_range'] = self.extract_salary_range(job.get('description', ''))
                    filtered_jobs.append(job)
                    
            except Exception as e:
                logger.error(f"Error filtering job {job.get('title', 'Unknown')}: {e}")
                continue
        
        # Sort by M&A relevance score (descending)
        filtered_jobs.sort(key=lambda x: x['ma_score'], reverse=True)
        
        logger.info(f"Filtered {len(filtered_jobs)} M&A-relevant jobs from {len(jobs)} total jobs")
        return filtered_jobs

    def prioritize_applications(self, jobs: List[Dict]) -> List[Dict]:
        """Prioritize job applications based on multiple factors"""
        def priority_score(job):
            score = job.get('ma_score', 0)
            
            # Boost for target companies
            if job.get('is_target_company', False):
                score += 20
            
            # Boost for salary range alignment
            salary_range = job.get('salary_range', (0, 0))
            if salary_range[0] >= 120000:  # Target salary threshold
                score += 15
            
            # Boost for location preference
            location = job.get('location', '').lower()
            if any(target in location for target in self.geographic_targets['primary']):
                score += 10
            elif any(target in location for target in self.geographic_targets['secondary']):
                score += 5
            
            return score
        
        prioritized_jobs = sorted(jobs, key=priority_score, reverse=True)
        
        # Add priority rank to each job
        for i, job in enumerate(prioritized_jobs):
            job['priority_rank'] = i + 1
            job['priority_score'] = priority_score(job)
        
        logger.info(f"Prioritized {len(prioritized_jobs)} M&A jobs for application")
        return prioritized_jobs