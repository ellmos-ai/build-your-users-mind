# Security Policy

## Reporting
Please report vulnerabilities via **GitHub Private Vulnerability Reporting** on this repository
(Security → Report a vulnerability). Do not open public issues for security problems.

## Data & privacy model
This tool processes **your own AI interaction logs**. Treat the produced corpus and avatar files as
**private personal data**:
- The corpus (`STUDIE/`), classified chunks, and filled avatar files are **gitignored** by default —
  never commit a real corpus.
- The extractor redacts API keys, tokens, emails, IP-like and long digit runs **before writing**.
- **Health, tax, or other sensitive content is the operator's responsibility** to redact before the
  corpus or any avatar file leaves a private environment.
- No data is sent anywhere by the scripts themselves; classification runs through whatever agent/LLM
  you point it at — review that agent's data handling separately.

## Secrets
Any secret ever committed must be **rotated**, not just removed from the working tree.
