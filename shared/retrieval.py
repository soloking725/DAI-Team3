"""
RAG retrieval module.

Queries ChromaDB for relevant context chunks and returns
concatenated context string with source metadata for citation.
"""

import logging
from typing import Optional

import chromadb

from shared.config import (
    CHROMA_PATH,
    COLLECTION_NAME,
    DEFAULT_TOP_K,
    DISTANCE_THRESHOLD,
)

logger = logging.getLogger(__name__)

# Module-level cached client — created once, reused across all calls
_chroma_client = None
_chroma_collection = None


def _get_collection():
    """Lazily initialize and return the ChromaDB collection (cached)."""
    global _chroma_client, _chroma_collection
    if _chroma_collection is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
        _chroma_collection = _chroma_client.get_or_create_collection(name=COLLECTION_NAME)
    return _chroma_collection


def retrieve_context(
    query: str,
    top_k: int = DEFAULT_TOP_K,
    visa_type: Optional[str] = None,
    distance_threshold: float = DISTANCE_THRESHOLD,
    origin_country: Optional[str] = None,
    category: Optional[str] = None,
) -> dict:
    """
    Query ChromaDB for relevant context chunks.

    Args:
        query: User's question string.
        top_k: Number of chunks to retrieve.
        visa_type: Optional visa type filter (e.g., "F-1", "J-1", "M-1"). Applied as
            a real Chroma `where` filter against the per-type `is_f1`/`is_j1`/`is_m1`/
            `is_h1b` boolean flags set at ingestion time (see ingest.py/ingest_static.py),
            not just appended to the query text.
        distance_threshold: Maximum cosine distance to accept.
        origin_country: Optional country-of-origin filter (e.g. "India") for chunks
            tagged with that `origin_country` at ingestion time — falls back to
            unfiltered results if no country-specific content matches.
        category: Optional content-category filter (e.g. "interview_prep",
            "extenuating_circumstances") for chunks tagged with that `category`
            at ingestion time.

    Returns:
        dict with keys:
            - context (str): Concatenated context text.
            - sources (list[dict]): Source metadata with URLs.
            - distances (list[float]): Cosine distances.
            - found (bool): Whether any results were found.
            - error (str, optional): Error message if retrieval failed.
    """
    try:
        collection = _get_collection()

        conditions = []
        if visa_type:
            flag = f"is_{visa_type.lower().replace('-', '')}"
            conditions.append({flag: True})
        if origin_country:
            conditions.append({"origin_country": origin_country})
        if category:
            conditions.append({"category": category})

        if len(conditions) > 1:
            where = {"$and": conditions}
        elif conditions:
            where = conditions[0]
        else:
            where = None

        results = collection.query(
            query_texts=[query],
            n_results=top_k,
            where=where,
            include=["documents", "distances", "metadatas"],
        )

        # A visa_type filter can legitimately return nothing (e.g. content that
        # predates the flag, or a visa type with no dedicated content yet) —
        # fall back to an unfiltered query rather than surfacing a false "not found".
        if where and not (results.get("documents") and results["documents"][0]):
            results = collection.query(
                query_texts=[query],
                n_results=top_k,
                include=["documents", "distances", "metadatas"],
            )

        distances = results["distances"][0] if results["distances"] else []
        documents = results["documents"][0] if results["documents"] else []
        metadatas = results["metadatas"][0] if results["metadatas"] else []

        # Filter by distance threshold
        filtered_docs = []
        filtered_distances = []
        filtered_metadata = []

        for i, dist in enumerate(distances):
            if dist < distance_threshold:
                filtered_docs.append(documents[i])
                filtered_distances.append(dist)
                filtered_metadata.append(metadatas[i])

        logger.info(
            "Retrieved %d chunks (threshold %.2f) for query: %s",
            len(filtered_docs),
            distance_threshold,
            query[:60],
        )

        # Build context string
        context_parts = []
        for i, doc in enumerate(filtered_docs):
            meta = filtered_metadata[i] or {}
            source_label = meta.get("source_url", "Unknown source")
            section = meta.get("section", "")
            context_parts.append(
                f"[Source: {source_label} | Section: {section}]\n{doc}"
            )

        context = "\n\n---\n\n".join(context_parts)

        # Build sources list
        sources = []
        seen_urls: set[str] = set()
        for meta in filtered_metadata:
            if meta and meta.get("source_url"):
                url = meta["source_url"]
                if url not in seen_urls:
                    sources.append(
                        {
                            "url": url,
                            "title": meta.get("title", "Official Source"),
                            "agency": meta.get("agency", "USCIS"),
                            "section": meta.get("section", ""),
                        }
                    )
                    seen_urls.add(url)

        return {
            "context": context if context else "",
            "sources": sources,
            "distances": filtered_distances,
            "found": len(filtered_docs) > 0,
        }

    except Exception as e:
        logger.error("ChromaDB retrieval failed: %s", e, exc_info=True)
        return {
            "context": "",
            "sources": [],
            "distances": [],
            "found": False,
            "error": str(e),
        }
