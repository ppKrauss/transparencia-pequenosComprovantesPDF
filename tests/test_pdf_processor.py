from pathlib import Path

from transparencia_comprovantes.config import load_config
from transparencia_comprovantes.processors.pdf import PdfProcessor, PdfRunOptions


PIX_TEXT = """
Comprovante de Pix
09/07/2026
Valor pago
R$ 12,34
Forma de pagamento
Saldo em conta
Dados do recebedor
Para
MARIA DA SILVA
Informacao para o recebedor
Prestacao de contas
Central de Atendimento Santander
"""


def test_pdf_processor_extracts_pix_row_from_text():
    row, should_stop = PdfProcessor(load_config()).row_from_text(
        1, "comprovante.pdf", "sha1", "2026-07-09", PIX_TEXT
    )
    assert should_stop is False
    assert row[1:3] == ["Pix", "Santander"]
    assert row[6] == "2026-07-09"
    assert row[8] == "R$ 12,34"
    assert row[10] == "MARIA DA SILVA"


def test_unknown_document_returns_err04_and_configured_stop():
    processor = PdfProcessor(load_config(), PdfRunOptions(True, False))
    row, should_stop = processor.row_from_text(1, "x.pdf", "hash", "2026-01-01", "sem padrao")
    assert row[1:3] == ["undefined", "generico"]
    assert row[7] == "err04"
    assert should_stop is True


def test_known_but_unsupported_document_returns_err03():
    text = "Documento de Arrecadacao"
    row, should_stop = PdfProcessor(load_config()).row_from_text(
        1, "x.pdf", "hash", "2026-01-01", text
    )
    assert row[1] == "Outros"
    assert row[7] == "err03"
    assert should_stop is False


def test_text_size_limit_returns_err02_and_stop():
    config = load_config()
    config["settings"]["max_text_chars"] = 3
    processor = PdfProcessor(config, PdfRunOptions(False, True))
    row, should_stop = processor.row_from_text(1, "x.pdf", "hash", "2026-01-01", "texto longo")
    assert row[7] == "err02"
    assert should_stop is True


def test_file_size_limit_returns_err01(tmp_path):
    path = tmp_path / "large.pdf"
    path.write_bytes(b"1234")
    config = load_config()
    config["settings"]["max_bytes"] = 3
    row, should_stop = PdfProcessor(config, PdfRunOptions(False, True)).process_file(path, 1)
    assert row[7] == "err01"
    assert should_stop is True


def test_process_file_reads_metadata_hash_and_text(monkeypatch, tmp_path):
    path = tmp_path / "receipt.pdf"
    path.write_bytes(b"pdf")
    processor = PdfProcessor(load_config())
    monkeypatch.setattr(processor, "extract_text", lambda _: PIX_TEXT)
    row, should_stop = processor.process_file(path, 7)
    assert row[0] == "7"
    assert row[1] == "Pix"
    assert row[3] == "receipt.pdf"
    assert len(row[4]) == 40
    assert should_stop is False


def test_extract_text_joins_pages_and_respects_text_limit(monkeypatch, tmp_path):
    class Page:
        def __init__(self, text):
            self.text = text

        def extract_text(self):
            return self.text

    class Reader:
        def __init__(self, stream):
            self.pages = [Page("abc"), Page(None), Page("def")]

    path = tmp_path / "x.pdf"
    path.write_bytes(b"pdf")
    config = load_config()
    config["settings"]["max_text_chars"] = 4
    processor = PdfProcessor(config)
    monkeypatch.setattr(
        "transparencia_comprovantes.processors.pdf.pypdf.PdfReader", Reader
    )
    assert processor.extract_text(path) == "abc\n\ndef"


def test_process_directory_skips_names_and_stops(monkeypatch, tmp_path):
    for name in ("a.pdf", "b.pdf", "c.pdf"):
        (tmp_path / name).write_bytes(b"pdf")
    processor = PdfProcessor(load_config())
    calls = []

    def fake_process(path: Path, doc_id: int):
        calls.append((path.name, doc_id))
        return [path.name], path.name == "b.pdf"

    monkeypatch.setattr(processor, "process_file", fake_process)
    rows = processor.process_directory(tmp_path, {"a.pdf"})
    assert calls == [("b.pdf", 1)]
    assert rows == [["b.pdf"]]


def test_process_directory_continues_and_increments_ids(monkeypatch, tmp_path):
    for name in ("a.pdf", "b.pdf"):
        (tmp_path / name).write_bytes(b"pdf")
    processor = PdfProcessor(load_config())
    monkeypatch.setattr(
        processor, "process_file", lambda path, doc_id: ([str(doc_id), path.name], False)
    )
    assert processor.process_directory(tmp_path) == [["1", "a.pdf"], ["2", "b.pdf"]]
