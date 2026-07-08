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
SOURCE_URLS = [
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/apply-for-a-student-visa.html",
        "title": "State Department - F-1 Student Visa Application",
        "agency": "State Department",
        "visa_type": ["F-1"],
    },
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/other-study-options/vocational-students.html",
        "title": "State Department - M-1 Vocational Student Visa",
        "agency": "State Department",
        "visa_type": ["M-1"],
    },
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas/study/exchange-visitor.html",
        "title": "State Department - J-1 Exchange Visitor Program",
        "agency": "State Department",
        "visa_type": ["J-1"],
    },
    {
        "url": "https://www.uscis.gov/international-students-academics",
        "title": "USCIS - International Students and Academics",
        "agency": "USCIS",
        "visa_type": ["F-1", "J-1", "M-1"],
    },
    {
        "url": "https://www.uscis.gov/j-exchange-visitor",
        "title": "USCIS - J Exchange Visitor",
        "agency": "USCIS",
        "visa_type": ["J-1"],
    },
    {
        "url": "https://www.uscis.gov/m-vocational-student",
        "title": "USCIS - M Vocational Student",
        "agency": "USCIS",
        "visa_type": ["M-1"],
    },
    {
        "url": "https://studyinthestates.dhs.gov/f-students",
        "title": "SEVP - F-1 Student Regulations",
        "agency": "SEVP",
        "visa_type": ["F-1"],
    },
    {
        "url": "https://studyinthestates.dhs.gov/m-students",
        "title": "SEVP - M-1 Student Regulations",
        "agency": "SEVP",
        "visa_type": ["M-1"],
    },
    {
        "url": "https://www.uscis.gov/sites/default/files/document/fee_index/USCIS%20Fee%20Index%20-%20English.pdf",
        "title": "USCIS Fee Index",
        "agency": "USCIS",
        "visa_type": ["all"],
    },
    {
        "url": "https://www.ssa.gov/foreign/immigrant/apply.html",
        "title": "SSA - Applying for SSN as an Immigrant",
        "agency": "SSA",
        "visa_type": ["post-visa"],
    },
    {
        "url": "https://www.irs.gov/individuals/international-taxes/nonresident-alien-individuals",
        "title": "IRS - Nonresident Alien Tax Information",
        "agency": "IRS",
        "visa_type": ["post-visa"],
    },
]


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

        # Fast mode: skip unchanged
        if fast:
            h = content_hash(url)
            if cache.get(url) and cache[url]["hash"] == h:
                print(f"  [SKIP] Content unchanged\n")
                skipped += 1
                continue

        text = fetch_page(url)
        if not text:
            print("  No content retrieved. Skipping.\n")
            errors += 1
            continue

        chunks = chunk_text(text)
        print(f"  Text length: {len(text)} chars")
        print(f"  Chunks created: {len(chunks)}")

        store_in_chroma(chunks, source, overwrite=True)
        total_chunks += len(chunks)

        # Update cache
        cache[url] = {
            "hash": content_hash(text),
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
