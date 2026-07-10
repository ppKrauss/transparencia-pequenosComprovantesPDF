from __future__ import annotations

import csv
import sys
from pathlib import Path


def write_pipe_csv(
    header: list[str],
    rows: list[list[str]],
    separator: str = "|",
    output_path: Path | None = None,
) -> None:
    if output_path:
        with output_path.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.writer(stream, delimiter=separator, lineterminator="\n")
            writer.writerow(header)
            writer.writerows(rows)
        return

    writer = csv.writer(sys.stdout, delimiter=separator, lineterminator="\n")
    writer.writerow(header)
    writer.writerows(rows)


def write_pdf_xlsx(header: list[str], rows: list[list[str]], output_path: Path) -> None:
    import pandas as pd

    dataframe = pd.DataFrame(rows, columns=header)
    dataframe.to_excel(output_path, index=False, sheet_name="comprovantes")


def write_image_outputs(rows: list[dict[str, str]], output_xlsx: Path) -> None:
    import pandas as pd

    dataframe = pd.DataFrame(rows)
    with pd.ExcelWriter(output_xlsx, engine="openpyxl") as writer:
        dataframe.drop(columns=["ocr_texto"]).to_excel(
            writer, index=False, sheet_name="comprovantes"
        )
        dataframe[["arquivo", "categoria", "tipo_comprovante", "emissor", "ocr_texto"]].to_excel(
            writer, index=False, sheet_name="ocr_texto"
        )

    dataframe.drop(columns=["ocr_texto"]).to_csv(
        output_xlsx.with_suffix(".csv"), index=False, sep="|"
    )
