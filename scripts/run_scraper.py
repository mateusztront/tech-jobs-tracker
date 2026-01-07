"""
Manual scraper execution script.
Runs the NoFluffJobs scraper and displays results.
"""

import sys
import os
import time
import logging
import yaml
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Add src directory to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.scraper.nofluff_scraper import NoFluffScraper
from src.database.db_manager import DatabaseManager


def setup_logging():
    """Configure logging."""
    log_dir = project_root / 'logs'
    log_dir.mkdir(exist_ok=True)

    log_file = log_dir / f'scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'

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

    # Merge configs
    config.update(scraper_config)

    return config


def display_job_summary(job: dict):
    """Display a summary of a scraped job."""
    print(f"\n{'='*60}")
    print(f"Job ID: {job.get('job_id', 'N/A')}")
    print(f"Title: {job.get('title', 'N/A')}")
    print(f"Company: {job.get('company_name', 'N/A')}")
    print(f"Salary: {job.get('salary', 'N/A')}")
    print(f"Location: {job.get('location', 'N/A')}")
    print(f"Seniority: {job.get('seniority', 'N/A')}")
    print(f"Technologies: {', '.join(job.get('technologies', []))[:100]}")
    print(f"URL: {job.get('url', 'N/A')}")


def main():
    """Main execution function."""
    print("=" * 60)
    print("NoFluffJobs Scraper")
    print("=" * 60)

    # Setup
    log_file = setup_logging()
    logging.info("Starting scraper execution")
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

    # Initialize database
    db = DatabaseManager(str(db_path))

    # Confirm scraping
    print("\nScraper Configuration:")
    print(f"  - Base URL: {config['scraper']['base_url']}")
    print(f"  - Max pages: {config['scraping']['max_pages']}")
    print(f"  - Max jobs: {config['scraping'].get('max_jobs_per_run', 1000)}")
    print(f"  - Rate limit: {config['rate_limiting']['min_delay_seconds']}-{config['rate_limiting']['max_delay_seconds']}s per request")

    print("\n⚠️  This will make requests to NoFluffJobs website.")
    print("   Please ensure you're following ethical scraping practices.")

    response = input("\nProceed with scraping? (yes/no): ")
    if response.lower() != 'yes':
        print("Scraping cancelled.")
        return 0

    # Check robots.txt
    print("\nChecking robots.txt...")
    scraper = NoFluffScraper(config)
    scraper.check_robots_txt()

    # Run scraper
    print("\n" + "=" * 60)
    print("STARTING SCRAPE")
    print("=" * 60)

    start_time = time.time()

    try:
        with NoFluffScraper(config) as scraper:
            jobs = scraper.scrape_all()

        duration = time.time() - start_time

        # Display results
        print("\n" + "=" * 60)
        print("SCRAPING COMPLETED")
        print("=" * 60)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Jobs scraped: {len(jobs)}")

        if jobs:
            print(f"\nFirst 3 jobs:")
            for job in jobs[:3]:
                display_job_summary(job)

            # Save to file for inspection
            import json
            output_file = project_root / 'logs' / f'scraped_jobs_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(jobs, f, indent=2, ensure_ascii=False)

            print(f"\n✓ Full data saved to: {output_file}")
            print(f"\nNext steps:")
            print(f"  1. Review scraped data in {output_file}")
            print(f"  2. Implement ETL pipeline to process and load data into database")
            print(f"  3. Run ETL to populate database with job data")

        else:
            print("\n⚠️  No jobs were scraped. Possible reasons:")
            print("  - Website structure may have changed")
            print("  - Network connectivity issues")
            print("  - Rate limiting or blocking")
            print(f"\nCheck the log file for details: {log_file}")

        # Record scrape run
        db.record_scrape_run(
            jobs_found=len(jobs),
            jobs_new=0,  # Will be updated when ETL runs
            jobs_updated=0,
            status='success' if jobs else 'partial',
            duration_seconds=duration
        )

        return 0

    except KeyboardInterrupt:
        print("\n\nScraping interrupted by user")
        logging.info("Scraping interrupted by user")
        return 1

    except Exception as e:
        print(f"\n\n✗ Error during scraping: {e}")
        logging.error(f"Scraping failed: {e}", exc_info=True)

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
