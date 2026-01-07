# Tech Jobs Tracker

A data analytics dashboard that scrapes multiple job boards to track IT job market trends. Currently supports NoFluffJobs with plans to add more sources. Analyzes salary ranges, technology popularity, remote work trends, geographic distribution, and required skills.

## Features

- **Daily Automated Scraping**: GitHub Actions workflow scrapes job boards every day
- **Historical Tracking**: Maintains snapshots to track trends over time
- **Interactive Dashboard**: Streamlit-based visualization with filters
- **Key Metrics**:
  - Salary ranges by technology and role
  - Technology popularity trends
  - Skills required by employers
  - Remote vs office job ratios
  - Geographic distribution across Polish cities

## Tech Stack

- **Python 3.11+**
- **Database**: SQLite
- **Web Scraping**: Requests + BeautifulSoup4
- **Dashboard**: Streamlit + Plotly
- **Automation**: GitHub Actions
- **Data Processing**: Pandas

## Project Structure

```
tech-jobs-tracker/
├── .github/workflows/       # GitHub Actions automation
├── src/
│   ├── scraper/            # Web scraping logic (supports multiple sites)
│   ├── database/           # Database models and manager
│   ├── etl/                # Data extraction, transformation, loading
│   └── dashboard/          # Streamlit dashboard and visualizations
├── config/                 # Configuration files
├── data/                   # SQLite database (gitignored)
├── logs/                   # Application logs
├── scripts/                # Utility scripts
└── tests/                  # Unit tests
```

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/tech-jobs-tracker.git
   cd tech-jobs-tracker
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize database**:
   ```bash
   python scripts/init_database.py
   ```

## Usage

### Quick Start

```bash
# 1. Populate with sample data
python scripts/populate_sample_data.py

# 2. Run dashboard
streamlit run src/dashboard/app.py
```

### Run Complete ETL Pipeline

Scrape, process, and load real data:
```bash
python scripts/run_etl.py
```

### Manual Scraping Only

```bash
python scripts/run_scraper.py
```

### View Dashboard

```bash
streamlit run src/dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Automated Daily Scraping

GitHub Actions workflow runs automatically every day at 6:00 AM UTC (8:00 AM Poland time).

**Setup:**
1. Push repository to GitHub
2. Enable Actions in repository settings
3. Workflow runs automatically

**Manual Trigger:**
- Go to Actions tab → Daily Job Scraper → Run workflow

See [GITHUB_ACTIONS_SETUP.md](GITHUB_ACTIONS_SETUP.md) for detailed setup instructions.

## Database Schema

- **job_postings**: Core job entries with unique IDs
- **job_snapshots**: Daily snapshots for historical tracking
- **salaries**: Salary ranges with currency and period
- **technologies**: Normalized list of technologies/skills
- **job_technologies**: Many-to-many relationship between jobs and skills
- **daily_metrics**: Pre-aggregated metrics for dashboard performance
- **scrape_runs**: Scraper execution metadata and monitoring

## Development Roadmap

### Phase 1: Foundation ✅
- [x] Project structure
- [x] Database schema (7 tables with indexes)
- [x] Configuration files
- [x] Database manager with transactions

### Phase 2: Web Scraper ✅
- [x] Rate limiter implementation (2-5s delays, exponential backoff)
- [x] HTML parser (job listings + details)
- [x] Main scraper logic (pagination, error handling)
- [x] Manual execution script
- [x] Circuit breaker pattern

### Phase 3: ETL Pipeline ✅
- [x] Data extractor (validation, cleaning)
- [x] Data transformer (salary normalization, location standardization, tech categorization)
- [x] Data loader (upserts, expiration tracking, daily metrics)
- [x] End-to-end pipeline script

### Phase 4: Dashboard ✅
- [x] Main Streamlit app (5 tabs, responsive layout)
- [x] Salary visualizations (6 different charts)
- [x] Technology trend charts (6 visualizations)
- [x] Geographic distribution maps (7 charts)
- [x] Skills analysis components
- [x] KPI metrics dashboard
- [x] Data caching and performance optimization

### Phase 5: Automation ✅
- [x] GitHub Actions workflow (daily at 6 AM UTC)
- [x] Statistics updater workflow
- [x] Monitoring and notifications (auto-create issues on failure)
- [x] Error handling and logging
- [x] Artifact upload (30-day retention)

### Phase 6: Polish & Deploy
- [x] Component tests (database, scraper, ETL)
- [x] Comprehensive documentation
- [ ] Unit tests (optional: additional coverage)
- [ ] Performance optimization (optional: database indexing)
- [ ] Deployment to Streamlit Cloud (optional)

## Configuration

Edit `config/config.yaml` for general settings and `config/scraper_config.yaml` for scraping parameters.

Key settings:
- **Rate limiting**: 2-5 seconds between requests
- **Max pages**: 100 pages per scrape
- **Retry attempts**: 3 attempts with exponential backoff

## Contributing

This is a personal project for learning and portfolio purposes. Feel free to fork and adapt for your own use.

## License

MIT License

## Disclaimer

This project is for educational purposes. Always respect website terms of service and implement ethical scraping practices:
- Rate limiting and delays between requests
- Respectful user-agent
- Checking robots.txt
- Scraping during off-peak hours

**Supported Job Boards:**
- NoFluffJobs (Poland) - Current implementation
- More sources planned for future releases

## Author

Data Engineer with 4 years of experience in Python and SQL
