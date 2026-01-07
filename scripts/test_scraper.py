"""
Test scraper components with mock HTML.
"""

import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from bs4 import BeautifulSoup
from src.scraper.parser import JobParser
from src.scraper.rate_limiter import RateLimiter, CircuitBreaker


def test_parser():
    """Test HTML parser with mock data."""
    print("=" * 60)
    print("TEST: HTML Parser")
    print("=" * 60)

    # Mock job listing HTML
    listing_html = """
    <html>
        <body>
            <a href="/pl/job/python-developer-123">Python Developer</a>
            <a href="/pl/job/java-engineer-456">Java Engineer</a>
            <a href="/pl/job/devops-specialist-789">DevOps Specialist</a>
        </body>
    </html>
    """

    parser = JobParser("https://nofluffjobs.com")
    soup = BeautifulSoup(listing_html, 'lxml')
    urls = parser.extract_job_urls(soup)

    print(f"✓ Extracted {len(urls)} job URLs:")
    for url in urls:
        print(f"  - {url}")

    assert len(urls) == 3, f"Expected 3 URLs, got {len(urls)}"

    # Mock job detail HTML
    detail_html = """
    <html>
        <body>
            <h1>Senior Python Developer</h1>
            <div class="company">Tech Corp</div>
            <div class="salary">15000 - 20000 PLN</div>
            <div class="location">Warszawa / Zdalnie</div>
            <span class="tech-tag">Python</span>
            <span class="tech-tag">Django</span>
            <span class="tech-tag">PostgreSQL</span>
            <span class="tech-tag">Docker</span>
            <div class="description">
                Great opportunity to work with Python and modern technologies.
                We use AWS for infrastructure and Git for version control.
            </div>
        </body>
    </html>
    """

    soup = BeautifulSoup(detail_html, 'lxml')
    job_data = parser.parse_job_detail(soup, "https://nofluffjobs.com/job/test-123")

    print("\n✓ Parsed job details:")
    print(f"  - Job ID: {job_data['job_id']}")
    print(f"  - Title: {job_data['title']}")
    print(f"  - Company: {job_data['company_name']}")
    print(f"  - Salary: {job_data['salary']}")
    print(f"  - Location: {job_data['location']}")
    print(f"  - Seniority: {job_data['seniority']}")
    print(f"  - Technologies: {', '.join(job_data['technologies'])}")

    assert job_data['title'] == 'Senior Python Developer'
    assert job_data['company_name'] == 'Tech Corp'
    assert job_data['seniority'] == 'senior'
    assert len(job_data['technologies']) >= 4

    print("\n✓ Parser tests passed!")


def test_rate_limiter():
    """Test rate limiter."""
    print("\n" + "=" * 60)
    print("TEST: Rate Limiter")
    print("=" * 60)

    config = {
        'min_delay_seconds': 0.1,
        'max_delay_seconds': 0.2,
        'requests_per_minute': 10,
        'retry_attempts': 3,
        'retry_backoff': 2
    }

    rate_limiter = RateLimiter(config)

    print("Testing basic delay...")
    import time
    start = time.time()
    rate_limiter.wait()
    elapsed = time.time() - start

    print(f"✓ Delay: {elapsed:.3f}s (expected 0.1-0.2s)")
    assert 0.05 <= elapsed <= 0.3, f"Delay out of range: {elapsed}s"

    print("\nTesting rate limit checking...")
    for i in range(5):
        rate_limiter.wait()

    within_limit = rate_limiter.check_rate_limit()
    print(f"✓ Within rate limit: {within_limit}")

    print("\nTesting retry delay calculation...")
    delays = [rate_limiter.get_retry_delay(i) for i in range(3)]
    print(f"✓ Retry delays: {delays} (exponential backoff)")
    assert delays == [1, 2, 4], f"Unexpected delays: {delays}"

    print("\n✓ Rate limiter tests passed!")


def test_circuit_breaker():
    """Test circuit breaker."""
    print("\n" + "=" * 60)
    print("TEST: Circuit Breaker")
    print("=" * 60)

    breaker = CircuitBreaker(failure_threshold=3, timeout_seconds=1)

    print("Testing circuit states...")
    assert breaker.state == 'closed'
    assert breaker.can_proceed() == True
    print("✓ Initial state: closed")

    # Record failures
    for i in range(3):
        breaker.record_failure()
        print(f"  - Failure {i+1} recorded")

    assert breaker.state == 'open'
    assert breaker.can_proceed() == False
    print("✓ Circuit opened after 3 failures")

    # Wait for timeout
    print("  - Waiting for timeout...")
    import time
    time.sleep(1.1)

    assert breaker.can_proceed() == True
    assert breaker.state == 'half-open'
    print("✓ Circuit moved to half-open state")

    # Record success
    breaker.record_success()
    assert breaker.state == 'closed'
    print("✓ Circuit closed after success")

    print("\n✓ Circuit breaker tests passed!")


def main():
    """Run all tests."""
    print("#" * 60)
    print("# SCRAPER COMPONENT TESTS")
    print("#" * 60)

    try:
        test_parser()
        test_rate_limiter()
        test_circuit_breaker()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)
        print("\nScraper components are ready!")
        print("\nNext: Test with real NoFluffJobs website:")
        print("  python scripts/run_scraper.py")
        print("\n")

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
