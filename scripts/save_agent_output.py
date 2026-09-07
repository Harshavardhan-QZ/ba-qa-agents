#!/usr/bin/env python3
"""Persist one Westfield agent's final structured output as a traceable
Markdown artifact under output/<agent>/<run-id>.md.

This is the single shared mechanism every Westfield agent (Orchestrator,
BA/QA, Automation, UI, API, Code Gen) uses to persist its output, so that
run-id minting, frontmatter formatting, directory creation, and the
no-overwrite guarantee live in one place instead of being re-implemented
per agent.

Usage:
    python scripts/save_agent_output.py \
        --agent ba-qa \
        --status completed \
        --input-type requirement \
        --content-file /path/to/body.md \
        [--run-id run-20260817-204500] \
        [--parent-run-id run-20260817-190000] \
        [--parent-output output/orchestrator/run-20260817-190000.md] \
        [--parent-output output/ba-qa/run-20260817-190000.md] \
        [--requirement-id DEMO-1] \
        [--source jira:DEMO-1] \
        [--review-status pending_ba_po_review]

- --run-id is optional. Omit it when this agent is the root of a new
  workflow execution (e.g. invoked directly by the user with no upstream
  run in play); a new one is minted from the current time. Pass it when
  continuing a workflow that already has one, so every agent in that run
  shares the same run_id.
- --parent-run-id / --parent-output are optional ("if applicable"): use
  them when this artifact builds on an upstream artifact, whether from the
  same run or an earlier one.
- --parent-output may be repeated (e.g. Code Gen consuming both a UI and an
  API findings artifact).
- --requirement-id / --source / --review-status are optional, agent-
  agnostic metadata fields used by the Requirements Refinement capability
  (ba-qa-agent + the requirement-analysis skill) so a refinement package's
  requirement identity, input source, and BA/PO review gate are recorded in
  frontmatter, not buried in prose. Any agent may pass them when they apply;
  omit them when they don't (e.g. Automation/UI/API/Code Gen artifacts have
  no independent review gate of their own). --review-status is restricted
  to REVIEW_STATUS_VALUES below — there is deliberately no "approved" value
  anywhere in that set: approval is a human act that happens outside this
  script and outside every artifact it writes.

On success, prints exactly two lines to stdout:
    <path to the written artifact>
    RUN_ID=<the run-id used>
so the calling agent can relay both the artifact path and the run_id to any
agent it delegates to next.

Never overwrites an existing artifact and never deletes anything.
"""
import argparse
import datetime
import os
import re
import sys

AGENT_DIRS = {
    "orchestrator": "orchestrator",
    "ba-qa": "ba-qa",
    "automation": "automation",
    "ui": "ui",
    "api": "api",
    "code-gen": "code-gen",
}

RUN_ID_RE = re.compile(r"^run-[A-Za-z0-9_-]+$")

# Mirrors ReviewStatusValue in schemas/requirement_refinement_result.schema.json.
# No "approved" value exists in this set on purpose — a Requirements
# Refinement package can only ever be persisted in a not-yet-approved state;
# an actual approval is a human act recorded outside this mechanism.
REVIEW_STATUS_VALUES = (
    "pending_ba_po_review",
    "blocked_missing_input",
    "requires_conflict_resolution",
)


def mint_run_id(output_root):
    now = datetime.datetime.now()
    base = "run-" + now.strftime("%Y%m%d-%H%M%S")
    candidate = base
    suffix = 1
    while any(
        os.path.exists(os.path.join(output_root, d, candidate + ".md"))
        for d in AGENT_DIRS.values()
    ):
        candidate = f"{base}-{suffix}"
        suffix += 1
    return candidate


def build_frontmatter(
    run_id,
    agent,
    input_type,
    status,
    parent_run_id,
    parent_outputs,
    requirement_id=None,
    source=None,
    review_status=None,
):
    timestamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
    lines = [
        "---",
        f"run_id: {run_id}",
        f"agent: {agent}",
        f"timestamp: {timestamp}",
        f"input_type: {input_type}",
    ]
    if requirement_id:
        lines.append(f"requirement_id: {requirement_id}")
    if source:
        lines.append(f"source: {source}")
    if parent_run_id:
        lines.append(f"parent_run_id: {parent_run_id}")
    if parent_outputs:
        lines.append("parent_output:")
        for po in parent_outputs:
            lines.append(f"  - {po}")
    lines.append(f"status: {status}")
    if review_status:
        lines.append(f"review_status: {review_status}")
    lines.append("---")
    lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--agent", required=True, choices=sorted(AGENT_DIRS.keys()))
    parser.add_argument("--status", required=True, choices=["completed", "blocked", "failed"])
    parser.add_argument("--input-type", required=True)
    parser.add_argument("--content-file", required=True, help="Path to a file containing the agent's Markdown body (no frontmatter).")
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--parent-run-id", default=None)
    parser.add_argument("--parent-output", action="append", default=[])
    parser.add_argument("--output-root", default="output")
    parser.add_argument(
        "--requirement-id",
        default=None,
        help="Stable requirement identifier (e.g. a Jira issue key) this artifact refines, when applicable.",
    )
    parser.add_argument(
        "--source",
        default=None,
        help="Where the requirement identity came from, e.g. 'jira:DEMO-1', 'free-text-requirement', 'brd-excerpt'.",
    )
    parser.add_argument(
        "--review-status",
        default=None,
        choices=REVIEW_STATUS_VALUES,
        help="BA/PO review gate for a Requirements Refinement package. No 'approved' choice exists — "
        "approval is never recorded by this script.",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.content_file):
        print(f"ERROR: content file not found: {args.content_file}", file=sys.stderr)
        sys.exit(1)

    run_id = args.run_id or mint_run_id(args.output_root)
    if not RUN_ID_RE.match(run_id):
        print(f"ERROR: run-id must match 'run-<alnum/-/_>': {run_id}", file=sys.stderr)
        sys.exit(1)

    subdir = AGENT_DIRS[args.agent]
    target_dir = os.path.join(args.output_root, subdir)
    os.makedirs(target_dir, exist_ok=True)
    target_path = os.path.join(target_dir, f"{run_id}.md")

    if os.path.exists(target_path):
        print(
            f"ERROR: refusing to overwrite existing artifact: {target_path}. "
            "Use a different --run-id (or omit --run-id to mint a fresh one).",
            file=sys.stderr,
        )
        sys.exit(1)

    with open(args.content_file, "r", encoding="utf-8") as f:
        body = f.read()

    header = build_frontmatter(
        run_id,
        args.agent,
        args.input_type,
        args.status,
        args.parent_run_id,
        args.parent_output,
        requirement_id=args.requirement_id,
        source=args.source,
        review_status=args.review_status,
    )

    with open(target_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(header)
        f.write(body if body.endswith("\n") else body + "\n")

    print(target_path)
    print(f"RUN_ID={run_id}")


if __name__ == "__main__":
    main()
