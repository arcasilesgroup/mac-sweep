"""Tests for mac_sweep.core.cleanup."""

import csv
import os
import tempfile

from mac_sweep.core.cleanup import load_candidates, select_by_names, sort_for_browse


def _write_csv(rows):
    """Write a temporary CSV with the standard audit columns."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="",
    )
    writer = csv.writer(tmp)
    writer.writerow(["Category", "Name", "Source", "Detail", "Status",
                     "Last Used", "Description", "Size"])
    for row in rows:
        writer.writerow(row)
    tmp.close()
    return tmp.name


# ── Test data rows ──

ROW_ACTIVE_GUI = [
    "GUI Application", "Slack", "Manual Install", "", "Active",
    "2026-02-01", "Team communication", "500000"]
ROW_OCCASIONAL_GUI = [
    "GUI Application", "Warp", "Homebrew Cask", "cask: warp", "Occasional",
    "2026-01-15", "Terminal emulator", "300000"]
ROW_DORMANT_FORMULA = [
    "Homebrew Formula", "hugo", "explicit", "explicitly installed", "Dormant",
    "N/A", "Static site generator", ""]
ROW_UNKNOWN_NPM = [
    "npm Global", "eslint", "npm", "v8.56.0", "Unknown",
    "N/A", "JavaScript linter", ""]
ROW_INFRASTRUCTURE_PIP = [
    "pip", "numpy", "pip", "v1.24.0", "Infrastructure",
    "N/A", "Numerical computing", ""]
ROW_INFRASTRUCTURE_GEM = [
    "Ruby Gem", "bundler", "gem", "system-default (2.3.0)", "Infrastructure",
    "N/A", "System Ruby gem", ""]
ROW_PROTECTED_SAFARI = [
    "GUI Application", "Safari", "Apple", "Apple", "Active",
    "2026-02-01", "Web browser", "100000"]
ROW_BREW_DEPENDENCY = [
    "Homebrew Formula", "openssl", "dependency",
    "dependency (required by: python@3.12, node)", "Active",
    "N/A", "TLS library", ""]
ROW_DORMANT_GUI = [
    "GUI Application", "OldApp", "Manual Install", "", "Dormant",
    "2025-06-01", "Some old app", "100000"]


class TestLoadCandidatesDefault:
    """Default mode: only Dormant items."""

    def test_only_dormant_included(self):
        path = _write_csv([ROW_ACTIVE_GUI, ROW_DORMANT_FORMULA,
                           ROW_OCCASIONAL_GUI, ROW_UNKNOWN_NPM])
        try:
            candidates = load_candidates(path)
            names = [c.name for c in candidates]
            assert "hugo" in names
            assert "Slack" not in names
            assert "Warp" not in names
            assert "eslint" not in names
        finally:
            os.unlink(path)

    def test_include_unknown(self):
        path = _write_csv([ROW_DORMANT_FORMULA, ROW_UNKNOWN_NPM,
                           ROW_ACTIVE_GUI])
        try:
            candidates = load_candidates(path, include_unknown=True)
            names = [c.name for c in candidates]
            assert "hugo" in names
            assert "eslint" in names
            assert "Slack" not in names
        finally:
            os.unlink(path)


class TestLoadCandidatesBrowseMode:
    """--browse mode: all statuses except protected/infrastructure."""

    def test_browse_includes_active_apps(self):
        path = _write_csv([ROW_ACTIVE_GUI, ROW_DORMANT_FORMULA])
        try:
            candidates = load_candidates(path, browse_all=True)
            names = [c.name for c in candidates]
            assert "Slack" in names
            assert "hugo" in names
        finally:
            os.unlink(path)

    def test_browse_includes_occasional_apps(self):
        path = _write_csv([ROW_OCCASIONAL_GUI])
        try:
            candidates = load_candidates(path, browse_all=True)
            names = [c.name for c in candidates]
            assert "Warp" in names
        finally:
            os.unlink(path)

    def test_browse_still_blocks_protected(self):
        path = _write_csv([ROW_PROTECTED_SAFARI, ROW_ACTIVE_GUI])
        try:
            candidates = load_candidates(path, browse_all=True)
            names = [c.name for c in candidates]
            assert "Safari" not in names
            assert "Slack" in names
        finally:
            os.unlink(path)

    def test_browse_still_blocks_infrastructure(self):
        path = _write_csv([ROW_INFRASTRUCTURE_PIP, ROW_INFRASTRUCTURE_GEM,
                           ROW_DORMANT_FORMULA])
        try:
            candidates = load_candidates(path, browse_all=True)
            names = [c.name for c in candidates]
            assert "numpy" not in names
            assert "bundler" not in names
            assert "hugo" in names
        finally:
            os.unlink(path)

    def test_browse_still_blocks_brew_dependencies(self):
        path = _write_csv([ROW_BREW_DEPENDENCY, ROW_DORMANT_FORMULA])
        try:
            candidates = load_candidates(path, browse_all=True)
            names = [c.name for c in candidates]
            assert "openssl" not in names
            assert "hugo" in names
        finally:
            os.unlink(path)

    def test_browse_includes_all_safe_statuses(self):
        path = _write_csv([ROW_ACTIVE_GUI, ROW_OCCASIONAL_GUI,
                           ROW_DORMANT_FORMULA, ROW_UNKNOWN_NPM])
        try:
            candidates = load_candidates(path, browse_all=True)
            names = [c.name for c in candidates]
            assert len(candidates) == 4
            assert "Slack" in names
            assert "Warp" in names
            assert "hugo" in names
            assert "eslint" in names
        finally:
            os.unlink(path)


class TestSortForBrowse:
    def test_dormant_before_active(self):
        path = _write_csv([ROW_ACTIVE_GUI, ROW_DORMANT_FORMULA,
                           ROW_OCCASIONAL_GUI, ROW_UNKNOWN_NPM])
        try:
            candidates = load_candidates(path, browse_all=True)
            sorted_c = sort_for_browse(candidates)
            statuses = [c.status for c in sorted_c]
            assert statuses == ["Dormant", "Unknown", "Occasional", "Active"]
        finally:
            os.unlink(path)

    def test_alphabetical_within_status(self):
        row_a = list(ROW_DORMANT_GUI)
        row_a[1] = "Zebra"
        row_b = list(ROW_DORMANT_GUI)
        row_b[1] = "Alpha"
        path = _write_csv([row_a, row_b])
        try:
            candidates = load_candidates(path, browse_all=True)
            sorted_c = sort_for_browse(candidates)
            names = [c.name for c in sorted_c]
            assert names == ["Alpha", "Zebra"]
        finally:
            os.unlink(path)

    def test_empty_list(self):
        result = sort_for_browse([])
        assert result == []


class TestSelectByNames:
    def test_select_existing(self):
        path = _write_csv([ROW_DORMANT_FORMULA, ROW_DORMANT_GUI])
        try:
            candidates = load_candidates(path, browse_all=True)
            matched, unmatched = select_by_names(
                candidates, {"hugo"})
            assert len(matched) == 1
            assert matched[0].name == "hugo"
            assert unmatched == set()
        finally:
            os.unlink(path)

    def test_select_nonexistent(self):
        path = _write_csv([ROW_DORMANT_FORMULA])
        try:
            candidates = load_candidates(path, browse_all=True)
            matched, unmatched = select_by_names(
                candidates, {"nonexistent"})
            assert len(matched) == 0
            assert "nonexistent" in unmatched
        finally:
            os.unlink(path)
