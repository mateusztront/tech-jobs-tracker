"""
Display database information and statistics.
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.database.db_manager import DatabaseManager

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def main():
    db = DatabaseManager("data/jobs.db")

    print("=" * 60)
    print("DATABASE INFORMATION")
    print("=" * 60)

    # List all tables
    tables = db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )

    print(f"\nTables ({len(tables)}):")
    for table in tables:
        # Get row count
        count_result = db.fetch_one(f"SELECT COUNT(*) as count FROM {table['name']}")
        print(f"  - {table['name']:20} ({count_result['count']} rows)")

    # Show indexes
    indexes = db.fetch_all(
        "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%' ORDER BY name"
    )

    print(f"\nIndexes ({len(indexes)}):")
    for idx in indexes:
        print(f"  - {idx['name']}")

    # Last scrape info
    last_scrape = db.get_last_scrape_time()
    if last_scrape:
        print(f"\nLast successful scrape: {last_scrape}")
    else:
        print("\nNo scrape runs recorded yet")

    print("=" * 60)

    db.close()


if __name__ == "__main__":
    main()
