# WHAT WOULD <USER> SAY — Vorhersage-Playbook (Feedback-Präkognition)

> **Inferentiell** (Modell-Vorhersage aus Mustern). Das *antizipierte Feedback* von `<USER>`, das den
> Agenten in dessen Abwesenheit steuert. Wird in `WHAT-<USER>-SAID-ABOUT-…` gegen echtes Feedback evaluiert.

## Konfidenz-Legende
- 🟢 **hoch** — konsistentes Muster → handeln.
- 🟡 **mittel** — kontextabhängig → handeln + loggen + Feedback einholen.
- 🔴 **niedrig/neuartig** — kein Muster → **eskalieren statt raten**.

## Situations-Playbook
| Situation | Vorhersage: was <USER> will | Konfidenz |
|---|---|---|
| <Situation 1> | <vorhergesagtes Verhalten/Entscheidung> | 🟢/🟡/🔴 |

*(Aus den Domänen-Clustern füllen: je Cluster → Situation + typische Entscheidung + Konfidenz aus Cluster-Konsistenz.)*

## Default-Heuristik bei Unsicherheit
1. Reversibel + im Muster → handeln (loggen). 2. Irreversibel/extern → nicht ohne Bestätigung.
3. Konflikt mit Kern-Werten → vorsichtigere Variante. 4. Kein Muster (🔴) → eskalieren.
