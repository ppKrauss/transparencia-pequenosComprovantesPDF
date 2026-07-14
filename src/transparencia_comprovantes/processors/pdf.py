from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import pypdf

from ..config import compile_entries, compile_field_groups
from ..utils.hashing import file_digest
from ..utils.text import escape_separator, extract_br_date, first_captured_group


@dataclass
class PdfRunOptions:
    stop_on_no_pattern: bool
    stop_on_size_error: bool


class PdfProcessor:
    def __init__(self, config: dict[str, Any], options: PdfRunOptions | None = None):
        settings = config.get("settings", {})
        pdf_config = config.get("pdf", {})

        self.separator = settings.get("csv_separator", "|")
        self.max_text_chars = int(settings.get("max_text_chars", 20000))
        self.layout_bytes = int(settings.get("layout_bytes", 50000))
        self.max_bytes = int(
            settings.get("max_bytes", self.max_text_chars * 2 + self.layout_bytes * 2)
        )
        self.header = list(settings.get("pdf_csv_header", []))
        self.options = options or PdfRunOptions(
            stop_on_no_pattern=bool(settings.get("stop_on_no_pattern", True)),
            stop_on_size_error=bool(settings.get("stop_on_size_error", False)),
        )
        self.document_patterns = compile_entries(pdf_config.get("document_patterns", []))
        self.emitter_patterns = compile_entries(pdf_config.get("emitter_patterns", []))
        self.field_patterns = compile_field_groups(pdf_config.get("field_patterns", {}))

    def extract_patterns(
        self,
        label_pattern_pairs: list[tuple[str, Any]],
        text: str,
        return_label: bool = False,
    ) -> list[str]:
        values = []
        for label, pattern in label_pattern_pairs:
            if not pattern:
                values.append("")
                continue
            match = pattern.search(text)
            if return_label:
                values.append(label if match else "")
            else:
                value = first_captured_group(match)
                values.append(escape_separator(value, self.separator))
        return values

    def detect_emissor(self, text: str) -> str:
        matches = self.extract_patterns(self.emitter_patterns, text, return_label=True)
        return next((emitter for emitter in matches if emitter), "generico")

    def build_error_row(
        self,
        doc_id: int,
        doc_tipo: str,
        doc_emissor: str,
        file_values: list[str],
        reg_data: str,
        reg_status: str,
    ) -> list[str]:
        return [str(doc_id), doc_tipo, doc_emissor] + file_values + [
            reg_data,
            reg_status,
            "",
            "",
            "",
            "",
            "",
        ]

    def extract_text(self, path: Path) -> str:
        with path.open("rb") as pdf_file:
            reader = pypdf.PdfReader(pdf_file)
            text_parts = []
            text_len = 0
            for page in reader.pages:
                text = page.extract_text() or ""
                text_parts.append(text)
                text_len += len(text)
                if text_len > self.max_text_chars:
                    break
        return "\n".join(text_parts)

    def row_from_text(
        self,
        doc_id: int,
        file_name: str,
        sha1sum: str,
        file_date: str,
        full_text: str,
    ) -> tuple[list[str], bool]:
        file_values = [file_name, sha1sum, file_date]
        if len(full_text) > self.max_text_chars:
            print("---- Tamanho excedeu o limite de caracteres no texto ----", file=sys.stderr)
            print(" arquivo: " + file_name, file=sys.stderr)
            return (
                self.build_error_row(
                    doc_id, "undefined", "generico", file_values, "", "err02"
                ),
                self.options.stop_on_size_error,
            )

        for doc_type, pattern in self.document_patterns:
            if not pattern:
                continue
            match = pattern.search(full_text)
            if not match:
                continue

            date_source = match.group(1).strip() if match.lastindex else ""
            data_comprovante = extract_br_date(date_source)
            emissor = self.detect_emissor(full_text)
            base_values = [str(doc_id), doc_type, emissor, file_name, sha1sum, file_date]

            if doc_type in {"Pix", "Pagamento"}:
                pattern_group = self.field_patterns.get(
                    emissor, self.field_patterns.get("generico", [])
                )
                values = self.extract_patterns(pattern_group, full_text)
                return base_values + [data_comprovante, "ok-auto"] + values, False

            return base_values + ["", "err03", "", "", "", "", ""], False

        print("---- TEXTO SEM PADRAO RECONHECIDO! ----", file=sys.stderr)
        print(full_text, file=sys.stderr)
        return (
            self.build_error_row(
                doc_id, "undefined", "generico", file_values, "", "err04"
            ),
            self.options.stop_on_no_pattern,
        )

    def process_file(self, path: Path, doc_id: int) -> tuple[list[str], bool]:
        file_stat = path.stat()
        file_date = datetime.fromtimestamp(file_stat.st_mtime).date().isoformat()
        sha1sum = file_digest(path, "sha1")
        file_values = [path.name, sha1sum, file_date]

        if file_stat.st_size > self.max_bytes:
            print("---- Tamanho excedeu o limite de bytes ----", file=sys.stderr)
            print(" arquivo: " + path.name, file=sys.stderr)
            return (
                self.build_error_row(
                    doc_id, "undefined", "generico", file_values, "", "err01"
                ),
                self.options.stop_on_size_error,
            )

        full_text = self.extract_text(path)
        return self.row_from_text(doc_id, path.name, sha1sum, file_date, full_text)

    def process_directory(self, folder: Path, stop_files: set[str] | None = None) -> list[list[str]]:
        rows = []
        stop_files = stop_files or set()
        doc_id = 1
        for path in sorted(folder.glob("*.pdf")):
            if path.name in stop_files:
                continue
            row, should_stop = self.process_file(path, doc_id)
            rows.append(row)
            doc_id += 1
            if should_stop:
                print(" -- FIM --", file=sys.stderr)
                break
        return rows
