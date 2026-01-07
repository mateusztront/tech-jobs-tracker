"""
NoFluffJobs IT Market Dashboard - Main Streamlit App
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import date, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.dashboard.utils.data_loader import DashboardDataLoader
from src.dashboard.components import salary_charts, tech_trends, geo_charts


# Page configuration
st.set_page_config(
    page_title="NoFluffJobs IT Market Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_database():
    """Get database connection (cached)."""
    db_path = project_root / "data" / "jobs.db"
    return DatabaseManager(str(db_path))


@st.cache_data(ttl=3600)
def load_dashboard_data(_data_loader, date_from, date_to):
    """Load all dashboard data (cached for 1 hour)."""
    return {
        'jobs': _data_loader.get_active_jobs(date_from, date_to),
        'salary': _data_loader.get_salary_data(date_from, date_to),
        'technology': _data_loader.get_technology_data(date_from, date_to),
        'location': _data_loader.get_location_data(date_from, date_to),
        'salary_by_tech': _data_loader.get_salary_by_technology(top_n=20),
        'kpis': _data_loader.get_kpi_metrics(),
        'scrape_info': _data_loader.get_last_scrape_info()
    }


def main():
    """Main dashboard application."""

    # Header
    st.markdown('<div class="main-header">📊 NoFluffJobs IT Market Dashboard</div>', unsafe_allow_html=True)
    st.markdown("---")

    # Initialize database and data loader
    try:
        db = get_database()
        data_loader = DashboardDataLoader(db)
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.info("Please ensure the database exists. Run: python scripts/init_database.py")
        return

    # Sidebar
    with st.sidebar:
        st.title("🔍 Filters")

        # Date range selector
        st.subheader("Date Range")
        date_preset = st.selectbox(
            "Quick Select",
            ["Last 7 days", "Last 30 days", "Last 90 days", "All time", "Custom"]
        )

        if date_preset == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                date_from = st.date_input("From", value=date.today() - timedelta(days=30))
            with col2:
                date_to = st.date_input("To", value=date.today())
        elif date_preset == "All time":
            date_from = None
            date_to = None
        else:
            days = {"Last 7 days": 7, "Last 30 days": 30, "Last 90 days": 90}[date_preset]
            date_from = date.today() - timedelta(days=days)
            date_to = date.today()

        st.markdown("---")

        # Refresh button
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        # Info section
        st.markdown("---")
        st.subheader("ℹ️ About")
        st.markdown("""
        This dashboard analyzes IT job market trends from NoFluffJobs.

        **Data includes:**
        - Salary ranges
        - Technology demand
        - Location trends
        - Remote work statistics
        """)

    # Load data
    with st.spinner("Loading data..."):
        data = load_dashboard_data(data_loader, date_from, date_to)

    # Last update info
    scrape_info = data['scrape_info']
    st.caption(f"Last updated: {scrape_info['last_update']} | Status: {scrape_info['status']}")

    # KPI Metrics
    st.subheader("📈 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)

    kpis = data['kpis']

    with col1:
        st.metric(
            label="Total Active Jobs",
            value=f"{kpis['total_jobs']:,}",
            delta=f"+{scrape_info['jobs_new']}" if scrape_info['jobs_new'] > 0 else None
        )

    with col2:
        avg_salary = kpis['avg_salary']
        st.metric(
            label="Average Salary",
            value=f"{avg_salary:,.0f} PLN" if avg_salary > 0 else "N/A"
        )

    with col3:
        remote_pct = kpis['remote_pct']
        st.metric(
            label="Remote Jobs",
            value=f"{remote_pct:.1f}%" if remote_pct > 0 else "N/A"
        )

    with col4:
        st.metric(
            label="Top Technology",
            value=kpis['top_technology']
        )

    st.markdown("---")

    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💰 Salaries",
        "📈 Technology Trends",
        "🗺️ Geographic Distribution",
        "🔧 Skills Analysis",
        "📊 Overview"
    ])

    # Tab 1: Salaries
    with tab1:
        st.header("💰 Salary Analysis")

        if not data['salary'].empty:
            col1, col2 = st.columns(2)

            with col1:
                fig = salary_charts.plot_salary_distribution(data['salary'])
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = salary_charts.plot_salary_by_seniority(data['jobs'])
                st.plotly_chart(fig, use_container_width=True)

            # Salary by technology
            st.subheader("Salary by Technology")
            fig = salary_charts.plot_salary_by_technology(data['salary_by_tech'], top_n=15)
            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                fig = salary_charts.plot_salary_trends(data['salary'])
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = salary_charts.plot_salary_by_location_type(data['jobs'])
                st.plotly_chart(fig, use_container_width=True)

            # Summary statistics
            with st.expander("📊 Salary Statistics"):
                summary = salary_charts.create_salary_summary_table(data['salary'])
                if not summary.empty:
                    st.dataframe(summary, use_container_width=True, hide_index=True)
        else:
            st.info("No salary data available. Run the ETL pipeline to populate the database.")

    # Tab 2: Technology Trends
    with tab2:
        st.header("📈 Technology Trends")

        if not data['technology'].empty:
            # Top technologies
            fig = tech_trends.plot_top_technologies(data['technology'], top_n=20)
            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                fig = tech_trends.plot_technology_categories(data['technology'])
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = tech_trends.plot_technology_trends(data['technology'], top_n=10)
                st.plotly_chart(fig, use_container_width=True)

            # Heatmap
            st.subheader("Technology Demand Heatmap")
            fig = tech_trends.plot_skill_demand_heatmap(data['technology'])
            st.plotly_chart(fig, use_container_width=True)

            # Summary table
            with st.expander("📊 Technology Statistics"):
                summary = tech_trends.create_technology_summary_table(data['technology'], top_n=30)
                if not summary.empty:
                    st.dataframe(summary, use_container_width=True)
        else:
            st.info("No technology data available. Run the ETL pipeline to populate the database.")

    # Tab 3: Geographic Distribution
    with tab3:
        st.header("🗺️ Geographic Distribution")

        if not data['location'].empty:
            col1, col2 = st.columns(2)

            with col1:
                fig = geo_charts.plot_jobs_by_city(data['location'], top_n=15)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = geo_charts.plot_location_type_distribution(data['location'])
                st.plotly_chart(fig, use_container_width=True)

            # Regional comparison
            fig = geo_charts.plot_regional_comparison(data['location'])
            st.plotly_chart(fig, use_container_width=True)

            col1, col2 = st.columns(2)

            with col1:
                fig = geo_charts.plot_city_by_location_type(data['location'], top_n=10)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                fig = geo_charts.plot_remote_percentage_trend(data['location'])
                st.plotly_chart(fig, use_container_width=True)

            # Location summary
            with st.expander("📊 Location Statistics"):
                summary = geo_charts.create_location_summary_table(data['location'], top_n=20)
                if not summary.empty:
                    st.dataframe(summary, use_container_width=True)
        else:
            st.info("No location data available. Run the ETL pipeline to populate the database.")

    # Tab 4: Skills Analysis
    with tab4:
        st.header("🔧 Skills Analysis")

        if not data['technology'].empty:
            col1, col2 = st.columns(2)

            with col1:
                fig = tech_trends.plot_technology_by_category(data['technology'], top_per_category=5)
                st.plotly_chart(fig, use_container_width=True)

            with col2:
                if not data['salary_by_tech'].empty:
                    # Top paying technologies
                    st.subheader("💎 Highest Paying Technologies")
                    top_paying = data['salary_by_tech'].nlargest(10, 'avg_salary')
                    for idx, row in top_paying.iterrows():
                        st.metric(
                            label=row['technology'],
                            value=f"{row['avg_salary']:,.0f} PLN",
                            delta=f"{row['job_count']} jobs"
                        )

            # Technology demand by category
            st.subheader("Technology Demand by Category")
            fig = tech_trends.plot_technology_categories(data['technology'])
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No skills data available. Run the ETL pipeline to populate the database.")

    # Tab 5: Overview
    with tab5:
        st.header("📊 Market Overview")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Dataset Summary")
            total_jobs = data['kpis']['total_jobs']
            st.write(f"**Total Active Jobs:** {total_jobs:,}")
            st.write(f"**Jobs with Salary Data:** {len(data['salary'])}")
            st.write(f"**Technologies Tracked:** {data['technology']['technology'].nunique() if not data['technology'].empty else 0}")
            st.write(f"**Cities:** {data['location']['city'].nunique() if not data['location'].empty else 0}")

        with col2:
            st.subheader("Recent Activity")
            st.write(f"**Last Scrape:** {scrape_info['last_update']}")
            st.write(f"**Jobs Found:** {scrape_info['jobs_found']}")
            st.write(f"**New Jobs:** {scrape_info['jobs_new']}")
            st.write(f"**Status:** {scrape_info['status'].upper()}")

        # Recent jobs table
        if not data['jobs'].empty:
            st.subheader("Recent Job Postings")
            recent_jobs = data['jobs'].head(20)[['title', 'company_name', 'city', 'seniority_level', 'salary_avg']].copy()
            if not recent_jobs.empty:
                recent_jobs['salary_avg'] = recent_jobs['salary_avg'].apply(
                    lambda x: f"{x:,.0f} PLN" if pd.notna(x) else "N/A"
                )
                recent_jobs.columns = ['Title', 'Company', 'City', 'Seniority', 'Avg Salary']
                st.dataframe(recent_jobs, use_container_width=True, hide_index=True)

    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: gray; padding: 1rem;">
        <p>NoFluffJobs IT Market Dashboard | Data Engineering Project</p>
        <p>Built with Streamlit & Plotly | Data from NoFluffJobs</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    import pandas as pd  # Import here to avoid issues
    main()
