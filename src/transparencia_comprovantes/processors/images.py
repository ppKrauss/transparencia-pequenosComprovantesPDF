from __future__ import annotations

import tempfile
import zipfile
from pathlib import Path
from typing import Any

from ..config import compile_entries, compile_field_groups
from ..utils.text import first_captured_group, normalize_text


IMG_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".tif", ".tiff"}


class ImageProcessor:
    def __init__(self, config: dict[str, Any]):
        image_config = config.get("images", {})
        self.marker_terms = image_config.get("marker_terms", [])
        self.emitter_patterns = compile_entries(image_config.get("emitter_patterns", []))
        self.type_patterns = compile_entries(image_config.get("type_patterns", []))
        self.field_patterns = compile_field_groups(image_config.get("field_patterns", {}))

    def ocr_image(self, path: Path) -> str:
        from PIL import Image, ImageFilter, ImageOps
        import pytesseract

        image = Image.open(path).convert("RGB")
        image = ImageOps.grayscale(image)
        image = ImageOps.autocontrast(image)
        image = image.filter(ImageFilter.SHARPEN)

        if image.width < 1200:
            image = image.resize((image.width * 2, image.height * 2))

        text = pytesseract.image_to_string(image, lang="por+eng", config="--psm 6")
        return normalize_text(text)

    def detect_emissor(self, text: str) -> str:
        normalized = normalize_text(text)
        for label, pattern in self.emitter_patterns:
            if pattern and pattern.search(normalized):
                return label
        return ""

    def detect_tipo(self, text: str) -> str:
        normalized = normalize_text(text).lower()
        if not any(term.lower() in normalized for term in self.marker_terms):
            return "nao_identificado"
        for label, pattern in self.type_patterns:
            if pattern and pattern.search(normalized):
                return label
        return "comprovante_bancario"

    def classify_categoria(self, text: str, tipo: str, emissor: str) -> str:
        normalized = normalize_text(text).lower()
        if len(normalized) < 30:
            return "ocr_falhou"
        if tipo == "nao_identificado" and not emissor:
            return "nao_bancario_ou_desconhecido"
        if tipo == "nao_identificado":
            return "desconhecido"
        return "comprovante_bancario"

    def extract_fields(self, text: str, emissor: str) -> dict[str, str]:
        normalized = normalize_text(text)
        pattern_group = self.field_patterns.get(emissor, self.field_patterns.get("generico", []))
        fields: dict[str, str] = {}
        for label, pattern in pattern_group:
            if not pattern:
                fields[label] = ""
                continue
            match = pattern.search(normalized)
            fields[label] = first_captured_group(match)
        return fields

    def row_from_text(self, file_name: str, text: str) -> dict[str, str]:
        emissor = self.detect_emissor(text)
        tipo = self.detect_tipo(text)
        categoria = self.classify_categoria(text, tipo, emissor)
        fields = self.extract_fields(text, emissor)

        observacoes = ""
        if categoria != "comprovante_bancario":
            observacoes = "Arquivo nao classificado como comprovante bancario por regras/OCR."
        elif not fields.get("codigo_transacao"):
            observacoes = "Comprovante provavel, mas sem codigo de transacao extraido."
        elif not fields.get("valor"):
            observacoes = "Comprovante provavel, mas sem valor extraido."

        return {
            "arquivo": file_name,
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
            "observacoes": observacoes,
            "ocr_texto": text,
        }

    def process_file(self, path: Path) -> dict[str, str]:
        try:
            return self.row_from_text(path.name, self.ocr_image(path))
        except Exception as exc:
            return error_row(path.name, exc)

    def process_files(self, files: list[Path]) -> list[dict[str, str]]:
        rows = []
        for index, path in enumerate(files, 1):
            print(f"[{index}/{len(files)}] OCR: {path.name}")
            rows.append(self.process_file(path))
        return rows


def error_row(file_name: str, exc: Exception) -> dict[str, str]:
    return {
        "arquivo": file_name,
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
        "observacoes": f"Erro: {exc}",
        "ocr_texto": "",
    }


def image_files_from_input(input_path: Path):
    if input_path.is_dir():
        return sorted(path for path in input_path.rglob("*") if path.suffix.lower() in IMG_EXTS), None

    if zipfile.is_zipfile(input_path):
        tmp = tempfile.TemporaryDirectory()
        outdir = Path(tmp.name)
        with zipfile.ZipFile(input_path, "r") as zipped:
            zipped.extractall(outdir)
        files = sorted(path for path in outdir.rglob("*") if path.suffix.lower() in IMG_EXTS)
        return files, tmp

    if input_path.suffix.lower() in IMG_EXTS:
        return [input_path], None

    raise ValueError(f"Entrada nao reconhecida: {input_path}")
