import json
import os
from datetime import datetime, timedelta
import time  # Importar time para adicionar um pequeno delay
import pytz
import requests
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=dotenv_path)

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Define o fuso horário
try:
    TIMEZONE_BR = pytz.timezone('America/Sao_Paulo')
except pytz.exceptions.UnknownTimeZoneError:
    print("Erro: Fuso horário 'America/Sao_Paulo' desconhecido. Usando UTC.")
    TIMEZONE_BR = pytz.utc

# Caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_OUTPUT_PATH = os.path.join(BASE_DIR, 'index.html')

# --- CONSTANTES ---
# Lista de idiomas para buscar (códigos ISO 639-1)
LANGUAGES_TO_SEARCH = ['pt', 'en', 'es', 'fr', 'de']
# Número de artigos a pedir por idioma
ARTICLES_PER_LANG = 15 # Total ~75 artigos (15 * 5)


# --- Funções de Busca de Notícias (Modificada para Multi-idioma) ---

def fetch_geopolitics_news(api_key):
    """Busca notícias recentes sobre geopolítica em MÚLTIPLOS IDIOMAS usando a NewsAPI."""
    if not api_key:
        print("Erro: Chave da NewsAPI não configurada no arquivo .env")
        return None

    # Define o período de busca (ex: últimos 2 dias para mais resultados)
    current_time_local = datetime.now(TIMEZONE_BR)
    start_time_local = current_time_local - timedelta(days=2) # Aumentado para 2 dias

    # Converte para UTC e formata
    current_time_utc = current_time_local.astimezone(pytz.utc)
    start_time_utc = start_time_local.astimezone(pytz.utc)
    from_date_iso = start_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    to_date_iso = current_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    print(f"Buscando notícias (UTC) de {from_date_iso} até {to_date_iso}")
    print(f"Idiomas: {', '.join(LANGUAGES_TO_SEARCH)}")

    all_articles = [] # Lista para acumular artigos de todos os idiomas
    query = '"geopolitics" OR "international relations" OR "diplomacy" OR "international conflict" OR "geopolítica" OR "relações internacionais"' # Query mais ampla

    for lang_code in LANGUAGES_TO_SEARCH:
        print(f"\nBuscando em idioma: [{lang_code.upper()}]...")

        url = (f"https://newsapi.org/v2/everything?"
               f"q={query}&"
               f"from={from_date_iso}&"
               f"to={to_date_iso}&"
               f"language={lang_code}&" # Usa o código do idioma atual do loop
               f"sortBy=relevancy&" # Relevancy pode ser melhor para multi-idioma
               f"pageSize={ARTICLES_PER_LANG}&" # Pede N artigos para este idioma
               f"apiKey={api_key}")

        print(f"  URL: {url.replace(api_key, '***API_KEY***')}")

        try:
            response = requests.get(url, timeout=15) # Timeout um pouco maior
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok":
                articles_found = data.get("articles", [])
                print(f"  -> Encontrados: {len(articles_found)} artigos em [{lang_code.upper()}]")

                # Adiciona informação do idioma a cada artigo antes de guardar
                for article in articles_found:
                    article['search_language'] = lang_code # Guarda o idioma da busca

                all_articles.extend(articles_found) # Adiciona à lista geral
            else:
                print(f"  -> Erro da API NewsAPI [{lang_code.upper()}]: Status={data.get('status')}, Code={data.get('code')}, Message={data.get('message')}")

            # Pequeno delay para não sobrecarregar a API (especialmente no plano gratuito)
            time.sleep(0.5) # Espera meio segundo entre as chamadas

        except requests.exceptions.Timeout:
            print(f"  -> Erro: Timeout ao buscar notícias em [{lang_code.upper()}].")
            continue # Pula para o próximo idioma
        except requests.exceptions.RequestException as e:
            print(f"  -> Erro de conexão/requisição em [{lang_code.upper()}]: {e}")
            continue # Pula para o próximo idioma
        except Exception as e:
            print(f"  -> Erro inesperado em [{lang_code.upper()}]: {e}")
            continue # Pula para o próximo idioma

    print(f"\nBusca finalizada. Total de artigos coletados (bruto): {len(all_articles)}")
    # Opcional: Remover duplicatas baseadas na URL (se artigos idênticos aparecerem em buscas diferentes)
    unique_articles = {article['url']: article for article in all_articles}.values()
    print(f"Total de artigos únicos (por URL): {len(unique_articles)}")

    return list(unique_articles)


# --- Função de Adaptação (Modificada para incluir idioma) ---

def adapt_api_data(api_articles):
    """Adapta os dados da NewsAPI para o formato interno, incluindo idioma."""
    adapted_news = []
    if not api_articles:
        print("Nenhum artigo recebido para adaptar.")
        return adapted_news

    print(f"Adaptando {len(api_articles)} artigos únicos...")
    for article in api_articles:
        title = article.get('title')
        url = article.get('url')
        source_name = article.get('source', {}).get('name')
        lang = article.get('search_language', 'N/A') # Recupera o idioma guardado

        if not title or not url or not source_name or title == '[Removed]':
            # print(f"  -> Pulando artigo inválido/removido: Título='{title}', URL='{url}'")
            continue

        # Cria a estrutura da notícia no formato esperado
        noticia = {
            "title": title.strip(),
            "summary": article.get('description', '').strip() if article.get('description') else '',
            "language": lang, # Adiciona o código do idioma
            "sources": [
                {
                    "label": source_name,
                    "url": url
                }
            ]
        }
        adapted_news.append(noticia)

    print(f"{len(adapted_news)} artigos adaptados com sucesso.")
    # Opcional: Ordenar notícias (ex: por idioma, depois título)
    # adapted_news.sort(key=lambda x: (x['language'], x['title']))
    return adapted_news


# --- Funções de Geração de HTML (Modificada para mostrar idioma) ---

def generate_news_item_html(noticia):
    """Gera o bloco HTML para um único item de notícia, mostrando o idioma."""
    title = noticia.get('title', 'Título Indisponível')
    summary = noticia.get('summary', '')
    sources = noticia.get('sources', [])
    lang = noticia.get('language', '').upper() # Pega o idioma e coloca em maiúsculas

    item_html = f'    <article class="news-item lang-{lang.lower()}">\n' # Adiciona classe CSS com idioma
    # Mostra o idioma ao lado do título
    item_html += f'      <h3 class="news-title">{title} <span class="lang-indicator">[{lang}]</span></h3>\n'
    if summary:
        item_html += f'      <p class="news-summary">{summary}</p>\n'
    if sources:
        item_html += '      <div class="news-sources">\n'
        item_html += '        <h4>Fontes:</h4>\n'
        for source in sources:
            label = source.get('label', 'Fonte Desconhecida')
            url = source.get('url', '#')
            item_html += f'        <div class="source">\n'
            item_html += f'          <span class="source-label">{label}:</span>\n'
            item_html += f'          <a href="{url}" target="_blank" rel="noopener noreferrer" class="source-link">Ver artigo completo em {label}</a>\n'
            item_html += f'        </div>\n'
        item_html += '      </div>\n'
    else:
         item_html += '      <p><em>Nenhuma fonte disponível para esta notícia.</em></p>\n'
    item_html += '    </article>\n'
    return item_html

# Função generate_page_html permanece quase igual, apenas chama a generate_news_item_html modificada
def generate_page_html(noticias):
    """Gera o conteúdo HTML completo da página."""
    now_local = datetime.now(TIMEZONE_BR)
    update_date_str = now_local.strftime('%d/%m/%Y às %H:%M:%S %Z')
    current_year = now_local.year

    news_items_html = ""
    if noticias:
         # Ordena notícias por idioma antes de gerar o HTML (opcional)
         # noticias.sort(key=lambda x: (x.get('language', ''), x.get('title', '')))
         news_items_html = "\n".join([generate_news_item_html(noticia) for noticia in noticias])
    else:
         news_items_html = "    <p>Nenhuma notícia encontrada ou ocorreu um erro durante a busca.</p>"

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Notícias de geopolítica com múltiplas fontes e perspectivas.">
    <title>GeoNotícias - Perspectivas Múltiplas</title>
    <link rel="stylesheet" href="style.css">
    <style>
      .lang-indicator {{
        font-size: 0.8em;
        color: #777;
        font-weight: normal;
        margin-left: 5px;
      }}
    </style>
</head>
<body>
    <header class="site-header">
        <h1>GeoNotícias</h1>
        <p>Análise geopolítica com fontes diversificadas</p>
        <p style="font-size: 0.8em;">Notícias fornecidas por <a href="https://newsapi.org/" target="_blank" rel="noopener">NewsAPI.org</a></p>
        <p class="update-info">Atualizado em: <span id="update-date">{update_date_str}</span></p>
    </header>
    <main class="news-container">
        <h2>Notícias Globais Recentes</h2>
{news_items_html}
    </main>
    <footer class="site-footer">
        <p>&copy; <span id="current-year">{current_year}</span> GeoNotícias.</p>
        <p><a href="https://github.com/SEU_USUARIO/geopolitica-news" target="_blank" rel="noopener">Ver código no GitHub</a></p>
    </footer>
</body>
</html>"""
    return html_content

# Função write_html_file permanece inalterada
def write_html_file(html_content, output_path):
    """Escreve o conteúdo HTML no arquivo de saída especificado."""
    try:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Arquivo HTML gerado/atualizado com sucesso em: '{output_path}'")
        return True
    except IOError as e:
        print(f"Erro de I/O ao escrever o arquivo HTML em '{output_path}': {e}")
        return False
    except Exception as e:
        print(f"Erro inesperado ao escrever o arquivo HTML: {e}")
        return False

# --- Função Principal (sem alterações significativas) ---

def main():
    """Função principal: busca notícias multi-idioma, adapta, gera HTML e salva."""
    print(f"\n[{datetime.now(TIMEZONE_BR).isoformat()}] Iniciando processo de geração do site...")

    # 1. Buscar notícias da API (agora busca em múltiplos idiomas)
    print("-" * 30)
    api_articles = fetch_geopolitics_news(NEWSAPI_KEY)
    print("-" * 30)

    # 2. Adaptar os dados da API para o formato interno (incluindo idioma)
    noticias_adaptadas = adapt_api_data(api_articles)
    print("-" * 30)

    # 3. Gerar o conteúdo HTML completo da página (mostrando idioma)
    print("Gerando conteúdo HTML...")
    html_completo = generate_page_html(noticias_adaptadas)
    print("-" * 30)

    # 4. Escrever o HTML gerado no arquivo index.html
    print(f"Escrevendo arquivo em: {HTML_OUTPUT_PATH}")
    write_html_file(html_completo, HTML_OUTPUT_PATH)
    print("-" * 30)

    print(f"[{datetime.now(TIMEZONE_BR).isoformat()}] Processo finalizado.")


if __name__ == "__main__":
    # Verifica dependências
    try:
        import pytz
        import requests
        from dotenv import load_dotenv
    except ImportError as e:
        print("="*60 + "\n ERRO DE DEPENDÊNCIA ".center(60, "="))
        print(f"Erro ao importar biblioteca: {e}")
        print("Verifique se o venv está ativo e se rodou 'pip install -r requirements.txt'.")
        print("="*60)
        exit(1)

    main()