"""CLI command: config — view and modify configuration."""

from __future__ import annotations

import argparse
import json
import os
import sys

from mac_sweep.core.config import CONFIG_DIR, CONFIG_FILE, load_config


def register(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the config subcommand."""
    p = subparsers.add_parser(
        "config",
        help="View and modify configuration",
    )
    config_sub = p.add_subparsers(dest="config_action")

    config_sub.add_parser("show", help="Show current configuration")
    config_sub.add_parser("path", help="Show config file path")

    set_p = config_sub.add_parser("set", help="Set a config value")
    set_p.add_argument("key", help="Configuration key")
    set_p.add_argument("value", help="Configuration value")

    p.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the config command."""
    action = getattr(args, "config_action", None)

    if action == "show":
        return _show_config()
    elif action == "path":
        print(CONFIG_FILE)
        return 0
    elif action == "set":
        return _set_config(args.key, args.value)
    else:
        return _show_config()


def _show_config() -> int:
    """Show current configuration."""
    cfg = load_config()

    print("mac-sweep configuration")
    print("=" * 40)
    print(f"  active_days:        {cfg.active_days}")
    print(f"  occasional_days:    {cfg.occasional_days}")
    print(f"  min_cache_age_days: {cfg.min_cache_age_days}")
    print(f"  llm_timeout:        {cfg.llm_timeout}")
    print(f"  removal_timeout:    {cfg.removal_timeout}")
    print(f"  anthropic_api_key:  {'***set***' if cfg.anthropic_api_key else '(not set)'}")
    print(f"  openai_api_key:     {'***set***' if cfg.openai_api_key else '(not set)'}")
    if cfg.extra_protected_apps:
        print(f"  extra_protected:    {', '.join(sorted(cfg.extra_protected_apps))}")
    print(f"\n  Config file: {CONFIG_FILE}")
    return 0


def _set_config(key: str, value: str) -> int:
    """Set a config value."""
    os.makedirs(CONFIG_DIR, exist_ok=True)

    # Read existing config
    lines: list[str] = []
    found = False
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            for line in f:
                stripped = line.strip()
                if stripped.startswith("#") or "=" not in stripped:
                    lines.append(line.rstrip("\n"))
                    continue
                k, _ = stripped.split("=", 1)
                if k.strip() == key:
                    lines.append(f"{key}={value}")
                    found = True
                else:
                    lines.append(line.rstrip("\n"))

    if not found:
        lines.append(f"{key}={value}")

    with open(CONFIG_FILE, "w") as f:
        f.write("\n".join(lines) + "\n")

    # Set restrictive permissions
    os.chmod(CONFIG_FILE, 0o600)

    print(f"Set {key} in {CONFIG_FILE}", file=sys.stderr)
    return 0
