# Como Usar — Ferramenta de Coleta APIB/ATL

## O que este programa faz

Este programa coleta automaticamente os posts do perfil @apiboficial no Instagram desde janeiro de 2019, focando em publicações sobre o ATL (Acampamento Terra Livre). Os posts são salvos num banco de dados local, onde você pode pesquisar por palavras-chave, adicionar anotações, ver gráficos e exportar os dados para CSV ou Excel.

## Instalação (fazer só uma vez)

1. Certifique-se de ter Python instalado (versão 3.10 ou mais nova)
2. Clique duas vezes em `install.bat`
3. Aguarde a instalação terminar (pode demorar alguns minutos)

## Como iniciar o programa

1. Clique duas vezes em `run.bat`
2. O navegador abrirá automaticamente com a interface do programa
3. Se não abrir, acesse: http://localhost:8501

## Como fazer a coleta de posts

1. No menu lateral, clique em "📥 Coleta"
2. Clique no botão "Iniciar Coleta"
3. **Na primeira vez:** o programa vai fazer login automaticamente no Instagram — isso pode demorar alguns segundos. Não feche a janela.
4. **Nas próximas vezes:** o login é automático e instantâneo (sessão salva)
5. A coleta pode demorar várias horas — o programa está coletando posts desde 2019
6. Você pode fechar e reabrir: posts já coletados não serão duplicados

## O que fazer se aparecer erro de login

- Verifique se o computador está conectado à internet
- Se o Instagram pediu verificação por email, acesse o email da conta e confirme
- Depois de confirmar, clique em "Iniciar Coleta" novamente

## O que fazer se a coleta parar no meio

- Clique em "Iniciar Coleta" novamente — ela vai continuar de onde parou (sem duplicar)

## O que fazer se o Chrome abrir (versão antiga)

> Esta versão **não usa mais o Chrome**. Se isso acontecer, o programa está desatualizado.
> Feche tudo, abra o terminal na pasta do projeto e rode:
> ```
> git pull
> install.bat
> ```

## Seções do programa

- **📥 Coleta** — Coleta os posts do Instagram
- **🔍 Explorar Posts** — Pesquisa por palavras-chave e período
- **📝 Anotações** — Adiciona notas e categorias aos posts
- **📊 Dashboard** — Gráficos e estatísticas
- **💾 Exportar** — Exporta para CSV ou Excel

## Palavras-chave pré-definidas

ATL, Acampamento Terra Livre, ATL 2019, ATL 2020, ATL 2021, ATL 2022, ATL 2023, ATL 2024, ATL 2025

## Dúvidas frequentes

**Quantos posts serão coletados?**
Todos os posts do @apiboficial desde janeiro de 2019.

**A coleta é segura para a conta do Instagram?**
Sim. O programa usa intervalos aleatórios entre as requisições para não sobrecarregar o Instagram.

**O banco de dados fica onde?**
Na pasta `data/apib_posts.db` dentro do projeto. Não delete essa pasta.

**Posso usar o computador enquanto coleta?**
Sim. A coleta roda em segundo plano no navegador.

