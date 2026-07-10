from __future__ import annotations

import re
from importlib.resources import files
from pathlib import Path
from typing import Any

import yaml


DEFAULT_CONFIG_RESOURCE = "config.yml"
DEFAULT_RULES_RESOURCE = "rules.yml"


def read_yaml_file(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Arquivo YAML deve conter um objeto no topo: {path}")
    return data


def read_yaml_resource(resource_name: str) -> dict[str, Any]:
    resource = files("transparencia_comprovantes.patterns").joinpath(resource_name)
    with resource.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if not isinstance(data, dict):
        raise ValueError(f"Recurso YAML deve conter um objeto no topo: {resource_name}")
    return data


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(path: str | Path | None = None) -> dict[str, Any]:
    """Load settings and extraction rules from YAML.

    Defaults are split into config.yml and rules.yml. For compatibility, a custom
    path can still point to a single monolithic YAML containing settings and rules.
    If the custom file contains only rules, default settings are kept.
    """
    default_config = read_yaml_resource(DEFAULT_CONFIG_RESOURCE)

    if not path:
        return deep_merge(default_config, read_yaml_resource(DEFAULT_RULES_RESOURCE))

    custom_path = Path(path)
    if custom_path.is_dir():
        config_path = custom_path / DEFAULT_CONFIG_RESOURCE
        rules_path = custom_path / DEFAULT_RULES_RESOURCE
        config = (
            deep_merge(default_config, read_yaml_file(config_path))
            if config_path.exists()
            else default_config
        )
        if not rules_path.exists():
            raise FileNotFoundError(f"Arquivo de regras nao encontrado: {rules_path}")
        return deep_merge(config, read_yaml_file(rules_path))

    custom_data = read_yaml_file(custom_path)
    return deep_merge(default_config, custom_data)


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
