# transparencia-pequenosComprovantesPDF

Ferramentas para extrair dados estruturados de pequenos comprovantes bancarios em
PDF e imagens. O projeto agora usa um pacote Python modular, uma CLI unificada e
regras de extracao em YAML para facilitar manutencao por colaboradores humanos e
IA.

## Estrutura

```text
.
├── src/
│   ├── scanPDFs.py                         # wrapper de compatibilidade
│   ├── scanIMGs.py                         # wrapper de compatibilidade
│   └── transparencia_comprovantes/
│       ├── cli.py                          # CLI comprovantes-scan
│       ├── pdf.py                          # processamento de PDFs textuais
│       ├── images.py                       # processamento de imagens/OCR
│       ├── hashing.py                      # hashes via hashlib
│       ├── output.py                       # CSV/XLSX
│       └── patterns/
│           ├── config.yml                  # configuracoes de execucao
│           └── rules.yml                   # regex e regras de extracao
├── tests/                                  # testes unitarios
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci-cd.yml
```

## Instalacao local

```bash
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Para OCR de imagens, instale tambem o Tesseract no sistema operacional. No
container isso ja esta configurado.

## CLI unificada

Processar PDFs de uma pasta:

```bash
comprovantes-scan pdf ./resolvido -o meusComprovantesPDF.csv
```

Gerar CSV e XLSX:

```bash
comprovantes-scan pdf ./resolvido -o meusComprovantesPDF.csv
```

Gerar somente CSV:

```bash
comprovantes-scan pdf ./resolvido -o meusComprovantesPDF.csv --no-xlsx
```

Usar arquivo YAML alternativo de padroes:

```bash
comprovantes-scan pdf --patterns ./meus-padroes.yml ./resolvido -o saida.csv
```

Tambem e possivel apontar `--patterns` para uma pasta contendo `config.yml` e
`rules.yml`:

```bash
comprovantes-scan pdf --patterns ./minhas-regras ./resolvido -o saida.csv
```

Processar imagens, pasta ou ZIP por OCR:

```bash
comprovantes-scan images ./imagens saida_comprovantes.xlsx
comprovantes-scan images comprovantes1.zip saida_comprovantes.xlsx
```

Os wrappers antigos continuam disponiveis:

```bash
python src/scanPDFs.py ./resolvido -o saida.csv
python src/scanIMGs.py ./imagens saida_comprovantes.xlsx
```

## Regras em YAML

As configuracoes e regex ficam separadas em:

```text
src/transparencia_comprovantes/patterns/config.yml
src/transparencia_comprovantes/patterns/rules.yml
```

O `config.yml` concentra parametros de execucao:

- `settings.csv_separator`
- `settings.stop_on_no_pattern`
- `settings.stop_on_size_error`
- `settings.max_text_chars`
- `settings.layout_bytes`
- `settings.pdf_csv_header`

O `rules.yml` separa regras de PDF e imagens/OCR:

- `pdf.document_patterns`: identifica tipo do comprovante.
- `pdf.emitter_patterns`: identifica emissor/banco.
- `pdf.field_patterns`: extrai campos por emissor.
- `images.marker_terms`: termos minimos para reconhecer comprovantes via OCR.
- `images.type_patterns`: identifica tipo via texto OCR.
- `images.field_patterns`: extrai campos via texto OCR.

Para adicionar um banco ou tipo de comprovante, prefira editar `rules.yml` e
criar testes com textos anonimizados em `tests/`. Ajustes operacionais devem ir
para `config.yml`.

## Docker

Build da imagem:

```bash
docker build -t transparencia-comprovantes:local .
```

Uso com uma pasta local montada:

```bash
docker run --rm -v "$PWD/data:/data" transparencia-comprovantes:local \
  pdf /data/input -o /data/out/comprovantes.csv
```

Com Compose:

```bash
docker compose run --rm scanner
```

O `Dockerfile` instala as dependencias Python e o Tesseract com idioma
portugues (`tesseract-ocr-por`).

## Testes

```bash
pytest
```

Os testes atuais cobrem hashing com `hashlib`, normalizacao de texto,
carregamento/compilacao do YAML e extracao por textos sinteticos. Testes com
PDFs ou imagens reais devem usar fixtures anonimizadas.

## GitHub PR-CI-CD

O workflow esta em:

```text
.github/workflows/ci-cd.yml
```

Ele executa:

1. CI em pull requests e pushes para `main`.
2. Instalacao de dependencias Python e Tesseract.
3. `pytest`.
4. Build da imagem Docker.
5. Um job de CD seguro apenas em push para `main`, por enquanto com placeholder.

### Como configurar no GitHub

1. Suba o repositorio para o GitHub com a branch principal chamada `main`.
2. Abra uma Pull Request normalmente.
3. O job `Tests` deve passar antes do merge.
4. Ao aceitar/mergear a PR em `main`, o workflow roda novamente e executa o job
   `CD skeleton`.
5. Quando o destino de CD for definido, substitua o placeholder por uma acao
   concreta, por exemplo publicar imagem no GitHub Container Registry, gerar
   release, ou acionar deploy externo.

Para publicar imagens no GHCR futuramente, o caminho usual e adicionar login com
`GITHUB_TOKEN`, definir tags e executar `docker push`. O workflow ja declara
`packages: write`, mas nao publica nada ate essa etapa ser explicitamente
implementada.
