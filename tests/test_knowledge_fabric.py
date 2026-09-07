"""Tests for the Knowledge Fabric mock retrieval mechanism.

Exercises `search_knowledge` and `get_context` directly against the in-memory
`DOCUMENTS` store (no MCP transport / fastmcp needed), including the
`sample-pwdreset-*` MOCK documents added to test the Requirements Refinement
(BA/QA) flow before a real Knowledge Fabric is available.

Run with pytest:
    pytest tests/test_knowledge_fabric.py -v

Or standalone (no pytest required):
    python tests/test_knowledge_fabric.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "mcp-servers" / "knowledge-fabric"))

from tools.get_context import DocumentNotFound, get_context  # noqa: E402
from tools.knowledge_base import known_ids  # noqa: E402
from tools.search_knowledge import search_knowledge  # noqa: E402

PWDRESET_IDS = [
    "sample-pwdreset-001",
    "sample-pwdreset-002",
    "sample-pwdreset-003",
    "sample-pwdreset-004",
    "sample-pwdreset-005",
]


def test_sample_pwdreset_documents_are_registered():
    ids = known_ids()
    for doc_id in PWDRESET_IDS:
        assert doc_id in ids, f"expected sample document {doc_id} in knowledge base"


def test_search_finds_password_reset_documents():
    result = search_knowledge(query="password reset", top_k=10)
    found_ids = {r["document_id"] for r in result["results"]}
    for doc_id in PWDRESET_IDS:
        assert doc_id in found_ids, f"search_knowledge missed {doc_id}"


def test_search_results_expose_authority_and_domain():
    result = search_knowledge(query="password reset business rules", top_k=10)
    rules_doc = next(
        r for r in result["results"] if r["document_id"] == "sample-pwdreset-002"
    )
    assert rules_doc["authority"] is not None
    assert rules_doc["domain"] is not None
    assert "sample-data" in rules_doc["tags"]


def test_get_context_returns_full_content_and_metadata():
    ctx = get_context(document_id="sample-pwdreset-001")
    assert ctx["document_id"] == "sample-pwdreset-001"
    assert "SAMPLE" in ctx["content"].upper()
    assert ctx["authority"] == "Approved - Current (Product/BA sign-off)"
    assert ctx["domain"] is not None
    assert ctx["version"] == "v2.3"
    assert ctx["word_count"] > 0


def test_get_context_surfaces_related_pwdreset_documents():
    ctx = get_context(document_id="sample-pwdreset-001")
    related_ids = {r["document_id"] for r in ctx["related"]}
    # At least one other sample password-reset document should be related
    # via shared tags (e.g. "password-reset", "account-recovery").
    assert related_ids & set(PWDRESET_IDS[1:])


def test_get_context_unknown_id_raises():
    try:
        get_context(document_id="does-not-exist")
    except DocumentNotFound:
        pass
    else:
        raise AssertionError("expected DocumentNotFound for an unknown id")


def test_legacy_and_current_policy_are_both_retrievable_for_conflict_check():
    """Sanity check for conflict-detection testing: the legacy implementation
    (deprecated) and the current IAM policy (approved) must both be
    retrievable so the BA/QA agent can compare them and report a conflict."""
    legacy = get_context(document_id="sample-pwdreset-005")
    current_policy = get_context(document_id="sample-pwdreset-003")
    assert "Deprecated" in legacy["authority"]
    assert "Approved" in current_policy["authority"]


if __name__ == "__main__":
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_")]
    failures = 0
    for test in tests:
        try:
            test()
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"FAIL: {test.__name__}: {exc}")
        else:
            print(f"PASS: {test.__name__}")
    print(f"\n{len(tests) - failures}/{len(tests)} passed")
    sys.exit(1 if failures else 0)
