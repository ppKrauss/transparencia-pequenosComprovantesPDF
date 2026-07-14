from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Any

import yaml


CONFIG_FILE = "config.yml"
RULES_FILE = "rules.yml"
DATA_DIR_ENV = "COMPROVANTES_DATA_DIR"


def read_yaml_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Arquivo YAML deve conter um objeto no topo: {path}")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def default_data_dir() -> Path:
    """Locate the project data directory in source and installed layouts."""
    if configured := os.environ.get(DATA_DIR_ENV):
        return Path(configured)

    source_data = Path(__file__).resolve().parents[2] / "data"
    if source_data.is_dir():
        return source_data

    return Path(sys.prefix) / "share" / "transparencia-comprovantes" / "data"


def load_config(data_dir: str | Path | None = None) -> dict[str, Any]:
    """Load the required ``config.yml`` and ``rules.yml`` files from one directory."""
    directory = Path(data_dir) if data_dir is not None else default_data_dir()
    if not directory.is_dir():
        raise FileNotFoundError(f"Diretorio de dados nao encontrado: {directory}")

    config_path = directory / CONFIG_FILE
    rules_path = directory / RULES_FILE
    missing = [path.name for path in (config_path, rules_path) if not path.is_file()]
    if missing:
        raise FileNotFoundError(
            f"Arquivo(s) obrigatorio(s) ausente(s) em {directory}: {', '.join(missing)}"
        )
    return deep_merge(read_yaml_file(config_path), read_yaml_file(rules_path))


def regex_flags(flag_names: list[str] | None) -> int:
    flags = 0
    for name in flag_names or []:
        try:
            flags |= getattr(re, name.upper())
        except AttributeError as exc:
            raise ValueError(f"Flag de regex invalida: {name}") from exc
    return flags


def compile_entries(entries: list[dict[str, Any]]) -> list[tuple[str, re.Pattern[str] | None]]:
    compiled: list[tuple[str, re.Pattern[str] | None]] = []
    for entry in entries or []:
        label = str(entry["label"])
        pattern = entry.get("pattern") or ""
        flags = regex_flags(entry.get("flags"))
        compiled.append((label, re.compile(pattern, flags) if pattern else None))
    return compiled


def compile_field_groups(
    groups: dict[str, list[dict[str, Any]]]
) -> dict[str, list[tuple[str, re.Pattern[str] | None]]]:
    return {name: compile_entries(entries) for name, entries in (groups or {}).items()}
