"""Tests for mac_sweep.core.doctor."""

from mac_sweep.core.doctor import (
    check_disk_pressure,
    check_outdated_audit,
    run_checks,
)
from mac_sweep.core.models import Diagnostic


class TestRunChecks:
    def test_returns_list_of_diagnostics(self):
        results = run_checks()
        assert isinstance(results, list)
        assert len(results) > 0
        for d in results:
            assert isinstance(d, Diagnostic)
            assert d.check
            assert d.status in ("ok", "warning", "error")
            assert d.message


class TestCheckDiskPressure:
    def test_returns_diagnostic(self):
        result = check_disk_pressure()
        assert isinstance(result, Diagnostic)
        assert result.check == "disk_pressure"
        # On most dev machines there should be enough space
        assert result.status in ("ok", "warning", "error")


class TestCheckOutdatedAudit:
    def test_no_report_warns(self):
        # Assuming no report exists at "reports/app-audit-report.csv"
        # in the test working directory
        result = check_outdated_audit()
        assert isinstance(result, Diagnostic)
        assert result.check == "outdated_audit"
