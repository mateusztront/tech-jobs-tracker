"""
Complete ETL pipeline script.
Scrapes jobs, transforms data, and loads into database.
"""

import sys
import os
import time
import logging
import yaml
import json
from pathlib import Path
from datetime import datetime, date

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraper.nofluff_scraper import NoFluffScraper
from src.etl.extractor import DataExtractor
from src.etl.transformer import DataTransformer
from src.etl.loader import DataLoader
from src.database.db_manager import DatabaseManager


def setup_logging():
    """Configure logging."""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f'etl_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )

    return log_file


def load_config():
    """Load configuration files."""
    config_path = project_root / 'config' / 'config.yaml'
    scraper_config_path = project_root / 'config' / 'scraper_config.yaml'

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    with open(scraper_config_path, 'r', encoding='utf-8') as f:
        scraper_config = yaml.safe_load(f)

    config.update(scraper_config)

    return config


def main():
    """Main ETL pipeline execution."""
    print("=" * 60)
    print("NoFluffJobs ETL Pipeline")
    print("=" * 60)

    # Setup
    log_file = setup_logging()
    logging.info("Starting ETL pipeline")
    print(f"\nLog file: {log_file}")

    # Load configuration
    try:
        config = load_config()
        logging.info("Configuration loaded successfully")
    except Exception as e:
        logging.error(f"Failed to load configuration: {e}")
        return 1

    # Check database
    db_path = project_root / config['database']['path']
    if not db_path.exists():
        logging.error(f"Database not found at {db_path}")
        logging.error("Please run: python scripts/init_database.py")
        return 1

    # Initialize components
    db = DatabaseManager(str(db_path))
    extractor = DataExtractor()
    transformer = DataTransformer()
    loader = DataLoader(db)

    # Display configuration
    print("\nETL Configuration:")
    print(f"  - Database: {db_path}")
    print(f"  - Max jobs to scrape: {config['scraping'].get('max_jobs_per_run', 1000)}")
    print(f"  - Max pages: {config['scraping']['max_pages']}")

    start_time = time.time()

    try:
        # STEP 1: SCRAPE
        print("\n" + "=" * 60)
        print("STEP 1: SCRAPING")
        print("=" * 60)

        with NoFluffScraper(config) as scraper:
            raw_jobs = scraper.scrape_all()

        if not raw_jobs:
            logging.warning("No jobs scraped. Pipeline stopped.")
            print("\n⚠️  No jobs were scraped. Check the logs for details.")
            return 1

        print(f"✓ Scraped {len(raw_jobs)} jobs")

        # Save raw data for inspection
        raw_data_file = project_root / 'logs' / f'raw_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(raw_data_file, 'w', encoding='utf-8') as f:
            json.dump(raw_jobs, f, indent=2, ensure_ascii=False)
        print(f"  - Raw data saved to: {raw_data_file}")

        # STEP 2: EXTRACT
        print("\n" + "=" * 60)
        print("STEP 2: EXTRACTION")
        print("=" * 60)

        extracted_jobs = extractor.extract_batch(raw_jobs)
        print(f"✓ Extracted {len(extracted_jobs)}/{len(raw_jobs)} valid jobs")

        if not extracted_jobs:
            logging.error("No valid jobs after extraction")
            return 1

        # STEP 3: TRANSFORM
        print("\n" + "=" * 60)
        print("STEP 3: TRANSFORMATION")
        print("=" * 60)

        transformed_jobs = transformer.transform_batch(extracted_jobs)
        print(f"✓ Transformed {len(transformed_jobs)}/{len(extracted_jobs)} jobs")

        # Show sample transformed data
        if transformed_jobs:
            sample = transformed_jobs[0]
            print("\nSample transformed job:")
            print(f"  - Title: {sample['job_posting']['title']}")
            print(f"  - Company: {sample['job_posting']['company_name']}")
            if sample.get('salary'):
                sal = sample['salary']
                print(f"  - Salary: {sal['salary_min']}-{sal['salary_max']} {sal['currency']} ({sal['period']})")
            snap = sample['snapshot']
            print(f"  - Location: {snap.get('city', 'N/A')} ({snap.get('location_type', 'N/A')})")
            print(f"  - Seniority: {snap.get('seniority_level', 'N/A')}")
            print(f"  - Technologies: {len(sample.get('technologies', []))}")

        # STEP 4: LOAD
        print("\n" + "=" * 60)
        print("STEP 4: LOADING")
        print("=" * 60)

        stats = loader.load_all(transformed_jobs, snapshot_date=date.today())

        print(f"✓ Load complete:")
        print(f"  - New jobs: {stats['jobs_new']}")
        print(f"  - Updated jobs: {stats['jobs_updated']}")
        print(f"  - Expired jobs: {stats['jobs_expired']}")
        print(f"  - New technologies: {stats['technologies_new']}")
        print(f"  - Errors: {stats['errors']}")

        # STEP 5: FINALIZE
        duration = time.time() - start_time

        print("\n" + "=" * 60)
        print("ETL PIPELINE COMPLETED")
        print("=" * 60)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Total jobs processed: {len(raw_jobs)}")
        print(f"Jobs loaded: {stats['jobs_new'] + stats['jobs_updated']}")

        # Record scrape run
        db.record_scrape_run(
            jobs_found=len(raw_jobs),
            jobs_new=stats['jobs_new'],
            jobs_updated=stats['jobs_updated'],
            jobs_expired=stats['jobs_expired'],
            status='success',
            duration_seconds=duration
        )

        # Show database stats
        print("\nDatabase Statistics:")
        total_jobs = db.fetch_one("SELECT COUNT(*) as count FROM job_postings")
        active_jobs = db.fetch_one("SELECT COUNT(*) as count FROM job_postings WHERE is_active = 1")
        total_techs = db.fetch_one("SELECT COUNT(*) as count FROM technologies")

        print(f"  - Total jobs in database: {total_jobs['count']}")
        print(f"  - Active jobs: {active_jobs['count']}")
        print(f"  - Technologies tracked: {total_techs['count']}")

        print("\n✓ ETL pipeline completed successfully!")
        print("\nNext steps:")
        print("  1. Run the dashboard: streamlit run src/dashboard/app.py")
        print("  2. Schedule with GitHub Actions for daily updates")

        return 0

    except KeyboardInterrupt:
        print("\n\nETL pipeline interrupted by user")
        logging.info("ETL pipeline interrupted by user")
        return 1

    except Exception as e:
        print(f"\n\n✗ Error during ETL pipeline: {e}")
        logging.error(f"ETL pipeline failed: {e}", exc_info=True)

        # Record failed run
        db.record_scrape_run(
            status='failed',
            error_message=str(e),
            duration_seconds=time.time() - start_time
        )

        return 1

    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
