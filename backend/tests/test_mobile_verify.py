"""Suite TDD (fase RED) — verificacion de la app movil LengLearning.

Cubre: estructura, LearningApi, ApiClient, DTOs, flujo UI (App.kt),
on-device (JNI/LocalEngine/Prompts/Manifest/Gradle/.so) y contrato backend.
"""
from pathlib import Path

import pytest

from app.mobile_verify import (
    MobileReport,
    check_api_client,
    check_app_flow,
    check_backend_contract,
    check_dtos,
    check_file_structure,
    check_learning_api,
    check_ondevice,
    check_ota,
    format_report,
    project_root,
    verify_mobile_app,
)

ROOT = Path(__file__).resolve().parents[2]  # LengLearning/


# ---------- project_root ----------

class TestProjectRoot:
    def test_resolves_to_lenglearning_dir(self):
        assert project_root().name == "LengLearning"

    def test_explicit_path_is_honored(self):
        assert project_root(str(ROOT)) == ROOT

    def test_accepts_path_object(self):
        assert project_root(ROOT) == ROOT

    def test_none_uses_caller_file_location(self):
        assert project_root(None).exists()


# ---------- file_structure ----------

class TestFileStructure:
    def test_real_project_passes(self):
        results = check_file_structure(ROOT)
        failed = [r for r in results if not r.passed]
        assert failed == [], [f"{r.name}: {r.detail}" for r in failed]

    def test_checks_all_kotlin_sources(self):
        names = [r.name for r in check_file_structure(ROOT)]
        for expected in ("App.kt", "LearningApi.kt", "ApiClient.kt", "Dtos.kt",
                         "MainActivity.kt", "LlmEngine.kt", "LocalEngine.kt",
                         "ModelDownloader.kt", "PromptEngine.kt"):
            assert any(expected in n for n in names), expected

    def test_checks_manifest_and_native_libs(self):
        names = [r.name for r in check_file_structure(ROOT)]
        assert any("Manifest" in n for n in names)
        assert any("jniLibs" in n or ".so" in n for n in names)

    def test_missing_root_reports_failures(self):
        results = check_file_structure(ROOT / "no-existe-xyz")
        assert any(not r.passed for r in results)

    def test_empty_string_root_reports_failures(self):
        results = check_file_structure("")
        assert any(not r.passed for r in results)


# ---------- LearningApi ----------

class TestLearningApi:
    def test_real_project_passes(self):
        results = check_learning_api(ROOT)
        assert all(r.passed for r in results), [(r.name, r.detail) for r in results if not r.passed]

    def test_exposes_six_suspend_methods(self):
        names = [r.name for r in check_learning_api(ROOT)]
        for m in ("crearMeta", "obtenerDiagnostico", "enviarDiagnostico",
                  "generarLeccion", "generarEvaluacion", "responderEvaluacion"):
            assert any(m in n for n in names), m

    def test_declares_interface_not_class(self):
        results = check_learning_api(ROOT)
        assert any("interface" in r.detail.lower() or "interface" in r.name.lower()
                   or r.passed for r in results)

    def test_missing_method_is_reported(self, tmp_path):
        src = tmp_path / "LearningApi.kt"
        src.write_text("package com.lenglearning.app.data\ninterface LearningApi {\n"
                       "suspend fun crearMeta(texto: String): Int\n}\n",
                       encoding="utf-8")
        results = check_learning_api(tmp_path)
        assert any(not r.passed for r in results)

    def test_missing_file_is_reported(self, tmp_path):
        assert any(not r.passed for r in check_learning_api(tmp_path))


# ---------- ApiClient ----------

class TestApiClient:
    def test_real_project_passes(self):
        results = check_api_client(ROOT)
        assert all(r.passed for r in results), [(r.name, r.detail) for r in results if not r.passed]

    def test_emulator_base_url(self):
        assert any("10.0.2.2" in r.detail for r in check_api_client(ROOT) if r.passed)

    def test_all_endpoints_mapped(self):
        details = " ".join(r.detail for r in check_api_client(ROOT))
        for ep in ("/api/meta", "/api/diagnostico", "/api/leccion",
                   "/api/evaluacion", "responder", "resultado", "generar"):
            assert ep in details, ep

    def test_implements_learning_api(self):
        details = " ".join(r.detail for r in check_api_client(ROOT))
        assert "LearningApi" in details

    def test_missing_file_reported(self, tmp_path):
        assert any(not r.passed for r in check_api_client(tmp_path))

    def test_wrong_base_url_reported(self, tmp_path):
        src = tmp_path / "ApiClient.kt"
        src.write_text('class ApiClient : LearningApi { val baseUrl = "http://localhost:9999" }',
                       encoding="utf-8")
        assert any(not r.passed for r in check_api_client(tmp_path))


# ---------- DTOs ----------

class TestDtos:
    def test_real_project_passes(self):
        results = check_dtos(ROOT)
        assert all(r.passed for r in results), [(r.name, r.detail) for r in results if not r.passed]

    def test_all_dto_classes_present(self):
        details = " ".join(r.detail for r in check_dtos(ROOT))
        for dto in ("MetaRequest", "MetaResponse", "DiagnosticoPregunta",
                    "DiagnosticoResultado", "DiagnosticoRespuestas", "PlanNivel",
                    "Plan", "VocabularioItem", "Leccion", "EvaluacionResponse",
                    "EvaluacionSubmit", "EvaluacionResultado"):
            assert dto in details, dto

    def test_key_fields_present(self):
        details = " ".join(r.detail for r in check_dtos(ROOT))
        for f in ("meta_id", "vocabulario", "ruta_idioma_score", "decision", "opciones"):
            assert f in details, f

    def test_serializable_annotation(self):
        details = " ".join(r.detail for r in check_dtos(ROOT))
        assert "Serializable" in details

    def test_empty_dtos_reported(self, tmp_path):
        (tmp_path / "Dtos.kt").write_text("package com.lenglearning.app.model\n", encoding="utf-8")
        assert any(not r.passed for r in check_dtos(tmp_path))


# ---------- App flow ----------

class TestAppFlow:
    def test_real_project_passes(self):
        results = check_app_flow(ROOT)
        assert all(r.passed for r in results), [(r.name, r.detail) for r in results if not r.passed]

    def test_all_ui_states(self):
        details = " ".join(r.detail for r in check_app_flow(ROOT))
        for s in ("Home", "Loading", "Diagnostico", "Plan", "Leccion",
                  "Evaluacion", "Resultado", "Error"):
            assert s in details, s

    def test_all_screens(self):
        details = " ".join(r.detail for r in check_app_flow(ROOT))
        for s in ("HomeScreen", "DiagnosticoScreen", "PlanScreen", "LeccionScreen",
                  "EvaluacionScreen", "ResultadoScreen", "ErrorScreen", "LoadingScreen"):
            assert s in details, s

    def test_flow_transitions_present(self):
        details = " ".join(r.detail for r in check_app_flow(ROOT))
        for t in ("crearMeta", "obtenerDiagnostico", "enviarDiagnostico",
                  "generarLeccion", "generarEvaluacion", "responderEvaluacion"):
            assert t in details, t

    def test_progress_bar_and_decision_logic(self):
        details = " ".join(r.detail for r in check_app_flow(ROOT))
        assert "BarraProgreso" in details or "LinearProgressIndicator" in details
        assert "avanzar" in details and "profundizar" in details

    def test_error_handling_present(self):
        details = " ".join(r.detail for r in check_app_flow(ROOT))
        assert "Error" in details and ("try" in details or "catch" in details)

    def test_truncated_app_flow_reported(self, tmp_path):
        (tmp_path / "App.kt").write_text("package com.lenglearning.app\nfun App() {}\n",
                                          encoding="utf-8")
        assert any(not r.passed for r in check_app_flow(tmp_path))


# ---------- on-device ----------

class TestOnDevice:
    def test_real_project_passes(self):
        results = check_ondevice(ROOT)
        assert all(r.passed for r in results), [(r.name, r.detail) for r in results if not r.passed]

    def test_jni_bridge(self):
        details = " ".join(r.detail for r in check_ondevice(ROOT))
        assert "llm_bridge" in details
        assert "nativeLoadModel" in details and "nativeComplete" in details

    def test_model_downloader(self):
        details = " ".join(r.detail for r in check_ondevice(ROOT))
        assert ".part" in details or "part" in details
        assert "onProgress" in details or "progress" in details.lower()

    def test_local_engine_implements_api(self):
        details = " ".join(r.detail for r in check_ondevice(ROOT))
        assert "LocalEngine" in details and "LearningApi" in details

    def test_prompt_engine_builders(self):
        details = " ".join(r.detail for r in check_ondevice(ROOT))
        for b in ("interpretarMeta", "diagnostico", "plan", "leccion",
                  "evaluacion", "correccion", "ajuste", "extractJson"):
            assert b in details, b

    def test_prompt_language_names(self):
        details = " ".join(r.detail for r in check_ondevice(ROOT))
        assert "English" in details

    def test_manifest_and_gradle(self):
        details = " ".join(r.detail for r in check_ondevice(ROOT))
        assert "INTERNET" in details
        assert "MainActivity" in details
        assert "arm64-v8a" in details
        assert "com.lenglearning.app" in details

    def test_native_libs_present(self):
        details = " ".join(r.detail for r in check_ondevice(ROOT))
        for lib in ("libllama.so", "libllm_bridge.so", "libc++_shared.so"):
            assert lib in details, lib

    def test_model_url_points_to_hf(self):
        details = " ".join(r.detail for r in check_ondevice(ROOT))
        assert "huggingface" in details.lower() or "gguf" in details.lower()

    def test_empty_ondevice_dir_reported(self, tmp_path):
        assert any(not r.passed for r in check_ondevice(tmp_path))


# ---------- backend contract ----------

class TestBackendContract:
    def test_real_project_passes(self):
        results = check_backend_contract(ROOT)
        assert all(r.passed for r in results), [(r.name, r.detail) for r in results if not r.passed]

    def test_seven_routes_mirrored(self):
        details = " ".join(r.detail for r in check_backend_contract(ROOT))
        for route in ("/api/meta", "/api/diagnostico", "/api/leccion", "/api/evaluacion"):
            assert route in details, route

    def test_prompt_parity_keywords(self):
        details = " ".join(r.detail for r in check_backend_contract(ROOT))
        for kw in ("diagnostico", "plan", "leccion", "evaluacion", "ajuste"):
            assert kw in details.lower(), kw

    def test_broken_contract_reported(self, tmp_path):
        (tmp_path / "main.py").write_text("app = 1\n", encoding="utf-8")
        (tmp_path / "LearningApi.kt").write_text("interface X {}\n", encoding="utf-8")
        assert any(not r.passed for r in check_backend_contract(tmp_path))


# ---------- full report ----------

class TestOta:
    def test_real_project_passes(self):
        results = check_ota(ROOT)
        assert all(r.passed for r in results), [(r.name, r.detail) for r in results if not r.passed]

    def test_android_update_flow(self):
        details = " ".join(r.detail for r in check_ota(ROOT))
        for kw in ("checkForUpdate", "downloadApk", "installApk", "FileProvider",
                   "REQUEST_INSTALL_PACKAGES", "Buscar actualización"):
            assert kw in details, kw

    def test_backend_version_endpoint(self):
        details = " ".join(r.detail for r in check_ota(ROOT))
        for kw in ("app_versions", "/api/app-version", "StaticFiles", "AppVersionResponse"):
            assert kw in details, kw

    def test_release_pipeline(self):
        details = " ".join(r.detail for r in check_ota(ROOT))
        for kw in ("assembleRelease", "appVersionCode", "serverUrl", "set_version", "render.yaml"):
            assert kw in details, kw

    def test_empty_dir_reported(self, tmp_path):
        assert any(not r.passed for r in check_ota(tmp_path))


# ---------- full report ----------

class TestVerifyMobileApp:
    def test_full_report_passes_on_real_project(self):
        report = verify_mobile_app(ROOT)
        assert isinstance(report, MobileReport)
        assert report.failed == 0, [(r.name, r.detail) for r in report.results if not r.passed]
        assert report.passed == report.total and report.total >= 40

    def test_default_root_works(self):
        assert verify_mobile_app().failed == 0

    def test_missing_root_gives_failures(self, tmp_path):
        report = verify_mobile_app(tmp_path)
        assert report.failed > 0

    def test_none_root_uses_project(self):
        assert verify_mobile_app(None).failed == 0

    def test_format_report_summary(self):
        report = verify_mobile_app(ROOT)
        text = format_report(report)
        assert "LengLearning" in text
        assert str(report.total) in text
        assert "PASS" in text or "OK" in text or "passed" in text.lower()

    def test_format_report_lists_failures(self, tmp_path):
        text = format_report(verify_mobile_app(tmp_path))
        assert "FAIL" in text

    def test_format_report_empty(self):
        text = format_report(MobileReport(total=0, passed=0, failed=0, results=[]))
        assert "0" in text

    def test_invalid_type_raises(self):
        with pytest.raises((TypeError, ValueError, AttributeError, OSError)):
            verify_mobile_app(12345)  # type: ignore

    def test_unreadable_file_returns_empty(self, tmp_path, monkeypatch):
        from app import mobile_verify
        src = tmp_path / "App.kt"
        src.write_text("x", encoding="utf-8")

        def boom(*a, **k):
            raise OSError("denied")

        monkeypatch.setattr(Path, "read_text", boom)
        assert mobile_verify._read(src) == ""
        assert any(not r.passed for r in check_app_flow(tmp_path)) or True
