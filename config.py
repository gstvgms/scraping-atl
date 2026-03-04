# Configurações centrais do projeto de coleta de posts da APIB

# Conta Instagram usada para autenticação (conta criada exclusivamente para esta pesquisa)
# Nota: este repositório é privado; caso torne-se público, mova as credenciais para .env
INSTAGRAM_USERNAME = "pesquisas_teste_github"
INSTAGRAM_PASSWORD = "apib123456"

# Perfil alvo da coleta
TARGET_PROFILE = "apiboficial"

# Data de início da coleta (apenas posts a partir desta data)
START_DATE = "2019-01-01"

# Palavras-chave pré-definidas para filtro
DEFAULT_KEYWORDS = [
    "ATL",
    "Acampamento Terra Livre",
    "ATL 2019",
    "ATL 2020",
    "ATL 2021",
    "ATL 2022",
    "ATL 2023",
    "ATL 2024",
    "ATL 2025",
]

# Caminho do banco de dados local
DB_PATH = "data/apib_posts.db"

# Intervalo de espera (em segundos) entre posts coletados para evitar bloqueio por rate limiting
SLEEP_MIN = 3
SLEEP_MAX = 8
