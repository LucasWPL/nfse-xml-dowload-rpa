# RPA para Download de XML de NFS-e 🔄📜

Este projeto automatiza o processo de login e download de arquivos XML de Notas Fiscais de Serviços Eletrônicas (NFSe) usando Selenium WebDriver e Python. O código navega pelas páginas de "Notas Emitidas" e realiza o download dos arquivos XML de cada registro disponível, enquanto lida com paginação e verificações para mensagens como "Nenhum registro encontrado".

**⚠️ Importante**: Para realizar o login com sucesso, é necessário ter um cadastro no [Portal do Contribuinte](https://www.nfse.gov.br/EmissorNacional/Login) e usar as credenciais corretas (inscrição e senha).

## Requisitos 🛠️

Antes de executar o código, você precisa ter o seguinte instalado em seu sistema:

- Python 3.x
- [pip](https://pip.pypa.io/en/stable/) para gerenciar pacotes Python

## Instalação ⚙️

1. Clone este repositório:

   ```bash
   git clone https://github.com/LucasWPL/nfse-xml-dowload-rpa.git
   cd nfse-xml-dowload-rpa
   ```

2. Instale as dependências
```bash
pip install -r requirements.txt
```

3. Crie um arquivo .env usando como base o .env.example 📑

## Como usar ▶️
Executando o script: Após configurar as variáveis de ambiente e instalar as dependências, basta rodar o script principal.

```bash
python3 main.py
```
O script irá:

- 🔐 Realizar login no sistema de NFSe com as credenciais fornecidas.
- 📄 Navegar pelas páginas de "Notas Emitidas" e buscar links para download.
- ⬇️ Baixar os arquivos XML dos links encontrados.
- 🔄 Continuar a navegação e o download até que não haja mais registros ou até encontrar a mensagem de "Nenhum registro encontrado".
