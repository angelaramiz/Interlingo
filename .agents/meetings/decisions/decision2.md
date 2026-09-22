# Decisión 2 — Stack y estrategia de plataformas

**Fecha:** 2026-08-12

## Decisión
- **Frontend móvil**: Kotlin Multiplatform + Compose Multiplatform.
- **Fase 1 (ahora)**: solo target **Android** para validar el producto.
- **Fase 2 (post-validación)**: añadir target **iOS** al mismo módulo compartido.
- **Sin React**: una sola codebase Kotlin para las plataformas móviles.

## Backend (compartido para web/móvil)
- **FastAPI** + **SQLite** + **OpenRouter**.
- Contrato **JSON** bien definido desde el día 1 (lo consumirán Android e iOS).

## Motivo
- KMP permite empezar Android-only sin sacrificar iOS futuro (incremental, sin reescribir).
- Validar el ciclo meta → diagnóstico → lección → evaluación → ajuste primero en una plataforma.
