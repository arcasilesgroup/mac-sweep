"""Tests for mac_sweep.core.audit."""

import os
import tempfile
import time

from mac_sweep.core.audit import classify_age, format_date, parse_mdls_date, process_audit
from mac_sweep.core.models import Status


class TestClassifyAge:
    def test_active(self):
        epoch = time.time() - 86400  # 1 day ago
        assert classify_age(epoch) == Status.ACTIVE

    def test_occasional(self):
        epoch = time.time() - (15 * 86400)  # 15 days ago
        assert classify_age(epoch) == Status.OCCASIONAL

    def test_dormant(self):
        epoch = time.time() - (60 * 86400)  # 60 days ago
        assert classify_age(epoch) == Status.DORMANT

    def test_zero_epoch(self):
        assert classify_age(0) == Status.UNKNOWN

    def test_negative_epoch(self):
        assert classify_age(-1) == Status.UNKNOWN

    def test_none_epoch(self):
        assert classify_age(None) == Status.UNKNOWN

    def test_boundary_seven_days(self):
        epoch = time.time() - (7 * 86400)
        assert classify_age(epoch) == Status.ACTIVE

    def test_boundary_thirty_days(self):
        epoch = time.time() - (30 * 86400)
        assert classify_age(epoch) == Status.OCCASIONAL

    def test_with_explicit_now(self):
        now = 1000000
        epoch = now - 86400  # 1 day before now
        assert classify_age(epoch, now=now) == Status.ACTIVE


class TestFormatDate:
    def test_valid_epoch(self):
        result = format_date(1736899200)
        assert result.startswith("2025-01-1")

    def test_zero_epoch(self):
        assert format_date(0) == "N/A"

    def test_none_epoch(self):
        assert format_date(None) == "N/A"

    def test_negative_epoch(self):
        assert format_date(-1) == "N/A"


class TestParseMdlsDate:
    def test_valid_date_with_timezone(self):
        result = parse_mdls_date("2025-01-15 12:34:56 +0000")
        assert result > 0

    def test_null_string(self):
        assert parse_mdls_date("(null)") == 0
        assert parse_mdls_date("null") == 0

    def test_empty_string(self):
        assert parse_mdls_date("") == 0

    def test_none(self):
        assert parse_mdls_date(None) == 0

    def test_invalid_format(self):
        assert parse_mdls_date("not-a-date") == 0

    def test_whitespace_handling(self):
        result = parse_mdls_date("  2025-01-15 12:34:56 +0000  ")
        assert result > 0


class TestProcessAudit:
    def test_empty_tmpdir(self):
        with tempfile.TemporaryDirectory() as td:
            result = process_audit(td)
            assert result.apps == ()
            assert result.formulas == ()

    def test_with_sample_data(self, sample_audit_dir):
        result = process_audit(sample_audit_dir)
        assert isinstance(result.apps, tuple)
        # Should find apps from app_paths.txt
        app_names = [a.name for a in result.apps]
        assert "Slack" in app_names
        assert "OldApp" in app_names

    def test_running_app_detected_active(self, sample_audit_dir):
        result = process_audit(sample_audit_dir)
        slack = next((a for a in result.apps if a.name == "Slack"), None)
        assert slack is not None
        assert slack.status == Status.ACTIVE

    def test_returns_hostname(self, sample_audit_dir):
        result = process_audit(sample_audit_dir)
        assert result.hostname  # should be non-empty

    def test_result_is_frozen(self, sample_audit_dir):
        result = process_audit(sample_audit_dir)
        assert hash(result) is not None
