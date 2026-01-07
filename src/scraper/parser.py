"""
HTML parser for NoFluffJobs website.
Extracts job listings and detailed job information.
"""

import re
import logging
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin


class JobParser:
    """Parses HTML content from NoFluffJobs."""

    def __init__(self, base_url: str = "https://nofluffjobs.com"):
        """
        Initialize parser.

        Args:
            base_url: Base URL for the job site
        """
        self.base_url = base_url

    def extract_job_urls(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract all job URLs from a listing page.

        Args:
            soup: BeautifulSoup object of the listing page

        Returns:
            List of absolute job URLs
        """
        job_urls = []

        # NoFluffJobs typically uses links with specific patterns
        # Try multiple selectors to be robust
        selectors = [
            'a[href*="/job/"]',
            'a.posting-list-item',
            'a[class*="posting"]',
            'div.posting a',
            'article a[href*="/pl/job/"]'
        ]

        for selector in selectors:
            links = soup.select(selector)
            for link in links:
                href = link.get('href')
                if href and '/job/' in href:
                    # Convert to absolute URL
                    absolute_url = urljoin(self.base_url, href)
                    if absolute_url not in job_urls:
                        job_urls.append(absolute_url)

        logging.info(f"Extracted {len(job_urls)} job URLs from page")
        return job_urls

    def parse_job_detail(self, soup: BeautifulSoup, url: str) -> Dict:
        """
        Parse detailed job information from a job detail page.

        Args:
            soup: BeautifulSoup object of the job detail page
            url: URL of the job posting

        Returns:
            Dictionary with job details
        """
        job_data = {
            'url': url,
            'job_id': self._extract_job_id(url),
            'title': self._extract_title(soup),
            'company_name': self._extract_company(soup),
            'description': self._extract_description(soup),
            'requirements': self._extract_requirements(soup),
            'salary': self._extract_salary(soup),
            'location': self._extract_location(soup),
            'technologies': self._extract_technologies(soup),
            'seniority': self._extract_seniority(soup),
            'employment_type': self._extract_employment_type(soup),
        }

        return job_data

    def _extract_job_id(self, url: str) -> str:
        """
        Extract unique job ID from URL.

        Args:
            url: Job posting URL

        Returns:
            Job ID string
        """
        # Extract from URL pattern: /job/some-job-title-123abc
        match = re.search(r'/job/([^/?]+)', url)
        if match:
            return match.group(1)

        # Fallback: use hash of URL
        import hashlib
        return hashlib.md5(url.encode()).hexdigest()[:16]

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract job title."""
        # Try multiple selectors
        selectors = ['h1', 'h1.posting-title', '[class*="title"]']

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text(strip=True)
                if title and len(title) > 5:  # Sanity check
                    return title

        logging.warning("Could not extract job title")
        return "Unknown Title"

    def _extract_company(self, soup: BeautifulSoup) -> str:
        """Extract company name."""
        selectors = [
            '[class*="company"]',
            'a[href*="/company/"]',
            'div.company-name',
            'span.company'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                company = element.get_text(strip=True)
                if company:
                    return company

        logging.warning("Could not extract company name")
        return "Unknown Company"

    def _extract_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job description."""
        # Look for description section
        selectors = [
            '[class*="description"]',
            '[class*="about"]',
            'section.job-description',
            'div.description'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                # Get text, preserve some structure
                description = element.get_text(separator='\n', strip=True)
                if description:
                    return description[:5000]  # Limit length

        return None

    def _extract_requirements(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract job requirements."""
        selectors = [
            '[class*="requirement"]',
            '[class*="must-have"]',
            'section.requirements'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                requirements = element.get_text(separator='\n', strip=True)
                if requirements:
                    return requirements[:5000]

        return None

    def _extract_salary(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract salary information."""
        # Look for salary elements
        selectors = [
            '[class*="salary"]',
            '[class*="money"]',
            'span.salary',
            'div.salary-range'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                salary_text = element.get_text(strip=True)
                # Look for numbers and currency
                if re.search(r'\d', salary_text):
                    return salary_text

        # Try to find in text
        text = soup.get_text()
        salary_match = re.search(r'(\d[\d\s]*-[\d\s]*\d)\s*(PLN|zł|EUR)', text)
        if salary_match:
            return salary_match.group(0)

        return None

    def _extract_location(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract location information."""
        selectors = [
            '[class*="location"]',
            '[class*="city"]',
            'span.location',
            'div.location'
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                location = element.get_text(strip=True)
                if location:
                    return location

        return None

    def _extract_technologies(self, soup: BeautifulSoup) -> List[str]:
        """Extract required technologies/skills."""
        technologies = []

        # Look for technology tags/badges
        selectors = [
            '[class*="technology"]',
            '[class*="skill"]',
            '[class*="tech-"]',
            'span.tag',
            'div.tags span'
        ]

        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                tech = element.get_text(strip=True)
                if tech and len(tech) > 1 and tech not in technologies:
                    technologies.append(tech)

        # If no structured tags, try to extract from description
        if not technologies:
            technologies = self._extract_technologies_from_text(soup)

        return technologies[:50]  # Limit to 50

    def _extract_technologies_from_text(self, soup: BeautifulSoup) -> List[str]:
        """
        Extract technologies from text using common technology keywords.

        Args:
            soup: BeautifulSoup object

        Returns:
            List of technology names found
        """
        # Common technologies in Polish IT job market
        tech_keywords = [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C#', 'C++', 'Go', 'Rust',
            'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala',
            'React', 'Angular', 'Vue', 'Django', 'Flask', 'FastAPI', 'Spring',
            'Node.js', 'Express', '.NET', 'ASP.NET',
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch', 'Oracle',
            'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform',
            'Git', 'Jenkins', 'GitLab', 'CI/CD', 'Ansible',
            'Linux', 'Ubuntu', 'Windows', 'MacOS'
        ]

        text = soup.get_text()
        found_techs = []

        for tech in tech_keywords:
            # Case-insensitive search
            if re.search(r'\b' + re.escape(tech) + r'\b', text, re.IGNORECASE):
                if tech not in found_techs:
                    found_techs.append(tech)

        return found_techs

    def _extract_seniority(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract seniority level."""
        # Get title and description
        title_elem = soup.select_one('h1')
        title = title_elem.get_text(strip=True).lower() if title_elem else ''

        # Check for seniority keywords
        if any(word in title for word in ['senior', 'starszy', 'lead', 'principal', 'architect']):
            return 'senior'
        elif any(word in title for word in ['junior', 'młodszy', 'trainee', 'graduate']):
            return 'junior'
        elif any(word in title for word in ['mid', 'regular']):
            return 'mid'

        # Check in body
        text = soup.get_text().lower()
        if 'senior' in text or 'starszy' in text:
            return 'senior'
        elif 'junior' in text or 'młodszy' in text:
            return 'junior'

        return 'mid'  # Default

    def _extract_employment_type(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract employment type (full-time, part-time, contract, etc.)."""
        text = soup.get_text().lower()

        if 'b2b' in text:
            return 'b2b'
        elif 'full-time' in text or 'pełny etat' in text:
            return 'full-time'
        elif 'part-time' in text or 'część etatu' in text:
            return 'part-time'
        elif 'contract' in text or 'kontrakt' in text or 'umowa' in text:
            return 'contract'

        return None

    def has_next_page(self, soup: BeautifulSoup) -> bool:
        """
        Check if there's a next page in pagination.

        Args:
            soup: BeautifulSoup object

        Returns:
            True if next page exists, False otherwise
        """
        # Look for pagination next button
        next_selectors = [
            'a[rel="next"]',
            'a.next',
            'a[aria-label*="next"]',
            'button.next',
            'a:contains("Next")',
            'a:contains("Następna")'
        ]

        for selector in next_selectors:
            element = soup.select_one(selector)
            if element and not element.get('disabled'):
                return True

        return False
