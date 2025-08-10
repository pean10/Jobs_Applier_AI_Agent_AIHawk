"""
M&A Resume Optimization Module
Specialized resume tailoring for Mergers & Acquisitions roles
"""
import re
from typing import Dict, List, Set
from src.logging import logger
from src.resume_schemas.resume import Resume

class MAResumeOptimizer:
    """Optimize resumes specifically for M&A job applications"""
    
    def __init__(self):
        self.ma_skill_keywords = {
            'technical': {
                'financial modeling', 'dcf analysis', 'lbo modeling', 'valuation',
                'due diligence', 'merger model', 'accretion/dilution analysis',
                'comparable company analysis', 'precedent transactions',
                'synergy analysis', 'integration planning'
            },
            'software': {
                'excel', 'vba', 'bloomberg terminal', 'factset', 'capital iq',
                'powerpoint', 'word', 'outlook', 'refinitiv', 'pitchbook'
            },
            'certifications': {
                'cfa', 'chartered financial analyst', 'cpa', 'mba',
                'series 7', 'series 63', 'frm', 'financial risk manager'
            },
            'soft_skills': {
                'client relationship management', 'presentation skills',
                'project management', 'team leadership', 'analytical thinking',
                'attention to detail', 'time management', 'communication'
            }
        }
        
        self.ma_action_verbs = {
            'analyzed', 'evaluated', 'modeled', 'structured', 'executed',
            'managed', 'led', 'developed', 'created', 'built', 'designed',
            'negotiated', 'advised', 'presented', 'coordinated', 'facilitated'
        }

    def extract_job_keywords(self, job_description: str) -> Set[str]:
        """Extract relevant keywords from M&A job description"""
        keywords = set()
        description_lower = job_description.lower()
        
        # Extract all M&A skill keywords present in job description
        for category, skills in self.ma_skill_keywords.items():
            for skill in skills:
                if skill in description_lower:
                    keywords.add(skill)
        
        # Extract specific M&A terms
        ma_terms = [
            'merger', 'acquisition', 'divestiture', 'spin-off', 'joint venture',
            'private equity', 'leveraged buyout', 'management buyout',
            'strategic buyer', 'financial buyer', 'investment banking'
        ]
        
        for term in ma_terms:
            if term in description_lower:
                keywords.add(term)
        
        logger.debug(f"Extracted {len(keywords)} M&A keywords from job description")
        return keywords

    def optimize_experience_descriptions(self, experience_details: List[Dict], 
                                       target_keywords: Set[str]) -> List[Dict]:
        """Optimize experience descriptions for M&A relevance"""
        optimized_experience = []
        
        for exp in experience_details:
            optimized_exp = exp.copy()
            
            # Optimize responsibilities
            if 'key_responsibilities' in exp:
                optimized_responsibilities = []
                
                for resp in exp['key_responsibilities']:
                    resp_text = resp.get('responsibility', '') if isinstance(resp, dict) else str(resp)
                    
                    # Enhance with M&A-specific language
                    enhanced_resp = self._enhance_responsibility_text(resp_text, target_keywords)
                    optimized_responsibilities.append({'responsibility': enhanced_resp})
                
                optimized_exp['key_responsibilities'] = optimized_responsibilities
            
            # Optimize skills acquired
            if 'skills_acquired' in exp:
                enhanced_skills = self._enhance_skills_list(exp['skills_acquired'], target_keywords)
                optimized_exp['skills_acquired'] = enhanced_skills
            
            optimized_experience.append(optimized_exp)
        
        return optimized_experience

    def _enhance_responsibility_text(self, text: str, target_keywords: Set[str]) -> str:
        """Enhance responsibility text with M&A-specific terminology"""
        enhanced_text = text
        
        # Replace generic terms with M&A-specific ones
        replacements = {
            'financial analysis': 'M&A financial analysis and due diligence',
            'analysis': 'valuation analysis',
            'models': 'financial models including DCF and LBO analyses',
            'presentations': 'pitch books and management presentations',
            'clients': 'M&A clients and strategic buyers',
            'deals': 'M&A transactions',
            'projects': 'M&A deal execution projects'
        }
        
        for generic, specific in replacements.items():
            if generic in text.lower() and any(kw in target_keywords for kw in specific.split()):
                enhanced_text = re.sub(re.escape(generic), specific, enhanced_text, flags=re.IGNORECASE)
        
        # Add quantifiable metrics where possible
        if 'transaction' in enhanced_text.lower() and '$' not in enhanced_text:
            enhanced_text += ' (transactions valued at $50M-$2B)'
        
        return enhanced_text

    def _enhance_skills_list(self, skills: List[str], target_keywords: Set[str]) -> List[str]:
        """Enhance skills list with M&A-relevant skills"""
        enhanced_skills = skills.copy()
        
        # Add M&A-specific skills that match target keywords
        ma_skills_to_add = [
            'Financial Modeling (DCF, LBO, Merger Models)',
            'Due Diligence and Valuation Analysis',
            'M&A Transaction Execution',
            'Bloomberg Terminal and FactSet',
            'Pitch Book Development',
            'Client Relationship Management'
        ]
        
        for skill in ma_skills_to_add:
            skill_keywords = skill.lower().split()
            if any(kw in target_keywords for kw in skill_keywords) and skill not in enhanced_skills:
                enhanced_skills.append(skill)
        
        return enhanced_skills

    def generate_ma_summary(self, resume: Resume, job_description: str) -> str:
        """Generate M&A-focused professional summary"""
        target_keywords = self.extract_job_keywords(job_description)
        
        # Extract years of experience
        years_exp = self._extract_years_of_experience(resume.experience_details)
        
        # Build summary components
        summary_parts = []
        
        # Opening statement
        if years_exp >= 5:
            summary_parts.append(f"Senior M&A professional with {years_exp}+ years of experience")
        elif years_exp >= 2:
            summary_parts.append(f"Experienced M&A analyst with {years_exp} years of experience")
        else:
            summary_parts.append("Results-driven finance professional with M&A expertise")
        
        # Core competencies
        core_skills = []
        if 'financial modeling' in target_keywords:
            core_skills.append('advanced financial modeling')
        if 'due diligence' in target_keywords:
            core_skills.append('comprehensive due diligence')
        if 'valuation' in target_keywords:
            core_skills.append('valuation analysis')
        
        if core_skills:
            summary_parts.append(f"specializing in {', '.join(core_skills)}")
        
        # Industry focus
        summary_parts.append("Proven track record in M&A transaction execution, client advisory, and deal structuring across multiple industries")
        
        # Technical skills
        tech_skills = []
        if 'excel' in target_keywords or 'bloomberg' in target_keywords:
            tech_skills.append('advanced Excel/VBA and Bloomberg Terminal proficiency')
        if 'powerpoint' in target_keywords:
            tech_skills.append('expert-level presentation development')
        
        if tech_skills:
            summary_parts.append(f"Strong technical skills including {', '.join(tech_skills)}")
        
        return '. '.join(summary_parts) + '.'

    def _extract_years_of_experience(self, experience_details: List[Dict]) -> int:
        """Extract total years of relevant M&A experience"""
        if not experience_details:
            return 0
        
        total_years = 0
        for exp in experience_details:
            employment_period = exp.get('employment_period', '')
            years = self._parse_employment_period(employment_period)
            
            # Weight M&A-relevant experience more heavily
            position = exp.get('position', '').lower()
            if any(term in position for term in ['m&a', 'investment banking', 'corporate finance']):
                total_years += years
            else:
                total_years += years * 0.5  # Partial credit for other finance roles
        
        return int(total_years)

    def _parse_employment_period(self, period: str) -> float:
        """Parse employment period string to extract years"""
        if not period:
            return 0
        
        # Handle various date formats
        period_lower = period.lower()
        if 'present' in period_lower or 'current' in period_lower:
            # Extract start year and calculate to present
            years = re.findall(r'\b(19|20)\d{2}\b', period)
            if years:
                start_year = int(years[0])
                current_year = 2024  # Update as needed
                return current_year - start_year
        
        # Extract all years from the period
        years = re.findall(r'\b(19|20)\d{2}\b', period)
        if len(years) >= 2:
            return int(years[-1]) - int(years[0])
        
        return 1  # Default to 1 year if can't parse

    def optimize_resume_for_ma_job(self, resume: Resume, job_description: str) -> Dict:
        """Comprehensive resume optimization for M&A job application"""
        target_keywords = self.extract_job_keywords(job_description)
        
        optimized_resume = {
            'personal_information': resume.personal_information,
            'professional_summary': self.generate_ma_summary(resume, job_description),
            'education_details': resume.education_details,
            'experience_details': self.optimize_experience_descriptions(
                resume.experience_details or [], target_keywords
            ),
            'projects': resume.projects,
            'achievements': resume.achievements,
            'certifications': resume.certifications,
            'languages': resume.languages,
            'interests': resume.interests,
            'target_keywords': list(target_keywords),
            'optimization_score': self._calculate_optimization_score(resume, target_keywords)
        }
        
        logger.info(f"Resume optimized for M&A role with score: {optimized_resume['optimization_score']}")
        return optimized_resume

    def _calculate_optimization_score(self, resume: Resume, target_keywords: Set[str]) -> float:
        """Calculate how well the resume matches M&A job requirements"""
        if not target_keywords:
            return 0.0
        
        # Count keyword matches in resume
        resume_text = str(resume).lower()
        matches = sum(1 for keyword in target_keywords if keyword in resume_text)
        
        # Calculate percentage match
        score = (matches / len(target_keywords)) * 100
        return round(score, 2)