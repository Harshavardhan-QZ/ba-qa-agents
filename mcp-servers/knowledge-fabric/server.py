"""Knowledge Fabric MCP server.

Exposes two tools over the Model Context Protocol:

    search_knowledge(query, top_k=5)  -> ranked matches from the knowledge base
    get_context(document_id)          -> full content for one document

Runs over stdio by default:

    python server.py

Or over HTTP for remote clients:

    python server.py --transport http --port 8000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

# Allow `python server.py` from any working directory.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tools.get_context import DocumentNotFound  # noqa: E402
from tools.get_context import get_context as _get_context  # noqa: E402
from tools.knowledge_base import all_documents  # noqa: E402
from tools.search_knowledge import MAX_TOP_K  # noqa: E402
from tools.search_knowledge import search_knowledge as _search_knowledge  # noqa: E402

mcp = FastMCP(
    name="knowledge-fabric",
    instructions=(
        "Searchable internal knowledge base. Call search_knowledge first to find "
        "relevant documents and their document_id values, then call get_context "
        "with a document_id to read the full text before answering. Prefer "
        "grounding answers in retrieved content over prior knowledge."
    ),
)


@mcp.tool(
    tags={"knowledge", "search"},
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
def search_knowledge(query: str, top_k: int = 5) -> dict[str, Any]:
    """Search the knowledge base and return the best matching documents.

    Use this to discover which documents are relevant to a question. Each result
    includes a document_id, a relevance score, and a short snippet. Pass a
    document_id to get_context to read the full document.

    Args:
        query: Free-text search terms, for example "incident escalation policy".
        top_k: Maximum number of results to return (1-25). Defaults to 5.

    Returns:
        A dict with the original query, a result count, and a ranked results
        list containing document_id, title, source, tags, updated, domain,
        authority, score, matched_terms, and snippet for each hit. domain and
        authority are None for documents that don't set them.
    """
    if top_k < 1 or top_k > MAX_TOP_K:
        raise ToolError(f"top_k must be between 1 and {MAX_TOP_K}, got {top_k}.")
    return _search_knowledge(query=query, top_k=top_k)


@mcp.tool(
    tags={"knowledge", "context"},
    annotations={"readOnlyHint": True, "openWorldHint": False},
)
def get_context(document_id: str) -> dict[str, Any]:
    """Retrieve the full text and metadata of one knowledge base document.

    Call this after search_knowledge to read a complete document rather than
    just a snippet.

    Args:
        document_id: Identifier returned by search_knowledge, for example "kb-002".

    Returns:
        A dict with the document's id, title, source, tags, updated date,
        domain, authority (authority/status, e.g. "Approved - Current" or
        "Deprecated - Superseded"), version, word count, full content, and a
        list of related documents. domain/authority/version are None for
        documents that don't set them.

    Raises:
        ToolError: If no document exists with the given id.
    """
    try:
        return _get_context(document_id=document_id)
    except DocumentNotFound as exc:
        raise ToolError(str(exc)) from exc


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Knowledge Fabric MCP server")
    parser.add_argument(
        "--transport",
        default="stdio",
        choices=["stdio", "http", "sse"],
        help="Transport to serve on. Defaults to stdio for local MCP clients.",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host for http/sse.")
    parser.add_argument("--port", type=int, default=8000, help="Port for http/sse.")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    print(
        f"[knowledge-fabric] {len(all_documents())} documents loaded",
        file=sys.stderr,
    )
    if args.transport == "stdio":
        # No banner on stdio: that stream is the MCP channel's neighbour and
        # clients tend to surface anything on stderr as a warning.
        mcp.run(show_banner=False)
    else:
        mcp.run(transport=args.transport, host=args.host, port=args.port)