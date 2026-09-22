# Historial

## 2026-08-12 — Definición de concepto y MVP
- Aprobado el concepto de doble ruta (idioma + tema) para LengLearning.
- Definidos requisitos técnicos, de diseño del sistema y UX/UI.
- Documentado el MVP: meta → diagnóstico → lección → evaluación → ajuste.
- Creada la estructura `.agents/` (memoria y contexto del agente).

## 2026-08-12 — Stack aprobado
- Kotlin Multiplatform + Compose Multiplatform (Android primero, iOS después).
- Backend compartido: FastAPI + SQLite + OpenRouter.

## 2026-08-12 — Backend MVP creado
- Esqueleto FastAPI + SQLite en `backend/`: modelos (usuario, meta, nivel, evaluación, traza), schemas Pydantic, motor de prompts, cliente OpenRouter (modelo configurable por env) y servicios del ciclo completo (meta → diagnóstico → plan → lección → evaluación → ajuste).
- Rutas API registradas y verificado que el servidor arranca.

## 2026-08-12 — App Android (KMP) esqueleto compilado
- Proyecto Kotlin Multiplatform + Compose Multiplatform en `android/` (módulo composeApp, Android-first).
- Paquete `com.lenglearning.app`, minSdk 26, compileSdk/targetSdk 35.
- Cliente Ktor + kotlinx.serialization hacia el backend; pantalla de meta → diagnóstico → plan.
- `assembleDebug` OK (APK 10.5 MB). Gradle wrapper 8.9, AGP 8.6, Kotlin 2.0.21, CMP 1.7.3.

## 2026-08-12 — Flujo completo app + backend probado
- Backend: el plan devuelve IDs de nivel; Nivel guarda `tipo_actividad`; resultado incluye `tipo_error`.
- App: flujo completo meta → diagnóstico → plan → lección → evaluación → resultado (feedback, scores idioma/tema, decisión, siguiente nivel) con barra de progreso.
- Ciclo e2e verificado con la IA mockeada (sin API key). Falta probar con API key real.

## 2026-08-12 — Modelo local Qwen3-4B integrado
- Instalado `llama-cpp-python` (CPU) y descargado `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (2.33 GB) a `D:\models`.
- Nuevo provider `app/ai/local.py` + dispatcher `app/ai/inference.py` (AI_PROVIDER=local|openrouter).
- Prompts reforzados: usan nombre completo del idioma y exigen contenido en el idioma objetivo (arreglado bug que generaba en portugués).
- Ciclo e2e completo verificado con el modelo local: meta → diagnóstico → plan(5) → lección → evaluación → resultado. Contenido generado en inglés.

## 2026-08-12 — Inferencia on-device en la app
- Compilado llama.cpp para Android (NDK 28, arm64-v8a): `libllama.so` + `libggml*.so` + puente JNI propio (`libllm_bridge.so`) en `jniLibs/arm64-v8a`.
- Kotlin: `LlmEngine` (JNI), `ModelDownloader` (descarga GGUF a filesDir con progreso), `PromptEngine` (prompts portados), `LocalEngine` (implementa `LearningApi` on-device). Backend se conserva (`ApiClient` disponible).
- `MainActivity`: descarga el modelo en primer arranque, lo carga y pasa `LocalEngine` a la UI.
- APK 78 MB, compila OK. Pendiente: probar en dispositivo físico arm64.

## 2026-09-20 — Verificación TDD de la app móvil (103/103 OK)
- Nuevo `backend/app/mobile_verify.py` + `backend/tests/test_mobile_verify.py`: ciclo RED→GREEN→REFACTOR estricto.
- 55 tests pytest, cobertura 100% sobre `mobile_verify.py` (umbral exigido 80%).
- Verificado: 9 fuentes Kotlin + Manifest + 6 `.so`; `LearningApi` (6 métodos) espeja las 7 rutas backend; `ApiClient` (baseUrl 10.0.2.2:8000 + 7 endpoints); 12 DTOs `@Serializable`; máquina de 8 estados y 8 pantallas en `App.kt` con progreso, decisión avanzar/profundizar y manejo de errores; on-device (`llm_bridge` JNI, descarga con `.part` + progreso, `LocalEngine`, 7 builders de `PromptEngine` + `extractJson`, INTERNET, arm64-v8a, URL HF del GGUF); paridad de prompts con `backend/app/ai/prompts.py`.
- Hallazgo menor (corregido en el verificador, no en la app): hay dos `build.gradle.kts` y el primero en orden de disco no trae `abiFilters`; el verificador ahora concatena todos.
