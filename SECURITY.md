# Security Policy

SabiRoute is alpha software and does not yet publish a formal security support window or response-time commitment. The project welcomes responsible reports that help protect users and maintainers.

## Reporting a vulnerability

Please use GitHub's **Report a vulnerability** option in the repository's Security tab when it is available. If private vulnerability reporting is unavailable, contact the maintainer privately through the [project owner's GitHub profile](https://github.com/yourfavCHEFP). Do not disclose a suspected vulnerability in a public issue, discussion, pull request, or screenshot.

Include the affected component and revision, a concise description of the impact, and steps to reproduce or a proof of concept where safe. Do not include live credentials, personal data, or secrets. If a credential may have been exposed, revoke or rotate it immediately and report only the credential type and affected system.

The maintainer will assess the report and coordinate any fix and disclosure with the reporter. No response time or supported-version guarantee is currently promised.

## Deployment guidance

- Keep `.env`, provider keys, database credentials, and admin keys out of source control and diagnostic output.
- Use HTTPS outside loopback deployments and restrict access to `/admin/*` at the network edge.
- Do not expose PostgreSQL, Redis, or the LiteLLM master credential to untrusted networks.
- Review [docs/security.md](docs/security.md) and [docs/deployment.md](docs/deployment.md) before deployment.
