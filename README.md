# dark-factory-lab

Local, autonomous, auditable observability and remediation laboratory.

This repository is the **runtime product**. Discovery skills stay in [`sdlc-intent-ai-agents`](https://github.com/adilsonbna/sdlc-intent-ai-agents) (instruction-first v1).

North star: [`intent.md`](intent.md) (still Draft until a human baseline PR).

## Status

Milestone 1: repository and policy foundation.

Do not add application runtime (Compose, agents, Gemini) until `requirements.md` has MVP must-haves with acceptance outcomes.

## Layout

```text
apps/web                 React dashboard (stub)
apps/api                 FastAPI backend (stub)
services/orchestrator    Deterministic incident state machine (stub)
generators               Synthetic telemetry / fault injectors (stub)
eval/scenarios           24-scenario catalog (stub)
infra/compose            Docker Compose lab (stub)
docs/adr                 Architecture decision records
docs/runbooks            Start, stop, reset, incident, rollback, kill switch
```

## Commands (placeholders until milestone 2)

```bash
make up      # start the lab
make down    # stop the lab
make reset   # wipe local lab state
make eval    # run the evaluation harness
```

## SDLC

1. Change that affects goals, autonomy, data, model, or thresholds → update `intent.md` first.
2. Open an issue with REQ-id and acceptance.
3. One coherent PR with evidence.
4. Independent review for approval, security, data, deploy, or audit changes.
5. Persistent changes go through GitHub pull requests. Agents do not self-approve.

## License

MIT. See [LICENSE](LICENSE).
