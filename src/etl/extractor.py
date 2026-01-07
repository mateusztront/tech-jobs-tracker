"""
Data extractor for ETL pipeline.
Extracts and validates structured data from raw scraper output.
"""

import logging
import hashlib
from typing import Dict, Optional, List
from datetime import date


class DataExtractor:
    """Extracts structured data from raw scraper output."""

    def __init__(self):
        """Initialize extractor."""
        self.required_fields = ['job_id', 'title', 'company_name', 'url']

    def extract_job_data(self, raw_data: Dict) -> Optional[Dict]:
        """
        Extract and validate job data from raw scraper output.

        Args:
            raw_data: Raw job data from scraper

        Returns:
            Validated job data dictionary or None if invalid
        """
        try:
            # Validate required fields
            if not self.validate_required_fields(raw_data):
                logging.warning(f"Missing required fields in job data")
                return None

            # Extract core job posting data
            job_posting = {
                'job_id': raw_data['job_id'],
                'title': self._clean_text(raw_data['title']),
                'company_name': self._clean_text(raw_data['company_name']),
                'url': raw_data['url'],
                'first_seen_date': date.today(),
                'last_seen_date': date.today(),
                'is_active': True
            }

            # Extract snapshot data
            snapshot = {
                'description': self._clean_text(raw_data.get('description')),
                'requirements': self._clean_text(raw_data.get('requirements')),
                'location': raw_data.get('location'),
                'seniority': raw_data.get('seniority'),
                'employment_type': raw_data.get('employment_type')
            }

            # Extract salary data
            salary = {
                'salary_text': raw_data.get('salary')
            }

            # Extract technologies
            technologies = raw_data.get('technologies', [])

            return {
                'job_posting': job_posting,
                'snapshot': snapshot,
                'salary': salary,
                'technologies': technologies
            }

        except Exception as e:
            logging.error(f"Error extracting job data: {e}")
            return None

    def validate_required_fields(self, data: Dict) -> bool:
        """
        Validate that required fields are present.

        Args:
            data: Job data dictionary

        Returns:
            True if valid, False otherwise
        """
        for field in self.required_fields:
            if field not in data or not data[field]:
                logging.warning(f"Missing required field: {field}")
                return False

        return True

    def validate_job_data(self, data: Dict) -> bool:
        """
        Validate extracted job data.

        Args:
            data: Extracted job data

        Returns:
            True if valid, False otherwise
        """
        if not data:
            return False

        # Check required sections
        if 'job_posting' not in data:
            return False

        job_posting = data['job_posting']

        # Validate job_id
        if not job_posting.get('job_id'):
            logging.warning("Invalid job_id")
            return False

        # Validate title
        title = job_posting.get('title', '')
        if len(title) < 3:
            logging.warning(f"Title too short: {title}")
            return False

        # Validate company
        company = job_posting.get('company_name', '')
        if len(company) < 2:
            logging.warning(f"Company name too short: {company}")
            return False

        # Validate URL
        url = job_posting.get('url', '')
        if not url.startswith('http'):
            logging.warning(f"Invalid URL: {url}")
            return False

        return True

    def generate_job_id(self, job_data: Dict) -> str:
        """
        Generate unique job ID from job data.
        Uses URL as primary identifier.

        Args:
            job_data: Job data dictionary

        Returns:
            Unique job ID string
        """
        # If job_id already exists in data, use it
        if job_data.get('job_id'):
            return job_data['job_id']

        # Generate from URL
        url = job_data.get('url', '')
        if url:
            # Extract slug from URL
            import re
            match = re.search(r'/job/([^/?]+)', url)
            if match:
                return match.group(1)

        # Fallback: hash of URL + title + company
        composite = f"{url}_{job_data.get('title', '')}_{job_data.get('company_name', '')}"
        return hashlib.md5(composite.encode()).hexdigest()[:16]

    def _clean_text(self, text: Optional[str]) -> Optional[str]:
        """
        Clean text data.

        Args:
            text: Text to clean

        Returns:
            Cleaned text or None
        """
        if not text:
            return None

        # Strip whitespace
        text = text.strip()

        # Remove multiple spaces
        import re
        text = re.sub(r'\s+', ' ', text)

        # Remove null bytes
        text = text.replace('\x00', '')

        return text if text else None

    def extract_batch(self, raw_data_list: List[Dict]) -> List[Dict]:
        """
        Extract data from a batch of raw job data.

        Args:
            raw_data_list: List of raw job data dictionaries

        Returns:
            List of extracted and validated job data
        """
        extracted_jobs = []

        for raw_data in raw_data_list:
            extracted = self.extract_job_data(raw_data)

            if extracted and self.validate_job_data(extracted):
                extracted_jobs.append(extracted)
            else:
                logging.warning(f"Skipping invalid job: {raw_data.get('url', 'Unknown')}")

        logging.info(f"Extracted {len(extracted_jobs)}/{len(raw_data_list)} valid jobs")

        return extracted_jobs
