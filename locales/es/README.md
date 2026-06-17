> El inglés (README.md) es el documento autoritativo; esta traducción puede estar desactualizada.

# build-your-users-mind

> **What you mind is what you get.**

**🌐 [EN](../../README.md) · [DE](../de/README.md) · [ES](README.md) · [JA](../ja/README.md) · [RU](../ru/README.md) · [ZH](../zh/README.md)** — El inglés es autoritativo; las traducciones pueden estar desactualizadas.

Una receta para que cualquier agente de IA (Claude, Codex, Gemini/agy, Kimi, …) construya un **theory-of-mind model of its own user** (modelo de teoría de la mente de su propio usuario) empírico y auto-mejorable a partir de sus propios registros de interacción, y actúe según el espíritu del usuario cuando este no esté presente.

Funciona mediante **feedforward**: en lugar de esperar una retroalimentación que no llegará mientras el usuario esté ausente, el agente *predice la retroalimentación del usuario antes de que llegue* y utiliza esa predicción como una señal de guía o recompensa; luego evalúa la predicción frente a la realidad para mejorar.

## "Sé lo que quieres."

Esa frase es todo el propósito. El agente lee las instrucciones pasadas del usuario, destila **qué decide el usuario, cómo lo expresa y si quedó satisfecho**, y lo convierte en un pequeño conjunto de documentos vivos que puede consultar en el momento en que surge una decisión y el usuario no está localizable.

No es una personalidad de chatbot ni un marco de trabajo pesado: es un método + un puñado de scripts + plantillas de documentos. La única parte específica del agente es el *source adapter* (donde cada agente lee sus propios registros). Todo lo demás es universal.

## Cómo funciona — feedback precognition

Un bucle de ejecución de 0 a 4 (ver `templates/START.md`):

| Paso | Archivo | Rol |
|---|---|---|
| 0 | proyecto `DECISIONS.md` | las decisiones específicas del proyecto tienen prioridad (más específicas) |
| 1 | `WHAT-<USER>-SAID` | reglas/decisiones **basadas en evidencia** (con citas de IDs de prompts) |
| 2 | `WHAT-WOULD-<USER>-SAY` | **precognition** (precognición) — retroalimentación predicha + confianza (🟢/🟡/🔴) |
| 3 | `WHAT-I-DID…` + `MY-ACTIONS.txt` | registro de acciones tomadas con base en la predicción |
| 4 | `WHAT-<USER>-SAID-ABOUT…` | **evaluación** — predicción vs. realidad → mejora (1) y (2) |

Métrica de calidad = **con qué frecuencia la reacción anticipada coincide con la retroalimentación real posterior del usuario.**
En caso de 🔴 (nuevo/sin patrón), la regla es **escalar, no adivinar.**

### Pipeline (construir el modelo)

1. **Extraer** (`scripts/corpus_extract.py`) — determinista: extraer solo las instrucciones escritas por humanos de sus registros, filtrar los turnos sintéticos, **ocultar secretos**, vincular cada instrucción con la `outcome_signal` del siguiente turno (elogio/corrección/reemisión/ninguna).
2. **Chunk** (`scripts/chunk_corpus.py`) — eliminar duplicados, dominios opcionales, fragmentar por tamaño para el enjambre.
3. **Clasificar** (enjambre) — taxonomía de 8 tipos (`TAXONOMY.md`) + decision_kind + patrón de formulación. Enjambre jerárquico (líderes de dominio × trabajadores de fragmentos); ver el skill integrado `skills/swarm-operations/`.
4. **Agregar** (`scripts/aggregate_stats.py`) — distribución de tipos, relación B:K, puntos de inflexión.
5. **Crear** (Author) los archivos de avatar desde `templates/` and **vincular** (bind) un puntero corto en el archivo de memoria/reglas del propio agente (Claude `CLAUDE.md`, Codex `GPT.md`/`AGENTS.md`, Gemini `GEMINI.md`, …).

Ver `SKILL.md` para la receta completa y `SOURCE-ADAPTERS.md` para las ubicaciones de los registros de cada agente.

## Theory of us — trasfondo teórico

El sistema modela la **díada** (agente ↔ usuario), no solo al usuario de forma aislada: una *Theory of Us* (teoría de nosotros).
Se fundamenta en:
- Investigación de **Theory of Mind** (Teoría de la Mente) para agentes LLM: predecir y condicionar el estado mental de un interlocutor mejora los resultados (por ejemplo, *ToM-SWE*, arXiv 2510.21903; *Infusing Theory of Mind into Socially Intelligent LLM Agents*, 2509.22887; *Persistent Memory & User Profiles*, 2510.07925).
- **Prompt-Archaeology** (L. Geiger) — el método de clasificar protocolos completos de interacción humano-IA, cuya taxonomía de 8 tipos reutiliza este módulo (`TAXONOMY.md`).
- Un límite conocido: la ToM de los LLM es **robusta en casos recurrentes, pero frágil bajo variaciones novedosas o adversarias**; de ahí los niveles de confianza y la regla de "escalar, no adivinar".

## Sesgos y límites (leer antes de confiar)

- **La aprobación silenciosa es invisible**: los usuarios escriben correcciones, no elogios → el modelo sobrerrepresenta las correcciones y se inclina hacia lo "crítico". Calibre en consecuencia.
- **Los IDs de evidencia provienen de la síntesis del LLM**: verifique los más importantes contra el corpus bruto.
- **Sesgo del clasificador**: verifique aleatoriamente una muestra; informe el acuerdo inter-evaluador para un uso serio.

## Privacidad y redacción

El extractor redacta claves API, tokens, correos electrónicos, datos similares a IP y series largas de dígitos **antes de escribir**.
**Es responsabilidad del agente redactar el contenido de salud, impuestos u otro contenido sensible del usuario** antes de que el corpus o cualquier archivo de avatar salga de un espacio privado. Nunca confirme un corpus real: ver `.gitignore`.

## Suggested GitHub topics

`theory-of-mind` · `llm` · `user-modeling` · `personalization` · `ai-agents` · `prompt-analysis` · `feedback` · `decision-support`

## Créditos y Licencia

Método: *Prompt-Archaeology* por Lukas Geiger. Módulo y concepto: Lukas Geiger (+ Claude).
Dependencia incluida: skill `swarm-operations`. **MIT** — ver `LICENSE`.
Implementación de referencia (privada, no distribuida): una instancia personal construida sobre los propios registros del autor.
