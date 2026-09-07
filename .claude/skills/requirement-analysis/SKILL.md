---
name: requirement-analysis
description: Reusable Requirements Refinement procedure — takes a Jira issue, a free-text requirement/user story/BRD excerpt, optional existing acceptance criteria, and optional additional context, and produces a full evidence-backed refinement package (requirement understanding, business rules, dependencies, duplicates, conflicts, gaps, clarification questions, impact analysis, testability/automation feasibility, confirmed/proposed acceptance criteria, test scenarios, traceability candidates, a requirements-critic pass, and a BA/PO review package) grounded in Knowledge Fabric and Jira evidence, without inventing business rules or approving anything. Use whenever a requirement needs analysis, clarification, refinement, quality validation, acceptance criteria, test scenarios/cases, gap analysis, impact analysis, duplicate/conflict detection, or preparation for BA/PO review.
---

# Requirement Analysis — Requirements Refinement Procedure

A structured, evidence-first procedure for turning a raw requirement into a
BA/PO-reviewable refinement package: grounded in retrieved project knowledge,
explicit about what's unknown or conflicting, never inventing a business
rule, and traceable end to end. This is the workflow `ba-qa-agent` follows
for every substantive request; it is also the reusable procedure a future
**Test Authoring** step and the **orchestrator** can invoke directly when
they need requirement-level grounding rather than final test-case authorship
or routing decisions. Nothing in this skill approves a requirement — its
terminal output always remains a candidate for human BA/PO review.

## Input contract

Accepts exactly one requirement identity, plus optional extras — apply the
same discipline regardless of which identity shape was given:

1. **A Jira user story** — at minimum issue key, summary, description, issue
   type, and status, plus whatever else was supplied (e.g. an
   acceptance-criteria custom field, labels, components). Whether the issue
   was retrieved live via the Atlassian connector or handed to you already
   populated is not this skill's concern — either way, treat the retrieved/
   supplied fields as the source-of-truth input and label facts drawn from
   them `[Confirmed – Jira Requirement]` (see Classification labels).
2. **A free-text requirement, user story, or BRD excerpt** — pasted or typed
   directly, with no Jira issue behind it. Label facts drawn from this text
   `[Confirmed – Requirement]`.
3. **Optional: existing acceptance criteria** — text, list, or a Jira
   AC-shaped custom field, supplied alongside either identity above. Label
   facts drawn from it `[Confirmed – Supplied AC]`. Never re-derive or
   contradict it silently — treat a disagreement between supplied AC and the
   requirement text itself as a Conflict.
4. **Optional: additional context** — design notes, linked docs, prior
   discussion, constraints. Use only what is actually supplied; its absence
   is never a reason to invent equivalent content.

Determine which identity shape you were given **before** doing anything
else — it decides which Confirmed label applies for the rest of the run.
Never hardcode an example Jira key, project, issue type, summary,
description, or acceptance criterion — every one of these comes from what
was actually retrieved or supplied in this run, never from a prior session.

## Core policies

These twelve rules govern every step below. When a later section and this
one appear to overlap, this section is the authority on the rule itself; the
later section is the authority on where in the output it's applied.

### 1. When Jira retrieval is required

Retrieve via the Atlassian connector's `getJiraIssue` (plus
`getAccessibleAtlassianResources` once per session, to resolve `cloudId`,
reused thereafter) **only when given a bare Jira issue key or issue URL**.
Use `fields: ["*all"]` (or at minimum summary, description, issuetype,
status, plus every other field) so an acceptance-criteria-shaped custom
field can be found by scanning field names dynamically — never hardcode a
specific `customfield_<N>` ID. If the Jira story's fields were already
supplied in the conversation (by the user or an upstream agent), do **not**
re-fetch — use exactly what was given. If the input is free-text with no
Jira issue behind it, never call a Jira tool at all, even if the text
happens to mention a ticket number in passing — a mention is not a
retrieval request.

### 2. When Knowledge Fabric retrieval is required

Use `search_knowledge` whenever the requirement touches anything that could
be governed by existing project knowledge: domain rules, policies, prior
requirements, architecture decisions, API/design conventions,
security/compliance rules, process/runbook steps, or naming and terminology
used elsewhere in the project. In practice this is almost every real
requirement — skip it only for a requirement that is purely self-contained
and references no system, policy, or prior behavior at all. Do not answer
from general knowledge or assumption when the fact is the kind of thing that
would be documented internally (a severity threshold, a retention window, an
auth flow, a versioning rule, etc.) — retrieve it, or flag its absence as a
Gap.

### 3. How context relevance is evaluated

Relevance is a two-pass judgment, never a one-shot guess:

1. **Triage** — after `search_knowledge`, use `score`, `matched_terms`, and
   `snippet` to decide which hits are worth opening. A high score or a
   matched term is a reason to look, not a reason to cite.
2. **Confirmation** — call `get_context` on every hit that looks materially
   relevant and judge relevance from the full `content`, the `updated` date,
   and `source` — never from the snippet alone. Only after this step can a
   document be cited or assigned a policy applicability tier (see Policy
   applicability tiers).

Re-run `search_knowledge` if a retrieved document introduces new
project-specific terminology (a policy name, a tiering scheme) — that
vocabulary deserves its own follow-up search. Record every search that came
back empty; an absence is itself a finding (see Gaps), not something to omit
from the output.

### 4. How authoritative sources are prioritized

Priority order below governs **which source anchors a Confirmed label**, not
which source wins in a disagreement — a disagreement between two sources at
any tier, or across tiers, is always a Conflict (see rule 6), never resolved
by rank.

1. **The requirement's own source text** (Jira fields / free-text /
   supplied AC) — authoritative for what was actually asked for. Nothing
   overrides this for determining scope-as-stated.
2. **Knowledge Fabric, Directly applicable tier** — authoritative for how
   the stated requirement must behave under governing policy.
3. **Knowledge Fabric, Potentially applicable / Requires confirmation
   tiers** — informative only; anything derived from these stays Proposed,
   never Confirmed, until a human confirms applicability.
4. **Repo-local evidence** (existing test files under `tests/**`, prior
   `output/ba-qa/*.md` refinement artifacts) — lowest-authority sourced
   evidence; useful for discovering candidate concrete values or prior
   analysis, never authoritative over the requirement text or Knowledge
   Fabric. If the repo-local evidence itself self-discloses as unverified or
   supplied test input (as existing draft scripts in this repo do), carry
   that caveat forward verbatim rather than upgrading its trust level.
5. **Agent inference** (`[Assumption]`, `[Recommendation]`) — never
   authoritative; always the lowest tier; always labeled as such.

### 5. How confirmed facts differ from assumptions

A **Confirmed** fact is a quote or close paraphrase of something actually
retrieved or supplied in this run — a Jira field, free-text clause, supplied
AC, or the full content of a `get_context` call. An **Assumption** is
anything the agent infers, defaults, or fills a silence with — no matter how
reasonable. The test is provenance, not plausibility: if you cannot point to
the exact retrieved/supplied text or document it came from, it is not
Confirmed. See Classification labels for the exact label set and the
non-negotiable rule against ever promoting an Assumption to Confirmed.

### 6. How conflicts are represented

Every Conflict uses the same four-part structure, never a prose paragraph
that blends the parts together — see Conflict record format. A Conflict is
never resolved by the agent: not by picking a side, not by averaging or
blending values, not by silently preferring the higher-priority source from
rule 4. The output states the disagreement and the decision the requirement
owner must make; it never states a resolved answer.

### 7. How gaps differ from conflicts

A **Gap** is the absence of documented information — nothing in the
requirement, supplied AC, additional context, or Knowledge Fabric addresses
it. A **Conflict** is the presence of two sourced statements that disagree.
Never record a Gap as a Conflict (there is nothing to disagree with) and
never record a Conflict as a Gap (the information exists — twice, and
inconsistently). See Gap classification for the required tagging format.

### 8. How acceptance criteria are classified as confirmed vs proposed

**Confirmed Acceptance Criteria** are derived only from `[Confirmed – Jira
Requirement]`, `[Confirmed – Requirement]`, `[Confirmed – Supplied AC]`, or
`[Confirmed – Knowledge Fabric]` statements at the Directly Applicable tier.
**Proposed Acceptance Criteria (requires BA/PO confirmation)** are derived
from an `[Assumption]`, a `[Recommendation]`, or a Potentially
Applicable/Requires Confirmation policy tier. The two lists are never
merged, regardless of how likely a Proposed item seems to be correct.

### 9. How evidence/citations are attached

Every Retrieved-Evidence claim carries its concrete source inline, not just
a category label:

- Knowledge Fabric: `[Confirmed – Knowledge Fabric: <document_id>]`, always
  earned via an actual `get_context` call in this run — never a snippet
  alone, never a document id from a prior session.
- Jira: `[Confirmed – Jira Requirement]` for core fields; `[Retrieved
  Evidence – Jira: <field name>]` for a secondary field consulted beyond the
  core requirement text (e.g. a linked issue, a comment), when it was
  actually retrieved as part of `fields: ["*all"]` and materially used.
- Repo-local: `[Retrieved Evidence – Repo: <path>]` for any file actually
  opened via `Read`/`Grep`/`Glob` (an existing test, a prior artifact) —
  must name the exact path.

An item with no traceable source is never presented as evidence — it is an
`[Assumption]`, a `[Recommendation]`, or an `[Unknown]` instead.

### 10. When clarification questions must be generated

Generate one clarification question for every Ambiguity (a statement that
admits more than one reasonable reading) and every Gap that a BA/PO could
plausibly resolve with a single decision. A clarification question must be
answerable in one sentence or one decision — "please clarify requirements"
is not an acceptable question. If a Gap or Unknown cannot yet be phrased as
a useful, answerable question (the missing context is too broad to frame),
record it under Unknowns instead of forcing a low-quality question.

### 11. When the agent must stop and escalate

Escalate as `blocked` (see Failure handling in Output shape) rather than
proceeding when:

- The input identity is missing, empty, or an unresolvable Jira key —
  there is nothing to analyze.
- A required retrieval tool call fails entirely and no fallback evidence
  path exists for a step that depends on it (e.g. Jira retrieval fails for
  a bare-key input with no supplied fallback fields).
- Completing the analysis would require write access to Jira, production
  systems, or generating automation code/final test cases — name the
  boundary and stop that portion rather than working around it.

A run that surfaces many Ambiguities, Conflicts, or Gaps is **not** a reason
to escalate — that is the expected, successful output of a hard
requirement. Only escalate when the procedure genuinely cannot produce a
package at all, or a specific step is categorically out of scope.

### 12. What must never be inferred

Never invent, guess, or default:

- A business rule, threshold, value, or policy that isn't sourced from the
  requirement, supplied AC, or Knowledge Fabric — mark it `[Unknown]` and
  raise a clarification question instead.
- A URL, API endpoint, UI selector, database value, or credential not
  present in retrieved/supplied evidence — mark `[Blocked – missing
  information]`.
- The resolution of a Conflict, or which authoritative source "wins."
- The existence of a duplicate or related requirement beyond what
  `search_knowledge` or repo-local evidence actually surfaced.
- An automation layer decision beyond a high-level candidate — the full
  decision belongs to `automation-agent`.
- Approval, completion, or "ready" status for the requirement — that is a
  human BA/PO decision only (see Human approval, in Scope boundary).

## Tool inventory

Use only tools that are actually registered and actually granted to the
invoking agent — never assume a plausibly-named tool exists:

| Tool | Purpose | Notes |
|---|---|---|
| `search_knowledge(query, top_k)` | Discover candidate Knowledge Fabric documents | Real, registered. Query per concept, not one query for the whole requirement. |
| `get_context(document_id)` | Read a document's full content before citing it | Real, registered. Mandatory before any Confirmed – Knowledge Fabric claim. |
| `getJiraIssue` | Retrieve a Jira issue's fields, read-only | Real, via the Atlassian connector. `fields: ["*all"]`; never hardcode a custom field ID. |
| `getAccessibleAtlassianResources` | Resolve `cloudId` | Real, via the Atlassian connector. Resolve once, reuse. |
| `Read` / `Grep` / `Glob` | Find repo-local evidence (existing tests, prior artifacts) | Read-only; never edit. |

**Do not invent, call, or assume the existence of** a `detect_conflicts`,
`detect_gaps`, `check_freshness`, `find_authoritative_source`,
`get_relationships`, `trace_requirement`, `get_recommendations`,
`get_metrics`, `submit_feedback` tool, any Jira JQL/search tool, any Jira
issue-hierarchy or sprint-field tool, or any Confluence tool — none of these
are registered for this skill's use today. Where the procedure below asks
for a capability that would need one of these (duplicate search across a
project, automated conflict/gap detection, requirement-hierarchy traversal,
sprint-scoped queries, freshness scoring), perform the equivalent reasoning
by hand over the tools that do exist (`search_knowledge`, `get_context`,
repo-local `Read`/`Grep`/`Glob`, and whatever Jira fields `getJiraIssue`
actually returned) and **explicitly state the capability is unavailable
in its general form** rather than presenting a best-effort manual result as
if it were the output of a dedicated tool.

## Classification labels

Every statement in the output belongs to exactly one label — never left for
the reader to guess:

| Label | Meaning | How it's earned |
|---|---|---|
| **`[Confirmed – Jira Requirement]`** | Stated directly in the Jira issue's fields, when the input is a Jira user story. | Quote or closely paraphrase the actual field content. |
| **`[Confirmed – Requirement]`** | Stated directly in a free-text requirement with no Jira issue behind it. | Quote or closely paraphrase the requirement clause. |
| **`[Confirmed – Supplied AC]`** | Stated in optionally-supplied existing acceptance criteria. | Quote of the supplied AC. |
| **`[Confirmed – Knowledge Fabric: <document_id>]`** | Stated directly in a document opened with `get_context`. | Must trace to a specific `document_id` actually retrieved — never a snippet alone. |
| **`[Retrieved Evidence – Jira: <field>]`** | A secondary Jira field beyond the core requirement text. | Must trace to an actually-retrieved field. |
| **`[Retrieved Evidence – Repo: <path>]`** | A repo-local file actually opened (test, prior artifact, source). | Must trace to an actually-read path. |
| **`[Assumption]`** | Plausible, but asserted by the agent, not sourced from input or evidence. | Anything inferred, defaulted, or used to fill a silence. |
| **`[Recommendation]`** | Advice on what the team *should* decide or do — not a claim about what *is* required. | Used for suggestions the requirement owner must still approve. |
| **`[Unknown]`** | Cannot be determined and cannot yet be phrased as a useful clarification question. | Used sparingly — prefer a Clarification Question whenever one can be formed. |
| **`[Blocked – missing information]`** | A concrete downstream value (URL, selector, endpoint, credential, data value) has no source anywhere. | Applied at the specific unsupported field, not the whole item. |

Use `[Confirmed – Jira Requirement]` and `[Confirmed – Requirement]` as
alternatives, never both in the same analysis — pick the one matching the
actual input shape.

Rules:

- **Never promote an assumption to confirmed.** An `[Assumption]` (or
  `[Unknown]`) stays labeled that way for the entire document, no matter how
  reasonable it is or how many other statements depend on it. Restate the
  label every time a later section builds on it — never drop it.
- Never blend a confirmed fact and an assumption into one unlabeled
  statement. If part of a sentence is grounded and part is inferred, split
  the sentence or label each clause separately.
- A `[Recommendation]` is never itself an acceptance criterion — see Core
  policy 8 for how recommendations feed into Proposed ACs.
- Carry every label forward verbatim into the Traceability Candidates
  section so a reviewer can jump straight to the source without re-deriving
  it.

## Policy applicability tiers

When a retrieved Knowledge Fabric document could bear on the requirement,
classify *how* it applies — don't flatten every hit into "relevant":

| Tier | Meaning |
|---|---|
| **Directly applicable** | The document states a rule that unambiguously governs this requirement as written. |
| **Potentially applicable** | The document governs an adjacent or analogous case, but applying it here requires an inference. |
| **Requires confirmation** | The document is topically related but it's genuinely unclear whether it was intended to govern this case — treat any AC drawn from it as Proposed, not Confirmed. |

State the tier next to each document in **Retrieved Evidence**, and use it
per Core policy 8 to decide whether an AC derived from that document is
Confirmed or Proposed.

## The procedure

Run these steps in order. Each maps to one or more Output shape sections
below; a step marked *(conditional)* produces its section only when the
required evidence actually exists — otherwise that section states "not
applicable" and says why.

1. **Validate input** — confirm exactly one requirement identity was given
   and it is non-empty/resolvable. If not, stop and escalate (Core policy
   11) rather than guessing at intent.
2. **Normalize the requirement** — for a Jira story, produce the
   Original/Refined/Refinements-supported-by-Knowledge-Fabric split (see
   Refined User Story). For free text, restate it in your own words in
   Requirement Understanding. Never add scope; label every clarifying word
   that isn't a direct quote.
3. **Retrieve context** — per Core policies 1–3: Jira retrieval only if a
   bare key was given; Knowledge Fabric retrieval via the
   `search_knowledge` → `get_context` workflow below.
4. **Analyze business intent and extract structure** — Actor, Trigger,
   Preconditions, Process, Expected Outcome(s), each stated separately and
   labeled. Do not blend Process narrative with Business Rules (next step).
5. **Extract business rules separately** — every explicit rule, threshold,
   or constraint, quoted/labeled on its own, never folded into the Process
   narrative from step 4.
6. **Detect ambiguity and vague language** — flag any phrase admitting more
   than one reasonable reading; state the assumed reading as `[Assumption]`.
7. **Detect missing information** — distinct from ambiguity: something
   simply absent. Feeds Gaps (step 7 output) and, per Core policy 10,
   Clarification Questions.
8. **Generate clarification questions** — one per unresolved
   ambiguity/gap that can be phrased as an answerable question (Core
   policy 10).
9. **Identify dependencies** — UI, API, data, and external-system
   dependencies implied by the process/outcomes; sourced where possible,
   `[Assumption]` or `[Blocked – missing information]` otherwise.
10. **Detect duplicates/related requirements** *(bounded by tool
    inventory)* — search `search_knowledge` and repo-local prior
    `output/ba-qa/*.md` artifacts (via `Grep`/`Glob`) for the same Jira key
    or clearly overlapping subject matter. No Jira-wide search tool is
    available (see Tool inventory) — state plainly that this is not an
    exhaustive project-wide search, not that no duplicates exist.
11. **Detect contradictions/conflicts** — across Jira/free-text vs.
    Knowledge Fabric, supplied AC vs. requirement text, or Knowledge Fabric
    vs. Knowledge Fabric; four-part format (below); never resolved.
12. **Compare versions** *(conditional — only when evidence exists)* —
    evidence means a prior `output/ba-qa/*.md` artifact for the same Jira
    key/requirement, found via `Grep`/`Glob`, or Jira fields that expose
    prior state if actually retrieved. Otherwise: "not applicable — no
    prior version evidence found."
13. **Analyze change impact** *(conditional — only when evidence exists)* —
    evidence means Knowledge Fabric's `related` documents list or a prior
    artifact's own Impact Analysis. Otherwise: "not applicable — no impact
    evidence found."
14. **Assess testability** — does the requirement, as refined, have an
    observable pass/fail signal; if not, that is a Testability Gap.
15. **Assess automation feasibility** — high level only: candidate layer
    (UI/API/manual-only/undecidable), never a full automation plan — that
    decision belongs to `automation-agent`.
16. **Identify edge cases and risks** — sourced from the stated process and
    retrieved policy where possible; unsupported ones are `[Recommendation]`,
    never asserted as required.
17. **Draft/refine acceptance criteria** — Confirmed vs. Proposed split per
    Core policy 8.
18. **Map to existing tests/automation** *(conditional — only when evidence
    exists)* — search `tests/**` via `Grep`/`Glob`/`Read`; carry forward any
    "supplied, not verified" caveat the existing file already discloses
    (Core policy 4). Otherwise: "not applicable — no existing test evidence
    found."
19. **Write test scenarios** — high-level, numbered, each traced to an AC;
    not automation code, not step-by-step detail.
20. **Draft detailed test cases** — step-by-step, sourced or explicitly
    `[Blocked – missing information]`/`[Assumption]` per field. This is the
    natural handoff point for a **Test Authoring** step: a caller that only
    needs refinement through Traceability Candidates (step 21) may stop
    before this step and hand the package to Test Authoring for final
    detailed test-case authorship instead of generating them here.
21. **Build traceability candidates** — a proposed (not final) chain:
    Requirement → Business Rule/AC → Test Scenario → existing test (if any,
    from step 18) → dependency (from step 9). Marked "candidate" throughout.
22. **Run a requirements critic pass** — run all fourteen checks in
    Requirements Critic pass below against the draft; revise what can be
    revised, escalate what can't, and report the result via the
    `critic_status`/`findings`/`corrections`/`unresolved_items`/
    `escalation_required` return contract.
23. **Validate the structured result** — mechanical check: every Output
    shape section present or marked not-applicable; every statement carries
    exactly one label; every Gap has exactly one primary type; every
    Conflict has all four parts; nothing promoted from Assumption to
    Confirmed anywhere. Record the result, including anything found but not
    fully fixable (see Failure handling).
24. **Prepare the BA/PO review package** — assemble the full Output shape
    below, including the mandatory "NOT APPROVED — awaiting BA/PO review"
    line. This package is a candidate input, never a final one, until a
    human BA/PO acts on it outside this skill.

### The search_knowledge → get_context workflow (detail for step 3)

1. **Decompose the requirement into search concepts.** Pull out domain
   nouns, system/feature names, policy areas, and any terminology that
   sounds project-specific. A single requirement usually yields 2–5 distinct
   search queries — don't rely on one query built from the whole sentence.
2. **Call `search_knowledge` for each concept.** Use focused, specific
   queries. Review `score`, `matched_terms`, and `snippet` to triage before
   trusting a hit (Core policy 3).
3. **Call `get_context` on every document that looks materially relevant.**
   A snippet is a pointer, not a source — never cite or build acceptance
   criteria/test cases from a snippet alone. Read the full `content`, note
   `updated` and `source`, and check `related` documents for anything else
   worth pulling in.
4. **Re-search if the first pass surfaces new terminology.**
5. **Record what came back empty.** An absent result is itself a finding —
   surface it under Gaps, not silently dropped.
6. **Assemble the evidence pack.** Combine the retrieved/supplied
   requirement input (Jira fields, or free text/BRD) with every opened
   Knowledge Fabric document — `document_id`, title, `source`, `domain`,
   `authority`, policy applicability tier, and the exact excerpt relied on
   — into one working evidence set. Every step from Business Intent (step
   4) onward draws only from this pack plus the requirement's own source
   text; it is contextual evidence, never a replacement for the Jira/
   free-text requirement as the source of what's actually being asked for
   (Core policy 4, rule 1). This pack is also what Output section 4
   (Retrieved Evidence) reports.

### Conflict record format

Every entry under **Conflicts** uses this exact four-part structure — never
a prose paragraph that blends the parts together:

1. **Requirement statement** — the exact clause from the input (for a Jira
   story, "Jira requirement statement," quoting the actual field content;
   for free text, the requirement clause; for supplied AC, the AC text).
2. **Conflicting source** — `document_id`/title and exact clause (Knowledge
   Fabric), or the other conflicting field/source, quoted.
3. **Why they conflict** — one or two sentences on the specific
   incompatibility, not a restatement of both sides.
4. **Required clarification / decision** — the question the requirement
   owner must answer, or the decision they must make, to resolve it.

Do not pick a winner, average, or blend conflicting values (Core policy 6).
Never silently fold a conflicting source's version into the Refined Story —
the refined story reflects the original business intent; the conflict is
recorded separately.

### Gap classification

Every entry under **Gaps** is tagged with exactly one primary type:

| Type | Meaning |
|---|---|
| **Business requirement gap** | The requirement owner hasn't specified something a business stakeholder needs to decide. |
| **Security gap** | A security-relevant control is unspecified. |
| **Functional gap** | A behavior needed for the feature to work correctly is unspecified. |
| **Testability gap** | The requirement can't be verified as stated. |
| **Traceability gap** | Neither the requirement nor retrieved evidence addresses something needed to trace a downstream artifact back to a source. |

**Format rule (strict):** exactly one primary type. Never join two types
with a slash or plus sign. A plausible second type is a parenthetical
secondary in this exact format:

```
<Primary gap type> (secondary: <Secondary gap type>)
```

Correct: `Security gap (secondary: Functional gap)`.
Incorrect: `Security gap / Functional gap`, `Security + Functional gap`, or
listing two types with no primary/secondary distinction. At most one
secondary — a gap needing more than one secondary should be split into two
entries.

### Refined User Story (Jira input only)

When the input is a Jira user story, produce a dedicated Refined User Story
section with three explicit parts:

1. **Original Jira Story** — the issue's summary/description reproduced
   verbatim, labeled `[Confirmed – Jira Requirement]`. Never edit or
   paraphrase; it's the record of what was actually asked for.
2. **Refined Story** — the same story restated for clarity using only
   `[Confirmed – Jira Requirement]` and Directly-applicable `[Confirmed –
   Knowledge Fabric: doc-id]` content. Anything added for clarity that isn't
   confirmed by either source is labeled `[Assumption]`/`[Recommendation]`
   inline — never silently folded in.
3. **Refinements supported by Knowledge Fabric** — a short list naming
   exactly which documents changed or sharpened the wording, and how.

The Refined Story must never contradict the Original Jira Story. If
Knowledge Fabric suggests different behavior, that's a Conflict, not a
silent rewrite. For free-text input, this three-part split doesn't apply —
use Requirement Understanding instead.

## Requirements Critic pass (detail for step 22)

Before assembling the BA/PO review package, the draft must survive an
adversarial self-review. This pass does not exist to eliminate Conflicts,
Gaps, or Clarification Questions — a completed package is allowed to be
dense with all three (see Failure handling). It exists to make sure they
are the *right* ones, correctly formed, and that nothing else in the draft
is quietly wrong.

### The fourteen checks

Run all fourteen against the current draft, every time, even on a short or
simple requirement:

1. **Original intent preserved?** — Does the Refined Story (or, for
   free-text input, Requirement Understanding) still say what the Original
   actually asked for? Flag any narrowing, broadening, or behavior change
   that isn't Confirmed by the input or a Directly-applicable Knowledge
   Fabric document.
2. **Any business rule unsupported?** — Does every Business Rules entry
   marked confirmed actually resolve to a confirmable source (requirement
   text, supplied AC, or Directly-applicable Knowledge Fabric — never
   repo-local evidence, never a snippet)?
3. **Assumption presented as fact?** — Does any statement read as
   established fact (no hedge, no label) but actually has no evidence
   behind it, or duplicate/contradict something already listed in
   Assumptions?
4. **Acceptance criteria testable?** — Does each AC have an observable
   pass/fail signal, or is it actually a Testability Gap wearing an AC's
   clothing?
5. **Acceptance criteria internally consistent?** — Do any two ACs
   contradict each other? (If so, that's very likely a missed Conflict —
   see check 6.)
6. **Gaps vs. Conflicts correctly separated?** — Does any "Gap" actually
   describe two disagreeing sourced statements (should be a Conflict)?
   Does any "Conflict" actually describe a mere absence (should be a Gap)?
7. **Conflicts evidence-backed?** — Does each Conflict's two sides both
   resolve to real, actually-retrieved evidence — not a hypothetical or an
   inferred disagreement?
8. **Clarification questions necessary and actionable?** — Does each
   question map to a real Ambiguity/Gap, avoid duplicating another
   question, and stay answerable in one sentence/decision?
9. **Dependencies evidence-based?** — Is every Dependency either sourced or
   explicitly labeled Assumption/Blocked — never asserted as a bare
   confirmed fact with nothing behind it?
10. **Edge cases relevant?** — Does each edge case actually connect to
    *this* requirement's process/outcomes, or is it generic boilerplate
    pasted in without a real tie to what was asked?
11. **Automation feasibility grounded?** — Does the stated candidate layer
    and rationale stay within what dependencies/process evidence actually
    supports, without drifting into invented technical detail (a specific
    endpoint, tool, or selector no evidence names)?
12. **Traceability evidence-backed?** — Does every Traceability Candidate's
    referenced requirement/business-rule/AC id actually exist elsewhere in
    this same draft, with evidence that actually resolves?
13. **Citations present for material claims?** — Sweep the whole draft
    (not just business rules/ACs/dependencies) for any statement that reads
    as material but carries neither an evidence reference nor an
    Assumption/Recommendation/Unknown label.
14. **Any tool operation claimed but not actually performed?** — Does any
    evidence entry, or any prose in the draft, claim a retrieval (a Jira
    search, a Confluence lookup, a Knowledge Fabric conflict/gap/freshness
    check) using a tool that was never actually called, isn't granted, or
    doesn't exist (see Tool inventory)? This check exists specifically to
    catch a false capability claim before it reaches a BA/PO.

### Disposition: revise, escalate, or leave unresolved

Every problem the critic finds gets exactly one disposition:

- **Revise** — a reasoning or formatting defect fixable using only what's
  already been retrieved or supplied in this run: a mislabeling, a
  misclassified Gap/Conflict, a dangling reference, a duplicate or
  unanswerable Clarification Question, an unsupported claim that should be
  downgraded. Fix it in place before finishing the draft. **Revision may
  only remove, downgrade, relabel, or reformat — it may never upgrade a
  claim's evidentiary status.** Discovering a business rule has no evidence
  is fixed by relabeling it `[Assumption]`/`[Unknown]` and adding a
  Clarification Question, never by finding or asserting evidence that
  wasn't actually retrieved.
- **Escalate** — the defect reflects something only a human can resolve:
  genuinely ambiguous original intent, a Conflict with no available
  resolution path, an acceptance criterion that can only be made testable
  by a business decision not yet made. Do not attempt to resolve it
  yourself — make sure it is already recorded as a Conflict, Gap, or
  Clarification Question (add one if the earlier steps missed it), and
  flag it for escalation (see Return contract below).
- **Unresolved** — rare: the defect can be neither fixed with what's on
  hand nor cleanly reduced to one business decision (e.g. a retrieval tool
  failed outright mid-run with no fallback path). Disclose it plainly
  rather than hiding it inside a fixed-looking draft.

**Never invent evidence to close any of the fourteen checks.** If closing a
finding would require evidence that was not actually retrieved or supplied
in this run, the finding is not closed — it is revised into an honest
`[Assumption]`/`[Unknown]`/Gap, or escalated. Fabricating a citation to
make a check pass is a worse outcome than leaving the check open.

### Return contract

Report the critic pass using exactly these fields — this is what Output
shape section 24 (Requirements Critic Findings) and
`quality_assessment.critic_status`/`findings`/`corrections`/
`unresolved_items`/`escalation_required` in
`schemas/requirement_refinement_result.schema.json` both bind to:

- **`critic_status`** — one of:
  - `clean` — all fourteen checks passed with nothing to report.
  - `revised` — one or more findings were found and fixed by revision; none
    require escalation and none are unresolved.
  - `escalation_required` — at least one finding needs a human/business
    decision.
  - `unresolved_issues_remain` — at least one finding could not be fixed or
    cleanly escalated as a single decision.

  When more than one applies, report the most severe:
  `unresolved_issues_remain` > `escalation_required` > `revised` > `clean`.
- **`findings`** — every problem actually found, each with: which of the 14
  checks it came from, a short description, and its disposition
  (`revise`/`escalate`/`unresolved`).
- **`corrections`** — one entry per finding actually fixed by revision:
  what changed and where. Every `revise`-disposition finding must appear
  here — if it couldn't actually be fixed, its disposition was wrong; call
  it `unresolved` instead.
- **`unresolved_items`** — one entry per finding with disposition
  `escalate` or `unresolved`, with why it wasn't resolved in this pass.
- **`escalation_required`** — `true` if any finding has disposition
  `escalate`, else `false`. A downstream reader can check this one field
  without walking every finding.

## Output shape

Produce output in this section order, adapting depth to what was asked but
never dropping a section without stating it doesn't apply:

0. **Jira Story Input** *(Jira input only)* — issue key, summary,
   description, issue type, status, and any other supplied fields,
   reproduced as given.
1. **Requirement Understanding / Refined User Story** — per step 2; for
   Jira input, the Original/Refined/Refinements split; for free text,
   Requirement Understanding restated with scope boundaries noted.
2. **Structural Extraction** — Actor, Trigger, Preconditions, Process,
   Expected Outcome(s) (step 4), each labeled.
3. **Business Rules** — extracted separately from Process (step 5).
4. **Retrieved Evidence** — every Knowledge Fabric document (`document_id`,
   title, source, contribution, policy applicability tier) and every
   repo-local artifact opened, plus every search that returned nothing
   (step 3).
5. **Ambiguities / Clarifications** — flagged phrases and the assumed
   reading (step 6).
6. **Assumptions** — every `[Assumption]` used anywhere, collected for
   review.
7. **Missing Information** — distinct from Ambiguities (step 7).
8. **Clarification Questions** — one per resolvable ambiguity/gap (step 8).
9. **Unknowns** — anything that couldn't be determined or phrased as a
   useful question (Core policy 12).
10. **Dependencies** — UI / API / Data / External systems (step 9).
11. **Related / Duplicate Requirements** — found via available evidence
    only, with the search-scope limitation stated explicitly (step 10).
12. **Conflicts** — four-part format (step 11).
13. **Gaps** — single primary type + optional secondary (step 7).
14. **Version Comparison** *(conditional)* (step 12).
15. **Change Impact Analysis** *(conditional; "not applicable" otherwise)*
    (step 13).
16. **Testability Assessment** (step 14).
17. **Automation Feasibility Assessment** — high level only (step 15).
18. **Edge Cases & Risks** (step 16).
19. **Acceptance Criteria** — **Confirmed Acceptance Criteria** and
    **Proposed Acceptance Criteria (requires BA/PO confirmation)**, never
    merged (step 17, Core policy 8).
20. **Test Scenarios** — Scenario ID, title, Related Acceptance Criterion,
    Type (Positive/Negative/Boundary/Security/Integration), source
    classification (step 19).
21. **Detailed Test Cases** — Test Case ID, Title, Preconditions, Test Data
    (if known), Steps, Expected Result, Related Scenario, Related AC,
    Source/Traceability — generated here when this skill's caller owns
    final test-case authorship (e.g. `ba-qa-agent`'s current mandate);
    otherwise state "deferred to Test Authoring" and stop at step 20 (step
    20 in the procedure).
22. **Existing Test/Automation Mapping** *(conditional)* (step 18).
23. **Traceability Candidates** — Requirement → Business Rule/AC → Test
    Scenario → existing test (if any) → dependency, marked "candidate"
    throughout (step 21). For a Jira input, root the chain at the issue
    (e.g. `Jira: DEMO-1 → AC-001 → TS-001 → TC-001`).
24. **Requirements Critic Findings** — `critic_status`, `findings`,
    `corrections`, `unresolved_items`, `escalation_required`, per the
    Requirements Critic pass return contract above (step 22).
25. **Validation Result** (step 23).
26. **BA/PO Review Package Summary** — open-question count, conflict count,
    gap count, confirmed-vs-proposed AC count, and the mandatory line:
    **"Approval status: NOT APPROVED — awaiting BA/PO review."**

Favor tables and numbered lists for scannability. Keep prose short — this
output is reviewed by a BA or QA engineer under time pressure, not read
end-to-end as narrative.

## Failure handling

- **`completed`** — a full package was produced, however dense with Gaps,
  Conflicts, Unknowns, and Clarification Questions. That density is a
  successful, precise outcome, not a failure.
- **`blocked`** — the procedure could not begin per Core policy 11. Still
  produce the package skeleton with a `## Blocking Reason` and `## Required
  Input` section.
- A single failed retrieval or an unresolved labeling question found during
  the critic/validation pass (steps 22–23) does not block the whole run —
  record it as a Gap/Unknown in the affected section and continue. A
  `critic_status` of `escalation_required` or `unresolved_issues_remain`
  (see Requirements Critic pass) is not itself a reason for `blocked` —
  escalation and disclosed-unresolved items are still a `completed` package;
  reserve `blocked` for Core policy 11's stop conditions only.

## Human approval

The package's terminal state is always "NOT APPROVED — awaiting BA/PO
review." It becomes an approved downstream input only through an explicit
human BA/PO action outside this skill — never through any language or
status field this skill itself produces. If a human later approves,
rejects, or resolves part of the package (e.g. picks a side in a Conflict),
that decision is external input to incorporate on a subsequent run, never
something to infer here.

## Scope boundary

This skill produces analysis and refinement artifacts only: understanding,
structure, business rules, dependencies, conflicts, gaps, questions,
criteria, scenarios, candidate traceability, and (where the caller owns
final test-case authorship) detailed test cases, all as text. It never:

- Writes automation code or executes browser/system actions.
- Creates, edits, transitions, comments on, or links a Jira issue, PR, or
  other ticket — Jira access here is `getJiraIssue`/
  `getAccessibleAtlassianResources`, read-only, nothing else.
- Approves a requirement, makes a business decision, or resolves a Conflict
  on the requirement owner's behalf.
- Claims a capability (project-wide duplicate search, automated conflict
  detection, freshness scoring, hierarchy/sprint traversal) that isn't
  backed by an actually-registered tool — see Tool inventory. Where such a
  capability is requested but unavailable, say so explicitly rather than
  performing a narrower manual approximation and presenting it as the full
  capability.

Where a request goes beyond this scope, complete the analysis portion and
name what's out of scope rather than silently expanding this skill's
boundaries to cover it.
