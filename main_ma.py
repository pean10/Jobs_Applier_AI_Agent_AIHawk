"""
Main entry point for M&A Job Application System
Specialized version of AIHawk for M&A roles in Rockville Centre and NYC
"""
import sys
import json
import schedule
import time
from datetime import datetime
from pathlib import Path
import click
import inquirer
from typing import Dict, List

from src.logging import logger
from src.ma_application_manager import MAApplicationManager
from src.ma_dashboard import MADashboard
from main import ConfigValidator, FileManager

class MAConfigValidator(ConfigValidator):
    """Extended config validator for M&A-specific settings"""
    
    MA_REQUIRED_KEYS = {
        "target_location": str,
        "search_radius_miles": int,
        "daily_application_limit": int,
        "weekly_application_limit": int,
        "min_ma_relevance_score": float,
        "target_companies": list,
        "ma_keywords": list,
        "email_follow_up": bool
    }
    
    @classmethod
    def validate_ma_config(cls, config_path: Path) -> dict:
        """Validate M&A-specific configuration"""
        config = cls.load_yaml(config_path)
        
        # Validate M&A-specific keys
        for key, expected_type in cls.MA_REQUIRED_KEYS.items():
            if key not in config:
                # Set defaults for missing keys
                defaults = {
                    "target_location": "Rockville Centre, NY",
                    "search_radius_miles": 25,
                    "daily_application_limit": 15,
                    "weekly_application_limit": 75,
                    "min_ma_relevance_score": 70.0,
                    "target_companies": [],
                    "ma_keywords": ["M&A", "Mergers and Acquisitions", "Investment Banking"],
                    "email_follow_up": True
                }
                config[key] = defaults[key]
                logger.warning(f"Missing M&A config key '{key}', using default: {defaults[key]}")
            elif not isinstance(config[key], expected_type):
                raise ValueError(f"Invalid type for M&A config key '{key}'. Expected {expected_type.__name__}")
        
        # Validate search radius
        if not 5 <= config["search_radius_miles"] <= 50:
            raise ValueError("Search radius must be between 5 and 50 miles")
        
        # Validate application limits
        if config["daily_application_limit"] > 50:
            raise ValueError("Daily application limit cannot exceed 50")
        
        if config["weekly_application_limit"] > 200:
            raise ValueError("Weekly application limit cannot exceed 200")
        
        # Validate M&A relevance score
        if not 0 <= config["min_ma_relevance_score"] <= 100:
            raise ValueError("M&A relevance score must be between 0 and 100")
        
        return config

def create_ma_config_template():
    """Create M&A-specific configuration template"""
    ma_config = {
        # Geographic targeting
        "target_location": "Rockville Centre, NY",
        "search_radius_miles": 25,
        
        # Application limits
        "daily_application_limit": 15,
        "weekly_application_limit": 75,
        
        # M&A-specific settings
        "min_ma_relevance_score": 70.0,
        "ma_keywords": [
            "M&A", "Mergers and Acquisitions", "Investment Banking",
            "Corporate Finance", "Private Equity", "Deal Advisory",
            "Transaction Services", "Business Development"
        ],
        
        # Target company categories
        "target_companies": {
            "bulge_bracket": [
                "Goldman Sachs", "JPMorgan Chase", "Morgan Stanley",
                "Bank of America", "Citigroup", "Barclays"
            ],
            "boutique": [
                "Evercore", "Moelis & Company", "Lazard", "Centerview Partners",
                "Perella Weinberg Partners", "Greenhill & Co"
            ],
            "consulting": [
                "McKinsey & Company", "Bain & Company", "Boston Consulting Group",
                "Deloitte", "PwC", "EY", "KPMG"
            ],
            "private_equity": [
                "Blackstone", "KKR", "Carlyle Group", "Apollo Global Management",
                "TPG", "Warburg Pincus"
            ]
        },
        
        # Job board settings
        "job_boards": {
            "linkedin": True,
            "indeed": True,
            "glassdoor": True,
            "axial": False,  # Requires premium access
            "mergersclub": False  # Requires premium access
        },
        
        # Email settings
        "email_follow_up": True,
        "follow_up_delay_days": 5,
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587,
        "user_email": "",
        "email_password": "",
        
        # Resume optimization
        "resume_optimization": {
            "emphasize_ma_skills": True,
            "include_deal_experience": True,
            "highlight_financial_modeling": True,
            "add_industry_keywords": True
        },
        
        # Scheduling
        "auto_run_schedule": {
            "enabled": True,
            "run_time": "09:00",  # 9 AM daily
            "timezone": "America/New_York"
        }
    }
    
    config_path = Path("data_folder/ma_config.yaml")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    import yaml
    with open(config_path, 'w') as f:
        yaml.dump(ma_config, f, default_flow_style=False, indent=2)
    
    logger.info(f"Created M&A configuration template at {config_path}")
    return config_path

def setup_ma_environment():
    """Set up M&A-specific environment and files"""
    logger.info("Setting up M&A job application environment...")
    
    # Create necessary directories
    directories = [
        "data_folder/output",
        "data_folder/ma_resumes",
        "data_folder/ma_cover_letters",
        "log/ma_applications"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    # Create M&A config if it doesn't exist
    ma_config_path = Path("data_folder/ma_config.yaml")
    if not ma_config_path.exists():
        create_ma_config_template()
    
    # Create M&A-specific resume template if it doesn't exist
    ma_resume_path = Path("data_folder/ma_resume_profile.yaml")
    if not ma_resume_path.exists():
        logger.info("M&A resume profile not found. Please create one based on the template.")
    
    logger.info("M&A environment setup complete")

@click.command()
@click.option('--mode', type=click.Choice(['run', 'dashboard', 'setup', 'test']), 
              default='run', help='Operation mode')
@click.option('--schedule', is_flag=True, help='Run in scheduled mode')
@click.option('--config', type=click.Path(exists=True), 
              help='Path to M&A configuration file')
def main(mode: str, schedule: bool, config: str):
    """
    M&A Job Application System - Specialized AIHawk for M&A roles
    
    Targets M&A opportunities in Rockville Centre, NY and NYC area
    """
    try:
        logger.info("Starting M&A Job Application System")
        
        if mode == 'setup':
            setup_ma_environment()
            print("✅ M&A environment setup complete!")
            print("📝 Please review and customize the configuration files:")
            print("   - data_folder/ma_config.yaml")
            print("   - data_folder/ma_resume_profile.yaml")
            return
        
        # Validate data folder and files
        data_folder = Path("data_folder")
        secrets_file, work_prefs_file, resume_file, output_folder = FileManager.validate_data_folder(data_folder)
        
        # Load and validate configurations
        base_config = ConfigValidator.validate_config(work_prefs_file)
        llm_api_key = ConfigValidator.validate_secrets(secrets_file)
        
        # Load M&A-specific config
        ma_config_path = Path(config) if config else Path("data_folder/ma_config.yaml")
        if ma_config_path.exists():
            ma_config = MAConfigValidator.validate_ma_config(ma_config_path)
            base_config.update(ma_config)
        else:
            logger.warning("M&A config not found, using defaults")
            ma_config_path = create_ma_config_template()
            ma_config = MAConfigValidator.validate_ma_config(ma_config_path)
            base_config.update(ma_config)
        
        # Add file paths to config
        base_config["uploads"] = FileManager.get_uploads(resume_file)
        base_config["outputFileDirectory"] = output_folder
        
        if mode == 'dashboard':
            logger.info("Starting M&A Dashboard...")
            dashboard = MADashboard(base_config)
            dashboard.run_dashboard()
            
        elif mode == 'test':
            logger.info("Running M&A system test...")
            run_ma_test(base_config, llm_api_key)
            
        elif mode == 'run':
            if schedule:
                logger.info("Starting scheduled M&A job application system...")
                run_scheduled_ma_system(base_config, llm_api_key)
            else:
                logger.info("Running single M&A job search session...")
                run_single_ma_session(base_config, llm_api_key)
    
    except Exception as e:
        logger.error(f"Error in M&A job application system: {e}")
        raise

def run_single_ma_session(config: Dict, api_key: str):
    """Run a single M&A job search and application session"""
    try:
        # Initialize M&A application manager
        ma_manager = MAApplicationManager(config, api_key)
        
        # Run daily job search
        results = ma_manager.run_daily_job_search()
        
        # Generate and display report
        report = ma_manager.generate_daily_report()
        print("\n" + "="*60)
        print("M&A JOB APPLICATION SESSION COMPLETE")
        print("="*60)
        print(report)
        print("="*60)
        
        # Show statistics
        stats = ma_manager.get_application_statistics()
        print(f"\n📊 Session Results:")
        print(f"   • Jobs Found: {results['jobs_found']}")
        print(f"   • Applications Submitted: {results['applications_submitted']}")
        print(f"   • High Priority Jobs: {results['high_priority_jobs']}")
        print(f"   • Total Applications to Date: {stats['total_applications']}")
        print(f"   • Current Response Rate: {stats['response_rate']}%")
        
        if results['errors']:
            print(f"\n⚠️  Errors Encountered: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"   • {error}")
        
    except Exception as e:
        logger.error(f"Error in single M&A session: {e}")
        raise

def run_scheduled_ma_system(config: Dict, api_key: str):
    """Run M&A system on a schedule"""
    try:
        ma_manager = MAApplicationManager(config, api_key)
        
        # Schedule daily job search
        run_time = config.get('auto_run_schedule', {}).get('run_time', '09:00')
        schedule.every().day.at(run_time).do(
            lambda: ma_manager.run_daily_job_search()
        )
        
        print(f"🕒 M&A Job Application System scheduled to run daily at {run_time}")
        print("Press Ctrl+C to stop the scheduler")
        
        # Keep the scheduler running
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
            
    except KeyboardInterrupt:
        logger.info("Scheduled M&A system stopped by user")
    except Exception as e:
        logger.error(f"Error in scheduled M&A system: {e}")
        raise

def run_ma_test(config: Dict, api_key: str):
    """Run M&A system test"""
    try:
        print("🧪 Running M&A System Test...")
        
        # Test 1: Configuration validation
        print("✓ Configuration validation passed")
        
        # Test 2: Initialize components
        ma_manager = MAApplicationManager(config, api_key)
        print("✓ M&A Application Manager initialized")
        
        # Test 3: Database setup
        stats = ma_manager.get_application_statistics()
        print("✓ Database connection successful")
        
        # Test 4: Job scraping (limited test)
        from src.ma_job_scraper import MAJobScraper
        scraper = MAJobScraper(config)
        print("✓ Job scraper initialized")
        
        # Test 5: Resume optimization
        from src.ma_resume_optimizer import MAResumeOptimizer
        optimizer = MAResumeOptimizer()
        test_keywords = optimizer.extract_job_keywords("M&A Analyst position requiring financial modeling and due diligence experience")
        print(f"✓ Resume optimizer working - extracted {len(test_keywords)} keywords")
        
        print("\n🎉 All M&A system tests passed!")
        print(f"📊 Current application statistics: {stats}")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise

if __name__ == "__main__":
    main()