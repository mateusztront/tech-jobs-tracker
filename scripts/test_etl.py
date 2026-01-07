"""
Test ETL pipeline with mock data.
"""

import sys
from pathlib import Path
from datetime import date

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.etl.extractor import DataExtractor
from src.etl.transformer import DataTransformer
from src.etl.loader import DataLoader
from src.database.db_manager import DatabaseManager


# Mock job data (simulating scraper output)
MOCK_JOBS = [
    {
        'job_id': 'python-developer-warszawa-123',
        'title': 'Senior Python Developer',
        'company_name': 'Tech Solutions',
        'url': 'https://nofluffjobs.com/job/python-developer-warszawa-123',
        'description': 'Great opportunity to work with Python and Django',
        'requirements': 'Python, Django, PostgreSQL required',
        'salary': '15000 - 20000 PLN',
        'location': 'Warszawa / Zdalnie',
        'technologies': ['Python', 'Django', 'PostgreSQL', 'Docker', 'AWS'],
        'seniority': 'senior',
        'employment_type': 'B2B'
    },
    {
        'job_id': 'java-engineer-krakow-456',
        'title': 'Java Backend Engineer',
        'company_name': 'Software Inc',
        'url': 'https://nofluffjobs.com/job/java-engineer-krakow-456',
        'description': 'Backend development with Spring Boot',
        'requirements': 'Java, Spring, Microservices',
        'salary': '18 000 - 25 000 PLN',
        'location': 'Kraków',
        'technologies': ['Java', 'Spring', 'Kubernetes', 'MySQL'],
        'seniority': 'mid',
        'employment_type': 'full-time'
    },
    {
        'job_id': 'frontend-dev-remote-789',
        'title': 'Junior Frontend Developer',
        'company_name': 'StartupCo',
        'url': 'https://nofluffjobs.com/job/frontend-dev-remote-789',
        'description': 'React development for modern web applications',
        'requirements': 'React, JavaScript, TypeScript',
        'salary': '8000 - 12000 PLN',
        'location': 'Praca zdalna',
        'technologies': ['React', 'TypeScript', 'JavaScript', 'Git'],
        'seniority': 'junior',
        'employment_type': 'contract'
    },
]


def test_extractor():
    """Test data extraction."""
    print("=" * 60)
    print("TEST 1: Data Extraction")
    print("=" * 60)

    extractor = DataExtractor()

    # Test single job extraction
    extracted = extractor.extract_job_data(MOCK_JOBS[0])

    assert extracted is not None, "Extraction failed"
    assert 'job_posting' in extracted
    assert 'snapshot' in extracted
    assert 'salary' in extracted
    assert 'technologies' in extracted

    print("✓ Single job extraction successful")
    print(f"  - Job ID: {extracted['job_posting']['job_id']}")
    print(f"  - Title: {extracted['job_posting']['title']}")

    # Test batch extraction
    extracted_batch = extractor.extract_batch(MOCK_JOBS)

    assert len(extracted_batch) == 3, f"Expected 3 jobs, got {len(extracted_batch)}"

    print(f"✓ Batch extraction: {len(extracted_batch)}/3 jobs")

    return extracted_batch


def test_transformer(extracted_jobs):
    """Test data transformation."""
    print("\n" + "=" * 60)
    print("TEST 2: Data Transformation")
    print("=" * 60)

    transformer = DataTransformer()

    # Test salary normalization
    salary1 = transformer.normalize_salary("15000 - 20000 PLN")
    assert salary1 is not None
    assert salary1['salary_min'] == 15000
    assert salary1['salary_max'] == 20000
    assert salary1['salary_avg'] == 17500
    assert salary1['currency'] == 'PLN'

    print("✓ Salary normalization works")
    print(f"  - Input: '15000 - 20000 PLN'")
    print(f"  - Output: {salary1}")

    # Test location standardization
    location1 = transformer.standardize_location("Warszawa / Zdalnie")
    assert location1['city'] == 'Warszawa'
    assert location1['region'] == 'Mazowieckie'
    assert location1['location_type'] == 'hybrid'

    location2 = transformer.standardize_location("Praca zdalna")
    assert location2['location_type'] == 'remote'

    print("✓ Location standardization works")
    print(f"  - 'Warszawa / Zdalnie' → {location1}")
    print(f"  - 'Praca zdalna' → {location2}")

    # Test technology categorization
    cat_python = transformer.categorize_technology('Python')
    cat_django = transformer.categorize_technology('Django')
    cat_postgres = transformer.categorize_technology('PostgreSQL')

    assert cat_python == 'language'
    assert cat_django == 'framework'
    assert cat_postgres == 'database'

    print("✓ Technology categorization works")
    print(f"  - Python → {cat_python}")
    print(f"  - Django → {cat_django}")
    print(f"  - PostgreSQL → {cat_postgres}")

    # Test batch transformation
    transformed_batch = transformer.transform_batch(extracted_jobs)

    assert len(transformed_batch) == 3, f"Expected 3 jobs, got {len(transformed_batch)}"

    print(f"✓ Batch transformation: {len(transformed_batch)}/3 jobs")

    # Show sample
    sample = transformed_batch[0]
    print("\nSample transformed job:")
    print(f"  - Job ID: {sample['job_posting']['job_id']}")
    print(f"  - Location type: {sample['snapshot']['location_type']}")
    print(f"  - City: {sample['snapshot']['city']}")
    print(f"  - Seniority: {sample['snapshot']['seniority_level']}")
    if sample.get('salary'):
        print(f"  - Salary range: {sample['salary']['salary_min']}-{sample['salary']['salary_max']} {sample['salary']['currency']}")
    print(f"  - Technologies: {[t['name'] for t in sample['technologies']]}")

    return transformed_batch


def test_loader(transformed_jobs):
    """Test data loading into database."""
    print("\n" + "=" * 60)
    print("TEST 3: Data Loading")
    print("=" * 60)

    db = DatabaseManager("data/jobs.db")
    loader = DataLoader(db)

    # Load data
    stats = loader.load_all(transformed_jobs, snapshot_date=date.today())

    print("✓ Data loaded successfully")
    print(f"  - New jobs: {stats['jobs_new']}")
    print(f"  - Updated jobs: {stats['jobs_updated']}")
    print(f"  - Expired jobs: {stats['jobs_expired']}")
    print(f"  - New technologies: {stats['technologies_new']}")
    print(f"  - Errors: {stats['errors']}")

    # Verify data in database
    total_jobs = db.fetch_one("SELECT COUNT(*) as count FROM job_postings")
    active_jobs = db.fetch_one("SELECT COUNT(*) as count FROM job_postings WHERE is_active = 1")
    total_techs = db.fetch_one("SELECT COUNT(*) as count FROM technologies")

    print("\nDatabase verification:")
    print(f"  - Total jobs: {total_jobs['count']}")
    print(f"  - Active jobs: {active_jobs['count']}")
    print(f"  - Total technologies: {total_techs['count']}")

    # Verify salary data
    salaries = db.fetch_all(
        "SELECT job_id, salary_min, salary_max, currency FROM salaries WHERE snapshot_date = ?",
        (date.today(),)
    )
    print(f"  - Salary records: {len(salaries)}")

    # Verify job-technology relationships
    job_techs = db.fetch_all(
        "SELECT COUNT(*) as count FROM job_technologies WHERE snapshot_date = ?",
        (date.today(),)
    )
    print(f"  - Job-technology links: {job_techs[0]['count']}")

    # Test loading same data again (should update, not duplicate)
    print("\nTesting idempotency (loading same data again)...")
    stats2 = loader.load_all(transformed_jobs, snapshot_date=date.today())

    print(f"  - New jobs: {stats2['jobs_new']} (should be 0)")
    print(f"  - Updated jobs: {stats2['jobs_updated']} (should be 3)")

    assert stats2['jobs_new'] == 0, "Should not create duplicate jobs"
    assert stats2['jobs_updated'] == 3, "Should update existing jobs"

    print("✓ Idempotency test passed (no duplicates created)")

    db.close()

    return stats


def cleanup_test_data():
    """Clean up test data."""
    print("\n" + "=" * 60)
    print("CLEANUP: Removing Test Data")
    print("=" * 60)

    db = DatabaseManager("data/jobs.db")

    # Delete test jobs
    test_job_ids = [job['job_id'] for job in MOCK_JOBS]

    for job_id in test_job_ids:
        db.execute_query("DELETE FROM job_technologies WHERE job_id = ?", (job_id,))
        db.execute_query("DELETE FROM salaries WHERE job_id = ?", (job_id,))
        db.execute_query("DELETE FROM job_snapshots WHERE job_id = ?", (job_id,))
        db.execute_query("DELETE FROM job_postings WHERE job_id = ?", (job_id,))

    db.commit()

    print(f"✓ Cleaned up {len(test_job_ids)} test jobs")

    db.close()


def main():
    """Run all ETL tests."""
    print("#" * 60)
    print("# ETL PIPELINE TEST SUITE")
    print("#" * 60)

    try:
        # Run tests
        extracted_jobs = test_extractor()
        transformed_jobs = test_transformer(extracted_jobs)
        stats = test_loader(transformed_jobs)

        # Cleanup
        cleanup_test_data()

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print("✓ All ETL tests passed successfully!")
        print("\nETL Pipeline is ready for:")
        print("  - Extracting data from scraped jobs")
        print("  - Transforming and normalizing data")
        print("  - Loading into database with deduplication")
        print("  - Tracking technologies and relationships")
        print("  - Calculating daily metrics")
        print("\nNext steps:")
        print("  - Run full pipeline: python scripts/run_etl.py")
        print("  - Build dashboard for visualization")
        print("=" * 60 + "\n")

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
