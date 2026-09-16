# Project Intent

Status: Draft v0.1<br>
Working title: dark-factory-lab<br>
Language: English<br>
Repository: https://github.com/adilsonbna/dark-factory-lab<br>
License: MIT<br>

## 1. Purpose

Build a local, autonomous, auditable observability and remediation laboratory in which AI agents detect known failures, investigate root causes, propose and validate fixes, deploy them safely, verify recovery, and roll back when necessary.

The product demonstrates a “dark factory” operating model for software operations: routine incident handling is performed end to end by specialized agents, while deterministic controls enforce safety, policy, retries, and auditability.

## 2. Problem

The current environment does not provide complete, trustworthy visibility of all telemetry in one dashboard. Failures are detected and corrected manually, increasing operational effort and recovery time.

## 3. Users

### DevOps operator

Needs to:

- Monitor the complete local Docker environment.
- Detect and investigate incidents.
- Inspect evidence, root-cause analysis, agent actions, code changes, validation results, deployment status, rollback status, and audit history.
- Interrupt automation through a kill switch.

### Manager

Needs to:

- Understand overall system health.
- See open and resolved incidents.
- Track recurrence, detection time, diagnosis time, recovery time, rollback time, false-alert rate, automation success, and remediation failures.
- Verify that the autonomous process is operating within policy.

## 4. Product Vision

A self-observing and self-remediating local platform where:

1. Rust and Python generators produce synthetic telemetry and inject controlled failures.
2. OpenTelemetry collects logs, metrics, and traces.
3. ClickHouse stores the telemetry.
4. ClickStack and HyperDX provide observability capabilities.
5. A custom React dashboard presents operational, management, agent, and audit views.
6. A FastAPI backend connects the dashboard, ClickStack MCP, GitHub, and the agent control plane.
7. Specialized agents investigate, fix, validate, release, and verify changes.
8. A deterministic orchestrator controls state transitions, permissions, retries, deployment, rollback, and escalation.

## 5. MVP Goals

- Detect 100% of the predefined injected-failure catalog.
- Provide a root-cause diagnosis for every accepted scenario.
- Remediate accepted scenarios autonomously.
- Maintain immutable evidence for every incident and decision.
- Prevent agents from approving their own changes.
- Ensure all persistent changes flow through GitHub pull requests.
- Demonstrate the complete autonomous workflow live.
- Make the laboratory reproducible through single commands.

“100% coverage” applies only to the closed, versioned test catalog. It is not a claim that the system can detect or correct every unknown real-world failure.

## 6. Success Metrics

- Detection time: no more than 30 seconds.
- Diagnosis time: no more than 2 minutes.
- Service restoration time: no more than 15 minutes.
- Rollback time: no more than 2 minutes.
- False-alert rate: below 5%.
- Unauthorized actions: zero.
- Missing audit records: zero.
- Prohibited data mutations: zero.

## 7. MVP Scope

### Runtime environment

- Linux.
- Docker Compose.
- Baseline capacity:
  - 8 vCPUs.
  - 16 GB RAM.
  - 40 GB free storage.
  - No local GPU requirement.

### Application stack

- React with TypeScript frontend.
- Python with FastAPI backend.
- Rust and Python telemetry and failure generators.
- OpenTelemetry using OTLP and an OpenTelemetry Collector.
- ClickHouse.
- ClickStack with HyperDX.
- ClickStack MCP for semantic observability access.
- GitHub monorepo, Issues, Projects, pull requests, and Actions.
- Google Gemini as the initial LLM provider.
- Gemini 3.8 Flash stable as the initial pinned model.
- An internal model adapter to support future migration.

### Data

- Synthetic telemetry only.
- Local Docker environment only.
- Low- and medium-severity incidents only.
- Single authenticated operator.

## 8. Explicit Non-Goals

The first MVP will not include:

- Kubernetes.
- Cloud deployment.
- Real production environments.
- Real or sensitive telemetry.
- High- or critical-severity incidents.
- Email alerts.
- Multiple LLM providers.
- Multi-user or multi-tenant access.
- Mobile applications.
- Direct modification of telemetry data.
- Agents modifying their own rules or approval policies.
- Formal WCAG conformance as a release gate.
- A monetary LLM budget as a release gate.

## 9. System Architecture Principles

- The browser never connects directly to ClickHouse.
- The React application communicates only with the FastAPI backend.
- The backend acts as an authenticated MCP client for ClickStack.
- Observability queries are read-only by default.
- Persistent system changes require a GitHub pull request.
- Deterministic code, not an LLM, owns the incident state machine.
- Agents operate with least privilege and task-specific tools.
- Every action must be attributable to an incident, agent role, model version, prompt version, tool call, and repository revision.
- Generated code and commands run in an isolated environment before deployment.
- The operator always retains a kill switch.

## 10. Agent Roles

### Orchestrator

A deterministic service that controls:

- Incident state transitions.
- Permissions.
- Retry limits.
- Timeouts.
- Quality gates.
- Deployment sequencing.
- Rollback.
- Circuit breaking.
- Audit completeness.

### Triage Agent

- Classifies the incident.
- Assigns low or medium severity.
- Removes duplicates.
- Identifies the affected service and telemetry window.

### Investigation Agent

- Queries ClickStack MCP.
- Correlates logs, metrics, and traces.
- Produces an evidence-backed root-cause hypothesis.
- Identifies the allowed remediation scope.

### Remediation Agent

- Creates a branch.
- Modifies only authorized code or configuration.
- Adds or updates tests.
- Opens a pull request with evidence and expected outcomes.

### Validation Agent

- Is independent from the remediation agent.
- Cannot approve a change it created.
- Executes all quality gates.
- Approves or rejects the pull request with evidence.

### Release Agent

- Performs the approved merge.
- Executes blue-green deployment.
- Runs health checks.
- Observes the new version.
- Triggers rollback when gates fail.

## 11. Incident State Machine

Primary path:

1. Detected.
2. Triaged.
3. Investigating.
4. Fix proposed.
5. Validating.
6. Approved.
7. Deploying.
8. Observing.
9. Resolved.

Alternative terminal paths:

- Rolled back.
- Escalated.

Every transition requires timestamped evidence and a policy decision.

## 12. Retry and Escalation Policy

- A remediation cycle may run at most three times.
- Each attempt must produce new evidence or a materially different fix.
- After three failed attempts, a circuit breaker stops further changes.
- The incident is marked as escalated.
- A specific dashboard alert is created.
- Email escalation is deferred beyond the MVP.
- No loop may continue indefinitely.

## 13. Failure Catalog

The MVP will cover eight categories:

1. Application exception.
2. Stopped container.
3. CPU saturation.
4. Memory saturation.
5. Network connectivity failure.
6. Telemetry-pipeline failure.
7. Invalid configuration.
8. Deployment regression.

Each category contains three scenarios:

- Two visible development scenarios.
- One hidden evaluation scenario.

Total: 24 scenarios.

Each scenario defines:

- Injected fault.
- Expected telemetry.
- Ground-truth root cause.
- Allowed remediation actions.
- Prohibited actions.
- Expected healthy state.
- Time limits.
- Rollback condition.

## 14. Evaluation and Release Gate

The MVP is approved only when:

- All 24 scenarios pass.
- The complete suite passes three consecutive times.
- All 72 executions meet the timing targets.
- False alerts remain below 5%.
- No prohibited action occurs.
- No audit evidence is missing.
- No agent bypasses the pull-request workflow.
- No remediation agent approves its own work.
- Recovery is verified through health checks and an observation window.
- Rollback is demonstrated successfully.

Evaluation uses deterministic ground truth. A second LLM’s opinion is not sufficient proof of correctness.

## 15. Pull Request Quality Gates

The validation agent must require:

- Reproducible build.
- Formatting, lint, and type checks.
- Unit tests.
- Integration tests.
- End-to-end tests.
- Regression tests.
- Reproduction of the original failure.
- Proof that the failure is corrected.
- Telemetry comparison before and after the change.
- Static application security testing.
- Secret scanning.
- Dependency vulnerability scanning.
- Container image scanning.
- Software bill of materials.
- Artifact provenance and supply-chain integrity.
- Docker and infrastructure policy checks.
- Diff size and file-scope limits.
- Protection of data, credentials, and approval rules.
- CPU, memory, latency, and telemetry-volume checks.
- False-positive and side-effect tests.
- Sandboxed execution.
- Blue-green deployment checks.
- Post-deployment health checks.
- Observation window.
- Tested automatic rollback.
- Independent approval.
- Complete audit evidence.

## 16. Deployment and Rollback

Deployment uses a local blue-green strategy:

1. Build a new immutable image.
2. Start the candidate version in parallel.
3. Run health, functional, security, and observability checks.
4. Switch traffic only after all gates pass.
5. Keep the previous version available during the observation window.
6. Roll back automatically within two minutes if a gate fails.

## 17. Dashboard Requirements

### DevOps view

Display:

- Incident status and severity.
- Affected service.
- Detection timestamp.
- Correlated logs, metrics, and traces.
- Root-cause hypothesis and evidence.
- Agent timeline.
- Tool calls.
- Proposed remediation.
- Pull request and diff summary.
- Validation results.
- Deployment status.
- Health checks.
- Rollback status.
- Retry count.
- Audit trail.
- Kill switch.

### Management view

Display:

- Overall system health.
- Open and resolved incidents.
- Incident recurrence.
- Mean detection, diagnosis, recovery, and rollback times.
- Autonomous remediation success rate.
- False-alert rate.
- Failed-remediation rate.
- Agent and LLM usage trends.
- Release qualification status.

Alerts in the MVP appear only in the dashboard and only for low- and medium-severity incidents.

## 18. Agent Observability

Agents must emit OpenTelemetry for:

- Model calls.
- Tool calls.
- MCP queries.
- Latency.
- Token usage.
- Estimated cost.
- Prompt and policy version.
- Model version.
- Structured decision.
- Confidence and risk classification.
- Validation result.
- Deployment result.
- Rollback result.

Application and agent telemetry must share an incident correlation identifier.

## 19. AI Governance

- Prompts, instructions, schemas, tools, and policies are versioned in Git.
- Behavior changes require pull requests.
- Agent changes rerun the full evaluation suite.
- The model cannot change its own governing rules.
- Model outputs must use validated structured schemas.
- Tool permissions are allow-listed.
- Every external side effect is policy checked.
- The human owner retains accountability and emergency control.
- Model confidence alone never authorizes a deployment.

## 20. Security Requirements

- Localhost-only exposure by default.
- Authentication required for operator actions.
- Read-only ClickStack and ClickHouse access for investigation.
- Least-privilege GitHub credentials.
- No secrets committed to Git.
- Example environment files only.
- Automated secret scanning.
- Dependency and container scanning.
- Protected branches and required checks.
- Immutable audit records.
- Sandboxed code execution.
- Bounded concurrency and timeouts.
- No destructive data operations.

## 21. Retention

- Raw telemetry: 7 days.
- Incident and operational audit data: 30 days.
- GitHub changes, approvals, and pull-request evidence: permanent.
- Cleanup must be automated.
- Cleanup must never remove versioned evidence associated with a code change.

## 22. Developer Experience

The project must provide reproducible commands to:

- Start the laboratory.
- Seed telemetry.
- Inject a selected scenario.
- Run the complete demonstration.
- Run evaluations.
- Export evidence.
- Stop the laboratory.
- Reset to a clean state.

Every experiment receives a unique run identifier.

## 23. Project Management

GitHub is the source of truth:

- GitHub Projects tracks milestones, dependencies, and status.
- GitHub Issues define executable work and acceptance criteria.
- Pull requests contain changes and evidence.
- GitHub Actions enforce quality gates.
- Architecture decisions are stored as ADRs.
- No issue is complete without a linked artifact or verified test result.

Delivery is milestone-driven rather than date-driven.

Suggested milestones:

1. Repository and policy foundation.
2. Reproducible Docker laboratory.
3. Telemetry generation and ingestion.
4. ClickStack MCP integration.
5. React and FastAPI dashboard.
6. Incident state machine.
7. Investigation agents.
8. Pull-request remediation.
9. Independent validation.
10. Blue-green release and rollback.
11. Evaluation harness.
12. Full autonomous demonstration.

## 24. Documentation Set

`intent.md` remains the product north star.

Separate versioned documents will cover:

- Architecture.
- Threat model.
- AI risk register.
- Evaluation catalog.
- Security controls.
- Runbooks.
- Architecture decision records.
- Contribution guide.
- Security policy.
- Operational playbook.

## 25. Deferred Decisions

- Display name beyond the repository id `dark-factory-lab`.
- Final agent framework; Google ADK is the preferred candidate pending a technical spike.
- Monetary Gemini budget.
- Real-data privacy and residency policy.
- High- and critical-severity handling.
- Email notifications.
- Cloud and Kubernetes deployment.
- Multiple LLM providers.
- Formal WCAG 2.2 AA release gate.

## 26. Standards and Guidance Alignment

The project will use the following references as guidance, tailored to the MVP’s risk and scale:

- [ISO/IEC 5338](https://www.iso.org/obp/ui?_escaped_fragment_=iso%3Astd%3Aiso-iec%3A5338%3Aed-1%3Av1%3Aen) for AI system life-cycle processes.
- [ISO/IEC 42001](https://www.iso.org/standard/42001) for AI management and continual improvement.
- [ISO/IEC 23894](https://www.iso.org/standard/77304.html) for AI risk management.
- [NIST AI RMF](https://www.nist.gov/itl/ai-risk-management-framework) and its Govern, Map, Measure, and Manage functions.
- [NIST Generative AI Profile](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-generative-artificial-intelligence) for generative-AI-specific risks.
- [OWASP Top 10 for LLM Applications](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/) for application security.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) as a deferred accessibility target.

These references guide the process; the MVP does not claim certification or formal compliance.

## 27. Definition of Done

The MVP is done when a user can start the local laboratory, inject any scenario from the catalog, observe autonomous detection and diagnosis, see a validated pull request created and merged, watch a blue-green deployment restore health, inspect automatic rollback when appropriate, and verify the complete audit trail in the custom dashboard—with all release gates passing.
