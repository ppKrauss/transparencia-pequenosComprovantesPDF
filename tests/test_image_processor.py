from transparencia_comprovantes.config import load_config
from transparencia_comprovantes.images import ImageProcessor


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
