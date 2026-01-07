"""
Database manager for handling SQLite connections and operations.
Provides safe, parameterized query execution and transaction management.
"""

import sqlite3
import logging
from pathlib import Path
from typing import Optional, List, Tuple, Any
from contextlib import contextmanager


class DatabaseManager:
    """Manages SQLite database connections and operations."""

    def __init__(self, db_path: str = "data/jobs.db"):
        """
        Initialize database manager.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection: Optional[sqlite3.Connection] = None
        self._ensure_db_directory()

    def _ensure_db_directory(self):
        """Ensure the database directory exists."""
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        """
        Create and return a database connection.

        Returns:
            SQLite connection object
        """
        if self.connection is None or self._is_connection_closed():
            self.connection = sqlite3.connect(
                self.db_path,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
            )
            # Enable foreign key constraints
            self.connection.execute("PRAGMA foreign_keys = ON")
            # Return rows as dictionaries
            self.connection.row_factory = sqlite3.Row

        return self.connection

    def _is_connection_closed(self) -> bool:
        """Check if the connection is closed."""
        try:
            self.connection.execute("SELECT 1")
            return False
        except (sqlite3.ProgrammingError, AttributeError):
            return True

    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            self.connection = None

    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.

        Usage:
            with db_manager.get_connection() as conn:
                conn.execute(...)
        """
        conn = self.connect()
        try:
            yield conn
        finally:
            pass  # Don't close, connection is reused

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None
    ) -> sqlite3.Cursor:
        """
        Execute a single query with parameters.

        Args:
            query: SQL query string
            params: Query parameters (tuple or dict)

        Returns:
            Cursor object
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor
        except sqlite3.Error as e:
            logging.error(f"Database error: {e}")
            logging.error(f"Query: {query}")
            logging.error(f"Params: {params}")
            raise

    def execute_many(
        self,
        query: str,
        data: List[Tuple]
    ):
        """
        Execute a query with multiple parameter sets.

        Args:
            query: SQL query string
            data: List of parameter tuples
        """
        conn = self.connect()
        cursor = conn.cursor()

        try:
            cursor.executemany(query, data)
            conn.commit()
        except sqlite3.Error as e:
            conn.rollback()
            logging.error(f"Database error: {e}")
            logging.error(f"Query: {query}")
            raise

    def fetch_one(self, query: str, params: Optional[Tuple] = None) -> Optional[dict]:
        """
        Execute a query and fetch one result.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            Result row as dictionary or None
        """
        cursor = self.execute_query(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None

    def fetch_all(self, query: str, params: Optional[Tuple] = None) -> List[dict]:
        """
        Execute a query and fetch all results.

        Args:
            query: SQL query string
            params: Query parameters

        Returns:
            List of result rows as dictionaries
        """
        cursor = self.execute_query(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

    @contextmanager
    def transaction(self):
        """
        Context manager for database transactions.

        Usage:
            with db_manager.transaction():
                db_manager.execute_query(...)
                db_manager.execute_query(...)
        """
        conn = self.connect()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logging.error(f"Transaction failed, rolling back: {e}")
            raise

    def commit(self):
        """Commit current transaction."""
        if self.connection:
            self.connection.commit()

    def rollback(self):
        """Rollback current transaction."""
        if self.connection:
            self.connection.rollback()

    def record_scrape_run(
        self,
        jobs_found: int = 0,
        jobs_new: int = 0,
        jobs_updated: int = 0,
        jobs_expired: int = 0,
        status: str = 'success',
        error_message: Optional[str] = None,
        duration_seconds: Optional[float] = None
    ):
        """
        Record a scraper run in the database.

        Args:
            jobs_found: Total jobs found in this run
            jobs_new: New jobs added
            jobs_updated: Existing jobs updated
            jobs_expired: Jobs marked as expired
            status: Run status ('success', 'partial', 'failed')
            error_message: Error message if failed
            duration_seconds: Runtime in seconds
        """
        query = '''
            INSERT INTO scrape_runs (
                run_date, jobs_found, jobs_new, jobs_updated,
                jobs_expired, status, error_message, duration_seconds
            ) VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)
        '''

        self.execute_query(
            query,
            (jobs_found, jobs_new, jobs_updated, jobs_expired,
             status, error_message, duration_seconds)
        )
        self.commit()

    def get_last_scrape_time(self) -> Optional[str]:
        """
        Get the timestamp of the last successful scrape.

        Returns:
            ISO timestamp string or None
        """
        query = '''
            SELECT run_date
            FROM scrape_runs
            WHERE status = 'success'
            ORDER BY run_date DESC
            LIMIT 1
        '''

        result = self.fetch_one(query)
        return result['run_date'] if result else None

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.commit()
        else:
            self.rollback()
        self.close()
