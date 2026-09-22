# Input Pendiente

## Concepto aprobado (2026-08-12)
- Aprendizaje de idiomas mediante temas de interés (doble ruta: idioma + tema).
- MVP: meta → diagnóstico → lección → evaluación → ajuste, con plan de 5 niveles.
- Documentado en meetings/decisions/decision1.md y architecture.md.

## Decisiones que necesita el desarrollador
- [x] Stack definitivo: KMP/Compose (Android primero, iOS después) + FastAPI + SQLite + OpenRouter
- [x] Modelo de IA: **local Qwen3-4B** por defecto (AI_PROVIDER=local); OpenRouter opcional
- [ ] ¿Idiomas objetivo iniciales? (¿inglés primero?) — probado con inglés (en)
- [ ] ¿Niveles de idioma basados en CEFR (A1-C2)?
- [ ] ¿Niveles de tema por complejidad técnica propia?
- [ ] ¿Se inicializa repositorio git ahora?
- [ ] ¿Dónde se guardan las claves de API? (env / config)
- [x] ¿Versión mínima de Android / min SDK? → minSdk 26 (compileSdk/targetSdk 35)
- [x] ¿Paquete base de la app? → com.interlingo.app
