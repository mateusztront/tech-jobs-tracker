# NoFluffJobs IT Market Dashboard - Project Summary

## 🎯 Project Overview

A complete data analytics platform that automatically scrapes NoFluffJobs daily to track IT job market trends in Poland. Features real-time dashboards, historical trend analysis, and automated data collection.

**Built by:** Data Engineer with 4 years of experience in Python and SQL
**Purpose:** Portfolio project demonstrating end-to-end data engineering skills
**Status:** ✅ Fully Functional (Phases 1-5 Complete)

## 📊 Key Features

- **Automated Daily Scraping**: GitHub Actions scrapes NoFluffJobs at 6 AM UTC daily
- **Historical Tracking**: Maintains snapshots to analyze trends over time
- **Interactive Dashboard**: Streamlit-based with 19 different visualizations
- **Comprehensive ETL**: Extract → Transform → Load pipeline with data quality checks
- **Real-time Monitoring**: Auto-creates GitHub issues on scraper failures

### Analytics Capabilities

1. **Salary Analysis**
   - Distribution across all jobs
   - Comparison by technology (Top 20)
   - Trends over time
   - Breakdown by seniority level (Junior/Mid/Senior)
   - Comparison by location type (Remote/Office/Hybrid)

2. **Technology Trends**
   - Most in-demand technologies
   - Popularity trends over time
   - Category distribution (Language/Framework/Database/Cloud/Tool)
   - Demand heatmap
   - Technology co-occurrence

3. **Geographic Insights**
   - Jobs by city (Top 15)
   - Regional distribution
   - Remote work percentage trend
   - Location type distribution

4. **Skills Intelligence**
   - Top paying technologies
   - Skills by category
   - Demand patterns

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Automation)               │
│         Daily at 6:00 AM UTC │ Manual Trigger Available      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Web Scraper (Phase 2)                      │
│  • Rate Limiter (2-5s delays)  • Circuit Breaker            │
│  • HTML Parser                  • Error Handling             │
│  • Pagination Handler           • Retry Logic (3x)           │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   ETL Pipeline (Phase 3)                     │
│  ┌───────────┐   ┌────────────┐   ┌──────────┐             │
│  │ Extractor │ → │Transformer │ → │  Loader  │             │
│  │ Validate  │   │ Normalize  │   │  Upsert  │             │
│  │  Clean    │   │Categorize  │   │  Track   │             │
│  └───────────┘   └────────────┘   └──────────┘             │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                 SQLite Database (Phase 1)                    │
│  • 7 Tables (job_postings, job_snapshots, salaries, etc.)   │
│  • 10 Indexes for performance                               │
│  • Foreign key constraints                                  │
│  • Historical snapshots for trend analysis                  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│             Streamlit Dashboard (Phase 4)                    │
│  • 5 Interactive Tabs  • 19 Visualizations                  │
│  • KPI Metrics         • Date Filtering                     │
│  • Data Caching (1hr)  • Responsive Layout                  │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Project Structure

```
nofluffjobs-dashboard/
├── .github/workflows/          # GitHub Actions automation
│   ├── daily_scrape.yml       # Daily scraping workflow
│   └── update_stats.yml       # Statistics updater
│
├── src/
│   ├── scraper/               # Web scraping components
│   │   ├── nofluff_scraper.py # Main scraper (2-phase: URLs → Details)
│   │   ├── parser.py          # HTML parsing logic
│   │   └── rate_limiter.py    # Rate limiting + circuit breaker
│   │
│   ├── database/              # Database layer
│   │   ├── models.py          # Schema definitions (7 tables)
│   │   └── db_manager.py      # Connection management, transactions
│   │
│   ├── etl/                   # ETL pipeline
│   │   ├── extractor.py       # Data extraction & validation
│   │   ├── transformer.py     # Normalization & categorization
│   │   └── loader.py          # Database loading with upserts
│   │
│   └── dashboard/             # Streamlit dashboard
│       ├── app.py             # Main dashboard application
│       ├── components/        # Visualization components
│       │   ├── salary_charts.py    (6 charts)
│       │   ├── tech_trends.py      (6 charts)
│       │   └── geo_charts.py       (7 charts)
│       └── utils/
│           └── data_loader.py # Optimized database queries
│
├── config/                    # Configuration files
│   ├── config.yaml           # General settings
│   └── scraper_config.yaml   # Scraper parameters
│
├── data/
│   └── jobs.db               # SQLite database (committed by Actions)
│
├── logs/                     # Application logs
├── scripts/                  # Utility scripts
│   ├── init_database.py     # Initialize database
│   ├── run_scraper.py       # Manual scraper execution
│   ├── run_etl.py           # Complete ETL pipeline
│   ├── populate_sample_data.py  # Sample data generator
│   ├── test_database.py     # Database tests
│   ├── test_scraper.py      # Scraper tests
│   └── test_etl.py          # ETL tests
│
├── tests/                    # Unit tests
├── README.md                 # Main documentation
├── DASHBOARD_README.md       # Dashboard usage guide
├── GITHUB_ACTIONS_SETUP.md   # Automation setup guide
└── requirements.txt          # Python dependencies
```

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Language** | Python 3.11+ | Core development |
| **Database** | SQLite | Data storage with ACID compliance |
| **Web Scraping** | Requests + BeautifulSoup | HTML parsing and extraction |
| **Dashboard** | Streamlit + Plotly | Interactive visualizations |
| **Data Processing** | Pandas | Data manipulation and analysis |
| **Automation** | GitHub Actions | Scheduled daily execution |
| **Configuration** | YAML | Settings management |
| **Testing** | Pytest | Component testing |

## 📈 Database Schema

### Core Tables (7)

1. **job_postings** - Main job entries
   - Fields: job_id (PK), title, company_name, url, first_seen_date, last_seen_date, is_active
   - Purpose: Track unique job postings and lifecycle

2. **job_snapshots** - Historical snapshots
   - Fields: job_id, snapshot_date, description, location_type, city, region, seniority_level
   - Purpose: Daily snapshots for trend analysis

3. **salaries** - Compensation data
   - Fields: job_id, snapshot_date, salary_min, salary_max, salary_avg, currency, is_b2b
   - Purpose: Track salary ranges and types

4. **technologies** - Normalized tech list
   - Fields: id (PK), name (unique), category
   - Purpose: Categorize technologies (30+ tracked)

5. **job_technologies** - Many-to-many relationships
   - Fields: job_id, technology_id, proficiency_level, snapshot_date
   - Purpose: Link jobs to required technologies

6. **daily_metrics** - Aggregated statistics
   - Fields: metric_date, total_jobs, remote_jobs, avg_salary_pln, median_salary_pln
   - Purpose: Pre-calculated metrics for dashboard performance

7. **scrape_runs** - Execution metadata
   - Fields: run_date, jobs_found, jobs_new, jobs_updated, status, duration_seconds
   - Purpose: Monitor scraper health and performance

### Indexes (10)
- Optimized queries on job_id, snapshot_date, active status, and technology names
- Ensures fast dashboard loading even with large datasets

## 🔄 Data Flow

### 1. Scraping Phase
```
NoFluffJobs Website
    ↓ (Rate-limited requests)
Raw HTML Pages
    ↓ (BeautifulSoup parsing)
Raw Job Data (JSON)
```

### 2. ETL Phase
```
Raw Job Data
    ↓ (Extractor: validate, clean)
Extracted Data
    ↓ (Transformer: normalize, categorize)
Transformed Data
    ↓ (Loader: upsert, track)
SQLite Database
```

### 3. Dashboard Phase
```
SQLite Database
    ↓ (Optimized queries)
Cached DataFrames (1hr TTL)
    ↓ (Plotly visualizations)
Interactive Dashboard
```

## 🚀 Key Accomplishments

### Phase 1: Foundation ✅
- ✅ 7-table database schema with foreign keys
- ✅ Transaction-safe database manager
- ✅ Comprehensive configuration system
- ✅ Project structure following best practices

### Phase 2: Web Scraper ✅
- ✅ Ethical scraping with 2-5s delays
- ✅ Circuit breaker pattern (prevents hammering on failures)
- ✅ Exponential backoff retry logic (3 attempts)
- ✅ Pagination handling
- ✅ 429 rate limit detection and handling

### Phase 3: ETL Pipeline ✅
- ✅ Salary normalization: "15 000 - 20 000 PLN" → {min: 15000, max: 20000, avg: 17500}
- ✅ Location standardization: "Warszawa / Zdalnie" → {city: Warszawa, type: hybrid}
- ✅ Technology categorization: 30+ technologies across 5 categories
- ✅ Idempotent loading (no duplicates on re-run)
- ✅ Job expiration tracking

### Phase 4: Dashboard ✅
- ✅ 19 interactive visualizations
- ✅ 5 analytical tabs
- ✅ KPI metrics dashboard
- ✅ Date range filtering
- ✅ Data caching for performance
- ✅ Responsive layout

### Phase 5: Automation ✅
- ✅ Daily GitHub Actions workflow
- ✅ Auto-commit database updates
- ✅ Failure monitoring (auto-creates issues)
- ✅ Artifact upload (logs retention)
- ✅ Statistics updater workflow

## 📊 Sample Results

With sample data (100 jobs):
- **Technologies Tracked**: 30 unique
- **Cities**: 8 Polish cities
- **Salary Range**: 6,000 - 28,000 PLN
- **Location Types**: Remote (33%), Office (33%), Hybrid (33%)
- **Seniority Levels**: Junior, Mid, Senior distribution

## 🎓 Learning Outcomes

This project demonstrates proficiency in:

1. **Data Engineering**
   - ETL pipeline design and implementation
   - Database schema design with normalization
   - Data quality and validation
   - Historical data tracking

2. **Web Scraping**
   - Ethical scraping practices
   - Rate limiting and retry logic
   - HTML parsing and extraction
   - Error handling and resilience

3. **Data Visualization**
   - Interactive dashboard design
   - Multiple visualization types
   - User experience considerations
   - Performance optimization

4. **Automation & DevOps**
   - GitHub Actions workflows
   - Scheduled task execution
   - Monitoring and alerting
   - CI/CD concepts

5. **Software Engineering**
   - Modular architecture
   - Code organization
   - Testing practices
   - Documentation

## 🔮 Future Enhancements (Optional)

1. **Advanced Analytics**
   - Salary prediction ML model
   - Job recommendation system
   - Skill gap analysis
   - Market saturation indicators

2. **Extended Coverage**
   - Multiple job boards (JustJoin.IT, Pracuj.pl)
   - International markets
   - Comparison analysis

3. **Real-time Features**
   - Email alerts for matching jobs
   - Webhook notifications
   - Real-time dashboard updates

4. **Scalability**
   - PostgreSQL migration (for larger datasets)
   - Redis caching
   - Horizontal scaling

5. **Deployment**
   - Streamlit Cloud deployment
   - Docker containerization
   - API for programmatic access

## 📝 Documentation

| Document | Purpose |
|----------|---------|
| README.md | Project overview and quick start |
| DASHBOARD_README.md | Dashboard usage and features |
| GITHUB_ACTIONS_SETUP.md | Automation setup guide |
| PROJECT_SUMMARY.md | Comprehensive project overview (this file) |

## 🏆 Project Highlights

- **Fully Functional**: All 5 phases implemented and tested
- **Production-Ready**: Error handling, logging, monitoring
- **Well-Documented**: 4 comprehensive documentation files
- **Tested**: Component tests for database, scraper, and ETL
- **Automated**: Hands-free daily operation via GitHub Actions
- **Scalable**: Designed to handle growing datasets
- **Ethical**: Respects website terms and implements rate limiting

## 📞 Support & Contributing

This is a personal portfolio project. Feel free to:
- Fork and adapt for your own use
- Reference in your own projects
- Learn from the implementation

## ⚖️ License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- **NoFluffJobs** - Data source (educational use only)
- **Streamlit** - Dashboard framework
- **Plotly** - Visualization library
- **GitHub Actions** - Automation platform

---

**Project Status**: ✅ Complete (5/6 phases)
**Last Updated**: 2026-01-06
**Built with**: ❤️ and lots of ☕
