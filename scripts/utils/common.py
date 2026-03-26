from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[2]


def resolve_repo_root(root: str | None = None) -> Path:
    return Path(root).resolve() if root else REPO_ROOT


def ensure_parent(path: str | Path) -> Path:
    resolved = Path(path)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def load_json_lines(path: str | Path) -> list[dict]:
    file_path = Path(path)
    records: list[dict] = []

    with file_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped:
                continue
            try:
                records.append(json.loads(stripped))
            except json.JSONDecodeError:
                records = []
                break

    if records:
        return records

    with file_path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if isinstance(data, list):
        return data

    raise ValueError(f"Expected a JSON array or JSONL file: {file_path}")


def write_json_lines(records: Iterable[dict], path: str | Path) -> Path:
    output_path = ensure_parent(path)
    with output_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    return output_path


def load_json_object(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return data
