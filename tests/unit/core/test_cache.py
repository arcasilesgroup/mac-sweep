"""Tests for mac_sweep.core.cache."""

from mac_sweep.core.cache import analyze_all, clean_all
from mac_sweep.core.cache_modules import list_modules


class TestAnalyzeAll:
    def test_returns_list(self):
        results = analyze_all()
        assert isinstance(results, list)
        assert len(results) > 0

    def test_all_modules_scanned(self):
        results = analyze_all()
        modules_scanned = {r.module for r in results}
        assert modules_scanned == set(list_modules())

    def test_specific_modules(self):
        results = analyze_all(modules=["npm", "pip"])
        modules_scanned = {r.module for r in results}
        assert modules_scanned == {"npm", "pip"}

    def test_each_result_has_module_and_label(self):
        results = analyze_all()
        for r in results:
            assert r.module
            assert r.label

    def test_unknown_module(self):
        results = analyze_all(modules=["nonexistent_xyz"])
        assert len(results) == 1
        assert results[0].error


class TestCleanAll:
    def test_returns_list(self):
        analyses = analyze_all(modules=["pip"])
        results = clean_all(analyses, execute=False)
        assert isinstance(results, list)

    def test_dryrun_does_not_delete(self):
        analyses = analyze_all(modules=["pip"])
        results = clean_all(analyses, execute=False)
        assert isinstance(results, list)
