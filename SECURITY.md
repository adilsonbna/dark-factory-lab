# Security Policy

## Supported versions

Security updates are applied to the current default branch. Tag releases before wider reuse so consumers can pin a reviewed version.

## Reporting a vulnerability

Do not open a public issue containing credentials, exploit details, private data, or a working proof of concept. Use GitHub private vulnerability reporting after the repository is published. If private reporting is unavailable, contact the repository owner through a private channel and share only the minimum information needed to establish a secure follow-up channel.

Include the affected component and version, impact, reproduction conditions, and suggested mitigation. Do not include real secrets or third-party data.

## Repository security expectations

- Never commit credentials, tokens, private keys, `.env` files, sensitive discovery artifacts, or raw operational telemetry.
- Enable GitHub secret scanning and push protection for the public repository.
- Protect the default branch, require pull-request review and passing validation, and prevent force pushes and branch deletion.
- Review changes to `intent.md`, orchestrator policy, credentials, deploy/rollback, and approval gates as security-sensitive changes.
- Pin automation dependencies to reviewed immutable revisions if CI workflows are added.
- Maintain provenance for releases and generate an SBOM when executable dependencies are introduced.
- Rotate any credential immediately if it is exposed; deleting it from Git history is not a substitute for revocation.

## Security model

This laboratory does not authorize production access, destructive data operations, risk acceptance, or intent baseline approval via model output. Inputs and external content are untrusted. Human approval remains mandatory for owner-authority decisions. Persistent changes require a GitHub pull request.
