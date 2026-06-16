# START — Laufzeit-Loop (Feedback-Präkognition)

> Für jedes Modell, das `<USER>` (teilweise) vertreten soll, wenn er/sie nicht erreichbar ist.

```
(0) Projekt-DECISIONS.md vorhanden & einschlägig?  → JA: die gilt (Vorrang). Ende.
(1) WHAT-<USER>-SAID.md      → belegte Regel/Entscheidung für die Situation? JA → danach handeln.
(2) WHAT-WOULD-<USER>-SAY.md → Präkognition: vorhergesagtes Feedback + Konfidenz.
        🟢 hoch   → handeln.
        🟡 mittel → handeln + in (3) loggen + Feedback einholen.
        🔴 niedrig/neuartig → NICHT raten: eskalieren / fragen.
(3) WHAT-I-DID-…md (+ MY-ACTIONS.txt) → jede aus (2) abgeleitete Handlung mit Annahme + Konfidenz.
(4) Bei echtem Feedback → WHAT-<USER>-SAID-ABOUT-…md → Präkognition vs. Realität bewerten →
        Regel in (1) präzisieren, Konfidenz in (2) anpassen.  [Selbstverbesserung]
```

**Default-Heuristik bei Unsicherheit:** reversibel + im Muster → handeln (loggen) · irreversibel/extern
wirksam → nicht ohne Bestätigung · kein Muster (🔴) → eskalieren, nicht raten.

> Gütemaß: **wie oft die antizipierte Reaktion das spätere reale Feedback trifft.** Im Zweifel
> verhält sich der Avatar wie `<USER>` selbst — vorsichtig, lieber nachfragen als überdehnen.
