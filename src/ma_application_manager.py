"""
M&A Application Manager
Coordinates the entire M&A job application process
"""
import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from email.mime.base import MimeBase
from email import encoders

from src.logging import logger
from src.ma_job_scraper import MAJobScraper, MAJobListing
from src.ma_job_filter import MAJobFilter
from src.ma_resume_optimizer import MAResumeOptimizer
from src.libs.resume_and_cover_builder import ResumeFacade, ResumeGenerator, StyleManager
from src.resume_schemas.resume import Resume
from src.utils.chrome_utils import init_browser

@dataclass
class ApplicationRecord:
    """Record of a job application"""
    job_id: str
    job_title: str
    company: str
    application_date: datetime
    status: str  # 'submitted', 'responded', 'rejected', 'interview'
    response_date: Optional[datetime] = None
    notes: str = ""
    follow_up_sent: bool = False
    ma_relevance_score: float = 0.0

class MAApplicationManager:
    """Manages the complete M&A job application workflow"""
    
    def __init__(self, config: Dict, api_key: str):
        self.config = config
        self.api_key = api_key
        self.db_path = Path("data_folder/output/ma_applications.db")
        self.setup_database()
        
        # Initialize components
        self.job_scraper = MAJobScraper(config)
        self.job_filter = MAJobFilter()
        self.resume_optimizer = MAResumeOptimizer()
        
        # Email configuration
        self.email_config = {
            'smtp_server': config.get('smtp_server', 'smtp.gmail.com'),
            'smtp_port': config.get('smtp_port', 587),
            'email': config.get('user_email', ''),
            'password': config.get('email_password', '')
        }
        
        # Application limits
        self.daily_application_limit = config.get('daily_application_limit', 15)
        self.weekly_application_limit = config.get('weekly_application_limit', 75)

    def setup_database(self):
        """Initialize SQLite database for tracking applications"""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE,
                job_title TEXT,
                company TEXT,
                job_url TEXT,
                application_date TIMESTAMP,
                status TEXT,
                response_date TIMESTAMP,
                notes TEXT,
                follow_up_sent BOOLEAN DEFAULT FALSE,
                ma_relevance_score REAL,
                resume_path TEXT,
                cover_letter_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_search_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_date DATE,
                jobs_found INTEGER,
                applications_submitted INTEGER,
                response_rate REAL,
                notes TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized for M&A application tracking")

    def run_daily_job_search(self) -> Dict:
        """Execute daily M&A job search and application process"""
        logger.info("Starting daily M&A job search and application process")
        
        session_stats = {
            'date': datetime.now().date(),
            'jobs_found': 0,
            'applications_submitted': 0,
            'high_priority_jobs': 0,
            'errors': []
        }
        
        try:
            # Check daily application limits
            if not self._can_submit_applications():
                logger.warning("Daily/weekly application limits reached")
                return session_stats
            
            # 1. Scrape new M&A jobs
            logger.info("Scraping M&A job opportunities...")
            raw_jobs = self.job_scraper.get_all_ma_jobs()
            session_stats['jobs_found'] = len(raw_jobs)
            
            # 2. Filter and prioritize jobs
            logger.info("Filtering and prioritizing M&A jobs...")
            filtered_jobs = self.job_filter.filter_ma_jobs(
                [asdict(job) for job in raw_jobs], 
                min_score=70.0
            )
            prioritized_jobs = self.job_filter.prioritize_applications(filtered_jobs)
            session_stats['high_priority_jobs'] = len(prioritized_jobs)
            
            # 3. Apply to top jobs
            applications_submitted = 0
            for job_data in prioritized_jobs[:self.daily_application_limit]:
                try:
                    if self._already_applied(job_data['title'], job_data['company']):
                        logger.info(f"Already applied to {job_data['title']} at {job_data['company']}")
                        continue
                    
                    success = self._submit_application(job_data)
                    if success:
                        applications_submitted += 1
                        logger.info(f"Successfully applied to {job_data['title']} at {job_data['company']}")
                    
                    # Rate limiting
                    import time
                    time.sleep(30)  # 30 seconds between applications
                    
                except Exception as e:
                    error_msg = f"Error applying to {job_data.get('title', 'Unknown')}: {e}"
                    logger.error(error_msg)
                    session_stats['errors'].append(error_msg)
            
            session_stats['applications_submitted'] = applications_submitted
            
            # 4. Send follow-up emails for previous applications
            self._send_follow_up_emails()
            
            # 5. Save session statistics
            self._save_session_stats(session_stats)
            
        except Exception as e:
            logger.error(f"Error in daily job search process: {e}")
            session_stats['errors'].append(str(e))
        
        finally:
            self.job_scraper.cleanup()
        
        logger.info(f"Daily job search completed: {session_stats}")
        return session_stats

    def _can_submit_applications(self) -> bool:
        """Check if we can submit more applications based on limits"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check daily limit
        today = datetime.now().date()
        cursor.execute(
            "SELECT COUNT(*) FROM applications WHERE DATE(application_date) = ?",
            (today,)
        )
        daily_count = cursor.fetchone()[0]
        
        # Check weekly limit
        week_ago = today - timedelta(days=7)
        cursor.execute(
            "SELECT COUNT(*) FROM applications WHERE DATE(application_date) > ?",
            (week_ago,)
        )
        weekly_count = cursor.fetchone()[0]
        
        conn.close()
        
        can_apply = (daily_count < self.daily_application_limit and 
                    weekly_count < self.weekly_application_limit)
        
        if not can_apply:
            logger.warning(f"Application limits reached - Daily: {daily_count}/{self.daily_application_limit}, Weekly: {weekly_count}/{self.weekly_application_limit}")
        
        return can_apply

    def _already_applied(self, job_title: str, company: str) -> bool:
        """Check if we've already applied to this job/company combination"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT COUNT(*) FROM applications WHERE job_title = ? AND company = ?",
            (job_title, company)
        )
        count = cursor.fetchone()[0]
        conn.close()
        
        return count > 0

    def _submit_application(self, job_data: Dict) -> bool:
        """Submit application for a specific M&A job"""
        try:
            # Load user resume
            resume_path = Path("data_folder/plain_text_resume.yaml")
            with open(resume_path, 'r') as f:
                resume_content = f.read()
            
            resume = Resume(resume_content)
            
            # Optimize resume for this specific job
            optimized_resume_data = self.resume_optimizer.optimize_resume_for_ma_job(
                resume, job_data.get('description', '')
            )
            
            # Generate tailored resume and cover letter
            style_manager = StyleManager()
            available_styles = style_manager.get_styles()
            if available_styles:
                # Use first available style
                first_style = list(available_styles.keys())[0]
                style_manager.set_selected_style(first_style)
            
            resume_generator = ResumeGenerator()
            resume_generator.set_resume_object(resume)
            
            driver = init_browser()
            
            resume_facade = ResumeFacade(
                api_key=self.api_key,
                style_manager=style_manager,
                resume_generator=resume_generator,
                resume_object=resume,
                output_path=Path("data_folder/output")
            )
            
            resume_facade.set_driver(driver)
            
            # Create job URL simulation for resume generation
            job_url = job_data.get('url', 'https://example.com/job')
            
            # For demo purposes, we'll create a simple job description page
            job_html = f"""
            <html>
            <body>
                <h1>{job_data.get('title', 'M&A Position')}</h1>
                <h2>{job_data.get('company', 'Company')}</h2>
                <p>{job_data.get('description', 'M&A role description')}</p>
            </body>
            </html>
            """
            
            # Save temporary job page
            temp_job_file = Path("data_folder/output/temp_job.html")
            with open(temp_job_file, 'w') as f:
                f.write(job_html)
            
            # Use file:// URL for local file
            file_url = f"file://{temp_job_file.absolute()}"
            resume_facade.link_to_job(file_url)
            
            # Generate tailored resume
            resume_pdf, resume_filename = resume_facade.create_resume_pdf_job_tailored()
            
            # Generate cover letter
            cover_letter_pdf, cover_letter_filename = resume_facade.create_cover_letter()
            
            # Save application record
            job_id = f"{job_data.get('company', '').replace(' ', '_')}_{job_data.get('title', '').replace(' ', '_')}"
            
            application_record = ApplicationRecord(
                job_id=job_id,
                job_title=job_data.get('title', ''),
                company=job_data.get('company', ''),
                application_date=datetime.now(),
                status='submitted',
                ma_relevance_score=job_data.get('ma_score', 0.0)
            )
            
            self._save_application_record(application_record, job_data.get('url', ''))
            
            # Clean up temporary files
            if temp_job_file.exists():
                temp_job_file.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Error submitting application: {e}")
            return False

    def _save_application_record(self, record: ApplicationRecord, job_url: str):
        """Save application record to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO applications 
            (job_id, job_title, company, job_url, application_date, status, 
             ma_relevance_score, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            record.job_id,
            record.job_title,
            record.company,
            job_url,
            record.application_date,
            record.status,
            record.ma_relevance_score,
            record.notes
        ))
        
        conn.commit()
        conn.close()

    def _send_follow_up_emails(self):
        """Send follow-up emails for applications submitted 5-7 days ago"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Find applications from 5-7 days ago that haven't had follow-ups
        start_date = datetime.now() - timedelta(days=7)
        end_date = datetime.now() - timedelta(days=5)
        
        cursor.execute('''
            SELECT job_id, job_title, company, application_date 
            FROM applications 
            WHERE application_date BETWEEN ? AND ? 
            AND follow_up_sent = FALSE 
            AND status = 'submitted'
        ''', (start_date, end_date))
        
        applications = cursor.fetchall()
        
        for app in applications:
            try:
                self._send_follow_up_email(app[1], app[2])  # title, company
                
                # Mark follow-up as sent
                cursor.execute(
                    "UPDATE applications SET follow_up_sent = TRUE WHERE job_id = ?",
                    (app[0],)
                )
                
                logger.info(f"Sent follow-up email for {app[1]} at {app[2]}")
                
            except Exception as e:
                logger.error(f"Error sending follow-up email for {app[1]}: {e}")
        
        conn.commit()
        conn.close()

    def _send_follow_up_email(self, job_title: str, company: str):
        """Send a follow-up email for a specific application"""
        if not self.email_config['email'] or not self.email_config['password']:
            logger.warning("Email configuration not set, skipping follow-up email")
            return
        
        subject = f"Following up on {job_title} application"
        
        body = f"""
        Dear Hiring Manager,

        I hope this email finds you well. I wanted to follow up on my recent application for the {job_title} position at {company}.

        I am very excited about the opportunity to contribute to your M&A team and would welcome the chance to discuss how my experience in financial modeling, due diligence, and deal execution can add value to your organization.

        I would be happy to provide any additional information you might need or to schedule a conversation at your convenience.

        Thank you for your time and consideration.

        Best regards,
        [Your Name]
        """
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.email_config['email']
            msg['To'] = "hr@example.com"  # This would need to be extracted from job posting
            msg['Subject'] = subject
            
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['email'], self.email_config['password'])
            
            text = msg.as_string()
            server.sendmail(self.email_config['email'], "hr@example.com", text)
            server.quit()
            
        except Exception as e:
            logger.error(f"Error sending follow-up email: {e}")
            raise

    def _save_session_stats(self, stats: Dict):
        """Save job search session statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO job_search_sessions 
            (session_date, jobs_found, applications_submitted, notes)
            VALUES (?, ?, ?, ?)
        ''', (
            stats['date'],
            stats['jobs_found'],
            stats['applications_submitted'],
            json.dumps(stats)
        ))
        
        conn.commit()
        conn.close()

    def get_application_statistics(self) -> Dict:
        """Get comprehensive application statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total applications
        cursor.execute("SELECT COUNT(*) FROM applications")
        total_applications = cursor.fetchone()[0]
        
        # Applications by status
        cursor.execute("SELECT status, COUNT(*) FROM applications GROUP BY status")
        status_counts = dict(cursor.fetchall())
        
        # Response rate
        responded = status_counts.get('responded', 0) + status_counts.get('interview', 0)
        response_rate = (responded / total_applications * 100) if total_applications > 0 else 0
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        cursor.execute("SELECT COUNT(*) FROM applications WHERE application_date > ?", (week_ago,))
        recent_applications = cursor.fetchone()[0]
        
        # Top companies applied to
        cursor.execute("""
            SELECT company, COUNT(*) as count 
            FROM applications 
            GROUP BY company 
            ORDER BY count DESC 
            LIMIT 10
        """)
        top_companies = cursor.fetchall()
        
        conn.close()
        
        return {
            'total_applications': total_applications,
            'status_breakdown': status_counts,
            'response_rate': round(response_rate, 2),
            'recent_applications': recent_applications,
            'top_companies': top_companies
        }

    def generate_daily_report(self) -> str:
        """Generate a daily activity report"""
        stats = self.get_application_statistics()
        
        report = f"""
        M&A Job Application Daily Report - {datetime.now().strftime('%Y-%m-%d')}
        
        📊 Overall Statistics:
        • Total Applications: {stats['total_applications']}
        • Response Rate: {stats['response_rate']}%
        • Recent Activity (7 days): {stats['recent_applications']} applications
        
        📈 Status Breakdown:
        """
        
        for status, count in stats['status_breakdown'].items():
            report += f"• {status.title()}: {count}\n        "
        
        report += f"""
        
        🏢 Top Target Companies:
        """
        
        for company, count in stats['top_companies'][:5]:
            report += f"• {company}: {count} applications\n        "
        
        return report