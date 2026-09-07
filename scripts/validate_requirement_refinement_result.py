#!/usr/bin/env python3
"""Deterministic validator for RequirementRefinementResult documents.

schemas/requirement_refinement_result.schema.json defines the shape of the
contract (types, enums, required fields, and the structural conditionals a
plain JSON Schema can express). This module checks everything a static
shape cannot: cross-references between fields, evidence-registry integrity,
and the platform's non-negotiable Requirements Refinement rules — chiefly
that nothing may claim "confirmed" without a resolvable, appropriately
sourced evidence reference. No new dependency is introduced: this uses only
the Python standard library, so a project that has never installed a JSON
Schema validator can still run these checks.

This module implements validation only. It does not read or write anything
under output/, does not call scripts/save_agent_output.py, and does not
implement persistence in any form — that remains a separate, later task.

Usage:
    python scripts/validate_requirement_refinement_result.py <path-to-result.json>

Exits 0 with no output if the document is valid, or exits 1 and prints one
violation per line otherwise. Importable as a library via `validate(payload)`.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any

RUN_ID_RE = re.compile(r"^run-[A-Za-z0-9_-]+$")

# Evidence source types that may back a "confirmed" claim, business rule, or
# acceptance criterion. Deliberately excludes repo_file, jira_search_result,
# and additional_context — the requirement-analysis skill's label set has no
# "Confirmed – Repo" / "Confirmed – Additional Context" / "Confirmed – Jira
# Search" label, so evidence of those types can inform or corroborate but can
# never, by itself, promote a claim to confirmed.
CONFIRMABLE_SOURCE_TYPES = {
    "jira_requirement_field",
    "free_text_requirement",
    "supplied_acceptance_criteria",
}

JIRA_INPUT_SHAPES = {"jira_issue_key", "jira_story_supplied"}

GAP_TYPES = {"business_requirement", "security", "functional", "testability", "traceability"}


class Violation(str):
    """A human-readable validation failure. Plain str subclass for typing clarity."""


def _get(d: dict, path: str, default=None):
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def _is_confirmable_evidence(ev: dict) -> bool:
    if ev.get("source_type") in CONFIRMABLE_SOURCE_TYPES:
        return True
    if ev.get("source_type") == "knowledge_fabric" and ev.get("tier") == "directly_applicable":
        return True
    return False


def _check_evidence_registry(evidence: list[dict], violations: list[str]) -> dict[str, dict]:
    by_id: dict[str, dict] = {}
    seen_ids: set[str] = set()
    for ev in evidence:
        eid = ev.get("id")
        if eid in seen_ids:
            violations.append(f"evidence: duplicate id {eid!r}")
        seen_ids.add(eid)
        by_id[eid] = ev

        source_type = ev.get("source_type")
        tier = ev.get("tier")
        if source_type == "knowledge_fabric" and tier is None:
            violations.append(f"evidence[{eid}]: source_type is knowledge_fabric but tier is null")
        if source_type != "knowledge_fabric" and tier is not None:
            violations.append(f"evidence[{eid}]: tier set ({tier!r}) but source_type is {source_type!r}, not knowledge_fabric")
        if not (ev.get("excerpt") or "").strip():
            violations.append(f"evidence[{eid}]: excerpt is empty — a citation with no retrieved text is not grounding")

        retrieved_via = ev.get("retrieved_via")
        expects_supplied = source_type in {"free_text_requirement", "supplied_acceptance_criteria", "additional_context"}
        if expects_supplied and retrieved_via != "user_supplied":
            violations.append(
                f"evidence[{eid}]: source_type {source_type!r} should have retrieved_via 'user_supplied', got {retrieved_via!r}"
            )
    return by_id


def _check_evidence_refs(label: str, ids: list[str], by_id: dict[str, dict], violations: list[str]) -> None:
    for eid in ids or []:
        if eid not in by_id:
            violations.append(f"{label}: references unknown evidence id {eid!r} — evidence claimed but never captured in the registry")


def _check_claim(label: str, claim: dict, by_id: dict[str, dict], violations: list[str], allow_empty_evidence_ok: bool = False) -> None:
    if not claim:
        return
    basis = claim.get("basis")
    evidence_ids = claim.get("evidence_ids") or []
    _check_evidence_refs(f"{label}.evidence_ids", evidence_ids, by_id, violations)

    if basis == "confirmed":
        if not evidence_ids:
            violations.append(f"{label}: basis is 'confirmed' but evidence_ids is empty")
        elif not any(_is_confirmable_evidence(by_id[eid]) for eid in evidence_ids if eid in by_id):
            violations.append(
                f"{label}: basis is 'confirmed' but none of its evidence is a confirmable source type "
                f"(requirement text, supplied AC, or Directly-applicable Knowledge Fabric) — "
                f"an unsupported claim must not be labeled confirmed"
            )
    else:
        if evidence_ids:
            violations.append(f"{label}: basis is {basis!r} but evidence_ids is non-empty — non-confirmed claims cannot carry confirming evidence")
        if not (claim.get("rationale") or "").strip():
            violations.append(f"{label}: basis is {basis!r} but rationale is missing")


def _check_acceptance_criterion(ac: dict, by_id: dict[str, dict], cq_ids: set[str], violations: list[str]) -> None:
    label = f"acceptance_criteria[{ac.get('id')}]"
    status = ac.get("status")
    evidence_ids = ac.get("evidence_ids") or []
    blocking_ids = ac.get("blocking_clarification_question_ids") or []
    _check_evidence_refs(f"{label}.evidence_ids", evidence_ids, by_id, violations)

    if status == "confirmed":
        if not evidence_ids:
            violations.append(f"{label}: status is 'confirmed' but evidence_ids is empty")
        elif not any(_is_confirmable_evidence(by_id[eid]) for eid in evidence_ids if eid in by_id):
            violations.append(f"{label}: status is 'confirmed' but no confirmable evidence backs it")
        if blocking_ids:
            violations.append(f"{label}: status is 'confirmed' but blocking_clarification_question_ids is non-empty")
    elif status == "blocked_by_clarification":
        if not blocking_ids:
            violations.append(f"{label}: status is 'blocked_by_clarification' but blocking_clarification_question_ids is empty")
        for cid in blocking_ids:
            if cid not in cq_ids:
                violations.append(f"{label}: blocking_clarification_question_ids references unknown question id {cid!r}")
    elif status == "proposed":
        if blocking_ids:
            violations.append(f"{label}: status is 'proposed' but blocking_clarification_question_ids is non-empty")
    else:
        violations.append(f"{label}: unrecognized status {status!r}")


def _check_conditional_list(label: str, node: dict, violations: list[str]) -> None:
    if node is None:
        return
    applicable = node.get("applicable")
    entries = node.get("entries") or []
    reason = node.get("reason_if_not_applicable")
    if applicable is False:
        if entries:
            violations.append(f"{label}: applicable is false but entries is non-empty")
        if not (reason or "").strip():
            violations.append(f"{label}: applicable is false but reason_if_not_applicable is missing")
    if applicable is True and not entries:
        violations.append(f"{label}: applicable is true but entries is empty")


def _scan_for_forbidden_approval_keys(node: Any, path: str, violations: list[str]) -> None:
    """Defensive recursive scan: no key resembling an approval flag may be
    present anywhere in the document, and review_status.status may never be
    an approved-looking value. This exists because a hand-authored or
    hand-edited document might add a field the schema would reject but a
    non-schema-validating caller would not catch.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            lowered = key.lower()
            if "approved" in lowered or "approval" in lowered:
                violations.append(f"{path}.{key}: no approval-related field is permitted in this contract; approval happens outside it")
            _scan_for_forbidden_approval_keys(value, f"{path}.{key}", violations)
    elif isinstance(node, list):
        for i, item in enumerate(node):
            _scan_for_forbidden_approval_keys(item, f"{path}[{i}]", violations)
    elif isinstance(node, str):
        if node.strip().lower() in {"approved", "approve", "sign-off", "signed off"}:
            violations.append(f"{path}: value {node!r} reads as an approval — this contract may never assert approval")


def validate(payload: dict) -> list[str]:
    """Validate a RequirementRefinementResult payload. Returns a list of
    human-readable violation strings; an empty list means the document is
    valid. Never raises on a malformed document — missing/malformed fields
    are reported as violations, not exceptions, so a caller can always get a
    full list of problems in one pass.
    """
    violations: list[str] = []

    run_id = payload.get("run_id", "")
    if not RUN_ID_RE.match(run_id or ""):
        violations.append(f"run_id: {run_id!r} does not match the platform's run-id pattern ^run-[A-Za-z0-9_-]+$")

    evidence = payload.get("evidence") or []
    by_id = _check_evidence_registry(evidence, violations)

    # --- source / original_requirement / refined_story consistency -------
    source = payload.get("source") or {}
    input_shape = source.get("input_shape")
    original = payload.get("original_requirement") or {}
    if input_shape in JIRA_INPUT_SHAPES:
        if original.get("jira_fields") is None:
            violations.append("original_requirement.jira_fields: must be non-null when source.input_shape is a Jira shape")
        if not source.get("jira_key"):
            violations.append("source.jira_key: must be set when source.input_shape is a Jira shape")
    else:
        if original.get("jira_fields") is not None:
            violations.append("original_requirement.jira_fields: must be null for a non-Jira input_shape")
        if source.get("jira_key") is not None or source.get("jira_cloud_id") is not None:
            violations.append("source.jira_key/jira_cloud_id: must be null for a non-Jira input_shape")

    _check_evidence_refs("original_requirement.evidence_id", [original.get("evidence_id")], by_id, violations)

    refined_story = payload.get("refined_story") or {}
    expects_refined_story = input_shape in JIRA_INPUT_SHAPES
    if refined_story.get("applicable") != expects_refined_story:
        violations.append(
            f"refined_story.applicable ({refined_story.get('applicable')!r}) does not match "
            f"source.input_shape ({input_shape!r}) — expected {expects_refined_story!r}"
        )
    _check_evidence_refs(
        "refined_story.refinements_supported_by_evidence_ids",
        refined_story.get("refinements_supported_by_evidence_ids"),
        by_id,
        violations,
    )

    # --- Claim-shaped single/array fields ---------------------------------
    _check_claim("business_intent", payload.get("business_intent") or {}, by_id, violations)
    for field in ("actors", "triggers", "preconditions", "process", "expected_outcomes", "edge_cases", "business_rules"):
        for item in payload.get(field) or []:
            _check_claim(f"{field}[{item.get('id')}]", item, by_id, violations)
    for dep in payload.get("dependencies") or []:
        _check_claim(f"dependencies[{dep.get('id')}]", dep, by_id, violations)

    # --- Acceptance criteria ----------------------------------------------
    clarification_questions = payload.get("clarification_questions") or []
    cq_ids = {cq.get("id") for cq in clarification_questions}
    ac_ids_seen: set[str] = set()
    for ac in payload.get("acceptance_criteria") or []:
        aid = ac.get("id")
        if aid in ac_ids_seen:
            violations.append(f"acceptance_criteria: duplicate id {aid!r}")
        ac_ids_seen.add(aid)
        _check_acceptance_criterion(ac, by_id, cq_ids, violations)

    # --- Gaps ---------------------------------------------------------------
    for gap in payload.get("gaps") or []:
        gid = gap.get("id")
        primary = gap.get("primary_type")
        secondary = gap.get("secondary_type")
        if primary not in GAP_TYPES:
            violations.append(f"gaps[{gid}]: primary_type {primary!r} is not a recognized gap type")
        if secondary is not None:
            if secondary not in GAP_TYPES:
                violations.append(f"gaps[{gid}]: secondary_type {secondary!r} is not a recognized gap type")
            if secondary == primary:
                violations.append(f"gaps[{gid}]: secondary_type equals primary_type ({primary!r}) — a gap needs at most one *different* secondary type")
        cqid = gap.get("clarification_question_id")
        if cqid is not None and cqid not in cq_ids:
            violations.append(f"gaps[{gid}]: clarification_question_id references unknown question id {cqid!r}")

    # --- Clarification questions -------------------------------------------
    for cq in clarification_questions:
        if not (cq.get("question") or "").strip():
            violations.append(f"clarification_questions[{cq.get('id')}]: question is empty")

    # --- Conflicts: no resolution-shaped keys, evidence refs resolve -------
    forbidden_conflict_keys = {"resolution", "resolved", "resolved_by", "winner", "decision_made"}
    for conflict in payload.get("conflicts") or []:
        cid = conflict.get("id")
        extra = forbidden_conflict_keys & set(conflict.keys())
        if extra:
            violations.append(f"conflicts[{cid}]: contains forbidden resolution-shaped key(s) {sorted(extra)} — a conflict may never be recorded as resolved")
        _check_evidence_refs(f"conflicts[{cid}].requirement_statement_evidence_id", [conflict.get("requirement_statement_evidence_id")], by_id, violations)
        _check_evidence_refs(f"conflicts[{cid}].conflicting_statement_evidence_id", [conflict.get("conflicting_statement_evidence_id")], by_id, violations)

    # --- Related / duplicate requirements -----------------------------------
    _check_conditional_list("related_requirements", payload.get("related_requirements"), violations)
    _check_conditional_list("duplicate_candidates", payload.get("duplicate_candidates"), violations)
    for entry in (payload.get("duplicate_candidates") or {}).get("entries") or []:
        if not (entry.get("search_scope_limitation") or "").strip():
            violations.append(f"duplicate_candidates.entries[{entry.get('id')}]: search_scope_limitation is missing")
    rr_scope = (payload.get("related_requirements") or {}).get("search_scope_limitation")
    if not (rr_scope or "").strip():
        violations.append("related_requirements.search_scope_limitation is missing")

    # --- Existing test mapping ----------------------------------------------
    etm = payload.get("existing_test_mapping") or {}
    _check_conditional_list("existing_test_mapping", etm, violations)
    for entry in etm.get("entries") or []:
        eid = entry.get("evidence_id")
        ev = by_id.get(eid)
        if ev is None:
            violations.append(f"existing_test_mapping.entries[{entry.get('id')}]: evidence_id {eid!r} not found in evidence registry")
        elif ev.get("source_type") != "repo_file":
            violations.append(f"existing_test_mapping.entries[{entry.get('id')}]: evidence_id {eid!r} is not a repo_file evidence entry")

    # --- Traceability candidates --------------------------------------------
    for tc in payload.get("traceability_candidates") or []:
        if tc.get("status") != "candidate":
            violations.append(f"traceability_candidates[{tc.get('id')}]: status must be exactly 'candidate', got {tc.get('status')!r}")
        _check_evidence_refs(f"traceability_candidates[{tc.get('id')}].evidence_ids", tc.get("evidence_ids"), by_id, violations)

    # --- Confirmed facts ------------------------------------------------------
    for cf in payload.get("confirmed_facts") or []:
        if not cf.get("evidence_ids"):
            violations.append(f"confirmed_facts[{cf.get('id')}]: evidence_ids is empty — every confirmed fact must cite evidence")
        _check_evidence_refs(f"confirmed_facts[{cf.get('id')}].evidence_ids", cf.get("evidence_ids"), by_id, violations)

    # --- Assumptions / Recommendations / Unknowns: no confirming evidence --
    for a in payload.get("assumptions") or []:
        if "evidence_ids" in a:
            violations.append(f"assumptions[{a.get('id')}]: must not carry an 'evidence_ids' field (only 'related_evidence_ids' is allowed)")
        _check_evidence_refs(f"assumptions[{a.get('id')}].related_evidence_ids", a.get("related_evidence_ids"), by_id, violations)
    for r in payload.get("recommendations") or []:
        _check_evidence_refs(f"recommendations[{r.get('id')}].related_evidence_ids", r.get("related_evidence_ids"), by_id, violations)

    # --- Quality assessment: Requirements Critic pass -----------------------
    qa = payload.get("quality_assessment") or {}
    findings = qa.get("findings") or []
    corrections = qa.get("corrections") or []
    unresolved_items = qa.get("unresolved_items") or []
    critic_status = qa.get("critic_status")

    finding_ids = {f.get("id") for f in findings}
    seen_finding_ids: set = set()
    for f in findings:
        fid = f.get("id")
        if fid in seen_finding_ids:
            violations.append(f"quality_assessment.findings: duplicate id {fid!r}")
        seen_finding_ids.add(fid)
        cn = f.get("check_number")
        if not isinstance(cn, int) or not (1 <= cn <= 14):
            violations.append(f"quality_assessment.findings[{fid}]: check_number {cn!r} is not an integer 1-14")

    correction_finding_ids = [c.get("finding_id") for c in corrections]
    unresolved_finding_ids = [u.get("finding_id") for u in unresolved_items]

    for fid in correction_finding_ids:
        if fid not in finding_ids:
            violations.append(f"quality_assessment.corrections: references unknown finding id {fid!r}")
    for fid in unresolved_finding_ids:
        if fid not in finding_ids:
            violations.append(f"quality_assessment.unresolved_items: references unknown finding id {fid!r}")

    for f in findings:
        fid = f.get("id")
        disposition = f.get("disposition")
        in_corrections = fid in correction_finding_ids
        in_unresolved = fid in unresolved_finding_ids
        if disposition == "revise":
            if not in_corrections:
                violations.append(
                    f"quality_assessment.findings[{fid}]: disposition is 'revise' but has no matching entry in "
                    f"corrections — if it couldn't actually be fixed, its disposition should be 'unresolved'"
                )
            if in_unresolved:
                violations.append(f"quality_assessment.findings[{fid}]: disposition is 'revise' but also appears in unresolved_items")
        elif disposition in {"escalate", "unresolved"}:
            if not in_unresolved:
                violations.append(f"quality_assessment.findings[{fid}]: disposition is {disposition!r} but has no matching entry in unresolved_items")
            if in_corrections:
                violations.append(f"quality_assessment.findings[{fid}]: disposition is {disposition!r} but also appears in corrections — a finding requiring escalation cannot be self-resolved")
        else:
            violations.append(f"quality_assessment.findings[{fid}]: unrecognized disposition {disposition!r}")

    actual_escalation_required = any(f.get("disposition") == "escalate" for f in findings)
    if qa.get("escalation_required") != actual_escalation_required:
        violations.append(
            f"quality_assessment.escalation_required is {qa.get('escalation_required')!r} but "
            f"actual findings imply {actual_escalation_required!r}"
        )

    has_unresolved = any(f.get("disposition") == "unresolved" for f in findings)
    if not findings:
        expected_status = "clean"
    elif has_unresolved:
        expected_status = "unresolved_issues_remain"
    elif actual_escalation_required:
        expected_status = "escalation_required"
    else:
        expected_status = "revised"
    if critic_status != expected_status:
        violations.append(f"quality_assessment.critic_status is {critic_status!r} but findings imply {expected_status!r}")

    dv = qa.get("deterministic_validation") or {}
    if dv.get("passed") is True and dv.get("violations"):
        violations.append("quality_assessment.deterministic_validation.passed is true but violations is non-empty")

    # --- Confidence: counts must match, level must be bounded by them -----
    confidence = payload.get("confidence") or {}
    factors = confidence.get("factors") or {}
    expected_factors = {
        "gap_count": len(payload.get("gaps") or []),
        "conflict_count": len(payload.get("conflicts") or []),
        "unknown_count": len(payload.get("unknowns") or []),
        "assumption_count": len(payload.get("assumptions") or []),
        "open_clarification_question_count": len(clarification_questions),
        "evidence_count": len(evidence),
    }
    for key, expected in expected_factors.items():
        if factors.get(key) != expected:
            violations.append(f"confidence.factors.{key} is {factors.get(key)!r} but actual count is {expected}")

    level = confidence.get("level")
    conflict_count = expected_factors["conflict_count"]
    unresolved_count = expected_factors["unknown_count"] + expected_factors["open_clarification_question_count"]
    if conflict_count > 0 and level != "low":
        violations.append(f"confidence.level is {level!r} but conflict_count is {conflict_count} — any open conflict caps confidence at 'low'")
    elif conflict_count == 0 and unresolved_count > 0 and level == "high":
        violations.append(
            f"confidence.level is 'high' but there are {unresolved_count} unresolved unknown(s)/clarification question(s) — "
            f"'high' requires zero conflicts, unknowns, and open clarification questions"
        )

    # --- Review status: never approved --------------------------------------
    review_status = payload.get("review_status") or {}
    if review_status.get("status") not in {"pending_ba_po_review", "blocked_missing_input", "requires_conflict_resolution"}:
        violations.append(f"review_status.status {review_status.get('status')!r} is not a recognized (always-unapproved) value")
    note = (review_status.get("note") or "").lower()
    if "approved" in note and "not approved" not in note and "not-approved" not in note:
        violations.append("review_status.note appears to assert approval — this contract must never claim approval")

    _scan_for_forbidden_approval_keys(payload, "$", violations)

    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", help="Path to a JSON file containing a RequirementRefinementResult document.")
    args = parser.parse_args()

    with open(args.path, "r", encoding="utf-8") as f:
        payload = json.load(f)

    violations = validate(payload)
    if not violations:
        return 0

    for v in violations:
        print(v, file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
