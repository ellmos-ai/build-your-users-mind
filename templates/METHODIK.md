# METHODIK — wie dieser Avatar entstand & wie er zu lesen ist

## Datenbasis
- Quelle(n): <Agent-Logs, z.B. ~/.claude/projects> · Zeitfenster: <seit …> · N eindeutige Prompts: <…>

## Pipeline
0/1 deterministisch (`scripts/corpus_extract.py`) → Chunking (`chunk_corpus.py`) → Stufe-2-Schwarm
(Klassifikation, 8-Typen `TAXONOMY.md`) → Stufe 3/4 (`aggregate_stats.py`) → Avatar-Dateien.

## Kennzahlen
- Typ-Verteilung · B:K · Proaktiv:Reaktiv · Wendepunkte · decision_kind — siehe `STUDIE/04_statistik.md`.

## Bias & Grenzen (immer mitnennen)
- **Stille Zustimmung unsichtbar** → Korrekturen überrepräsentiert, Avatar skemmt „kritisch".
- **Präkognitions-Fragilität:** robust bei wiederkehrenden, fragil bei neuartigen Situationen → Konfidenz-Stufen, 🔴 = eskalieren.
- **LLM-Klassifikator-Bias:** ohne Spotcheck/Kappa grobkörniger; Beleg-IDs aus Synthese → gegenlesen.
- **Redaction:** Secrets/Mails/IP maskiert; nutzerspezifisch Gesundheit/Steuer **vor jedem Teilen** schließen.

## Aktualisieren
Skripte periodisch neu laufen (Logs persistieren ohnehin) — **kein Per-Prompt-Hook**. Laufzeit-Lessons
(Datei 4) in `WHAT-<USER>-SAID.md` einarbeiten.
