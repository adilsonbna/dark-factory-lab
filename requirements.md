# Requirements

Status: Draft
Traces to: `intent.md` (baseline pending owner approval)

## Reading guide

- Every requirement below is an MVP must-have; there are no "should"/"nice-to-have" entries in this document.
- Each requirement carries an **acceptance outcome** (observable) and a **source** (`intent.md` section) plus an **evaluation mapping** (scenario ID or release-gate check in `evaluation-plan.md`).
- `REQ-` IDs are stable and never reused. Material changes to goals, autonomy, data, model, or thresholds update `intent.md` first (per README SDLC rule 1).

## Demo topology

The lab observes a minimal synthetic target so every fault category has a real container to act on:

| Component | Role |
|-----------|------|
| `checkout` (Rust) | HTTP API; emits OTel traces/metrics/logs; calls `inventory` |
| `inventory` (Python) | HTTP API; dependency of `checkout`; emits OTel |
| `generator` | Rust/Python workload generator + fault injector; drives `checkout`, injects catalog scenarios |
| `otel-collector` | Receives OTLP; exports to ClickHouse |
| `clickhouse` | Telemetry store |
| `clickstack` | Observability stack (HyperDX); exposes MCP server |
| `api` (FastAPI) | Backend; authenticated ClickStack MCP client, GitHub client, agent control-plane bridge |
| `web` (React) | Dashboard; talks only to `api` |
| `orchestrator` | Deterministic incident state machine; supervises agents |

---

## RUNTIME — reproducibility and developer experience

### REQ-RUNTIME-01 — Single-command startup
**Statement:** `make up` starts the complete laboratory from a clean checkout on one Linux host within the baseline capacity (8 vCPU, 16 GB RAM, 40 GB free disk, no GPU).
**Acceptance:** after `make up`, every Compose service reports healthy; a seeded request round-trips through `checkout` → `inventory` → ClickHouse and is queryable.
**Source:** intent §7, §22. **Evaluated by:** EVAL-QUAL-01 (environment bootstrap).

### REQ-RUNTIME-02 — Single-command stop
**Statement:** `make down` stops all services and releases bound ports.
**Acceptance:** no lab container remains running; `docker compose ps` is empty.
**Source:** intent §22. **Evaluated by:** EVAL-QUAL-01.

### REQ-RUNTIME-03 — Clean reset
**Statement:** `make reset` wipes local lab state (telemetry, incident/audit store) and returns to a clean, re-runnable state.
**Acceptance:** after reset, zero incidents, zero audit rows, zero retained telemetry rows; `make up` then starts clean.
**Source:** intent §22. **Evaluated by:** EVAL-QUAL-01.

### REQ-RUNTIME-04 — Unique run identifier
**Statement:** every experiment, evaluation run, and demo run carries a unique run ID that is propagated into telemetry and audit records.
**Acceptance:** two consecutive runs produce distinct run IDs; both IDs are queryable in telemetry and audit.
**Source:** intent §22. **Evaluated by:** EVAL-QUAL-08 (correlation).

---

## TELEM — telemetry generation and ingestion

### REQ-TELEM-01 — Synthetic telemetry emission
**Statement:** the generator emits synthetic logs, metrics, and traces over OTLP; `checkout` and `inventory` emit real application telemetry (traces, metrics, logs).
**Acceptance:** all three signal types are present in ClickHouse for a seeded run.
**Source:** intent §4, §7. **Evaluated by:** EVAL-QUAL-03 (telemetry integrity).

### REQ-TELEM-02 — Collector forwarding
**Statement:** the OpenTelemetry Collector receives OTLP and exports to ClickHouse without a persistent local queue bottleneck.
**Acceptance:** telemetry from generation to ClickHouse query latency is bounded within scenario time limits.
**Source:** intent §4, §7. **Evaluated by:** EVAL-QUAL-03.

### REQ-TELEM-03 — Deterministic fault injection
**Statement:** any of the 24 catalog scenarios can be injected on demand by scenario ID.
**Acceptance:** `make inject SC=<id>` triggers exactly the scenario's injected fault, and no other scenario, in a clean environment.
**Source:** intent §13. **Evaluated by:** every scenario's execution precondition.

### REQ-TELEM-04 — No direct telemetry mutation
**Statement:** no agent or user action modifies raw telemetry in ClickHouse; remediation cannot rewrite history.
**Acceptance:** the data-mutation guard rejects any attempt to update/delete telemetry rows; attempt is audited.
**Source:** intent §8, §9. **Evaluated by:** EVAL-SAFETY (prohibited actions), release gate G-4.

---

## OBS — observability access

### REQ-OBS-01 — Semantic MCP access
**Statement:** the backend is an authenticated client of the ClickStack MCP server and can issue read-only semantic queries (logs, metrics, traces) by service and time window.
**Acceptance:** an investigation query returns correlated log/metric/trace results for a known incident window.
**Source:** intent §4, §9. **Evaluated by:** EVAL-QUAL-04 (observability access).

### REQ-OBS-02 — Read-only by default
**Statement:** observability queries are read-only by default; write-capable observability actions require an explicit, audited, policy-checked escalation.
**Acceptance:** the default MCP toolset contains no mutation verbs; an attempt to use one is denied and audited.
**Source:** intent §9. **Evaluated by:** EVAL-SAFETY, release gate G-4.

---

## UI — dashboard

### REQ-UI-01 — DevOps view
**Statement:** the DevOps view displays, for each incident: status, severity, affected service, detection timestamp, correlated signals, root-cause hypothesis and evidence, agent timeline, tool calls, proposed remediation, PR/diff summary, validation results, deployment status, health checks, rollback status, retry count, audit trail, and the kill switch.
**Acceptance:** a resolved and an escalated incident each render all listed fields with non-empty evidence.
**Source:** intent §17. **Evaluated by:** EVAL-QUAL-05 (dashboard completeness).

### REQ-UI-02 — Management view
**Statement:** the Management view displays overall health, open/resolved incidents, recurrence, mean detection/diagnosis/recovery/rollback times, remediation success rate, false-alert rate, failed-remediation rate, agent/LLM usage trends, and release qualification status.
**Acceptance:** after a full evaluation run, every metric on the Management view matches the harness's reported numbers.
**Source:** intent §17. **Evaluated by:** EVAL-QUAL-05.

### REQ-UI-03 — Kill switch
**Statement:** the operator can interrupt automation at any time from the dashboard; the switch stops the orchestrator's forward progress and marks the incident escalated-with-user-intervention.
**Acceptance:** activating the kill switch during an in-flight scenario halts further agent actions within 5 seconds and produces an audit record.
**Source:** intent §9, §17. **Evaluated by:** EVAL-QUAL-06 (kill switch).

### REQ-UI-04 — Browser isolation
**Statement:** the browser never connects directly to ClickHouse or any data store; it talks only to the FastAPI backend.
**Acceptance:** the web app has no ClickHouse/hyperDX connection configuration; all data reaches the browser via `api`.
**Source:** intent §9. **Evaluated by:** EVAL-QUAL-05, architecture review.

---

## API — backend

### REQ-API-01 — Authenticated operator actions
**Statement:** operator actions through the backend require authentication; the single operator is authenticated before any state-changing action.
**Acceptance:** an unauthenticated state-changing request is rejected (401/403) and audited.
**Source:** intent §20. **Evaluated by:** EVAL-QUAL-07 (authentication).

### REQ-API-02 — MCP and GitHub client
**Statement:** the backend is the only component holding ClickStack MCP and GitHub credentials; agents receive scoped capabilities, not raw credentials.
**Acceptance:** credentials exist only in the backend's secret store; agent containers have no mounted GitHub/ClickStack secrets.
**Source:** intent §4, §9, §20. **Evaluated by:** EVAL-SAFETY, architecture review.

### REQ-API-03 — Structured agent interface
**Statement:** the backend exposes the control-plane interface through which the orchestrator dispatches agents and collects their structured decisions.
**Acceptance:** an agent decision is represented by a validated schema and is attributable to role, model, prompt, and tool call.
**Source:** intent §18, §19. **Evaluated by:** EVAL-QUAL-08 (attribution).

---

## AGENT — agent roles

### REQ-AGENT-01 — Triage
**Statement:** the triage agent classifies an incident, assigns low/medium severity, removes duplicates, and identifies the affected service and telemetry window.
**Acceptance:** for a duplicate of an open incident, triage marks it duplicate; for a novel incident it produces severity ≤ medium, service, and window.
**Source:** intent §10. **Evaluated by:** every scenario's triage step.

### REQ-AGENT-02 — Investigation
**Statement:** the investigation agent queries ClickStack MCP, correlates logs/metrics/traces, and produces an evidence-backed root-cause hypothesis plus the allowed remediation scope.
**Acceptance:** for every accepted scenario, the hypothesis identifies the ground-truth root cause category with at least one cited signal.
**Source:** intent §10. **Evaluated by:** every scenario's diagnosis step.

### REQ-AGENT-03 — Remediation
**Statement:** the remediation agent creates a branch, modifies only authorized code/configuration, adds or updates tests, and opens a pull request with evidence and expected outcomes.
**Acceptance:** the PR diff stays within the scenario's allowed remediation scope and includes a test reproducing the fault.
**Source:** intent §10. **Evaluated by:** every scenario's fix step + scope check.

### REQ-AGENT-04 — Validation independence
**Statement:** the validation agent is independent from the remediation agent, cannot approve a change it created, executes all quality gates, and approves or rejects with evidence.
**Acceptance:** a self-approval attempt is blocked and audited; every approval carries gate results.
**Source:** intent §10, §15. **Evaluated by:** release gate G-6 (no self-approval).

### REQ-AGENT-05 — Release and rollback
**Statement:** the release agent performs the approved merge, runs blue-green deployment, health checks, and observation, and triggers rollback when gates fail.
**Acceptance:** a failing post-deploy gate triggers rollback within the time target with the previous version restored.
**Source:** intent §10, §16. **Evaluated by:** EVAL-RECOVERY, EVAL-ROLLBACK.

### REQ-AGENT-06 — Agent observability
**Statement:** agents emit OpenTelemetry for model calls, tool calls, MCP queries, latency, token usage, estimated cost, prompt/policy version, model version, structured decisions, confidence/risk classification, and validation/deploy/rollback results.
**Acceptance:** every field is present and attributable for each agent step in a run.
**Source:** intent §18. **Evaluated by:** EVAL-QUAL-08.

### REQ-AGENT-07 — Correlation identifier
**Statement:** application and agent telemetry share an incident correlation ID.
**Acceptance:** a single ID joins the app trace, agent trace, tool calls, and audit record for one incident.
**Source:** intent §18. **Evaluated by:** EVAL-QUAL-08.

---

## ORCH — orchestrator (deterministic)

### REQ-ORCH-01 — State machine ownership
**Statement:** deterministic code (not an LLM) owns incident state transitions along Detected → Triaged → Investigating → Fix proposed → Validating → Approved → Deploying → Observing → Resolved, with terminal states Rolled back and Escalated.
**Acceptance:** an LLM cannot advance state directly; only orchestrator policy emits transition records.
**Source:** intent §9, §11. **Evaluated by:** EVAL-QUAL-02 (state machine).

### REQ-ORCH-02 — Transition evidence
**Statement:** every state transition requires timestamped evidence and a policy decision.
**Acceptance:** every transition record carries a timestamp, evidence reference, and policy decision reference.
**Source:** intent §11. **Evaluated by:** EVAL-QUAL-02, release gate G-5 (no missing audit).

### REQ-ORCH-03 — Bounded retries and escalation
**Statement:** a remediation cycle runs at most three times, each attempt requiring new evidence or a materially different fix; after three failures a circuit breaker stops changes and the incident is marked Escalated with a dashboard alert.
**Acceptance:** a scenario forced to fail repeatedly reaches Escalated after exactly three attempts; no fourth change is attempted.
**Source:** intent §12. **Evaluated by:** EVAL-ESCALATION.

### REQ-ORCH-04 — Timeouts and concurrency bounds
**Statement:** the orchestrator enforces per-step timeouts and bounded concurrency; no remediation loop may run indefinitely.
**Acceptance:** a hung step is interrupted by its timeout and recorded; concurrent incidents are capped at a configured limit.
**Source:** intent §12, §20. **Evaluated by:** EVAL-SAFETY.

---

## DEPLOY — deployment and rollback

### REQ-DEPLOY-01 — Blue-green deployment
**Statement:** deployment builds a new immutable image, starts the candidate in parallel, runs health/functional/security/observability gates, and switches traffic only after all gates pass, keeping the previous version during the observation window.
**Acceptance:** during a successful deploy, both versions run concurrently until the traffic switch; the previous version remains reachable through the observation window.
**Source:** intent §16. **Evaluated by:** EVAL-RECOVERY.

### REQ-DEPLOY-02 — Automatic rollback
**Statement:** rollback completes automatically within two minutes of a failing gate, restoring the previous version.
**Acceptance:** a deliberate post-deploy gate failure restores the prior version within 120 seconds and records a rollback audit event.
**Source:** intent §16, §6. **Evaluated by:** EVAL-ROLLBACK.

### REQ-DEPLOY-03 — PR-only persistent change
**Statement:** all persistent system changes flow through a GitHub pull request; no agent may mutate the running environment outside the PR/deploy path.
**Acceptance:** no deployment occurs without a linked merged PR; direct edits to running services are blocked.
**Source:** intent §9. **Evaluated by:** release gate G-5.

---

## SEC — security

### REQ-SEC-01 — Localhost-only exposure
**Statement:** all lab services are bound to localhost/private interfaces by default; nothing is exposed to the public network.
**Acceptance:** a port scan of the host's external interface finds no lab service.
**Source:** intent §20. **Evaluated by:** EVAL-SAFETY, architecture review.

### REQ-SEC-02 — Least-privilege credentials
**Statement:** GitHub credentials are scoped to the minimum needed (read repo, create branch/PR, trigger checks); no credential grants repo administration or approval-policy override.
**Acceptance:** the token's scopes cannot force-push to protected branches, delete branches, or modify branch protection.
**Source:** intent §20. **Evaluated by:** EVAL-SAFETY.

### REQ-SEC-03 — Secret hygiene
**Statement:** no secrets are committed; only `.env.example` is present; automated secret scanning runs on PRs.
**Acceptance:** the repository and PRs contain no detected secrets; `.env` is git-ignored.
**Source:** intent §20. **Evaluated by:** release gate (secret scan).

### REQ-SEC-04 — Sandboxed generated execution
**Statement:** generated code and commands run in an isolated, network-restricted environment before deployment.
**Acceptance:** a generated command attempting to reach an external network or mutate host state is blocked by the sandbox.
**Source:** intent §9, §20. **Evaluated by:** EVAL-SAFETY.

### REQ-SEC-05 — No destructive data operations
**Statement:** agents cannot perform destructive data operations on telemetry or audit data.
**Acceptance:** any attempted delete/truncate on telemetry/audit is denied and audited.
**Source:** intent §20. **Evaluated by:** EVAL-SAFETY, release gate G-4.

### REQ-SEC-06 — Supply-chain scanning
**Statement:** dependency vulnerability scanning, container image scanning, SBOM generation, and artifact provenance run as part of PR gates.
**Acceptance:** a PR introducing a known-vulnerable pinned dependency is rejected by CI.
**Source:** intent §15, §20. **Evaluated by:** release gate (supply chain).

---

## AUDIT — audit and attribution

### REQ-AUDIT-01 — Immutable audit records
**Statement:** every incident and decision produces an immutable, append-only audit record.
**Acceptance:** audit records cannot be edited or deleted after write; tamper attempts are denied.
**Source:** intent §20. **Evaluated by:** release gate G-5.

### REQ-AUDIT-02 — Full attribution
**Statement:** every action is attributable to incident, agent role, model version, prompt version, tool call, and repository revision.
**Acceptance:** each action record carries all six attribution fields populated.
**Source:** intent §9, §18. **Evaluated by:** EVAL-QUAL-08.

### REQ-AUDIT-03 — Retention
**Statement:** raw telemetry is retained 7 days, incident/operational audit data 30 days, GitHub changes/approvals/PR evidence permanently; cleanup is automated and never removes versioned evidence tied to a code change.
**Acceptance:** after the retention window, raw telemetry is gone and audit rows are pruned, while PR-linked evidence remains.
**Source:** intent §21. **Evaluated by:** EVAL-QUAL-09 (retention), documented policy.

---

## GOV — AI governance

### REQ-GOV-01 — Versioned governing artifacts
**Statement:** prompts, instructions, schemas, tools, and policies are versioned in Git; behavior changes require pull requests.
**Acceptance:** a prompt/policy change is only effective through a merged PR; the running prompt version matches the deployed revision.
**Source:** intent §19. **Evaluated by:** EVAL-QUAL-08 (version attribution).

### REQ-GOV-02 — Model cannot self-govern
**Statement:** the model cannot change its own governing rules, tool allow-list, or approval policies.
**Acceptance:** an agent attempt to modify its rules/policies/tools is denied and audited.
**Source:** intent §19. **Evaluated by:** EVAL-SAFETY, release gate G-4.

### REQ-GOV-03 — Validated structured schemas
**Statement:** model outputs use validated structured schemas; malformed output is rejected and retried within the bounded cycle, never silently coerced into a deployment.
**Acceptance:** an injected malformed model output is rejected by the schema validator and does not advance state.
**Source:** intent §19. **Evaluated by:** EVAL-QUAL-02, EVAL-SAFETY.

### REQ-GOV-04 — Confidence never authorizes
**Statement:** model confidence or a second LLM's opinion alone never authorizes a deployment; authorization requires deterministic gates and independent approval.
**Acceptance:** a high-confidence, gate-failing change is not deployed.
**Source:** intent §19, §14. **Evaluated by:** release gate G-6.

### REQ-GOV-05 — Model adapter
**Statement:** an internal model adapter isolates Gemini as the initial pinned provider (`gemini-3.8-flash-stable`) so the model can be swapped without touching agent code.
**Acceptance:** the adapter exposes a single interface; the model identifier is configuration, not source.
**Source:** intent §7. **Evaluated by:** architecture review.

---

## EVAL — evaluation

### REQ-EVAL-01 — Catalog completeness
**Statement:** the evaluation catalog contains 24 scenarios: 8 categories × 3 (two visible, one hidden), each with injected fault, expected telemetry, ground-truth root cause, allowed remediation, prohibited actions, expected healthy state, time limits, and rollback condition.
**Acceptance:** the catalog is machine-readable and all 24 scenarios execute.
**Source:** intent §13. **Evaluated by:** EVAL-QUAL-02 (catalog integrity).

### REQ-EVAL-02 — Release gate
**Statement:** the MVP is approved only when all 24 scenarios pass, the full suite passes three consecutive times (72 executions), all executions meet timing targets, false-alert rate < 5%, zero prohibited actions, zero missing audit evidence, no PR-workflow bypass, no self-approval, recovery verified via health checks + observation window, and rollback demonstrated.
**Acceptance:** the release gate evaluates all criteria from harness output, not from assertions.
**Source:** intent §14. **Evaluated by:** release gates G-1..G-7.

---

## Deferred (not in MVP)

Per `intent.md` §8 and §25, out of scope: Kubernetes, cloud, real/sensitive telemetry, high/critical severity, email alerts, multiple LLM providers, multi-user/tenant, mobile, direct telemetry mutation, self-modifying rules, WCAG gate, monetary budget gate, display-name decision, final agent framework selection.
