# ibovespa_data

## Visao Geral
Projeto voltado a reunir, padronizar e explorar dados historicos do Ibovespa obtidos na B3, preparando uma base consistente para analises quantitativas, automatizacoes e publicacao de resultados.

## Pre-requisitos
- Python 3.10 ou superior
- Gerenciador de pacotes `pip` (ou equivalente, como `pipx` ou `poetry`)
- Conexao estavel com a internet para baixar arquivos da B3

## Estrutura de Pastas
```
ibovespa_data/
|-- data/
|   |-- cotahist/
|   `-- ibov_carteiras/
|-- docs/
|-- out/
|-- src/
`-- tests/
```

## Como baixar dados da B3
### Arquivos COTAHIST
1. Acesse https://www.b3.com.br e navegue ate Produtos e Servicos > Acoes > Dados de Mercado.
2. Localize a secao de Historico de negociacoes (arquivos COTAHIST) e selecione o periodo desejado (diario, mensal ou anual).
3. Baixe os arquivos `.zip` correspondentes e extraia o conteudo para `data/cotahist/`, mantendo a nomeacao original.

### Carteiras do Ibovespa
1. Na pagina da B3, acesse Indices > Carteiras de indices.
2. Escolha a opcao Ibovespa e selecione a carteira (vigente ou historica) que deseja baixar.
3. Baixe o arquivo `.xlsx` ou `.csv` disponibilizado e salve em `data/ibov_carteiras/`, organizando por data de validade quando desejar.

## Observacoes sobre carteiras
- Os arquivos em `data/ibov_carteiras` estao padronizados com o cabecalho `Codigo,Acao,Tipo,Qtde Teorica,Part %`.
- A carteira `IBOV_2022-09-02_2022-12-02.csv` replica os valores de `IBOV_2022-05-02_2022-08-02.csv` ate que seja encontrada uma fonte oficial para o periodo.

## Roteiro de Uso (5 passos)
1. Baixar: obtenha os arquivos brutos da B3 e armazene em `data/`.
2. Parsear: desenvolva scripts em `src/` para ler e transformar os arquivos em estruturas tabulares padronizadas.
3. Cruzar: combine informacoes de cotacao e composicao de carteira para gerar tabelas analiticas.
4. Validar: implemente testes em `tests/` e checagens automatizadas para garantir a qualidade dos dados.
5. Exportar: gere relatorios, dashboards ou datasets finais e grave em `out/` para consumo posterior.

## Tarefas Makefile
- `make setup`: instala dependencias (requirements + ruff)
- `make lint`: executa ruff em `src/` e `tests/`
- `make test`: roda a suite de testes (`pytest -q`)
- `make build`: gera o CSV consolidado via `python src/cli.py build`
- `make validate`: executa validacoes sobre o CSV gerado (`python src/cli.py validate`)

## Volume das Saidas
- A coluna `volume` traz o volume financeiro em R$ quando o pipeline roda com `--volume-field volume_brl`.
- Use `--volume-field volume_shares` para gravar a quantidade negociada (QUATOT) mantendo a coluna `volume`.

## Exemplo de Execucao
1. `make setup`
2. Copie arquivos de exemplo para as pastas de entrada:
   - `cp tests/fixtures/cotahist_sample.txt data/cotahist/COTAHIST.EXAMPLE.TXT`
   - `cp tests/fixtures/IBOV_2025-09-02_2026-01-02.csv data/ibov_carteiras/`
3. `make build`
4. `make validate`
5. `python -c "import pandas as pd; print(pd.read_csv('out/ibov_b3.csv').head().to_string(index=False))"`

Preview gerado a partir dos arquivos de exemplo:
```
      date asset   close     volume
2025-09-03 ITUB4 34567.0  6222060.0
2025-09-02 PETR4 12345.0  1851750.0
2025-09-02 VALE3 98765.0 19753000.0
```

## Uso dos Dados
- Baixe os arquivos diretamente das fontes oficiais da B3 para garantir atualizacoes e cumprimento das politicas de uso.
- Os exemplos e scripts sao indicados para uso interno e fins de estudo.
- Para redistribuicao, comercializacao ou publicacao de market data, consulte as licencas e termos vigentes da B3 e demais provedores.

## Pre-commit
- `pip install pre-commit`
- `pre-commit install`
- `pre-commit run --all-files` (opcional para validar tudo de uma vez)
