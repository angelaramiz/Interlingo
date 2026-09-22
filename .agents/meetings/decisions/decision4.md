# Decisión 4 — Nombre del producto: Interlingo

**Fecha:** 2026-08-12

## Decisión
El producto se llama **Interlingo** (interest + lingo). Aplica a label de la app, repo y package.

## Alcance del renombre
- Label: "LengLearning" → "Interlingo".
- Package: `com.lenglearning.app` → `com.interlingo.app` (namespace, applicationId, fuentes Kotlin, prefijos JNI en `bridge.cpp` + rebuild de `libllm_bridge.so`).
- Backend, scripts, APK (`interlingo.apk`), DB (`interlingo.db`), docs y verificador.
- Carpeta del proyecto: `LengLearning/` → `Interlingo/`.

## Conservado a propósito
- Keystore y alias (`lenglearning-release.jks` / `lenglearning`): la identidad de firma debe persistir para que el OTA actualice sobre instalaciones existentes.
- Modelo GGUF: nombre de archivo original de HuggingFace.
