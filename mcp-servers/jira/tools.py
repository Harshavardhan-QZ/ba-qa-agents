"""Reference interface for the Atlassian (Jira + Confluence) MCP tools
available to agents in this Claude Code session.

IMPORTANT — what this file is, and is not:

- These tools are NOT provided by this repository's own `.mcp.json`
  (which only registers the `knowledge-fabric` server). They come from a
  separate, account-level "claude.ai Atlassian Rovo" MCP connector
  (`mcp__claude_ai_Atlassian_Rovo__*`) that is already live in this session,
  the same way the Playwright MCP tools are available without a project
  `.mcp.json` entry.
- As actually surfaced to this session, this connector exposes read-only
  Jira/Confluence/Teamwork-Graph retrieval tools only — none of the
  write/mutating tools documented below (create/edit/comment/worklog/
  transition/link) have been observed as callable tools in this session.
  They are kept below as a schema-accurate reference in case a future
  session's connector grants them, but no Westfield agent should assume
  any of them are actually callable without first confirming that via its
  own session's tool list.
- This module does NOT contain the real backend implementation of these
  tools. That implementation runs on Atlassian's / claude.ai's
  infrastructure, and is not something accessible to or reproducible by
  this codebase. Every function below is a schema-accurate STUB: its
  signature and docstring mirror the tool's actual JSON Schema exactly as
  exposed to this session, but the body only raises `NotImplementedError`.
- Real execution happens exclusively through the MCP tool-call mechanism
  (i.e. an agent invoking `mcp__claude_ai_Atlassian_Rovo__<name>` directly),
  not by calling anything in this file. Treat this module as a typed,
  greppable reference/catalog of what's available — not a working client.
- No tool was executed to produce this file. It was written by inspecting
  the tool schemas surfaced to this session (via ToolSearch) and, for a
  few tools, one real prior read-only call (`getJiraIssue`,
  `getAccessibleAtlassianResources`) made in an earlier task, in this
  same conversation.

Every one of these tools requires a `cloudId` (except `fetch`, which
derives it from the ARI, and `atlassianUserInfo`/`search`, which need
none). Resolve `cloudId` once via `get_accessible_atlassian_resources()`
and reuse it.
"""

from __future__ import annotations

from typing import Any, Literal


# ---------------------------------------------------------------------------
# Shared / cross-cutting tools (used by both Jira and Confluence workflows)
# ---------------------------------------------------------------------------


def get_accessible_atlassian_resources() -> list[dict[str, Any]]:
    """mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources

    Get cloudId to make tool calls. When a link is provided (e.g.
    https://site.atlassian.net/*), try passing the site hostname (e.g.
    site.atlassian.net) as cloudId to other tools first; if that fails,
    use this tool to list accessible resources.

    Parameters: none.
    Returns: list of {id, url, name, scopes, avatarUrl} per accessible site.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def search(query: str, cloudId: str | None = None) -> Any:
    """mcp__claude_ai_Atlassian_Rovo__search

    Search Jira and Confluence using Rovo Search. ALWAYS use this tool to
    search for Jira and Confluence content unless the word CQL or JQL is
    used in the context.

    Args:
        query: The search query to use for Rovo Search.
        cloudId: Not needed for this tool — cloudId is derived from the
            access token automatically.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def fetch(id: str, cloudId: str | None = None) -> Any:
    """mcp__claude_ai_Atlassian_Rovo__fetch

    Get details of a Jira issue or Confluence page by ARI (Atlassian
    Resource Identifier). If the id is not an ARI, use a different tool to
    fetch the content.

    Args:
        id: ARI from search results, e.g.
            "ari:cloud:jira:cloudId:issue/10107" or
            "ari:cloud:confluence:cloudId:page/123456789".
        cloudId: Not needed — extracted from the ARI automatically.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def atlassian_user_info() -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__atlassianUserInfo

    Get current user info. Parameters: none.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


# ---------------------------------------------------------------------------
# Jira tools
# ---------------------------------------------------------------------------


def get_jira_issue(
    cloudId: str,
    issueIdOrKey: str,
    fields: list[str] | None = None,
    fieldsByKeys: bool | None = None,
    expand: str | None = None,
    properties: list[str] | None = None,
    responseContentFormat: Literal["markdown", "adf"] | None = None,
    updateHistory: bool | None = None,
    failFast: bool | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getJiraIssue — Get issue details.

    Args:
        cloudId: Cloud ID (UUID or site URL).
        issueIdOrKey: Issue ID or key (e.g. "PROJ-123" or "10000").
        fields: Fields to return. Defaults to summary, description, status,
            issuetype, priority, labels, components, assignee, reporter,
            created, updated, resolution, project. Pass ["*all"] for every
            field (including custom fields, e.g. an acceptance-criteria
            custom field). Include "comment" to fetch comments.
        fieldsByKeys: Whether `fields` are referenced by key instead of ID.
        expand: Additional details to expand (e.g. "renderedFields,names").
        properties: Issue property keys to include.
        responseContentFormat: "markdown" (simplified) or "adf" (full
            Atlassian Document Format JSON).
        updateHistory: Whether to update the user's recently-viewed history.
        failFast: Fail fast instead of partially returning data when some
            fields can't be loaded.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def search_jira_issues_using_jql(
    cloudId: str,
    jql: str,
    fields: list[str] | None = None,
    maxResults: int | None = None,
    nextPageToken: str | None = None,
    responseContentFormat: Literal["markdown", "adf"] | None = None,
    searchResultMode: Literal["issues", "count", "all"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql

    Search issues with JQL. Total counts only when explicitly requested
    (searchResultMode="count" or "all").

    Args:
        cloudId: Cloud ID (UUID or site URL).
        jql: JQL query string.
        fields: Same defaulting rules as get_jira_issue.
        maxResults: 50-100.
        nextPageToken: Pagination token.
        responseContentFormat: "markdown" or "adf".
        searchResultMode: "issues" (default), "count", or "all".
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def create_jira_issue(
    cloudId: str,
    projectKey: str,
    issueTypeName: str,
    summary: str | None = None,
    description: str | dict[str, Any] | None = None,
    assignee_account_id: str | None = None,
    parent: str | None = None,
    transition: dict[str, str] | None = None,
    additional_fields: dict[str, Any] | None = None,
    contentFormat: Literal["markdown", "adf"] | None = None,
    responseContentFormat: Literal["markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__createJiraIssue

    Create a Jira issue. WRITE / MUTATING — not granted to any agent by
    default in this platform; see the module docstring.

    Args:
        cloudId: Cloud ID (UUID or site URL).
        projectKey: Project key.
        issueTypeName: Type (Task, Bug, Story, ...).
        summary: Issue summary.
        description: Plain text/Markdown string, or an ADF document object.
        assignee_account_id: Assignee account ID.
        parent: Parent issue key, for subtasks.
        transition: {"id": "<transitionId>"} to apply during creation.
        additional_fields: Any field without its own parameter (priority,
            labels, components, fixVersions, custom fields, ...).
        contentFormat / responseContentFormat: "markdown" or "adf".
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def edit_jira_issue(
    cloudId: str,
    issueIdOrKey: str,
    fields: dict[str, Any],
    contentFormat: Literal["markdown", "adf"] | None = None,
    responseContentFormat: Literal["markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__editJiraIssue

    Update an issue's fields. WRITE / MUTATING — not granted to any agent
    by default in this platform; see the module docstring.

    Args:
        cloudId: Cloud ID (UUID or site URL).
        issueIdOrKey: Issue ID or key.
        fields: Fields to set, keyed by field name or customfield_* ID.
            Pass an explicit null to clear a field.
        contentFormat / responseContentFormat: "markdown" or "adf".
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def add_comment_to_jira_issue(
    cloudId: str,
    issueIdOrKey: str,
    commentBody: str,
    commentId: str | None = None,
    commentVisibility: dict[str, str] | None = None,
    contentFormat: Literal["markdown", "adf"] | None = None,
    responseContentFormat: Literal["markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__addCommentToJiraIssue

    Add or update a comment on a Jira issue. WRITE / MUTATING — not granted
    to any agent by default in this platform; see the module docstring.

    Args:
        cloudId: Cloud ID (UUID or site URL).
        issueIdOrKey: Issue ID or key.
        commentBody: Comment body.
        commentId: ID of an existing comment to update; omit to add new.
        commentVisibility: {"type": "group"|"role", "value": "<name>"}.
        contentFormat / responseContentFormat: "markdown" or "adf".
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def add_worklog_to_jira_issue(
    cloudId: str,
    issueIdOrKey: str,
    timeSpent: str,
    commentBody: str | None = None,
    started: str | None = None,
    worklogId: str | None = None,
    visibility: dict[str, str] | None = None,
    contentFormat: Literal["markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__addWorklogToJiraIssue

    Add or update a worklog on a Jira issue. WRITE / MUTATING — not
    granted to any agent by default in this platform.

    Args:
        cloudId: Cloud ID (UUID or site URL).
        issueIdOrKey: Issue ID or key.
        timeSpent: e.g. "2h", "30m", "4d". Required for new worklogs.
        commentBody: Worklog comment.
        started: ISO 8601 date-time; defaults to now if omitted.
        worklogId: Existing worklog ID to update, if updating.
        visibility: {"type": "group"|"role", "value": "<name>"}.
        contentFormat: "markdown" or "adf".
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_jira_issue_remote_issue_links(
    cloudId: str,
    issueIdOrKey: str,
    globalId: str | None = None,
) -> list[dict[str, Any]]:
    """mcp__claude_ai_Atlassian_Rovo__getJiraIssueRemoteIssueLinks — Get remote links."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_jira_issue_type_meta_with_fields(
    cloudId: str,
    projectIdOrKey: str,
    issueTypeId: str,
    requiredFieldsOnly: bool | None = None,
    maxResults: int | None = None,
    startAt: int | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getJiraIssueTypeMetaWithFields — Get field metadata.

    requiredFieldsOnly defaults to True (only fields required to create an
    issue of this type); set False for all available fields.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_jira_project_issue_types_metadata(
    cloudId: str,
    projectIdOrKey: str,
    maxResults: int | None = None,
    startAt: int | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata — Get issue types."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_transitions_for_jira_issue(
    cloudId: str,
    issueIdOrKey: str,
    transitionId: str | None = None,
    expand: str | None = None,
    includeUnavailableTransitions: bool | None = None,
    skipRemoteOnlyCondition: bool | None = None,
    sortByOpsBarAndStatus: bool | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getTransitionsForJiraIssue — Get transitions."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def transition_jira_issue(
    cloudId: str,
    issueIdOrKey: str,
    transition: dict[str, str],
    fields: dict[str, Any] | None = None,
    update: dict[str, list[dict[str, Any]]] | None = None,
    historyMetadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__transitionJiraIssue — Transition issue status.

    WRITE / MUTATING — not granted to any agent by default in this
    platform; see the module docstring.

    Args:
        transition: {"id": "<transitionId>"} (use
            get_transitions_for_jira_issue to find valid IDs).
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def create_issue_link(
    cloudId: str,
    inwardIssue: str,
    outwardIssue: str,
    type: str,
    comment: str | None = None,
    contentFormat: Literal["markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__createIssueLink

    Create a link between two Jira issues. WRITE / MUTATING — not granted
    to any agent by default in this platform.

    For directional link types (e.g. "Blocks"): inwardIssue = issue that
    blocks, outwardIssue = issue that is blocked.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_issue_link_types(cloudId: str) -> list[dict[str, Any]]:
    """mcp__claude_ai_Atlassian_Rovo__getIssueLinkTypes

    Get available Jira issue link types (e.g. Blocks, Duplicate, Clones,
    Relates).
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_visible_jira_projects(
    cloudId: str,
    action: Literal["view", "browse", "edit", "create"] | None = None,
    searchString: str | None = None,
    expandIssueTypes: bool | None = None,
    maxResults: int | None = None,
    startAt: int | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects — Get projects.

    `action` defaults to "create" (projects the user could create issues
    in); pass "view"/"browse"/"edit" for other permission checks.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def lookup_jira_account_id(cloudId: str, searchString: str) -> list[dict[str, Any]]:
    """mcp__claude_ai_Atlassian_Rovo__lookupJiraAccountId — Lookup user IDs."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


# ---------------------------------------------------------------------------
# Confluence tools
# ---------------------------------------------------------------------------


def get_confluence_spaces(
    cloudId: str,
    ids: str | list[int] | None = None,
    keys: str | list[str] | None = None,
    type: Literal["global", "personal"] | None = None,
    status: Literal["current", "archived"] | None = None,
    labels: str | list[str] | None = None,
    favourite: bool | None = None,
    favoritedBy: str | None = None,
    expand: str | list[str] | None = None,
    limit: int | None = None,
    start: int | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getConfluenceSpaces — Get spaces."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_pages_in_confluence_space(
    cloudId: str,
    spaceId: str,
    title: str | None = None,
    status: Literal["current", "archived", "deleted", "trashed"] | None = None,
    sort: str | None = None,
    contentType: Literal["page", "blog"] | None = None,
    contentFormat: Literal["html", "markdown", "adf"] | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getPagesInConfluenceSpace — Get pages or blog posts in a space."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_confluence_page(
    cloudId: str,
    pageId: str,
    contentType: Literal["page", "blog"] | None = None,
    contentFormat: Literal["html", "markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getConfluencePage

    Get a Confluence page or blog post by ID (or tiny-link ID from a
    /wiki/x/ URL), including body content.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_confluence_page_descendants(
    cloudId: str,
    pageId: str,
    depth: int | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getConfluencePageDescendants — Get child pages of specified page."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_confluence_page_footer_comments(
    cloudId: str,
    pageId: str,
    contentType: Literal["page", "blog"] | None = None,
    status: Literal["current", "archived", "trashed", "deleted", "historical", "draft"] | None = None,
    includeReplies: bool | None = None,
    repliesPerComment: int | None = None,
    sort: Literal["id", "-id", "created-date", "-created-date"] | None = None,
    contentFormat: Literal["markdown", "adf"] | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getConfluencePageFooterComments — Get footer comments for a page or blog post."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_confluence_page_inline_comments(
    cloudId: str,
    pageId: str,
    contentType: Literal["page", "blog"] | None = None,
    status: Literal["current", "archived", "trashed", "deleted", "historical", "draft"] | None = None,
    resolutionStatus: Literal["resolved", "open", "dangling", "reopened"] | None = None,
    includeReplies: bool | None = None,
    repliesPerComment: int | None = None,
    sort: Literal["id", "-id", "created-date", "-created-date"] | None = None,
    contentFormat: Literal["markdown", "adf"] | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getConfluencePageInlineComments — Get inline comments for a page or blog post."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def get_confluence_comment_children(
    cloudId: str,
    commentId: str,
    commentType: Literal["footer", "inline"],
    sort: Literal["id", "-id", "created-date", "-created-date"] | None = None,
    contentFormat: Literal["markdown", "adf"] | None = None,
    limit: int | None = None,
    cursor: str | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__getConfluenceCommentChildren — Get reply (child) comments for a comment."""
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def create_confluence_page(
    cloudId: str,
    spaceId: str,
    body: str,
    title: str | None = None,
    parentId: str | None = None,
    status: Literal["current", "draft"] | None = None,
    contentType: Literal["page", "blog"] | None = None,
    subtype: Literal["live"] | None = None,
    isPrivate: bool | None = None,
    contentFormat: Literal["html", "markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__createConfluencePage

    Create a Confluence page or blog post. WRITE / MUTATING — not granted
    to any agent by default in this platform.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def update_confluence_page(
    cloudId: str,
    pageId: str,
    body: str,
    title: str | None = None,
    parentId: str | None = None,
    spaceId: str | None = None,
    status: Literal["current", "draft"] | None = None,
    contentType: Literal["page", "blog"] | None = None,
    versionMessage: str | None = None,
    includeBody: bool | None = None,
    contentFormat: Literal["html", "markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__updateConfluencePage

    Update a Confluence page or blog post. WRITE / MUTATING — not granted
    to any agent by default in this platform.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def create_confluence_footer_comment(
    cloudId: str,
    body: str,
    pageId: str | None = None,
    parentCommentId: str | None = None,
    contentType: Literal["page", "blog"] | None = None,
    attachmentId: str | None = None,
    customContentId: str | None = None,
    contentFormat: Literal["html", "markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__createConfluenceFooterComment

    Create a footer comment on a page or blog post. WRITE / MUTATING —
    not granted to any agent by default in this platform.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def create_confluence_inline_comment(
    cloudId: str,
    body: str,
    pageId: str | None = None,
    parentCommentId: str | None = None,
    inlineCommentProperties: dict[str, Any] | None = None,
    contentType: Literal["page", "blog"] | None = None,
    contentFormat: Literal["html", "markdown", "adf"] | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__createConfluenceInlineComment

    Create an inline comment on specific text in a page or blog post.
    WRITE / MUTATING — not granted to any agent by default in this
    platform. For top-level comments, provide pageId +
    inlineCommentProperties (textSelection, textSelectionMatchCount,
    textSelectionMatchIndex) after fetching the page to locate the exact
    text. For replies, provide parentCommentId only.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


def search_confluence_using_cql(
    cloudId: str,
    cql: str,
    cqlcontext: str | None = None,
    expand: str | None = None,
    limit: int | None = None,
    cursor: str | None = None,
    next: bool | None = None,
    prev: bool | None = None,
) -> dict[str, Any]:
    """mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql

    Search Confluence content (pages, blog posts, comments, attachments)
    using CQL (Confluence Query Language) — not interchangeable with JQL.
    """
    raise NotImplementedError("Real execution happens via the MCP tool call, not this stub.")


# ---------------------------------------------------------------------------
# Registry — maps the real MCP tool name to its stub above, for lookup only.
# ---------------------------------------------------------------------------

SHARED_TOOLS: dict[str, Any] = {
    "mcp__claude_ai_Atlassian_Rovo__getAccessibleAtlassianResources": get_accessible_atlassian_resources,
    "mcp__claude_ai_Atlassian_Rovo__search": search,
    "mcp__claude_ai_Atlassian_Rovo__fetch": fetch,
    "mcp__claude_ai_Atlassian_Rovo__atlassianUserInfo": atlassian_user_info,
}

JIRA_TOOLS: dict[str, Any] = {
    "mcp__claude_ai_Atlassian_Rovo__getJiraIssue": get_jira_issue,
    "mcp__claude_ai_Atlassian_Rovo__searchJiraIssuesUsingJql": search_jira_issues_using_jql,
    "mcp__claude_ai_Atlassian_Rovo__createJiraIssue": create_jira_issue,
    "mcp__claude_ai_Atlassian_Rovo__editJiraIssue": edit_jira_issue,
    "mcp__claude_ai_Atlassian_Rovo__addCommentToJiraIssue": add_comment_to_jira_issue,
    "mcp__claude_ai_Atlassian_Rovo__addWorklogToJiraIssue": add_worklog_to_jira_issue,
    "mcp__claude_ai_Atlassian_Rovo__getJiraIssueRemoteIssueLinks": get_jira_issue_remote_issue_links,
    "mcp__claude_ai_Atlassian_Rovo__getJiraIssueTypeMetaWithFields": get_jira_issue_type_meta_with_fields,
    "mcp__claude_ai_Atlassian_Rovo__getJiraProjectIssueTypesMetadata": get_jira_project_issue_types_metadata,
    "mcp__claude_ai_Atlassian_Rovo__getTransitionsForJiraIssue": get_transitions_for_jira_issue,
    "mcp__claude_ai_Atlassian_Rovo__transitionJiraIssue": transition_jira_issue,
    "mcp__claude_ai_Atlassian_Rovo__createIssueLink": create_issue_link,
    "mcp__claude_ai_Atlassian_Rovo__getIssueLinkTypes": get_issue_link_types,
    "mcp__claude_ai_Atlassian_Rovo__getVisibleJiraProjects": get_visible_jira_projects,
    "mcp__claude_ai_Atlassian_Rovo__lookupJiraAccountId": lookup_jira_account_id,
}

CONFLUENCE_TOOLS: dict[str, Any] = {
    "mcp__claude_ai_Atlassian_Rovo__getConfluenceSpaces": get_confluence_spaces,
    "mcp__claude_ai_Atlassian_Rovo__getPagesInConfluenceSpace": get_pages_in_confluence_space,
    "mcp__claude_ai_Atlassian_Rovo__getConfluencePage": get_confluence_page,
    "mcp__claude_ai_Atlassian_Rovo__getConfluencePageDescendants": get_confluence_page_descendants,
    "mcp__claude_ai_Atlassian_Rovo__getConfluencePageFooterComments": get_confluence_page_footer_comments,
    "mcp__claude_ai_Atlassian_Rovo__getConfluencePageInlineComments": get_confluence_page_inline_comments,
    "mcp__claude_ai_Atlassian_Rovo__getConfluenceCommentChildren": get_confluence_comment_children,
    "mcp__claude_ai_Atlassian_Rovo__createConfluencePage": create_confluence_page,
    "mcp__claude_ai_Atlassian_Rovo__updateConfluencePage": update_confluence_page,
    "mcp__claude_ai_Atlassian_Rovo__createConfluenceFooterComment": create_confluence_footer_comment,
    "mcp__claude_ai_Atlassian_Rovo__createConfluenceInlineComment": create_confluence_inline_comment,
    "mcp__claude_ai_Atlassian_Rovo__searchConfluenceUsingCql": search_confluence_using_cql,
}

# Tools that mutate Atlassian state (Jira issues or Confluence pages/comments).
# No Westfield agent is granted these by default — retrieval only.
WRITE_TOOLS = {
    "mcp__claude_ai_Atlassian_Rovo__createJiraIssue",
    "mcp__claude_ai_Atlassian_Rovo__editJiraIssue",
    "mcp__claude_ai_Atlassian_Rovo__addCommentToJiraIssue",
    "mcp__claude_ai_Atlassian_Rovo__addWorklogToJiraIssue",
    "mcp__claude_ai_Atlassian_Rovo__transitionJiraIssue",
    "mcp__claude_ai_Atlassian_Rovo__createIssueLink",
    "mcp__claude_ai_Atlassian_Rovo__createConfluencePage",
    "mcp__claude_ai_Atlassian_Rovo__updateConfluencePage",
    "mcp__claude_ai_Atlassian_Rovo__createConfluenceFooterComment",
    "mcp__claude_ai_Atlassian_Rovo__createConfluenceInlineComment",
}

ALL_TOOLS: dict[str, Any] = {**SHARED_TOOLS, **JIRA_TOOLS, **CONFLUENCE_TOOLS}
