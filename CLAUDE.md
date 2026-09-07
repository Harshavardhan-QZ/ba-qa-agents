Westfield AI Engineering Platform

Claude Code is the primary AI workspace and orchestration layer.

The platform contains:

1. Knowledge Fabric
2. BA/QA Agents
3. Automation Agents
4. Analytics & Quality Agents
5. DevOps Agents
6. Release & Operations Agents

Knowledge Fabric is the governed enterprise knowledge layer.

Agents use MCP servers to access enterprise systems.

MCP servers provide tools for:
- Knowledge retrieval
- Jira
- GitHub
- Azure DevOps
- TestRail
- SharePoint
- Playwright
- Other enterprise systems

Agents must prefer MCP tools instead of directly accessing enterprise systems.

Read operations can be performed according to permissions.

Write operations require appropriate approval.

All generated artifacts should maintain traceability to their source requirements.

Knowledge conflicts must be identified rather than silently resolved.