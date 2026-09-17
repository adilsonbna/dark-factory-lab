# Security Controls

Status: Draft
Traces to: `intent.md` §15, §19–§20; `architecture.md` trust boundaries; `requirements.md` SEC catalog

## 1. Scope and approach

Local, single-operator, synthetic-telemetry laboratory. The threat model treats **agent output and all external content (issues, PR text, telemetry, Gemini responses) as untrusted** and treats the human operator as the only authority for material decisions. Controls are mapped to `intent.md` §20 and aligned to OWASP Top 10 for LLM Applications, NIST AI RMF, and SSDF at the MVP's risk and scale (no certification claimed).

## 2. Assets

| Asset | Classification | Integrity requirement |
|-------|---------------|----------------------|
| Raw telemetry (ClickHouse) | Synthetic, low sensitivity | Immutable; no direct mutation |
| Audit/incident records | Operational | Immutable, append-only |
| Governing artifacts (prompts, schemas, tools, policies) | High value | Versioned in Git; only via PR |
| Credentials (Gemini key, GitHub token) | Secret | Never committed; least-privilege |
| Approval/authorization rules | High value | Model cannot modify |
| Operator session | Confidentiality | Authenticated |

## 3. Threat model

L = likelihood, I = impact (Low/Med/High).

| # | Threat | L | I | Control | REQ |
|---|--------|---|---|---------|-----|
| T-01 | Prompt injection via issue/PR/telemetry text | Med | High | Treat all external text as untrusted data, never instructions; schema-validated outputs; allow-listed tools | GOV-03, SEC-07 |
| T-02 | Model modifies its own rules/tools/policies | Low | High | Rule/tool/policy changes are Git+PR only; model has no write path to governance | GOV-02, SEC-05 |
| T-03 | Agent self-approves its change | Med | High | Validation agent independence; no cross-role approval; audit of approver identity | AGENT-04, G-6 |
| T-04 | Agent bypasses PR path (direct deploy/edit) | Med | High | Running services are read-only to agents; deploy only through PR→merge→blue-green | DEPLOY-03 |
| T-05 | Destructive telemetry/audit mutation | Med | High | Read-only observability; deny/audit mutation attempts | OBS-02, SEC-05 |
| T-06 | Sandbox escape (generated code reaches host/external net) | Low | High | Isolated network-restricted executor; bounded timeouts | SEC-04 |
| T-07 | Credential leakage (secrets in repo/PR) | Med | High | `.env.example` only; secret scanning on PR; push protection | SEC-03 |
| T-08 | Supply-chain compromise (bad dependency/image) | Med | Med | Dependency + container scanning; SBOM; provenance | SEC-06 |
| T-09 | Unauthenticated operator action | Med | Med | Auth required for state-changing actions; localhost-only exposure | API-01, SEC-01 |
| T-10 | Unbounded loop / resource exhaustion | Med | Med | Orchestrator retry cap, timeouts, concurrency bounds, circuit breaker | ORCH-03/04 |
| T-11 | Hallucinated but confident remediation | Med | Med | Deterministic gates + independent approval; confidence never authorizes | GOV-04, G-6 |
| T-12 | Data leakage to Gemini (prompt over-sharing) | Low | Med | Synthetic data only; model adapter boundary; no secrets in prompts | SEC-02, §7 data scope |
| T-13 | Sensitive content committed (`.env`, raw telemetry) | Low | Med | `.gitignore`; CONTRIBUTING policy; CI guardrail | SEC-03 |

## 4. Misuse cases (agent-specific)

1. **Remediation agent exfiltrates the GitHub token** — mitigated by not mounting raw credentials into agent containers; agents get scoped capabilities issued per action by `api`.
2. **Investigation agent issues a write query** — mitigated by read-only default MCP toolset; write verbs require policy-checked escalation and audit.
3. **Triage agent suppresses a real incident (false negative)** — mitigated by deterministic detection signatures independent of the LLM; the LLM classifies but does not gate detection.
4. **Release agent rolls back healthy traffic to mask a failed change** — mitigated by rollback decision being a deterministic gate result, not an agent choice.
5. **Agent replays an old approval to authorize a new change** — mitigated by approval records being non-replayable (bound to repo revision + incident + correlation ID).

## 5. Control categories

### Authentication & exposure
- Localhost/private-interface binding for all services (SEC-01).
- Authenticated operator for state-changing actions (API-01).
- Single-operator model; no multi-tenant surface (§7).

### Least privilege
- GitHub token scoped to branch/PR/check triggering; no admin, no branch-protection override (SEC-02).
- Per-role tool allow-lists; agents receive scoped capabilities, not raw credentials (SEC-07, API-02).
- Read-only observability by default (OBS-02).

### Data integrity & audit
- Append-only, immutable audit store (AUDIT-01).
- Six-field attribution on every action (AUDIT-02).
- Retention windows with automated, evidence-preserving cleanup (AUDIT-03).
- No direct telemetry mutation (TELEM-04, SEC-05).

### Governance & authorization
- Governing artifacts versioned in Git; PR-only changes (GOV-01).
- Model cannot self-govern (GOV-02).
- Confidence never authorizes deployment (GOV-04).
- Independent validation; no self-approval (AGENT-04).

### Execution isolation
- Network-restricted sandbox for generated code/commands (SEC-04).
- Bounded concurrency and timeouts (ORCH-04).
- Circuit breaker + escalation after three attempts (ORCH-03).

### Supply chain
- Dependency vulnerability scanning, container image scanning, SBOM, artifact provenance (SEC-06).
- Secret scanning + push protection (SEC-03).
- Protected default branch; PR review + passing checks required (SECURITY.md).

## 6. AI-specific risk register (OWASP LLM Top 10 mapping)

| OWASP LLM Top 10 (2025) | Mapping | Primary control |
|--------------------------|---------|-----------------|
| LLM01 Prompt Injection | T-01 | Untrusted-data policy; schema validation; allow-lists |
| LLM02 Sensitive Information Disclosure | T-12, T-13 | Synthetic data only; no secrets in prompts; secret scanning |
| LLM03 Supply Chain | T-08 | SBOM, provenance, dependency/container scanning |
| LLM04 Data & Model Poisoning | §7 synthetic data; single pinned model | Pin `gemini-3.8-flash-stable`; telemetry is non-training, local |
| LLM05 Improper Output Handling | T-11 | Structured schema validation; no raw output executed |
| LLM06 Excessive Agency | T-02, T-04 | Least privilege; PR-only path; deterministic state machine |
| LLM07 System Prompt Leakage | — | Prompts versioned; treated as non-secret but change-controlled |
| LLM08 Vector/Embedding Weakness | — | No vector store in MVP |
| LLM09 Misinformation | T-11 | Deterministic ground truth; LLM opinion is never proof |
| LLM10 Unbounded Consumption | T-10 | Retry cap, timeouts, concurrency bounds |

## 7. Residual risks (accepted for MVP)

- Single-operator model means the operator is also the audit reviewer (no separation of duties among humans); accepted because the laboratory has no real data or production authority.
- LLM provider (Gemini) is a third-party dependency for reasoning; synthetic data minimizes exposure; a model adapter limits blast radius and enables later swap.
- No runtime WAF/rate limiting beyond localhost exposure; accepted given non-public, single-host deployment.

These acceptances are documented here and require an owner decision to change; they do not reduce the hard controls above (immutability, PR-only change, independence, kill switch).
