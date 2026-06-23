# transparencia-pequenosComprovantesPDF
Ferramentas rascunho, para extração de dados em comprovantes de pagamentos por PIX, por boleto e outros pequenos comprovantes fiscais PDF do Brasil. Scripts de apoio para o dia a dia de pequenas auditoriais e apoio à transparencia.

## ScanPDFs
Comprovantes de pagamento por PIX e por Boleto são as formas mais comuns no Brasil que temos de comprovar que de fato pagamos, **sem depender terceiros no processo de comprovação**. Juridicamente de bancos e outros atores ainda podem ser necessários em casos extremos, pois os PDFs não são assinados, e a veracidade dos códigos de transação precisa ser confirmada.

Apesar da IA fazer todo processo de análise de PDFs, **o custo de efetuar extração em centenas ou milhares de documentos por IA pode ser muito alto**. A ideia neste repositório é **registrar regras**, ou seja registrar o trabalho da IA apenas uma vez, garantindo **custo zero** neste tipo de processamento.

Como usar: indicar dentro do Python a pasta onde estão os PDFs a serem analisados. A saída é um arquivo CSV separado por pipes. No Linux basta usar `python3 scanPDFs.py > meusComprovantesPDF.csv`
