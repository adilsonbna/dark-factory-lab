# Architecture

Status: Draft
Traces to: `intent.md` §4, §9–§11, §16–§18; `requirements.md` demo topology

## 1. Overview

The lab is a single-host, local, Docker-Compose system. A synthetic target (`checkout` → `inventory`) emits real application telemetry while generators drive traffic and inject catalog faults. OpenTelemetry carries all signals to ClickHouse; ClickStack (HyperDX) serves them; a FastAPI backend is the authenticated MCP/GitHub client and agent control-plane bridge; a React dashboard is the only human surface; a deterministic orchestrator supervises specialized agents end to end.

## 2. Non-negotiable principles

These are load-bearing constraints from `intent.md` §9; every component honors them:

- Browser ↔ `api` only; never browser ↔ ClickHouse/ClickStack.
- Observability queries are read-only by default.
- Deterministic code (the orchestrator) owns the incident state machine; the LLM never advances state directly.
- Persistent changes flow only through GitHub pull requests.
- Agents run with least privilege and task-specific, allow-listed tools.
- Every action is attributable to incident, agent role, model version, prompt version, tool call, and repository revision.
- Generated code/commands execute in an isolated sandbox before deployment.
- The operator always retains a kill switch.

## 3. Components

| Component | Tech | Responsibility |
|-----------|------|----------------|
| `web` | React + TypeScript | Dashboard (DevOps, Management views); talks only to `api` |
| `api` | Python + FastAPI | Auth; ClickStack MCP client; GitHub client; agent control-plane bridge; audit writer |
| `orchestrator` | Deterministic service | Incident state machine; permissions; retries/timeouts; quality gates; deploy sequencing; rollback; circuit breaker; escalation |
| agents (5 roles) | LLM workers via model adapter | Triage, Investigation, Remediation, Validation, Release; each with scoped tools |
| `model-adapter` | Internal interface | Isolates Gemini (`gemini-3.8-flash-stable`); swap provider without touching agent code |
| `sandbox` | Isolated executor | Runs generated code/commands, network-restricted, before deployment |
| `checkout` | Rust | Synthetic target HTTP API; calls `inventory`; emits OTel |
| `inventory` | Python | Synthetic target HTTP API; dependency of `checkout`; emits OTel |
| `generator` | Rust + Python | Synthetic workload generator + fault injector (drives the 24 scenarios) |
| `otel-collector` | OpenTelemetry Collector | Receives OTLP; exports to ClickHouse |
| `clickhouse` | ClickHouse | Telemetry store (logs, metrics, traces) |
| `clickstack` | ClickStack (HyperDX) | Observability UI/queries; exposes MCP server |
| `github` | GitHub (external) | Monorepo, Issues, Projects, PRs, Actions; source of truth for persistent change |
| `gemini` | Google Gemini (external) | Initial LLM provider, accessed only through the model adapter |

`postgres`/`sqlite`-class local store: the backend/orchestrator keep an append-only incident + audit store (separable from ClickHouse telemetry); choice finalized at Milestone 6.

## 4. Data flows

1. **Telemetry path:** `checkout`/`inventory`/`generator` → OTLP → `otel-collector` → ClickHouse → ClickStack.
2. **Fault injection:** operator/eval harness → `generator` (`make inject SC=<id>`) → mutates the target (fault category).
3. **Detection:** ingestion/detection monitor watches ClickHouse for signature matches → emits incident event with correlation ID.
4. **Orchestration:** `orchestrator` consumes the incident event → drives the state machine → dispatches agents via `api` control plane.
5. **Agent reasoning:** agent → `model-adapter` → Gemini; agent → ClickStack MCP (via `api`) for read-only correlation.
6. **Remediation:** remediation agent → GitHub (create branch, edit, test, open PR) — never touches running services directly.
7. **Validation:** validation agent → GitHub Actions quality gates + sandbox execution → approve/reject.
8. **Release:** release agent → merge → blue-green deploy (build image, start candidate, gate, switch traffic, observe) → rollback on failure.
9. **Audit:** every transition/action → append-only audit store, tagged with correlation ID and six-field attribution.
10. **Operator control:** `web` → `api` → kill switch → `orchestrator` (halts forward progress).

## 5. Trust boundaries

```text
                          ┌───────────────────────────────────────────┐
                          │  Operator trust zone (human)              │
                          │  browser ──► web ──► api (authenticated)  │
                          └───────────────────┬───────────────────────┘
                                              │ HTTPS/local, auth
   ┌──────────────────────────┐   ┌───────────▼───────────────────────────┐
   │  External (least trust)  │   │  Control plane trust zone             │
   │  github (scoped token)   │◄──┤  api · orchestrator · model-adapter  │
   │  gemini (via adapter)    │   │  audit store (append-only)           │
   └──────────────────────────┘   └───────────┬───────────────────────────┘
                                              │ scoped tools, allow-list
   ┌──────────────────────────┐   ┌───────────▼───────────────────────────┐
   │  Agent execution zone    │   │  Observability trust zone            │
   │  5 roles · sandbox       │──►│  clickstack (MCP, read-only)        │
   │  (no raw credentials)    │   │  clickhouse · otel-collector        │
   └──────────────────────────┘   └───────────────────────────────────────┘
   ┌──────────────────────────┐
   │  Target zone             │
   │  checkout · inventory    │
   │  generator (fault src)   │
   └──────────────────────────┘
```

Boundary rules:

- **Operator ↔ control plane:** authentication required for any state-changing operator action; read views are unauthenticated reads of already-audited data (operator is the sole user).
- **Control plane ↔ external:** GitHub token is least-privilege; Gemini is reached only through the model adapter; neither external party can push into the control plane.
- **Control plane ↔ agents:** agents receive scoped capabilities, never raw GitHub/ClickStack/Gemini credentials; tool calls are allow-listed per role.
- **Agents ↔ observability:** read-only by default; write-capable observability actions require an explicit, audited, policy-checked escalation.
- **Agents ↔ sandbox:** generated code and commands never run on the host or against live services; sandbox is network-restricted.
- **Target zone:** the only zone the generator may mutate; the only zone deployment (blue-green) replaces.

## 6. Incident state machine

Deterministic, owned by the orchestrator (`intent.md` §11):

```text
Detected → Triaged → Investigating → Fix proposed → Validating → Approved
   → Deploying → Observing → Resolved
                ↘ Rolled back   ↘ Escalated
```

- Every transition writes a timestamped evidence record and a policy decision.
- Retry cycle ≤ 3 attempts, each requiring new evidence; then circuit breaker → `Escalated`.
- Kill switch halts forward progress from any state.

## 7. Blue-green deployment

Per `intent.md` §16: build immutable image → start candidate in parallel → run health/functional/security/observability gates → switch traffic only after all pass → keep previous version during the observation window → auto-rollback ≤ 2 min on gate failure.

## 8. Repositories and delivery

- Monorepo: `apps/web`, `apps/api`, `services/orchestrator`, `generators/`, `infra/compose/`, `eval/scenarios/`, `docs/adr/`, `docs/runbooks/`.
- GitHub is the source of truth for issues, PRs, and Actions gates; ADRs record durable decisions.
- Milestones follow `intent.md` §23; this document targets Milestones 2–6.

## 9. Open decisions

Recorded in `intent.md` §25: agent framework (Google ADK preferred pending spike), display name, monetary budget. Component stubs remain `.gitkeep` until their milestone; no runtime code is added before `requirements.md` baselines.
