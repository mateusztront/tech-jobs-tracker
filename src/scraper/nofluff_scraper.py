"""
Main scraper for NoFluffJobs website.
Coordinates scraping with rate limiting and error handling.
"""

import requests
import logging
import time
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .rate_limiter import RateLimiter, CircuitBreaker
from .parser import JobParser


class NoFluffScraper:
    """Main scraper for NoFluffJobs."""

    def __init__(self, config: dict):
        """
        Initialize scraper.

        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.base_url = config['scraper']['base_url']
        self.search_url = config['scraper']['search_url']
        self.user_agent = config['scraper']['user_agent']
        self.timeout = config['scraper']['timeout_seconds']
        self.max_pages = config['scraping']['max_pages']
        self.max_jobs = config['scraping'].get('max_jobs_per_run', 1000)

        # Initialize components
        self.rate_limiter = RateLimiter(config['rate_limiting'])
        self.circuit_breaker = CircuitBreaker(failure_threshold=5, timeout_seconds=300)
        self.parser = JobParser(self.base_url)

        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })

        # Statistics
        self.stats = {
            'pages_scraped': 0,
            'jobs_found': 0,
            'jobs_scraped': 0,
            'errors': 0
        }

    def scrape_all(self) -> List[Dict]:
        """
        Scrape all job listings.

        Returns:
            List of job data dictionaries
        """
        logging.info("Starting NoFluffJobs scraper")
        logging.info(f"Max pages: {self.max_pages}, Max jobs: {self.max_jobs}")

        # Phase 1: Get all job URLs
        job_urls = self._scrape_job_urls()
        logging.info(f"Found {len(job_urls)} job URLs")

        if not job_urls:
            logging.warning("No job URLs found. Check if website structure changed.")
            return []

        # Limit to max jobs
        if len(job_urls) > self.max_jobs:
            logging.info(f"Limiting to {self.max_jobs} jobs")
            job_urls = job_urls[:self.max_jobs]

        # Phase 2: Scrape each job detail
        all_jobs = []
        for i, url in enumerate(job_urls, 1):
            if not self.circuit_breaker.can_proceed():
                logging.error("Circuit breaker open, stopping scrape")
                break

            try:
                logging.info(f"Scraping job {i}/{len(job_urls)}: {url}")

                # Rate limiting
                if i > 1:  # Don't wait before first request
                    self.rate_limiter.wait()

                job_data = self._scrape_job_detail(url)

                if job_data:
                    all_jobs.append(job_data)
                    self.stats['jobs_scraped'] += 1
                    self.circuit_breaker.record_success()
                    logging.info(f"✓ Successfully scraped: {job_data.get('title', 'Unknown')}")
                else:
                    logging.warning(f"Failed to scrape job: {url}")

            except Exception as e:
                self.stats['errors'] += 1
                self.circuit_breaker.record_failure()
                logging.error(f"Error scraping {url}: {e}")

                # Continue with next job
                continue

        # Log final statistics
        self._log_statistics()

        return all_jobs

    def _scrape_job_urls(self) -> List[str]:
        """
        Scrape all job URLs from listing pages.

        Returns:
            List of job URLs
        """
        all_urls = []
        page = 1

        while page <= self.max_pages:
            try:
                logging.info(f"Scraping listing page {page}")

                # Rate limiting
                if page > 1:
                    self.rate_limiter.wait()

                # Fetch page
                url = self._get_page_url(page)
                html = self._fetch_page(url)

                if not html:
                    logging.warning(f"Empty response for page {page}")
                    break

                soup = BeautifulSoup(html, 'lxml')

                # Extract job URLs
                page_urls = self.parser.extract_job_urls(soup)

                if not page_urls:
                    logging.info(f"No more jobs found on page {page}")
                    break

                all_urls.extend(page_urls)
                self.stats['pages_scraped'] += 1
                self.stats['jobs_found'] += len(page_urls)

                logging.info(f"Found {len(page_urls)} jobs on page {page} (total: {len(all_urls)})")

                # Check if there's a next page
                if not self.parser.has_next_page(soup):
                    logging.info("No more pages available")
                    break

                page += 1

            except Exception as e:
                logging.error(f"Error scraping page {page}: {e}")
                break

        # Remove duplicates
        unique_urls = list(set(all_urls))
        logging.info(f"Found {len(unique_urls)} unique job URLs (removed {len(all_urls) - len(unique_urls)} duplicates)")

        return unique_urls

    def _scrape_job_detail(self, url: str) -> Optional[Dict]:
        """
        Scrape detailed information for a single job.

        Args:
            url: Job posting URL

        Returns:
            Job data dictionary or None if failed
        """
        try:
            html = self._fetch_page(url)

            if not html:
                return None

            soup = BeautifulSoup(html, 'lxml')
            job_data = self.parser.parse_job_detail(soup, url)

            return job_data

        except Exception as e:
            logging.error(f"Error parsing job detail: {e}")
            return None

    def _fetch_page(self, url: str, retry_count: int = 0) -> Optional[str]:
        """
        Fetch a page with retry logic.

        Args:
            url: URL to fetch
            retry_count: Current retry attempt

        Returns:
            HTML content or None if failed
        """
        max_retries = self.rate_limiter.retry_attempts

        try:
            response = self.session.get(
                url,
                timeout=self.timeout,
                verify=self.config['scraper'].get('verify_ssl', True)
            )

            # Handle different status codes
            if response.status_code == 200:
                return response.text

            elif response.status_code == 429:
                # Rate limited
                if retry_count < max_retries:
                    logging.warning(f"Rate limited (429), retry {retry_count + 1}/{max_retries}")
                    self.rate_limiter.handle_rate_limit_error(retry_count)
                    return self._fetch_page(url, retry_count + 1)
                else:
                    logging.error("Max retries reached for rate limiting")
                    return None

            elif response.status_code == 404:
                # Job not found (might be expired)
                logging.info(f"Job not found (404): {url}")
                return None

            elif response.status_code in [500, 502, 503, 504]:
                # Server error
                if retry_count < max_retries:
                    delay = self.rate_limiter.get_retry_delay(retry_count)
                    logging.warning(f"Server error ({response.status_code}), waiting {delay}s before retry")
                    time.sleep(delay)
                    return self._fetch_page(url, retry_count + 1)
                else:
                    logging.error(f"Server error {response.status_code}, max retries reached")
                    return None

            else:
                logging.error(f"Unexpected status code {response.status_code} for {url}")
                return None

        except requests.Timeout:
            if retry_count < max_retries:
                logging.warning(f"Request timeout, retry {retry_count + 1}/{max_retries}")
                time.sleep(self.rate_limiter.get_retry_delay(retry_count))
                return self._fetch_page(url, retry_count + 1)
            else:
                logging.error(f"Timeout after {max_retries} retries")
                return None

        except requests.ConnectionError as e:
            if retry_count < max_retries:
                logging.warning(f"Connection error, retry {retry_count + 1}/{max_retries}")
                time.sleep(self.rate_limiter.get_retry_delay(retry_count) * 2)
                return self._fetch_page(url, retry_count + 1)
            else:
                logging.error(f"Connection error after {max_retries} retries: {e}")
                return None

        except Exception as e:
            logging.error(f"Unexpected error fetching {url}: {e}")
            return None

    def _get_page_url(self, page: int) -> str:
        """
        Get URL for a specific page number.

        Args:
            page: Page number

        Returns:
            URL string
        """
        # NoFluffJobs might use different pagination patterns
        # Try common patterns
        if page == 1:
            return self.search_url
        else:
            # Common patterns: ?page=2, ?p=2, /page/2
            return f"{self.search_url}?page={page}"

    def _log_statistics(self):
        """Log scraping statistics."""
        logging.info("=" * 60)
        logging.info("SCRAPING STATISTICS")
        logging.info("=" * 60)
        logging.info(f"Pages scraped: {self.stats['pages_scraped']}")
        logging.info(f"Jobs found: {self.stats['jobs_found']}")
        logging.info(f"Jobs scraped successfully: {self.stats['jobs_scraped']}")
        logging.info(f"Errors: {self.stats['errors']}")
        logging.info("=" * 60)

    def check_robots_txt(self):
        """
        Check robots.txt for scraping permissions.
        This is ethical scraping practice.
        """
        robots_url = urljoin(self.base_url, '/robots.txt')

        try:
            response = self.session.get(robots_url, timeout=10)
            if response.status_code == 200:
                logging.info("robots.txt content:")
                logging.info(response.text[:500])  # First 500 chars
                return response.text
        except Exception as e:
            logging.warning(f"Could not fetch robots.txt: {e}")

        return None

    def close(self):
        """Close the session."""
        self.session.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
