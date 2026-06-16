# TODO — build-your-users-mind

**Status:** `development` (Claude-Pfad vollständig; Referenz-Implementierung privat vorhanden)
**Sprache:** README englisch; SKILL/Doku deutsch+englisch gemischt (bewusst)

## Vor Public-Release (Gate)
- [ ] `final_gate_check.py` aus `.MODULES` ausführen, Ergebnis in `RELEASE_GATE.md` dokumentieren
- [ ] Leak-/Pfad-Scan grün (keine absoluten Privatpfade, keine Secrets)
- [ ] Repo-Name + Org final wählen (`build-your-users-mind`), Topics setzen

## Inhaltlich offen
- [ ] Source-Adapter Codex (rollout) + Gemini (SQLite) ausimplementieren (derzeit Skizze in `SOURCE-ADAPTERS.md`)
- [ ] Kimi-Adapter (Log-Format beim ersten Einsatz bestimmen)
- [ ] Klassifikations-Spotcheck / Inter-Rater-Kappa als optionalen Qualitäts-Schritt ergänzen
- [ ] `domains.json`-Beispiel beilegen (Domänen-Leads konfigurieren)
- [ ] Optionaler `requirements.txt`-Eintrag, falls eine Direct-API-Variante gebaut wird

## Bewusst NICHT enthalten
- Kein privater Korpus, keine ausgefüllten Avatar-Dateien (siehe `.gitignore`)
- Kein Per-Prompt-Hook (Batch + Logbuch bewusst gewählt)
