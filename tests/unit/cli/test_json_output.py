"""Tests for mac_sweep.cli.json_output."""

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
    AuditResult,
    CacheAnalysis,
    CleanupCandidate,
    Diagnostic,
    Status,
)


class TestAuditToJson:
    def test_has_required_fields(self):
        result = AuditResult(
            apps=(
                AuditedApp(
                    name="Slack", source="Manual Install", detail="",
                    status=Status.ACTIVE, last_used="2026-02-01",
                    size_bytes=500000,
                ),
            ),
            hostname="test-host",
        )
        data = audit_to_json(result)
        assert data["version"] == "2.0.0"
        assert data["command"] == "audit"
        assert "timestamp" in data
        assert data["hostname"] == "test-host"
        assert "summary" in data
        assert "apps" in data

    def test_summary_counts(self):
        result = AuditResult(
            apps=(
                AuditedApp(
                    name="Slack", source="Manual Install", detail="",
                    status=Status.ACTIVE, last_used="2026-02-01",
                ),
                AuditedApp(
                    name="Old", source="Manual Install", detail="",
                    status=Status.DORMANT, last_used="2025-01-01",
                ),
            ),
        )
        data = audit_to_json(result)
        assert data["summary"]["active"] == 1
        assert data["summary"]["dormant"] == 1

    def test_serializable(self):
        result = AuditResult()
        data = audit_to_json(result)
        # Should be JSON serializable
        json_str = json.dumps(data)
        assert json_str


class TestCleanupToJson:
    def test_has_required_fields(self):
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
        assert data["total"] == 1
        assert len(data["candidates"]) == 1

    def test_empty_candidates(self):
        data = cleanup_to_json([])
        assert data["total"] == 0
        assert data["candidates"] == []


class TestCacheToJson:
    def test_analyze_mode(self):
        analyses = [
            CacheAnalysis(
                module="npm", label="npm Cache",
                available=True, total_bytes=1024,
            ),
        ]
        data = cache_to_json(analyses)
        assert data["command"] == "cache"
        assert data["mode"] == "analyze"
        assert len(data["caches"]) == 1
        assert data["total_bytes"] == 1024

    def test_clean_mode(self):
        analyses = [
            CacheAnalysis(
                module="npm", label="npm Cache",
                available=True, total_bytes=1024,
            ),
        ]
        data = cache_to_json(analyses, clean_results=[], mode="dry-run")
        assert data["mode"] == "dry-run"
        assert "cleaned" in data


class TestStatusToJson:
    def test_wraps_data(self):
        data = status_to_json({"has_audit": True, "counts": {}})
        assert data["version"] == "2.0.0"
        assert data["command"] == "status"
        assert data["has_audit"] is True


class TestDoctorToJson:
    def test_serializes_diagnostics(self):
        diagnostics = [
            Diagnostic(
                check="disk_pressure", status="ok",
                message="Disk OK",
            ),
        ]
        data = doctor_to_json(diagnostics)
        assert data["command"] == "doctor"
        assert len(data["diagnostics"]) == 1
        assert data["diagnostics"][0]["check"] == "disk_pressure"

    def test_serializable(self):
        diagnostics = [
            Diagnostic(
                check="test", status="warning",
                message="Warning", details=("a", "b"),
            ),
        ]
        data = doctor_to_json(diagnostics)
        json_str = json.dumps(data)
        assert json_str
