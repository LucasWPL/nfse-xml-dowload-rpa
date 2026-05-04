# RPA para Download de NFS-e

Este projeto automatiza o login no portal nacional da NFS-e e faz o download dos arquivos disponiveis em "Notas Emitidas" usando Selenium com Python.

O fluxo foi ajustado para o comportamento atual do portal, que limita a consulta por periodos curtos. Em vez de depender apenas da paginacao antiga, o script agora:

- consulta o historico em janelas de ate 30 dias;
- percorre os meses sequencialmente, o que atende melhor ao cenario de uma nota por mes;
- coleta os links de download da tela antes de iniciar os downloads;
- organiza os arquivos em pastas no formato `ANO/xml` e `ANO/pdf`.

## Estrutura

O projeto foi separado em modulos para facilitar manutencao e evolucao:

- `main.py`: orquestracao da execucao
- `src/config.py`: leitura de configuracao e calculo do periodo
- `src/logger.py`: logs normal/debug
- `src/browser.py`: setup do Chrome/Selenium
- `src/portal_client.py`: login, navegacao, filtro e coleta dos downloads
- `src/download_service.py`: espera do download, deduplicacao e organizacao dos arquivos
- `src/workflow.py`: processamento de cada janela de consulta

## Requisitos

- Python 3.x
- `pip`
- Google Chrome instalado

## Instalacao

```bash
git clone https://github.com/LucasWPL/nfse-xml-dowload-rpa.git
cd nfse-xml-dowload-rpa
pip install -r requirements.txt
```

Crie um arquivo `.env` com base no `.env.example`.

## Variaveis de ambiente

- `NFSE_USERNAME`: CPF/CNPJ ou inscricao usada no portal
- `NFSE_PASSWORD`: senha do portal
- `DOWNLOAD_PATH`: pasta base onde os arquivos serao organizados
- `START_DATE`: data inicial da busca no formato `YYYY-MM-DD`
- `END_DATE`: data final da busca no formato `YYYY-MM-DD`; se vazio, usa a data de hoje
- `MONTHS_BACK`: usado apenas quando `START_DATE` nao for informado
- `MAX_PERIOD_DAYS`: limite da janela de consulta; mantenha `30`
- `WAIT_TIMEOUT`: timeout das esperas do Selenium
- `HEADLESS`: `true` ou `false`
- `DEBUG`: `true` ou `false`; quando ativo, mostra logs detalhados de campos e botoes encontrados

Evite usar `USERNAME` no `.env`, porque esse nome costuma existir no ambiente do sistema Linux. O projeto passou a priorizar `NFSE_USERNAME` e `NFSE_PASSWORD`.

## Como usar

```bash
python3 main.py
```

Para executar em modo debug:

```bash
DEBUG=true python3 main.py
```

Exemplo de saida esperada:

```text
/seu/download/2024/xml/nota-123.xml
/seu/download/2024/pdf/nota-123.pdf
```

## Observacoes

- O script tenta localizar os campos de data e o botao de consulta de forma tolerante, usando varios seletores.
- Se o portal alterar nomes de campos ou estrutura visual novamente, os seletores de `src/portal_client.py` podem precisar de ajuste.
- Quando a data da nota nao puder ser inferida pelo texto exibido na tela, o arquivo sera salvo no ano da janela consultada.
