# Política de seguridad

## Reporte de vulnerabilidades
Reporte las vulnerabilidades a través de **GitHub Private Vulnerability Reporting** en este repositorio (Security → Report a vulnerability). No abra issues públicos para problemas de seguridad.

## Modelo de datos y privacidad
Esta herramienta procesa **sus propios registros de interacción de IA**. Trate el corpus y los archivos de avatar producidos como **datos personales privados**:
- El corpus (`STUDIE/`), los fragmentos clasificados y los archivos de avatar completados están en el **.gitignore** por defecto — nunca confirme un corpus real.
- El extractor redacta claves API, tokens, correos electrónicos, datos similares a IP y series largas de dígitos **antes de escribir**.
- **Es responsabilidad del operador redactar el contenido de salud, impuestos u otro contenido sensible** antes de que el corpus o cualquier archivo de avatar salga de un entorno privado.
- Los scripts no envían ningún dato; la clasificación se ejecuta a través del agente/LLM al que lo dirija — revise el manejo de datos de ese agente por separado.

## Secretos
Cualquier secreto que se haya confirmado alguna vez debe ser **rotado**, no solo eliminado del árbol de trabajo.
