"""File I/O utilities: cache checking, JSON/CSV read-write, artifact paths."""

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_RAW = ROOT / "data" / "raw"
DATA_INTERIM = ROOT / "data" / "interim"
DATA_PROCESSED = ROOT / "data" / "processed"
DATA_OUTPUTS = ROOT / "data" / "outputs"


def cache_path(subdir: str, filename: str) -> Path:
    p = DATA_RAW / subdir
    p.mkdir(parents=True, exist_ok=True)
    return p / filename


def interim_path(subdir: str, filename: str) -> Path:
    p = DATA_INTERIM / subdir
    p.mkdir(parents=True, exist_ok=True)
    return p / filename


def processed_path(filename: str) -> Path:
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    return DATA_PROCESSED / filename


def outputs_path(filename: str) -> Path:
    DATA_OUTPUTS.mkdir(parents=True, exist_ok=True)
    return DATA_OUTPUTS / filename


def load_json(path: Path) -> dict | list | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(data: dict | list, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_text(path: Path) -> str | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def save_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def is_cached(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0
