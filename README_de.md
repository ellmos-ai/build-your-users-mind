> Englisch (README.md) ist maßgeblich; diese Übersetzung kann veraltet sein.

# build-your-users-mind

> **What you mind is what you get.**

**🌐 [EN](README.md) · [DE](README_de.md) · [ES](README_es.md) · [JA](README_ja.md) · [RU](README_ru.md) · [ZH](README_zh.md)** — Englisch ist maßgeblich; Übersetzungen können veraltet sein.

Ein Rezept für jeden KI-Agenten (Claude, Codex, Gemini/agy, Kimi, …), um aus seinen eigenen Interaktionsprotokollen ein empirisches, sich selbst verbesserndes **theory-of-mind-Modell seines eigenen Nutzers** aufzubauen – und im Sinne des Nutzers zu handeln, wenn dieser abwesend ist.

Es funktioniert per **feedforward**: Anstatt auf Feedback zu warten, das während der Abwesenheit des Nutzers nicht eintrifft, *sagt der Agent das Feedback des Nutzers voraus, bevor es kommt*, und nutzt diese Vorhersage als Leit- oder Belohnungssignal – danach bewertet er die Vorhersage anhand der Realität, um besser zu werden.

## „Ich weiß, was du willst.“

Dieser Satz bringt es auf den Punkt. Der Agent liest die vergangenen Prompts des Nutzers, destilliert, **was der Nutzer entscheidet, wie er es formuliert und ob er zufrieden war**, und wandelt dies in eine kleine Reihe lebendiger Dokumente um, die er konsultieren kann, sobald eine Entscheidung ansteht und der Nutzer nicht erreichbar ist.

Es ist **keine** Chatbot-Persona und **kein** schwerfälliges Framework – es ist eine Methode + eine Handvoll Skripte + Dokumentvorlagen. Der einzige agentspezifische Teil ist der *source adapter* (wo jeder Agent seine eigenen Protokolle liest). Alles andere ist universell.

## Wie es funktioniert — feedback precognition

Ein Laufzeit-Loop von 0 bis 4 (siehe `templates/START.md`):

| Schritt | Datei | Rolle |
|---|---|---|
| 0 | Projekt `DECISIONS.md` | Projektspezifische Entscheidungen gewinnen (spezifischer) |
| 1 | `WHAT-<USER>-SAID` | **Evidenzbasierte** Regeln/Entscheidungen (mit Zitaten von Prompt-IDs) |
| 2 | `WHAT-WOULD-<USER>-SAY` | **precognition** (Vorahnung) — vorhergesagtes Feedback + Konfidenz (🟢/🟡/🔴) |
| 3 | `WHAT-I-DID…` + `MY-ACTIONS.txt` | Protokoll der auf Basis der Vorhersage ergriffenen Maßnahmen |
| 4 | `WHAT-<USER>-SAID-ABOUT…` | **Evaluierung** — Vorhersage vs. Realität → verbessert (1) und (2) |

Qualitätsmetrik = **wie oft die erwartete Reaktion mit dem tatsächlichen späteren Feedback des Nutzers übereinstimmt.**
Bei 🔴 (neu/kein Muster) lautet die Regel: **Eskalieren, nicht raten.**

### Pipeline (Modell erstellen)

1. **Extraktion** (`scripts/corpus_extract.py`) — deterministisch: Nur vom Menschen geschriebene Prompts aus den Protokollen ziehen, synthetische Runden filtern, **Geheimnisse schwärzen**, jeden Prompt mit dem `outcome_signal` der nächsten Runde verknüpfen (Lob/Korrektur/erneutes Senden/keines).
2. **Chunking** (`scripts/chunk_corpus.py`) — Deduplizierung, optionale Domänen, Größen-Chunks für den Schwarm.
3. **Klassifizierung** (Schwarm) — 8-Typen-Taxonomie (`TAXONOMY.md`) + decision_kind + Formulierungsmuster. Hierarchischer Schwarm (Domain-Leads × Chunk-Worker); siehe mitgelieferten `skills/swarm-operations/`.
4. **Aggregation** (`scripts/aggregate_stats.py`) — Typverteilung, B:K-Verhältnis, Wendepunkte.
5. **Erstellung** (Authoring) der Avatar-Dateien aus `templates/` und **Verbindung** (Binding) eines kurzen Pointers in die eigene Speicher-/Regeldatei des Agenten (Claude `CLAUDE.md`, Codex `GPT.md`/`AGENTS.md`, Gemini `GEMINI.md`, …).

Siehe `SKILL.md` für das vollständige Rezept und `SOURCE-ADAPTERS.md` für die Protokoll-Speicherorte der einzelnen Agenten.

## Theory of us — theoretischer Hintergrund

Das System modelliert die **Dyade** (Agent ↔ Nutzer), nicht nur den Nutzer isoliert – eine *Theory of Us* (Theorie über uns).
Es basiert auf:
- Forschung zu **Theory of Mind** für LLM-Agenten — Die Vorhersage und Konditionierung auf den mentalen Zustand eines Gesprächspartners verbessert die Ergebnisse (z. B. *ToM-SWE*, arXiv 2510.21903; *Infusing Theory of Mind into Socially Intelligent LLM Agents*, 2509.22887; *Persistent Memory & User Profiles*, 2510.07925).
- **Prompt-Archaeology** (L. Geiger) — die Methode zur Klassifizierung vollständiger Mensch-KI-Interaktionsprotokolle, deren 8-Typen-Taxonomie dieses Modul wiederverwendet (`TAXONOMY.md`).
- Eine bekannte Grenze: LLM-ToM ist **robust bei wiederkehrenden Fällen, aber anfällig bei neuartigen/adversarialen Variationen** — daher die Vertrauensstufen und die Regel „Eskalieren, nicht raten“.

## Bias & Grenzen (lesen, bevor man darauf vertraut)

- **Stille Zustimmung ist unsichtbar** — Nutzer schreiben Korrekturen, kein Lob → das Modell überrepräsentiert Korrekturen und tendiert zu „kritisch“. Entsprechend kalibrieren.
- **Evidenz-IDs stammen aus LLM-Synthese** — tragende Belege anhand des Rohkorpus überprüfen.
- **Klassifikator-Bias** — Stichprobenartige Überprüfung; Berichterstattung über die Interrater-Reliabilität bei ernsthafter Nutzung.

## Privatsphäre & Schwärzung

Der Extraktor schwärzt API-Schlüssel, Token, E-Mails, IP-ähnliche Adressen und lange Ziffernfolgen **vor dem Schreiben**.
**Es liegt in der Verantwortung des Agenten, gesundheitliche, steuerliche oder andere sensible Nutzerinhalte zu schwärzen**, bevor der Korpus oder eine Avatar-Datei den privaten Bereich verlässt. Committe niemals einen echten Korpus — siehe `.gitignore`.

## Suggested GitHub topics

`theory-of-mind` · `llm` · `user-modeling` · `personalization` · `ai-agents` · `prompt-analysis` · `feedback` · `decision-support`

## Credits & Lizenz

Methode: *Prompt-Archaeology* von Lukas Geiger. Modul & Konzept: Lukas Geiger (+ Claude).
Mitgelieferte Abhängigkeit: `swarm-operations` Skill. **MIT** — siehe `LICENSE`.
Referenzimplementierung (privat, nicht ausgeliefert): eine persönliche Instanz, die auf den eigenen Protokollen des Autors aufbaut.
