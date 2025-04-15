import json
import os
from datetime import datetime, timedelta
import time  # Importar time para adicionar um pequeno delay
import pytz
import requests
from dotenv import load_dotenv
# Novas importações para Clustering
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
# from sklearn.metrics.pairwise import cosine_similarity # Usaremos distância pré-calculada
import numpy as np

# --- Configurações Iniciais ---

# Carrega variáveis do arquivo .env
dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=dotenv_path)

NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")

# Define o fuso horário
try:
    # Usando fuso horário de São Paulo como referência para 'local'
    # Ajuste conforme necessário para a relevância das suas notícias
    TIMEZONE_LOCAL = pytz.timezone('America/Sao_Paulo')
except pytz.exceptions.UnknownTimeZoneError:
    print("Aviso: Fuso horário 'America/Sao_Paulo' desconhecido. Usando UTC como local.")
    TIMEZONE_LOCAL = pytz.utc

# Caminhos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML_OUTPUT_PATH = os.path.join(BASE_DIR, 'index.html')

# --- Constantes Configuráveis ---
LANGUAGES_TO_SEARCH = ['pt', 'en', 'es', 'fr', 'de'] # Idiomas para buscar
ARTICLES_PER_LANG = 15 # Artigos por idioma (total bruto ~75)
SEARCH_WINDOW_DAYS = 2 # Janela de tempo para busca (ex: últimos 2 dias)
# Limiar de distância para clustering. MENOR = MAIS SIMILARIDADE EXIGIDA. Ajuste experimental!
CLUSTER_DISTANCE_THRESHOLD = 0.4 # Começar com 0.4 e ajustar (0.3 exige muita similaridade, 0.5 agrupa mais frouxamente)
EMBEDDING_MODEL_NAME = 'paraphrase-multilingual-mpnet-base-v2' # Modelo multilingual

# --- Carregar Modelo de Embedding (fora das funções para carregar só uma vez) ---
print(f"Carregando modelo de embedding: '{EMBEDDING_MODEL_NAME}' (pode levar tempo/baixar na 1ª vez)...")
embedding_model = None
try:
    # Tenta detectar se PyTorch com CUDA está disponível
    device = 'cuda'
    try:
        import torch
        if not torch.cuda.is_available():
            print("CUDA não disponível, usando CPU.")
            device = 'cpu'
    except ImportError:
        print("PyTorch não encontrado, usando CPU.")
        device = 'cpu'

    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
    print(f"Modelo carregado com sucesso. Usando device: {embedding_model.device}")
except Exception as e:
    print(f"Erro CRÍTICO ao carregar modelo de embedding '{EMBEDDING_MODEL_NAME}': {e}")
    print("O script não pode continuar sem o modelo.")
    # embedding_model permanecerá None

# --- Funções de Busca de Notícias (Multi-idioma) ---
def fetch_geopolitics_news(api_key):
    """Busca notícias recentes sobre geopolítica em MÚLTIPLOS IDIOMAS usando a NewsAPI."""
    if not api_key:
        print("Erro: Chave da NewsAPI não configurada no arquivo .env")
        return None

    current_time_local = datetime.now(TIMEZONE_LOCAL)
    start_time_local = current_time_local - timedelta(days=SEARCH_WINDOW_DAYS)

    current_time_utc = current_time_local.astimezone(pytz.utc)
    start_time_utc = start_time_local.astimezone(pytz.utc)
    from_date_iso = start_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
    to_date_iso = current_time_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    print(f"\nBuscando notícias (UTC) de {from_date_iso} até {to_date_iso}")
    print(f"Idiomas: {', '.join(LANGUAGES_TO_SEARCH)}")

    all_articles = []
    # Query um pouco mais ampla para cobrir variações linguísticas
    query = ('"geopolitics" OR "international relations" OR "diplomacy" OR "international conflict" OR "summit" OR '
             '"geopolítica" OR "relações internacionais" OR "diplomacia" OR "conflito internacional" OR "cúpula" OR '
             '"geopolitik" OR "internationale beziehungen" OR "diplomatie" OR "gipfel" OR '
             '"géopolitique" OR "relations internationales" OR "sommet" OR '
             '"geopolítica" OR "relaciones internacionales" OR "cumbre"')

    for lang_code in LANGUAGES_TO_SEARCH:
        print(f"\nBuscando em idioma: [{lang_code.upper()}]...")
        url = (f"https://newsapi.org/v2/everything?"
               f"q={query}&"
               f"from={from_date_iso}&to={to_date_iso}&"
               f"language={lang_code}&"
               f"sortBy=relevancy&" # Relevância pode ser melhor ao buscar em várias línguas
               f"pageSize={ARTICLES_PER_LANG}&"
               f"apiKey={api_key}")
        # print(f"  URL: {url.replace(api_key, '***API_KEY***')}") # Descomentar para debug

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "ok":
                articles_found = data.get("articles", [])
                print(f"  -> Encontrados: {len(articles_found)} artigos em [{lang_code.upper()}]")
                for article in articles_found:
                    article['search_language'] = lang_code # Guarda idioma da busca
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
    unique_articles = list({article['url']: article for article in all_articles if article.get('url')}.values()) # Remove duplicatas por URL
    print(f"Total de artigos únicos (por URL): {len(unique_articles)}")
    return unique_articles


# --- Função de Adaptação de Dados ---
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
        lang = article.get('search_language', 'N/A')
        description = article.get('description')

        if not title or not url or not source_name or title == '[Removed]' or len(title) < 15: # Pular títulos muito curtos ou removidos
            continue

        adapted_news.append({
            "title": title.strip(),
            "summary": description.strip() if description else '',
            "language": lang,
            "sources": [{"label": source_name, "url": url}]
        })
    print(f"{len(adapted_news)} artigos adaptados com sucesso.")
    return adapted_news


# --- Função de Clustering de Notícias ---
def cluster_news_by_event(noticias, model, distance_threshold=0.4):
    """Agrupa notícias baseadas na similaridade semântica dos títulos."""
    if not model:
        print("Erro: Modelo de embedding não disponível para clustering.")
        return None
    if not noticias:
        print("Nenhuma notícia para clusterizar.")
        return []

    print(f"\nIniciando clustering de {len(noticias)} notícias...")
    # Usaremos título + resumo para embeddings, pode dar resultados melhores
    texts_to_embed = [f"{n.get('title', '')} [SEP] {n.get('summary', '')}" for n in noticias]

    print("Gerando embeddings...")
    try:
        embeddings = model.encode(texts_to_embed, show_progress_bar=True, normalize_embeddings=True)
        # normalize_embeddings=True faz a normalização L2, ideal para cosine similarity
        print(f"Embeddings gerados com shape: {embeddings.shape}")
    except Exception as e:
        print(f"Erro ao gerar embeddings: {e}")
        return None

    print(f"Executando Agglomerative Clustering com distance_threshold={distance_threshold}...")
    # Como os embeddings estão normalizados, a distância Euclidiana ao quadrado é
    # monotonicamente relacionada à distância cosseno: dist_euc^2 = 2 * (1 - sim_cos)
    # Podemos usar 'euclidean' e ajustar o threshold, ou 'cosine' diretamente.
    # Usar 'cosine' é mais direto semanticamente.
    clustering = AgglomerativeClustering(
        n_clusters=None, # Define clusters pelo threshold, não número fixo
        metric='cosine', # Usa distância cosseno (1 - similaridade)
        linkage='average', # Método de ligação entre clusters
        distance_threshold=distance_threshold
    )

    try:
        # O fit com 'cosine' calcula as distâncias internamente
        labels = clustering.fit_predict(embeddings)
        n_clusters = clustering.n_clusters_
        print(f"Clustering concluído. Encontrados {n_clusters} clusters.")
    except Exception as e:
        print(f"Erro durante o clustering: {e}")
        return None

    # Organiza as notícias em clusters
    clusters = {}
    for i, label in enumerate(labels):
        if label == -1: continue # Ignorar ruído se usar algoritmos como DBSCAN
        if label not in clusters: clusters[label] = []
        clusters[label].append(noticias[i])

    grouped_news = sorted(list(clusters.values()), key=len, reverse=True)
    final_clusters = [cluster for cluster in grouped_news if len(cluster) > 1]
    singletons = [item for cluster in grouped_news if len(cluster) == 1 for item in cluster]

    print(f"-> {len(final_clusters)} clusters com mais de 1 notícia.")
    print(f"-> {len(singletons)} notícias não agrupadas (singletons).")

    return final_clusters + [[singleton] for singleton in singletons]


# --- Funções de Geração de HTML ---
def generate_news_item_html(noticia):
    """Gera HTML para um item de notícia não agrupado (singleton)."""
    title = noticia.get('title', 'Título Indisponível')
    summary = noticia.get('summary', '')
    sources = noticia.get('sources', [])
    lang = noticia.get('language', '').upper()

    item_html = f'    <article class="news-item news-item-single lang-{lang.lower()}">\n'
    item_html += f'      <h3 class="news-title">{title} <span class="lang-indicator">[{lang}]</span></h3>\n'
    if summary:
        item_html += f'      <p class="news-summary">{summary}</p>\n'
    if sources:
        source = sources[0] # Singleton só tem uma fonte na lista
        label = source.get('label', 'Fonte Desconhecida')
        url = source.get('url', '#')
        item_html += '      <div class="news-sources">\n'
        item_html += f'        <div class="source"><a href="{url}" target="_blank" rel="noopener noreferrer" class="source-link">Ver artigo completo em {label}</a></div>\n'
        item_html += '      </div>\n'
    item_html += '    </article>\n'
    return item_html

def generate_grouped_event_html(cluster):
    """Gera HTML para um evento agrupado (cluster de notícias)."""
    if not cluster: return ""
    # Título representativo: Título da primeira notícia (poderia ser melhorado)
    group_title = cluster[0].get('title', 'Evento Agrupado')
    # Resumo representativo: Resumo da primeira notícia (poderia ser melhorado)
    group_summary = cluster[0].get('summary', '')
    group_lang_codes = sorted(list(set([n.get('language', '').upper() for n in cluster])))

    event_html = f'  <section class="news-event-grouped">\n'
    event_html += f'    <h3 class="event-title">{group_title} <span class="lang-indicator">[{", ".join(group_lang_codes)}]</span> ({len(cluster)} fontes)</h3>\n'
    if group_summary:
         event_html += f'    <p class="event-summary"><em>(Resumo de uma das fontes):</em> {group_summary}</p>\n'
    event_html += '    <div class="event-sources-list">\n'
    event_html += '      <h4>Fontes sobre este evento:</h4>\n'
    # Ordenar fontes dentro do cluster (opcional, ex: por idioma)
    # cluster.sort(key=lambda x: x.get('language', ''))
    for i, noticia in enumerate(cluster):
        source = noticia.get('sources', [{}])[0]
        label = source.get('label', 'Fonte Desconhecida')
        url = source.get('url', '#')
        lang = noticia.get('language', '').upper()
        item_title = noticia.get('title', '') # Título específico da fonte

        event_html += f'      <div class="source-item">\n'
        event_html += f'          <span class="source-label">{i+1}. {label} [{lang}]:</span>\n'
        # O title="" no link mostra o título específico ao passar o mouse
        event_html += f'          <a href="{url}" target="_blank" rel="noopener noreferrer" class="source-link" title="{item_title}">Ver artigo</a>\n'
        event_html += f'      </div>\n'
    event_html += '    </div>\n'
    event_html += '  </section>\n'
    return event_html

def generate_page_html(clusters_or_news):
    """Gera o conteúdo HTML completo da página a partir de clusters ou lista simples."""
    now_local = datetime.now(TIMEZONE_LOCAL)
    update_date_str = now_local.strftime('%d/%m/%Y às %H:%M:%S %Z')
    current_year = now_local.year
    items_html = ""

    if clusters_or_news:
        print(f"Gerando HTML para {len(clusters_or_news)} itens/clusters...")
        for item in clusters_or_news:
            if isinstance(item, list) and len(item) > 1:
                items_html += generate_grouped_event_html(item)
            elif isinstance(item, list) and len(item) == 1:
                items_html += generate_news_item_html(item[0])
            elif isinstance(item, dict): # Fallback se receber lista simples por erro
                 print("WARN: Recebeu dicionário em vez de lista de cluster, tratando como singleton.")
                 items_html += generate_news_item_html(item)
    else:
         items_html = "    <p>Nenhuma notícia encontrada ou ocorreu um erro durante o processamento.</p>"

    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Notícias de geopolítica agrupadas por evento e fontes.">
    <title>GeoNotícias - Eventos e Perspectivas</title>
    <link rel="stylesheet" href="style.css">
    <style>
      .lang-indicator {{ font-size: 0.8em; color: #777; font-weight: normal; margin-left: 5px; }}
      .news-event-grouped {{ border: 1px solid #bdd; background-color: #f0faff; padding: 15px; margin-bottom: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05); }}
      .event-title {{ margin-top: 0; margin-bottom: 10px; color: #2c3e50; font-size: 1.2em;}}
      .event-summary {{ font-size: 0.9em; color: #555; margin-bottom: 15px; border-left: 3px solid #bde; padding-left: 10px;}}
      .event-sources-list h4 {{ margin-bottom: 8px; font-size: 0.95em; color: #333; }}
      .source-item {{ margin-bottom: 6px; font-size: 0.9em; }}
      .news-item-single {{ border: 1px solid #eee; background-color: #fff; padding: 15px; margin-bottom: 20px; border-radius: 5px;}}
    </style>
</head>
<body>
    <header class="site-header">
        <h1>GeoNotícias</h1>
        <p>Análise geopolítica com fontes diversificadas e agrupadas por evento.</p>
        <p style="font-size: 0.8em;">Notícias fornecidas por <a href="https://newsapi.org/" target="_blank" rel="noopener">NewsAPI.org</a></p>
        <p class="update-info">Atualizado em: <span id="update-date">{update_date_str}</span></p>
    </header>
    <main class="news-container">
        <h2>Eventos Globais Recentes</h2>
{items_html}
    </main>
    <footer class="site-footer">
        <p>&copy; <span id="current-year">{current_year}</span> GeoNotícias.</p>
        <p><a href="https://github.com/SEU_USUARIO/geopolitica-news" target="_blank" rel="noopener">Ver código no GitHub</a> (Substitua pelo seu link)</p>
    </footer>
</body>
</html>"""
    return html_content

# --- Função de Escrita de Arquivo ---
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

# --- Função Principal ---
def main():
    """Função principal: busca, adapta, clusteriza, gera HTML e salva."""
    start_time = time.time()
    print(f"\n[{datetime.now(TIMEZONE_LOCAL).isoformat()}] Iniciando processo...")

    # Verifica se o modelo de embedding foi carregado antes de prosseguir
    if embedding_model is None:
         print("="*60 + "\n ERRO CRÍTICO: Modelo de Embedding não carregado. Abortando. ".center(60, "=") + "\n" + "="*60)
         return # Não continua sem o modelo

    # 1. Buscar notícias
    api_articles = fetch_geopolitics_news(NEWSAPI_KEY)
    print("-" * 30)

    # 2. Adaptar dados
    noticias_adaptadas = adapt_api_data(api_articles)
    print("-" * 30)

    # 3. Clusterizar notícias
    clusters = cluster_news_by_event(noticias_adaptadas, embedding_model, CLUSTER_DISTANCE_THRESHOLD)
    print("-" * 30)

    # 4. Gerar HTML a partir dos clusters (ou lista vazia se falhar)
    print("Gerando conteúdo HTML...")
    html_completo = generate_page_html(clusters if clusters is not None else [])
    print("-" * 30)

    # 5. Escrever arquivo HTML
    print(f"Escrevendo arquivo em: {HTML_OUTPUT_PATH}")
    write_html_file(html_completo, HTML_OUTPUT_PATH)
    print("-" * 30)

    end_time = time.time()
    print(f"[{datetime.now(TIMEZONE_LOCAL).isoformat()}] Processo finalizado em {end_time - start_time:.2f} segundos.")

# --- Bloco de Execução ---
if __name__ == "__main__":
    # Verifica dependências cruciais na execução
    try:
        import pytz
        import requests
        from dotenv import load_dotenv
        import numpy
        from sentence_transformers import SentenceTransformer
        from sklearn.cluster import AgglomerativeClustering
    except ImportError as e:
        print("="*60 + f"\n ERRO DE DEPENDÊNCIA: {e} ".center(60, "="))
        print("Verifique se o venv está ativo e se rodou 'pip install -r requirements.txt'.")
        print("Pode ser necessário instalar PyTorch separadamente.")
        print("="*60)
        exit(1)

    main()