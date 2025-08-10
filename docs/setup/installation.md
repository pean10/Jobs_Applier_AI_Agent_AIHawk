# M&A Job Application System - Installation Guide

## Prerequisites

- Python 3.9 or higher
- Chrome browser (for web scraping)
- Git (for repository cloning)
- 8GB+ RAM recommended
- Stable internet connection

## Step-by-Step Installation

### 1. System Requirements Check

```bash
# Check Python version
python --version  # Should be 3.9+

# Check Chrome installation
google-chrome --version  # or chrome --version on some systems

# Check available memory
free -h  # Linux/Mac
```

### 2. Repository Setup

```bash
# Clone the repository
git clone <repository-url>
cd aihawk-ma-system

# Create virtual environment
python -m venv ma_env

# Activate virtual environment
# On Linux/Mac:
source ma_env/bin/activate
# On Windows:
ma_env\Scripts\activate
```

### 3. Dependencies Installation

```bash
# Install M&A-specific requirements
pip install -r requirements_ma.txt

# Verify installation
python -c "import streamlit, selenium, pandas; print('Dependencies installed successfully')"
```

### 4. ChromeDriver Setup

The system uses webdriver-manager to automatically handle ChromeDriver, but you can also install manually:

```bash
# Automatic (recommended)
# ChromeDriver will be downloaded automatically on first run

# Manual installation (if needed)
# Download from: https://chromedriver.chromium.org/
# Add to PATH or place in project directory
```

### 5. Environment Configuration

```bash
# Initialize M&A environment
python main_ma.py --mode setup
```

This creates:
- `data_folder/ma_config.yaml` - M&A-specific configuration
- `data_folder/ma_resume_profile.yaml` - Resume template
- `data_folder/output/` - Output directory
- `log/ma_applications/` - Logging directory

### 6. API Keys Configuration

Edit `data_folder/secrets.yaml`:

```yaml
# Required
llm_api_key: 'your-openai-api-key-here'

# Optional (for enhanced functionality)
linkedin_api_key: 'your-linkedin-api-key'
indeed_api_key: 'your-indeed-api-key'
google_maps_api_key: 'your-google-maps-api-key'

# Email configuration (for follow-ups)
email_password: 'your-app-specific-password'
```

### 7. Resume Profile Setup

Customize `data_folder/ma_resume_profile.yaml` with your information:

```yaml
personal_information:
  name: "Your Full Name"
  surname: "Your Surname"
  city: "Rockville Centre"
  country: "United States"
  email: "your.email@example.com"
  phone: "+1-XXX-XXX-XXXX"
  linkedin: "https://linkedin.com/in/yourprofile"

experience_details:
  - position: "M&A Analyst"
    company: "Previous Company"
    employment_period: "01/2022 - Present"
    location: "New York, NY"
    industry: "Investment Banking"
    key_responsibilities:
      - responsibility_1: "Conducted financial analysis for M&A transactions"
      - responsibility_2: "Built DCF and LBO models"
      - responsibility_3: "Managed due diligence processes"
    skills_acquired:
      - "Financial Modeling"
      - "Due Diligence"
      - "Valuation Analysis"
```

### 8. M&A Configuration

Review and customize `data_folder/ma_config.yaml`:

```yaml
# Geographic targeting
target_location: "Rockville Centre, NY"
search_radius_miles: 25

# Application limits
daily_application_limit: 15
weekly_application_limit: 75

# M&A relevance threshold
min_ma_relevance_score: 70.0

# Target keywords
ma_keywords:
  - "M&A"
  - "Mergers and Acquisitions"
  - "Investment Banking"
  - "Corporate Finance"
  - "Private Equity"
```

### 9. Verification Test

```bash
# Run system test
python main_ma.py --mode test
```

Expected output:
```
🧪 Running M&A System Test...
✓ Configuration validation passed
✓ M&A Application Manager initialized
✓ Database connection successful
✓ Job scraper initialized
✓ Resume optimizer working - extracted X keywords
🎉 All M&A system tests passed!
```

## Common Installation Issues

### Issue: ChromeDriver Not Found
```bash
# Solution: Update webdriver-manager
pip install --upgrade webdriver-manager

# Or set Chrome path manually
export CHROME_PATH="/usr/bin/google-chrome"
```

### Issue: SSL Certificate Errors
```bash
# Solution: Update certificates
pip install --upgrade certifi
```

### Issue: Memory Errors
```bash
# Solution: Increase swap space or use lighter models
# Edit ma_config.yaml:
job_scraping:
  max_concurrent_requests: 2  # Reduce from default 5
  batch_size: 10  # Reduce from default 20
```

### Issue: API Rate Limiting
```bash
# Solution: Adjust rate limits in configuration
rate_limiting:
  requests_per_minute: 30  # Reduce from default 60
  delay_between_requests: 2  # Increase from default 1
```

## Performance Optimization

### For Better Performance:
```yaml
# In ma_config.yaml
performance:
  enable_caching: true
  cache_duration_hours: 24
  parallel_processing: true
  max_workers: 4
```

### For Lower Resource Usage:
```yaml
# In ma_config.yaml
resource_optimization:
  headless_browser: true
  disable_images: true
  disable_javascript: false  # Keep true for M&A sites
  memory_limit_mb: 2048
```

## Next Steps

After successful installation:

1. **Test Run**: `python main_ma.py --mode run` (single session)
2. **Dashboard**: `python main_ma.py --mode dashboard` (analytics)
3. **Scheduled**: `python main_ma.py --mode run --schedule` (automated)

## Troubleshooting

If you encounter issues:

1. Check the [Troubleshooting Guide](troubleshooting.md)
2. Review log files in `log/ma_applications/`
3. Verify all configuration files are properly formatted
4. Ensure all API keys are valid and have sufficient quotas

## Security Considerations

- Store API keys securely
- Use app-specific passwords for email
- Regularly rotate credentials
- Monitor usage quotas
- Keep dependencies updated

## Updates and Maintenance

```bash
# Update dependencies
pip install --upgrade -r requirements_ma.txt

# Update configuration templates
python main_ma.py --mode setup --force-update

# Backup data before updates
cp -r data_folder data_folder_backup_$(date +%Y%m%d)
```

---

**Installation Complete!** 🎉

You're now ready to start your automated M&A job search. Begin with a test run to ensure everything is working correctly.