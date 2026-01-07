"""
Database initialization script.
Creates all tables and indexes for the job market dashboard.
"""

import sys
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager
from src.database.models import create_all_tables, drop_all_tables


def main():
    """Initialize the database with all tables and indexes."""
    print("=" * 60)
    print("IT Job Market Dashboard - Database Initialization")
    print("=" * 60)

    # Ask for confirmation if database exists
    db_path = project_root / "data" / "jobs.db"

    if db_path.exists():
        print(f"\nWarning: Database already exists at {db_path}")
        response = input("Do you want to recreate it? This will DELETE all data! (yes/no): ")

        if response.lower() != 'yes':
            print("Initialization cancelled.")
            return

        print("\nDropping existing tables...")
        db = DatabaseManager(str(db_path))
        with db.get_connection() as conn:
            drop_all_tables(conn)

    # Create database and tables
    print(f"\nCreating database at: {db_path}")
    db = DatabaseManager(str(db_path))

    with db.get_connection() as conn:
        create_all_tables(conn)

    print("\n" + "=" * 60)
    print("Database initialization completed successfully!")
    print("=" * 60)
    print(f"\nDatabase location: {db_path}")
    print("\nTables created:")
    print("  - job_postings")
    print("  - job_snapshots")
    print("  - salaries")
    print("  - technologies")
    print("  - job_technologies")
    print("  - daily_metrics")
    print("  - scrape_runs")
    print("\nYou can now run the scraper to populate the database.")


if __name__ == "__main__":
    main()
