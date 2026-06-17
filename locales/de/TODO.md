# Pre-Release TODO: build-your-users-mind

**Audit Date:** 2026-06-17
**Auditor:** Claude (für Lukas Geiger)
**Target Repo:** `ellmos-ai/build-your-users-mind` (zuerst privat)
**Status:** `development` — Claude-Pfad vollständig; Referenz-Implementierung privat vorhanden.

---

## BLOCKER
> Müssen vor Public-Release gelöst sein.

- [x] **Secrets:** keine API-Keys/Tokens/Passwörter in getrackten Dateien
- [x] **Private Data:** keine PII/echten Pfade (Leak-Scan grün)
- [x] **Hardcoded Paths:** generische/relative Pfade in allen Skripten
- [x] **Database Files:** keine `.db` getrackt
- [x] **.env Files:** keine `.env` getrackt
- [x] **BACH Internals:** keine BACH-internen Dokumente
- [x] **.gitignore:** Mindesteinträge vorhanden
- [x] **LICENSE:** MIT vorhanden
- [x] **README.md:** englisch, vollständig

## HIGH PRIORITY
- [ ] Source-Adapter Codex (rollout) + Gemini (SQLite) ausimplementieren (derzeit Skizze)
- [ ] Klassifikations-Spotcheck / Inter-Rater-Kappa als optionaler Qualitäts-Schritt
- [ ] `domains.json`-Beispiel beilegen

## MEDIUM PRIORITY
- [x] `SECURITY.md` hinzugefügt
- [ ] `CHANGELOG.md` ab v1.0.0
- [ ] `CONTRIBUTING.md`
- [ ] Kimi-Adapter (Log-Format beim ersten Einsatz)

## LOW PRIORITY
- [ ] Test-/Smoke-Suite, GitHub Actions CI, Badges

## Bewusst NICHT enthalten
- Kein privater Korpus, keine ausgefüllten Avatar-Dateien (siehe `.gitignore`)
- Kein Per-Prompt-Hook (Batch + Logbuch bewusst gewählt)

---

## STATUS

| Category | Status | Notes |
|----------|--------|-------|
| Secrets | :green_circle: | Leak-Scan grün |
| Private Data (PII) | :green_circle: | keine PII/Pfade |
| .gitignore | :green_circle: | Mindesteinträge + Korpus/Avatar-Ausschluss |
| Language (English) | :green_circle: | README englisch |
| BACH Internals | :green_circle: | keine |
| Database Files | :green_circle: | keine getrackt |
| README.md | :green_circle: | vollständig |
| LICENSE | :green_circle: | MIT |
| **Overall** | **READY** | privat; Adapter Codex/Gemini noch Skizze |

**Audit Date:** 2026-06-17
**Gate Check Exit Code:** `pending`

---

*Basis: MODULES/_templates/TODO_TEMPLATE.md*
