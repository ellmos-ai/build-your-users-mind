# Übersetzungsauftrag — README von `build-your-users-mind`

**Für:** agy/Gemini (oder anderen Übersetzungs-Agenten)
**Repo-Root:** `C:\Users\User\OneDrive\.TOPICS\.AI\.MODULES\build-your-users-mind`
**Quelle (maßgeblich):** `README.md` (Englisch)
**Aufruf-Hinweis (agy):** mit `--dangerously-skip-permissions --add-dir "<Repo-Root>"` starten und die
Dateien **direkt schreiben lassen** — NICHT über stdout zurückgeben (sonst CJK-Verstümmelung U+FFFD).

## Aufgabe
Übersetze `README.md` in **5 Zielsprachen** und schreibe je eine Datei in den Repo-Root:

| Sprache | Datei |
|---|---|
| Deutsch | `README_de.md` |
| Español | `README_es.md` |
| 日本語 | `README_ja.md` |
| Русский | `README_ru.md` |
| 中文 (vereinfacht) | `README_zh.md` |

(Englisch `README.md` bleibt unverändert und maßgeblich.)

## Regeln
1. **Nur Prosa übersetzen.** Unverändert lassen: Markdown-Struktur, Überschriften-**Anker/Links**,
   Code-Blöcke, Tabellen-Gerüst, CLI-Flags, Dateinamen, Topics.
2. **Eigennamen NICHT übersetzen:** `build-your-users-mind`, `feedforward`, `feedback precognition`
   (Fachbegriff, in Klammern lokal erklären erlaubt), Datei-/Ordnernamen, die Avatar-Dateinamen
   (`WHAT-USER-SAID` etc.).
3. **Tagline „what you mind is what you get"** als Marken-Claim **im englischen Original** lassen
   (optional eine lokalisierte Erklärung in Klammern dahinter).
4. **Echte Diakritika / native Schrift** verwenden (ä ö ü ß, ñ, 漢字/かな, Кириллица). Kein ASCII-Ersatz.
5. **Disclaimer als erste Zeile** jeder Übersetzung:
   `> English (README.md) is authoritative; this translation may lag.` — sinngemäß in der Zielsprache.
6. **Sprachwähler-Zeile** (falls in `README.md` vorhanden) in jede Übersetzung übernehmen, Pfade unverändert.
7. Ton: technisch-präzise, knapp; keine Emojis hinzufügen.

## Ergebnis
5 Dateien `README_<lang>.md` im Repo-Root, valides Markdown, gleiche Abschnittsreihenfolge wie das Original.
Danach kurze Bestätigung, welche Dateien geschrieben wurden (+ Zeilenzahl je Datei).
