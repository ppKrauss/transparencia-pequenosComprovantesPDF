import csv
import io

import pandas as pd

from transparencia_comprovantes.output import write_image_outputs, write_pdf_xlsx, write_pipe_csv


def test_write_pipe_csv_to_file(tmp_path):
    output = tmp_path / "out.csv"
    write_pipe_csv(["a", "b"], [["1", "2"]], "|", output)
    with output.open(encoding="utf-8", newline="") as stream:
        assert list(csv.reader(stream, delimiter="|")) == [["a", "b"], ["1", "2"]]


def test_write_pipe_csv_to_stdout(monkeypatch):
    stream = io.StringIO()
    monkeypatch.setattr("sys.stdout", stream)
    write_pipe_csv(["a"], [["1"]])
    assert stream.getvalue() == "a\n1\n"


def test_write_pdf_xlsx(tmp_path):
    output = tmp_path / "out.xlsx"
    write_pdf_xlsx(["a"], [["valor"]], output)
    assert pd.read_excel(output).to_dict("records") == [{"a": "valor"}]


def test_write_image_outputs_creates_summary_and_audit(tmp_path):
    output = tmp_path / "out.xlsx"
    rows = [{
        "arquivo": "a.png", "categoria": "comprovante_bancario",
        "tipo_comprovante": "PIX", "emissor": "Banco", "valor": "R$ 1,00",
        "ocr_texto": "texto",
    }]
    write_image_outputs(rows, output)
    assert output.exists()
    assert output.with_suffix(".csv").exists()
    assert pd.ExcelFile(output).sheet_names == ["comprovantes", "ocr_texto"]
