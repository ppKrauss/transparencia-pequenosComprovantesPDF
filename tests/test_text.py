import re

from transparencia_comprovantes.utils.text import (
    clean_value,
    escape_separator,
    extract_br_date,
    first_match,
    first_captured_group,
    normalize_text,
)


def test_normalize_text_removes_accents_and_extra_spaces():
    assert normalize_text(" Ação\tde\r\nPagamento  ") == "Acao de\nPagamento"


def test_extract_br_date_returns_iso_date():
    assert extract_br_date("Pago em 09/07/2026") == "2026-07-09"
    assert extract_br_date("31/02/2026") == "31/02/2026"
    assert extract_br_date(None) == ""


def test_first_captured_group_returns_first_non_empty_alternative():
    match = re.search(r"foo:(\d+)|bar:(\w+)", "bar:ABC")
    assert first_captured_group(match) == "ABC"
    assert first_captured_group(None) == ""


def test_clean_and_escape_values():
    assert clean_value("  valor:\n") == "valor"
    assert clean_value(None) == ""
    assert escape_separator("a|b\nc") == "a-b c"


def test_first_match_returns_first_capture_or_empty():
    patterns = [re.compile(r"id=(\d+)"), re.compile(r"codigo=(\d+)")]
    assert first_match(patterns, "codigo=42") == "42"
    assert first_match(patterns, "nada") == ""
