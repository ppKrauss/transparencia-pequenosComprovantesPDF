# transparencia-pequenosComprovantesPDF

Extrai dados estruturados de pequenos comprovantes bancarios em PDF e imagens.
O projeto oferece uma unica CLI, regras YAML editaveis e saidas CSV/XLSX.

## Estrutura

```text
.
|-- data/
|   |-- config.yml             # configuracoes de execucao
|   `-- rules.yml              # regex e regras de extracao
|-- src/
|   `-- transparencia_comprovantes/
|       |-- cli.py             # CLI unificada
|       |-- config.py          # carregamento dos YAMLs
|       |-- output.py          # CSV e XLSX
|       |-- processors/
|       |   |-- pdf.py         # PDFs textuais
|       |   `-- images.py      # imagens e OCR
|       `-- utils/
|           |-- hashing.py     # hashes via hashlib
|           `-- text.py        # normalizacao e extracao textual
|-- tests/
|-- Dockerfile
`-- docker-compose.yml
```

`src/transparencia_comprovantes` e o pacote instalavel do Python. Nao ha scripts
duplicados ou wrappers de compatibilidade em `src`.

## Instalacao

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

O processamento de imagens tambem requer Tesseract. A imagem Docker ja inclui
os idiomas portugues e ingles.

## Uso

```bash
# PDFs: CSV e XLSX
comprovantes-scan pdf ./entrada -o ./saida/comprovantes.csv

# PDFs: somente CSV
comprovantes-scan pdf ./entrada -o ./saida/comprovantes.csv --no-xlsx

# Imagens, pasta ou ZIP
comprovantes-scan images ./imagens ./saida/comprovantes.xlsx
```

Por padrao, a CLI carrega `data/config.yml` e `data/rules.yml`. Para usar outro
conjunto completo de dados:

```bash
comprovantes-scan --data-dir ./outras-regras pdf ./entrada -o saida.csv
```

Os dois arquivos sao obrigatorios. `config.yml` contem limites e opcoes de
execucao; `rules.yml` contem os padroes de PDF e OCR. Tambem e possivel definir
o diretorio pela variavel `COMPROVANTES_DATA_DIR`.

## Docker

```bash
docker build -t transparencia-comprovantes:local .
docker run --rm -v "$PWD/arquivos:/arquivos" transparencia-comprovantes:local \
  pdf /arquivos/entrada -o /arquivos/saida/comprovantes.csv
```

Com Compose:

```bash
docker compose run --rm scanner
```

## Testes

```bash
pytest
```

A suite valida configuracao, regex, hashing, classificacao e extracao de PDF/OCR,
tipos de entrada, geracao CSV/XLSX e fluxos da CLI. O limite minimo de cobertura
e 85% e e aplicado localmente e no CI.

O workflow `.github/workflows/ci-cd.yml` executa testes, build Docker e publica a
imagem no GHCR em pushes para `main`.
