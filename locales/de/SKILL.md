---
name: build-your-users-mind
description: Anleitung an ein beliebiges Agenten-Modell (Claude, Codex, agy/Gemini, Kimi), ein empirisches Theory-of-Mind-Modell SEINES Users aus den eigenen Interaktionslogs zu bauen, zu pflegen und an Memory/Regeldateien/System-Prompt anzubinden. Aktiviert sich bei "baue ein ToM/Entscheidungs-Avatar für meinen User", "Theory of Mind System Nutzer-Modell", "WHAT-WOULD-USER-SAY", "feedback precognition".
---

# build-your-users-mind — Agnostisches ToM-Modul (Feedback-Präkognition)

> **What you mind is what you get.** Ein **Rezept**, kein Framework. Jedes Agenten-Modell baut daraus ein
> ToM-Modell *seines* Users: eigene Daten auswerten → Entscheidungsmuster destillieren →
> Avatar-Dateien pflegen → an die eigene Memory/Regeldatei/System-Prompt anbinden.
>
> **Kern = Feedback-Präkognition (feedforward):** Sage das User-Feedback voraus, BEVOR es kommt; nutze es
> als Steuersignal in dessen Abwesenheit; evaluiere die Vorhersage hinterher gegen die Realität.
>
> **Vorlagen:** `templates/` (Avatar-Dateien), `scripts/` (Pipeline), `TAXONOMY.md` (8 Typen),
> `skills/swarm-operations/` (Klassifikations-Schwarm). Eine **private Referenz-Implementierung**
> (auf den Logs des Autors) existiert, wird aber nicht mitgeliefert.
>
> **Theoretische Basis:** *Prompt-Archaeology* (Methode, Taxonomie in `TAXONOMY.md`)
> + ToM-Forschung (ToM-SWE arXiv 2510.21903; Persistent Memory & User Profiles 2510.07925).

## Grundprinzip

LLMs sehen nie die Roh-Gigabytes. **Deterministische Skripte reduzieren zuerst** auf ein sauberes
Korpus der getippten User-Sätze; erst dann arbeitet ein **Klassifikations-Schwarm** semantisch.
Kern ist nicht „welche Prompts", sondern **„welche Entscheidung → welches Ergebnis → war der User zufrieden".**

## Die 6 Schritte

### 1. Quelle erschließen (Source-Adapter)
Finde die eigenen Interaktionslogs. Pro Modell unterschiedlich → siehe `SOURCE-ADAPTERS.md`.
Extrahiere **nur echte, vom Menschen getippte Prompts** (keine Tool-Results, System-Reminder,
Hook-Injektionen, Kontext-Kompaktierungs-Summaries). Felder: `ts, project, session, text`.

### 2. Reduzieren (deterministisch, kein LLM)
- Synthetische Turns filtern, Dedup, Boilerplate/Micro-Acks aggregieren.
- **Followup-Verknüpfung:** je Prompt den/die nächsten User-Turn(s) als `outcome_signal`
  (praise | reissue | correction | abandon | none) ableiten → das Zufriedenheits-Signal.
- **`decision_score`** über ein Entscheidungs-Lexikon (Korrektur/Präferenz/Regel/Steuerung).
- **REDACTION (Pflicht, bevor irgendetwas persistiert):** Secrets/Tokens/Keys/Mails — und je nach
  User auch **Gesundheit/Steuer/IP-Adressen**. Sensibles des Users wird maskiert.

### 3. Klassifizieren (Schwarm, hierarchisch + Stigmergy)
8-Typen-Taxonomie **SP/NT/NM/NS/KO/BE/RA/MP** (Definitionen in der PA-`GLOSSAR.md`) + `decision_kind`
(preference/correction/rule/direction_change/approval/rejection/process/none) + `formulation_pattern`
(charakteristische Wendung des Users). Bei großem Korpus: Domänen-Leads (Sonnet) dirigieren Chunk-Worker (Haiku).

### 4. Avatar-Dateien erzeugen
Struktur 1:1 wie in `templates/` (dort die Vorlagen kopieren, `<USER>`/`<AGENT>` ersetzen):
`WHAT-<USER>-SAID.md` (belegt) · `WHAT-WOULD-<USER>-SAY.md` (Vorhersage + Konfidenz) ·
`WHAT-I-DID-…md` + `MY-ACTIONS.txt` (Handlungs-Log) · `WHAT-<USER>-SAID-ABOUT-…md` (Lessons) ·
`PROMPT-LOG` (Cut-and-Clue) · `METHODIK.md` (inkl. Bias-Hinweis) · `START.md` (0→4-Loop).

### 5. Anbinden (entscheidend!)
Das ToM-Modell muss **tatsächlich genutzt** werden, nicht nur existieren:
- Kurze Regel/Pointer in die **eigene Memory/Regeldatei/System-Prompt** des Agenten
  (Claude: `CLAUDE.md`; Codex: `GPT.md`/`AGENTS.md`; agy: `GEMINI.md`; Kimi: `KIMI.md`)
  → zeigt auf den `START.md`-Loop. **Kurz halten** (Pointer, kein Volltext).
- **Vorrang-Regel:** projektbezogene `DECISIONS.md` gehen vor dem quer-liegenden Avatar.
- **Optionale Befehlseinstiegspunkte (Nuancen):** den Loop auf drei Tiefen plus einem Orchestrator
  bereitstellen — `read-my-mind` (Vorhersage, 0→2, keine Aktion), `decide-like-me` (eine Entscheidung,
  0→2, Workflow-Komponente), `be-my-avatar` (handeln, vollständig 0→4, nur reversibel, mit Log),
  `avatar-orchestrator` (Kette über viele Entscheidungen, bündelt 🔴/irreversible Punkte zu einer
  Rückfrage). Vorlagen in `templates/commands/`.
- **Versionierte Anbindung:** die projektlokale Kopie des Loops/Skills ist kanonisch; liefert der Agent
  zusätzlich eine registrierte Kopie, gewinnt die **höhere Version** — die ältere geroutete Kopie wird
  **ersetzt**. Das Projekt führt, die Registry folgt (kein Drift).

### 6. Pflegen (selbstverbessernd)
- **Empirische Basis:** Skripte periodisch neu laufen (Logs persistieren ohnehin) — **kein Per-Prompt-Hook**
  (Idempotenz-/Mehrfachregistrierungs-Falle vermeiden; Batch ist robuster).
- **Laufzeit (hingelotst):** im Namen des Users getroffene Annahmen → Datei (3) loggen;
  bei Feedback → Datei (4) → Regel in (1) nachziehen, Konfidenz in (2) anpassen.

## Bias & Grenzen (immer mitnennen)
- **Stille Zustimmung ist unsichtbar** → Korrekturen überrepräsentiert, Avatar skemmt „kritisch".
- **ToM-Fragilität:** robust bei wiederkehrenden, fragil bei neuartigen Situationen → Konfidenz-Stufen,
  bei 🔴 **eskalieren statt raten**.
- Beleg-IDs stammen aus LLM-Synthese → bei kritischer Nutzung gegen das Roh-Korpus gegenlesen.

## Schlankheits-Regel
Das einzig Modell-Spezifische ist der **Source-Adapter** (Schritt 1). Rezept, Taxonomie,
Avatar-Struktur und Anbindung sind universell. Nicht überbauen.
