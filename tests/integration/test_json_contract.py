"""Integration tests for JSON API contract.

These tests validate the JSON output contract that serves as the
API for a potential GUI frontend (SwiftUI).
"""

import json

from mac_sweep.cli.json_output import (
    audit_to_json,
    cache_to_json,
    cleanup_to_json,
    doctor_to_json,
    status_to_json,
)
from mac_sweep.core.models import (
    AuditedApp,
    AuditedFormula,
    AuditedPackage,
    AuditResult,
    CacheAnalysis,
    Category,
    CleanResult,
    CleanupCandidate,
    Diagnostic,
    Status,
)


def _make_audit_result():
    return AuditResult(
        apps=(
            AuditedApp(
                name="Slack", source="Manual Install", detail="",
                status=Status.ACTIVE, last_used="2026-02-01",
                description="Chat", size_bytes=500000000,
            ),
            AuditedApp(
                name="OldApp", source="Homebrew Cask", detail="cask: old",
                status=Status.DORMANT, last_used="2025-01-01",
                description="Old", size_bytes=100000000,
            ),
        ),
        formulas=(
            AuditedFormula(
                name="hugo", install_type="explicit",
                required_by="", status=Status.DORMANT,
                description="Static site generator",
            ),
        ),
        npm_packages=(
            AuditedPackage(
                name="eslint", category=Category.NPM_GLOBAL,
                version="8.56.0", status=Status.UNKNOWN,
                description="Linter",
            ),
        ),
        pipx_packages=(),
        pip_packages=(
            AuditedPackage(
                name="numpy", category=Category.PIP,
                version="1.24.0", status=Status.INFRASTRUCTURE,
                description="Numerical computing",
            ),
        ),
        gem_packages=(),
        hostname="test-mac.local",
    )


class TestAuditJsonContract:
    def test_top_level_fields(self):
        data = audit_to_json(_make_audit_result())
        assert data["version"] == "2.0.0"
        assert data["command"] == "audit"
        assert "timestamp" in data
        assert data["hostname"] == "test-mac.local"

    def test_summary_fields(self):
        data = audit_to_json(_make_audit_result())
        summary = data["summary"]
        assert "active" in summary
        assert "occasional" in summary
        assert "dormant" in summary
        assert "unknown" in summary
        assert "infrastructure" in summary
        assert "total" in summary
        assert "total_size_bytes" in summary
        assert "dormant_size_bytes" in summary

    def test_apps_array(self):
        data = audit_to_json(_make_audit_result())
        assert isinstance(data["apps"], list)
        app = data["apps"][0]
        assert "name" in app
        assert "source" in app
        assert "status" in app
        assert "size_bytes" in app
        assert "last_used" in app
        assert "description" in app

    def test_formulas_array(self):
        data = audit_to_json(_make_audit_result())
        assert isinstance(data["formulas"], list)
        f = data["formulas"][0]
        assert "name" in f
        assert "install_type" in f
        assert "status" in f

    def test_package_arrays(self):
        data = audit_to_json(_make_audit_result())
        assert isinstance(data["npm_packages"], list)
        assert isinstance(data["pipx_packages"], list)
        assert isinstance(data["pip_packages"], list)
        assert isinstance(data["gem_packages"], list)

    def test_json_serializable(self):
        data = audit_to_json(_make_audit_result())
        json_str = json.dumps(data)
        parsed = json.loads(json_str)
        assert parsed["command"] == "audit"


class TestCacheJsonContract:
    def test_analyze_mode(self):
        analyses = [
            CacheAnalysis(
                module="homebrew", label="Homebrew Cache",
                available=True, total_bytes=2500000000,
            ),
        ]
        data = cache_to_json(analyses)
        assert data["version"] == "2.0.0"
        assert data["command"] == "cache"
        assert data["mode"] == "analyze"
        assert isinstance(data["caches"], list)
        assert "total_bytes" in data
        assert "total_human" in data

        cache_entry = data["caches"][0]
        assert cache_entry["module"] == "homebrew"
        assert cache_entry["label"] == "Homebrew Cache"
        assert cache_entry["available"] is True
        assert "total_bytes" in cache_entry
        assert "total_human" in cache_entry
        assert "items" in cache_entry

    def test_clean_mode(self):
        analyses = [
            CacheAnalysis(
                module="npm", label="npm Cache",
                available=True, total_bytes=1000000,
            ),
        ]
        clean_results = [
            CleanResult(
                module="npm", label="npm Cache",
                freed_bytes=500000, items_removed=3,
            ),
        ]
        data = cache_to_json(analyses, clean_results, mode="dry-run")
        assert data["mode"] == "dry-run"
        assert "cleaned" in data
        cleaned = data["cleaned"][0]
        assert "freed_bytes" in cleaned
        assert "freed_human" in cleaned
        assert "items_removed" in cleaned

    def test_json_serializable(self):
        data = cache_to_json([])
        json_str = json.dumps(data)
        assert json.loads(json_str)


class TestStatusJsonContract:
    def test_required_fields(self):
        input_data = {
            "has_audit": True,
            "audit_age_hours": 2.5,
            "counts": {"gui_apps": 67, "formulas": 120, "dormant": 5},
            "disk": {
                "total_app_bytes": 25e9,
                "dormant_bytes": 3.2e9,
                "cache_bytes": 8e9,
                "reclaimable_bytes": 11.2e9,
            },
        }
        data = status_to_json(input_data)
        assert data["version"] == "2.0.0"
        assert data["command"] == "status"
        assert "timestamp" in data
        assert data["has_audit"] is True
        assert data["audit_age_hours"] == 2.5
        assert data["counts"]["gui_apps"] == 67

    def test_json_serializable(self):
        data = status_to_json({"has_audit": False})
        json_str = json.dumps(data)
        assert json.loads(json_str)


class TestDoctorJsonContract:
    def test_required_fields(self):
        diagnostics = [
            Diagnostic(
                check="disk_pressure", status="ok",
                message="Disk space OK (45 GB free)",
            ),
            Diagnostic(
                check="broken_symlinks", status="warning",
                message="3 broken symlinks",
                details=("foo", "bar", "baz"),
            ),
        ]
        data = doctor_to_json(diagnostics)
        assert data["version"] == "2.0.0"
        assert data["command"] == "doctor"
        assert isinstance(data["diagnostics"], list)
        assert len(data["diagnostics"]) == 2

        d = data["diagnostics"][0]
        assert "check" in d
        assert "status" in d
        assert "message" in d
        assert "details" in d

    def test_details_is_list(self):
        diagnostics = [
            Diagnostic(
                check="test", status="ok", message="OK",
                details=("a", "b"),
            ),
        ]
        data = doctor_to_json(diagnostics)
        assert isinstance(data["diagnostics"][0]["details"], list)

    def test_json_serializable(self):
        data = doctor_to_json([])
        json_str = json.dumps(data)
        assert json.loads(json_str)


class TestCleanupJsonContract:
    def test_required_fields(self):
        candidates = [
            CleanupCandidate(
                name="hugo", category="Homebrew Formula",
                description="SSG", status="Dormant",
                removal_method="brew_formula",
                removal_cmd=("brew", "uninstall", "hugo"),
            ),
        ]
        data = cleanup_to_json(candidates)
        assert data["version"] == "2.0.0"
        assert data["command"] == "cleanup"
        assert "total" in data
        assert isinstance(data["candidates"], list)

        c = data["candidates"][0]
        assert "name" in c
        assert "category" in c
        assert "status" in c
        assert "removal_cmd" in c
        assert "description" in c
