# Westfield AI Engineering Platform

Claude Code as the orchestration layer for an agentic requirement-to-automation
pipeline: a Jira issue or free-text requirement goes in, and a traceable chain
of BA/QA analysis, automation planning, and (optionally) generated test code
comes out — every claim in that chain grounded in evidence and explicitly
labeled `[Confirmed]` / `[Assumption]` / `[Unknown]`, never invented.

This repo is the platform definition itself: Claude Code subagents (in
[.claude/agents/](.claude/agents/)), a reusable procedure skill (in
[.claude/skills/](.claude/skills/)), a local MCP server for knowledge
retrieval, and the schemas/scripts/tests that keep the pipeline's output
contract honest.

## How it fits together

```
User request
     │
     ▼
westfield-orchestrator   — routes the request, never analyzes itself
     │
     ├──▶ ba-qa-agent          — Requirements Refinement (Jira / free-text → BA/PO review package)
     │        follows the requirement-analysis skill procedure
     │
     └──▶ automation-agent     — decides UI vs API vs manual, delegates, assembles a plan
              ├──▶ ui-agent      — Playwright-driven UI exploration → findings
              ├──▶ api-agent     — API/endpoint exploration → findings
              └──▶ code-gen-agent — turns findings into automation scripts
```

Every agent talks to enterprise systems only through MCP tools (per
[CLAUDE.md](CLAUDE.md)) — never directly — and every generated artifact is
saved with [scripts/save_agent_output.py](scripts/save_agent_output.py) under
`output/<agent>/run-<timestamp>.md`, carrying a `run_id` and, where
applicable, a `parent_run_id`/`parent_output` chain back to the artifacts it
was built from.

## Repository layout

| Path | What it is |
|---|---|
| [CLAUDE.md](CLAUDE.md) | Platform charter: the agent list, the MCP-first rule, read/write permission policy, traceability requirement. |
| [.claude/agents/](.claude/agents/) | Subagent definitions (see status table below). |
| [.claude/skills/requirement-analysis/SKILL.md](.claude/skills/requirement-analysis/SKILL.md) | The full Requirements Refinement procedure `ba-qa-agent` follows — evidence labeling rules, conflict/gap formats, the 14-point critic pass, output shape. |
| [.mcp.json](.mcp.json) | Registers the `knowledge-fabric` MCP server for this project (stdio, `python mcp-servers/knowledge-fabric/server.py`). |
| [mcp-servers/knowledge-fabric/](mcp-servers/knowledge-fabric/) | **Working** MCP server exposing `search_knowledge` / `get_context` over an in-memory mock document store. |
| [mcp-servers/jira/tools.py](mcp-servers/jira/tools.py) | **Reference only** — typed stubs documenting the Jira/Confluence tools the *account-level* Atlassian Rovo connector exposes. Not a server; nothing here is executable. |
| [mcp-servers/{azure-devops,github,playwright,testrail}/](mcp-servers/) | **Empty placeholders** — reserved for future MCP servers per CLAUDE.md's system list; not implemented. |
| [schemas/requirement_refinement_result.schema.json](schemas/requirement_refinement_result.schema.json) | Draft 2020-12 JSON Schema for the structured `RequirementRefinementResult` contract (not yet wired into any agent's actual output — see Leftover work). |
| [scripts/save_agent_output.py](scripts/save_agent_output.py) | Shared CLI every agent uses to persist a Markdown artifact under `output/` with consistent frontmatter and a minted/propagated `run_id`. |
| [scripts/validate_requirement_refinement_result.py](scripts/validate_requirement_refinement_result.py) | Standalone (stdlib-only) validator for a `RequirementRefinementResult` JSON document — cross-field and evidence-integrity checks the schema alone can't express. |
| [tests/](tests/) | Pytest suite (see Testing below — two files are still empty stubs). |
| `output/` | Generated run artifacts (git-ignored — see below). |
| `ba-qa-output.md` | An example BA/QA refinement package left at the repo root from a prior run (git-ignored). |

### Agent status

| Agent | State |
|---|---|
| `westfield-orchestrator` | Implemented |
| `ba-qa-agent` | Implemented — the most fully-specified agent; see the skill doc above |
| `automation-agent` | Implemented |
| `ui-agent` | Implemented (needs the Playwright MCP server to actually browse — see Leftover work) |
| `api-agent` | Implemented |
| `code-gen-agent` | Implemented |
| `analytics-agent`, `devops-agent`, `release-agent` | **Empty files** — named in CLAUDE.md's platform list but not yet written |

## Prerequisites

- **Python 3.10+**
- **Claude Code** (this repo is built to run inside it — the agents are
  Claude Code subagents, not a standalone application)
- **pip** for installing the Python dependencies below
- A GitHub/Jira/etc. login is *not* required to run the Knowledge Fabric
  server locally; it *is* required for `ba-qa-agent`'s Jira retrieval, which
  goes through your Claude Code session's own Atlassian connector, not
  anything installed by this repo

## Getting started

```bash
git clone <this-repo-url>
cd westfiled-claude

# Install the platform's own dependency (fastmcp, for the knowledge-fabric server)
pip install -r requirements.txt

# Open the folder in Claude Code
claude
```

Claude Code auto-loads [.mcp.json](.mcp.json) and starts the `knowledge-fabric`
MCP server for you (`python mcp-servers/knowledge-fabric/server.py`, over
stdio) — there is nothing extra to run by hand. You can sanity-check the
server standalone first:

```bash
python mcp-servers/knowledge-fabric/server.py
# stderr should print: [knowledge-fabric] <N> documents loaded
```

Then, inside Claude Code:

- **Refine a requirement:** *"Refine DEMO-1"* or paste a requirement/BRD
  excerpt and ask for refinement → routes to `ba-qa-agent`.
- **Plan automation from existing test cases:** *"Here are the test cases,
  plan the automation"* → routes to `automation-agent`, which fans out to
  `ui-agent`/`api-agent`.
- **Generate a script from ready findings:** *"Generate the Playwright test
  for this test case"* → `code-gen-agent`.
- **Run the whole pipeline:** *"Take this requirement all the way to
  automation scripts"* → `westfield-orchestrator` coordinates all of the
  above and threads the `run_id`/`parent_output` chain through automatically.

Jira retrieval (`ba-qa-agent`) uses the Atlassian Rovo MCP connector that's
already attached at the Claude Code account level in this environment — no
separate Jira credentials/config live in this repo. If that connector isn't
available in your environment, `ba-qa-agent` still works from a pasted
Jira story or free-text requirement; it just discloses the missing capability
rather than fabricating a Jira lookup (see `ba-qa-output.md` for a worked
example of exactly that disclosure).

## Testing

```bash
pip install pytest
pytest tests/ -v
```

| Test file | Status |
|---|---|
| [tests/test_knowledge_fabric.py](tests/test_knowledge_fabric.py) | Real tests against `search_knowledge`/`get_context` and the mock document store. |
| [tests/api/test_password_reset.py](tests/api/test_password_reset.py) | Example generated API automation script (pytest + requests) for a password-reset flow — sample output of the `api-agent` → `code-gen-agent` path, not a test of this repo's own code. |
| [tests/ui/password-reset.spec.ts](tests/ui/password-reset.spec.ts) | Example generated UI automation script (Playwright + TypeScript) for the same flow — same caveat; there's no `package.json`/Playwright config in the repo yet to actually run it (see Leftover work). |
| [tests/test_agents.py](tests/test_agents.py), [tests/test_mcp.py](tests/test_mcp.py) | **Empty stubs** — no tests written yet. |

## Leftover work / known gaps

This is a snapshot of what's intentionally unfinished, so a fresh contributor
doesn't mistake a placeholder for a bug:

- **`analytics-agent.md`, `devops-agent.md`, `release-agent.md` are empty.**
  CLAUDE.md's platform list names Analytics & Quality, DevOps, and Release &
  Operations agents; none have been authored yet.
- **`mcp-servers/{azure-devops,github,playwright,testrail}/` are empty
  directories.** CLAUDE.md calls for MCP tool access to these systems;
  `ui-agent` already assumes a Playwright MCP server is available in the
  Claude Code session (it's an account/global one, not one hosted here),
  and no project-local server exists for any of the four.
- **Knowledge Fabric is a mock.** `mcp-servers/knowledge-fabric/tools/knowledge_base.py`
  is an in-memory, hand-authored sample store (see its `SAMPLE / MOCK DATA
  NOTICE`), explicitly documented as a placeholder to be swapped for a real
  backend (vector DB, Confluence export, etc.) behind the same
  `all_documents()`/`get_document()` interface.
- **`mcp-servers/jira/tools.py` is a reference stub, not a server.** It
  documents the Atlassian Rovo connector's tool surface for readability/
  grep-ability; every function body raises `NotImplementedError` by design.
  Real Jira calls happen through Claude Code's own MCP tool-call mechanism.
- **`schemas/requirement_refinement_result.schema.json` and
  `scripts/validate_requirement_refinement_result.py` aren't wired up yet.**
  The JSON contract and its validator exist and are self-consistent, but no
  agent currently emits a `RequirementRefinementResult` JSON document for
  them to validate — `ba-qa-agent` currently produces the Markdown package
  described in the `requirement-analysis` skill instead. Wiring an agent to
  emit + validate this JSON is a separate, not-yet-started task.
- **`tests/test_agents.py` and `tests/test_mcp.py` are empty.** No
  automated coverage yet for agent behavior or the MCP server's tool
  contracts beyond `tests/test_knowledge_fabric.py`'s direct-call tests.
- **No Playwright project scaffolding.** `tests/ui/password-reset.spec.ts`
  is a sample generated script; there's no `package.json`,
  `playwright.config.ts`, or installed browsers in this repo to run it.
- **`output/` and `ba-qa-output.md` are git-ignored.** They're run
  artifacts from using the platform locally, not source — see
  [.gitignore](.gitignore). Don't expect them to survive a fresh clone.

## Traceability & governance rules (from CLAUDE.md)

- Agents must use MCP tools to reach enterprise systems — never call an
  external API/service directly.
- Read operations follow existing permissions; write operations require
  explicit approval (no agent in this repo is granted Jira/Confluence write
  access today — see `mcp-servers/jira/tools.py`'s `WRITE_TOOLS` set).
- Every generated artifact must trace back to its source requirement — this
  is why `scripts/save_agent_output.py` threads `run_id`/`parent_run_id`/
  `parent_output` through the whole pipeline.
- Knowledge conflicts are surfaced, never silently resolved — see the
  four-part Conflict format in the `requirement-analysis` skill.
