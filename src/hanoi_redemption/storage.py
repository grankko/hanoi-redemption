"""Atomic, inspectable JSON result storage."""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import UTC
from pathlib import Path

from .models import BenchmarkResult
from .protocols import protocol_label


@dataclass(frozen=True, slots=True)
class ResultEntry:
    path: Path
    result: BenchmarkResult


class ResultStore:
    def __init__(self, root: Path | str = "results"):
        self.root = Path(root)
        self.runs_dir = self.root / "runs"

    def save(self, result: BenchmarkResult) -> Path:
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        path = self.runs_dir / result_filename(result)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temporary, path)
        return path

    def load_all(self) -> list[BenchmarkResult]:
        return [entry.result for entry in self.entries()]

    def entries(self) -> list[ResultEntry]:
        if not self.runs_dir.exists():
            return []
        entries: list[ResultEntry] = []
        for path in self.runs_dir.glob("*.json"):
            try:
                entries.append(
                    ResultEntry(
                        path=path,
                        result=BenchmarkResult.model_validate_json(
                            path.read_text(encoding="utf-8")
                        ),
                    )
                )
            except (OSError, ValueError, json.JSONDecodeError):
                continue
        return sorted(entries, key=lambda entry: entry.result.created_at, reverse=True)

    def resolve(self, reference: str) -> BenchmarkResult:
        direct = Path(reference)
        if direct.is_file():
            return BenchmarkResult.model_validate_json(direct.read_text(encoding="utf-8"))

        stored_path = self.runs_dir / reference
        if stored_path.is_file():
            return BenchmarkResult.model_validate_json(stored_path.read_text(encoding="utf-8"))

        matches = [
            entry
            for entry in self.entries()
            if entry.result.run_id.startswith(reference)
            or entry.path.name.startswith(reference)
        ]
        if not matches:
            raise FileNotFoundError(f"no stored run matches {reference!r}")
        if len(matches) > 1:
            raise ValueError(f"run prefix {reference!r} matches {len(matches)} results")
        return matches[0].result


def result_filename(result: BenchmarkResult) -> str:
    created_at = result.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=UTC)
    timestamp = created_at.astimezone(UTC).strftime("%Y-%m-%d_%H-%M-%SZ")
    model = _safe_segment(result.config.model)
    reasoning = _safe_segment(result.config.reasoning_effort)
    protocol = _safe_segment(protocol_label(result.config.protocol).split()[0])
    status = _safe_segment(result.validation.status)
    return (
        f"{timestamp}_{model}_{reasoning}_{protocol}_{result.config.disks}d_"
        f"t{result.config.trial}_{status}_{result.run_id[:10]}.json"
    )


def _safe_segment(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-._")
    return (sanitized or "unknown")[:60]
