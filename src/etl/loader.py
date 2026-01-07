"""
Data loader for ETL pipeline.
Loads transformed data into the database.
"""

import logging
from typing import Dict, List, Optional, Set
from datetime import date

from ..database.db_manager import DatabaseManager


class DataLoader:
    """Loads transformed job data into the database."""

    def __init__(self, db: DatabaseManager):
        """
        Initialize data loader.

        Args:
            db: Database manager instance
        """
        self.db = db
        self.stats = {
            'jobs_new': 0,
            'jobs_updated': 0,
            'jobs_expired': 0,
            'technologies_new': 0,
            'errors': 0
        }

    def load_all(self, transformed_data_list: List[Dict], snapshot_date: date = None) -> Dict:
        """
        Load all transformed job data into database.

        Args:
            transformed_data_list: List of transformed job data
            snapshot_date: Date for this snapshot (defaults to today)

        Returns:
            Statistics dictionary
        """
        if snapshot_date is None:
            snapshot_date = date.today()

        # Reset stats for this load
        self.stats = {
            'jobs_new': 0,
            'jobs_updated': 0,
            'jobs_expired': 0,
            'technologies_new': 0,
            'errors': 0
        }

        logging.info(f"Loading {len(transformed_data_list)} jobs into database")

        # Track which jobs we've seen in this run
        active_job_ids = set()

        with self.db.transaction():
            for job_data in transformed_data_list:
                try:
                    self._load_job(job_data, snapshot_date)
                    active_job_ids.add(job_data['job_posting']['job_id'])
                except Exception as e:
                    self.stats['errors'] += 1
                    logging.error(f"Error loading job {job_data['job_posting'].get('job_id')}: {e}")

            # Mark jobs not seen in this run as inactive
            if active_job_ids:
                expired_count = self._mark_expired_jobs(active_job_ids)
                self.stats['jobs_expired'] = expired_count

            # Update daily metrics
            self._update_daily_metrics(snapshot_date)

        logging.info(f"Load complete: {self.stats}")

        return self.stats

    def _load_job(self, job_data: Dict, snapshot_date: date):
        """
        Load a single job into the database.

        Args:
            job_data: Transformed job data
            snapshot_date: Date for this snapshot
        """
        job_posting = job_data['job_posting']
        job_id = job_posting['job_id']

        # Check if job already exists
        existing = self.db.fetch_one(
            "SELECT * FROM job_postings WHERE job_id = ?",
            (job_id,)
        )

        if existing:
            # Update existing job
            self._update_job_posting(job_posting)
            self.stats['jobs_updated'] += 1
        else:
            # Insert new job
            self._insert_job_posting(job_posting)
            self.stats['jobs_new'] += 1

        # Insert snapshot
        self._insert_job_snapshot(job_id, job_data['snapshot'], snapshot_date)

        # Insert salary if available
        if job_data.get('salary'):
            self._insert_salary(job_id, job_data['salary'], snapshot_date)

        # Insert technologies
        if job_data.get('technologies'):
            self._insert_technologies(job_id, job_data['technologies'], snapshot_date)

    def _insert_job_posting(self, job_posting: Dict):
        """Insert new job posting."""
        query = '''
            INSERT INTO job_postings
            (job_id, title, company_name, url, first_seen_date, last_seen_date, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        '''

        self.db.execute_query(
            query,
            (
                job_posting['job_id'],
                job_posting['title'],
                job_posting['company_name'],
                job_posting['url'],
                job_posting['first_seen_date'],
                job_posting['last_seen_date'],
                1  # is_active
            )
        )

    def _update_job_posting(self, job_posting: Dict):
        """Update existing job posting."""
        query = '''
            UPDATE job_postings
            SET last_seen_date = ?,
                is_active = 1,
                updated_at = CURRENT_TIMESTAMP
            WHERE job_id = ?
        '''

        self.db.execute_query(
            query,
            (job_posting['last_seen_date'], job_posting['job_id'])
        )

    def _insert_job_snapshot(self, job_id: str, snapshot: Dict, snapshot_date: date):
        """Insert job snapshot for historical tracking."""
        query = '''
            INSERT OR REPLACE INTO job_snapshots
            (job_id, snapshot_date, description, requirements, location_type,
             city, region, country, seniority_level, employment_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        self.db.execute_query(
            query,
            (
                job_id,
                snapshot_date,
                snapshot.get('description'),
                snapshot.get('requirements'),
                snapshot.get('location_type'),
                snapshot.get('city'),
                snapshot.get('region'),
                snapshot.get('country', 'Poland'),
                snapshot.get('seniority_level'),
                snapshot.get('employment_type')
            )
        )

    def _insert_salary(self, job_id: str, salary: Dict, snapshot_date: date):
        """Insert salary information."""
        query = '''
            INSERT OR REPLACE INTO salaries
            (job_id, snapshot_date, currency, salary_min, salary_max,
             salary_avg, period, is_b2b)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''

        self.db.execute_query(
            query,
            (
                job_id,
                snapshot_date,
                salary.get('currency', 'PLN'),
                salary.get('salary_min'),
                salary.get('salary_max'),
                salary.get('salary_avg'),
                salary.get('period', 'monthly'),
                1 if salary.get('is_b2b') else 0
            )
        )

    def _insert_technologies(self, job_id: str, technologies: List[Dict], snapshot_date: date):
        """
        Insert job technologies with many-to-many relationship.

        Args:
            job_id: Job ID
            technologies: List of technology dictionaries
            snapshot_date: Snapshot date
        """
        for tech in technologies:
            tech_name = tech['name']
            tech_category = tech['category']

            # Get or create technology
            tech_id = self._get_or_create_technology(tech_name, tech_category)

            # Link to job
            self._link_job_technology(job_id, tech_id, snapshot_date)

    def _get_or_create_technology(self, tech_name: str, category: str) -> int:
        """
        Get existing technology ID or create new one.

        Args:
            tech_name: Technology name
            category: Technology category

        Returns:
            Technology ID
        """
        # Check if exists
        existing = self.db.fetch_one(
            "SELECT id FROM technologies WHERE name = ?",
            (tech_name,)
        )

        if existing:
            return existing['id']

        # Create new
        self.db.execute_query(
            "INSERT INTO technologies (name, category) VALUES (?, ?)",
            (tech_name, category)
        )

        self.stats['technologies_new'] += 1

        # Get the ID
        result = self.db.fetch_one(
            "SELECT id FROM technologies WHERE name = ?",
            (tech_name,)
        )

        return result['id']

    def _link_job_technology(self, job_id: str, tech_id: int, snapshot_date: date):
        """Link a technology to a job."""
        query = '''
            INSERT OR IGNORE INTO job_technologies
            (job_id, technology_id, snapshot_date)
            VALUES (?, ?, ?)
        '''

        self.db.execute_query(query, (job_id, tech_id, snapshot_date))

    def _mark_expired_jobs(self, active_job_ids: Set[str]) -> int:
        """
        Mark jobs not seen in current scrape as inactive.

        Args:
            active_job_ids: Set of job IDs seen in current scrape

        Returns:
            Number of jobs marked as expired
        """
        # Get all currently active job IDs
        all_active = self.db.fetch_all(
            "SELECT job_id FROM job_postings WHERE is_active = 1"
        )

        expired_count = 0

        for row in all_active:
            job_id = row['job_id']
            if job_id not in active_job_ids:
                # Mark as inactive
                self.db.execute_query(
                    "UPDATE job_postings SET is_active = 0 WHERE job_id = ?",
                    (job_id,)
                )
                expired_count += 1

        if expired_count > 0:
            logging.info(f"Marked {expired_count} jobs as inactive")

        return expired_count

    def _update_daily_metrics(self, metric_date: date):
        """
        Calculate and store daily aggregated metrics.

        Args:
            metric_date: Date for metrics
        """
        # Calculate metrics from current data
        metrics_query = '''
            SELECT
                COUNT(DISTINCT jp.job_id) as total_jobs,
                SUM(CASE WHEN js.location_type = 'remote' THEN 1 ELSE 0 END) as remote_jobs,
                SUM(CASE WHEN js.location_type = 'office' THEN 1 ELSE 0 END) as office_jobs,
                SUM(CASE WHEN js.location_type = 'hybrid' THEN 1 ELSE 0 END) as hybrid_jobs,
                AVG(s.salary_avg) as avg_salary,
                COUNT(DISTINCT s.job_id) as jobs_with_salary
            FROM job_postings jp
            LEFT JOIN job_snapshots js ON jp.job_id = js.job_id AND js.snapshot_date = ?
            LEFT JOIN salaries s ON jp.job_id = s.job_id AND s.snapshot_date = ?
            WHERE jp.is_active = 1
        '''

        metrics = self.db.fetch_one(metrics_query, (metric_date, metric_date))

        if not metrics:
            logging.warning("Could not calculate metrics")
            return

        # Calculate median salary (requires separate query)
        median_query = '''
            SELECT salary_avg
            FROM salaries
            WHERE snapshot_date = ?
            ORDER BY salary_avg
            LIMIT 1 OFFSET (
                SELECT COUNT(*) / 2
                FROM salaries
                WHERE snapshot_date = ?
            )
        '''

        median_result = self.db.fetch_one(median_query, (metric_date, metric_date))
        median_salary = median_result['salary_avg'] if median_result else None

        # Insert or update metrics
        insert_query = '''
            INSERT OR REPLACE INTO daily_metrics
            (metric_date, total_jobs, remote_jobs, office_jobs, hybrid_jobs,
             avg_salary_pln, median_salary_pln, jobs_scraped)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        '''

        self.db.execute_query(
            insert_query,
            (
                metric_date,
                metrics['total_jobs'],
                metrics['remote_jobs'],
                metrics['office_jobs'],
                metrics['hybrid_jobs'],
                metrics['avg_salary'],
                median_salary,
                metrics['total_jobs']
            )
        )

        logging.info(f"Updated daily metrics for {metric_date}")

    def get_statistics(self) -> Dict:
        """
        Get loading statistics.

        Returns:
            Statistics dictionary
        """
        return self.stats.copy()
