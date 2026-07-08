"""
RAG retrieval module.

Queries ChromaDB for relevant context chunks and returns
concatenated context string with source metadata for citation.
"""

import os
from typing import Optional

CHROMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "chroma_db")
COLLECTION_NAME = "student_visa_documents"


def retrieve_context(query, top_k=5, visa_type=None, distance_threshold=1.2):
    """
    Query ChromaDB for relevant context chunks.

    Args:
        query: User's question string.
        top_k: Number of chunks to retrieve.
        visa_type: Optional visa type filter (e.g., "F-1", "J-1", "M-1").
        distance_threshold: Maximum cosine distance to accept.

    Returns:
        dict: {
            "context": str - concatenated context text,
            "sources": list[dict] - source metadata with URLs,
            "distances": list[float] - cosine distances,
            "found": bool - whether any results were found
        }
    """
    try:
        import chromadb

        client = chromadb.PersistentClient(path=CHROMA_PATH)
        collection = client.get_or_create_collection(name=COLLECTION_NAME)

        # If visa_type is specified, include it in the query for better filtering
        search_query = f"{query} {visa_type}" if visa_type else query

        results = collection.query(
            query_texts=[search_query],
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

        # Build context string
        context_parts = []
        for i, doc in enumerate(filtered_docs):
            meta = filtered_metadata[i] or {}
            source_label = meta.get("source_url", "Unknown source")
            section = meta.get("section", "")
            context_parts.append(f"[Source: {source_label} | Section: {section}]\n{doc}")

        context = "\n\n---\n\n".join(context_parts)

        # Build sources list
        sources = []
        seen_urls = set()
        for meta in filtered_metadata:
            if meta and meta.get("source_url"):
                url = meta["source_url"]
                if url not in seen_urls:
                    sources.append({
                        "url": url,
                        "title": meta.get("title", "Official Source"),
                        "agency": meta.get("agency", "USCIS"),
                        "section": meta.get("section", ""),
                    })
                    seen_urls.add(url)

        return {
            "context": context if context else "",
            "sources": sources,
            "distances": filtered_distances,
            "found": len(filtered_docs) > 0,
        }

    except Exception as e:
        # If ChromaDB is not set up yet, return empty
        return {
            "context": "",
            "sources": [],
            "distances": [],
            "found": False,
            "error": str(e),
        }
