# dark-factory-lab

Local, autonomous, auditable observability and remediation laboratory.

This repository is the **runtime product**. Discovery skills stay in [`sdlc-intent-ai-agents`](https://github.com/adilsonbna/sdlc-intent-ai-agents) (instruction-first v1).

North star: [`intent.md`](intent.md) (still Draft until a human baseline PR).

## Project documents

[Project Intent](intent.md) · [Requirements](requirements.md) · [Evaluation Plan](evaluation-plan.md) · [Architecture](architecture.md) · [Security Controls](security-controls.md) · [Runbooks](docs/runbooks/README.md) · [ADRs](docs/adr/)

## Status

`intent.md` (v0.1) remains Draft until a human baseline PR. `requirements.md` carries stable `REQ-` IDs with acceptance outcomes.

| Milestone | Reported status | Repository evidence |
|-----------|-----------------|---------------------|
| 1–3 | Complete | Foundation, Compose laboratory, generators, OTel Collector, and ClickHouse are versioned. |
| 4 | Complete | Read-only MCP-shaped API tools exist; the Compose `clickstack` service is still a placeholder, so live ClickStack MCP must be re-verified. |
| 5 | Complete | React and FastAPI implementations are present. |
| 6 | Complete and tested | Deterministic state machine and focused tests are present. |
| 7 | In progress | Structured Triage and Investigation pipeline, Gemini adapter, evidence policies, and tests are implemented; a live model/MCP incident run remains. |
| 8–12 | Pending | No completion claim. |

The evaluation harness currently emits simulated results. Its `PASS` values are development fixtures and are not release qualification evidence.

## Layout

```text
apps/web                 React dashboard (DevOps and management views)
apps/api                 FastAPI backend, auth, telemetry, MCP, and dashboard routes
services/orchestrator    State machine plus Triage/Investigation agent pipeline
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

# 4. Run the 24-scenario development harness (simulated verdicts; not a release gate)
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

Focused orchestrator verification:

```bash
docker compose -f infra/compose/docker-compose.yml build orchestrator
docker compose -f infra/compose/docker-compose.yml run --rm --no-deps orchestrator python3 -m pytest -q
```

Agent execution is fail-closed unless `GEMINI_API_KEY` is configured. The pinned default model is `gemini-3.8-flash`; override it with `GEMINI_MODEL` only through a reviewed configuration change.

State-changing dashboard actions require `OPERATOR_TOKEN`. The browser requests it when the operator first uses the kill switch and retains it only in session storage for the current tab session.

## SDLC

1. Change that affects goals, autonomy, data, model, or thresholds → update `intent.md` first.
2. Open an issue with REQ-id and acceptance.
3. One coherent PR with evidence.
4. Independent review for approval, security, data, deploy, or audit changes.
5. Persistent changes go through GitHub pull requests. Agents do not self-approve.

## License

MIT. See [LICENSE](LICENSE).
