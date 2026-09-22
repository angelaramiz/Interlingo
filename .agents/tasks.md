# TAREAS ACTIVAS

## MVP — Ciclo: meta → diagnóstico → lección → evaluación → ajuste

### Setup
- [x] Decidir stack: KMP/Compose (Android primero, iOS después) + FastAPI + SQLite + OpenRouter
- [ ] Inicializar repositorio git (si aplica)
- [x] Esqueleto backend: FastAPI + SQLite + motor de prompts + OpenRouter (modelo configurable por env)
- [x] Esquema SQLite (usuario, meta, niveles, evaluaciones, traza)
- [x] Proyecto KMP en `android/` (composeApp: commonMain + androidMain) — compila assembleDebug OK
  - Namespace/paquete: com.interlingo.app, minSdk 26, compileSdk/targetSdk 35
  - Ktor client + kotlinx.serialization apuntando a backend (10.0.2.2:8000 en emulador)

### Motor de IA
- [x] Motor de prompts (meta, diagnóstico, plan, lección, evaluación, corrección, ajuste)
- [x] Formato JSON de salida definido (schemas.py)
- [x] Cliente OpenRouter con modelo configurable (OPENROUTER_MODEL en .env)
- [x] **Modelo local Qwen3-4B** (llama-cpp-python, CPU): provider `local` en `app/ai/local.py`
  - Modelo: `D:\models\Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (2.33 GB)
  - Dispatcher `app/ai/inference.py` (AI_PROVIDER=local|openrouter)
  - Ciclo e2e completo verificado con el modelo local (contenido en inglés)

### Funcionalidad
- [x] Diagnóstico inicial (3-10 preguntas) — probado e2e con IA mock
- [x] Generación de plan de 5 niveles — probado e2e
- [x] Lección (texto breve + vocabulario clave) — probado e2e
- [x] Evaluación tipo opción múltiple (y respuesta escrita en niveles altos) — probado e2e
- [x] Lógica de ajuste de nivel (avanzar / repetir / simplificar / profundizar) — probado e2e
- [ ] Probar flujo completo con API key real (OpenRouter) — opcional, ya hay modelo local
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
- [ ] Crear servicio web en Render (pendiente del desarrollador — ver input.md)
- [ ] Probar OTA en dispositivo físico

### Verificación
- [x] Verificación TDD de la app móvil (2026-09-20): `backend/app/mobile_verify.py` + 55 tests, cobertura 100%, 103/103 checks OK

### UX/UI
- [x] Pantalla de inicio (campo de meta + botón comenzar) — App.kt
- [ ] Onboarding corto (2-3 preguntas si la meta es ambigua)
- [x] Flujo diagnóstico → plan → lección → evaluación → resultado (App.kt)
- [x] Feedback inmediato con explicación + scores de idioma/tema + decisión del motor
- [x] Barra de progreso por nivel
- [ ] Diccionario integrado (clic en palabra → traducción)
- [ ] Control de dificultad manual (fácil / adecuado / difícil)
- [ ] Mockups de las 4 secuencias (lectura, producción guiada, respuesta escrita, explicación propia)

## Opcional (post-MVP)
- [ ] Texto a voz
- [ ] Repetición espaciada
- [ ] Exportación de artefactos

## Completado
- [x] Documentar concepto y MVP en .agents
