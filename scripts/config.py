import os
import pytz
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env localizado na pasta raiz do projeto
# O __file__ aqui aponta para config.py, então subimos dois níveis
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Chave da API
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Fuso Horário de Referência Local
try:
    TIMEZONE_LOCAL = pytz.timezone('America/Sao_Paulo')
except pytz.exceptions.UnknownTimeZoneError:
    print("Aviso: Fuso horário 'America/Sao_Paulo' desconhecido. Usando UTC como local.")
    TIMEZONE_LOCAL = pytz.utc

# Parâmetros da Busca de Notícias
LANGUAGES_TO_SEARCH = ['pt', 'en', 'es', 'fr', 'de']
ARTICLES_PER_LANG = 15
SEARCH_WINDOW_DAYS = 2
NEWS_QUERY = (
    '"geopolitics" OR "international relations" OR "diplomacy" OR "international conflict" OR "summit" OR '
    '"geopolítica" OR "relações internacionais" OR "diplomacia" OR "conflito internacional" OR "cúpula" OR '
    '"geopolitik" OR "internationale beziehungen" OR "diplomatie" OR "gipfel" OR '
    '"géopolitique" OR "relations internationales" OR "sommet" OR '
    '"geopolítica" OR "relaciones internacionales" OR "cumbre"'
)

# Parâmetros de Clustering
CLUSTER_DISTANCE_THRESHOLD = 0.4 # Ajuste experimentalmente!
EMBEDDING_MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2'

# Caminho do Arquivo HTML de Saída (relativo à raiz do projeto)
HTML_OUTPUT_FILENAME = "index.html"
HTML_OUTPUT_PATH = os.path.join(BASE_DIR, HTML_OUTPUT_FILENAME)

# Validação básica da API Key
if not NEWSAPI_KEY:
    print("*"*60)
    print(" ERRO DE CONFIGURAÇÃO ".center(60, "*"))
    print(" A variável NEWSAPI_KEY não foi encontrada no arquivo .env")
    print(f" Verifique se o arquivo '{dotenv_path}' existe e contém a chave.")
    print("*"*60)
    # Poderia lançar uma exceção aqui para parar a execução
    # raise ValueError("NEWSAPI_KEY não configurada.")