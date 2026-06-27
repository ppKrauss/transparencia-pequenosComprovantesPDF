# transparencia-pequenosComprovantesPDF
Ferramentas rascunho, para extração de dados em comprovantes de pagamentos por PIX, por boleto e outros pequenos comprovantes fiscais PDF do Brasil. Scripts de apoio para o dia a dia de pequenas auditoriais e apoio à transparencia.

## ScanPDFs

O script Python ScanPDFs é uma ferramenta para extração estruturada de dados de comprovantes bancários em PDF, especialmente comprovantes de pagamento por PIX e boleto.

Comprovantes de pagamento por PIX e por Boleto são as formas mais comuns no Brasil para comprovar que de fato pagamos: os arquivos PDF servem de evidência contábil, prova jurídica e registro de transparência.

Embora comprovantes em PDF sejam amplamente utilizados para demonstrar a realização de pagamentos, a validação definitiva de uma transação pode exigir a consulta aos sistemas das instituições financeiras envolvidas. Ainda assim, esses documentos costumam conter informações suficientes para processos de conferência, auditoria e organização financeira.

Nos últimos anos, modelos de IA passaram a ser utilizados para interpretar documentos desse tipo. Entretanto, quando é necessário processar centenas ou milhares de comprovantes, **o custo (computacional e financeiro) das soluções IA é alto**.

A proposta deste projeto é diferente: em vez de depender de IA em cada documento processado, o ScanPDFs utiliza regras de extração previamente definidas, por humanos e/ou por IA. Essas regras podem ser criadas e refinadas uma única vez, permitindo o processamento posterior de grandes volumes de documentos com rapidez, previsibilidade e **custo operacional praticamente nulo**.

### Como usar

Indique a pasta contendo os PDFs a serem analisados. Se nenhuma pasta for informada, o script usa o caminho interno definido em `buscar_PDFs_aqui`, preservando o comportamento original. A saída CSV usa campos separados por pipe (`|`).

Instalação mínima para PDF e planilha:

```bash
pip install pypdf pandas openpyxl
```

Usos principais:

| Uso | Comando | Resultado esperado |
| --- | --- | --- |
| Usar a pasta interna configurada em `buscar_PDFs_aqui` e imprimir CSV no terminal | `python3 scanPDFs.py` | CSV no stdout. Nenhum arquivo é criado automaticamente. |
| Usar a pasta interna e redirecionar CSV manualmente | `python3 scanPDFs.py > meusComprovantesPDF.csv` | Cria apenas `meusComprovantesPDF.csv`. Como o redirecionamento é feito pelo shell, o script não sabe o nome do arquivo e não cria XLSX automático. |
| Informar uma pasta e gravar CSV | `python3 scanPDFs.py ./resolvido -o meusComprovantesPDF.csv` | Cria `meusComprovantesPDF.csv` e também `meusComprovantesPDF.xlsx`. |
| Informar uma pasta, gravar CSV e escolher outro nome para XLSX | `python3 scanPDFs.py ./resolvido -o meusComprovantesPDF.csv --xlsx-output auditoria.xlsx` | Cria `meusComprovantesPDF.csv` e `auditoria.xlsx`. |
| Informar uma pasta e gerar somente CSV, sem XLSX | `python3 scanPDFs.py ./resolvido -o meusComprovantesPDF.csv --no-xlsx` | Cria apenas `meusComprovantesPDF.csv`. |
| Imprimir CSV no terminal e ainda gerar XLSX | `python3 scanPDFs.py ./resolvido --xlsx-output auditoria.xlsx` | CSV no stdout e arquivo `auditoria.xlsx`. |

Controles adicionais:

```bash
# Ignorar um ou mais arquivos pelo nome
python3 scanPDFs.py ./resolvido -o saida.csv --stop-file arquivo1.pdf --stop-file arquivo2.pdf

# Continuar processando quando um PDF não casar com padrões conhecidos
python3 scanPDFs.py ./resolvido -o saida.csv --continue-on-no-pattern

# Parar o processamento quando um PDF ultrapassar os limites de tamanho configurados
python3 scanPDFs.py ./resolvido -o saida.csv --stop-on-size-error
```

O CSV continua útil para Linux, bancos de dados e automações. O XLSX facilita auditoria visual e conferência manual.

## ScanIMGs

Similar ao script ScanPDFs porém mais complexo na instalação e menos acertivo nos resultados, por depender de OCR. Evebtualmente com passo de OCR externo e/ou HTML, poderá ser mais acertivo.

### Como usar

O `scanIMGs.py` aceita ZIP, pasta ou uma imagem individual. Ele sempre gera uma planilha XLSX e um CSV de mesmo nome, trocando apenas a extensão para `.csv`.

Instalação:

```bash
sudo apt install tesseract-ocr tesseract-ocr-por
pip install pytesseract pillow pandas openpyxl
# se necessário `pip install --upgrade "Pillow>=8.0.0"` para versao correta
```

Usos principais:

| Uso | Comando | Resultado esperado |
| --- | --- | --- |
| Usar entrada e saída padrão | `python3 scanIMGs.py` | Lê `comprovantes1.zip` e gera `saida_comprovantes.xlsx` + `saida_comprovantes.csv`. |
| Processar um ZIP e escolher a planilha de saída | `python3 scanIMGs.py comprovantes1.zip saida_comprovantes.xlsx` | Gera `saida_comprovantes.xlsx` + `saida_comprovantes.csv`. |
| Processar uma pasta de imagens | `python3 scanIMGs.py ./imagens saida_imagens.xlsx` | Gera `saida_imagens.xlsx` + `saida_imagens.csv`. |
| Processar uma única imagem | `python3 scanIMGs.py ./comprovante.jpg saida_comprovante.xlsx` | Gera `saida_comprovante.xlsx` + `saida_comprovante.csv`. |
| Informar só a entrada e usar nome padrão de saída | `python3 scanIMGs.py ./imagens` | Gera `saida_comprovantes.xlsx` + `saida_comprovantes.csv`. |

O XLSX inclui uma aba principal com os campos extraídos e uma aba com o texto OCR bruto para auditoria. Por isso, em lotes grandes, a planilha pode ficar pesada.
