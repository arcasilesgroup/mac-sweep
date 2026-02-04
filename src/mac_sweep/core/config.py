"""Configuration management for mac-sweep."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


# ── Named constants ──

DEFAULT_ACTIVE_DAYS = 7
DEFAULT_OCCASIONAL_DAYS = 30
DEFAULT_MIN_CACHE_AGE_DAYS = 7

LLM_TIMEOUT = 30
REMOVAL_TIMEOUT = 120
PROCESS_CHECK_TIMEOUT = 5
OSASCRIPT_TIMEOUT = 30

CONFIG_DIR = os.path.expanduser("~/.config/mac-sweep")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config")
AUDIT_LOG_FILE = os.path.join(CONFIG_DIR, "audit.log")


@dataclass
class SweepConfig:
    """Central configuration for mac-sweep."""

    active_days: int = DEFAULT_ACTIVE_DAYS
    occasional_days: int = DEFAULT_OCCASIONAL_DAYS
    min_cache_age_days: int = DEFAULT_MIN_CACHE_AGE_DAYS
    llm_timeout: int = LLM_TIMEOUT
    removal_timeout: int = REMOVAL_TIMEOUT
    anthropic_api_key: str = ""
    openai_api_key: str = ""
    extra_protected_apps: set[str] = field(default_factory=set)


def _read_config_file(path: str) -> dict[str, str]:
    """Read a KEY=value config file."""
    result: dict[str, str] = {}
    if not os.path.exists(path):
        return result
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                result[k.strip()] = v.strip()
    except OSError:
        pass
    return result


def _try_load_toml(path: str) -> dict[str, str]:
    """Try loading a TOML config file (Python 3.11+)."""
    try:
        import tomllib  # type: ignore[import-not-found]
    except ImportError:
        return {}
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "rb") as f:
            data = tomllib.load(f)
        result: dict[str, str] = {}
        for k, v in data.items():
            result[k] = str(v)
        return result
    except Exception:
        return {}


def load_config() -> SweepConfig:
    """Load configuration from defaults, config files, and env vars.

    Priority: defaults < config.toml < config (key=value) < env vars.
    """
    cfg = SweepConfig()

    # Try TOML first (Python 3.11+)
    toml_path = os.path.join(CONFIG_DIR, "config.toml")
    values = _try_load_toml(toml_path)

    # Then key=value fallback
    kv_values = _read_config_file(CONFIG_FILE)
    values.update(kv_values)

    # Apply config file values
    if "active_days" in values:
        try:
            cfg.active_days = int(values["active_days"])
        except ValueError:
            pass
    if "occasional_days" in values:
        try:
            cfg.occasional_days = int(values["occasional_days"])
        except ValueError:
            pass
    if "min_cache_age_days" in values:
        try:
            cfg.min_cache_age_days = int(values["min_cache_age_days"])
        except ValueError:
            pass
    if "ANTHROPIC_API_KEY" in values:
        cfg.anthropic_api_key = values["ANTHROPIC_API_KEY"]
    if "OPENAI_API_KEY" in values:
        cfg.openai_api_key = values["OPENAI_API_KEY"]
    if "extra_protected_apps" in values:
        cfg.extra_protected_apps = {
            a.strip()
            for a in values["extra_protected_apps"].split(",")
            if a.strip()
        }

    # Env vars override everything
    env_anthropic = os.environ.get("ANTHROPIC_API_KEY", "")
    if env_anthropic:
        cfg.anthropic_api_key = env_anthropic
    env_openai = os.environ.get("OPENAI_API_KEY", "")
    if env_openai:
        cfg.openai_api_key = env_openai

    return cfg
