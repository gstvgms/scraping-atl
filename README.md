# Scraping ATL — Coleta de Posts da APIB no Instagram

Ferramenta de pesquisa acadêmica para coleta e análise de publicações do Instagram da **APIB** (@apiboficial) desde 2019, com foco em posts relacionados ao **ATL (Acampamento Terra Livre)**.

Desenvolvida para auxiliar pesquisadoras com pouca experiência técnica na análise de dados para dissertações e trabalhos acadêmicos.

---

## Requisitos

- **Python 3.10 ou superior**
- **pip** (gerenciador de pacotes do Python, normalmente já vem instalado com o Python)
- Conexão com a internet
- Uma conta no Instagram para autenticação (já configurada em `config.py`)

---

## Instalação (Windows)

1. **Baixe e instale o Python 3.10+** em [python.org/downloads](https://www.python.org/downloads/).
   - Durante a instalação, marque a opção **"Add Python to PATH"**.

2. **Baixe o projeto** clicando em "Code → Download ZIP" no GitHub, e extraia a pasta.

3. **Abra o Prompt de Comando** (tecle `Win + R`, digite `cmd` e pressione Enter).

4. **Navegue até a pasta do projeto**:
   ```
   cd C:\caminho\para\scraping-atl
   ```

5. **Instale as dependências**:
   ```
   pip install -r requirements.txt
   ```

---

## Como usar

### 1. Coletar posts do Instagram

Execute o coletor no Prompt de Comando:

```
python collector.py
```

O coletor irá:
- Fazer login na conta de pesquisa configurada em `config.py`
- Baixar todos os posts da @apiboficial a partir de 01/01/2019
- Salvar os dados no banco local em `data/apib_posts.db`
- Mostrar o progresso no terminal

> **Atenção:** A coleta pode levar bastante tempo (horas) dependendo do número de posts. Deixe o computador ligado e conectado à internet.

### 2. Acessar a interface de análise *(Sprint 2 — em breve)*

```
streamlit run app.py
```

A interface permitirá buscar posts por palavra-chave, filtrar por data, visualizar gráficos e adicionar anotações.

---

## Aviso de uso responsável

Esta ferramenta é destinada **exclusivamente para fins de pesquisa acadêmica**.

- Respeite os [Termos de Uso do Instagram](https://help.instagram.com/581066165581870).
- Não utilize para fins comerciais ou para coletar dados de pessoas sem consentimento.
- O uso de pausas automáticas entre requisições (`time.sleep`) está implementado para respeitar os limites da plataforma.

---

## Sprints

### ✅ Sprint 1 — Estrutura base e coleta de dados
- `requirements.txt` — dependências do projeto
- `config.py` — configurações centrais (perfil, datas, palavras-chave)
- `database.py` — banco SQLite local com funções de inserção e consulta
- `collector.py` — coleta autenticada de posts via instaloader
- `.gitignore` — arquivos a ignorar no controle de versão
- `data/.gitkeep` — pasta para armazenar o banco local

### 🔜 Sprint 2 — Interface de análise (Streamlit)
- `app.py` — interface web para busca, filtragem, anotações e exportação
- Visualizações gráficas por ano e tipo de post
- Exportação para Excel (.xlsx)
