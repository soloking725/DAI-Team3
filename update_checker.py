"""
Update Checker - Hash-based content freshness monitoring for student visa sources.

Periodically checks official government pages for changes.
If content has changed, triggers re-ingestion.

Usage:
    python update_checker.py
"""

import os
import json
import hashlib
import requests
from datetime import datetime

CACHE_FILE = os.path.join(os.path.dirname(__file__), ".page_hashes_cache.json")

# Pages to monitor for changes (student visa focused)
MONITORED_PAGES = [
    "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html",
    "https://travel.state.gov/content/travel/en/us-visas/study/exchange-visitor.html",
    "https://travel.state.gov/content/travel/en/us-visas/study/other-study-options/vocational-students.html",
    "https://www.uscis.gov/international-students-academics",
    "https://www.uscis.gov/j-exchange-visitor",
    "https://www.uscis.gov/m-vocational-student",
    "https://studyinthestates.dhs.gov/f-students",
    "https://studyinthestates.dhs.gov/m-students",
]


def hash_page_content(url):
    """Fetch a page and compute a content hash."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        # Hash the text content
        content_hash = hashlib.md5(response.text.encode("utf-8")).hexdigest()
        return content_hash
    except Exception as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None


def load_hash_cache():
    """Load previously computed hashes."""
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_hash_cache(cache):
    """Save hashes to disk."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def check_for_updates():
    """
    Check all monitored pages for content changes.

    Returns:
        list: URLs that have changed
    """
    print("=" * 60)
    print("US Student Visa Information Resource - Update Checker")
    print("=" * 60)

    cache = load_hash_cache()
    changed_urls = []

    for url in MONITORED_PAGES:
        print(f"\nChecking: {url}")
        current_hash = hash_page_content(url)

        if current_hash is None:
            continue

        previous_hash = cache.get(url)

        if previous_hash is None:
            print("  [NEW] First time checking this page.")
            cache[url] = {
                "hash": current_hash,
                "last_checked": datetime.now().isoformat(),
            }
        elif previous_hash != current_hash:
            print("  [CHANGED] Content has changed since last check.")
            changed_urls.append(url)
            cache[url] = {
                "hash": current_hash,
                "last_checked": datetime.now().isoformat(),
            }
        else:
            print("  [OK] No changes detected.")

    save_hash_cache(cache)

    print("\n" + "=" * 60)
    if changed_urls:
        print(f"Changes detected in {len(changed_urls)} page(s):")
        for url in changed_urls:
            print(f"  - {url}")
        print("\nRun 'python ingest.py' to re-ingest updated content.")
    else:
        print("No changes detected. Database is up to date.")
    print("=" * 60)

    return changed_urls


if __name__ == "__main__":
    check_for_updates()
