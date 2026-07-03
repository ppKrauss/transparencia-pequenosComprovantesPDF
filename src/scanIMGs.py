#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Faz scan de ZIP ou pasta e extrai dados de comprovantes bancários em imagens JPG/PNG.

Dependências Python:
    pip install pytesseract pillow pandas openpyxl

Dependência do sistema:
    sudo apt install tesseract-ocr tesseract-ocr-por

Uso:
    python3 scanIMGs.py comprovantes1.zip saida_comprovantes.xlsx

Também aceita pasta:
    python3 scanIMGs.py ./imagens saida_comprovantes.xlsx
"""

import argparse
import re
import zipfile
import tempfile
import unicodedata
from pathlib import Path

import pandas as pd
from PIL import Image, ImageOps, ImageFilter
import pytesseract


IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}
DEFAULT_INPUT_PATH = "comprovantes1.zip"
DEFAULT_OUTPUT_XLSX = "saida_comprovantes.xlsx"


def norm(txt: str) -> str:
    txt = txt or ""
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    txt = txt.replace("\r", "\n")
    txt = re.sub(r"[ \t]+", " ", txt)
    txt = re.sub(r"\n{3,}", "\n\n", txt)
    return txt.strip()


def clean_value(v):
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip(" :;\n\t")


def first_match(patterns, text, flags=re.I | re.M):
    for pat in patterns:
        m = re.search(pat, text, flags)
        if m:
            return clean_value(m.group(1))
    return ""


def ocr_image(path: Path) -> str:
    img = Image.open(path).convert("RGB")

    # Pré-processamento simples para fotos de comprovante
    img = ImageOps.grayscale(img)
    img = ImageOps.autocontrast(img)
    img = img.filter(ImageFilter.SHARPEN)

    # Aumenta imagens pequenas
    if img.width < 1200:
        factor = 2
        img = img.resize((img.width * factor, img.height * factor))

    text = pytesseract.image_to_string(img, lang="por+eng", config="--psm 6")
    return norm(text)


def detect_emissor(text):
    t = norm(text).lower()
    if "santander" in t or "central de atendimento santander" in t:
        return "Santander"
    if "bradesco" in t:
        return "Bradesco"
    if "itau" in t or "itaú" in t:
        return "Itaú"
    if "nubank" in t:
        return "Nubank"
    if "caixa economica" in t or "caixa econômica" in t:
        return "Caixa"
    if "banco do brasil" in t:
        return "Banco do Brasil"
    return ""


def detect_tipo(text):
    t = norm(text).lower()

    if not any(x in t for x in [
        "pagamento", "pix", "ted", "doc", "transferencia", "transferência",
        "autenticacao", "autenticação", "codigo de barras", "código de barras",
        "comprovante", "transacao", "transação"
    ]):
        return "nao_identificado"

    if "ted agendada" in t:
        return "TED agendada"
    if re.search(r"\bted\b", t):
        return "TED"
    if re.search(r"\bpix\b", t):
        return "PIX"
    if re.search(r"\bdoc\b", t):
        return "DOC"
    if "codigo de barras" in t or "código de barras" in t or "convenio de arrecadacao" in t:
        return "pagamento_boleto_convenio"
    if "pagamento realizado com sucesso" in t:
        return "pagamento"
    if "transferencia" in t or "transferência" in t:
        return "transferencia"
    return "comprovante_bancario"


def classify_categoria(text, tipo, emissor):
    t = norm(text).lower()
    if len(t) < 30:
        return "ocr_falhou"
    if tipo == "nao_identificado" and not emissor:
        return "nao_bancario_ou_desconhecido"
    if tipo == "nao_identificado":
        return "desconhecido"
    return "comprovante_bancario"


def extract_santander(text):
    # Texto normalizado sem acentos melhora o regex.
    n = norm(text)

    row = {}

    row["valor"] = first_match([
        r"\bValor[:\s]*\n?\s*(R\$\s*[\d\.\,]+)",
        r"\bValor[:\s]*\n?\s*([\d\.\,]+)",
    ], n)

    row["codigo_transacao"] = first_match([
        r"Autenticacao bancaria[:\s]*\n?\s*([A-Z0-9]{10,})",
        r"Autenticacao[:\s]*\n?\s*([A-Z0-9]{10,})",
        r"Autentica[cç][aã]o banc[aá]ria[:\s]*\n?\s*([A-Z0-9]{10,})",
        r"Autentica[cç][aã]o[:\s]*\n?\s*([A-Z0-9]{10,})",
    ], n)

    row["data_transacao"] = first_match([
        r"Data da transa[cç][aã]o[:\s]*\n?\s*(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2})?)",
        r"Data da Transacao[:\s]*\n?\s*(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2})?)",
    ], n)

    row["data_pagamento"] = first_match([
        r"Data de Pagamento[:\s]*\n?\s*(\d{2}/\d{2}/\d{4})",
        r"Data de Agendamento[:\s]*\n?\s*(\d{2}/\d{2}/\d{4})",
    ], n)

    # Boleto / convênio
    empresa = first_match([
        r"Empresa[:\s]*\n?\s*(.+?)(?:\n|Convenio|Convênio)",
    ], n)
    convenio = first_match([
        r"Convenio de Arrecadacao[:\s]*\n?\s*([0-9]+)",
        r"Conv[eê]nio de Arrecada[cç][aã]o[:\s]*\n?\s*([0-9]+)",
    ], n)
    codigo_barras = first_match([
        r"Codigo de Barras[:\s]*\n?\s*([0-9\-\s\.]+(?:\n[0-9\-\s\.]+)?)",
        r"C[oó]digo de Barras[:\s]*\n?\s*([0-9\-\s\.]+(?:\n[0-9\-\s\.]+)?)",
    ], n)

    # TED / transferência
    pagador = first_match([
        r"Nome[:\s]*\n?\s*(.+?)(?:\n|Conta de Destino)",
        r"Nome Origem[:\s]*\n?\s*(.+?)(?:\n|Conta de Destino)",
    ], n)
    conta_origem = first_match([
        r"Conta Origem[:\s]*\n?\s*([0-9\/\.\-]+)",
    ], n)
    conta_destino = first_match([
        r"Conta de Destino[:\s]*\n?\s*([0-9\/\.\-]+)",
        r"Conta Destino[:\s]*\n?\s*([0-9\/\.\-]+)",
    ], n)
    nome_destino = first_match([
        r"Nome Destino[:\s]*\n?\s*(.+?)(?:\n|Instituicao|Instituição|CPF/CNPJ)",
        r"Favorecido[:\s]*\n?\s*(.+?)(?:\n|Instituicao|Instituição|CPF/CNPJ)",
    ], n)
    instituicao = first_match([
        r"Instituicao[:\s]*\n?\s*(.+?)(?:\n|CPF/CNPJ|Tipo Conta)",
        r"Institui[cç][aã]o[:\s]*\n?\s*(.+?)(?:\n|CPF/CNPJ|Tipo Conta)",
    ], n)
    cpf_cnpj = first_match([
        r"CPF/CNPJ[:\s]*\n?\s*([0-9\.\-\/]+)",
    ], n)

    if empresa:
        row["beneficiario"] = empresa
        row["conta_beneficiario"] = convenio
        row["codigo_barras"] = codigo_barras
    else:
        row["beneficiario"] = nome_destino
        row["conta_beneficiario"] = conta_destino
        row["codigo_barras"] = ""

    row["pagador"] = pagador
    row["conta_pagador"] = conta_origem
    row["cpf_cnpj_beneficiario"] = cpf_cnpj
    row["instituicao_beneficiario"] = instituicao

    return row


def extract_generic(text):
    n = norm(text)
    return {
        "valor": first_match([
            r"\bValor[:\s]*\n?\s*(R\$\s*[\d\.\,]+)",
            r"\bR\$\s*([\d\.\,]+)",
        ], n),
        "codigo_transacao": first_match([
            r"Autentica[cç][aã]o(?: banc[aá]ria)?[:\s]*\n?\s*([A-Z0-9]{10,})",
            r"(?:ID|Identificador|Controle)[:\s]*\n?\s*([A-Z0-9\-]{10,})",
        ], n),
        "data_transacao": first_match([
            r"Data da transa[cç][aã]o[:\s]*\n?\s*(\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}:\d{2})?)",
            r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})",
        ], n),
        "data_pagamento": "",
        "beneficiario": first_match([
            r"(?:Benefici[aá]rio|Favorecido|Recebedor|Destino)[:\s]*\n?\s*(.+?)(?:\n|CPF|CNPJ|Banco|Institui)",
        ], n),
        "conta_beneficiario": first_match([
            r"Conta(?: de Destino| destino)?[:\s]*\n?\s*([0-9\/\.\-]+)",
        ], n),
        "pagador": first_match([
            r"(?:Pagador|Nome Origem|Nome)[:\s]*\n?\s*(.+?)(?:\n|Conta|CPF|CNPJ)",
        ], n),
        "conta_pagador": "",
        "cpf_cnpj_beneficiario": first_match([
            r"CPF/CNPJ[:\s]*\n?\s*([0-9\.\-\/]+)",
        ], n),
        "instituicao_beneficiario": "",
        "codigo_barras": "",
    }


def image_files_from_input(input_path: Path):
    if input_path.is_dir():
        return sorted([p for p in input_path.rglob("*") if p.suffix.lower() in IMG_EXTS]), None

    if zipfile.is_zipfile(input_path):
        tmp = tempfile.TemporaryDirectory()
        outdir = Path(tmp.name)
        with zipfile.ZipFile(input_path, "r") as z:
            z.extractall(outdir)
        files = sorted([p for p in outdir.rglob("*") if p.suffix.lower() in IMG_EXTS])
        return files, tmp

    if input_path.suffix.lower() in IMG_EXTS:
        return [input_path], None

    raise ValueError(f"Entrada não reconhecida: {input_path}")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Executa OCR e extrai dados estruturados de comprovantes bancários em imagens."
    )
    parser.add_argument(
        "input_path",
        nargs="?",
        default=DEFAULT_INPUT_PATH,
        help="ZIP, pasta ou imagem a processar. Se omitido, usa comprovantes1.zip.",
    )
    parser.add_argument(
        "output_xlsx",
        nargs="?",
        default=DEFAULT_OUTPUT_XLSX,
        help="Planilha XLSX de saída. Se omitido, usa saida_comprovantes.xlsx.",
    )
    return parser.parse_args()


def process_file(path: Path):
    try:
        text = ocr_image(path)
        emissor = detect_emissor(text)
        tipo = detect_tipo(text)
        categoria = classify_categoria(text, tipo, emissor)

        if emissor == "Santander":
            fields = extract_santander(text)
        else:
            fields = extract_generic(text)

        obs = ""
        if categoria != "comprovante_bancario":
            obs = "Arquivo não classificado como comprovante bancário por regras/OCR."
        elif not fields.get("codigo_transacao"):
            obs = "Comprovante provável, mas sem código de transação extraído."
        elif not fields.get("valor"):
            obs = "Comprovante provável, mas sem valor extraído."

        return {
            "arquivo": path.name,
            "categoria": categoria,
            "tipo_comprovante": tipo,
            "emissor": emissor,
            "valor": fields.get("valor", ""),
            "beneficiario": fields.get("beneficiario", ""),
            "conta_beneficiario": fields.get("conta_beneficiario", ""),
            "cpf_cnpj_beneficiario": fields.get("cpf_cnpj_beneficiario", ""),
            "instituicao_beneficiario": fields.get("instituicao_beneficiario", ""),
            "pagador": fields.get("pagador", ""),
            "conta_pagador": fields.get("conta_pagador", ""),
            "codigo_transacao": fields.get("codigo_transacao", ""),
            "data_transacao": fields.get("data_transacao", ""),
            "data_pagamento": fields.get("data_pagamento", ""),
            "codigo_barras": fields.get("codigo_barras", ""),
            "observacoes": obs,
            "ocr_texto": text,
        }

    except Exception as e:
        return {
            "arquivo": path.name,
            "categoria": "erro",
            "tipo_comprovante": "erro",
            "emissor": "",
            "valor": "",
            "beneficiario": "",
            "conta_beneficiario": "",
            "cpf_cnpj_beneficiario": "",
            "instituicao_beneficiario": "",
            "pagador": "",
            "conta_pagador": "",
            "codigo_transacao": "",
            "data_transacao": "",
            "data_pagamento": "",
            "codigo_barras": "",
            "observacoes": f"Erro: {e}",
            "ocr_texto": "",
        }


def main():
    args = parse_args()
    input_path = Path(args.input_path)
    output_xlsx = Path(args.output_xlsx)

    files, tmp = image_files_from_input(input_path)
    print(f"Imagens encontradas: {len(files)}")

    rows = []
    for i, path in enumerate(files, 1):
        print(f"[{i}/{len(files)}] OCR: {path.name}")
        rows.append(process_file(path))

    df = pd.DataFrame(rows)

    # XLSX principal
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        df.drop(columns=["ocr_texto"]).to_excel(writer, index=False, sheet_name="comprovantes")
        df[["arquivo", "categoria", "tipo_comprovante", "emissor", "ocr_texto"]].to_excel(
            writer, index=False, sheet_name="ocr_texto"
        )

    # CSV pipe-separated, útil para Linux/PostgreSQL
    output_csv = output_xlsx.with_suffix(".csv")
    df.drop(columns=["ocr_texto"]).to_csv(output_csv, index=False, sep="|")

    print(f"Planilha gerada: {output_xlsx}")
    print(f"CSV gerado: {output_csv}")

    if tmp:
        tmp.cleanup()


if __name__ == "__main__":
    main()
