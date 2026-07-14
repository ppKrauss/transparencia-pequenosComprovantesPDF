import zipfile

import pytest

from transparencia_comprovantes.config import load_config
from transparencia_comprovantes.processors.images import (
    ImageProcessor,
    image_files_from_input,
)


def test_image_processor_extracts_santander_text_row():
    processor = ImageProcessor(load_config())
    text = """
Santander
Comprovante PIX
Valor: R$ 99,90
Autenticacao bancaria: ABCDEFGHIJ12345
Data da Transacao: 09/07/2026 10:11:12
Nome Destino: JOAO TESTE
CPF/CNPJ: 123.456.789-00
"""
    row = processor.row_from_text("foto.png", text)
    assert row["categoria"] == "comprovante_bancario"
    assert row["tipo_comprovante"] == "PIX"
    assert row["emissor"] == "Santander"
    assert row["valor"] == "R$ 99,90"
    assert row["codigo_transacao"] == "ABCDEFGHIJ12345"


@pytest.mark.parametrize(
    ("text", "categoria"),
    [
        ("curto", "ocr_falhou"),
        ("texto longo sem qualquer marcador bancario conhecido aqui", "nao_bancario_ou_desconhecido"),
        ("Santander texto longo sem marcador bancario reconhecido aqui", "desconhecido"),
    ],
)
def test_image_classification_failure_scenarios(text, categoria):
    row = ImageProcessor(load_config()).row_from_text("foto.png", text)
    assert row["categoria"] == categoria
    assert row["observacoes"]


def test_probable_receipt_reports_missing_transaction_code():
    row = ImageProcessor(load_config()).row_from_text(
        "foto.png", "Comprovante PIX com dados suficientes e Valor: R$ 10,00"
    )
    assert "sem codigo de transacao" in row["observacoes"]


def test_probable_receipt_reports_missing_value_after_transaction_code():
    text = "Comprovante PIX com Autenticacao: ABCDEFGHIJ12345 e outros dados suficientes"
    row = ImageProcessor(load_config()).row_from_text("foto.png", text)
    assert "sem valor" in row["observacoes"]


def test_marker_without_specific_type_uses_generic_receipt_type():
    processor = ImageProcessor(load_config())
    assert processor.detect_tipo("comprovante bancario sem modalidade") == "comprovante_bancario"


def test_process_file_converts_ocr_exception_to_error_row(monkeypatch, tmp_path):
    image = tmp_path / "foto.png"
    image.write_bytes(b"invalid")
    processor = ImageProcessor(load_config())
    monkeypatch.setattr(processor, "ocr_image", lambda _: (_ for _ in ()).throw(RuntimeError("falhou")))
    row = processor.process_file(image)
    assert row["categoria"] == "erro"
    assert row["observacoes"] == "Erro: falhou"


def test_ocr_image_preprocesses_resizes_and_normalizes(monkeypatch, tmp_path):
    class FakeImage:
        width = 500
        height = 200

        def convert(self, mode):
            assert mode == "RGB"
            return self

        def filter(self, image_filter):
            return self

        def resize(self, size):
            assert size == (1000, 400)
            return self

    fake_image = FakeImage()
    monkeypatch.setattr("PIL.Image.open", lambda path: fake_image)
    monkeypatch.setattr("PIL.ImageOps.grayscale", lambda image: image)
    monkeypatch.setattr("PIL.ImageOps.autocontrast", lambda image: image)
    monkeypatch.setattr(
        "pytesseract.image_to_string",
        lambda image, lang, config: " Ação   PIX ",
    )
    assert ImageProcessor(load_config()).ocr_image(tmp_path / "x.png") == "Acao PIX"


def test_process_files_runs_every_input(monkeypatch, tmp_path):
    files = [tmp_path / "a.png", tmp_path / "b.png"]
    processor = ImageProcessor(load_config())
    monkeypatch.setattr(processor, "process_file", lambda path: {"arquivo": path.name})
    assert processor.process_files(files) == [{"arquivo": "a.png"}, {"arquivo": "b.png"}]


def test_image_input_accepts_directory_single_file_and_zip(tmp_path):
    image = tmp_path / "a.png"
    ignored = tmp_path / "a.txt"
    image.write_bytes(b"img")
    ignored.write_text("x", encoding="utf-8")
    files, cleanup = image_files_from_input(tmp_path)
    assert files == [image]
    assert cleanup is None

    files, cleanup = image_files_from_input(image)
    assert files == [image]
    assert cleanup is None

    archive = tmp_path / "images.zip"
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("nested/b.jpg", b"img")
    files, cleanup = image_files_from_input(archive)
    try:
        assert [path.name for path in files] == ["b.jpg"]
    finally:
        cleanup.cleanup()


def test_image_input_rejects_unknown_input(tmp_path):
    path = tmp_path / "input.txt"
    path.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="Entrada nao reconhecida"):
        image_files_from_input(path)
