from pathlib import Path

import pytest

from transparencia_comprovantes.config import (
    compile_entries,
    deep_merge,
    load_config,
    read_yaml_file,
)


def write_data_dir(path: Path, config: str = "settings:\n  csv_separator: '|'\n") -> None:
    path.mkdir(exist_ok=True)
    (path / "config.yml").write_text(config, encoding="utf-8")
    (path / "rules.yml").write_text("pdf: {}\nimages: {}\n", encoding="utf-8")


def test_load_default_config_has_pdf_and_image_sections():
    config = load_config()
    assert "pdf" in config
    assert "images" in config
    assert config["settings"]["csv_separator"] == "|"


def test_load_config_requires_a_directory_with_both_files(tmp_path):
    with pytest.raises(FileNotFoundError, match="Diretorio de dados"):
        load_config(tmp_path / "ausente")

    (tmp_path / "config.yml").write_text("settings: {}", encoding="utf-8")
    with pytest.raises(FileNotFoundError, match="rules.yml"):
        load_config(tmp_path)


def test_load_config_merges_config_and_rules(tmp_path):
    write_data_dir(tmp_path, "settings:\n  csv_separator: '#'\n")
    config = load_config(tmp_path)
    assert config["settings"]["csv_separator"] == "#"
    assert config["pdf"] == {}


def test_environment_selects_default_data_dir(tmp_path, monkeypatch):
    write_data_dir(tmp_path)
    monkeypatch.setenv("COMPROVANTES_DATA_DIR", str(tmp_path))
    assert load_config()["settings"]["csv_separator"] == "|"


def test_yaml_top_level_must_be_an_object(tmp_path):
    path = tmp_path / "invalid.yml"
    path.write_text("- item\n", encoding="utf-8")
    with pytest.raises(ValueError, match="objeto no topo"):
        read_yaml_file(path)


def test_deep_merge_preserves_nested_values_and_replaces_lists():
    merged = deep_merge({"a": {"x": 1, "y": 2}, "items": [1]}, {"a": {"y": 3}, "items": [2]})
    assert merged == {"a": {"x": 1, "y": 3}, "items": [2]}


def test_compile_entries_applies_regex_flags_and_empty_patterns():
    compiled = compile_entries([
        {"label": "Pix", "pattern": "pix", "flags": ["IGNORECASE"]},
        {"label": "vazio", "pattern": ""},
    ])
    assert compiled[0][1].search("PIX")
    assert compiled[1] == ("vazio", None)


def test_compile_entries_rejects_invalid_regex_flag():
    with pytest.raises(ValueError, match="Flag de regex invalida"):
        compile_entries([{"label": "x", "pattern": "x", "flags": ["inexistente"]}])
