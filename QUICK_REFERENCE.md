# Quick Reference Guide

## 🚀 Quick Start Commands

```bash
# 1. Setup (first time only)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_database.py

# 2. Populate with sample data
python scripts/populate_sample_data.py

# 3. Run dashboard
streamlit run src/dashboard/app.py
```

## 📋 Common Commands

### Database Operations

```bash
# Initialize empty database
python scripts/init_database.py

# Populate with sample data (100 jobs)
python scripts/populate_sample_data.py

# Show database information
python scripts/show_db_info.py

# Direct SQL query
sqlite3 data/jobs.db "SELECT COUNT(*) FROM job_postings;"
```

### Scraping & ETL

```bash
# Run complete ETL pipeline (scrape → transform → load)
python scripts/run_etl.py

# Run scraper only (save to JSON)
python scripts/run_scraper.py

# Note: Scraped data is saved to logs/scraped_jobs_*.json
```

### Testing

```bash
# Test database components
python scripts/test_database.py

# Test scraper components
python scripts/test_scraper.py

# Test ETL pipeline
python scripts/test_etl.py

# Run all pytest tests
pytest tests/
```

### Dashboard

```bash
# Run dashboard locally
streamlit run src/dashboard/app.py

# Run on specific port
streamlit run src/dashboard/app.py --server.port 8502

# Run in browser mode (auto-open browser)
streamlit run src/dashboard/app.py --server.headless false
```

## 🔍 Useful SQL Queries

### Database Statistics

```sql
-- Total active jobs
SELECT COUNT(*) FROM job_postings WHERE is_active = 1;

-- Jobs by city
SELECT city, COUNT(*) as count
FROM job_snapshots
GROUP BY city
ORDER BY count DESC
LIMIT 10;

-- Average salary by technology
SELECT t.name, AVG(s.salary_avg) as avg_salary, COUNT(*) as jobs
FROM technologies t
JOIN job_technologies jt ON t.id = jt.technology_id
JOIN salaries s ON jt.job_id = s.job_id
GROUP BY t.name
ORDER BY avg_salary DESC
LIMIT 10;

-- Remote job percentage
SELECT
    location_type,
    COUNT(*) * 100.0 / (SELECT COUNT(*) FROM job_snapshots) as percentage
FROM job_snapshots
GROUP BY location_type;

-- Technology popularity trend (last 7 days)
SELECT
    t.name,
    jt.snapshot_date,
    COUNT(*) as job_count
FROM technologies t
JOIN job_technologies jt ON t.id = jt.technology_id
WHERE jt.snapshot_date >= date('now', '-7 days')
GROUP BY t.name, jt.snapshot_date
ORDER BY jt.snapshot_date, job_count DESC;
```

### Data Maintenance

```sql
-- Clean old snapshots (keep last 90 days)
DELETE FROM job_snapshots WHERE snapshot_date < date('now', '-90 days');
DELETE FROM salaries WHERE snapshot_date < date('now', '-90 days');
DELETE FROM job_technologies WHERE snapshot_date < date('now', '-90 days');

-- Vacuum database (reclaim space)
VACUUM;

-- Check database size
SELECT page_count * page_size / 1024 / 1024 as size_mb
FROM pragma_page_count(), pragma_page_size();

-- Verify data integrity
PRAGMA integrity_check;
PRAGMA foreign_key_check;
```

## ⚙️ Configuration

### Scraper Settings

Edit `config/scraper_config.yaml`:

```yaml
rate_limiting:
  min_delay_seconds: 2      # Minimum delay between requests
  max_delay_seconds: 5      # Maximum delay
  requests_per_minute: 20   # Rate limit

scraping:
  max_pages: 100            # Maximum pages to scrape
  max_jobs_per_run: 1000    # Limit total jobs
```

### Dashboard Settings

Edit `config/config.yaml`:

```yaml
dashboard:
  title: "NoFluffJobs IT Market Dashboard"
  auto_refresh_minutes: 60  # Cache TTL
  default_timeframe: 30     # Default date range (days)
```

## 🐛 Troubleshooting

### Dashboard won't start

```bash
# Check if database exists
ls -lh data/jobs.db

# If not, initialize
python scripts/init_database.py
python scripts/populate_sample_data.py

# Check Streamlit version
streamlit --version

# Reinstall if needed
pip install --upgrade streamlit
```

### Scraper fails

```bash
# Check logs
tail -50 logs/etl_*.log

# Test scraper components
python scripts/test_scraper.py

# Run with reduced load
# Edit config/scraper_config.yaml:
#   max_jobs_per_run: 10
python scripts/run_etl.py
```

### Database locked error

```bash
# Close any open connections
# Kill Python processes using the database
pkill -f "python.*app.py"

# Or restart computer if needed
```

### GitHub Actions fails

```bash
# Check Actions tab on GitHub for logs
# Common fixes:

# 1. Enable read/write permissions
#    Settings → Actions → General → Workflow permissions
#    Select "Read and write permissions"

# 2. Ensure database is tracked
git add -f data/jobs.db
git commit -m "Add database"
git push
```

## 📊 Dashboard Features

### Keyboard Shortcuts

- `Ctrl + R` - Refresh dashboard
- `F11` - Toggle full screen
- `Ctrl + Click` on chart - Download as PNG

### Date Range Filters

- **Last 7 days** - Recent trends
- **Last 30 days** - Monthly overview (recommended)
- **Last 90 days** - Quarterly analysis
- **All time** - Complete dataset
- **Custom** - Specific date range

### Chart Interactions

All Plotly charts support:
- **Hover** - View detailed information
- **Zoom** - Box select to zoom in
- **Pan** - Click and drag to move
- **Reset** - Double-click to reset view
- **Download** - Camera icon to save as PNG

## 🔄 Typical Workflows

### Daily Local Development

```bash
# Morning: Check for new data
streamlit run src/dashboard/app.py

# If needed: Run ETL to get fresh data
python scripts/run_etl.py

# View updated dashboard
# (Auto-refreshes every hour or click Refresh button)
```

### Weekly Maintenance

```bash
# Check scraper health
python scripts/show_db_info.py

# Review logs
ls -ltr logs/etl_*.log | tail -7

# Vacuum database
sqlite3 data/jobs.db "VACUUM;"

# Verify GitHub Actions
# Visit: https://github.com/YOUR_USERNAME/nofluffjobs-dashboard/actions
```

### Adding Real Data

```bash
# Run complete pipeline
python scripts/run_etl.py

# This will:
# 1. Scrape NoFluffJobs
# 2. Extract and validate data
# 3. Transform (normalize) data
# 4. Load into database
# 5. Update daily metrics

# View results in dashboard
streamlit run src/dashboard/app.py
```

## 🎯 Best Practices

### 1. Regular Backups

```bash
# Backup database
cp data/jobs.db data/jobs_backup_$(date +%Y%m%d).db

# Or use git
git add data/jobs.db
git commit -m "Backup: $(date +%Y-%m-%d)"
```

### 2. Monitor Database Size

```bash
# Check size
du -h data/jobs.db

# If > 100 MB, consider:
# - Cleaning old data
# - Using Git LFS
# - Moving to PostgreSQL
```

### 3. Keep Dependencies Updated

```bash
# Check outdated packages
pip list --outdated

# Update all
pip install --upgrade -r requirements.txt

# Freeze new versions
pip freeze > requirements.txt
```

## 📦 Useful Python Snippets

### Custom Analysis

```python
import pandas as pd
from src.database.db_manager import DatabaseManager

# Connect to database
db = DatabaseManager("data/jobs.db")

# Custom query
query = """
    SELECT title, salary_avg, city
    FROM job_postings jp
    JOIN job_snapshots js ON jp.job_id = js.job_id
    JOIN salaries s ON jp.job_id = s.job_id
    WHERE jp.is_active = 1 AND s.currency = 'PLN'
    ORDER BY s.salary_avg DESC
    LIMIT 10
"""

# Load into DataFrame
df = pd.DataFrame(db.fetch_all(query))
print(df)
```

### Export Data

```python
# Export to CSV
df.to_csv('top_jobs.csv', index=False)

# Export to Excel
df.to_excel('top_jobs.xlsx', index=False)

# Export to JSON
df.to_json('top_jobs.json', orient='records', indent=2)
```

## 🌐 URLs & Resources

| Resource | URL |
|----------|-----|
| Dashboard (local) | http://localhost:8501 |
| NoFluffJobs | https://nofluffjobs.com |
| Streamlit Docs | https://docs.streamlit.io |
| Plotly Docs | https://plotly.com/python |
| GitHub Actions Docs | https://docs.github.com/en/actions |

## 💡 Pro Tips

1. **Use sample data for development** - Faster iteration
2. **Cache dashboard queries** - Already implemented, but customize TTL if needed
3. **Run ETL during off-peak hours** - Respect NoFluffJobs servers
4. **Monitor GitHub Actions usage** - Free tier has limits on private repos
5. **Backup before major changes** - Especially database schema changes

---

**Need more help?** Check the full documentation:
- [README.md](README.md) - Project overview
- [DASHBOARD_README.md](DASHBOARD_README.md) - Dashboard guide
- [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) - Automation setup
- [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) - Complete project details
