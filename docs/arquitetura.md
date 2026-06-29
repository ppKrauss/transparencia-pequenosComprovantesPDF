# Arquitetura proposta

Este projeto nasce como um conjunto de scripts de apoio para reconhecer padrões de
comprovantes bancários brasileiros. As pastas `comprovantes1/` e `resolvido/`
devem ser tratadas como amostragens de calibração: elas ajudam a criar,
comparar e validar padrões de formatos de comprovantes, com foco em identificar
a instituição financeira usada no pagamento.

## Organização incremental do repositório

A estrutura atual deve evoluir sem quebrar o uso dos scripts existentes. Uma
organização sugerida é:

```text
.
├── docs/                 # arquitetura, formatos, guias de contribuição
├── src/                  # módulos Python quando os scripts forem empacotados
├── data/                 # metadados, amostras anonimizadas e inventários
│   └── _out/             # extrações, relatórios e comprovantes de integridade
├── tests/                # testes automatizados e fixtures pequenas
├── demo/                 # planilhas e saídas demonstrativas
├── scanPDFs.py           # entrada atual para PDFs textuais
└── scanIMGs.py           # entrada atual para imagens/OCR
```

Enquanto a refatoração para `src/` não acontece, os scripts da raiz continuam
funcionando como pontos de entrada estáveis.

## Módulos do sistema

### Scan

Responsável por localizar e inventariar entradas. Deve aceitar pasta, múltiplas
pastas e ZIP, preservando metadados úteis como nome original, data estimada de
origem, data do arquivo, tamanho e hashes.

Funções esperadas:

- percorrer lotes de arquivos;
- gerar inventário inicial;
- preservar SHA1 ou SHA256 como apoio à recuperação e preservação digital;
- registrar arquivos ignorados, pendentes e resolvidos;
- permitir movimentação ou marcação de "resolvidos" sem perder histórico;
- oferecer configuração amigável por CLI e, futuramente, por arquivo.

### Extract

Responsável por extrair representações dos documentos. PDFs textuais, OCR,
ícones, imagens de página e hashes de semelhança pertencem a este módulo.

Funções esperadas:

- extrair texto nativo de PDF;
- executar OCR em imagens ou páginas renderizadas;
- complementar PDF com OCR quando o texto nativo for insuficiente;
- salvar resultados intermediários em pasta própria;
- evitar reprocessamento caro;
- permitir uso de OCR externo quando o nativo não bastar.

### TextPatterns

Responsável por reconhecer frases, sequências de linhas e templates por emissor.
É a peça central para colaboração comunitária.

Funções esperadas:

- organizar padrões por instituição financeira;
- associar padrões a `template-ano`;
- manter regras separadas para PDF e OCR quando necessário;
- reaproveitar frases e sequencialidade comum entre PDF e OCR;
- permitir contribuição, revisão e testes de padrões por diferentes pessoas e IAs.

### Output

Responsável por gerar relatórios e arquivos finais.

Funções esperadas:

- gerar CSV simples e previsível;
- gerar planilhas Excel completas com Pandas;
- incluir abas de auditoria, como texto OCR bruto;
- consolidar erros, pendências e campos extraídos;
- manter schema centralizado para evitar divergência entre módulos.

## Compatibilidade com práticas Digital-Guard

Os repositórios da Digital-Guard tendem a separar documentação, dados e
código-fonte em camadas explícitas. Em `preserv-BR`, por exemplo, a organização
pública usa `data/`, `docs/` e `src/`, com dados de saída em `data/_out`.

Para este projeto, a adaptação mais importante é distinguir:

- código-fonte reutilizável;
- amostras anonimizadas e inventários em `data/`;
- resultados derivados em `data/_out`;
- documentação de formatos e decisões;
- inventários com hashes e metadados.

Essa separação ajuda a manter rastreabilidade sem misturar corpus sensível,
artefatos gerados e lógica de extração.

## Próximos passos recomendados

1. Criar fixtures anonimizadas pequenas em `data/samples/` ou `tests/fixtures/`.
2. Definir schema comum de saída para PDF e OCR.
3. Separar padrões por emissor em arquivos próprios.
4. Criar testes de TextPatterns usando textos extraídos anonimizados.
5. Migrar gradualmente lógica reutilizável para `src/`.
6. Manter os scripts da raiz como wrappers durante a transição.
