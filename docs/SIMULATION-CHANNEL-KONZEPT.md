# SIMULATION-CHANNEL — Erweiterungskonzept: ein Modell, das wie der Nutzer schreibt, promptet und entscheidet

> **Status:** Konzept (keine Implementierung). Aufgenommen auf Nutzeridee 2026-07-31
> („ein Modell, das wirklich versucht, wie ich zu schreiben, zu prompten, zu entscheiden —
> es soll alles, was ich gesagt habe, einmal lesen und mich simulieren").
> **Vorbehalt:** Rohe Prompt-/Chat-Inhalte bleiben lokale private Datenräume
> (privacy_class sensitive); dieses Konzept ändert daran nichts.

## 1. Idee

Ein neuer Kanal im System: ein Modell, das aus **allen** Äußerungen des Nutzers
(Prompts, Entscheidungen, Chatnachrichten) lernt, ihn zu **simulieren** — wie er
formuliert, wie er Aufgaben präzisiert, wie er entscheidet. Ziel ist kein
Chatbot über den Nutzer, sondern eine **arbeitende Stellvertretung** für
Formulierung und Entscheidungsstil.

## 2. Zwei Betriebsmodi (verbindlich)

### Role Mode — „es hält sich für mich"

- Das Modell schreibt **als** Lukas: eigene Wortwahl, eigene Präzisierungsmuster,
  eigene Priorisierungen (aus der 8-Typen-Taxonomie und den Beleg-Ketten abgeleitet).
- Es gibt Anweisungen/Prompts an Agenten **in seiner Rolle** zurück — mit
  derselben Kürze und Direktheit, die aus dem Korpus gelernt ist.

### Secure Mode — mit Distanz und Belegen

- Dasselbe Modell, aber jede Aussage/Entscheidung trägt ihre **Evidenz**:
  Quellen-Belege (Prompt-IDs, Entscheidungs-Einträge, Datumsanker) und eine
  **Konfidenz** je Behauptung („Lukas scheint …", „belegt aus N Entscheidungen").
- Unsichere oder neuartige Situationen werden nicht simuliert, sondern als
  offene Frage zurückgegeben (Eskalationspfad bleibt der echte Nutzer).

**Default ist Secure Mode.** Role Mode ist der delegierte, ausdrücklich
freizugebende Modus (siehe Kap. 5).

## 3. Harte Abgrenzung: es spricht, es führt nicht aus

- Der Kanal **spricht nur**: er liefert Text — Anweisungen, Prompt-Entwürfe,
  Entscheidungsvorschläge, Korrekturen — und **führt selbst nichts aus**.
- Die **Agenten behalten ihre Autonomie**: Sie prüfen den Output des Kanals wie
  jeden anderen Auftrag (Locks, Gates, eigene Verifikation). Eine Aussage des
  Kanals ist niemals automatisch Befehl.
- Typisierte Autorität (bestehende Regel D-20260730-001 bleibt): eine
  `predicted/delegated-avatar-decision` ist von einer `explicit-user-decision`
  unterscheidbar und darf nicht als wörtliche Nutzeräußerung dargestellt werden.
  Explizite Nutzerentscheidungen haben immer Vorrang.

## 4. Konfiguration (einstellbar)

| Feld | Bedeutung | Default |
|---|---|---|
| `mode` | `secure` \| `role` | `secure` |
| `scope` | Wie weit der Kanal reicht: `observe` (nur lesen/beraten), `propose` (Entwürfe liefern), `delegate` (im delegierten Rahmen entscheiden) | `observe` |
| `evidence_required` | Belegpflicht je Aussage (Secure Mode) | `true` |
| `corpus_window` | Zeitfenster des Korpus (z. B. alles / 90 Tage / 30 Tage) | `all` |
| `compressed` | Komprimierte Variante aktivieren (Kap. 5) | `true` |

## 5. Komprimierte Variante: lokales LLM als Interpretations-Schicht

- Ein **lokales LLM** (z. B. Ollama-Modell auf dem Host oder Mac Studio) fasst
  den Korpus chunkweise zusammen und **interpretiert** Absichten und Präferenzen:
  nicht Rohtext speichern, sondern verdichtete Aussagen wie
  „Lukas scheint es wichtig, dass Agenten ihm nur das zur Entscheidung geben,
  was wirklich sein Votum braucht."
- Ergebnis ist ein **Präferenz-/Absichts-Profil** (kleine, lesbare Datei mit
  Belegen), das der Kanal als Arbeitsgrundlage nutzt — statt bei jeder Anfrage
  den Vollkorpus zu laden.
- Aktualisierung: periodisch (nicht pro Prompt), mit Datumsanker je Aussage.

## 6. Bezug zu bestehenden Teilen

- **TOM_lm** (`_control-center/_TOM-lm`): der Entscheidungs-Avatar entscheidet
  schon heute delegiert im Rahmen; der Simulations-Kanal ergänzt die
  **generative** Seite (Schreiben/Prompten wie der Nutzer) — TOM_lm bleibt die
  Autoritäts-Typisierung, der Kanal ist ihr Sprachrohr.
- **8-Typen-Taxonomie (BYUM):** liefert die Klassifikation (SP/NT/NM/NS/KO/BE/RA/MP)
  und `formulation_pattern` — das Stil-Training des Kanals.
- **Gardener:** Suchschicht über dem Korpus (Chunk-Bereitstellung für die
  komprimierte Variante).
- **Privacy:** Rohtexte bleiben lokal; nur das Präferenz-Profil (mit Belegen,
  ohne Volltext-Zitate wo nicht nötig) verlässt die private Zone — und auch das
  nur innerhalb der eigenen Hosts.

## 7. Offene Fragen (vor Umsetzung klären)

1. Corpus-Grenze: welche Quellen zählen (Prompts aller Agenten? Chat-Exports?
   Entscheidungsdateien?) und mit welcher Redaktion?
2. Wer darf den Role Mode aktivieren (nur der Nutzer selbst, pro Scope)?
3. Wie wird eine Simulation als solche für Dritte kenntlich gemacht
   (Signatur/Header in jedem Output)?
4. Metrik: woran misst man „klingt wie Lukas" — Review durch den Nutzer in
   Intervallen, Feedback-Loop wie bei TOM_lm?

## 8. Nonclaims

- Kein Ersatz für den Nutzer, keine Personen-Imitation für Externe.
- Keine automatische Ausführung, keine Autorität über Agenten-Gates hinweg.
- Kein Export roher Prompt-/Chat-Inhalte in irgendeine Cloud.
