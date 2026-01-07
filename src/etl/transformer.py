"""
Data transformer for ETL pipeline.
Normalizes, cleans, and standardizes job data.
"""

import re
import logging
from typing import Dict, Optional, List, Tuple


class DataTransformer:
    """Transforms and normalizes job data."""

    # Polish cities to regions mapping
    CITY_TO_REGION = {
        'Warszawa': 'Mazowieckie',
        'Kraków': 'Małopolskie',
        'Wrocław': 'Dolnośląskie',
        'Poznań': 'Wielkopolskie',
        'Gdańsk': 'Pomorskie',
        'Gdynia': 'Pomorskie',
        'Sopot': 'Pomorskie',
        'Szczecin': 'Zachodniopomorskie',
        'Łódź': 'Łódzkie',
        'Katowice': 'Śląskie',
        'Gliwice': 'Śląskie',
        'Bydgoszcz': 'Kujawsko-pomorskie',
        'Lublin': 'Lubelskie',
        'Białystok': 'Podlaskie',
        'Rzeszów': 'Podkarpackie',
        'Toruń': 'Kujawsko-pomorskie',
    }

    # Technology categories
    TECHNOLOGY_CATEGORIES = {
        'language': [
            'Python', 'Java', 'JavaScript', 'TypeScript', 'C#', 'C++', 'Go',
            'Rust', 'Ruby', 'PHP', 'Swift', 'Kotlin', 'Scala', 'R', 'Julia'
        ],
        'framework': [
            'React', 'Angular', 'Vue', 'Django', 'Flask', 'FastAPI', 'Spring',
            'Node.js', 'Express', '.NET', 'ASP.NET', 'Laravel', 'Rails',
            'Symfony', 'Next.js', 'Nuxt.js', 'Svelte'
        ],
        'database': [
            'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
            'Oracle', 'SQL Server', 'Cassandra', 'DynamoDB', 'MariaDB',
            'SQLite', 'Neo4j', 'CouchDB'
        ],
        'cloud': [
            'AWS', 'Azure', 'GCP', 'Google Cloud', 'Heroku', 'DigitalOcean',
            'Linode', 'Cloudflare'
        ],
        'tool': [
            'Docker', 'Kubernetes', 'Git', 'Jenkins', 'GitLab', 'GitHub',
            'Terraform', 'Ansible', 'Vagrant', 'CI/CD', 'Jira', 'Confluence'
        ]
    }

    def __init__(self):
        """Initialize transformer."""
        pass

    def transform(self, extracted_data: Dict) -> Dict:
        """
        Transform extracted job data.

        Args:
            extracted_data: Extracted job data

        Returns:
            Transformed job data
        """
        transformed = {
            'job_posting': extracted_data['job_posting'].copy(),
            'snapshot': self._transform_snapshot(extracted_data['snapshot']),
            'salary': self._transform_salary(extracted_data['salary']),
            'technologies': self._transform_technologies(extracted_data['technologies'])
        }

        return transformed

    def _transform_snapshot(self, snapshot: Dict) -> Dict:
        """
        Transform snapshot data.

        Args:
            snapshot: Snapshot data

        Returns:
            Transformed snapshot
        """
        transformed = snapshot.copy()

        # Parse location
        location_data = self.standardize_location(snapshot.get('location'))
        transformed.update(location_data)

        # Normalize seniority
        transformed['seniority_level'] = self.normalize_seniority(
            snapshot.get('seniority')
        )

        return transformed

    def _transform_salary(self, salary: Dict) -> Optional[Dict]:
        """
        Transform salary data.

        Args:
            salary: Salary data with raw text

        Returns:
            Normalized salary dictionary or None
        """
        salary_text = salary.get('salary_text')
        return self.normalize_salary(salary_text)

    def _transform_technologies(self, technologies: List[str]) -> List[Dict]:
        """
        Transform technologies list.

        Args:
            technologies: List of technology names

        Returns:
            List of technology dictionaries with categories
        """
        transformed = []

        for tech in technologies:
            tech_dict = {
                'name': tech,
                'category': self.categorize_technology(tech)
            }
            transformed.append(tech_dict)

        return transformed

    def normalize_salary(self, salary_text: Optional[str]) -> Optional[Dict]:
        """
        Parse and normalize salary text.

        Args:
            salary_text: Raw salary text (e.g., "10 000 - 15 000 PLN")

        Returns:
            Normalized salary dictionary or None
        """
        if not salary_text:
            return None

        try:
            # Remove spaces for easier parsing
            cleaned = salary_text.replace(' ', '').replace('\xa0', '')

            # Extract numbers
            numbers = re.findall(r'\d+', cleaned)
            if len(numbers) < 2:
                # Try single number (might be exact salary)
                if len(numbers) == 1:
                    value = int(numbers[0])
                    numbers = [value, value]
                else:
                    return None

            salary_min = int(numbers[0])
            salary_max = int(numbers[1])

            # Validate range
            if salary_min > salary_max:
                salary_min, salary_max = salary_max, salary_min

            # Detect currency
            currency = 'PLN'
            if 'EUR' in cleaned or '€' in cleaned:
                currency = 'EUR'
            elif 'USD' in cleaned or '$' in cleaned:
                currency = 'USD'

            # Detect period
            period = 'monthly'
            if '/h' in cleaned or 'godz' in cleaned.lower() or 'hour' in cleaned.lower():
                period = 'hourly'
            elif '/rok' in cleaned or 'annual' in cleaned.lower() or 'yearly' in cleaned.lower():
                period = 'annual'

            # Detect B2B vs employment
            is_b2b = any(word in cleaned.lower() for word in ['b2b', 'netto', 'net'])

            # Calculate average
            salary_avg = (salary_min + salary_max) / 2

            return {
                'salary_min': float(salary_min),
                'salary_max': float(salary_max),
                'salary_avg': float(salary_avg),
                'currency': currency,
                'period': period,
                'is_b2b': is_b2b
            }

        except Exception as e:
            logging.warning(f"Could not parse salary '{salary_text}': {e}")
            return None

    def standardize_location(self, location_text: Optional[str]) -> Dict:
        """
        Parse and standardize location information.

        Args:
            location_text: Raw location text

        Returns:
            Dictionary with location_type, city, region, country
        """
        if not location_text:
            return {
                'location_type': None,
                'city': None,
                'region': None,
                'country': 'Poland'
            }

        location_lower = location_text.lower()

        # Detect remote keywords
        remote_keywords = ['zdalna', 'remote', 'zdalnie', 'praca zdalna', 'remotely']
        is_remote = any(keyword in location_lower for keyword in remote_keywords)

        # Extract city
        city = None
        region = None

        for city_name, region_name in self.CITY_TO_REGION.items():
            if city_name.lower() in location_lower:
                city = city_name
                region = region_name
                break

        # Determine location type
        if is_remote and city:
            location_type = 'hybrid'
        elif is_remote:
            location_type = 'remote'
        elif city:
            location_type = 'office'
        else:
            location_type = None

        return {
            'location_type': location_type,
            'city': city,
            'region': region,
            'country': 'Poland'
        }

    def categorize_technology(self, tech_name: str) -> str:
        """
        Categorize a technology.

        Args:
            tech_name: Technology name

        Returns:
            Category string (language/framework/database/cloud/tool/other)
        """
        tech_lower = tech_name.lower()

        # First pass: exact match
        for category, tech_list in self.TECHNOLOGY_CATEGORIES.items():
            for tech in tech_list:
                if tech.lower() == tech_lower:
                    return category

        # Second pass: substring match (tech name contains list item)
        for category, tech_list in self.TECHNOLOGY_CATEGORIES.items():
            for tech in tech_list:
                if tech.lower() in tech_lower:
                    return category

        return 'other'

    def normalize_seniority(self, seniority: Optional[str]) -> str:
        """
        Normalize seniority level.

        Args:
            seniority: Raw seniority string

        Returns:
            Normalized seniority (junior/mid/senior)
        """
        if not seniority:
            return 'mid'  # Default

        seniority_lower = seniority.lower()

        if any(word in seniority_lower for word in ['senior', 'starszy', 'lead', 'principal', 'architect']):
            return 'senior'
        elif any(word in seniority_lower for word in ['junior', 'młodszy', 'trainee', 'graduate', 'entry']):
            return 'junior'
        else:
            return 'mid'

    def extract_seniority_from_title(self, title: str) -> str:
        """
        Extract seniority from job title.

        Args:
            title: Job title

        Returns:
            Seniority level
        """
        return self.normalize_seniority(title)

    def clean_description(self, description: Optional[str], max_length: int = 5000) -> Optional[str]:
        """
        Clean and truncate job description.

        Args:
            description: Raw description
            max_length: Maximum length

        Returns:
            Cleaned description
        """
        if not description:
            return None

        # Remove excessive whitespace
        cleaned = re.sub(r'\s+', ' ', description)

        # Truncate
        if len(cleaned) > max_length:
            cleaned = cleaned[:max_length] + '...'

        return cleaned

    def transform_batch(self, extracted_data_list: List[Dict]) -> List[Dict]:
        """
        Transform a batch of extracted job data.

        Args:
            extracted_data_list: List of extracted job data

        Returns:
            List of transformed job data
        """
        transformed_list = []

        for data in extracted_data_list:
            try:
                transformed = self.transform(data)
                transformed_list.append(transformed)
            except Exception as e:
                logging.error(f"Error transforming job data: {e}")
                continue

        logging.info(f"Transformed {len(transformed_list)}/{len(extracted_data_list)} jobs")

        return transformed_list
