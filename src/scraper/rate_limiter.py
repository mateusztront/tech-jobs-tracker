"""
Rate limiter for ethical web scraping.
Implements delays, request tracking, and exponential backoff.
"""

import time
import random
import logging
from typing import Optional
from datetime import datetime, timedelta


class RateLimiter:
    """Manages request rate limiting for ethical scraping."""

    def __init__(self, config: dict):
        """
        Initialize rate limiter.

        Args:
            config: Configuration dict with rate limiting settings
        """
        self.min_delay = config.get('min_delay_seconds', 2)
        self.max_delay = config.get('max_delay_seconds', 5)
        self.requests_per_minute = config.get('requests_per_minute', 20)
        self.retry_attempts = config.get('retry_attempts', 3)
        self.retry_backoff = config.get('retry_backoff', 2)

        # Request tracking
        self.request_times = []
        self.last_request_time: Optional[float] = None

    def wait(self):
        """
        Wait appropriate time before next request.
        Implements random delay between min and max delay.
        """
        # Calculate delay
        delay = random.uniform(self.min_delay, self.max_delay)

        # If we have a last request time, ensure minimum delay
        if self.last_request_time:
            elapsed = time.time() - self.last_request_time
            if elapsed < self.min_delay:
                additional_wait = self.min_delay - elapsed
                delay = max(delay, additional_wait)

        # Wait
        time.sleep(delay)

        # Update last request time
        self.last_request_time = time.time()

        # Track request time
        self._record_request()

    def _record_request(self):
        """Record request time for rate limiting."""
        now = time.time()
        self.request_times.append(now)

        # Clean up old request times (older than 1 minute)
        cutoff = now - 60
        self.request_times = [t for t in self.request_times if t > cutoff]

    def check_rate_limit(self) -> bool:
        """
        Check if we're within rate limits.

        Returns:
            True if within limits, False otherwise
        """
        # Clean old requests
        now = time.time()
        cutoff = now - 60
        self.request_times = [t for t in self.request_times if t > cutoff]

        # Check if we've exceeded requests per minute
        return len(self.request_times) < self.requests_per_minute

    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        while not self.check_rate_limit():
            logging.warning("Rate limit approached, waiting 10 seconds...")
            time.sleep(10)

    def get_retry_delay(self, attempt: int) -> float:
        """
        Calculate retry delay with exponential backoff.

        Args:
            attempt: Current retry attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        return self.retry_backoff ** attempt

    def handle_rate_limit_error(self, attempt: int = 0):
        """
        Handle rate limit error (429 status code).

        Args:
            attempt: Current retry attempt number
        """
        delay = self.get_retry_delay(attempt) * 60  # Convert to minutes
        logging.warning(f"Rate limited! Waiting {delay/60:.1f} minutes before retry...")
        time.sleep(delay)

    def reset(self):
        """Reset rate limiter state."""
        self.request_times = []
        self.last_request_time = None


class CircuitBreaker:
    """
    Circuit breaker pattern for handling repeated failures.
    Prevents hammering a service that's having issues.
    """

    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 300):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening circuit
            timeout_seconds: How long to wait before trying again
        """
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = 'closed'  # closed, open, half-open

    def record_success(self):
        """Record a successful request."""
        self.failure_count = 0
        self.state = 'closed'

    def record_failure(self):
        """Record a failed request."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = 'open'
            logging.error(
                f"Circuit breaker opened after {self.failure_count} failures. "
                f"Waiting {self.timeout_seconds}s before retry."
            )

    def can_proceed(self) -> bool:
        """
        Check if requests can proceed.

        Returns:
            True if circuit is closed or half-open, False if open
        """
        if self.state == 'closed':
            return True

        if self.state == 'open':
            # Check if timeout has passed
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    self.state = 'half-open'
                    logging.info("Circuit breaker entering half-open state")
                    return True

            return False

        # half-open state
        return True

    def reset(self):
        """Reset circuit breaker."""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'closed'
