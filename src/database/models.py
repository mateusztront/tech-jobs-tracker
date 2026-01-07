"""
Database schema definitions for IT job market dashboard.
Defines SQLite tables for job postings, salaries, technologies, and metrics.
"""

# SQL schema definitions
SCHEMA = {
    'job_postings': '''
        CREATE TABLE IF NOT EXISTS job_postings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            company_name TEXT NOT NULL,
            url TEXT NOT NULL,
            first_seen_date DATE NOT NULL,
            last_seen_date DATE NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',

    'job_snapshots': '''
        CREATE TABLE IF NOT EXISTS job_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            snapshot_date DATE NOT NULL,
            description TEXT,
            requirements TEXT,
            location_type TEXT,
            city TEXT,
            region TEXT,
            country TEXT DEFAULT 'Poland',
            seniority_level TEXT,
            employment_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES job_postings(job_id),
            UNIQUE(job_id, snapshot_date)
        )
    ''',

    'salaries': '''
        CREATE TABLE IF NOT EXISTS salaries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            snapshot_date DATE NOT NULL,
            currency TEXT DEFAULT 'PLN',
            salary_min REAL,
            salary_max REAL,
            salary_avg REAL,
            period TEXT DEFAULT 'monthly',
            is_b2b BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES job_postings(job_id)
        )
    ''',

    'technologies': '''
        CREATE TABLE IF NOT EXISTS technologies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',

    'job_technologies': '''
        CREATE TABLE IF NOT EXISTS job_technologies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id TEXT NOT NULL,
            technology_id INTEGER NOT NULL,
            proficiency_level TEXT,
            snapshot_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES job_postings(job_id),
            FOREIGN KEY (technology_id) REFERENCES technologies(id),
            UNIQUE(job_id, technology_id, snapshot_date)
        )
    ''',

    'daily_metrics': '''
        CREATE TABLE IF NOT EXISTS daily_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            metric_date DATE UNIQUE NOT NULL,
            total_jobs INTEGER,
            remote_jobs INTEGER,
            office_jobs INTEGER,
            hybrid_jobs INTEGER,
            avg_salary_pln REAL,
            median_salary_pln REAL,
            jobs_scraped INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''',

    'scrape_runs': '''
        CREATE TABLE IF NOT EXISTS scrape_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_date TIMESTAMP NOT NULL,
            jobs_found INTEGER,
            jobs_new INTEGER,
            jobs_updated INTEGER,
            jobs_expired INTEGER,
            status TEXT,
            error_message TEXT,
            duration_seconds REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    '''
}

# Index definitions for performance optimization
INDEXES = [
    'CREATE INDEX IF NOT EXISTS idx_job_postings_active ON job_postings(is_active)',
    'CREATE INDEX IF NOT EXISTS idx_job_postings_job_id ON job_postings(job_id)',
    'CREATE INDEX IF NOT EXISTS idx_job_snapshots_date ON job_snapshots(snapshot_date)',
    'CREATE INDEX IF NOT EXISTS idx_job_snapshots_job_id ON job_snapshots(job_id)',
    'CREATE INDEX IF NOT EXISTS idx_salaries_date ON salaries(snapshot_date)',
    'CREATE INDEX IF NOT EXISTS idx_salaries_job_id ON salaries(job_id)',
    'CREATE INDEX IF NOT EXISTS idx_job_technologies_date ON job_technologies(snapshot_date)',
    'CREATE INDEX IF NOT EXISTS idx_job_technologies_job_id ON job_technologies(job_id)',
    'CREATE INDEX IF NOT EXISTS idx_daily_metrics_date ON daily_metrics(metric_date)',
    'CREATE INDEX IF NOT EXISTS idx_technologies_name ON technologies(name)',
]


def create_all_tables(connection):
    """
    Create all database tables and indexes.

    Args:
        connection: SQLite database connection
    """
    cursor = connection.cursor()

    # Create tables
    for table_name, create_sql in SCHEMA.items():
        cursor.execute(create_sql)
        print(f"Created table: {table_name}")

    # Create indexes
    for index_sql in INDEXES:
        cursor.execute(index_sql)

    print(f"Created {len(INDEXES)} indexes")

    connection.commit()


def drop_all_tables(connection):
    """
    Drop all database tables (useful for testing/reset).

    Args:
        connection: SQLite database connection
    """
    cursor = connection.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    # Drop each table
    for table in tables:
        table_name = table[0]
        if table_name != 'sqlite_sequence':  # Skip system table
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            print(f"Dropped table: {table_name}")

    connection.commit()
