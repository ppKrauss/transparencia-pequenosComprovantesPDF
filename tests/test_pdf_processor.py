from transparencia_comprovantes.config import load_config
from transparencia_comprovantes.pdf import PdfProcessor


def test_pdf_processor_extracts_pix_row_from_text():
    processor = PdfProcessor(load_config())
    text = """
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

    row, should_stop = processor.row_from_text(
        1,
        "comprovante.pdf",
        "sha1",
        "2026-07-09",
        text,
    )

    assert should_stop is False
    assert row[1] == "Pix"
    assert row[2] == "Santander"
    assert row[6] == "2026-07-09"
    assert row[8] == "R$ 12,34"
    assert row[10] == "MARIA DA SILVA"
