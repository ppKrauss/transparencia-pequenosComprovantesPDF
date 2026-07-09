from __future__ import annotations

import argparse
from pathlib import Path

from .config import load_config
from .images import ImageProcessor, image_files_from_input
from .output import write_image_outputs, write_pdf_xlsx, write_pipe_csv
from .pdf import PdfProcessor, PdfRunOptions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="comprovantes-scan",
        description="Extrai dados de comprovantes PDF e imagens usando regras em YAML.",
    )
    parser.add_argument(
        "--patterns",
        help="Arquivo YAML alternativo com padroes de extracao.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    pdf_parser = subparsers.add_parser("pdf", help="Processa comprovantes PDF textuais.")
    pdf_parser.add_argument(
        "--patterns",
        default=argparse.SUPPRESS,
        help="Arquivo YAML alternativo com padroes de extracao.",
    )
    pdf_parser.add_argument(
        "input_path",
        nargs="?",
        default=".",
        help="Pasta contendo PDFs. Se omitido, usa a pasta atual.",
    )
    pdf_parser.add_argument("-o", "--output-csv", help="Arquivo CSV de saida.")
    pdf_parser.add_argument("--xlsx-output", help="Arquivo XLSX de saida.")
    pdf_parser.add_argument("--no-xlsx", action="store_true", help="Nao gerar XLSX.")
    pdf_parser.add_argument(
        "--stop-file",
        action="append",
        default=[],
        help="Nome de arquivo PDF a ignorar. Pode ser usado varias vezes.",
    )
    pdf_parser.add_argument(
        "--continue-on-no-pattern",
        action="store_true",
        help="Continua quando um PDF nao casar com padroes conhecidos.",
    )
    pdf_parser.add_argument(
        "--stop-on-size-error",
        action="store_true",
        help="Para quando um PDF ultrapassar os limites configurados.",
    )

    image_parser = subparsers.add_parser("images", help="Processa imagens ou ZIP por OCR.")
    image_parser.add_argument(
        "--patterns",
        default=argparse.SUPPRESS,
        help="Arquivo YAML alternativo com padroes de extracao.",
    )
    image_parser.add_argument(
        "input_path",
        nargs="?",
        default="comprovantes1.zip",
        help="ZIP, pasta ou imagem a processar.",
    )
    image_parser.add_argument(
        "output_xlsx",
        nargs="?",
        default="saida_comprovantes.xlsx",
        help="Planilha XLSX de saida.",
    )
    return parser


def run_pdf(args: argparse.Namespace) -> int:
    config = load_config(args.patterns)
    settings = config.get("settings", {})
    options = PdfRunOptions(
        stop_on_no_pattern=False
        if args.continue_on_no_pattern
        else bool(settings.get("stop_on_no_pattern", True)),
        stop_on_size_error=True
        if args.stop_on_size_error
        else bool(settings.get("stop_on_size_error", False)),
    )
    processor = PdfProcessor(config, options)
    input_path = Path(args.input_path)
    if not input_path.is_dir():
        raise ValueError(f"Entrada PDF deve ser uma pasta: {input_path}")

    rows = processor.process_directory(input_path, set(args.stop_file))
    output_csv = Path(args.output_csv) if args.output_csv else None
    write_pipe_csv(processor.header, rows, processor.separator, output_csv)

    xlsx_output = Path(args.xlsx_output) if args.xlsx_output else None
    if not args.no_xlsx:
        if xlsx_output is None and output_csv is not None:
            xlsx_output = output_csv.with_suffix(".xlsx")
        if xlsx_output is not None:
            write_pdf_xlsx(processor.header, rows, xlsx_output)
    return 0


def run_images(args: argparse.Namespace) -> int:
    config = load_config(args.patterns)
    input_path = Path(args.input_path)
    output_xlsx = Path(args.output_xlsx)

    files, tmp = image_files_from_input(input_path)
    print(f"Imagens encontradas: {len(files)}")
    try:
        rows = ImageProcessor(config).process_files(files)
        write_image_outputs(rows, output_xlsx)
    finally:
        if tmp:
            tmp.cleanup()

    print(f"Planilha gerada: {output_xlsx}")
    print(f"CSV gerado: {output_xlsx.with_suffix('.csv')}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "pdf":
        return run_pdf(args)
    if args.command == "images":
        return run_images(args)
    parser.error("Comando invalido.")
    return 2
