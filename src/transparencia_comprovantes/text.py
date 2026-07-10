from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Iterable


def normalize_text(text: str | None) -> str:
    text = text or ""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(char for char in text if not unicodedata.combining(char))
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def clean_value(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip(" :;\n\t")


def escape_separator(text: object, separator: str = "|") -> str:
    return (
        str(text)
        .replace(separator, "-")
        .replace("\r", " ")
        .replace("\n", " ")
        .strip()
    )


def first_match(
    patterns: Iterable[re.Pattern[str]], text: str, group: int = 1
) -> str:
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            return clean_value(match.group(group))
    return ""


def first_captured_group(match: re.Match[str] | None) -> str:
    if not match:
        return ""
    for value in match.groups():
        if value is not None:
            return clean_value(value)
    return ""


def extract_br_date(text: str | None) -> str:
    text = text or ""
    match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if not match:
        return text
    try:
        return datetime.strptime(match.group(0), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return text
