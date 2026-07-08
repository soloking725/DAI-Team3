"""
Document ingestion pipeline.

Scrapes USCIS, State Dept, SSA, and IRS pages.
Splits into chunks. Stores in ChromaDB with metadata for citation.

Usage:
    python ingest.py
"""

import os
import hashlib
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
import chromadb

# -------------------------------------------------------
# Configuration
# -------------------------------------------------------

CHROMA_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")
COLLECTION_NAME = "visa_documents"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Official government URLs to scrape
SOURCE_URLS = [
    {
        "url": "https://www.uscis.gov/i-129",
        "title": "USCIS Form I-129 Instructions",
        "agency": "USCIS",
        "visa_type": ["I-129", "H-1B"],
    },
    {
        "url": "https://www.uscis.gov/i-485",
        "title": "USCIS Form I-485 Instructions",
        "agency": "USCIS",
        "visa_type": ["I-485"],
    },
    {
        "url": "https://www.uscis.gov/h-1b",
        "title": "USCIS H-1B Visa Information",
        "agency": "USCIS",
        "visa_type": ["H-1B"],
    },
    {
        "url": "https://www.uscis.gov/sites/default/files/document/fee_index/USCIS%20Fee%20Index%20-%20English.pdf",
        "title": "USCIS Fee Index",
        "agency": "USCIS",
        "visa_type": ["all"],
    },
    {
        "url": "https://travel.state.gov/content/travel/en/us-visas.html",
        "title": "State Department US Visas",
        "agency": "State Department",
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


def fetch_page(url):
    """Fetch a webpage and return cleaned text."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; VisaInfoBot/1.0)"
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        if url.endswith(".pdf"):
            # Placeholder for PDF parsing
            print(f"  [SKIP] PDF not yet implemented: {url}")
            return None

        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        return "\n".join(lines)

    except Exception as e:
        print(f"  [ERROR] Failed to fetch {url}: {e}")
        return None


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


def store_in_chroma(chunks, metadata_template):
    """Store chunks in ChromaDB with metadata."""
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)

    for i, chunk in enumerate(chunks):
        doc_id = f"{metadata_template['url']}_{i}"
        meta = metadata_template.copy()
        meta["chunk_index"] = i
        meta["section"] = f"Chunk {i + 1}"

        collection.add(
            ids=[doc_id],
            documents=[chunk],
            metadatas=[meta],
        )


def run_ingestion():
    """Run the full ingestion pipeline."""
    print("=" * 60)
    print("US Visa Information Resource - Document Ingestion")
    print("=" * 60)

    print(f"\nLoading embedding model: {EMBEDDING_MODEL}...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Set up ChromaDB
    print(f"ChromaDB path: {CHROMA_PATH}")
    client = chromadb.PersistentClient(path=CHROMA_PATH)
    collection = client.get_or_create_collection(name=COLLECTION_NAME)
    print(f"Collection '{COLLECTION_NAME}' ready. Current count: {collection.count()}\n")

    total_chunks = 0

    for source in SOURCE_URLS:
        url = source["url"]
        print(f"Fetching: {source['title']}")
        print(f"  URL: {url}")

        text = fetch_page(url)
        if not text:
            print("  No content retrieved. Skipping.\n")
            continue

        chunks = chunk_text(text)
        print(f"  Text length: {len(text)} chars")
        print(f"  Chunks created: {len(chunks)}")

        store_in_chroma(chunks, source)
        total_chunks += len(chunks)
        print(f"  Stored in ChromaDB.\n")

    print("=" * 60)
    print(f"Ingestion complete. Total chunks stored: {total_chunks}")
    print(f"ChromaDB collection size: {collection.count()}")
    print("=" * 60)


if __name__ == "__main__":
    run_ingestion()
