# dark-factory-lab

Local, autonomous, auditable observability and remediation laboratory.

This repository is the **runtime product**. Discovery skills stay in [`sdlc-intent-ai-agents`](https://github.com/adilsonbna/sdlc-intent-ai-agents) (instruction-first v1).

North star: [`intent.md`](intent.md) (still Draft until a human baseline PR).

## Project documents

[Project Intent](intent.md) · [Requirements](requirements.md) · [Evaluation Plan](evaluation-plan.md) · [Architecture](architecture.md) · [Security Controls](security-controls.md) · [Runbooks](docs/runbooks/README.md) · [ADRs](docs/adr/)

## Status

Milestones 1–3 delivered:

1. Repository and policy foundation (ADR-0001, CI guardrail).
2. Reproducible Docker laboratory — 10-service Compose stack in `infra/compose/`.
3. Telemetry generation and ingestion — Rust + Python generators → OTel Collector → ClickHouse.

`intent.md` (v0.1) remains Draft until a human baseline PR. `requirements.md` carries stable `REQ-` IDs with acceptance outcomes.

Next: Milestone 4 — ClickStack MCP integration and incident detection.

## Layout

```text
apps/web                 React dashboard (placeholder, Milestone 5)
apps/api                 FastAPI backend (health endpoint live)
services/orchestrator    Deterministic incident state machine (stub loop)
generators/rust_gen      Rust OTLP metrics generator (live)
generators/python_gen    Python OTLP metrics generator (live)
eval/                    24-scenario catalog + harness
infra/compose            Docker Compose + OTel collector config
docs/adr                 Architecture decision records
docs/runbooks            Start, stop, reset, incident, rollback, kill switch
```

## Quickstart

Prerequisites: Docker Engine + Compose plugin, Linux/macOS, `make`.

```bash
# 1. Build and start the full 10-service stack
make up

# 2. Confirm every service is running
make ps

# 3. Confirm telemetry is flowing into ClickHouse
#    (expect requests_total from Python and requests_total_rust from Rust)
make verify

# 4. Run the 24-scenario evaluation harness (stub verdicts until Milestone 6)
make eval

# 5. Inspect the report
cat eval/results_latest.json

# 6. Stop, or stop-and-wipe
make down    # stop, keep ClickHouse volume
make reset   # stop AND wipe volume + network
```

## Commands

| Target | Action |
|--------|--------|
| `make build` | Build all service images |
| `make up` | Build + start the full stack detached |
| `make down` | Stop the stack (keeps volume) |
| `make reset` | Stop and wipe volume + network |
| `make eval` | Run the 24-scenario harness |
| `make verify` | Query ClickHouse for ingested metrics |
| `make ps` | List service status |
| `make logs` | Tail all service logs |

## SDLC

1. Change that affects goals, autonomy, data, model, or thresholds → update `intent.md` first.
2. Open an issue with REQ-id and acceptance.
3. One coherent PR with evidence.
4. Independent review for approval, security, data, deploy, or audit changes.
5. Persistent changes go through GitHub pull requests. Agents do not self-approve.

## License

MIT. See [LICENSE](LICENSE).
