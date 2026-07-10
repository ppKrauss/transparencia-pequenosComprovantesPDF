from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml


DEFAULT_PATTERN_RESOURCE = "default.yml"


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load extraction rules from YAML."""
    if path:
        with Path(path).open("r", encoding="utf-8") as stream:
            config = yaml.safe_load(stream)
    else:
        resource = files("transparencia_comprovantes.patterns").joinpath(
            DEFAULT_PATTERN_RESOURCE
        )
        with resource.open("r", encoding="utf-8") as stream:
            config = yaml.safe_load(stream)

    if not isinstance(config, dict):
        raise ValueError("Arquivo de padroes YAML deve conter um objeto no topo.")
    return config


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
