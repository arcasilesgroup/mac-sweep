"""Docker cache module."""

from __future__ import annotations

import shutil
import subprocess

from mac_sweep.core.models import CacheAnalysis, CacheItem, CleanResult


def parse_docker_size(s: str) -> int:
    """Parse Docker size strings like '2.5GB', '128MB', '0B'."""
    s = s.strip().upper()
    # Remove parenthesized percentage like "(50%)"
    if "(" in s:
        s = s[:s.index("(")].strip()
    multipliers = {
        "B": 1, "KB": 1024, "MB": 1024**2,
        "GB": 1024**3, "TB": 1024**4,
    }
    for suffix, mult in sorted(
        multipliers.items(), key=lambda x: -len(x[0])
    ):
        if s.endswith(suffix):
            try:
                return int(float(s[:-len(suffix)].strip()) * mult)
            except ValueError:
                return 0
    return 0


class DockerCache:
    """Analyze and clean Docker/OrbStack caches."""

    @property
    def name(self) -> str:
        return "docker"

    @property
    def label(self) -> str:
        return "Docker / OrbStack"

    def analyze(self) -> CacheAnalysis:
        has_docker = shutil.which("docker") is not None
        if not has_docker:
            return CacheAnalysis(module=self.name, label=self.label)

        total = 0
        items: list[CacheItem] = []
        try:
            result = subprocess.run(
                ["docker", "system", "df", "--format",
                 "{{.Type}}\t{{.Size}}\t{{.Reclaimable}}"],
                capture_output=True, text=True, timeout=15,
            )
            if result.returncode != 0:
                return CacheAnalysis(
                    module=self.name, label=self.label,
                    error=result.stderr.strip(),
                )
            for line in result.stdout.strip().splitlines():
                parts = line.split("\t")
                if len(parts) >= 3:
                    reclaimable_str = parts[2].strip()
                    reclaimable_bytes = parse_docker_size(reclaimable_str)
                    items.append(CacheItem(
                        path=f"docker:{parts[0].strip()}",
                        size_bytes=reclaimable_bytes,
                    ))
                    total += reclaimable_bytes
        except Exception as e:
            return CacheAnalysis(
                module=self.name, label=self.label, error=str(e),
            )

        return CacheAnalysis(
            module=self.name, label=self.label, available=True,
            total_bytes=total, items=items,
        )

    def clean(
        self,
        analysis: CacheAnalysis,
        min_age_days: int = 7,
        execute: bool = False,
    ) -> CleanResult:
        result = CleanResult(module=self.name, label=analysis.label)
        result.freed_bytes = analysis.total_bytes
        result.items_removed = len(analysis.items)

        if execute:
            try:
                proc = subprocess.run(
                    ["docker", "system", "prune", "-f"],
                    capture_output=True, text=True, timeout=120,
                )
                if proc.returncode != 0:
                    result.errors.append(proc.stderr.strip())
            except Exception as e:
                result.errors.append(str(e))

        return result
