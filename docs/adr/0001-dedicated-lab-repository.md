# ADR-0001: Implement the lab in a dedicated repository

- Status: Accepted
- Date: 2026-09-16
- Decision owner: Project owner
- Reviewers: Maintainers
- Supersedes: None
- Superseded by: None

## Context

`sdlc-intent-ai-agents` is an instruction-first skill suite (ADR-0006 there). The product in `intent.md` needs runtime code, Docker, and CI.

## Decision

Runtime for the observability/remediation laboratory lives in `dark-factory-lab`. Discovery skills remain in `sdlc-intent-ai-agents`.

## Consequences

- Skill contracts can stay dependency-free.
- This repository owns application supply chain, CI, and deployment evidence.
- Intent baseline must be copied or linked; material intent changes are dual-tracked until a sync process exists.
