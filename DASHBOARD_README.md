# NoFluffJobs IT Market Dashboard

## Running the Dashboard

### Prerequisites

1. **Database initialized** with sample data:
   ```bash
   python scripts/init_database.py
   python scripts/populate_sample_data.py
   ```

2. **Dependencies installed**:
   ```bash
   pip install -r requirements.txt
   ```

### Launch Dashboard

```bash
streamlit run src/dashboard/app.py
```

The dashboard will open in your browser at `http://localhost:8501`

## Dashboard Features

### 5 Main Sections

#### 1. 💰 Salaries
- Salary distribution histogram
- Salary by seniority level (junior/mid/senior)
- Average salary by technology
- Salary trends over time
- Salary by location type (remote/office/hybrid)
- Detailed salary statistics

#### 2. 📈 Technology Trends
- Top 20 most in-demand technologies
- Technology popularity trends over time
- Distribution by category (language/framework/database/cloud/tool)
- Technology demand heatmap
- Detailed technology statistics

#### 3. 🗺️ Geographic Distribution
- Jobs by city (top 15)
- Location type distribution (remote/office/hybrid)
- Regional comparison
- Location types by city
- Remote work percentage trend
- Detailed location statistics

#### 4. 🔧 Skills Analysis
- Top technologies by category
- Highest paying technologies
- Technology co-occurrence (coming soon)
- Skills demand analysis

#### 5. 📊 Market Overview
- Dataset summary
- Recent activity
- Recent job postings table
- Key metrics at a glance

### Key Metrics (Top of Dashboard)

- **Total Active Jobs**: Current number of active job postings
- **Average Salary**: Average across all jobs with salary data
- **Remote Jobs %**: Percentage of remote positions
- **Top Technology**: Most in-demand technology

### Filters (Sidebar)

- **Date Range**: Filter data by time period
  - Last 7 days
  - Last 30 days
  - Last 90 days
  - All time
  - Custom range

- **Refresh Data**: Clear cache and reload data

## Dashboard Architecture

```
src/dashboard/
├── app.py                      # Main Streamlit application
├── utils/
│   └── data_loader.py         # Database query functions
└── components/
    ├── salary_charts.py       # Salary visualizations
    ├── tech_trends.py         # Technology trend charts
    └── geo_charts.py          # Geographic visualizations
```

## Data Flow

```
Database (jobs.db)
    ↓
DashboardDataLoader (cached queries)
    ↓
Streamlit App (with filters)
    ↓
Plotly Charts (interactive visualizations)
```

## Performance Features

- **Data Caching**: Dashboard data cached for 1 hour using `@st.cache_data`
- **Resource Caching**: Database connection cached using `@st.cache_resource`
- **Lazy Loading**: Charts load only when tabs are selected
- **Optimized Queries**: Pre-aggregated metrics for faster loading

## Tips for Use

1. **Date Range**: Use "Last 30 days" for best performance with sample data
2. **Refresh**: Click "Refresh Data" after running ETL pipeline to see new data
3. **Interactive Charts**: All Plotly charts support:
   - Zoom (box select)
   - Pan
   - Hover for details
   - Download as PNG

4. **Full Screen**: Click expand icon on any chart for full-screen view

## Customization

### Change Theme
Edit `.streamlit/config.toml`:
```toml
[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

### Modify KPIs
Edit `src/dashboard/app.py`, function `load_dashboard_data()`

### Add New Charts
1. Create visualization function in appropriate component file
2. Import in `app.py`
3. Add to relevant tab

## Troubleshooting

### Dashboard won't start
- Check that `data/jobs.db` exists
- Verify Streamlit is installed: `pip install streamlit`

### No data showing
- Run: `python scripts/populate_sample_data.py`
- Click "Refresh Data" in sidebar

### Charts are empty
- Check date range filter
- Verify data exists for selected period
- Check browser console for errors

## Next Steps

1. **Real Data**: Run ETL pipeline to scrape real NoFluffJobs data
   ```bash
   python scripts/run_etl.py
   ```

2. **Automation**: Set up GitHub Actions for daily updates

3. **Deployment**: Deploy to Streamlit Cloud for public access

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review database with `python scripts/show_db_info.py`
- Verify data with SQL queries
