> Englisch (README.md) ist maßgeblich; diese Übersetzung kann veraltet sein.

# Sicherheitsrichtlinie

## Meldung von Schwachstellen
Bitte melden Sie Sicherheitslücken über die **GitHub Private Vulnerability Reporting**-Funktion dieses Repositories (Security → Report a vulnerability). Bitte öffnen Sie keine öffentlichen Issues für Sicherheitsprobleme.

## Daten- und Datenschutzmodell
Dieses Tool verarbeitet **Ihre eigenen KI-Interaktionsprotokolle**. Behandeln Sie den erzeugten Korpus und die Avatar-Dateien als **private personenbezogene Daten**:
- Der Korpus (`STUDIE/`), klassifizierte Chunks und ausgefüllte Avatar-Dateien sind standardmäßig über die **.gitignore** ausgeschlossen — committen Sie niemals einen echten Korpus.
- Der Extraktor schwärzt API-Schlüssel, Token, E-Mails, IP-ähnliche Adressen und lange Ziffernfolgen **vor dem Schreiben**.
- **Es liegt in der Verantwortung des Operators, gesundheitliche, steuerliche oder andere sensible Inhalte zu schwärzen**, bevor der Korpus oder eine Avatar-Datei eine private Umgebung verlässt.
- Die Skripte selbst senden keine Daten an externe Server; die Klassifizierung läuft über den Agenten/das LLM, auf das Sie sie verweisen — prüfen Sie die Datenbehandlung dieses Agenten separat.

## Geheimnisse (Secrets)
Jedes Geheimnis, das jemals committet wurde, muss **rotiert** (geändert) werden, nicht nur aus dem Working Tree entfernt werden.
