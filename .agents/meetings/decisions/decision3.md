# Decisión 3 — Versionado, OTA y releases

**Fecha:** 2026-08-12

## Decisiones
- **Repo**: solo `git init` + commits locales. Sin remoto por ahora (decisión del desarrollador).
- **Hosting del backend**: **Render** (`render.yaml` en la raíz; `AI_PROVIDER=openrouter` allí porque el GGUF local no cabe en Render).
- **Firma**: keystore release generado en `android/keystore/` (gitignored). Passwords por parámetro en cada release, nunca al repo.

## Sistema OTA instalado (adaptación de la skill `ota-android-generic` de inventorio)
- Backend: tabla `app_versions` (clave/valor JSON) + `GET /api/app-version` + APKs en `backend/static/` (`/static/lenglearning.apk`).
- Android: `UpdateManager` (check silencioso al arrancar + botón manual "Buscar actualización", descarga con `.part`, instalación vía FileProvider). Requiere `REQUEST_INSTALL_PACKAGES` y aceptar "instalar apps desconocidas".
- `release.ps1` (raíz): build release firmado → copia APK a `backend/static/` → actualiza SQLite (`backend/scripts/set_version.py`) → verifica endpoint.
- Versionado y `SERVER_URL` por props de Gradle (`-PappVersionCode`, `-PappVersionName`, `-PserverUrl`).
