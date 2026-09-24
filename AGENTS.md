# AGENTS.md — Interlingo

Language-learning-by-topic app. Two halves: `backend/` (FastAPI + SQLite, AI content engine) and `android/` (Kotlin Multiplatform + Compose, Android-first, on-device inference via bundled llama.cpp). They share one contract: `LearningApi` in `android/.../commonMain/.../data/LearningApi.kt` mirrors the 7 learning routes (`/api/meta`, `/api/diagnostico…`, `/api/meta/{id}/niveles`, `/api/leccion…`, `/api/evaluacion…`) plus session resume (`GET /api/metas` → `listarMetas`, existing niveles route → `obtenerNiveles`); `/api/health` and `/api/app-version` are extra.

## Layout

- `backend/app/` — `main.py` (routes, also runs `Base.metadata.create_all` on import), `config.py`, `database.py`, `models.py`, `schemas.py`, `ai/` (prompts, OrcaRouter client, local llama.cpp provider, dispatcher), `services/` (diagnostic, planner, lesson, evaluate, adjust)
- `android/composeApp/src/commonMain/` — UI (`App.kt` takes `api: LearningApi`), DTOs, `ApiClient`
- `android/composeApp/src/androidMain/` — `MainActivity` (downloads model, loads engine, passes `LocalEngine` to `App`), `llm/` (`LlmEngine` JNI wrapper, `ModelDownloader`, `PromptEngine`, `LocalEngine`)
- `android/composeApp/src/main/jniLibs/arm64-v8a/` — prebuilt native `.so` (checked in intent: Gradle does NOT compile native code)
- `.agents/` — project memory, keep it updated (see below)

## Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt   # venv lives at backend/.venv
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload     # NOT uvicorn.exe (dies instantly on this box)
.\.venv\Scripts\python.exe -m pytest tests/ -q                  # TDD gate: both suites must stay green
```

- Config is `backend/.env` (machine-local, gitignored): `AI_PROVIDER=local|orcarouter`, `LOCAL_MODEL_PATH`, `ORCA_MODEL`, `DATABASE_URL`. Backend reads `.env` from its own cwd — run every command from `backend/`. `main.py` also mounts `StaticFiles(directory="static")` with a RELATIVE path, so launching from anywhere else breaks `/static` + `version.json`.
- Services call `chat_json` from `app.ai.inference` (the `AI_PROVIDER` dispatcher). Never call `orcarouter`/`local` directly from services.
- `OrcaRouterClient` (`app/ai/orcarouter.py`, OpenAI-compatible endpoint) retries (backoff) on 429/5xx/timeouts, falls through `orca_fallback_models` (comma-separated env) on 404, reuses one `httpx.Client`, and parses JSON tolerantly. New tunables: `ORCA_TIMEOUT`, `ORCA_MAX_RETRIES`. Unit tests: `backend/tests/test_orcarouter_client.py` (mocked transport).
- Prompt template functions live in `app/ai/prompts.py`. Service functions must NOT reuse a template name — alias on import (`interpretar_meta as interpretar_meta_prompt`); a same-name call recurses instead of hitting the template (this bug already happened once).
- Local provider keeps the model loaded in a module-global; a fresh process reloads the ~2.3 GB GGUF (expect ~15–20 s on first call).
- Prompts pass full language names (`English`), never codes (`en`) — the 4B model generates in the wrong language otherwise.
- API key for tests: mock `chat_json` on the imported instance (`from app.ai.orcarouter import orcarouter`), not on the module.

## Android

```powershell
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"   # JDK 17; system java (v25) breaks Gradle 8.9/AGP
$env:GRADLE_USER_HOME = "D:\gradle-home"                          # keeps caches off the nearly-full C:
cd android
.\gradlew.bat :composeApp:assembleDebug --no-daemon
# APK: android/composeApp/build/outputs/apk/debug/composeApp-debug.apk
```
- Versions (all in `android/gradle/libs.versions.toml`): Gradle 8.9, AGP 8.6.0, Kotlin 2.0.21, Compose Multiplatform 1.7.3. `applicationId`/namespace `com.interlingo.app`, minSdk 26, compileSdk/targetSdk 35.
- `abiFilters = arm64-v8a` only. Consequence: the stock x86_64 emulator CANNOT load the native libs — test on a physical arm64 device. Emulator QA works only via backend-first (`MainActivity` probes `GET /api/health` with 5 s timeout → `ApiClient(serverUrl)` when reachable, else model download + `LocalEngine`); the emulator therefore never touches native code when the backend is up.
- `ApiClient` installs Ktor `HttpTimeout` (connect 15 s / socket 120 s / request 300 s). Never remove it: without timeouts a slow server leaves the UI stuck on "Generando contenido…" forever. App errors go through `mensajeError()` in `App.kt` (raw Ktor dumps must never reach the user).
- Emulator QA (adapted from the `emulador-android` skill, adb direct, AVD `Medium_Phone_API_35`, pkg `com.interlingo.app`): host port **8000 is taken by another project's server** — run this backend on 8001 and build debug with `"-PserverUrl=http://10.0.2.2:8001"`. Seed resume sessions with direct DB inserts (no AI needed), then delete the rows after.
- JNI names are coupled: Kotlin `com.interlingo.app.llm.LlmEngine.native*` ↔ C `Java_com_interlingo_app_llm_LlmEngine_native*` in `D:\build\bridge\bridge.cpp`. Renaming the package/class breaks the bridge silently at runtime (`UnsatisfiedLinkError`).
- If the LLM feature is ever removed, remove ALL native traces together (`jniLibs/`, `externalNativeBuild` if added, `System.loadLibrary`) — leftovers break the build even when unused.
- On-device prompts are a port of `backend/app/ai/prompts.py` (`PromptEngine.kt`). Change a template in one place, change it in both.
- `MainActivity` downloads `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (~2.3 GB) from the public unsloth HF URL in `MainActivity.kt` to `filesDir/models/` on first launch. Do NOT bundle the GGUF in `assets/`/`res/raw`.
- Emulator backend URL is `http://10.0.2.2:8000` (host localhost). `android:usesCleartextTraffic="true"` exists for local HTTP dev — remove before any production release.
- Rebuilding native libs (recipe, all output to D:): `D:\build\llama.cpp` (ggml-org, depth-1 clone) configured with NDK 28.2 toolchain, `-DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-28`, flags `GGML_OPENMP=OFF LLAMA_CURL=OFF ANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON` (last one is mandatory for Android 15+ 16 KB pages), target `llama`; bridge in `D:\build\bridge` linked against `D:\build\llama-build\bin`. Copy `libllama.so libggml*.so libllm_bridge.so` + NDK `libc++_shared.so` into `jniLibs/arm64-v8a/`.

## Releases & OTA (`release.ps1` at root)

```powershell
.\release.ps1 -VersionCode 6 -VersionName "0.2.4" -ServerUrl "https://<tu-api>.onrender.com" -KeystorePassword "..." -KeyPassword "..."
# current production: versionCode 6 / v0.2.4 — bump both every release
```

- Pipeline: `:composeApp:assembleRelease` (signed) → upload APK to GitHub Release → write `version.json` + commit + push → POST Render deploy hook → poll `/api/app-version` until the new `versionCode` answers. (The SQLite upsert via `backend/scripts/set_version.py` still runs, but only matters for local dev — production reads `version.json`.)
- `release.ps1` REQUIRES `-ServerUrl` for release builds (guardrail: without it the APK bakes in the emulator URL `http://10.0.2.2:8000` and OTA fails on physical devices — this already shipped once as v0.2.0).
- `versionCode`/`versionName`/`SERVER_URL` come from Gradle props (`-PappVersionCode`, `-PappVersionName`, `-PserverUrl`), NOT from editing `build.gradle.kts`. The app reads its own `versionCode` via `PackageManager` to compare against `/api/app-version`.
- PowerShell→`gradlew.bat` quirk: quote EVERY `-P` arg (`"-PappVersionCode=2"`), otherwise values with dots split into bogus tasks (e.g. `Task '.2.0' not found`).
- Signing via `-Pandroid.injected.signing.*` props. Keystore lives in `android/keystore/` (gitignored); passwords only as CLI params, never in the repo.
- Same secrecy rule for `-RenderHookUrl` (Render deploy-hook key): pass it per-run, never commit it. After push, `release.ps1` POSTs the hook to force the redeploy, then polls `/api/app-version` until the new `versionCode` answers.
- On-device update flow (`androidMain/.../update/UpdateManager.kt`): silent check on start + manual "Buscar actualización" button; download to external Downloads with `.part`+rename; install via `FileProvider` (`${applicationId}.fileprovider` + `res/xml/file_paths.xml`). Needs `REQUEST_INSTALL_PACKAGES` and the user enabling "install unknown apps".
- Backend serves APKs from `backend/static/` (`/static/...`). `backend/static/*.apk` is gitignored — the APK lands there only at release time.
- Version truth is `backend/static/version.json` (committed, MUST be BOM-less: PS 5.1 `Set-Content -Encoding utf8` writes a BOM that breaks `json.loads` → silent fallback to defaults; `release.ps1` writes it via .NET UTF-8-no-BOM). `/api/app-version` reads it first (with `utf-8-sig`), then the `app_versions` SQLite row, then defaults. `GET /api/health` is the cheap wake-up ping (no DB).
- APK hosting is GitHub Releases (`gh release create/upload`), NOT the repo: `https://github.com/angelaramiz/Interlingo/releases/download/vX.Y.Z/interlingo.apk`. Repo is public so the phone downloads without auth.
- Render note (`render.yaml`): production uses `AI_PROVIDER=orcarouter` (the 2.3 GB local GGUF does not fit Render's disk/RAM) pointed at **OrcaRouter** (`ORCA_BASE_URL=https://api.orcarouter.ai/v1/chat/completions`, `ORCA_MODEL=z-ai/glm-5.3-flash-free`, free tier). `ORCA_API_KEY` (sk-orca-…) must be set in the Render dashboard. Orca free models REQUIRE the workspace owner to link an established GitHub account (console → profile) or add credits — otherwise every call 429s with `free_rate_limited`.
- Render service was created MANUALLY, so it IGNORES `render.yaml`: env vars (`PYTHON_VERSION`, keys) must be set in the dashboard, not the yaml. Current production: `https://interlingo.onrender.com` (+ `PYTHON_VERSION=3.12.6`, because the pinned `pydantic==2.9.2` has no wheel for Render's default Python 3.14). `backend/.python-version` (=3.12) is only a backup signal.
- Render does NOT auto-deploy from the repo here — every release must POST the deploy hook (`-RenderHookUrl`, secret, per-run only). Render free sleeps: first request after idle needs ~60 s cold start, so the app calls `UpdateManager.wakeUp()` (retries `GET /api/health` up to 3 min with UI progress) BEFORE the version check; check timeouts are 15 s connect / 60 s read for the same reason.
- `.ps1` files MUST keep the UTF-8 BOM. The `edit`/`write` tools strip it, and PowerShell 5.1 then misreads Unicode (`═ → ⚠️`) as ANSI, producing phantom parse errors far from the cause. After any `.ps1` edit, re-apply BOM and re-parse. Also: with `$ErrorActionPreference="Stop"`, any native stderr (`gh`, `git push`) is terminating — toggle EAP to `Continue` around those calls and check `$LASTEXITCODE`.

## Session memory (`.agents/`)

This project tracks itself in `.agents/` — read and update it, don't rely on chat history:

- `tasks.md` — check/uncheck as work completes; `input.md` — open questions for the developer
- `architecture.md` — current stack and decisions; `meetings/decisions/decisionN.md` — one file per decision, dated
- `.agents/rules/` — agent workflow rules; `.agents/roles/manifiesto-roles.md` — agent vs human responsibilities
- After finishing work: mark tasks, append to `history/README.md`, record new decisions

## Machine gotchas (this dev box)

- `C:` is nearly full (~1 GB free). Put models, builds, and caches on `D:` (`D:\models`, `D:\build`, `D:\gradle-home`). Never `pip`/Gradle-cache onto `C:` defaults.
- Git remote is `angelaramiz/Interlingo` (branch `main`, public). Committing + pushing is the normal flow (each `release.ps1` run commits `version.json` itself); the deploy hook, not the push, triggers Render.
- The TDD gate is TWO suites, both must stay green from `backend/` (`pytest tests/ -q`): `test_mobile_verify.py` (static app verifier — extend `app/mobile_verify.py` + tests when adding app surfaces) and `test_orcarouter_client.py` (mocked-transport unit tests). Test-writing trap: failure details echo the checked keyword (`missing <kw>`), so `kw in details` asserts are VACUOUS — assert on `result.passed` flags instead (see `TestOta` timeout/guardrail tests + `_fun_body` helper).
