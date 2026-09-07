"""Implementation of the `search_knowledge` tool.

Keyword scoring over the in-memory dataset. Deliberately dependency free so the
server runs with nothing but FastMCP installed; replace the body of
`search_knowledge` with a vector search call when a real index exists, keeping
the same return shape.
"""

from __future__ import annotations

import re
from typing import Any

from .knowledge_base import all_documents

# Words that add noise to a keyword match rather than signal.
_STOPWORDS = frozenset(
    """
    a an and are as at be by do does for from how in into is it its of on or
    our that the their there these this to was we what when where which who
    why will with you your
    """.split()
)

_TOKEN_RE = re.compile(r"[a-z0-9]+")

# Suffixes stripped to a common stem, longest first, so that "escalate" and
# "escalation" or "rotate" and "rotation" are treated as the same term.
_SUFFIXES = (
    "izations", "ization", "ational", "ations", "ements", "ation", "ement",
    "ments", "ment",
    "ingly", "ives", "ions", "ing", "ion", "ies", "ive", "ied", "ers", "est",
    "ate", "ers", "er", "ed", "es", "al", "ly", "s", "y", "e",
)
_MIN_STEM = 3

# Relative weight of a match, by field.
_TITLE_WEIGHT = 3.0
_TAG_WEIGHT = 2.0
_BODY_WEIGHT = 1.0

MAX_TOP_K = 25
_SNIPPET_RADIUS = 160


def _stem(word: str) -> str:
    """Strip one common suffix, provided enough of the word survives."""
    for suffix in _SUFFIXES:
        if word.endswith(suffix):
            trimmed = word[: -len(suffix)]
            if len(trimmed) >= _MIN_STEM:
                return trimmed
    return word


def _tokenize(text: str) -> list[str]:
    """Lowercase a string, drop stopwords, and reduce each word to its stem."""
    return [
        _stem(token)
        for token in _TOKEN_RE.findall(text.lower())
        if token not in _STOPWORDS
    ]


def _query_terms(query: str) -> list[tuple[str, str]]:
    """Return (original word, stem) pairs for a query, preserving order."""
    seen: set[str] = set()
    terms: list[tuple[str, str]] = []
    for token in _TOKEN_RE.findall(query.lower()):
        if token in _STOPWORDS:
            continue
        stem = _stem(token)
        if stem in seen:
            continue
        seen.add(stem)
        terms.append((token, stem))
    return terms


def _matches(token: str, stem: str) -> bool:
    """True if a document stem and a query stem refer to the same word.

    Exact match always counts. Prefix matching is allowed only once the shorter
    stem is long enough to be distinctive, which keeps three-letter stems from
    sweeping up unrelated words.
    """
    if token == stem:
        return True
    if min(len(token), len(stem)) < 4:
        return False
    return token.startswith(stem) or stem.startswith(token)


def _count_matches(tokens: list[str], stem: str) -> int:
    """Count document stems that refer to the same word as the query stem."""
    return sum(1 for t in tokens if _matches(t, stem))


def _build_snippet(content: str, stems: list[str]) -> str:
    """Return a window of `content` centred on the earliest matching stem."""
    lowered = content.lower()
    position = -1
    for stem in stems:
        found = lowered.find(stem)
        if found != -1 and (position == -1 or found < position):
            position = found

    if position == -1:
        snippet = content[: _SNIPPET_RADIUS * 2].strip()
        return snippet.replace("\n\n", " ") + ("..." if len(content) > _SNIPPET_RADIUS * 2 else "")

    start = max(0, position - _SNIPPET_RADIUS)
    end = min(len(content), position + _SNIPPET_RADIUS)

    # Avoid clipping mid-word at either edge.
    if start > 0:
        start = content.find(" ", start) + 1
    if end < len(content):
        end = content.rfind(" ", start, end)

    snippet = content[start:end].strip().replace("\n\n", " ")
    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(content) else ""
    return f"{prefix}{snippet}{suffix}"


def _score_document(
    doc: dict[str, Any], terms: list[tuple[str, str]]
) -> tuple[float, list[str], list[str]]:
    """Score one document against the query.

    Returns the score, the original words that matched, and their stems.
    """
    title_tokens = _tokenize(doc["title"])
    tag_tokens = _tokenize(" ".join(doc["tags"]))
    body_tokens = _tokenize(doc["content"])

    score = 0.0
    matched: list[str] = []
    matched_stems: list[str] = []

    for word, stem in terms:
        title_hits = _count_matches(title_tokens, stem)
        tag_hits = _count_matches(tag_tokens, stem)
        body_hits = _count_matches(body_tokens, stem)

        if not (title_hits or tag_hits or body_hits):
            continue

        matched.append(word)
        matched_stems.append(stem)
        score += title_hits * _TITLE_WEIGHT
        score += tag_hits * _TAG_WEIGHT
        # Diminishing returns on repeated body hits, so that long documents do
        # not rank highly purely by being long.
        score += min(body_hits, 5) * _BODY_WEIGHT

    # Reward documents covering more of the query, not just one term loudly.
    if terms:
        score *= 1.0 + (len(matched) / len(terms))

    return round(score, 3), matched, matched_stems


def search_knowledge(query: str, top_k: int = 5) -> dict[str, Any]:
    """Rank knowledge base documents against a free-text query."""
    query = (query or "").strip()
    if not query:
        return {
            "query": query,
            "count": 0,
            "results": [],
            "note": "Empty query. Provide search terms.",
        }

    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        top_k = 5
    top_k = max(1, min(top_k, MAX_TOP_K))

    terms = _query_terms(query)
    if not terms:
        return {
            "query": query,
            "count": 0,
            "results": [],
            "note": "Query contained only stopwords.",
        }

    scored: list[dict[str, Any]] = []
    for doc in all_documents():
        score, matched, matched_stems = _score_document(doc, terms)
        if score <= 0:
            continue
        scored.append(
            {
                "document_id": doc["id"],
                "title": doc["title"],
                "source": doc["source"],
                "tags": doc["tags"],
                "updated": doc["updated"],
                "domain": doc.get("domain"),
                "authority": doc.get("authority"),
                "score": score,
                "matched_terms": matched,
                "snippet": _build_snippet(doc["content"], matched_stems),
            }
        )

    scored.sort(key=lambda r: (-r["score"], r["document_id"]))
    results = scored[:top_k]

    payload: dict[str, Any] = {
        "query": query,
        "count": len(results),
        "results": results,
    }
    if not results:
        payload["note"] = "No documents matched. Try broader or different terms."
    return payload