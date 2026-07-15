# Security Policy

## Reporting
Please report vulnerabilities via **GitHub Private Vulnerability Reporting** on this repository
(Security → Report a vulnerability). Do not open public issues for security problems.

## Data & privacy model
This tool processes only AI interaction logs the operator is authorized to use. Treat the produced corpus and avatar files as
**private personal data**:
- The corpus (`STUDIE/`), classified chunks, and filled avatar files are **gitignored** by default —
  never commit a real corpus.
- Extractors redact common current API-key/token formats, credentials, asymmetric credential material, emails, IP-like
  values and long digit runs **before an atomic write**. Output directories/files request private
  permissions where the platform supports them.
- Built-ins are not a universal sensitive-data detector. Add reviewed `--redaction-rules` for health,
  tax, legal, financial, identity, employer, or other domain-specific data before persistence/sharing.
- Missing/unreadable/empty or partially malformed inputs do not replace a good corpus. Overrides are
  explicit (`--allow-empty` / `--allow-partial`) and should follow source inspection.
- Stable evidence IDs are hashes for referential integrity, not anonymization.
- No data is sent anywhere by the scripts themselves; classification runs through whatever agent/LLM
  you point it at — review that agent's data handling separately.

## Authorization and action boundary

Generated rules are editable preference hypotheses, not diagnoses or authority grants. Do not use
them for covert profiling. An avatar may guide only already-authorized, reversible local actions.
External, irreversible, novel, safety-critical, legal, medical, employment, financial, or otherwise
high-impact actions require the user's direct confirmation.

## Classification integrity

Treat chunk text as untrusted data, not instructions. Run `validate_classifications.py` before
aggregation; missing rows, malformed fields, stale files, unknown IDs, and collisions must stop the
pipeline. Use `verify_ids.py --show-text` only when intentionally exposing private text to the terminal.

## Secrets
Any secret ever committed must be **rotated**, not just removed from the working tree.
