# Architecture

Status: Draft
Traces to: `intent.md` sections 9–11, 16

- Browser talks only to FastAPI.
- FastAPI is the authenticated ClickStack MCP client.
- Observability queries are read-only by default.
- Deterministic orchestrator owns incident state, retries, deploy, rollback, and kill switch.
- Agents operate with least privilege and cannot approve their own changes.
- Persistent system changes require a GitHub pull request.
