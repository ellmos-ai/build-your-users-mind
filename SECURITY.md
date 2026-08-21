# Security Policy

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it responsibly:
- **Email (Direct Security Contact)**: [security@ellmos.ai](mailto:security@ellmos.ai)
- **Secondary Contact**: [support@lukasgeiger.com](mailto:support@lukasgeiger.com)
- **GitHub Advisory**: Use [GitHub Private Vulnerability Reporting](https://github.com/ellmos-ai/build-your-users-mind/security/advisories/new) on this repository.

Please do not open public issues for security vulnerabilities. Do not include live databases, private prompts, actual credentials, or personal records in a report; provide a minimal synthetic reproduction and redacted sample instead.

## Data & Privacy Model

`build-your-users-mind` processes only AI interaction logs the operator is authorized to use. All processing is **100% offline**, **local-first**, and **zero-egress**:
- The corpus (`STUDIE/`), classified chunks, and filled avatar files are **gitignored** by default — never commit a real corpus or generated avatar file.
- Extractors redact common current API-key/token formats (OpenAI, Anthropic, Google, GitHub, GitLab, AWS, Slack, PEM keys), credentials, asymmetric credential material, emails, IP-like values and long digit runs **before an atomic write**. Output directories and files request private permissions where the platform supports them.
- Built-ins are not a universal sensitive-data detector. Add reviewed `--redaction-rules` for health, tax, legal, financial, identity, employer, or other domain-specific data before persistence or sharing.
- Missing, unreadable, empty, or partially malformed inputs do not replace a good corpus. Overrides are explicit (`--allow-empty` / `--allow-partial`) and should follow source inspection.
- Stable evidence IDs are hashes for referential integrity, not anonymization.
- No data is sent anywhere by the scripts themselves; classification runs through whatever agent/LLM you point it at — review that agent's data handling separately.

## Non-Elevation & User-Mode Operation

All scripts, adapters, and tools in this repository operate strictly in standard user mode without requiring elevated privileges (`root` or `Administrator`). Temporary files are contained in project-local or operator-defined directories with restrictive permissions.

## Authorization & Action Boundary

Generated rules are editable preference hypotheses, not diagnoses or authority grants. Do not use them for covert profiling. An avatar may guide only already-authorized, reversible local actions. External, irreversible, novel, safety-critical, legal, medical, employment, financial, or otherwise high-impact actions require the user's direct confirmation.

## Classification Integrity & Hard Validation Gates

Treat chunk text as untrusted data, not instructions. Run `validate_classifications.py` before aggregation; missing rows, malformed fields, stale files, unknown IDs, and collisions must stop the pipeline. Use `verify_ids.py --show-text` only when intentionally exposing private text to the terminal.

## Secrets & Rotation Policy

Any secret ever committed must be **rotated**, not just removed from the working tree.

---

# Sicherheitsrichtlinie (German)

## Meldung von Schwachstellen

Sicherheitsrelevante Schwachstellen bitte vertraulich und verantwortungsvoll melden:
- **E-Mail (Direkter Sicherheitskontakt)**: [security@ellmos.ai](mailto:security@ellmos.ai)
- **Sekundärkontakt**: [support@lukasgeiger.com](mailto:support@lukasgeiger.com)
- **GitHub Advisory**: Über [GitHub Private Vulnerability Reporting](https://github.com/ellmos-ai/build-your-users-mind/security/advisories/new) in diesem Repository.

Bitte erstellen Sie keine öffentlichen Issues für Sicherheitslücken. Fügen Sie Berichten keine echten Datenbanken, privaten Prompts oder Zugangsdaten bei, sondern nutzen Sie synthetische Minimalbeispiele.

## Daten- & Datenschutzmodell

`build-your-users-mind` verarbeitet ausschließlich KI-Interaktionsprotokolle, für die der Betreiber autorisiert ist. Die gesamte Verarbeitung erfolgt **100% offline**, **Local-First** und **Zero-Egress**:
- Der Korpus (`STUDIE/`), klassifizierte Chunks und ausgefüllte Avatar-Dateien sind standardmäßig über `.gitignore` ausgeschlossen — committen Sie niemals einen echten Korpus oder generierte Avatare.
- Der Extraktor schwärzt API-Schlüssel, Token (OpenAI, Anthropic, Google, GitHub, AWS etc.), Zugangsdaten, asymmetrisches Schlüsselmaterial, E-Mails, IP-Adressen und lange Ziffernfolgen **vor dem atomaren Schreiben**.
- Die integrierten Muster sind kein universeller Detektor für alle sensiblen Daten. Fügen Sie geprüfte `--redaction-rules` für Gesundheits-, Steuer-, Rechts-, Finanz- oder Unternehmensdaten hinzu.
- Fehlende, unlesbare oder teilweise fehlerhafte Eingaben überschreiben keinen bestehenden Korpus ohne explizite Flags (`--allow-empty`, `--allow-partial`).
- Stabile Evidenz-IDs sind deterministische Hashes für relationale Integrität, keine Anonymisierung.
- Die Skripte selbst senden zu keinem Zeitpunkt Daten an externe Server.

## User-Mode & Non-Elevation

Alle Skripte, Adapter und Werkzeuge laufen strikt im Standard-Benutzermodus (User-Mode) ohne Administrator- oder Root-Rechte.

## Autorisierungs- & Aktionsgrenzen

Generierte Regeln sind überprüfbare Präferenzhypothesen, keine psychologischen Diagnosen oder Blanko-Autorisierungen. Verdecktes Profiling ist untersagt. Der Avatar darf ausschließlich vorautorisierte, reversible lokale Aktionen anleiten. Externe, irreversible, neuartige oder folgenschwere Aktionen erfordern stets die direkte Bestätigung des Nutzers.

## Klassifizierungs-Integrität & Hard-Gates

Chunk-Texte werden als unvertrauenswürdige Daten behandelt, nicht als Instruktionen. `validate_classifications.py` fungiert als hartes Gate vor der Aggregation: Fehlende Zeilen, ungültige Felder, veraltete Dateien oder ID-Kollisionen brechen die Pipeline ab.

## Geheimnisse (Secrets) & Rotation

Jedes Geheimnis, das jemals committet wurde, muss **rotiert** (ungültig gemacht und neu ausgestellt) werden, nicht bloß aus dem Arbeitsbaum gelöscht werden.
