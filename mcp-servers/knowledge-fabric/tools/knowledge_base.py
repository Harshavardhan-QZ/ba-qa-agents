"""In-memory sample knowledge dataset for the Knowledge Fabric MCP server.

This is a placeholder store. Swap `DOCUMENTS` for a real backend (vector DB,
Confluence export, S3 index, ...) by keeping the same document shape and the
`all_documents()` / `get_document()` accessors below.

Document shape:
    id          str        stable identifier, used by get_context
    title       str
    source      str        where the document came from
    tags        list[str]
    updated     str        ISO-8601 date (last_updated)
    content     str        full body text
    domain      str        optional; topic/domain area, e.g. "Authentication"
    authority   str        optional; authority/status, e.g. "Approved - Current",
                           "Deprecated - Superseded", "Closed - Historical Record"
    version     str        optional; document version, if the source tracks one

`domain`, `authority`, and `version` are optional and default to None when a
document does not set them — existing documents below predate these fields.

SAMPLE / MOCK DATA NOTICE
-------------------------
The `sample-pwdreset-*` documents in this file are hand-authored MOCK data
created only to test the Requirements Refinement (BA/QA) flow before a real
Knowledge Fabric is available. They do not represent real enterprise policy,
requirements, defects, or systems. When a real Knowledge Fabric is connected,
delete these entries (or the whole in-memory store) and point
`all_documents()` / `get_document()` at the real backend — the MCP server and
the ba-qa-agent need no other change, since both only ever consume the
document shape above via `search_knowledge` and `get_context`.
"""

from __future__ import annotations

from typing import Any

DOCUMENTS: list[dict[str, Any]] = [
    {
        "id": "kb-001",
        "title": "Onboarding a New Service to the Platform",
        "source": "platform-handbook/onboarding.md",
        "tags": ["onboarding", "platform", "deployment", "checklist", "engineering", "process"],
        "updated": "2026-04-12",
        "content": (
            "Every new service must be registered in the service catalog before it can "
            "receive production traffic. Registration requires an owning team, an on-call "
            "rotation, and a documented service level objective.\n\n"
            "The onboarding checklist has four stages. First, scaffold the repository from "
            "the service template so that linting, test harnesses, and the build pipeline "
            "are wired up consistently. Second, declare infrastructure in Terraform under "
            "the team namespace. Third, connect logging and metrics to the shared "
            "observability stack. Fourth, run a load test against staging and attach the "
            "results to the launch review.\n\n"
            "Services that skip the launch review are blocked at the ingress layer. The "
            "platform team runs the review every Tuesday and turnaround is usually one week."
        ),
    },
    {
        "id": "kb-002",
        "title": "Incident Response Runbook",
        "source": "sre/runbooks/incident-response.md",
        "tags": ["incident", "sre", "on-call", "runbook", "escalation", "engineering", "process"],
        "updated": "2026-06-02",
        "content": (
            "An incident begins the moment customer impact is suspected, not when it is "
            "confirmed. The on-call engineer declares the incident, opens a channel, and "
            "takes the incident commander role until it is explicitly handed over.\n\n"
            "Severity levels drive escalation. SEV1 means total outage or data loss and "
            "pages the leadership rotation immediately. SEV2 means major degradation for a "
            "subset of customers and pages the owning team. SEV3 covers minor issues that "
            "can wait for business hours.\n\n"
            "Mitigation always takes priority over diagnosis. Roll back first, investigate "
            "afterwards. Write the postmortem within five business days and keep it "
            "blameless: the goal is to find the missing guardrail, not the person who "
            "tripped over it."
        ),
    },
    {
        "id": "kb-003",
        "title": "Data Retention and Classification Policy",
        "source": "legal/policies/data-retention.md",
        "tags": ["policy", "data", "privacy", "compliance", "retention", "security"],
        "updated": "2026-01-28",
        "content": (
            "Data is classified into four tiers: public, internal, confidential, and "
            "restricted. Restricted data includes personal identifiers, payment details, "
            "and anything covered by a customer data processing agreement.\n\n"
            "Retention windows differ by tier. Internal telemetry is kept for ninety days. "
            "Application logs containing user identifiers are kept for thirty days and then "
            "purged automatically. Financial records are retained for seven years to satisfy "
            "audit requirements.\n\n"
            "Any export of restricted data outside the production boundary requires an "
            "approved access request and is logged for audit. Deletion requests from "
            "customers must be fulfilled within thirty days across primary stores, backups, "
            "and downstream analytics warehouses."
        ),
    },
    {
        "id": "kb-004",
        "title": "API Design Guidelines",
        "source": "engineering/guides/api-design.md",
        "tags": ["api", "rest", "design", "versioning", "engineering", "architecture"],
        "updated": "2026-05-19",
        "content": (
            "Public APIs are contracts. Once published, a field cannot change meaning and a "
            "response cannot lose a field without a version bump.\n\n"
            "Prefer resource-oriented REST with plural nouns and predictable nesting. Use "
            "cursor-based pagination rather than offsets so that results stay stable while "
            "the underlying collection changes. Return structured error objects with a "
            "machine-readable code, a human-readable message, and a request identifier.\n\n"
            "Versioning happens in the URL path. Deprecated versions stay available for at "
            "least six months and emit a deprecation header so that clients can detect the "
            "sunset date programmatically."
        ),
    },
    {
        "id": "kb-005",
        "title": "Vector Search and Retrieval Architecture",
        "source": "engineering/design/retrieval-architecture.md",
        "tags": ["search", "retrieval", "embeddings", "rag", "architecture", "engineering", "data"],
        "updated": "2026-07-08",
        "content": (
            "The retrieval layer sits between raw document storage and any consumer that "
            "needs grounded context. Documents are chunked on semantic boundaries, embedded, "
            "and written to the vector index alongside their metadata.\n\n"
            "Query time is a hybrid: a dense vector search supplies semantic recall while a "
            "sparse keyword pass anchors exact terms such as error codes and product names. "
            "Results are merged with reciprocal rank fusion and then reranked by a smaller "
            "cross-encoder before the top results are returned.\n\n"
            "Freshness matters more than index size. A nightly reindex would leave the "
            "corpus a day stale, so writes are streamed and the index is updated "
            "incrementally within minutes of a source document changing."
        ),
    },
    {
        "id": "kb-006",
        "title": "Employee Expense and Travel Policy",
        "source": "people-ops/policies/expenses.md",
        "tags": ["expenses", "travel", "policy", "people-ops", "reimbursement", "process"],
        "updated": "2026-03-04",
        "content": (
            "Spend company money as if it were your own. Where the policy is silent, use "
            "judgement and expect to explain the decision.\n\n"
            "Flights under six hours are booked in economy. Longer flights may be booked in "
            "premium economy with manager approval. Hotels should stay within the city cap "
            "published in the booking tool.\n\n"
            "Submit receipts within thirty days of the expense date. Anything above the "
            "single-item threshold needs an itemised receipt rather than a card statement "
            "line. Reimbursements are processed in the payroll run following approval."
        ),
    },
    {
        "id": "kb-007",
        "title": "Authentication and Session Management",
        "source": "security/guides/authentication.md",
        "tags": ["security", "auth", "oauth", "sessions", "tokens", "engineering", "api"],
        "updated": "2026-06-25",
        "content": (
            "All first-party clients authenticate through the central identity provider "
            "using OAuth 2.1 with PKCE. Passwords are never handled by product services.\n\n"
            "Access tokens are short lived at fifteen minutes and are refreshed silently. "
            "Refresh tokens rotate on every use, and reuse of a consumed refresh token is "
            "treated as compromise: the whole token family is revoked and the user is asked "
            "to sign in again.\n\n"
            "Service-to-service calls use workload identity rather than static secrets. Any "
            "long-lived credential that cannot be eliminated must be stored in the secret "
            "manager and rotated on a ninety day schedule."
        ),
    },
    {
        "id": "kb-008",
        "title": "Quarterly Planning Process",
        "source": "handbook/planning/quarterly.md",
        "tags": ["planning", "process", "okr", "roadmap", "handbook", "policy"],
        "updated": "2026-02-17",
        "content": (
            "Planning runs on a quarterly cadence with a two week window before the quarter "
            "starts. The goal is alignment, not a Gantt chart.\n\n"
            "Each team publishes at most three objectives. Objectives describe an outcome a "
            "customer would notice; key results are the measurable evidence. Work that keeps "
            "the lights on is budgeted as a percentage of capacity rather than written as an "
            "objective.\n\n"
            "Mid-quarter changes are expected. When priorities shift, the team updates the "
            "plan in place and notes what was dropped, so that the trade-off is visible "
            "rather than silently absorbed."
        ),
    },
    # ------------------------------------------------------------------
    # SAMPLE / MOCK DATA — password-reset requirement, for testing the
    # Requirements Refinement (BA/QA) flow only. Not real enterprise
    # knowledge. See the SAMPLE / MOCK DATA NOTICE in the module docstring.
    # ------------------------------------------------------------------
    {
        "id": "sample-pwdreset-001",
        "title": "[SAMPLE DATA] Password Reset — Business Requirement (Current)",
        "source": "mock-kfa/product/requirements/password-reset-brd.md",
        "domain": "Authentication / Account Recovery — Business Requirement",
        "authority": "Approved - Current (Product/BA sign-off)",
        "version": "v2.3",
        "tags": [
            "password-reset", "authentication", "account-recovery",
            "sample-data", "requirement", "business", "product",
        ],
        "updated": "2026-05-01",
        "content": (
            "SAMPLE / MOCK KNOWLEDGE FABRIC DATA — for testing the Requirements "
            "Refinement flow only. This is not a real production requirement.\n\n"
            "Business requirement: registered users who lose access to their "
            "account must be able to reset their own password without contacting "
            "support staff.\n\n"
            "Actor: a registered end user who cannot sign in.\n"
            "Trigger: the user selects \"Forgot password\" on the sign-in screen.\n"
            "Process: the user enters their registered email address. If the "
            "email matches an account, the system sends a password-reset link. "
            "The user follows the link, sets a new password, and regains access.\n"
            "Expected outcome: the user can sign in with the new password "
            "immediately after completing the reset.\n\n"
            "The reset link should expire after a reasonable time to limit "
            "exposure if the email is intercepted. Stakeholders have also asked "
            "that the overall flow feel fast and frictionless for the end user.\n\n"
            "This requirement does not state what should happen for accounts "
            "protected by multi-factor authentication (MFA), and does not state "
            "any limit on how many reset requests a single account may generate "
            "in a given period. The flow depends on the outbound email delivery "
            "service and on the identity verification used at login."
        ),
    },
    {
        "id": "sample-pwdreset-002",
        "title": "[SAMPLE DATA] Password Reset — Business Rules",
        "source": "mock-kfa/product/business-rules/password-reset-rules.md",
        "domain": "Authentication / Account Recovery — Business Rules",
        "authority": "Approved - Current (BA-maintained rule set)",
        "version": "v1.4",
        "tags": [
            "password-reset", "authentication", "account-recovery",
            "sample-data", "business-rules", "policy",
        ],
        "updated": "2026-05-10",
        "content": (
            "SAMPLE / MOCK KNOWLEDGE FABRIC DATA — for testing the Requirements "
            "Refinement flow only. This is not a real production rule set.\n\n"
            "BR-1: A password-reset link expires 30 minutes after it is issued "
            "and may be used exactly once.\n"
            "BR-2: An account may request at most 3 password-reset emails "
            "within a rolling 1-hour window; further requests in that window "
            "are silently rate-limited.\n"
            "BR-3: The new password must not match any of the account's last 5 "
            "passwords.\n"
            "BR-4: Completing a password reset immediately invalidates all "
            "existing active sessions for that account, on every device.\n"
            "BR-5: If the account has multi-factor authentication (MFA) "
            "enabled, the user must re-verify the second factor before the new "
            "password takes effect.\n"
            "BR-6: The reset email is sent only to the email address currently "
            "on file for the account; no SMS or other alternate-channel "
            "fallback is defined for accounts without a reachable recovery "
            "email."
        ),
    },
    {
        "id": "sample-pwdreset-003",
        "title": "[SAMPLE DATA] Authentication & Identity Management Policy (Current)",
        "source": "mock-kfa/security/policies/iam-authentication-policy.md",
        "domain": "Authentication / Identity & Access Management — Security Policy",
        "authority": "Approved - Current (Security & Compliance, mandatory)",
        "version": "v3.0",
        "tags": [
            "password-reset", "authentication", "account-recovery",
            "sample-data", "policy", "iam", "identity-management",
            "security", "mfa", "compliance",
        ],
        "updated": "2026-06-15",
        "content": (
            "SAMPLE / MOCK KNOWLEDGE FABRIC DATA — for testing the Requirements "
            "Refinement flow only. This is not a real production policy.\n\n"
            "Section 4 — Credential Reset Standards (mandatory for all "
            "first-party applications):\n"
            "4.1 Any flow that issues a new credential (password reset, forced "
            "reset, admin-triggered reset) must invalidate all active sessions "
            "for the affected account.\n"
            "4.2 Accounts enrolled in multi-factor authentication must "
            "re-verify the second factor as part of any credential reset; a "
            "reset must never silently downgrade an account to single-factor "
            "authentication.\n"
            "4.3 Reset tokens/links must be single-use and must expire no "
            "later than 30 minutes after issuance.\n"
            "4.4 Every credential reset event must be written to the security "
            "audit log with account id, timestamp, and initiating IP address.\n"
            "4.5 Security questions are not an approved identity-verification "
            "factor for any first-party application; email-based verification "
            "or MFA re-verification are the only approved methods.\n\n"
            "This policy supersedes any conflicting engineering documentation "
            "for password-reset or other credential-reset flows."
        ),
    },
    {
        "id": "sample-pwdreset-004",
        "title": "[SAMPLE DATA] Historical Defect — Password-Reset Token Reuse (DEF-2024-118)",
        "source": "mock-kfa/qa/defects/DEF-2024-118.md",
        "domain": "Authentication / Account Recovery — Defect History",
        "authority": "Closed - Historical Record (resolved defect, informational)",
        "version": "N/A — defect record (opened 2024-10-20, closed 2024-11-02)",
        "tags": [
            "password-reset", "authentication", "account-recovery",
            "sample-data", "defect", "historical", "qa", "regression", "security",
        ],
        "updated": "2024-11-02",
        "content": (
            "SAMPLE / MOCK KNOWLEDGE FABRIC DATA — for testing the Requirements "
            "Refinement flow only. This is a fabricated historical defect "
            "record, not a live Jira issue.\n\n"
            "Defect ID: DEF-2024-118 (sample/historical only)\n"
            "Title: Password-reset token could be replayed after first use\n"
            "Status: Closed — Fixed. Opened 2024-10-20, closed 2024-11-02.\n\n"
            "Summary: the password-reset endpoint validated only a token's "
            "signature and expiry, not whether it had already been consumed. "
            "Anyone who obtained a copy of a reset link (for example via a "
            "shared mail gateway) could use it a second time to reset the "
            "password again after the legitimate user had already completed "
            "their own reset, locking the real user out.\n\n"
            "Root cause: token consumption state was not persisted; a token "
            "remained valid for its full lifetime regardless of prior use.\n\n"
            "Fix: reset tokens are now marked consumed on first successful use "
            "and rejected on any subsequent attempt; completing a reset also "
            "invalidates any other outstanding reset tokens for the same "
            "account.\n\n"
            "Recommended regression coverage: verify a used reset token is "
            "rejected on a second attempt, and verify that issuing a new reset "
            "request invalidates prior outstanding tokens for that account."
        ),
    },
    {
        "id": "sample-pwdreset-005",
        "title": "[SAMPLE DATA] Legacy Password-Reset Implementation (Superseded)",
        "source": "mock-kfa/engineering/legacy/password-reset-legacy-impl.md",
        "domain": "Authentication / Account Recovery — Legacy Engineering (Superseded)",
        "authority": (
            "Deprecated - Superseded (historical/migration reference only; "
            "do not treat as current behavior)"
        ),
        "version": "v1.0 (released 2019-08-14; superseded 2023-03-01)",
        "tags": [
            "password-reset", "authentication", "account-recovery",
            "sample-data", "legacy", "deprecated", "engineering", "conflict-source",
        ],
        "updated": "2019-08-14",
        "content": (
            "SAMPLE / MOCK KNOWLEDGE FABRIC DATA — for testing the Requirements "
            "Refinement flow only. This is not a description of current "
            "production behavior.\n\n"
            "STATUS: DEPRECATED / SUPERSEDED — retained only for historical and "
            "migration reference.\n\n"
            "This document describes the password-reset implementation as it "
            "existed prior to the 2023 authentication overhaul:\n"
            "- Reset links were valid for 24 hours from issuance and could be "
            "reused any number of times until they expired.\n"
            "- Identity verification for a reset request could be satisfied by "
            "answering two security questions instead of confirming the "
            "account email.\n"
            "- Multi-factor authentication was not re-checked as part of a "
            "reset; an MFA-enabled account was reset the same way as any "
            "other account.\n"
            "- The system did not check new passwords against password "
            "history; a user could reset their password back to a previous "
            "one.\n"
            "- There was no rate limit on reset requests for a given account.\n\n"
            "This implementation was replaced starting 2023-03-01 following "
            "the identity/access management policy overhaul (see the current "
            "Authentication & Identity Management Policy) and following the "
            "password-reset token-replay defect (DEF-2024-118)."
        ),
    },
]

# Fast lookup by id, built once at import time.
_INDEX: dict[str, dict[str, Any]] = {doc["id"]: doc for doc in DOCUMENTS}


def all_documents() -> list[dict[str, Any]]:
    """Return every document in the knowledge base."""
    return DOCUMENTS


def get_document(document_id: str) -> dict[str, Any] | None:
    """Return one document by id, or None if it does not exist."""
    return _INDEX.get(document_id)


def known_ids() -> list[str]:
    """Return all valid document ids."""
    return list(_INDEX)