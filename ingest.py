"""
Document ingestion pipeline for student visa content.

Scrapes USCIS, State Dept, SEVP, SSA, and IRS pages relevant to
F-1, J-1, and M-1 student visas. Splits into chunks. Stores in ChromaDB with metadata for citation.

Uses curl_cffi for Cloudflare bypass (gov sites are protected).
Uses pdfplumber for PDF parsing.

Usage:
    python ingest.py          # full re-ingest
    python ingest.py --fast   # only update changed pages
"""

import os
import json
import time
import hashlib
import datetime
import pdfplumber
import curl_cffi
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import chromadb

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "student_visa_documents"
CHUNK_SIZE = 800
CHUNK_OVERLAP = 150
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
CACHE_FILE = os.path.join(os.path.dirname(__file__), "ingest_cache.json")
RETRY_COUNT = 3
RETRY_DELAY = 2  # seconds between retries

# Official government URLs to scrape (student visa focused)
# Verified working with curl_cffi (impersonate="chrome")
SOURCE_URLS = [
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas/study.html",
        "title": "State Department - Study in the United States (F-1/M-1/J-1 Overview)",
        "agency": "State Department",
        "visa_type": ["F-1", "M-1", "J-1"],
    },
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas.html",
        "title": "State Department - US Visas Overview",
        "agency": "State Department",
        "visa_type": ["F-1", "M-1", "J-1"],
    },
    {
        "url": "https://www.uscis.gov/working-in-the-united-states/students-and-exchange-visitors",
        "title": "USCIS - Students and Exchange Visitors",
        "agency": "USCIS",
        "visa_type": ["F-1", "J-1", "M-1"],
    },
    {
        "url": "https://studyinthestates.dhs.gov/",
        "title": "DHS/SEVP - Study in the States",
        "agency": "SEVP",
        "visa_type": ["F-1", "M-1", "J-1"],
    },
    {
        "url": "https://www.uscis.gov/",
        "title": "USCIS - Homepage (Immigration Benefits)",
        "agency": "USCIS",
        "visa_type": ["F-1", "J-1", "M-1"],
    },
    {
        "url": "https://studyinthestates.dhs.gov/students/work/obtaining-a-social-security-number",
        "title": "DHS/SEVP - Obtaining a Social Security Number",
        "agency": "SEVP",
        "visa_type": ["F-1", "J-1", "M-1"],
    },
    {
        # Live-scraped counterpart to the hand-authored SSA content in
        # ingest_static.py — the old live URL (ssa.gov/foreign/immigrant/apply.html)
        # 404s; this is the current page covering the same SSA-5 application.
        "url": "https://www.ssa.gov/ssnumber/ss5doc.htm",
        "title": "SSA - Documents Needed for a Social Security Card",
        "agency": "SSA",
        "visa_type": ["F-1", "J-1", "M-1"],
    },
    {
        # Replaces the stale irs.gov/individuals/international-taxes/... path —
        # the IRS reorganized this section under international-taxpayers/.
        "url": "https://www.irs.gov/individuals/international-taxpayers/foreign-students-scholars-teachers-researchers-and-exchange-visitors",
        "title": "IRS - Foreign Students, Scholars, Teachers, Researchers and Exchange Visitors",
        "agency": "IRS",
        "visa_type": ["F-1", "J-1", "M-1"],
    },
]

# Origin-country-specific embassy/consulate visa pages. Each is tagged with
# origin_country so shared/retrieval.py's origin_country filter can surface
# country-specific guidance (embassy locations, appointment quirks, local
# notices) instead of only the generic US-agency pages above. Unlike
# ingest_static.py's hand-authored country content, these run through the
# normal scrape pipeline so they stay current on every `python ingest.py` run
# — the whole point of live ingestion for content that changes per-post
# (e.g. temporary visa-issuance pauses, new appointment systems).
ORIGIN_COUNTRY_SOURCE_URLS = [
    {
        "url": "https://ph.usembassy.gov/visas/",
        "title": "US Embassy Philippines - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Philippines",
    },
    {
        "url": "https://vn.usembassy.gov/visas/",
        "title": "US Embassy Vietnam - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Vietnam",
    },
    {
        "url": "https://pk.usembassy.gov/visas/important-visa-information/",
        "title": "US Embassy Pakistan - Important Visa Information",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Pakistan",
    },
    {
        "url": "https://bd.usembassy.gov/visas/",
        "title": "US Embassy Bangladesh - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Bangladesh",
    },
    {
        "url": "https://mx.usembassy.gov/visas/",
        "title": "US Embassy Mexico - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Mexico",
    },
    {
        "url": "https://gh.usembassy.gov/visas/",
        "title": "US Embassy Ghana - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Ghana",
    },
    {
        "url": "https://np.usembassy.gov/visas/",
        "title": "US Embassy Nepal - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Nepal",
    },
    {
        "url": "https://id.usembassy.gov/visas/",
        "title": "US Embassy Indonesia - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Indonesia",
    },
    # Added after checking Colby's own international-student profile (top
    # countries: China, Canada, India) and IIE Open Doors' latest top-sending
    # countries — Canada, Colombia, and Peru are among the countries that hit
    # record highs in the most recent report; Japan is called out specifically
    # for Colby's "best value" fit.
    {
        "url": "https://ca.usembassy.gov/consular-services/",
        "title": "US Embassy Canada - Consular Services",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Canada",
    },
    {
        "url": "https://co.usembassy.gov/visas/",
        "title": "US Embassy Colombia - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Colombia",
    },
    {
        "url": "https://pe.usembassy.gov/visas/",
        "title": "US Embassy Peru - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Peru",
    },
    {
        "url": "https://jp.usembassy.gov/visas/",
        "title": "US Embassy Japan - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Japan",
    },
    # The remaining five of the 17 pinned COMMON_ORIGIN_COUNTRIES (see
    # shared/countries.py) used to be hand-authored, static content in
    # ingest_static.py. Moved to the live scrape pipeline here so they stay
    # current the same way as the twelve above, instead of going stale.
    {
        "url": "https://in.usembassy.gov/visas/",
        "title": "US Mission India - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "India",
    },
    {
        "url": "https://china.usembassy-china.org.cn/visas/",
        "title": "US Mission China - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "China",
    },
    {
        "url": "https://ng.usembassy.gov/visas/",
        "title": "US Mission Nigeria - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Nigeria",
    },
    {
        "url": "https://br.usembassy.gov/visas/",
        "title": "US Embassy Brazil - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Brazil",
    },
    {
        "url": "https://kr.usembassy.gov/visas/",
        "title": "US Embassy South Korea - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "South Korea",
    },
    {
        "url": "https://tr.usembassy.gov/visas/",
        "title": "US Embassy Turkey - Visas",
        "agency": "US Embassy",
        "visa_type": ["F-1", "J-1", "M-1"],
        "origin_country": "Turkey",
    },
]

SOURCE_URLS = SOURCE_URLS + ORIGIN_COUNTRY_SOURCE_URLS


# -------------------------------------------------------
# Curl client (persistent session, Cloudflare bypass)
# -------------------------------------------------------

_client = None


def get_client():
    """Get or create a persistent curl_cffi client."""
    global _client
    if _client is None:
        _client = curl_cffi.requests.Session(
            impersonate="chrome",
            timeout=30,
            verify=True,
        )
    return _client


# -------------------------------------------------------
# Fetching and parsing
# -------------------------------------------------------

def fetch_page(url):
    """Fetch a webpage and return cleaned text, handling Cloudflare protection."""
    client = get_client()

    for attempt in range(1, RETRY_COUNT + 1):
        try:
            print(f"  Attempt {attempt}/{RETRY_COUNT}...")
            response = client.get(url)

            if response.status_code >= 500:
                print(f"  Server error {response.status_code}, retrying...")
                time.sleep(RETRY_DELAY * attempt)
                continue

            response.raise_for_status()

            if url.endswith(".pdf"):
                return parse_pdf(response.content)

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove noise
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
                tag.decompose()

            # Try to find main content area for cleaner extraction
            main = soup.find("main") or soup.find("article") or soup.find("body")
            if not main:
                main = soup

            text = main.get_text(separator="\n", strip=True)

            # Clean up whitespace
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            text = "\n".join(lines)

            if len(text) < 100:
                print(f"  Warning: very short content ({len(text)} chars), might be blocked")
                return None

            return text

        except Exception as e:
            print(f"  Error: {e}")
            if attempt < RETRY_COUNT:
                time.sleep(RETRY_DELAY * attempt)

    print(f"  [FAILED] All {RETRY_COUNT} attempts failed for {url}")
    return None


def parse_pdf(pdf_bytes):
    """Parse a PDF and extract text."""
    import io
    try:
        text_parts = []
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)

        text = "\n".join(text_parts)
        # Clean up
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)
    except Exception as e:
        print(f"  PDF parse error: {e}")
        return None


# -------------------------------------------------------
# Chunking and storage
# -------------------------------------------------------

def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks."""
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap

    return chunks


def content_hash(text):
    """Hash content to detect changes."""
    return hashlib.md5(text.encode()).hexdigest()


def load_cache():
    """Load ingest cache (hashes of previously fetched pages)."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return json.load(f)
    return {}


def save_cache(cache):
    """Save ingest cache."""
    with open(CACHE_FILE, "w") as f:
        json.dump(cache, f, indent=2)


def store_in_chroma(chunks, metadata_template, overwrite=True):
    """Store chunks in ChromaDB with metadata."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    # If overwriting, remove old chunks for this URL
    if overwrite:
        prefix = f"{metadata_template['url']}_"
        try:
            existing = collection.get(where={"source_url": metadata_template["url"]})
            if existing["ids"]:
                collection.delete(ids=existing["ids"])
        except Exception:
            pass  # No existing data

    for i, chunk in enumerate(chunks):
        doc_id = f"{metadata_template['url']}_{i}"
        meta = metadata_template.copy()
        meta["source_url"] = metadata_template["url"]  # ensure consistent key
        meta["chunk_index"] = i
        meta["section"] = f"Chunk {i + 1}"
        meta["scraped_at"] = datetime.datetime.now().isoformat()

        # Chroma metadata values must be scalar, so a chunk's visa_type list
        # (e.g. ["F-1", "J-1"]) becomes per-type boolean flags for real
        # where-filtering in shared/retrieval.py, instead of the old approach
        # of just concatenating visa_type into the query text.
        visa_types = [v.lower() for v in meta.pop("visa_type", [])]
        for vt in ("f-1", "j-1", "m-1", "h-1b"):
            meta[f"is_{vt.replace('-', '')}"] = vt in visa_types
        meta.setdefault("country", "US")  # destination-side content is about entering the US
        meta.setdefault("origin_country", "")  # set for content specific to a country of origin

        # upsert
        collection.upsert(
            ids=[doc_id],
            documents=[chunk],
            metadatas=[meta],
        )


# -------------------------------------------------------
# Main pipeline
# -------------------------------------------------------

def run_ingestion(fast=False):
    """
    Run the full ingestion pipeline.

    Args:
        fast: If True, only re-fetch pages whose content has changed.
    """
    print("=" * 60)
    print("US Student Visa Information Resource - Document Ingestion")
    print("=" * 60)

    print(f"\nLoading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Set up ChromaDB
    print(f"ChromaDB path: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' ready. Current count: {collection.count()}\n")

    # Load cache
    cache = load_cache() if fast else {}

    total_chunks = 0
    skipped = 0
    errors = 0

    for source in SOURCE_URLS:
        url = source["url"]
        print(f"Fetching: {source['title']}")
        print(f"  URL: {url}")

        # Whether a page's content has changed can only be known after
        # fetching it (no ETag/HEAD support here), so --fast still fetches
        # every page — it skips the (comparatively expensive) chunk + embed +
        # ChromaDB store step when the content hash matches last run. A URL
        # new to the cache (e.g. one just added to SOURCE_URLS) always falls
        # through and gets stored, same as a full run.
        text = fetch_page(url)
        if not text:
            print("  No content retrieved. Skipping.\n")
            errors += 1
            continue

        h = content_hash(text)
        if fast and cache.get(url) and cache[url]["hash"] == h:
            print(f"  [SKIP] Content unchanged\n")
            skipped += 1
            continue

        chunks = chunk_text(text)
        print(f"  Text length: {len(text)} chars")
        print(f"  Chunks created: {len(chunks)}")

        store_in_chroma(chunks, source, overwrite=True)
        total_chunks += len(chunks)

        # Update cache
        cache[url] = {
            "hash": h,
            "scraped_at": datetime.datetime.now().isoformat(),
            "chunk_count": len(chunks),
        }
        print(f"  Stored in ChromaDB.\n")

    save_cache(cache)

    print("=" * 60)
    print(f"Ingestion complete.")
    print(f"  New chunks stored: {total_chunks}")
    print(f"  Skipped (unchanged): {skipped}")
    print(f"  Errors: {errors}")
    print(f"  ChromaDB collection size: {collection.count()}")
    print("=" * 60)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest government visa content")
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Only re-fetch pages whose content has changed",
    )
    args = parser.parse_args()
    run_ingestion(fast=args.fast)
