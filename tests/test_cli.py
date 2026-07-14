from pathlib import Path

import pytest

from transparencia_comprovantes import cli


def test_main_rejects_pdf_file_input(tmp_path):
    path = tmp_path / "input.pdf"
    path.write_bytes(b"pdf")
    with pytest.raises(ValueError, match="deve ser uma pasta"):
        cli.main(["pdf", str(path), "--no-xlsx"])


def test_run_pdf_writes_csv_without_xlsx(monkeypatch, tmp_path):
    output = tmp_path / "out.csv"
    monkeypatch.setattr(cli.PdfProcessor, "process_directory", lambda self, folder, stops: [["1"] * len(self.header)])
    assert cli.main(["pdf", str(tmp_path), "-o", str(output), "--no-xlsx"]) == 0
    assert output.exists()
    assert not output.with_suffix(".xlsx").exists()


def test_run_pdf_derives_xlsx_name_and_honors_flags(monkeypatch, tmp_path):
    output = tmp_path / "out.csv"
    captured = {}

    def fake_process(self, folder, stops):
        captured["options"] = self.options
        captured["stops"] = stops
        return []

    monkeypatch.setattr(cli.PdfProcessor, "process_directory", fake_process)
    monkeypatch.setattr(
        cli,
        "write_pdf_xlsx",
        lambda header, rows, path: captured.update(xlsx=path),
    )
    result = cli.main(
        [
            "pdf",
            str(tmp_path),
            "-o",
            str(output),
            "--continue-on-no-pattern",
            "--stop-on-size-error",
            "--stop-file",
            "ignorar.pdf",
        ]
    )
    assert result == 0
    assert captured["options"].stop_on_no_pattern is False
    assert captured["options"].stop_on_size_error is True
    assert captured["stops"] == {"ignorar.pdf"}
    assert captured["xlsx"] == output.with_suffix(".xlsx")


def test_run_images_cleans_temporary_input(monkeypatch, tmp_path):
    class Cleanup:
        called = False

        def cleanup(self):
            self.called = True

    cleanup = Cleanup()
    monkeypatch.setattr(cli, "image_files_from_input", lambda path: ([Path("a.png")], cleanup))
    monkeypatch.setattr(cli.ImageProcessor, "process_files", lambda self, files: [])
    monkeypatch.setattr(cli, "write_image_outputs", lambda rows, output: None)
    assert cli.main(["images", "input.zip", str(tmp_path / "out.xlsx")]) == 0
    assert cleanup.called
