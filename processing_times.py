"""
Processing Times - Live fetch from USCIS for student visa processing.

Fetches current processing times from the USCIS egov endpoint.
Caches results for 24 hours to avoid excessive requests.

Usage:
    from processing_times import get_processing_times
    times = get_processing_times()
"""

import os
import json
import time
import requests
from datetime import datetime, timedelta

CACHE_FILE = os.path.join(os.path.dirname(__file__), ".processing_times_cache.json")
CACHE_DURATION_HOURS = 24

# USCIS processing times endpoint
USCIS_PROCESSING_URL = "https://egov.uscis.gov/processing-times/"


def load_cache():
    """Load cached processing times if still valid."""
    if not os.path.exists(CACHE_FILE):
        return None

    try:
        with open(CACHE_FILE, "r") as f:
            data = json.load(f)

        cached_time = datetime.fromisoformat(data.get("cached_at", ""))
        if datetime.now() - cached_time < timedelta(hours=CACHE_DURATION_HOURS):
            return data.get("data")
        return None
    except Exception:
        return None


def save_cache(data):
    """Cache processing times to disk."""
    cache_data = {
        "cached_at": datetime.now().isoformat(),
        "data": data,
    }
    with open(CACHE_FILE, "w") as f:
        json.dump(cache_data, f, indent=2)


def fetch_processing_times():
    """
    Fetch processing times from USCIS for student visa-related forms.
    Returns a dict of form -> processing time info.

    NOTE: This is a placeholder implementation. The actual USCIS processing
    times page may require a different approach (e.g., hitting their API
    endpoint or parsing the specific form page).

    Student visa relevant forms:
    - I-765 (Application for Employment Authorization) - used for OPT/CPT
    - I-20 (Certificate of Eligibility) - issued by DSO, not USCIS
    - DS-160 (Online Nonimmigrant Visa Application) - State Department, not USCIS
    """
    # Student visa processing is primarily handled at US embassies/consulates,
    # not through USCIS form processing times. Key relevant USCIS forms:
    # - I-765 (OPT application)
    # - I-539 (Change of Status)

    print("[processing_times] Live fetch placeholder - configure actual USCIS endpoint")
    print("[processing_times] Check https://egov.uscis.gov/processing-times/ for the actual data source")
    print("[processing_times] Student visa interview times vary by embassy; check travel.state.gov")

    return {
        "i-765": {
            "description": "Application for Employment Authorization (OPT/CPT)",
            "service_center": "Varies by service center",
            "current_processing": "Check egov.uscis.gov for live data",
            "premium_processing": "Not available for I-765",
            "last_checked": datetime.now().isoformat(),
        },
        "i-539": {
            "description": "Application to Extend/Change Nonimmigrant Status",
            "service_center": "Varies by service center",
            "current_processing": "Check egov.uscis.gov for live data",
            "premium_processing": "Not available for I-539",
            "last_checked": datetime.now().isoformat(),
        },
        "visa_interview": {
            "description": "F-1/J-1/M-1 Visa Interview Wait Times",
            "service_center": "Varies by US embassy/consulate",
            "current_processing": "Check travel.state.gov for location-specific wait times",
            "premium_processing": "Not available",
            "note": "Wait times vary significantly by country and season. Summer months (May-August) typically have longer waits.",
            "last_checked": datetime.now().isoformat(),
        },
    }


def get_processing_times(form=None):
    """
    Get processing times, using cache if available.

    Args:
        form: Optional form type filter (e.g., "i-765", "i-539")

    Returns:
        dict: Processing times data
    """
    # Try cache first
    cached = load_cache()
    if cached:
        if form:
            return cached.get(form.lower())
        return cached

    # Fetch fresh data
    data = fetch_processing_times()
    save_cache(data)

    if form:
        return data.get(form.lower())
    return data


if __name__ == "__main__":
    print("USCIS Processing Times (Student Visa)")
    print("=" * 40)
    times = get_processing_times()
    for form, info in times.items():
        print(f"\n{form.upper()}")
        for key, value in info.items():
            print(f"  {key}: {value}")
