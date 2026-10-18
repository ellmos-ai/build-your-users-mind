# Contributing to build-your-users-mind

[English](#english) · [Deutsch](#deutsch)

---

<a id="english"></a>
## English

Thank you for contributing to `build-your-users-mind`. We aim to keep the local-first architecture, deterministic safety gates, public documentation, and empirical user-modeling recipes accurate, privacy-preserving, and consistent.

### 1. Architecture, Privacy Boundaries & Security Invariants

- **Local-first & Zero-Egress core:** All corpus extraction (`corpus_extract.py`), log merging (`merge_corpora.py`), chunking (`chunk_corpus.py`), validation (`validate_classifications.py`), and decision prediction scoring (`score_predictions.py`) operate strictly within the Python standard library. Do not introduce network calls, cloud telemetry, or third-party tracking into runtime scripts.
- **Strict Loopback Boundary in Secure-Mode:** The optional simulated text avatar (`secure_text_avatar.py`) strictly limits socket connections to loopback (`127.0.0.1`, `localhost`, `::1`) over HTTP. No outbound external connections are permitted.
- **Never submit real private data:** Never commit real interaction logs, generated user profiles, filled avatar documents (`WHAT-USER-SAID.md`, `WHAT-WOULD-USER-SAY.md`), credentials, `.env` files, or private filesystem paths. All adapter fixtures and test cases must use purely synthetic test data.
- **Unprivileged user-mode operation (`RunAsInvoker`):** All CLI routines and scripts must run within standard user privileges without administrative or root elevation (no sudo or UAC prompts).
- **Statutory Liability Disclaimer & Security SLA:** Unpaid open-source provision governed by § 521 BGB Gefälligkeitsrecht. Security disclosures are handled with a committed 48-hour response time via `security@ellmos.ai` and `security@open-bricks.org` (or GitHub Private Vulnerability Reporting).

### 2. Local Development Workflow (Plan D)

- Work strictly from a local Git clone at the repository root (`C:\_Local_DEV\repos\build-your-users-mind` or equivalent local clone directory).
- Cloud storage folders (e.g. OneDrive) serve solely as gitless mirrors/projections for multi-device visibility; never develop or initialize `.git` directly inside cloud-synchronized folders.

### 3. Version Freeze Discipline (T-20260920-167562623)

- Package versions (e.g., `version = "1.1.0-dev"` in `pyproject.toml` and `ellmos-module.v2.json`) remain strictly frozen during routine maintenance, technical hygiene, and marketing runs.
- Version increments are reserved exclusively for dedicated, user-authorized release tickets.
- All technical hygiene improvements, new contract tests, and documentation refinements belong under `## Unreleased` in `CHANGELOG.md`.

### 4. Quality Gates and Local Verification

Before submitting a pull request or committing changes, execute the full local quality verification suite:

```bash
# 1. Bytecode compilation
python -m compileall -q scripts tests examples

# 2. Ruff code formatting and linting
ruff check .

# 3. Pytest suite
pytest -v

# 4. Unittest discovery
python -m unittest discover -s tests -v

# 5. Schema and manifest contract validation
python -c "import json; json.load(open('ellmos-module.v2.json', encoding='utf-8')); json.load(open('schemas/classification.schema.json', encoding='utf-8'))"

# 6. Git cleanliness and version freeze verification
git diff --check
git diff -G"version = "
```

---

<a id="deutsch"></a>
## Deutsch

Vielen Dank für deinen Beitrag zu `build-your-users-mind`. Wir halten die lokale Architektur, deterministische Sicherheits-Tore, öffentliche Dokumentation und empirische Modellierungs-Rezepte präzise, datenschutzwahrend und konsistent.

### 1. Architektur, Privatsphäre-Grenzen & Sicherheitsinvariante

- **Lokaler & Zero-Egress Kern:** Alle Skripte zur Korpus-Extraktion (`corpus_extract.py`), Zusammenführung (`merge_corpora.py`), Chunk-Erstellung (`chunk_corpus.py`), Validierung (`validate_classifications.py`) und Bewertung (`score_predictions.py`) arbeiten rein mit der Python-Standardbibliothek. Führe keine Netzwerkaufrufe, Cloud-Telemetrie oder externe Tracking-Dienste in Laufzeit-Skripte ein.
- **Strikte Loopback-Grenze im Secure-Modus:** Der optionale Text-Avatar (`secure_text_avatar.py`) beschränkt Socket-Verbindungen strikt auf Loopback (`127.0.0.1`, `localhost`, `::1`) über HTTP. Ausgehende externe Verbindungen sind unzulässig.
- **Niemals reale persönliche Daten einreichen:** Reiche niemals reale Interaktionsprotokolle, generierte Nutzerprofile, ausgefüllte Avatar-Dokumente (`WHAT-USER-SAID.md`, `WHAT-WOULD-USER-SAY.md`), Zugangsdaten, `.env`-Dateien oder private Dateipfade ein. Alle Adapter-Fixtures und Tests müssen rein synthetische Daten verwenden.
- **Unprivilegierter Betrieb (`RunAsInvoker`):** Alle CLI-Routinen und Skripte laufen in Standard-Benutzerrechten ohne administrative Rechte oder Root-Erhöhung (kein sudo, keine UAC-Prompts).
- **Gesetzlicher Haftungsausschluss & Sicherheits-SLA:** Unentgeltliche Bereitstellung nach § 521 BGB (Gefälligkeitsrecht). Sicherheitsmeldungen werden verbindlich innerhalb von 48 Stunden über `security@ellmos.ai` und `security@open-bricks.org` (oder GitHub Private Vulnerability Reporting) bearbeitet.

### 2. Lokaler Entwicklungsworkflow (Plan D)

- Entwickle ausschließlich in einem lokalen Git-Klon im Repository-Wurzelverzeichnis (`C:\_Local_DEV\repos\build-your-users-mind` bzw. lokalem Entwicklungsordner).
- Cloud-Speicherordner (wie OneDrive) dienen rein als gitlose Spiegel/Projektionen für die geräteübergreifende Verfügbarkeit; niemals `.git` in Cloud-Synchronisationsordnern betreiben.

### 3. Versions-Einfrier-Disziplin (T-20260920-167562623)

- Paketversionen (z. B. `version = "1.1.0-dev"` in `pyproject.toml` und `ellmos-module.v2.json`) bleiben bei routinemäßiger Pflege, technischer Hygiene und Marketing-Läufen strikt unverändert.
- Versionsanhebungen sind ausdrücklich separat autorisierten Release-Vorgängen vorbehalten.
- Alle technischen Pflege-Maßnahmen, neuen Vertragstests und Dokumentations-Aktualisierungen gehören unter `## Unreleased` in `CHANGELOG.md`.

### 4. Qualitätsprüfungen und lokale Verifikation

Führe vor jedem Commit oder Pull Request die vollständige Qualitätsprüfung durch:

```bash
# 1. Bytecode-Kompilierung
python -m compileall -q scripts tests examples

# 2. Ruff Linter- und Formatierungsprüfung
ruff check .

# 3. Pytest-Testsuite
pytest -v

# 4. Unittest-Discovery
python -m unittest discover -s tests -v

# 5. Schema- und Manifest-Validierung
python -c "import json; json.load(open('ellmos-module.v2.json', encoding='utf-8')); json.load(open('schemas/classification.schema.json', encoding='utf-8'))"

# 6. Whitespace- und Versions-Integritätsprüfung
git diff --check
git diff -G"version = "
```
