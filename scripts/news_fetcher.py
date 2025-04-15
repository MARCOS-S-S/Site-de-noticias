import requests
import time
from datetime import datetime, timedelta
# Importa configurações do mesmo pacote
from .config import NEWSAPI_KEY, LANGUAGES_TO_SEARCH, ARTICLES_PER_LANG, SEARCH_WINDOW_DAYS, NEWS_QUERY, TIMEZONE_LOCAL, pytz

def fetch_geopolitics_news():
    """Busca notícias recentes sobre geopolítica em múltiplos idiomas."""
    if not NEWSAPI_KEY:
        print("Erro Interno: Chave da NewsAPI não disponível no fetcher.")
        # A validação principal está no config.py, mas é bom checar.
        return None # Retorna None em caso de erro grave

    current_time_local = datetime.now(TIMEZONE_LOCAL)
    start_time_local = current_time_local - timedelta(days=SEARCH_WINDOW_DAYS)
    current_time_utc = current_time_local.astimezone(pytz.utc)
    start_time_utc = start_time_local.astimezone(pytz.utc)
    from_date_iso = start_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    to_date_iso = current_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    print(f"\nBuscando notícias (UTC) de {from_date_iso} até {to_date_iso}")
    print(f"Idiomas: {', '.join(LANGUAGES_TO_SEARCH)}")

    all_articles = []
    for lang_code in LANGUAGES_TO_SEARCH:
        print(f"\nBuscando em idioma: [{lang_code.upper()}]...")
        url = (f"https://newsapi.org/v2/everything?"
               f"q={NEWS_QUERY}&"
               f"from={from_date_iso}&to={to_date_iso}&"
               f"language={lang_code}&sortBy=relevancy&"
               f"pageSize={ARTICLES_PER_LANG}&apiKey={NEWSAPI_KEY}")

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok":
                articles_found = data.get("articles", [])
                print(f"  -> Encontrados: {len(articles_found)} artigos em [{lang_code.upper()}]")
                for article in articles_found:
                    article['search_language'] = lang_code
                all_articles.extend(articles_found)
            else:
                 print(f"  -> Erro da API NewsAPI [{lang_code.upper()}]: Status={data.get('status')}, Code={data.get('code')}, Message={data.get('message')}")
            time.sleep(0.5)
        except requests.exceptions.Timeout:
            print(f"  -> Erro: Timeout ao buscar notícias em [{lang_code.upper()}].")
        except requests.exceptions.RequestException as e:
            print(f"  -> Erro de conexão/requisição em [{lang_code.upper()}]: {e}")
        except Exception as e:
            print(f"  -> Erro inesperado em [{lang_code.upper()}]: {e}")

    print(f"\nBusca finalizada. Total de artigos coletados (bruto): {len(all_articles)}")
    # Remover duplicatas por URL (ignora artigos sem URL)
    unique_articles = list({article['url']: article for article in all_articles if article.get('url')}.values())
    print(f"Total de artigos únicos (por URL): {len(unique_articles)}")
    return unique_articles