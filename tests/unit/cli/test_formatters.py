"""Tests for mac_sweep.cli.formatters."""

from mac_sweep.cli.formatters import (
    STATUS_EMOJI,
    format_status,
    generate_cache_report,
    generate_csv_report,
    generate_markdown_report,
)
from mac_sweep.core.models import (
    AuditedApp,
    AuditedFormula,
    AuditedPackage,
    AuditResult,
    CacheAnalysis,
    Category,
    Status,
)


class TestFormatStatus:
    def test_active(self):
        result = format_status(Status.ACTIVE)
        assert "Active" in result

    def test_string_status(self):
        result = format_status("Dormant")
        assert "Dormant" in result

    def test_all_statuses_have_emoji(self):
        for status_name in ("Active", "Occasional", "Dormant",
                            "Unknown", "Infrastructure"):
            assert status_name in STATUS_EMOJI


class TestGenerateCsvReport:
    def test_generates_csv(self):
        result = AuditResult(
            apps=(
                AuditedApp(
                    name="Slack", source="Manual Install", detail="",
                    status=Status.ACTIVE, last_used="2026-02-01",
                    description="Chat app",
                ),
            ),
        )
        csv_str = generate_csv_report(result)
        assert "Category" in csv_str  # header
        assert "Slack" in csv_str
        assert "GUI Application" in csv_str

    def test_empty_result(self):
        result = AuditResult()
        csv_str = generate_csv_report(result)
        assert "Category" in csv_str  # header exists even if empty


class TestGenerateMarkdownReport:
    def test_generates_markdown(self):
        result = AuditResult(
            apps=(
                AuditedApp(
                    name="Slack", source="Manual Install", detail="",
                    status=Status.ACTIVE, last_used="2026-02-01",
                ),
            ),
            hostname="test-host",
        )
        md = generate_markdown_report(result)
        assert "# macOS Application Audit Report" in md
        assert "Slack" in md
        assert "test-host" in md

    def test_includes_summary(self):
        result = AuditResult(
            apps=(
                AuditedApp(
                    name="Slack", source="Manual Install", detail="",
                    status=Status.ACTIVE, last_used="2026-02-01",
                ),
            ),
        )
        md = generate_markdown_report(result)
        assert "## Summary" in md

    def test_includes_cleanup_guidance(self):
        result = AuditResult(
            apps=(
                AuditedApp(
                    name="OldApp", source="Manual Install", detail="",
                    status=Status.DORMANT, last_used="2025-01-01",
                ),
            ),
        )
        md = generate_markdown_report(result)
        assert "## Cleanup Guidance" in md
        assert "OldApp" in md


class TestGenerateCacheReport:
    def test_generates_cache_report(self):
        analyses = [
            CacheAnalysis(
                module="npm", label="npm Cache",
                available=True, total_bytes=1024000,
            ),
        ]
        report = generate_cache_report(analyses)
        assert "# Developer Cache Report" in report
        assert "npm Cache" in report

    def test_empty_analyses(self):
        report = generate_cache_report([])
        assert "# Developer Cache Report" in report
