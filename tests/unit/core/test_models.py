"""Tests for mac_sweep.core.models."""

from mac_sweep.core.models import (
    AuditedApp,
    AuditedFormula,
    AuditedPackage,
    AuditResult,
    CacheAnalysis,
    CacheItem,
    Category,
    CleanResult,
    CleanupCandidate,
    Diagnostic,
    RemovalMethod,
    Source,
    Status,
)


class TestStatusEnum:
    def test_values(self):
        assert Status.ACTIVE.value == "Active"
        assert Status.OCCASIONAL.value == "Occasional"
        assert Status.DORMANT.value == "Dormant"
        assert Status.UNKNOWN.value == "Unknown"
        assert Status.INFRASTRUCTURE.value == "Infrastructure"

    def test_from_string(self):
        assert Status("Active") == Status.ACTIVE
        assert Status("Dormant") == Status.DORMANT


class TestCategoryEnum:
    def test_values(self):
        assert Category.GUI_APPLICATION.value == "GUI Application"
        assert Category.HOMEBREW_FORMULA.value == "Homebrew Formula"
        assert Category.NPM_GLOBAL.value == "npm Global"


class TestSourceEnum:
    def test_values(self):
        assert Source.HOMEBREW_CASK.value == "Homebrew Cask"
        assert Source.APP_STORE.value == "App Store"


class TestRemovalMethodEnum:
    def test_values(self):
        assert RemovalMethod.BREW_CASK.value == "brew_cask"
        assert RemovalMethod.GUI_TRASH.value == "gui_trash"


class TestAuditedApp:
    def test_frozen(self):
        app = AuditedApp(
            name="Slack", source="Manual Install", detail="",
            status=Status.ACTIVE, last_used="2026-02-01",
        )
        assert app.name == "Slack"

    def test_hashable(self):
        app = AuditedApp(
            name="Slack", source="Manual Install", detail="",
            status=Status.ACTIVE, last_used="2026-02-01",
        )
        # Frozen dataclasses are hashable
        assert hash(app) is not None

    def test_equality(self):
        a = AuditedApp(
            name="Slack", source="Manual Install", detail="",
            status=Status.ACTIVE, last_used="2026-02-01",
        )
        b = AuditedApp(
            name="Slack", source="Manual Install", detail="",
            status=Status.ACTIVE, last_used="2026-02-01",
        )
        assert a == b


class TestCleanupCandidate:
    def test_display_cmd_auto_generated(self):
        c = CleanupCandidate(
            name="hugo", category="Homebrew Formula",
            description="", status="Dormant",
            removal_method="brew_formula",
            removal_cmd=("brew", "uninstall", "hugo"),
        )
        assert c.display_cmd == "brew uninstall hugo"

    def test_display_cmd_explicit(self):
        c = CleanupCandidate(
            name="OldApp", category="GUI Application",
            description="", status="Dormant",
            removal_method="gui_trash",
            display_cmd="Move to Trash via Finder",
        )
        assert c.display_cmd == "Move to Trash via Finder"

    def test_frozen(self):
        c = CleanupCandidate(
            name="hugo", category="Homebrew Formula",
            description="", status="Dormant",
            removal_method="brew_formula",
        )
        assert hash(c) is not None


class TestAuditResult:
    def test_default_empty(self):
        result = AuditResult()
        assert result.apps == ()
        assert result.formulas == ()
        assert result.npm_packages == ()

    def test_with_data(self):
        app = AuditedApp(
            name="Slack", source="Manual Install", detail="",
            status=Status.ACTIVE, last_used="2026-02-01",
        )
        result = AuditResult(apps=(app,))
        assert len(result.apps) == 1


class TestDiagnostic:
    def test_creation(self):
        d = Diagnostic(
            check="disk_pressure", status="ok",
            message="Disk space OK",
        )
        assert d.check == "disk_pressure"
        assert d.details == ()

    def test_with_details(self):
        d = Diagnostic(
            check="broken_symlinks", status="warning",
            message="3 broken", details=("a", "b", "c"),
        )
        assert len(d.details) == 3
