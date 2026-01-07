"""
Test script to validate database functionality.
Tests all CRUD operations and database manager methods.
"""

import sys
from pathlib import Path
from datetime import date, datetime

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager

# Fix encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_connection():
    """Test database connection."""
    print("\n" + "=" * 60)
    print("TEST 1: Database Connection")
    print("=" * 60)

    db = DatabaseManager("data/jobs.db")
    conn = db.connect()

    # Test simple query
    cursor = conn.execute("SELECT 1 as test")
    result = cursor.fetchone()

    assert result['test'] == 1, "Connection test failed"
    print("✓ Database connection successful")
    print(f"✓ Database path: {db.db_path}")

    return db


def test_insert_sample_job(db):
    """Test inserting a sample job posting."""
    print("\n" + "=" * 60)
    print("TEST 2: Insert Sample Job Posting")
    print("=" * 60)

    # Insert job posting
    job_data = {
        'job_id': 'test-job-001',
        'title': 'Senior Python Developer',
        'company_name': 'Tech Company',
        'url': 'https://nofluffjobs.com/job/test-001',
        'first_seen_date': date.today(),
        'last_seen_date': date.today(),
        'is_active': 1
    }

    query = '''
        INSERT INTO job_postings
        (job_id, title, company_name, url, first_seen_date, last_seen_date, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''

    db.execute_query(query, tuple(job_data.values()))
    db.commit()

    # Verify insertion
    result = db.fetch_one("SELECT * FROM job_postings WHERE job_id = ?", ('test-job-001',))

    assert result is not None, "Job insertion failed"
    assert result['title'] == 'Senior Python Developer', "Job title mismatch"
    assert result['company_name'] == 'Tech Company', "Company name mismatch"

    print("✓ Job posting inserted successfully")
    print(f"  - Job ID: {result['job_id']}")
    print(f"  - Title: {result['title']}")
    print(f"  - Company: {result['company_name']}")
    print(f"  - Active: {bool(result['is_active'])}")


def test_insert_technologies(db):
    """Test inserting technologies."""
    print("\n" + "=" * 60)
    print("TEST 3: Insert Technologies")
    print("=" * 60)

    technologies = [
        ('Python', 'language'),
        ('Django', 'framework'),
        ('PostgreSQL', 'database'),
        ('Docker', 'tool'),
        ('AWS', 'cloud')
    ]

    query = "INSERT INTO technologies (name, category) VALUES (?, ?)"
    db.execute_many(query, technologies)

    # Verify insertion
    results = db.fetch_all("SELECT * FROM technologies ORDER BY name")

    assert len(results) == 5, f"Expected 5 technologies, got {len(results)}"

    print(f"✓ Inserted {len(results)} technologies:")
    for tech in results:
        print(f"  - {tech['name']} ({tech['category']})")


def test_insert_job_snapshot(db):
    """Test inserting job snapshot with salary."""
    print("\n" + "=" * 60)
    print("TEST 4: Insert Job Snapshot and Salary")
    print("=" * 60)

    # Insert job snapshot
    snapshot_query = '''
        INSERT INTO job_snapshots
        (job_id, snapshot_date, description, location_type, city, region, seniority_level)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    '''

    db.execute_query(
        snapshot_query,
        ('test-job-001', date.today(), 'Great Python opportunity',
         'hybrid', 'Warszawa', 'Mazowieckie', 'senior')
    )

    # Insert salary
    salary_query = '''
        INSERT INTO salaries
        (job_id, snapshot_date, salary_min, salary_max, salary_avg, currency, period, is_b2b)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    '''

    db.execute_query(
        salary_query,
        ('test-job-001', date.today(), 15000, 20000, 17500, 'PLN', 'monthly', 1)
    )

    db.commit()

    # Verify
    snapshot = db.fetch_one(
        "SELECT * FROM job_snapshots WHERE job_id = ?",
        ('test-job-001',)
    )

    salary = db.fetch_one(
        "SELECT * FROM salaries WHERE job_id = ?",
        ('test-job-001',)
    )

    assert snapshot is not None, "Snapshot insertion failed"
    assert salary is not None, "Salary insertion failed"

    print("✓ Job snapshot inserted successfully")
    print(f"  - Location: {snapshot['city']} ({snapshot['location_type']})")
    print(f"  - Seniority: {snapshot['seniority_level']}")

    print("✓ Salary data inserted successfully")
    print(f"  - Range: {salary['salary_min']:,} - {salary['salary_max']:,} {salary['currency']}")
    print(f"  - Average: {salary['salary_avg']:,} {salary['currency']}")
    print(f"  - Type: {'B2B' if salary['is_b2b'] else 'Employment'}")


def test_job_technologies_relationship(db):
    """Test many-to-many relationship between jobs and technologies."""
    print("\n" + "=" * 60)
    print("TEST 5: Job-Technologies Relationship")
    print("=" * 60)

    # Get technology IDs
    python_id = db.fetch_one("SELECT id FROM technologies WHERE name = ?", ('Python',))['id']
    django_id = db.fetch_one("SELECT id FROM technologies WHERE name = ?", ('Django',))['id']
    postgres_id = db.fetch_one("SELECT id FROM technologies WHERE name = ?", ('PostgreSQL',))['id']

    # Link technologies to job
    job_tech_data = [
        ('test-job-001', python_id, 'required', date.today()),
        ('test-job-001', django_id, 'required', date.today()),
        ('test-job-001', postgres_id, 'nice-to-have', date.today())
    ]

    query = '''
        INSERT INTO job_technologies
        (job_id, technology_id, proficiency_level, snapshot_date)
        VALUES (?, ?, ?, ?)
    '''

    db.execute_many(query, job_tech_data)

    # Verify with JOIN query
    verify_query = '''
        SELECT t.name, t.category, jt.proficiency_level
        FROM job_technologies jt
        JOIN technologies t ON jt.technology_id = t.id
        WHERE jt.job_id = ?
        ORDER BY t.name
    '''

    results = db.fetch_all(verify_query, ('test-job-001',))

    assert len(results) == 3, f"Expected 3 technologies, got {len(results)}"

    print(f"✓ Linked {len(results)} technologies to job:")
    for tech in results:
        print(f"  - {tech['name']} ({tech['proficiency_level']})")


def test_scrape_run_logging(db):
    """Test scrape run logging."""
    print("\n" + "=" * 60)
    print("TEST 6: Scrape Run Logging")
    print("=" * 60)

    # Record a successful scrape run
    db.record_scrape_run(
        jobs_found=100,
        jobs_new=25,
        jobs_updated=10,
        jobs_expired=5,
        status='success',
        duration_seconds=45.5
    )

    # Verify
    result = db.fetch_one(
        "SELECT * FROM scrape_runs ORDER BY run_date DESC LIMIT 1"
    )

    assert result is not None, "Scrape run logging failed"
    assert result['status'] == 'success', "Status mismatch"
    assert result['jobs_found'] == 100, "Jobs found mismatch"

    print("✓ Scrape run logged successfully")
    print(f"  - Status: {result['status']}")
    print(f"  - Jobs found: {result['jobs_found']}")
    print(f"  - New: {result['jobs_new']}")
    print(f"  - Updated: {result['jobs_updated']}")
    print(f"  - Expired: {result['jobs_expired']}")
    print(f"  - Duration: {result['duration_seconds']}s")


def test_last_scrape_time(db):
    """Test getting last scrape time."""
    print("\n" + "=" * 60)
    print("TEST 7: Get Last Scrape Time")
    print("=" * 60)

    last_scrape = db.get_last_scrape_time()

    assert last_scrape is not None, "Last scrape time not found"

    print(f"✓ Last scrape time: {last_scrape}")


def test_transaction_rollback(db):
    """Test transaction rollback on error."""
    print("\n" + "=" * 60)
    print("TEST 8: Transaction Rollback")
    print("=" * 60)

    try:
        with db.transaction():
            # Insert a job
            db.execute_query(
                "INSERT INTO job_postings (job_id, title, company_name, url, first_seen_date, last_seen_date) VALUES (?, ?, ?, ?, ?, ?)",
                ('rollback-test', 'Test Job', 'Test Co', 'http://test.com', date.today(), date.today())
            )

            # Cause an error (duplicate job_id)
            db.execute_query(
                "INSERT INTO job_postings (job_id, title, company_name, url, first_seen_date, last_seen_date) VALUES (?, ?, ?, ?, ?, ?)",
                ('rollback-test', 'Test Job', 'Test Co', 'http://test.com', date.today(), date.today())
            )
    except:
        pass

    # Verify rollback - job should not exist
    result = db.fetch_one("SELECT * FROM job_postings WHERE job_id = ?", ('rollback-test',))

    assert result is None, "Transaction rollback failed"

    print("✓ Transaction rollback works correctly")
    print("  - Duplicate insert was rolled back")


def test_aggregate_query(db):
    """Test aggregate query for dashboard."""
    print("\n" + "=" * 60)
    print("TEST 9: Aggregate Query (Dashboard Preview)")
    print("=" * 60)

    # Complex query simulating dashboard data
    query = '''
        SELECT
            COUNT(DISTINCT jp.job_id) as total_jobs,
            AVG(s.salary_avg) as avg_salary,
            COUNT(CASE WHEN js.location_type = 'remote' THEN 1 END) as remote_jobs,
            COUNT(CASE WHEN js.location_type = 'office' THEN 1 END) as office_jobs,
            COUNT(CASE WHEN js.location_type = 'hybrid' THEN 1 END) as hybrid_jobs
        FROM job_postings jp
        LEFT JOIN job_snapshots js ON jp.job_id = js.job_id
        LEFT JOIN salaries s ON jp.job_id = s.job_id
        WHERE jp.is_active = 1
    '''

    result = db.fetch_one(query)

    assert result is not None, "Aggregate query failed"

    print("✓ Aggregate query executed successfully")
    print("\nDashboard Metrics Preview:")
    print(f"  - Total active jobs: {result['total_jobs']}")
    print(f"  - Average salary: {result['avg_salary']:,.0f} PLN" if result['avg_salary'] else "  - Average salary: N/A")
    print(f"  - Remote jobs: {result['remote_jobs']}")
    print(f"  - Office jobs: {result['office_jobs']}")
    print(f"  - Hybrid jobs: {result['hybrid_jobs']}")


def test_technology_popularity(db):
    """Test technology popularity query."""
    print("\n" + "=" * 60)
    print("TEST 10: Technology Popularity Query")
    print("=" * 60)

    query = '''
        SELECT
            t.name,
            t.category,
            COUNT(jt.job_id) as job_count,
            SUM(CASE WHEN jt.proficiency_level = 'required' THEN 1 ELSE 0 END) as required_count
        FROM technologies t
        LEFT JOIN job_technologies jt ON t.id = jt.technology_id
        GROUP BY t.id, t.name, t.category
        ORDER BY job_count DESC
    '''

    results = db.fetch_all(query)

    assert len(results) > 0, "Technology query failed"

    print(f"✓ Found {len(results)} technologies")
    print("\nTechnology Popularity:")
    for tech in results:
        print(f"  - {tech['name']:15} {tech['job_count']} jobs ({tech['required_count']} required)")


def cleanup_test_data(db):
    """Clean up test data."""
    print("\n" + "=" * 60)
    print("CLEANUP: Removing Test Data")
    print("=" * 60)

    # Delete in correct order due to foreign keys
    db.execute_query("DELETE FROM job_technologies WHERE job_id = ?", ('test-job-001',))
    db.execute_query("DELETE FROM salaries WHERE job_id = ?", ('test-job-001',))
    db.execute_query("DELETE FROM job_snapshots WHERE job_id = ?", ('test-job-001',))
    db.execute_query("DELETE FROM job_postings WHERE job_id = ?", ('test-job-001',))
    db.execute_query("DELETE FROM technologies")
    db.commit()

    print("✓ Test data cleaned up successfully")


def main():
    """Run all tests."""
    print("\n" + "#" * 60)
    print("# DATABASE FUNCTIONALITY TEST SUITE")
    print("#" * 60)

    try:
        # Run tests
        db = test_connection()
        test_insert_sample_job(db)
        test_insert_technologies(db)
        test_insert_job_snapshot(db)
        test_job_technologies_relationship(db)
        test_scrape_run_logging(db)
        test_last_scrape_time(db)
        test_transaction_rollback(db)
        test_aggregate_query(db)
        test_technology_popularity(db)

        # Cleanup
        cleanup_test_data(db)

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✓ All 10 tests passed successfully!")
        print("\nDatabase is fully functional and ready for:")
        print("  - Web scraper integration")
        print("  - ETL pipeline")
        print("  - Dashboard visualization")
        print("=" * 60 + "\n")

        db.close()
        return 0

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
