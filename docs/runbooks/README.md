# Operational Runbooks

Status: Draft (procedures to be wired in Milestone 2; `make` targets are placeholders until then)
Traces to: `intent.md` §16, §21–§22; `requirements.md` RUNTIME catalog

## 1. Scope

Procedures for operating the local dark-factory-lab: startup, health check, scenario injection, incident response, rollback, kill switch, reset, shutdown, and maintenance. All commands are single-command reproducible per `intent.md` §22.

## 2. Prerequisites

- Linux host within baseline capacity (8 vCPU / 16 GB RAM / 40 GB disk).
- Docker + Compose plugin.
- `GEMINI_API_KEY` and `GITHUB_TOKEN` in a local `.env` (never committed).

## 3. Startup

```bash
make up
```

- Builds/creates all Compose services: `checkout`, `inventory`, `generator`, `otel-collector`, `clickhouse`, `clickstack`, `api`, `web`, `orchestrator`, sandbox.
- Readiness: all services report healthy before the command returns.
- Verify telemetry path: seed traffic is queryable in ClickStack.

## 4. Health check

```bash
docker compose ps          # all services Up (healthy)
make eval -- health        # optional: qualification layer EVAL-QUAL-01/03
```

Expected: `checkout`→`inventory` round-trip succeeds; logs/metrics/traces present in ClickHouse.

## 5. Inject a scenario

```bash
make inject SC=<id>        # e.g. SC-03-V1
```

- The generator injects exactly the named fault; no other scenario triggers.
- Watch detection (≤ 30 s), diagnosis (≤ 2 min), remediation, validation, deploy, observation, resolution.
- Dashboard DevOps view shows the live timeline, evidence, PR, and audit trail.

## 6. Incident response (operator, manual intervention)

When an incident requires the operator instead of the autonomous path:

1. Identify the incident and its correlation ID from the DevOps view.
2. Inspect evidence, root-cause hypothesis, agent timeline, and tool calls.
3. Decide: allow automation to continue, escalate, or kill.
4. To escalate manually: set the incident to `Escalated` in the orchestrator (policy-checked, audited).
5. To halt immediately: use the kill switch (§8).

Never edit telemetry or audit records to "clean up" an incident; records are immutable.

## 7. Rollback (manual)

The release agent performs automatic rollback on gate failure. For a manual rollback:

1. Identify the failing version and the previous known-good image.
2. Run the deterministic rollback (traffic switch back to previous version).
3. Confirm health checks pass on the restored version.
4. Record the rollback with the incident correlation ID and the gate that failed.

Rollback target: ≤ 2 minutes from gate failure to restored health.

## 8. Kill switch

From the dashboard DevOps view, or via the backend control plane:

- The kill switch halts orchestrator forward progress from any state within 5 seconds.
- Effect: no further agent actions; incident is marked escalated-with-user-intervention; an audit record is written.
- Recovery: after resolving the underlying issue, the operator may clear the kill switch; automation resumes only on a new, clean incident.

## 9. Reset

```bash
make reset
```

- Wipes local state: telemetry, incident/audit store, and temporary artifacts.
- Preserves: Git history, PRs, versioned evidence tied to code changes.
- Post-condition: `make up` starts clean.

## 10. Shutdown

```bash
make down
```

- Stops all services and releases bound ports. No state is lost beyond the retention policy.

## 11. Maintenance

### Retention cleanup (automated)

- Raw telemetry: 7 days.
- Incident/operational audit: 30 days.
- GitHub changes/approvals/PR evidence: permanent.
- Cleanup must never remove versioned evidence tied to a code change.

### Credential rotation

- Rotate immediately on any suspected exposure; deleting from Git history is not a substitute for revocation (per SECURITY.md).
- After rotation, update local `.env` only; never commit the new value.

### Dependency and image hygiene

- Pull-request gates run dependency vulnerability scanning, container image scanning, and SBOM generation.
- Regenerate the SBOM on release; retain provenance.

### Evaluation re-run

- Any change to agents, prompts, tools, policies, or the orchestrator re-runs the full 24-scenario suite (three consecutive passes for a release claim).

## 12. Troubleshooting

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| `make up` hangs | unhealthy dependency | `docker compose logs <svc>`; check port conflicts |
| No telemetry in ClickStack | collector/ClickHouse down | check `otel-collector`, `clickhouse` health; review exporter config |
| Incident never detected | detection signature mismatch | verify `SC=<id>` injected; inspect generator logs |
| Agent stalls | Gemini/model adapter or MCP unreachable | check `api` logs, `GEMINI_API_KEY`, ClickStack MCP |
| Remediation loop exceeds 3 attempts | circuit breaker engaged | expect `Escalated`; investigate root cause manually |
| Kill switch unresponsive | orchestrator not receiving control input | verify `api`→`orchestrator` connectivity |
