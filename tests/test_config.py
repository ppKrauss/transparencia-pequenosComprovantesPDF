from transparencia_comprovantes.config import compile_entries, load_config


def test_load_default_config_has_pdf_and_image_sections():
    config = load_config()

    assert "pdf" in config
    assert "images" in config
    assert config["settings"]["csv_separator"] == "|"


def test_load_rules_only_file_keeps_default_settings(tmp_path):
    rules_path = tmp_path / "rules.yml"
    rules_path.write_text(
        """
pdf:
  document_patterns: []
images:
  marker_terms: []
""",
        encoding="utf-8",
    )

    config = load_config(rules_path)

    assert config["settings"]["csv_separator"] == "|"
    assert config["pdf"]["document_patterns"] == []
    assert config["images"]["marker_terms"] == []


def test_load_config_directory_uses_config_and_rules_files(tmp_path):
    (tmp_path / "config.yml").write_text(
        """
settings:
  csv_separator: "#"
""",
        encoding="utf-8",
    )
    (tmp_path / "rules.yml").write_text(
        """
pdf:
  document_patterns: []
images:
  marker_terms: []
""",
        encoding="utf-8",
    )

    config = load_config(tmp_path)

    assert config["settings"]["csv_separator"] == "#"
    assert config["settings"]["pdf_csv_header"][0] == "ID"
    assert config["pdf"]["document_patterns"] == []


def test_compile_entries_applies_regex_flags():
    entries = [{"label": "Pix", "pattern": "pix", "flags": ["IGNORECASE"]}]

    compiled = compile_entries(entries)

    assert compiled[0][0] == "Pix"
    assert compiled[0][1].search("PIX")
