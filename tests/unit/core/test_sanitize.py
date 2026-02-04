"""Tests for mac_sweep.core.sanitize."""

from mac_sweep.core.sanitize import (
    applescript_escape,
    cmd_to_display,
    cmd_to_shell,
    safe_removal_cmd,
    validate_app_path,
    validate_cask_token,
    validate_package_name,
)


class TestValidateCaskToken:
    def test_valid_tokens(self):
        assert validate_cask_token("warp")
        assert validate_cask_token("alt-tab")
        assert validate_cask_token("iterm2")
        assert validate_cask_token("visual-studio-code")
        assert validate_cask_token("1password")

    def test_invalid_tokens(self):
        assert not validate_cask_token("")
        assert not validate_cask_token("warp; rm -rf /")
        assert not validate_cask_token("wa rp")
        assert not validate_cask_token("$(whoami)")
        assert not validate_cask_token("Warp")
        assert not validate_cask_token("-leading-dash")


class TestValidatePackageName:
    def test_valid_names(self):
        assert validate_package_name("express")
        assert validate_package_name("@angular/cli")
        assert validate_package_name("python3.12")
        assert validate_package_name("my_package")
        assert validate_package_name("node-gyp")
        assert validate_package_name("icu4c@78")

    def test_invalid_names(self):
        assert not validate_package_name("")
        assert not validate_package_name("; rm -rf /")
        assert not validate_package_name("$(whoami)")
        assert not validate_package_name("-leading-dash")
        assert not validate_package_name(" spaces ")


class TestValidateAppPath:
    def test_valid_paths(self):
        assert validate_app_path("/Applications/Warp.app")
        assert validate_app_path("/Applications/Utilities/Terminal.app")

    def test_invalid_paths(self):
        assert not validate_app_path("/tmp/evil.app")
        assert not validate_app_path("/Users/me/evil.app")
        assert not validate_app_path("/Applications/../etc/passwd")


class TestApplescriptEscape:
    def test_no_escaping_needed(self):
        assert applescript_escape("/Applications/Warp.app") == "/Applications/Warp.app"

    def test_quotes_escaped(self):
        assert applescript_escape('path"with"quotes') == 'path\\"with\\"quotes'

    def test_backslashes_escaped(self):
        assert applescript_escape("path\\back") == "path\\\\back"

    def test_combined(self):
        result = applescript_escape('a"b\\c')
        assert result == 'a\\"b\\\\c'


class TestSafeRemovalCmd:
    def test_brew_cask(self):
        cmd, undo = safe_removal_cmd("brew_cask", "warp")
        assert cmd == ["brew", "uninstall", "--cask", "warp"]
        assert undo == ["brew", "install", "--cask", "warp"]

    def test_brew_formula(self):
        cmd, undo = safe_removal_cmd("brew_formula", "hugo")
        assert cmd == ["brew", "uninstall", "hugo"]
        assert undo == ["brew", "install", "hugo"]

    def test_npm(self):
        cmd, undo = safe_removal_cmd("npm", "express")
        assert cmd == ["npm", "uninstall", "-g", "express"]
        assert undo == ["npm", "install", "-g", "express"]

    def test_pipx(self):
        cmd, undo = safe_removal_cmd("pipx", "black")
        assert cmd == ["pipx", "uninstall", "black"]
        assert undo == ["pipx", "install", "black"]

    def test_invalid_cask_token_rejected(self):
        cmd, undo = safe_removal_cmd("brew_cask", "$(evil)")
        assert cmd is None
        assert undo is None

    def test_invalid_package_name_rejected(self):
        cmd, undo = safe_removal_cmd("brew_formula", "; rm -rf /")
        assert cmd is None
        assert undo is None

    def test_unknown_method(self):
        cmd, undo = safe_removal_cmd("unknown", "anything")
        assert cmd is None
        assert undo is None


class TestCmdToDisplay:
    def test_simple_command(self):
        result = cmd_to_display(["brew", "uninstall", "hugo"])
        assert result == "brew uninstall hugo"

    def test_command_with_special_chars(self):
        result = cmd_to_display(["brew", "uninstall", "--cask", "my-app"])
        assert "my-app" in result


class TestCmdToShell:
    def test_simple_command(self):
        result = cmd_to_shell(["brew", "install", "hugo"])
        assert result == "brew install hugo"
