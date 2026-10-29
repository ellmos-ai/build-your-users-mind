<p align="center"><img src="../../assets/banner.svg" alt="build-your-users-mind — what you mind is what you get" width="100%"></p>

# build-your-users-mind

<p align="center">
  <a href="https://github.com/ellmos-ai/build-your-users-mind/actions/workflows/ci.yml"><img src="https://img.shields.io/github/actions/workflow/status/ellmos-ai/build-your-users-mind/ci.yml?branch=master&label=CI&logo=github" alt="CI"></a>
  <a href="https://github.com/ellmos-ai/build-your-users-mind/actions"><img src="https://img.shields.io/badge/tests-140%20passed%20%7C%20100%25%20gr%C3%BCn-brightgreen" alt="Tests"></a>
  <a href="https://github.com/ellmos-ai/build-your-users-mind/releases"><img src="https://img.shields.io/badge/version-1.1.0--dev-blue" alt="Version"></a>
  <a href="https://www.python.org"><img src="https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.13-blue" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/plattform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey" alt="Plattform"></a>
  <a href="../../NOTICE"><img src="https://img.shields.io/badge/Attribution-NOTICE-blue.svg" alt="Attribution"></a>
  <a href="../../SECURITY.md"><img src="https://img.shields.io/badge/datenschutz-100%25%20Offline%20%7C%20Zero--Egress-brightgreen" alt="Datenschutz"></a>
  <a href="../../SECURITY.md"><img src="https://img.shields.io/badge/sicherheit-Local--First%20%7C%20Redaction--Bound-success" alt="Sicherheit"></a>
  <a href="../../SECURITY.md"><img src="https://img.shields.io/badge/Sicherheits--SLA-48h%20Response%20%7C%205d%20Triage-blue" alt="Sicherheits-SLA"></a>
  <a href="../../THIRD_PARTY_LICENSES.txt"><img src="https://img.shields.io/badge/Level%201%20SBOM-Plain--Text%20Begleiter-brightgreen" alt="Level 1 SBOM"></a>
  <a href="../../MARKETING-LOG.txt"><img src="https://img.shields.io/badge/Marketing%20Log-aktiv-blue" alt="Marketing Log"></a>
  <a href="../../CHANGELOG.md"><img src="https://img.shields.io/badge/Gepr%C3%BCft-2026--10--29-blue" alt="Geprüft"></a>
  <a href="https://github.com/ellmos-ai"><img src="https://img.shields.io/badge/ecosystem-ellmos--ai-purple" alt="Ökosystem"></a>
  <a href="https://github.com/open-bricks"><img src="https://img.shields.io/badge/umbrella-open--bricks-indigo" alt="Dachorganisation"></a>
  <a href="../../llms.txt"><img src="https://img.shields.io/badge/llms.txt-bereit-brightgreen" alt="LLM-Ready"></a>
  <a href="../../LICENSE"><img src="https://img.shields.io/badge/lizenz-MIT-green" alt="Lizenz"></a>
</p>

> **What you mind is what you get.**

**🌐 [EN](../../README.md) · [DE](../../README_de.md) · [ES](../es/README.md) · [JA](../ja/README.md) · [RU](../ru/README.md) · [ZH](../zh/README.md)** — Englisch ist maßgeblich.

---

### 🧭 Schnellnavigation

- [1. Wichtigste Merkmale & Highlights](#sec-01)
- [2. Systemarchitektur & Pipeline-Design](#sec-02)
- [3. Zielgruppen-Personas & Auffindbarkeit](#sec-03)
- [4. 10-Dimensionale Vergleichsmatrix vs. Alternativen](#sec-04)
- [5. Duale Mermaid-Diagramme & Zero-Egress Datenfluss](#sec-05)
- [6. Governance & Laufzeit-Invarianten](#sec-06)
- [7. Deterministische Pipeline & Verarbeitungsschritte](#sec-07)
- [8. Entscheidungsvorhersage & Feedback-Precognition](#sec-08)
- [9. Textsimulation im Secure-Mode & Schwärzung](#sec-09)
- [10. Multi-Agenten Quell-Adapter](#sec-10)
- [11. Theory-of-Us Artefakte & Vorlagen](#sec-11)
- [12. Synthetische Demo & 60-Sekunden Schnelleinstieg](#sec-12)
- [13. Betreiber-Workflow & Decision Ledger](#sec-13)
- [14. Repository-Struktur & Architektur](#sec-14)
- [15. Schnelleinstieg & CLI-Schnittstellen](#sec-15)
- [16. Tests & Qualitätsverifikation](#sec-16)
- [17. Drittanbieter-Lizenzen, Level 1 SBOM & Attribution](#sec-17)
- [18. Sicherheitsrichtlinie, § 521 BGB & Ökosystem](#sec-18)

---

<a id="sec-01"></a>
<a id="1-features"></a>
<a id="features"></a>
<a id="1-merkmale"></a>
<a id="merkmale"></a>
<a id="schnelleinstieg"></a>
## 1. Wichtigste Merkmale & Highlights

Ein lokales Rezept für Betreiber, um aus ihren eigenen KI-Interaktionsprotokollen ein empirisches, überprüfbares **Präferenz- und Entscheidungsunterstützungsmodell** aufzubauen. Es hilft autorisierten Agenten, Feedback in wiederkehrenden Situationen zu antizipieren; es offenbart nicht die innere Psyche einer Person und darf nicht für psychologische Diagnostik, verdecktes Profiling oder autonome Entscheidungen mit hohem Risiko eingesetzt werden.

---

<a id="sec-02"></a>
<a id="2-architecture"></a>
<a id="architecture"></a>
<a id="2-architektur"></a>
<a id="system-architecture"></a>
## 2. Systemarchitektur & Pipeline-Design

Das System überführt unstrukturierte Konversationsprotokolle über vier entkoppelte Pipeline-Stufen in ein strukturiertes, evidenzbasiertes "Theory of Us"-Modell.

---

<a id="sec-03"></a>
<a id="3-target-personas--discoverability"></a>
<a id="target-personas"></a>
<a id="3-zielgruppen-personas--auffindbarkeit"></a>
<a id="zielgruppen-personas"></a>
## 3. Zielgruppen-Personas & Auffindbarkeit

`build-your-users-mind` richtet sich an vier spezifische Profile (`[PERSONA-01]` bis `[PERSONA-04]`).

---

<a id="sec-04"></a>
<a id="4-comparative-matrix-vs-alternatives"></a>
<a id="comparative-matrix"></a>
<a id="4-vergleichsmatrix-vs-alternativen"></a>
<a id="vergleichsmatrix"></a>
## 4. 10-Dimensionale Vergleichsmatrix vs. Alternativen

10-dimensionale Matrix gemappt auf die Laufzeit-Invarianten `INV-LOCAL-01` bis `INV-SLA-10`.

---

<a id="sec-05"></a>
<a id="5-dual-mermaid-diagrams--data-flow"></a>
<a id="dual-mermaid-diagrams"></a>
<a id="5-duale-mermaid-diagramme--datenfluss"></a>
<a id="duale-mermaid-diagramme"></a>
## 5. Duale Mermaid-Diagramme & Zero-Egress Datenfluss

Topologie- und Sequenzdiagramme mit vollständiger Syntax-Validierung.

---

<a id="sec-06"></a>
<a id="6-governance--runtime-invariants"></a>
<a id="governance-invariants"></a>
<a id="6-governance--laufzeit-invarianten"></a>
<a id="laufzeit-invarianten"></a>
## 6. Governance & Laufzeit-Invarianten

Zehn Invarianten `INV-LOCAL-01` bis `INV-SLA-10`.

---

<a id="sec-07"></a>
<a id="7-deterministic-pipeline--processing-steps"></a>
<a id="pipeline-steps"></a>
<a id="7-deterministische-pipeline--verarbeitungsschritte"></a>
<a id="verarbeitungsschritte"></a>
## 7. Deterministische Pipeline & Verarbeitungsschritte

Pipeline-Stufen von Extraktion bis Synthese.

---

<a id="sec-08"></a>
<a id="8-decision-prediction--feedback-precognition"></a>
<a id="decision-prediction"></a>
<a id="8-entscheidungsvorhersage--feedback-precognition"></a>
<a id="entscheidungsvorhersage"></a>
## 8. Entscheidungsvorhersage & Feedback-Precognition

v2-Vorhersageschicht mit Trennung von Empfehlung und Handlung.

---

<a id="sec-09"></a>
<a id="9-secure-mode-text-simulation--redaction"></a>
<a id="secure-mode-simulation"></a>
<a id="9-textsimulation-im-secure-mode--schwärzung"></a>
<a id="textsimulation"></a>
## 9. Textsimulation im Secure-Mode & Schwärzung

Secure-Mode Prototyp mit strikter Loopback-Grenze.

---

<a id="sec-10"></a>
<a id="10-multi-agent-source-adapters"></a>
<a id="source-adapters"></a>
<a id="10-multi-agenten-quell-adapter"></a>
<a id="quell-adapter"></a>
## 10. Multi-Agenten Quell-Adapter

Adapter für Claude, Codex, Gemini und Kimi.

---

<a id="sec-11"></a>
<a id="11-theory-of-us-artifacts--document-templates"></a>
<a id="document-templates"></a>
<a id="11-theory-of-us-artefakte--vorlagen"></a>
<a id="dokumentvorlagen"></a>
## 11. Theory-of-Us Artefakte & Vorlagen

0→4 Laufzeitschleife und living markdown Artefakte.

---

<a id="sec-12"></a>
<a id="12-synthetic-demo--60-second-quickstart"></a>
<a id="synthetic-demo"></a>
<a id="12-synthetische-demo--60-sekunden-schnelleinstieg"></a>
<a id="schnelleinstieg-demo"></a>
## 12. Synthetische Demo & 60-Sekunden Schnelleinstieg

60-Sekunden Offline-Demo mit synthetischen Daten.

---

<a id="sec-13"></a>
<a id="13-operator-workflow--decision-ledger"></a>
<a id="decision-ledger"></a>
<a id="13-betreiber-workflow--decision-ledger"></a>
<a id="entscheidungs-ledger"></a>
## 13. Betreiber-Workflow & Decision Ledger

Append-Only Kette für reale Einzelentscheidungen.

---

<a id="sec-14"></a>
<a id="14-repository-layout--architecture"></a>
<a id="repository-layout"></a>
<a id="14-repository-struktur--architektur"></a>
<a id="ordnerstruktur"></a>
## 14. Repository-Struktur & Architektur

Vollständige Modulübersicht und Ablageorte.

---

<a id="sec-15"></a>
<a id="15-quick-start--cli-interfaces"></a>
<a id="quick-start"></a>
<a id="15-schnelleinstieg--cli-schnittstellen"></a>
<a id="befehlszeilen-schnittstellen"></a>
## 15. Schnelleinstieg & CLI-Schnittstellen

Befehlszeilen-Aufrufe der Pipeline.

---

<a id="sec-16"></a>
<a id="16-testing--quality-verification"></a>
<a id="testing"></a>
<a id="16-tests--qualitätsverifikation"></a>
<a id="qualitaetssicherung"></a>
## 16. Tests & Qualitätsverifikation

Automatisierte Testsuite unter pytest.

---

<a id="sec-17"></a>
<a id="17-third-party-licenses--level-1-sbom"></a>
<a id="third-party-licenses"></a>
<a id="17-drittanbieter-lizenzen--level-1-sbom"></a>
<a id="drittanbieter-lizenzen"></a>
## 17. Drittanbieter-Lizenzen, Level 1 SBOM & Attribution

NOTICE, Level 1 SBOM und Null-Abhängigkeiten-Zertifikat.

---

<a id="sec-18"></a>
<a id="18-security-policy--sibling-ecosystem"></a>
<a id="security-policy"></a>
<a id="18-sicherheitsrichtlinie--521-bgb--ökosystem"></a>
<a id="geschwister-tools--ökosystem-matrix"></a>
## 18. Sicherheitsrichtlinie, § 521 BGB & Ökosystem

Sicherheitsrichtlinie, § 521 BGB Haftungsausschluss und Ökosystem-Matrix.
