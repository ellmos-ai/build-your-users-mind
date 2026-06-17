# TODO previo al lanzamiento: build-your-users-mind

**Fecha de auditoría:** 2026-06-17
**Auditor:** Claude (para Lukas Geiger)
**Repositorio destino:** `ellmos-ai/build-your-users-mind` (inicialmente privado)
**Estado:** `development` — el camino de Claude está completo; la implementación de referencia privada existe.

---

## BLOQUEADORES
> Deben resolverse antes del lanzamiento público.

- [x] **Secretos:** Sin claves API/tokens/contraseñas en archivos rastreados.
- [x] **Datos privados:** Sin PII/rutas reales (el escaneo de fugas está en verde).
- [x] **Rutas codificadas:** Rutas genéricas/relativas en todos los scripts.
- [x] **Archivos de base de datos:** Sin archivos `.db` rastreados.
- [x] **Archivos .env:** Sin archivos `.env` rastreados.
- [x] **Internos de BACH:** Sin documentos internos de BACH.
- [x] **.gitignore:** Entradas mínimas presentes.
- [x] **LICENCIA:** Licencia MIT presente.
- [x] **README.md:** En inglés, completo.

## PRIORIDAD ALTA
- [ ] Implementar adaptadores de fuente para Codex (rollout) + Gemini (SQLite) (actualmente bocetos).
- [ ] Agregar verificación de muestreo de clasificación / Kappa inter-evaluador como paso de calidad opcional.
- [ ] Agregar ejemplo de `domains.json`.

## PRIORIDAD MEDIA
- [x] Añadido `SECURITY.md`.
- [ ] Crear `CHANGELOG.md` a partir de la v1.0.0.
- [ ] Crear `CONTRIBUTING.md`.
- [ ] Adaptador de Kimi (formato de registro durante el primer uso).

## PRIORIDAD BAJA
- [ ] Suite de prueba/smoke, GitHub Actions CI, badges.

## Excluido intencionalmente
- Sin corpus privado, sin archivos de avatar completados (forzado por `.gitignore`).
- Sin hook por instrucción (procesamiento por lotes + libro de registro elegido intencionalmente).

---

## ESTADO

| Categoría | Estado | Notas |
|----------|--------|-------|
| Secretos | :green_circle: | Escaneo de fugas verde |
| Datos privados (PII) | :green_circle: | Sin PII/rutas |
| .gitignore | :green_circle: | Entradas mínimas + exclusión de corpus/avatar |
| Idioma (Inglés) | :green_circle: | README en inglés |
| Internos de BACH | :green_circle: | Ninguno |
| Archivos de base de datos | :green_circle: | Ninguno rastreado |
| README.md | :green_circle: | Completo |
| LICENCIA | :green_circle: | MIT |
| **General** | **LISTO** | Privado; adaptadores de Codex/Gemini aún en boceto |

**Fecha de auditoría:** 2026-06-17
**Código de salida del Gate Check:** `pending`

---

*Base: MODULES/_templates/TODO_TEMPLATE.md*
