"""
Populate database with sample data for dashboard testing.
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import random

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


# Sample data templates
COMPANIES = ["TechCorp", "SoftwareInc", "StartupCo", "DataSolutions", "CloudVentures",
             "AI Innovations", "WebDev Studio", "MobileTech", "FinTech Pro", "GameDev Plus"]

TECHNOLOGIES = {
    'language': ['Python', 'JavaScript', 'Java', 'TypeScript', 'C#', 'Go', 'Ruby', 'PHP'],
    'framework': ['React', 'Angular', 'Vue', 'Django', 'Flask', 'Spring', 'Node.js', '.NET'],
    'database': ['PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch'],
    'cloud': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes'],
    'tool': ['Git', 'Jenkins', 'Terraform', 'Ansible']
}

CITIES = ['Warszawa', 'Kraków', 'Wrocław', 'Poznań', 'Gdańsk', 'Katowice', 'Łódź', 'Szczecin']
LOCATION_TYPES = ['remote', 'office', 'hybrid']
SENIORITY_LEVELS = ['junior', 'mid', 'senior']


def generate_sample_jobs(num_jobs: int = 50, num_days: int = 7) -> list:
    """Generate sample job data."""
    jobs = []
    start_date = date.today() - timedelta(days=num_days)

    for i in range(num_jobs):
        # Random snapshot date within range
        days_offset = random.randint(0, num_days)
        snapshot_date = start_date + timedelta(days=days_offset)

        seniority = random.choice(SENIORITY_LEVELS)
        city = random.choice(CITIES)
        location_type = random.choice(LOCATION_TYPES)
        company = random.choice(COMPANIES)

        # Select random technologies (3-6 per job)
        all_techs = []
        for category, tech_list in TECHNOLOGIES.items():
            all_techs.extend(tech_list)

        num_techs = random.randint(3, 6)
        selected_techs = random.sample(all_techs, num_techs)

        # Generate salary based on seniority
        salary_ranges = {
            'junior': (6000, 12000),
            'mid': (12000, 18000),
            'senior': (18000, 28000)
        }

        min_sal, max_sal = salary_ranges[seniority]
        salary_min = random.randint(min_sal, max_sal - 2000)
        salary_max = salary_min + random.randint(2000, 6000)

        # Create job data
        job = {
            'job_id': f'sample-job-{i:03d}',
            'title': f'{seniority.title()} {selected_techs[0]} Developer',
            'company_name': company,
            'url': f'https://nofluffjobs.com/job/sample-{i}',
            'description': f'Exciting opportunity to work with {", ".join(selected_techs[:3])}',
            'requirements': f'Required: {", ".join(selected_techs)}',
            'salary': f'{salary_min} - {salary_max} PLN',
            'location': f'{city} / {"Zdalnie" if location_type == "remote" else ""}',
            'technologies': selected_techs,
            'seniority': seniority,
            'employment_type': 'B2B' if random.random() > 0.5 else 'full-time'
        }

        jobs.append((job, snapshot_date))

    return jobs


def main():
    """Populate database with sample data."""
    print("=" * 60)
    print("Populating Database with Sample Data")
    print("=" * 60)

    # Initialize components
    db = DatabaseManager("data/jobs.db")
    extractor = DataExtractor()
    transformer = DataTransformer()

    # Generate sample jobs
    num_jobs = 100
    num_days = 14

    print(f"\nGenerating {num_jobs} sample jobs over {num_days} days...")
    sample_jobs = generate_sample_jobs(num_jobs, num_days)

    # Process by date
    jobs_by_date = {}
    for job, snapshot_date in sample_jobs:
        if snapshot_date not in jobs_by_date:
            jobs_by_date[snapshot_date] = []
        jobs_by_date[snapshot_date].append(job)

    # Process each date
    total_loaded = 0

    for snapshot_date in sorted(jobs_by_date.keys()):
        jobs = jobs_by_date[snapshot_date]

        print(f"\nProcessing {len(jobs)} jobs for {snapshot_date}...")

        # Extract
        extracted = extractor.extract_batch(jobs)
        print(f"  - Extracted: {len(extracted)} jobs")

        # Transform
        transformed = transformer.transform_batch(extracted)
        print(f"  - Transformed: {len(transformed)} jobs")

        # Load
        loader = DataLoader(db)
        stats = loader.load_all(transformed, snapshot_date=snapshot_date)
        print(f"  - Loaded: {stats['jobs_new']} new, {stats['jobs_updated']} updated")
        print(f"  - Technologies: {stats['technologies_new']} new")

        total_loaded += len(transformed)

    # Verify data
    print("\n" + "=" * 60)
    print("Database Verification")
    print("=" * 60)

    total_jobs = db.fetch_one("SELECT COUNT(*) as count FROM job_postings")
    active_jobs = db.fetch_one("SELECT COUNT(*) as count FROM job_postings WHERE is_active = 1")
    total_techs = db.fetch_one("SELECT COUNT(*) as count FROM technologies")
    total_snapshots = db.fetch_one("SELECT COUNT(*) as count FROM job_snapshots")

    print(f"\nDatabase contents:")
    print(f"  - Total jobs: {total_jobs['count']}")
    print(f"  - Active jobs: {active_jobs['count']}")
    print(f"  - Technologies: {total_techs['count']}")
    print(f"  - Snapshots: {total_snapshots['count']}")

    print("\n✓ Sample data loaded successfully!")
    print("\nYou can now run the dashboard:")
    print("  streamlit run src/dashboard/app.py")

    db.close()


if __name__ == "__main__":
    main()
