# Security Policy / Sicherheitsrichtlinie

## English

### Execution Safety, Local-First Isolation, and Privacy Invariants

`build-your-users-mind` operates on sensitive interaction logs with strict fail-safe privacy and safety invariants:

1. **100% Local-First & Zero-Egress**: The extraction, merging, chunking, and validation pipeline runs entirely offline within the operator's local environment. No telemetry, user interaction data, or prompt logs are transmitted to external endpoints or third-party servers by this repository's scripts.
2. **Non-Elevation & Unprivileged Execution**: Operates strictly in standard user space without requiring administrator or root privileges.
3. **Fail-Closed Secret Redaction**: Built-in regex filters redact common API keys, bearer tokens, passwords, private keys, emails, IP addresses, and long digit runs prior to atomic file writes. Domain-specific sensitive data requires operator-defined `--redaction-rules`.
4. **Gitignore Safety & Data Containment**: Output corpora (`STUDIE/`, `00_corpus.jsonl`), classification chunks, and populated avatar files are gitignored by default. Real personal corpora and interaction logs must never be committed to version control.
5. **Authorization and Non-Diagnosis Boundary**: Generated preference models are hypotheses for authorized, reversible agent assistance. They do not grant autonomous authority and must never be used for psychological profiling, covert surveillance, or high-stakes autonomous actions without human confirmation.

### Prediction and Secure-Mode Generation

Recommendation, likely choice, simulated wording, explicit user decision, and execution authority are separate records. Generated text is never a user statement or primary evidence. Decision events require explicit feedback and remain private generated data.

The Secure-Mode prototype re-applies built-in redaction to retrieved evidence, omits the private prompt from its result, rejects non-loopback model endpoints, and never starts a model service. A loopback endpoint is still a separate local service whose model and retention settings the operator must review. Domain-sensitive information still requires custom redaction rules. Simulation output must not be sent to another person or system as if authored by the operator.

### Supported Versions

| Version | Supported | Notes |
|---|---|---|
| `1.1.x` | :white_check_mark: | Active development & release line |
| `< 1.1.0` | :x: | Legacy pre-1.1 preview releases |

### Reporting a Vulnerability

If you discover a security vulnerability, data leak risk, or redaction bypass, please report it privately to the maintainers rather than opening a public issue:

- **Security Team**: [security@ellmos.ai](mailto:security@ellmos.ai)
- **Ecosystem Security**: [security@open-bricks.org](mailto:security@open-bricks.org)
- **Primary Maintainer**: [support@lukasgeiger.com](mailto:support@lukasgeiger.com)
- **Ecosystem Lead**: [lukas@open-bricks.org](mailto:lukas@open-bricks.org)
- **GitHub Security Advisories**: [Open a Private Advisory](https://github.com/ellmos-ai/build-your-users-mind/security/advisories)
- **Response SLA**: Initial triage and acknowledgment within 48 hours.

---

## Deutsch

### Ausführungssicherheit, Local-First Isolation und Datenschutz-Invarianten

`build-your-users-mind` verarbeitet sensible Interaktionsprotokolle unter Einhaltung strikter Sicherheits- und Datenschutzregeln:

1. **100% Local-First & Zero-Egress**: Die gesamte Extraktions-, Merge-, Chunking- und Validierungs-Pipeline läuft vollständig offline auf dem lokalen System. Es erfolgt keinerlei Übertragung von Logdaten oder Telemetrie an externe Server durch die Skripte dieses Repositories.
2. **Unprivilegierter User-Mode (Non-Elevation)**: Alle Werkzeuge laufen im normalen Benutzerkontext ohne Administrator- oder Root-Rechte.
3. **Fail-Closed Geheimnis-Schwärzung**: Integrierte Filter schwärzen API-Schlüssel, Tokens, Passwörter, private Schlüssel, E-Mails, IP-Adressen und lange Zahlenketten vor dem atomaren Schreiben. Domänenspezifische Daten erfordern vom Betreiber definierte `--redaction-rules`.
4. **Gitignore-Schutz & Datenisolation**: Reale Korpora (`STUDIE/`, `00_corpus.jsonl`), Chunks und ausgefüllte Avatar-Dateien sind standardmäßig in `.gitignore` gesperrt und dürfen niemals in ein Git-Repository eingecheckt werden.
5. **Autorisierungs- und Nicht-Diagnose-Grenze**: Generierte Präferenzmodelle sind überprüfbare Hypothesen für autorisierte, reversible Agentenaktionen. Sie dürfen nicht für verdecktes Profiling, psychologische Diagnosen oder folgenreiche autonome Entscheidungen ohne menschliche Bestätigung eingesetzt werden.

### Vorhersage und Generierung im sicheren Modus

Empfehlung, wahrscheinliche Wahl, simulierte Formulierung, ausdrückliche Nutzerentscheidung und Ausführungsbefugnis sind getrennte Datensätze. Generierter Text ist weder eine Aussage des Nutzers noch Primärevidenz. Entscheidungsereignisse benötigen ausdrückliches Feedback und bleiben private, generierte Daten.

Der Prototyp für den sicheren Modus schwärzt abgerufene Evidenz erneut, lässt den privaten Prompt aus dem Ergebnis weg, lehnt Modell-Endpunkte außerhalb des Loopbacks ab und startet niemals selbst einen Modelldienst. Auch ein Loopback-Endpunkt ist ein separater lokaler Dienst, dessen Modell- und Aufbewahrungseinstellungen geprüft werden müssen. Domänensensible Informationen benötigen weiterhin eigene Schwärzungsregeln. Simulationsergebnisse dürfen nicht gegenüber anderen Personen oder Systemen als Äußerung des Nutzers ausgegeben werden.

### Unterstützte Versionen

| Version | Unterstützt | Status |
|---|---|---|
| `1.1.x` | :white_check_mark: | Aktive Release-Linie |
| `< 1.1.0` | :x: | Veraltete Vorschauversionen |

### Sicherheitslücke melden

Wenn Sie eine Sicherheitslücke, Schwärzungsumgehung oder unzureichende Isolation feststellen, melden Sie diese bitte vertraulich an die Maintainer:

- **Sicherheitsteam**: [security@ellmos.ai](mailto:security@ellmos.ai)
- **Ökosystem-Sicherheit**: [security@open-bricks.org](mailto:security@open-bricks.org)
- **Maintainer**: [support@lukasgeiger.com](mailto:support@lukasgeiger.com)
- **Ökosystem-Leitung**: [lukas@open-bricks.org](mailto:lukas@open-bricks.org)
- **GitHub Security Advisories**: [Privaten Sicherheitsbericht öffnen](https://github.com/ellmos-ai/build-your-users-mind/security/advisories)
- **Reaktionszeit (SLA)**: Erste Rückmeldung innerhalb von maximal 48 Stunden.
