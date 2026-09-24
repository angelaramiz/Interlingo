# Input Pendiente

## Concepto aprobado (2026-08-12)
- Aprendizaje de idiomas mediante temas de interés (doble ruta: idioma + tema).
- MVP: meta → diagnóstico → lección → evaluación → ajuste, con plan de 5 niveles.
- Documentado en meetings/decisions/decision1.md y architecture.md.

## Decisiones que necesita el desarrollador
- [x] Stack definitivo: KMP/Compose (Android primero, iOS después) + FastAPI + SQLite + OrcaRouter
- [x] Modelo de IA: **local Qwen3-4B** por defecto (AI_PROVIDER=local); OrcaRouter (GLM 5.3 Flash gratis) en producción
- [ ] ¿Idiomas objetivo iniciales? (¿inglés primero?) — probado con inglés (en)

## Crear servicio en Render (pendiente del desarrollador)
- [ ] En render.com → New + → Web Service → conectar repo `angelaramiz/Interlingo`
- [ ] `render.yaml` ya define todo: Root Directory `backend`, Build `pip install -r requirements.txt`, Start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] Variables de entorno en el dashboard (OrcaRouter, modelo gratis): `AI_PROVIDER=orcarouter`, `ORCA_BASE_URL=https://api.orcarouter.ai/v1/chat/completions`, `ORCA_MODEL=z-ai/glm-5.3-flash-free`, `ORCA_API_KEY=<tu clave sk-orca-...>` — borra las viejas `OPENROUTER_*` para no confundir (el servicio manual ignora render.yaml: cambiarlas en el dashboard; guardarlas redispara el deploy)
- [ ] DB persistente (Supabase, proyecto `hxzxcauujojjddexqvkk`): en dashboard Render poner `DATABASE_URL=postgresql://postgres:<pass>@db.hxzxcauujojjddexqvkk.supabase.co:5432/postgres` (pass = la de Supabase → Settings → Database; NUNCA al repo ni al chat). El backend crea las tablas solo con `create_all`.
- [ ] URL resultante (ej: `https://interlingo-api.onrender.com`): pasarla como `-ServerUrl` en el próximo `release.ps1` para que la app apunte al servidor real
- [ ] ¿Niveles de idioma basados en CEFR (A1-C2)?
- [ ] ¿Niveles de tema por complejidad técnica propia?
- [ ] ¿Se inicializa repositorio git ahora?
- [ ] ¿Dónde se guardan las claves de API? (env / config)
- [x] ¿Versión mínima de Android / min SDK? → minSdk 26 (compileSdk/targetSdk 35)
- [x] ¿Paquete base de la app? → com.interlingo.app
