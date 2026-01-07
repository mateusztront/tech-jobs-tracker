"""
Data loader for dashboard.
Provides optimized queries for dashboard visualizations.
"""

import pandas as pd
from datetime import date, timedelta
from typing import Optional, List
from ...database.db_manager import DatabaseManager


class DashboardDataLoader:
    """Loads and prepares data for dashboard visualizations."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize data loader.

        Args:
            db: Database manager instance
        """
        self.db = db

    def get_active_jobs(self, date_from: Optional[date] = None, date_to: Optional[date] = None) -> pd.DataFrame:
        """
        Get active jobs with all details.

        Args:
            date_from: Start date filter
            date_to: End date filter

        Returns:
            DataFrame with job data
        """
        query = '''
            SELECT
                jp.job_id,
                jp.title,
                jp.company_name,
                jp.url,
                jp.first_seen_date,
                jp.last_seen_date,
                js.snapshot_date,
                js.location_type,
                js.city,
                js.region,
                js.seniority_level,
                js.employment_type,
                s.salary_min,
                s.salary_max,
                s.salary_avg,
                s.currency,
                s.period,
                s.is_b2b
            FROM job_postings jp
            LEFT JOIN job_snapshots js ON jp.job_id = js.job_id
            LEFT JOIN salaries s ON jp.job_id = s.job_id AND js.snapshot_date = s.snapshot_date
            WHERE jp.is_active = 1
        '''

        if date_from:
            query += f" AND js.snapshot_date >= '{date_from}'"
        if date_to:
            query += f" AND js.snapshot_date <= '{date_to}'"

        query += " ORDER BY jp.first_seen_date DESC"

        rows = self.db.fetch_all(query)
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def get_salary_data(self, date_from: Optional[date] = None, date_to: Optional[date] = None) -> pd.DataFrame:
        """
        Get salary data for analysis.

        Args:
            date_from: Start date filter
            date_to: End date filter

        Returns:
            DataFrame with salary information
        """
        query = '''
            SELECT
                s.snapshot_date,
                s.salary_min,
                s.salary_max,
                s.salary_avg,
                s.currency,
                s.is_b2b,
                jp.title,
                js.seniority_level,
                js.city
            FROM salaries s
            JOIN job_postings jp ON s.job_id = jp.job_id
            JOIN job_snapshots js ON s.job_id = js.job_id AND s.snapshot_date = js.snapshot_date
            WHERE jp.is_active = 1 AND s.currency = 'PLN'
        '''

        if date_from:
            query += f" AND s.snapshot_date >= '{date_from}'"
        if date_to:
            query += f" AND s.snapshot_date <= '{date_to}'"

        rows = self.db.fetch_all(query)
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def get_technology_data(self, date_from: Optional[date] = None, date_to: Optional[date] = None) -> pd.DataFrame:
        """
        Get technology data with job counts.

        Args:
            date_from: Start date filter
            date_to: End date filter

        Returns:
            DataFrame with technology information
        """
        query = '''
            SELECT
                t.name as technology,
                t.category,
                jt.snapshot_date,
                COUNT(DISTINCT jt.job_id) as job_count
            FROM technologies t
            JOIN job_technologies jt ON t.id = jt.technology_id
            JOIN job_postings jp ON jt.job_id = jp.job_id
            WHERE jp.is_active = 1
        '''

        if date_from:
            query += f" AND jt.snapshot_date >= '{date_from}'"
        if date_to:
            query += f" AND jt.snapshot_date <= '{date_to}'"

        query += " GROUP BY t.id, t.name, t.category, jt.snapshot_date"
        query += " ORDER BY job_count DESC"

        rows = self.db.fetch_all(query)
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def get_location_data(self, date_from: Optional[date] = None, date_to: Optional[date] = None) -> pd.DataFrame:
        """
        Get location distribution data.

        Args:
            date_from: Start date filter
            date_to: End date filter

        Returns:
            DataFrame with location information
        """
        query = '''
            SELECT
                js.snapshot_date,
                js.location_type,
                js.city,
                js.region,
                COUNT(DISTINCT jp.job_id) as job_count
            FROM job_snapshots js
            JOIN job_postings jp ON js.job_id = jp.job_id
            WHERE jp.is_active = 1
        '''

        if date_from:
            query += f" AND js.snapshot_date >= '{date_from}'"
        if date_to:
            query += f" AND js.snapshot_date <= '{date_to}'"

        query += " GROUP BY js.snapshot_date, js.location_type, js.city, js.region"

        rows = self.db.fetch_all(query)
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def get_salary_by_technology(self, top_n: int = 20) -> pd.DataFrame:
        """
        Get average salary by technology.

        Args:
            top_n: Number of top technologies to return

        Returns:
            DataFrame with technology and salary data
        """
        query = f'''
            SELECT
                t.name as technology,
                t.category,
                COUNT(DISTINCT jt.job_id) as job_count,
                AVG(s.salary_avg) as avg_salary,
                MIN(s.salary_min) as min_salary,
                MAX(s.salary_max) as max_salary
            FROM technologies t
            JOIN job_technologies jt ON t.id = jt.technology_id
            JOIN salaries s ON jt.job_id = s.job_id AND jt.snapshot_date = s.snapshot_date
            JOIN job_postings jp ON jt.job_id = jp.job_id
            WHERE jp.is_active = 1 AND s.currency = 'PLN'
            GROUP BY t.id, t.name, t.category
            HAVING job_count >= 2
            ORDER BY job_count DESC
            LIMIT {top_n}
        '''

        rows = self.db.fetch_all(query)
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def get_daily_metrics(self, days: int = 90) -> pd.DataFrame:
        """
        Get daily aggregated metrics.

        Args:
            days: Number of days to retrieve

        Returns:
            DataFrame with daily metrics
        """
        date_from = date.today() - timedelta(days=days)

        query = f'''
            SELECT
                metric_date,
                total_jobs,
                remote_jobs,
                office_jobs,
                hybrid_jobs,
                avg_salary_pln,
                median_salary_pln
            FROM daily_metrics
            WHERE metric_date >= '{date_from}'
            ORDER BY metric_date ASC
        '''

        rows = self.db.fetch_all(query)
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def get_kpi_metrics(self) -> dict:
        """
        Get key performance indicators for dashboard.

        Returns:
            Dictionary with KPI values
        """
        # Total active jobs
        total_jobs = self.db.fetch_one(
            "SELECT COUNT(*) as count FROM job_postings WHERE is_active = 1"
        )

        # Average salary
        avg_salary = self.db.fetch_one(
            '''SELECT AVG(salary_avg) as avg_salary
               FROM salaries s
               JOIN job_postings jp ON s.job_id = jp.job_id
               WHERE jp.is_active = 1 AND s.currency = 'PLN'
               AND s.snapshot_date = (SELECT MAX(snapshot_date) FROM salaries)'''
        )

        # Remote percentage
        location_stats = self.db.fetch_one(
            '''SELECT
                SUM(CASE WHEN location_type = 'remote' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as remote_pct
               FROM job_snapshots js
               JOIN job_postings jp ON js.job_id = jp.job_id
               WHERE jp.is_active = 1
               AND js.snapshot_date = (SELECT MAX(snapshot_date) FROM job_snapshots)'''
        )

        # Top technology
        top_tech = self.db.fetch_one(
            '''SELECT t.name, COUNT(*) as count
               FROM technologies t
               JOIN job_technologies jt ON t.id = jt.technology_id
               JOIN job_postings jp ON jt.job_id = jp.job_id
               WHERE jp.is_active = 1
               AND jt.snapshot_date = (SELECT MAX(snapshot_date) FROM job_technologies)
               GROUP BY t.name
               ORDER BY count DESC
               LIMIT 1'''
        )

        return {
            'total_jobs': total_jobs['count'] if total_jobs else 0,
            'avg_salary': avg_salary['avg_salary'] if avg_salary and avg_salary['avg_salary'] else 0,
            'remote_pct': location_stats['remote_pct'] if location_stats and location_stats['remote_pct'] else 0,
            'top_technology': top_tech['name'] if top_tech else 'N/A'
        }

    def get_technology_trends(self, technologies: List[str], days: int = 30) -> pd.DataFrame:
        """
        Get trends for specific technologies over time.

        Args:
            technologies: List of technology names
            days: Number of days to analyze

        Returns:
            DataFrame with technology trends
        """
        date_from = date.today() - timedelta(days=days)

        placeholders = ','.join(['?' for _ in technologies])
        query = f'''
            SELECT
                t.name as technology,
                jt.snapshot_date,
                COUNT(DISTINCT jt.job_id) as job_count
            FROM technologies t
            JOIN job_technologies jt ON t.id = jt.technology_id
            JOIN job_postings jp ON jt.job_id = jp.job_id
            WHERE jp.is_active = 1
            AND t.name IN ({placeholders})
            AND jt.snapshot_date >= ?
            GROUP BY t.name, jt.snapshot_date
            ORDER BY jt.snapshot_date ASC
        '''

        rows = self.db.fetch_all(query, tuple(technologies) + (date_from,))
        return pd.DataFrame(rows) if rows else pd.DataFrame()

    def get_last_scrape_info(self) -> dict:
        """
        Get information about the last scrape run.

        Returns:
            Dictionary with scrape information
        """
        last_run = self.db.fetch_one(
            '''SELECT run_date, jobs_found, jobs_new, status
               FROM scrape_runs
               ORDER BY run_date DESC
               LIMIT 1'''
        )

        if last_run:
            return {
                'last_update': last_run['run_date'],
                'jobs_found': last_run['jobs_found'],
                'jobs_new': last_run['jobs_new'],
                'status': last_run['status']
            }

        return {
            'last_update': 'Never',
            'jobs_found': 0,
            'jobs_new': 0,
            'status': 'unknown'
        }
