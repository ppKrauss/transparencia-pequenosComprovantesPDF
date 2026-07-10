#!/usr/bin/env python3
"""Wrapper de compatibilidade para a nova CLI unificada."""

import sys

from transparencia_comprovantes.cli import main


if __name__ == "__main__":
    raise SystemExit(main(["pdf", *sys.argv[1:]]))
