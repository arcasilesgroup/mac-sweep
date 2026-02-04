"""Shared fixtures for mac-sweep tests."""

import csv
import os
import tempfile

import pytest


@pytest.fixture
def sample_audit_dir():
    """Create a temporary directory with sample audit data files."""
    with tempfile.TemporaryDirectory() as td:
        # app_paths.txt
        with open(os.path.join(td, "app_paths.txt"), "w") as f:
            f.write("/Applications/Slack.app\n")
            f.write("/Applications/OldApp.app\n")

        # ps_aux.txt
        with open(os.path.join(td, "ps_aux.txt"), "w") as f:
            f.write("user  1234  /Applications/Slack.app/Contents/MacOS/Slack\n")

        # sysprof.json
        with open(os.path.join(td, "sysprof.json"), "w") as f:
            f.write('{"SPApplicationsDataType": []}')

        # brew_info.json
        with open(os.path.join(td, "brew_info.json"), "w") as f:
            f.write('{"formulae": [], "casks": []}')

        # Empty files
        for name in (
            "appstore_apps.txt", "launch_agents_content.txt",
            "mdls_results.txt", "app_sizes.txt", "brew_leaves.txt",
            "brew_formulas.txt", "brew_deps.txt",
            "npm_global.json", "npm_prefix.txt",
            "pipx_list.txt", "pip_list.json", "pip_descriptions.json",
            "gem_list.txt", "gem_userdir.txt",
        ):
            path = os.path.join(td, name)
            if name.endswith(".json"):
                if "list" in name:
                    with open(path, "w") as f:
                        f.write("[]")
                else:
                    with open(path, "w") as f:
                        f.write("{}")
            else:
                with open(path, "w") as f:
                    pass

        yield td


@pytest.fixture
def sample_csv():
    """Create a temporary CSV with sample audit data."""
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".csv", delete=False, newline="",
    )
    writer = csv.writer(tmp)
    writer.writerow(["Category", "Name", "Source", "Detail", "Status",
                     "Last Used", "Description", "Size"])
    writer.writerow(["GUI Application", "Slack", "Manual Install", "",
                     "Active", "2026-02-01", "Team communication", "500000"])
    writer.writerow(["GUI Application", "OldApp", "Manual Install", "",
                     "Dormant", "2025-06-01", "Some old app", "100000"])
    writer.writerow(["Homebrew Formula", "hugo", "explicit",
                     "explicitly installed", "Dormant", "N/A",
                     "Static site generator", ""])
    writer.writerow(["npm Global", "eslint", "npm", "v8.56.0",
                     "Unknown", "N/A", "JavaScript linter", ""])
    writer.writerow(["pip", "numpy", "pip", "v1.24.0",
                     "Infrastructure", "N/A", "Numerical computing", ""])
    tmp.close()
    yield tmp.name
    os.unlink(tmp.name)
