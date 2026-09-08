# Requirements Refinement Agent — Basic Flow

This document is a **polished overview** of how the Westfield AI Engineering
Platform's Requirements Refinement capability actually works today. It
summarizes, in flow form, what is fully specified in:

- [`.claude/agents/ba-qa-agent.md`](.claude/agents/ba-qa-agent.md) — the
  agent's own input/output contract and boundaries.
- [`.claude/skills/requirement-analysis/SKILL.md`](.claude/skills/requirement-analysis/SKILL.md)
  — the reusable procedure the agent follows (classification labels, core
  policies, the 24-step procedure, the Requirements Critic pass).

Those two files remain the **procedural source of truth**. This document
does not add, loosen, or reinterpret anything they define — it exists so a
new contributor can see the shape of the flow at a glance before reading the
full specification.

## Where it fits in the platform

```
User (Jira key / Jira story / free-text requirement / BRD excerpt)
        │
        ▼
Westfield Orchestrator  ──▶  ba-qa-agent (Requirements Refinement)
        │                          │
        │                          ▼
        │                requirement-analysis skill
        │                          │
        │             ┌────────────┴────────────┐
        │             ▼                          ▼
        │     Jira MCP tools            Knowledge Fabric MCP tools
        │   (getJiraIssue, etc.)     (search_knowledge, get_context)
        │             │                          │
        │             └────────────┬────────────┘
        │                          ▼
        │              Refinement + Requirements
        │                    Critic pass
        │                          │
        │                          ▼
        │           Structured BA/PO Review Package
        │        ("NOT APPROVED — awaiting BA/PO review")
        │                          │
        │                          ▼
        │         output/ba-qa/<run-id>.md  (persisted artifact)
        ▼
(only on an explicit next-stage request → automation-agent)
```

`ba-qa-agent` is the **only** agent in this platform that performs
Requirements Refinement. It never generates test scenarios, detailed test
cases, or automation code, and it never approves a requirement.

## 1. Input

The agent accepts **exactly one** requirement identity, plus optional
extras:

| Input | Label applied |
|---|---|
| Jira issue key or URL (retrieved read-only) | `[Confirmed – Jira Requirement]` |
| Jira story fields already supplied by the user/an upstream agent (not re-fetched) | `[Confirmed – Jira Requirement]` |
| Free-text requirement, user story, or BRD excerpt | `[Confirmed – Requirement]` |
| Optional: existing acceptance criteria | `[Confirmed – Supplied AC]` |
| Optional: approved supporting context (design notes, linked docs, constraints) actually supplied by the user | labeled inline; never invented to fill a silence |

The input shape is determined **before** anything else happens, since it
decides which Confirmed label applies for the rest of the run.

## 2. Tools actually available

| Capability | Tool | Notes |
|---|---|---|
| Jira single-issue retrieval | `getJiraIssue` | Read-only; `fields: ["*all"]`, never a hardcoded custom field ID |
| Resolve Jira cloud ID | `getAccessibleAtlassianResources` | Resolved once per session, reused |
| Jira issue search | `searchJiraIssuesUsingJql` | Read-only; evidence-gathering only (duplicates/related issues, prior-version context) — never a general Jira browse |
| Knowledge Fabric search | `search_knowledge` | One query per extracted concept (typically 2–5 per requirement) |
| Knowledge Fabric context | `get_context` | Mandatory before citing any document — a snippet alone is never sufficient |
| Repo-local evidence | `Read` / `Grep` / `Glob` | Read-only — prior `output/ba-qa/*.md` artifacts, existing `tests/**` |
| Persistence | `Bash` | Only to run `scripts/save_agent_output.py` |

No Jira write tool, no Confluence tool, and no Knowledge Fabric tool beyond
`search_knowledge`/`get_context` is granted. Where a step below would
benefit from a capability like automated conflict/gap detection or
project-wide duplicate search, the agent performs the equivalent reasoning
by hand and **states plainly that the broader tool doesn't exist** — it
never presents a manual approximation as if a dedicated tool produced it.

## 3. The flow

1. **Understand the request** and confirm it is (at least partly) a
   refinement task — an out-of-scope ask (automation code, final test
   cases, Jira edits) is named and stopped rather than attempted.
2. **Retrieve the Jira story** when a bare issue key was given (read-only);
   otherwise use exactly what was supplied.
3. **Preserve the original requirement** — quoted verbatim before any
   restatement; never overwritten by later refinement.
4. **Extract requirement terms/entities** (domain nouns, system/feature
   names, policy areas) as raw material for the next step.
5. **Build focused Knowledge Fabric queries** — one per concept, not one
   query for the whole requirement text.
6. **Search → triage → confirm** — `search_knowledge` for each query,
   triage by `score`/`matched_terms`/`snippet`, then `get_context` on every
   materially relevant hit before it can be cited. Re-search if new
   project-specific terminology surfaces. Every empty search is recorded —
   an absence is itself a finding.
7. **Assemble the evidence pack** — Jira fields (or free text/BRD) plus
   every retrieved Knowledge Fabric document (`document_id`, source,
   authority, policy applicability tier, exact excerpt). Everything from
   here on draws only from this pack plus the requirement's own source
   text.
8. **Analyze business intent** — Actor, Trigger, Preconditions, Process,
   Expected Outcome, each labeled separately.
9. **Extract business rules** separately from the process narrative — never
   invented, always sourced.
10. **Detect ambiguity** — flag any phrase admitting more than one reading;
    state the assumed reading as `[Assumption]`.
11. **Detect gaps** — missing information, each tagged with exactly one
    primary type (Business requirement / Security / Functional /
    Testability / Traceability gap).
12. **Generate clarification questions** — one per resolvable
    ambiguity/gap, each answerable in a single sentence or decision.
13. **Identify dependencies** — UI/API/data/external systems, sourced or
    labeled `[Assumption]`/`[Blocked – missing information]`.
14. **Detect duplicates/related requirements**, when evidence permits —
    via `search_knowledge`, `searchJiraIssuesUsingJql`, and prior
    `output/ba-qa/*.md` artifacts; explicitly not an exhaustive Jira-wide
    search.
15. **Detect conflicts**, when evidence permits — four-part format
    (requirement statement / conflicting source / why they conflict /
    required clarification), **never resolved** by the agent.
16. **Compare versions**, when evidence permits — a prior artifact for the
    same key, or retrieved Jira history; otherwise "no prior version
    evidence found."
17. **Assess testability** — is there an observable pass/fail signal as
    stated.
18. **Assess automation feasibility** — high-level candidate layer only
    (UI/API/manual-only/undecidable); the full plan belongs to
    `automation-agent`.
19. **Identify edge cases and risks** — sourced where possible;
    unsupported ones labeled `[Recommendation]`.
20. **Draft/refine acceptance criteria** — Confirmed vs. Proposed, never
    merged; no test scenarios or test cases produced here.
21. **Build traceability candidates** — Requirement → Business Rule/AC →
    dependency/existing test, marked "candidate," never final.
22. **Run the Requirements Critic pass** — all fourteen checks (see below)
    over the draft; revise what can be fixed with existing evidence,
    escalate what needs a human decision, disclose what's genuinely
    unresolved. Never invent evidence to close a finding.
23. **Return the structured BA/PO review package** (22 output sections)
    and persist it.

## 4. Evidence & classification labels

Every statement in the output carries exactly one label:

| Label | Meaning |
|---|---|
| `[Confirmed – Jira Requirement]` | Stated directly in retrieved/supplied Jira fields |
| `[Confirmed – Requirement]` | Stated directly in free-text requirement input |
| `[Confirmed – Supplied AC]` | Stated in supplied acceptance criteria |
| `[Confirmed – Knowledge Fabric: <document_id>]` | Stated in a document opened via `get_context` |
| `[Retrieved Evidence – Jira: <field>]` / `[Retrieved Evidence – Repo: <path>]` | A secondary Jira field or repo file actually consulted |
| `[Assumption]` | Inferred/defaulted by the agent, not sourced |
| `[Recommendation]` | Advice the requirement owner must still approve |
| `[Unknown]` | Cannot be determined and cannot be phrased as a question |
| `[Blocked – missing information]` | A concrete downstream value has no source anywhere |

An assumption is never promoted to confirmed, no matter how reasonable it
looks or how many later sections build on it.

## 5. Requirements Critic pass

Before the package is returned, the draft is checked against all fourteen
adversarial checks defined in the skill (original intent preserved,
unsupported business rules, assumption-as-fact, AC testability, AC internal
consistency, Gap/Conflict separation, Conflict evidence, clarification
question quality, dependency evidence, edge-case relevance, automation
feasibility grounding, traceability evidence, citations for material
claims, and any tool operation claimed but not actually performed).

Each finding is disposed of as exactly one of **revise** (fixable from
existing evidence — may only downgrade/relabel/reformat, never upgrade
evidentiary status), **escalate** (needs a human/business decision), or
**unresolved** (can be neither fixed nor cleanly escalated — disclosed
plainly). The overall result is reported as one `critic_status`: `clean`,
`revised`, `escalation_required`, or `unresolved_issues_remain` (most
severe wins).

## 6. Output package (22 sections)

1. Requirement Summary
2. Original Requirement (verbatim)
3. Refined Story
4. Business Intent
5. Confirmed Facts
6. Business Rules
7. Acceptance Criteria (Confirmed / Proposed — never merged)
8. Edge Cases / Risks
9. Dependencies
10. Related / Duplicate Requirements
11. Conflicts
12. Gaps
13. Clarification Questions
14. Testability Assessment
15. Automation Feasibility
16. Existing Test/Automation Mapping
17. Traceability (candidate chain)
18. Evidence / Citations
19. Assumptions
20. Unknowns
21. Requirements Quality Assessment (the Critic pass result)
22. BA/PO Approval Required — counts + the mandatory line:
    **"Approval status: NOT APPROVED — awaiting BA/PO review."**

Any section that doesn't apply states "not applicable" and why, rather
than being dropped silently.

## 7. Persistence & traceability

The finished package is saved via `scripts/save_agent_output.py` as
`output/ba-qa/<run-id>.md`, tagged with `--requirement-id`, `--source`,
and `--review-status` (`pending_ba_po_review`, `blocked_missing_input`, or
`requires_conflict_resolution`). A `run_id` handed down from the
Westfield Orchestrator (or another agent) is reused; otherwise one is
minted and reported back so it can be threaded through any later
automation-planning stage.

## 8. Hard boundaries

The agent never:

- Approves a requirement, or implies approval/readiness/sign-off.
- Writes to Jira in any way (create/edit/comment/transition/link) — only
  `getJiraIssue`, `getAccessibleAtlassianResources`, and
  `searchJiraIssuesUsingJql` are used, all read-only.
- Generates test scenarios, detailed test cases, or automation code.
- Modifies application source code, repositories, or deploys anything.
- Resolves a Conflict, or makes a business decision on the requirement
  owner's behalf.
- Invents a business rule, URL, endpoint, selector, or credential not
  present in retrieved/supplied evidence.

Every package this agent produces ends the same way, regardless of how
clean or how gap-ridden the requirement turned out to be:

> **Approval status: NOT APPROVED — awaiting BA/PO review.**
