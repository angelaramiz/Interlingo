# AGENTS.md — LengLearning

Language-learning-by-topic app. Two halves: `backend/` (FastAPI + SQLite, AI content engine) and `android/` (Kotlin Multiplatform + Compose, Android-first, on-device inference via bundled llama.cpp). They share one contract: `LearningApi` in `android/.../commonMain/.../data/LearningApi.kt` mirrors the 7 backend routes.

## Layout

- `backend/app/` — `main.py` (routes, also runs `Base.metadata.create_all` on import), `config.py`, `database.py`, `models.py`, `schemas.py`, `ai/` (prompts, OpenRouter client, local llama.cpp provider, dispatcher), `services/` (diagnostic, planner, lesson, evaluate, adjust)
- `android/composeApp/src/commonMain/` — UI (`App.kt` takes `api: LearningApi`), DTOs, `ApiClient`
- `android/composeApp/src/androidMain/` — `MainActivity` (downloads model, loads engine, passes `LocalEngine` to `App`), `llm/` (`LlmEngine` JNI wrapper, `ModelDownloader`, `PromptEngine`, `LocalEngine`)
- `android/composeApp/src/main/jniLibs/arm64-v8a/` — prebuilt native `.so` (checked in intent: Gradle does NOT compile native code)
- `.agents/` — project memory, keep it updated (see below)

## Backend

```powershell
cd backend
.\.venv\Scripts\python.exe -m pip install -r requirements.txt   # venv lives at backend/.venv
.\.venv\Scripts\uvicorn.exe app.main:app --reload
```

- Config is `backend/.env` (machine-local, gitignored): `AI_PROVIDER=local|openrouter`, `LOCAL_MODEL_PATH`, `OPENROUTER_MODEL`, `DATABASE_URL`. Backend reads `.env` from its own cwd — run every command from `backend/`.
- Services call `chat_json` from `app.ai.inference` (the `AI_PROVIDER` dispatcher). Never call `openrouter`/`local` directly from services.
- Prompt template functions live in `app/ai/prompts.py`. Service functions must NOT reuse a template name — alias on import (`interpretar_meta as interpretar_meta_prompt`); a same-name call recurses instead of hitting the template (this bug already happened once).
- Local provider keeps the model loaded in a module-global; a fresh process reloads the ~2.3 GB GGUF (expect ~15–20 s on first call).
- Prompts pass full language names (`English`), never codes (`en`) — the 4B model generates in the wrong language otherwise.
- API key for tests: mock `chat_json` on the imported instance (`from app.ai.openrouter import openrouter`), not on the module.

## Android

```powershell
$env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"   # JDK 17; system java (v25) breaks Gradle 8.9/AGP
$env:GRADLE_USER_HOME = "D:\gradle-home"                          # keeps caches off the nearly-full C:
cd android
.\gradlew.bat :composeApp:assembleDebug --no-daemon
# APK: android/composeApp/build/outputs/apk/debug/composeApp-debug.apk
```
- Versions (all in `android/gradle/libs.versions.toml`): Gradle 8.9, AGP 8.6.0, Kotlin 2.0.21, Compose Multiplatform 1.7.3. `applicationId`/namespace `com.lenglearning.app`, minSdk 26, compileSdk/targetSdk 35.
- `abiFilters = arm64-v8a` only. Consequence: the stock x86_64 emulator CANNOT load the native libs — test on a physical arm64 device.
- JNI names are coupled: Kotlin `com.lenglearning.app.llm.LlmEngine.native*` ↔ C `Java_com_lenglearning_app_llm_LlmEngine_native*` in `D:\build\bridge\bridge.cpp`. Renaming the package/class breaks the bridge silently at runtime (`UnsatisfiedLinkError`).
- If the LLM feature is ever removed, remove ALL native traces together (`jniLibs/`, `externalNativeBuild` if added, `System.loadLibrary`) — leftovers break the build even when unused.
- On-device prompts are a port of `backend/app/ai/prompts.py` (`PromptEngine.kt`). Change a template in one place, change it in both.
- `MainActivity` downloads `Qwen3-4B-Instruct-2507-Q4_K_M.gguf` (~2.3 GB) from the public unsloth HF URL in `MainActivity.kt` to `filesDir/models/` on first launch. Do NOT bundle the GGUF in `assets/`/`res/raw`.
- Emulator backend URL is `http://10.0.2.2:8000` (host localhost). `android:usesCleartextTraffic="true"` exists for local HTTP dev — remove before any production release.
- Rebuilding native libs (recipe, all output to D:): `D:\build\llama.cpp` (ggml-org, depth-1 clone) configured with NDK 28.2 toolchain, `-DANDROID_ABI=arm64-v8a -DANDROID_PLATFORM=android-28`, flags `GGML_OPENMP=OFF LLAMA_CURL=OFF ANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON` (last one is mandatory for Android 15+ 16 KB pages), target `llama`; bridge in `D:\build\bridge` linked against `D:\build\llama-build\bin`. Copy `libllama.so libggml*.so libllm_bridge.so` + NDK `libc++_shared.so` into `jniLibs/arm64-v8a/`.

## Releases & OTA (`release.ps1` at root)

```powershell
.\release.ps1 -VersionCode 2 -VersionName "0.2.0" -ServerUrl "https://<tu-api>.onrender.com" -KeystorePassword "..." -KeyPassword "..."
```

- Pipeline: `:composeApp:assembleRelease` (signed) → copy APK to `backend/static/lenglearning.apk` → upsert `app_versions` in SQLite (`backend/scripts/set_version.py`) → `GET {ServerUrl}/api/app-version` verify.
- `versionCode`/`versionName`/`SERVER_URL` come from Gradle props (`-PappVersionCode`, `-PappVersionName`, `-PserverUrl`), NOT from editing `build.gradle.kts`. The app reads its own `versionCode` via `PackageManager` to compare against `/api/app-version`.
- PowerShell→`gradlew.bat` quirk: quote EVERY `-P` arg (`"-PappVersionCode=2"`), otherwise values with dots split into bogus tasks (e.g. `Task '.2.0' not found`).
- Signing via `-Pandroid.injected.signing.*` props. Keystore lives in `android/keystore/` (gitignored); passwords only as CLI params, never in the repo.
- On-device update flow (`androidMain/.../update/UpdateManager.kt`): silent check on start + manual "Buscar actualización" button; download to external Downloads with `.part`+rename; install via `FileProvider` (`${applicationId}.fileprovider` + `res/xml/file_paths.xml`). Needs `REQUEST_INSTALL_PACKAGES` and the user enabling "install unknown apps".
- Backend serves APKs from `backend/static/` (`/static/...`). `backend/static/*.apk` is gitignored — the APK lands there only at release time.
- Render note (`render.yaml`): production uses `AI_PROVIDER=openrouter` (the 2.3 GB local GGUF does not fit Render's disk/RAM). `OPENROUTER_API_KEY` must be set in the Render dashboard.

## Session memory (`.agents/`)

This project tracks itself in `.agents/` — read and update it, don't rely on chat history:

- `tasks.md` — check/uncheck as work completes; `input.md` — open questions for the developer
- `architecture.md` — current stack and decisions; `meetings/decisions/decisionN.md` — one file per decision, dated
- `.agents/rules/` — agent workflow rules; `.agents/roles/manifiesto-roles.md` — agent vs human responsibilities
- After finishing work: mark tasks, append to `history/README.md`, record new decisions

## Machine gotchas (this dev box)

- `C:` is nearly full (~1 GB free). Put models, builds, and caches on `D:` (`D:\models`, `D:\build`, `D:\gradle-home`). Never `pip`/Gradle-cache onto `C:` defaults.
- Git repo is local-only (no remote, developer's choice). Commit freely; do not add a remote or push unless asked.
- The TDD gate `backend/tests/test_mobile_verify.py` must stay green (`pytest tests/test_mobile_verify.py -q` from `backend/`); extend `app/mobile_verify.py` + tests when adding app surfaces.
