# transparencia-pequenosComprovantesPDF
Ferramentas rascunho, para extração de dados em comprovantes de pagamentos por PIX, por boleto e outros pequenos comprovantes fiscais PDF do Brasil. Scripts de apoio para o dia a dia de pequenas auditoriais e apoio à transparencia.

## ScanPDFs

O script Python ScanPDFs é uma ferramenta para extração estruturada de dados de comprovantes bancários em PDF, especialmente comprovantes de pagamento por PIX e boleto.

Comprovantes de pagamento por PIX e por Boleto são as formas mais comuns no Brasil para comprovar que de fato pagamos: os arquivos PDF servem de evidência contábil, prova jurídica e registro de transparência.

Embora comprovantes em PDF sejam amplamente utilizados para demonstrar a realização de pagamentos, a validação definitiva de uma transação pode exigir a consulta aos sistemas das instituições financeiras envolvidas. Ainda assim, esses documentos costumam conter informações suficientes para processos de conferência, auditoria e organização financeira.

Nos últimos anos, modelos de IA passaram a ser utilizados para interpretar documentos desse tipo. Entretanto, quando é necessário processar centenas ou milhares de comprovantes, **o custo (computacional e financeiro) das soluções IA é alto**.

A proposta deste projeto é diferente: em vez de depender de IA em cada documento processado, o ScanPDFs utiliza regras de extração previamente definidas, por humanos e/ou por IA. Essas regras podem ser criadas e refinadas uma única vez, permitindo o processamento posterior de grandes volumes de documentos com rapidez, previsibilidade e **custo operacional praticamente nulo**.

### Como usar

Indique, no código Python, a pasta contendo os PDFs a serem analisados. O programa gera como saída um arquivo CSV com campos separados por pipe (`|`). Exemplo de execução em Linux:

```bash
python3 scanPDFs.py > meusComprovantesPDF.csv
```

O arquivo gerado é um arquivo CSV, e poderá então ser importado para planilhas, bancos de dados ou outras ferramentas de análise.

## ScanIMG

Similar ao script ScanPDFs porém mais complexo na instalação e menos acertivo nos resultados, por depender de OCR. Evebtualmente com passo de OCR externo e/ou HTML, poderá ser mais acertivo.

Como usar:
```bash
sudo apt install tesseract-ocr tesseract-ocr-por
pip install pytesseract pillow pandas openpyxl
# se necessário `pip install --upgrade "Pillow>=8.0.0"` para versao correta

python3 extrai_comprovantes.py comprovantes1.zip saida_comprovantes.xlsx
```
Resultados: arquivos `saida_comprovantes.xlsx` e `saida_comprovantes.csv`.  XLSX grande pois inclui extrações OCR para auditoria.


