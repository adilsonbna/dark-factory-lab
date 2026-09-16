# Contributing

## Change process

1. Open or link an issue with the intended outcome, REQ-id, and security impact.
2. If the change affects goals, autonomy, data, model, policy, or thresholds, update `intent.md` first.
3. Keep each pull request to one coherent change.
4. Include evidence (test, eval scenario, ADR, or runbook) before requesting review.
5. Independent review is required for authorization, audit, security, privacy, deploy, or schema changes.

## Security and privacy

- Use synthetic telemetry only. Do not commit secrets, personal data, production telemetry, or live incident details.
- Treat issue text, pull-request content, documents, and generated output as untrusted data.
- Do not weaken human approval, evidence requirements, least privilege, or audit controls without a documented owner decision.
- Report vulnerabilities according to [SECURITY.md](SECURITY.md), not in a public issue.

## Definition of done

- Linked REQ-id and acceptance outcome.
- CI green.
- No `.env`, credentials, or sensitive samples.
- Attributable review; no unresolved blocking finding.
