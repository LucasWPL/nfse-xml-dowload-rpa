# RPA para Download de NFS-e

Este projeto automatiza o login no portal nacional da NFS-e e faz o download dos arquivos disponíveis em "Notas Emitidas" usando Selenium com Python.

O fluxo foi ajustado para o comportamento atual do portal, que limita a consulta por períodos curtos. Em vez de depender apenas da paginação antiga, o script agora:

- consulta o histórico em janelas de até 30 dias;
- percorre os meses sequencialmente, o que atende melhor ao cenário de uma nota por mês;
- coleta os links de download da tela antes de iniciar os downloads;
- organiza os arquivos em pastas no formato `ANO/xml` e `ANO/pdf`.

## Estrutura

O projeto foi separado em módulos para facilitar manutenção e evolução:

- `main.py`: orquestração da execução
- `desktop_app.py`: interface desktop local em `tkinter`
- `src/config.py`: leitura de configuração e cálculo do período
- `src/logger.py`: logs normal/debug
- `src/browser.py`: setup do Chrome/Selenium
- `src/portal_client.py`: login, navegação, filtro e coleta dos downloads
- `src/download_service.py`: espera do download, deduplicação e organização dos arquivos
- `src/workflow.py`: processamento de cada janela de consulta

## Requisitos

- Python 3.x
- `pip`
- Google Chrome instalado
- `tkinter` disponível no Python se você for usar a interface desktop

## Instalação

```bash
git clone https://github.com/LucasWPL/nfse-xml-dowload-rpa.git
cd nfse-xml-dowload-rpa
pip install -r requirements.txt
```

Crie um arquivo `.env` com base no `.env.example`.

## Variáveis de ambiente

- `NFSE_USERNAME`: CPF/CNPJ ou inscricao usada no portal
- `NFSE_PASSWORD`: senha do portal
- `DOWNLOAD_PATH`: pasta base onde os arquivos serão organizados
- `START_DATE`: data inicial da busca no formato `YYYY-MM-DD`
- `END_DATE`: data final da busca no formato `YYYY-MM-DD`; se vazio, usa a data de hoje
- `MONTHS_BACK`: usado apenas quando `START_DATE` não for informado
- `MAX_PERIOD_DAYS`: limite da janela de consulta; mantenha `30`
- `WAIT_TIMEOUT`: timeout das esperas do Selenium
- `HEADLESS`: `true` ou `false`
- `DEBUG`: `true` ou `false`; quando ativo, mostra logs detalhados de campos e botões encontrados

Evite usar `USERNAME` no `.env`, porque esse nome costuma existir no ambiente do sistema Linux. O projeto passou a priorizar `NFSE_USERNAME` e `NFSE_PASSWORD`.

## Como usar

```bash
python3 main.py
```

Para abrir a interface desktop:

```bash
python3 desktop_app.py
```

Ou:

```bash
make run-app
```

Para executar em modo debug:

```bash
DEBUG=true python3 main.py
```

Exemplo de saída esperada:

```text
/seu/download/2024/xml/nota-123.xml
/seu/download/2024/pdf/nota-123.pdf
```

## Observações

- O script tenta localizar os campos de data e o botão de consulta de forma tolerante, usando vários seletores.
- Se o portal alterar nomes de campos ou estrutura visual novamente, os seletores de `src/portal_client.py` podem precisar de ajuste.
- Quando a data da nota não puder ser inferida pelo texto exibido na tela, o arquivo será salvo no ano da janela consultada.
- A interface desktop roda localmente e faz uma execução por vez.
- Em algumas distros Linux, talvez você precise instalar `python3-tk` para abrir a interface desktop.
- Se depois você quiser empacotar como executável, o caminho natural é usar `PyInstaller` sobre `desktop_app.py`.
