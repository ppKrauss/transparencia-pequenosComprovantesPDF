from transparencia_comprovantes.config import compile_entries, load_config


def test_load_default_config_has_pdf_and_image_sections():
    config = load_config()

    assert "pdf" in config
    assert "images" in config
    assert config["settings"]["csv_separator"] == "|"


def test_compile_entries_applies_regex_flags():
    entries = [{"label": "Pix", "pattern": "pix", "flags": ["IGNORECASE"]}]

    compiled = compile_entries(entries)

    assert compiled[0][0] == "Pix"
    assert compiled[0][1].search("PIX")
