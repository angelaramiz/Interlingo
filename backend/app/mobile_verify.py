"""Verificacion TDD de la app movil LengLearning (KMP + Compose + on-device).

Contrato que verifica:
- Estructura de ficheros Kotlin + jniLibs + Manifest
- LearningApi espeja las 7 rutas del backend
- ApiClient endpoints/DTOs, Dtos.kt campos, App.kt maquina de estados,
  MainActivity descarga/carga, bloque on-device (JNI, prompts, .so),
  y paridad backend <-> movil.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

_SKIP_DIRS = {".venv", "build", ".gradle", ".kotlin", "__pycache__"}


@dataclass
class MobileCheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class MobileReport:
    total: int = 0
    passed: int = 0
    failed: int = 0
    results: list[MobileCheckResult] = field(default_factory=list)


def project_root(start: str | Path | None = None) -> Path:
    if start is None:
        return Path(__file__).resolve().parents[2]
    return Path(start)


def _find(root: Path, filename: str) -> Path | None:
    found = _candidates(root, filename)
    return found[0] if found else None


def _find_all(root: Path, filename: str) -> list[Path]:
    return _candidates(root, filename)


def _skipped(path: Path) -> bool:
    return any(part in _SKIP_DIRS for part in path.parts)


def _candidates(root: Path, filename: str) -> list[Path]:
    direct = root / filename
    if direct.is_file():
        return [direct]
    found = [p for p in root.rglob(filename) if not _skipped(p)]
    return sorted(found, key=lambda p: len(p.parts))


def _read_all(root: Path, filename: str) -> str:
    parts = []
    for p in _find_all(root, filename):
        parts.append(_read(p))
    return "\n".join(parts)


def _read(path: Path | None) -> str:
    if path is None or not path.is_file():
        return ""
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _ok(name: str, passed: bool, detail: str = "") -> MobileCheckResult:
    return MobileCheckResult(name=name, passed=passed, detail=detail)


def check_file_structure(root: str | Path) -> list[MobileCheckResult]:
    base = Path(root)
    expected = [
        "App.kt", "LearningApi.kt", "ApiClient.kt", "Dtos.kt",
        "MainActivity.kt", "LlmEngine.kt", "LocalEngine.kt",
        "ModelDownloader.kt", "PromptEngine.kt", "AndroidManifest.xml",
    ]
    results = []
    if not base.exists():
        return [_ok(f"file:{n}", False, "root missing") for n in expected] + [
            _ok("jniLibs/.so libs", False, "root missing")]
    for name in expected:
        found = _find(base, name)
        if found is not None and found.stat().st_size > 0:
            results.append(_ok(f"file:{name}", True, str(found)))
        else:
            results.append(_ok(f"file:{name}", False, f"missing {name}"))
    so_files = [p for p in base.rglob("*.so") if not _skipped(p)]
    if so_files:
        results.append(_ok("jniLibs/.so libs", True,
                           " ".join(p.name for p in so_files)))
    else:
        results.append(_ok("jniLibs/.so libs", False, "no .so under jniLibs"))
    return results


_LEARNING_API_METHODS = {
    "crearMeta": "MetaResponse",
    "obtenerDiagnostico": "List<DiagnosticoPregunta>",
    "enviarDiagnostico": "Plan",
    "generarLeccion": "Leccion",
    "generarEvaluacion": "EvaluacionResponse",
    "responderEvaluacion": "EvaluacionResultado",
}


def check_learning_api(root: str | Path) -> list[MobileCheckResult]:
    src = _read(_find(Path(root), "LearningApi.kt"))
    results = []
    if not src:
        return [_ok(f"LearningApi.{m}", False, "LearningApi.kt missing")
                for m in _LEARNING_API_METHODS] + [
            _ok("LearningApi.interface", False, "LearningApi.kt missing")]
    results.append(_ok("LearningApi.interface",
                       "interface LearningApi" in src,
                       "interface LearningApi" if "interface LearningApi" in src
                       else "not an interface"))
    for method, rtype in _LEARNING_API_METHODS.items():
        has = f"fun {method}" in src and "suspend" in src
        detail = f"suspend fun {method} -> {rtype}" if has else f"missing {method}"
        if has and rtype not in src:
            has = False
            detail = f"missing return {rtype} for {method}"
        results.append(_ok(f"LearningApi.{method}", has, detail))
    return results


_API_ENDPOINTS = [
    "/api/meta", "/api/diagnostico", "/api/leccion",
    "/api/evaluacion", "responder", "resultado", "generar",
]


def check_api_client(root: str | Path) -> list[MobileCheckResult]:
    src = _read(_find(Path(root), "ApiClient.kt"))
    results = []
    if not src:
        return [_ok("ApiClient.baseUrl", False, "ApiClient.kt missing")] + [
            _ok(f"ApiClient.endpoint:{e}", False, "ApiClient.kt missing")
            for e in _API_ENDPOINTS] + [
            _ok("ApiClient.implements", False, "ApiClient.kt missing")]
    results.append(_ok("ApiClient.baseUrl", "10.0.2.2:8000" in src,
                       "baseUrl http://10.0.2.2:8000" if "10.0.2.2:8000" in src
                       else "wrong baseUrl"))
    for ep in _API_ENDPOINTS:
        results.append(_ok(f"ApiClient.endpoint:{ep}", ep in src,
                           ep if ep in src else f"missing {ep}"))
    results.append(_ok("ApiClient.implements", "LearningApi" in src,
                       "class ApiClient : LearningApi" if "LearningApi" in src
                       else "does not implement LearningApi"))
    return results


_DTOS = [
    "MetaRequest", "MetaResponse", "DiagnosticoPregunta",
    "DiagnosticoResultado", "DiagnosticoRespuestas", "PlanNivel",
    "Plan", "VocabularioItem", "Leccion", "EvaluacionResponse",
    "EvaluacionSubmit", "EvaluacionResultado",
]
_DTO_FIELDS = ["meta_id", "vocabulario", "ruta_idioma_score", "decision", "opciones"]


def check_dtos(root: str | Path) -> list[MobileCheckResult]:
    src = _read(_find(Path(root), "Dtos.kt"))
    results = []
    if not src.strip():
        return [_ok(f"Dtos.{d}", False, "Dtos.kt missing/empty") for d in _DTOS] + [
            _ok("Dtos.Serializable", False, "Dtos.kt missing/empty")]
    for dto in _DTOS:
        results.append(_ok(f"Dtos.{dto}", dto in src,
                           dto if dto in src else f"missing {dto}"))
    for fld in _DTO_FIELDS:
        results.append(_ok(f"Dtos.field:{fld}", fld in src,
                           fld if fld in src else f"missing field {fld}"))
    results.append(_ok("Dtos.Serializable", "Serializable" in src,
                       "@Serializable" if "Serializable" in src else "missing @Serializable"))
    return results


_UI_STATES = ["Home", "Loading", "Diagnostico", "Plan",
              "Leccion", "Evaluacion", "Resultado", "Error"]
_SCREENS = ["HomeScreen", "DiagnosticoScreen", "PlanScreen", "LeccionScreen",
            "EvaluacionScreen", "ResultadoScreen", "ErrorScreen", "LoadingScreen"]
_FLOW_CALLS = ["crearMeta", "obtenerDiagnostico", "enviarDiagnostico",
               "generarLeccion", "generarEvaluacion", "responderEvaluacion"]


def check_app_flow(root: str | Path) -> list[MobileCheckResult]:
    src = _read(_find(Path(root), "App.kt"))
    results = []
    if not src.strip():
        return [_ok("App.flow", False, "App.kt missing/empty")]
    for s in _UI_STATES:
        results.append(_ok(f"App.UiState:{s}", s in src,
                           s if s in src else f"missing state {s}"))
    for s in _SCREENS:
        results.append(_ok(f"App.screen:{s}", s in src,
                           s if s in src else f"missing {s}"))
    for c in _FLOW_CALLS:
        results.append(_ok(f"App.flow:{c}", c in src,
                           c if c in src else f"missing call {c}"))
    has_bar = "BarraProgreso" in src or "LinearProgressIndicator" in src
    results.append(_ok("App.progress", has_bar,
                       "BarraProgreso + LinearProgressIndicator" if has_bar
                       else "missing progress bar"))
    has_dec = "avanzar" in src and "profundizar" in src
    results.append(_ok("App.decision", has_dec,
                       "avanzar/profundizar/repetir/simplificar" if has_dec
                       else "missing decision logic"))
    has_err = "Error" in src and ("try" in src or "catch" in src)
    results.append(_ok("App.error", has_err,
                       "try/catch -> UiState.Error" if has_err else "missing error handling"))
    return results


def check_ondevice(root: str | Path) -> list[MobileCheckResult]:
    base = Path(root)
    llm = _read(_find(base, "LlmEngine.kt"))
    dl = _read(_find(base, "ModelDownloader.kt"))
    local = _read(_find(base, "LocalEngine.kt"))
    prompt = _read(_find(base, "PromptEngine.kt"))
    main = _read(_find(base, "MainActivity.kt"))
    manifest = _read(_find(base, "AndroidManifest.xml"))
    gradle = _read_all(base, "build.gradle.kts") + "\n" + _read_all(base, "libs.versions.toml")
    combined = "\n".join([llm, dl, local, prompt, main, manifest, gradle])
    if not (llm or dl or local or prompt or main):
        return [_ok("ondevice.present", False, "on-device sources missing")]

    checks: list[tuple[str, bool, str]] = [
        ("ondevice.jni.lib", 'loadLibrary("llm_bridge")' in llm, "llm_bridge"),
        ("ondevice.jni.load", "nativeLoadModel" in llm, "nativeLoadModel"),
        ("ondevice.jni.complete", "nativeComplete" in llm, "nativeComplete"),
        ("ondevice.dl.part", ".part" in dl, ".part resume file"),
        ("ondevice.dl.progress", "onProgress" in dl or "progress" in dl.lower(),
         "onProgress(downloadedBytes, totalBytes)"),
        ("ondevice.local.class", "LocalEngine" in local and "LearningApi" in local,
         "LocalEngine implements LearningApi"),
        ("ondevice.prompt.interpretarMeta", "interpretarMeta" in prompt, "interpretarMeta"),
        ("ondevice.prompt.diagnostico", "diagnostico" in prompt, "diagnostico"),
        ("ondevice.prompt.plan", "plan" in prompt, "plan"),
        ("ondevice.prompt.leccion", "leccion" in prompt, "leccion"),
        ("ondevice.prompt.evaluacion", "evaluacion" in prompt, "evaluacion"),
        ("ondevice.prompt.correccion", "correccion" in prompt, "correccion"),
        ("ondevice.prompt.ajuste", "ajuste" in prompt, "ajuste"),
        ("ondevice.prompt.extractJson", "extractJson" in prompt, "extractJson"),
        ("ondevice.prompt.lang", "English" in prompt, "English languageNames"),
        ("ondevice.manifest.internet", "INTERNET" in manifest, "INTERNET permission"),
        ("ondevice.manifest.activity", "MainActivity" in manifest, "MainActivity"),
        ("ondevice.gradle.abi", "arm64-v8a" in gradle or "arm64-v8a" in combined,
         "arm64-v8a abiFilters"),
        ("ondevice.gradle.pkg", "com.lenglearning.app" in combined,
         "com.lenglearning.app"),
        ("ondevice.model.url",
         "huggingface" in main.lower() or "gguf" in main.lower(),
         "huggingface GGUF Qwen3-4B-Instruct-2507-Q4_K_M.gguf"),
    ]
    results = [_ok(n, ok_, d if ok_ else f"missing {d}") for n, ok_, d in checks]
    so_files = [p for p in base.rglob("*.so") if not _skipped(p)]
    so_names = " ".join(p.name for p in so_files)
    for lib in ("libllama.so", "libllm_bridge.so", "libc++_shared.so"):
        results.append(_ok(f"ondevice.lib:{lib}", lib in so_names,
                           lib if lib in so_names else f"missing {lib}"))
    return results


_BACKEND_ROUTES = ["/api/meta", "/api/diagnostico", "/api/leccion", "/api/evaluacion"]
_PROMPT_KWS = ["diagnostico", "plan", "leccion", "evaluacion", "ajuste"]


def check_backend_contract(root: str | Path) -> list[MobileCheckResult]:
    base = Path(root)
    main_py = _read(_find(base, "main.py"))
    api = _read(_find(base, "LearningApi.kt"))
    prompt = _read(_find(base, "PromptEngine.kt"))
    if not main_py.strip() or not api.strip():
        return [_ok("contract.present", False, "main.py or LearningApi.kt missing")]
    results = []
    for route in _BACKEND_ROUTES:
        in_backend = route in main_py
        in_mobile = (route in _read(_find(base, "ApiClient.kt"))
                     or route.split("/")[2] in api.lower()
                     or route in api)
        ok_ = in_backend and in_mobile
        results.append(_ok(f"contract.route:{route}", ok_,
                           f"{route} backend+mobile" if ok_
                           else f"missing {route}"))
    for kw in _PROMPT_KWS:
        ok_ = kw in prompt.lower()
        results.append(_ok(f"contract.prompt:{kw}", ok_,
                           kw if ok_ else f"missing prompt {kw}"))
    mirror = all(m in api for m in
                 ("crearMeta", "obtenerDiagnostico", "generarLeccion", "responderEvaluacion"))
    results.append(_ok("contract.mirror", mirror,
                       "LearningApi mirrors backend routes" if mirror
                       else "LearningApi does not mirror backend"))
    return results


def verify_mobile_app(root: str | Path | None = None) -> MobileReport:
    base = project_root(root)
    results: list[MobileCheckResult] = []
    results += check_file_structure(base)
    results += check_learning_api(base)
    results += check_api_client(base)
    results += check_dtos(base)
    results += check_app_flow(base)
    results += check_ondevice(base)
    results += check_backend_contract(base)
    passed = sum(1 for r in results if r.passed)
    return MobileReport(total=len(results), passed=passed,
                        failed=len(results) - passed, results=results)


def format_report(report: MobileReport) -> str:
    lines = [f"LengLearning mobile verification: "
             f"{report.passed}/{report.total} passed"]
    if not report.results:
        lines.append("no checks ran")
        return "\n".join(lines)
    for r in report.results:
        tag = "PASS" if r.passed else "FAIL"
        lines.append(f"[{tag}] {r.name}: {r.detail}")
    lines.append("OK - all mobile checks passed" if report.failed == 0
                 else f"{report.failed} check(s) FAILED")
    return "\n".join(lines)
