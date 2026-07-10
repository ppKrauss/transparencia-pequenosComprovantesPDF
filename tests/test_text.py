import re

from transparencia_comprovantes.text import (
    extract_br_date,
    first_captured_group,
    normalize_text,
)


def test_normalize_text_removes_accents_and_extra_spaces():
    assert normalize_text(" Ação\tde\r\nPagamento  ") == "Acao de\nPagamento"


def test_extract_br_date_returns_iso_date():
    assert extract_br_date("Pago em 09/07/2026") == "2026-07-09"


def test_first_captured_group_returns_first_non_empty_alternative():
    match = re.search(r"foo:(\d+)|bar:(\w+)", "bar:ABC")
    assert first_captured_group(match) == "ABC"
