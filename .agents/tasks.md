# TAREAS ACTIVAS

## MVP — Ciclo: meta → diagnóstico → lección → evaluación → ajuste

### Setup
- [x] Decidir stack: KMP/Compose (Android primero, iOS después) + FastAPI + SQLite + OrcaRouter
- [ ] Inicializar repositorio git (si aplica)
- [x] Esqueleto backend: FastAPI + SQLite + motor de prompts + OrcaRouter (modelo configurable por env)
- [x] Esquema SQLite (usuario, meta, niveles, evaluaciones, traza)
- [x] Proyecto KMP en `android/` (composeApp: commonMain + androidMain) — compila assembleDebug OK
  - Namespace/paquete: com.interlingo.app, minSdk 26, compileSdk/targetSdk 35
  - Ktor client + kotlinx.serialization apuntando a backend (10.0.2.2:8000 en emulador)

### Motor de IA
- [x] Motor de prompts (meta, diagnóstico, plan, lección, evaluación, corrección, ajuste)
- [x] Formato JSON de salida definido (schemas.py)
- [x] Cliente OrcaRouter con modelo configurable (ORCA_MODEL en .env)
- [x] **Modelo local Qwen3-4B** (llama-cpp-python, CPU): provider `local` en `app/ai/local.py`
  - Modelo: `D:\models\Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (2.33 GB)
  - Dispatcher `app/ai/inference.py` (AI_PROVIDER=local|orcarouter)
  - Ciclo e2e completo verificado con el modelo local (contenido en inglés)

### Funcionalidad
- [x] Diagnóstico inicial (3-10 preguntas) — probado e2e con IA mock
- [x] Generación de plan de 5 niveles — probado e2e
- [x] Lección (texto breve + vocabulario clave) — probado e2e
- [x] Evaluación tipo opción múltiple (y respuesta escrita en niveles altos) — probado e2e
- [x] Lógica de ajuste de nivel (avanzar / repetir / simplificar / profundizar) — probado e2e
- [x] Probar flujo completo con API key real (OrcaRouter + GLM 5.3 Flash gratis verificado en vivo)
- [x] Probar flujo completo con modelo local Qwen3-4B (e2e OK)

### On-device (app descarga y corre el modelo)
- [x] Compilar llama.cpp nativo NDK (arm64-v8a): libllama + libggml + libc++ en jniLibs
- [x] Puente JNI (`llm_bridge.so` + `LlmEngine.kt`)
- [x] Descarga de GGUF a filesDir con progreso (`ModelDownloader`)
- [x] Prompts en Kotlin (`PromptEngine`) + `LocalEngine` (implementa LearningApi)
- [x] APK 78 MB con las .so (arm64-v8a), compila OK
- [ ] Probar en dispositivo físico arm64 (emulador x86_64 no carga las .so)

### Versionado, releases y OTA
- [x] git init + remoto `angelaramiz/Interlingo` + push (rama `main`)
- [x] Keystore release generado (`android/keystore/`, gitignored; password en `.credentials` local)
- [x] Backend: tabla `app_versions` + `GET /api/app-version` (lee `version.json` primero) + `/static` + `render.yaml` (Render)
- [x] Android: versionado por props (`-PappVersionCode/-PappVersionName`), `BuildConfig.SERVER_URL`, `UpdateManager` (check/descarga/instalación), FileProvider, botón manual + diálogo
- [x] `release.ps1`: build → GitHub Release → version.json + push → verify con espera de redeploy (validado e2e v0.2.0)
- [x] APK v0.2.0 publicado en GitHub Releases (URL pública verificada, 78.8 MB)
- [x] Verificador TDD extendido con checks OTA (60/60, 100% cobertura)
- [x] Crear servicio web en Render (pendiente del desarrollador — ver input.md)
- [x] Fix deploy Render: `PYTHON_VERSION=3.12.6` (pydantic 2.9.2 no tiene wheel para Python 3.14)
- [x] Backup `backend/.python-version` (=3.12) por si el yaml se ignora
- [ ] Fijar `PYTHON_VERSION=3.12.6` en dashboard de Render (servicio manual ignora render.yaml) — pendiente del desarrollador
- [x] Hook de Render integrado en `release.ps1` (`-RenderHookUrl`, secreto solo por parámetro)
- [x] Fix BOM en `version.json` (leía default por `json.loads` + BOM; ahora `utf-8-sig` y escritura sin BOM)
- [x] OTA verificado en producción: `interlingo.onrender.com/api/app-version` → v0.2.0 + APK GitHub
- [x] Fix "Sin conexión" (TDD): v0.2.0 llevaba SERVER_URL de emulador; v0.2.1 con URL real + timeouts 60s + guardrail `-ServerUrl` obligatorio en release
- [x] Release v0.2.1 (code 3) publicado y verificado e2e
- [x] Wake-up de Render (`/api/health` + `wakeUp` con reintentos, "Despertando servidor…")
- [x] OrcaRouter robusto (TDD): reintentos con backoff, fallback por 404, timeout configurable, reuso de cliente, parseo JSON tolerante + base_url configurable
- [x] Release v0.2.2 (code 4) de prueba publicado y verificado e2e
- [x] Icono squircle personalizado para Interlingo (esquinas transparentes, doble burbuja A/文, estrella IA, mipmaps y adaptive icon)
- [x] Release v0.2.3 (code 5) publicado y verificado e2e con nuevo icono
- [ ] Probar OTA en dispositivo físico
- [ ] Validación MVP en dispositivo (1 semana, base para modo conversacional):
  - [ ] Ciclo completo real (meta → diagnóstico → plan → lección → evaluación)
  - [ ] Tiempos: descarga modelo, carga, cada generación
  - [ ] Calidad del inglés generado y nivel adecuado
  - [ ] Calidad pedagógica (preguntas, feedback, ajuste)
  - [ ] Batería/calentamiento/crashes

### Sesiones en backend (2026-09-23)
- [x] `GET /api/metas` + `MetaResumen` (tests/test_metas.py, 4 tests con SQLite en memoria)
- [x] MainActivity backend-first (health 5s → ApiClient, si no LocalEngine) + etiqueta de modo en Home
- [x] Home "Mis sesiones" con Continuar → Plan (o Diagnóstico si aún sin niveles)
- [x] ApiClient HttpTimeout 15s/120s/300s + `mensajeError` amable en App.kt (fin del "Generando contenido..." infinito)
- [x] QA en emulador: Home en línea + resume + error finito verificados con capturas
- [x] Modelo Qwen3-4B re-descargado a `D:/models` (2.33 GB); generación local e2e verificada (meta→diagnóstico→plan→lección)
- [x] Release v0.2.4 (code 6) publicado y verificado e2e (backend-first + sesiones + diccionario)
- [ ] Probar OTA en dispositivo físico (instalar v0.2.4 y verificar actualización)

### Verificación
- [x] Verificación TDD de la app móvil (2026-09-20): `backend/app/mobile_verify.py` + 55 tests, cobertura 100%, 103/103 checks OK
- [x] Sesiones backend (2026-09-23): 82/82 tests pytest (`test_metas.py` + `TestSesionBackend` + checks nuevos)
- [x] Diccionario integrado (2026-09-24): TDD estricto RED→GREEN→REFACTOR — 19 tests nuevos `test_diccionario.py` + 6 `TestDiccionarioContract`; servicio 100% cobertura; 107/107 tests pytest en total

### UX/UI
- [x] Pantalla de inicio (campo de meta + botón comenzar) — App.kt
- [ ] Onboarding corto (2-3 preguntas si la meta es ambigua)
- [x] Flujo diagnóstico → plan → lección → evaluación → resultado (App.kt)
- [x] Feedback inmediato con explicación + scores de idioma/tema + decisión del motor
- [x] Barra de progreso por nivel
- [x] Diccionario integrado (clic en palabra → traducción) — TDD 2026-09-24: `POST /api/diccionario` + `buscarDefinicion` en LearningApi/ApiClient/LocalEngine + `diccionarioUser` en PromptEngine/backend + LeccionScreen con palabras tocables y diálogo (ver history)
- [ ] Control de dificultad manual (fácil / adecuado / difícil)
- [ ] Mockups de las 4 secuencias (lectura, producción guiada, respuesta escrita, explicación propia)

## Opcional (post-MVP)
- [ ] Texto a voz
- [ ] Repetición espaciada
- [ ] Exportación de artefactos

## Completado
- [x] Documentar concepto y MVP en .agents
