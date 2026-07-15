---
name: build-your-users-mind
description: Instrucciones para cualquier modelo de agente (Claude, Codex, agy/Gemini, Kimi) para construir, mantener y conectar un modelo empírico de teoría de la mente de SU usuario a partir de sus propios registros de interacción con archivos de memoria/reglas/system prompt. Se activa en "build a ToM/decision avatar for my user", "Theory of Mind system user model", "WHAT-WOULD-USER-SAY", "feedback precognition".
---

> **Translation status (2026-07-15): historical pre-1.1 draft. The root English documents are authoritative; do not use this translation as the current operational or security contract.**

# build-your-users-mind — Módulo agnóstico de ToM (Precognición de retroalimentación)

> **What you mind is what you get.** Una **receta**, no un marco de trabajo. Cada modelo de agente lo utiliza para construir un modelo de ToM de *su* usuario: evaluar datos propios → destilar patrones de decisión → mantener archivos de avatar → vincular a su propio archivo de memoria/reglas/system prompt.
>
> **Núcleo = feedback precognition (feedforward):** Prediga la retroalimentación del usuario ANTES de que llegue; utilícela como señal de control en su ausencia; evalúe la predicción frente a la realidad a posteriori para mejorar.
>
> **Plantillas:** `templates/` (archivos de avatar), `scripts/` (pipeline), `TAXONOMY.md` (8 tipos), `skills/swarm-operations/` (enjambre de clasificación). Existe una **implementación de referencia privada** (basada en los registros del autor) pero no se distribuye.
>
> **Base teórica:** *Prompt-Archaeology* (método, taxonomía en `TAXONOMY.md`) + investigación de ToM (ToM-SWE arXiv 2510.21903; Persistent Memory & User Profiles 2510.07925).

## Principio fundamental

Los LLM nunca ven gigabytes brutos. **Los scripts deterministas primero reducen** los datos a un corpus limpio de instrucciones de usuario escritas por humanos; solo entonces un **enjambre de clasificación** trabaja semánticamente.
El núcleo no es "qué instrucciones", sino **"qué decisión → qué resultado → si el usuario quedó satisfecho".**

## Los 6 pasos

### 1. Identificar la fuente (Adaptador de fuente)
Encuentre sus propios registros de interacción. Difiere según el modelo → ver `SOURCE-ADAPTERS.md`.
Extraiga **solo instrucciones genuinas escritas por humanos** (sin resultados de herramientas, recordatorios del sistema, inyecciones de hooks, resúmenes de compactación de contexto). Campos: `ts, project, session, text`.

### 2. Reducir (determinista, sin LLM)
- Filtrar turnos sintéticos, eliminar duplicados, agregar interacciones rutinarias/micro-reconocimientos.
- **Vínculo de seguimiento:** derivar los siguientes turnos del usuario por instrucción como una `outcome_signal` (praise | reissue | correction | abandon | none) → la señal de satisfacción.
- **`decision_score`** a través de un léxico de decisión (corrección/preferencia/regla/control).
- **REDACCIÓN (obligatoria antes de persistir):** redactar secretos/tokens/claves/correos electrónicos — y dependiendo del usuario, también **salud/impuestos/direcciones IP**. Los datos sensibles del usuario se enmascaran.

### 3. Clasificar (enjambre, jerárquico + estigmergia)
Taxonomía de 8 tipos **SP/NT/NM/NS/KO/BE/RA/MP** (definiciones en `TAXONOMY.md`) + `decision_kind` (preference/correction/rule/direction_change/approval/rejection/process/none) + `formulation_pattern` (fraseo característico del usuario). Para grandes corpus: los líderes de dominio (Sonnet) dirigen a los trabajadores de fragmentos (Haiku).

### 4. Generar archivos de avatar
Estructura 1:1 como en `templates/` (copiar plantillas, reemplazar `<USER>`/`<AGENT>`):
`WHAT-<USER>-SAID.md` (evidenciado) · `WHAT-WOULD-<USER>-SAY.md` (predicción + confianza) · `WHAT-I-DID-…md` + `MY-ACTIONS.txt` (registro de acciones) · `WHAT-<USER>-SAID-ABOUT-…md` (lecciones aprendidas) · `PROMPT-LOG` (recortes y pistas) · `METHODIK.md` (incl. advertencia de sesgo) · `START.md` (bucle 0→4).

### 5. Vincular (¡crucial!)
El modelo de ToM debe **usarse realmente**, no solo existir:
- Regla corta/puntero en el **propio archivo de memoria/reglas/system prompt** del agente (Claude: `CLAUDE.md`; Codex: `GPT.md`/`AGENTS.md`; agy: `GEMINI.md`; Kimi: `KIMI.md`) → apunta al bucle `START.md`. **Mantenerlo corto** (puntero, sin texto completo).
- **Regla de precedencia:** las decisiones específicas del proyecto en `DECISIONS.md` tienen prioridad sobre el avatar transversal.
- **Puntos de entrada de comandos opcionales (matices):** exponer el bucle en tres profundidades más un orquestador —
  `read-my-mind` (predecir, 0→2, sin acción), `decide-like-me` (una decisión, 0→2, componente de flujo de trabajo),
  `be-my-avatar` (actuar, completo 0→4, solo reversible, registros), `avatar-orchestrator` (encadenar sobre muchas decisiones,
  agrupando elementos 🔴/irreversibles en una sola pregunta). Plantillas en `templates/commands/`.
- **Vinculación versionada:** mantener la copia del proyecto del bucle/skill como canónica; si el agente también incluye una
  copia registrada, la **versión superior gana** y la copia enrutada más antigua es **reemplazada** — el proyecto
  lidera, el registro sigue (sin deriva).

### 6. Mantener (auto-mejorable)
- **Base empírica:** ejecutar los scripts periódicamente (los registros se persisten de todos modos) — **sin hook por instrucción** (evitar la trampa de idempotencia/registro múltiple; el procesamiento por lotes es más robusto).
- **Tiempo de ejecución (guiado):** registrar las suposiciones hechas en nombre del usuario → archivo (3); en caso de retroalimentación → archivo (4) → actualizar las reglas en (1), ajustar la confianza en (2).

## Sesgos y límites (mencionar siempre)
- **La aprobación silenciosa es invisible** → las correcciones se sobrerrepresentan, lo que hace que el avatar parezca "crítico".
- **Fragilidad de la ToM:** robusto en situaciones recurrentes, frágil ante variaciones nuevas/adversarias → niveles de confianza, en 🔴 **escalar en lugar de adivinar**.
- Los IDs de evidencia provienen de la síntesis del LLM → cotejar los clave con el corpus bruto para decisiones críticas.

## Principio de simplicidad
La única parte específica del modelo es el **adaptador de fuente** (Paso 1). La receta, la taxonomía, la estructura del avatar y el vínculo son universales. No sobrediseñar.
