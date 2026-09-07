"""Implementation of the `get_context` tool.

Fetches one full document by id and the handful of documents most closely
related to it, so a caller that found a hit via `search_knowledge` can pull
complete grounding material in a single follow-up call.
"""

from __future__ import annotations

from typing import Any

from .knowledge_base import all_documents, get_document, known_ids

_MAX_RELATED = 3


class DocumentNotFound(LookupError):
    """Raised when the requested document id is not in the knowledge base."""


def _related_documents(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Find documents sharing the most tags with `doc`."""
    tags = set(doc["tags"])
    candidates: list[tuple[int, dict[str, Any]]] = []

    for other in all_documents():
        if other["id"] == doc["id"]:
            continue
        shared = tags & set(other["tags"])
        if shared:
            candidates.append((len(shared), other))

    candidates.sort(key=lambda pair: (-pair[0], pair[1]["id"]))

    return [
        {
            "document_id": other["id"],
            "title": other["title"],
            "shared_tags": sorted(tags & set(other["tags"])),
        }
        for _, other in candidates[:_MAX_RELATED]
    ]


def get_context(document_id: str) -> dict[str, Any]:
    """Return the full content and metadata for a single document."""
    document_id = (document_id or "").strip()
    doc = get_document(document_id)

    if doc is None:
        raise DocumentNotFound(
            f"No document with id {document_id!r}. "
            f"Known ids: {', '.join(known_ids())}. "
            "Use search_knowledge to find a valid document_id."
        )

    content = doc["content"]

    return {
        "document_id": doc["id"],
        "title": doc["title"],
        "source": doc["source"],
        "tags": doc["tags"],
        "updated": doc["updated"],
        "domain": doc.get("domain"),
        "authority": doc.get("authority"),
        "version": doc.get("version"),
        "word_count": len(content.split()),
        "content": content,
        "related": _related_documents(doc),
    }