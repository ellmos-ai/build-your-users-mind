# TAXONOMY — 8 tipos de prompt + campos de clasificación

> Versión independiente (el módulo es autónomo). **Base metodológica:** *Prompt-Archaeology* (L. Geiger) — el método de clasificar un protocolo completo de interacción humano-IA.

## Los 8 tipos de prompt

| Tipo | Código | Definición | Indicador |
|---|---|---|---|
| Prompt de inicio | **SP** | Inicia un nuevo análisis o fase | Sin referencia al contexto previo |
| Tema de seguimiento | **NT** | Profundiza en un tema existente | "¿Y qué hay de...?" |
| Método de seguimiento | **NM** | Dispara método/herramienta/revisión/búsqueda/agente | Verbo de acción |
| Control de seguimiento | **NS** | Gestiona secuencia o prioridad | "Espera", "primero", "alto" |
| Corrección | **KO** | Corrige un error o suposición | Negación, contraejemplo |
| Confirmación | **BE** | Valida el estado intermedio | Aceptación/confirmación corta |
| Cambio de rumbo | **RA** | Cambio fundamental de dirección | Cuestiona todo el marco de trabajo |
| Meta-prompt | **MP** | Sobre el proceso o el diálogo en sí | Terminología del proceso |

**Casos límite:** SP vs. NT (nuevo vs. conectado) · NM vs. NS (disparar método vs. solo reordenar) · BE vs. KO ("sí, pero..." suele ser KO) · RA es más raro que KO, afecta a todo el marco.

## Campos de clasificación (por prompt)

| Campo | Valores |
|---|---|
| `type_code` | SP/NT/NM/NS/KO/BE/RA/MP |
| `topic` | Tema corto (relacionado con el proyecto) |
| `is_decision` | true si es decisión, preferencia, regla, corrección o cambio de rumbo |
| `decision_kind` | preference / correction / rule / direction_change / approval / rejection / process / none |
| `formulation_pattern` | Fraseo característico del usuario (fraseo original, corto) |
| `method_triggered` | WebSearch / WebFetch / Multi-Agent / Review / Cross-Model / Script / LaTeX / -- |
| `is_turning_point` | true/false |
| `outcome_signal` *(determinista, Etapa 0/1)* | praise / correction / reissue / none (derivado del siguiente turno del usuario) |

## Indicadores de sesgo (Etapa 4)
- **Confirmación:Corrección (B:K)** — La disparidad sugiere sesgo de aprobación; **la aprobación silenciosa es invisible** (no se escribe) → las correcciones se sobrerrepresentan.
- **Tasa de corrección por tema** — Temas propensos a errores.
- **Proactivo:Reactivo** — ¿Lidera el usuario o está impulsado por la IA?
- **Tasa de cambio de rumbo** — Flexibilidad epistémica.
