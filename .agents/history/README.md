# Historial

## 2026-08-12 — Definición de concepto y MVP
- Aprobado el concepto de doble ruta (idioma + tema) para Interlingo.
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
- Paquete `com.interlingo.app`, minSdk 26, compileSdk/targetSdk 35.
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

## 2026-08-12 — Repo + OTA + releases
- `git init` + commit inicial (solo local, sin remoto por decisión del desarrollador).
- Keystore release generado en `android/keystore/` (gitignored).
- Backend: tabla `app_versions`, `GET /api/app-version`, estáticos en `/static`, `render.yaml` para Render.
- Android: `UpdateManager` (check/descarga/instalación vía FileProvider), diálogo de update + botón manual, versionado y `SERVER_URL` por props de Gradle.
- `release.ps1` validado e2e: APK release firmado v0.2.0 (code 2), copiado a `backend/static`, DB actualizada, endpoint y descarga verificados en local.
- Verificador TDD extendido a OTA: 60/60, 100% cobertura.

## 2026-09-20 — Verificación TDD de la app móvil (103/103 OK)
- Nuevo `backend/app/mobile_verify.py` + `backend/tests/test_mobile_verify.py`: ciclo RED→GREEN→REFACTOR estricto.
- 55 tests pytest, cobertura 100% sobre `mobile_verify.py` (umbral exigido 80%).
- Verificado: 9 fuentes Kotlin + Manifest + 6 `.so`; `LearningApi` (6 métodos) espeja las 7 rutas backend; `ApiClient` (baseUrl 10.0.2.2:8000 + 7 endpoints); 12 DTOs `@Serializable`; máquina de 8 estados y 8 pantallas en `App.kt` con progreso, decisión avanzar/profundizar y manejo de errores; on-device (`llm_bridge` JNI, descarga con `.part` + progreso, `LocalEngine`, 7 builders de `PromptEngine` + `extractJson`, INTERNET, arm64-v8a, URL HF del GGUF); paridad de prompts con `backend/app/ai/prompts.py`.
- Hallazgo menor (corregido en el verificador, no en la app): hay dos `build.gradle.kts` y el primero en orden de disco no trae `abiFilters`; el verificador ahora concatena todos.

## 2026-09-22 — Icono personalizado squircle y Release OTA v0.2.3
- Diseñado icono de alta fidelidad exclusivo para Interlingo: formato squircle con esquinas 100% transparentes, doble burbuja de diálogo (frontal azul con "A", superior violeta con "文"), trazos orbitales de intercambio bidireccional y estrella dorada de 4 puntas simbolizando el motor IA adaptativo.
- Generados recursos vectoriales y rasterizados: master SVG, `ic_launcher.png`, `ic_launcher_round.png` e `ic_launcher_foreground.png` en 5 densidades (mdpi a xxxhdpi), y definiciones adaptive icon en `mipmap-anydpi-v26`.
- Actualizado `AndroidManifest.xml` con `android:icon` y `android:roundIcon`.
- Verificación TDD aprobada (70/70 tests OK en pytest).
- Ejecutado pipeline `release.ps1`: build release firmado (75.3 MB), publicación de release v0.2.3 en GitHub Releases, actualización de `version.json` (versionCode 5), commit, push y verificación en vivo contra `https://interlingo.onrender.com/api/app-version`.

## 2026-09-23 � Sesiones en backend + fin del hang (TDD + emulador)
- Causa del 'Generando contenido...' infinito: MainActivity usaba siempre LocalEngine (estado solo en memoria; al morir el proceso volvia a Home sin nada) y sin timeouts. ApiClient tampoco tenia timeout.
- Fix backend-first: MainActivity prueba GET /api/health (5s); si hay servidor usa ApiClient (sesiones en SQLite), si no LocalEngine. Etiqueta 'En linea' / 'Sin conexion' en Home.
- Nuevo GET /api/metas (MetaResumen: id/texto/tema/idioma/estado, ?limit, recientes primero) + LearningApi.listarMetas/obtenerNiveles + Home 'Mis sesiones' con Continuar (a Plan, o a Diagnostico si aun sin niveles).
- ApiClient con HttpTimeout (connect 15s / socket 120s / request 300s): Loading siempre resuelve. App.kt mapea errores a mensaje amable (mensajeError).
- TDD: tests/test_metas.py (TestClient + SQLite memoria + chat_json mock, 4 tests) + TestSesionBackend (8 tests) + checks nuevos en mobile_verify.py. RED 20 fallos -> GREEN 82/82.
- QA en emulador (Medium_Phone_API_35, adb directo segun skill emulador-android adaptada): backend en puerto 8001 (el 8000 lo ocupa otro proyecto), APK debug con -PserverUrl=http://10.0.2.2:8001, sesion QA sembrada y luego borrada. Evidencia: Home 'En linea' + 'Mis sesiones' (ETL/plan) -> Continuar -> Plan con 2 niveles; 'Empezar nivel' sin IA -> error amable finito (no hang).
- Pendiente: E2E de generacion real con IA (falta OPENROUTER_API_KEY en backend/.env o re-descargar GGUF a D:/models); probar OTA en dispositivo fisico.

## 2026-09-24 — Diccionario integrado, TDD estricto (RED→GREEN→REFACTOR)
- Alcance: tap en cualquier palabra del texto de la lección → traducción sin salir (cierra el hueco UX "diccionario integrado" del MVP).
- Backend: `POST /api/diccionario` {palabra, idioma_objetivo, idioma_nativo, contexto} → {termino, traduccion, definicion, ejemplo}. `app/services/dictionary.py` (valida/normaliza: vacía→400, >100 chars→400, fallo IA→502; usa el dispatcher `chat_json`, nunca openrouter/local directo) + `diccionario()` en `app/ai/prompts.py` (nombres completos de idioma, esquema JSON) + `DiccionarioRequest/Response` en schemas + ruta en `main.py`.
- Móvil: `buscarDefinicion` en `LearningApi`/`ApiClient` (POST /api/diccionario)/`LocalEngine` (vía LLM on-device) + `DiccionarioRequest/Response` en Dtos + `diccionarioUser` en `PromptEngine` (paridad con backend) + `LeccionScreen` con palabras tocables (FlowRow) y `AlertDialog` (traducción/definición/ejemplo, "Buscando…" y error amable). `UiState.Plan/Leccion/Evaluacion/Resultado` llevan `idiomaObjetivo` (default "en") para traducir en la dirección correcta.
- TDD: RED 19 fallos (sin implementación) → GREEN 19/19 `tests/test_diccionario.py` (happy path, normalización, vacío/nulo/largo/unicode, defaults, dispatcher, ruta 200/400/422/502) + RED→GREEN de 8 checks nuevos en `mobile_verify.py` + 6 tests `TestDiccionarioContract` (asserts sobre flags `passed`, no sobre detalles con keyword).
- Cobertura: `dictionary.py` 100%, `schemas.py` 100%, `diccionario()` ambas ramas (con/sin contexto); el resto de misses en prompts.py/main.py son builders/rutas preexistentes.
- Gate: 107/107 pytest (19 diccionario + 4 metas + 6 openrouter + 78 mobile_verify). Nota: `test_mobile_verify.py` completo tarda ~130 s (rglob sobre el repo por check); los errores `WinError 5/32` vistos al correrlo son del entorno (limpieza de tmp de pytest / fichero de salida dentro del basetemp), no del código — con `--basetemp` fuera del árbol sale 78 passed, exit 0.
- Pendiente: compilar APK debug para validar el Kotlin nuevo (`assembleDebug` no se corrió en esta sesión); QA en emulador del diálogo de diccionario; probar OTA en dispositivo físico.

## 2026-09-24 � QA release v0.2.3 en emulador
- 'Package conflicts' al actualizar sobre debug: esperado (firma debug vs release). Resuelto con uninstall + install del release: instala y corre.
- El release v0.2.3 (code 5, construido el 22) NO trae backend-first (cambio del 23-24, sin commitear): en emulador descarga el GGUF directo. Descarga detenida con force-stop.
- Produccion verificada arriba: /api/health ok, /api/app-version -> v0.2.3 code 5.
- Siguiente paso: release v0.2.4 (code 6) via release.ps1 para llevar backend-first + sesiones + diccionario al telefono.

## 2026-09-24 � Release v0.2.4 (code 6)
- Pipeline release.ps1 e2e: build release firmado (75.3 MB) -> GitHub Release v0.2.4 -> version.json + push -> hook Render -> /api/app-version sirve code 6 (intento 3).
- Incluye: backend-first + Mis sesiones + HttpTimeout/mensajeError + diccionario (tap-a-palabra).
- QA emulador previa: conflicto de firma debug/release explicado; release v0.2.3 instala limpio tras uninstall.

## 2026-09-24 � 500 al crear sesion en produccion
- Sintoma (telefono): El servidor no pudo generar el contenido. Reproducido: POST /api/meta prod -> 500 en ~1s (sin reintentos => 401 de OpenRouter: OPENROUTER_API_KEY ausente/invalida en dashboard Render, pendiente del desarrollador).
- Hallazgo: la meta se commiteaba ANTES de interpretar_meta -> zombies con tema vacio en Mis sesiones (visto en prod). Fix TDD: rollback de meta+usuario si la IA falla (test_meta_fallida_no_deja_zombie). Gate 108/108.
- Quedan 2 filas zombie en prod (intento real del usuario + 1 repro mio): sin endpoint de borrado, se dejan; rollback evita futuras.

## 2026-09-24 � Cambio a OrcaRouter (modelo gratis)
- El 500 de prod NO era la key (valida): Orca responde 429 free_rate_limited � los modelos gratis exigen vincular una cuenta GitHub establecida o agregar credito (pendiente del desarrollador en consola OrcaRouter).
- Codigo: OPENROUTER_BASE_URL configurable (param base_url + settings, test TDD TestBaseUrl), defaults a api.orcarouter.ai + z-ai/glm-5.3-flash-free. Nombres de vars OPENROUTER_* conservados para no tocar de mas el dashboard. Gate 110/110.
- Diagnostico en vivo con key del usuario via script temporal (borrado tras uso); clave NUNCA en repo.

## 2026-09-24 � Renombre a OrcaRouter
- orcarouter.py / OrcaRouterClient / settings ORCA_* / AI_PROVIDER=orcarouter / test_orcarouter_client.py. Historial y decisions fechados no se reescriben. Gate 110/110.

## 2026-09-24 � Produccion verificada e2e con OrcaRouter
- Tras dashboard ORCA_* + redeploy: POST /api/meta -> tema ETL, GET diagnostico -> 5 preguntas, POST resultado -> plan 5 niveles, POST leccion/1 -> titulo + 6 vocabulario. Todo generado por z-ai/glm-5.3-flash-free.
- Nota: disco efimero en Render free resetea interlingo.db en cada deploy (ids desde 1).
