import time
import os
from datetime import datetime

# Importa os módulos do pacote 'scripts'
from scripts.config import HTML_OUTPUT_PATH, TIMEZONE_LOCAL
from scripts.news_fetcher import fetch_geopolitics_news
from scripts.data_adapter import adapt_api_data
from scripts.news_clusterer import cluster_news_by_event, embedding_model # Importa o modelo já carregado
from scripts.html_generator import generate_page_html

def write_html_file(html_content, output_path):
    """Escreve o conteúdo HTML no arquivo de saída especificado."""
    # Esta função simples pode ficar aqui ou ir para um utils.py
    try:
        # Garante que o diretório de saída exista (caso output_path inclua pastas)
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

def run_pipeline():
    """Executa o pipeline completo de atualização do site."""
    start_time = time.time()
    print(f"\n[{datetime.now(TIMEZONE_LOCAL).isoformat()}] Iniciando pipeline de atualização...")
    print("=" * 60)

    # Etapa 0: Verificar se o modelo de embedding carregou (verificação extra)
    if embedding_model is None:
         print(" ERRO CRÍTICO: Modelo de Embedding não está carregado. Abortando pipeline. ")
         print(" Verifique os logs de inicialização em scripts/news_clusterer.py")
         print("=" * 60)
         return

    # Etapa 1: Buscar Notícias
    print("\n--- Etapa 1: Buscando Notícias ---")
    api_articles = fetch_geopolitics_news()
    if api_articles is None: # Erro grave na busca
        print("Erro crítico na busca de notícias. Abortando.")
        return
    print("-" * 30)

    # Etapa 2: Adaptar Dados
    print("\n--- Etapa 2: Adaptando Dados ---")
    noticias_adaptadas = adapt_api_data(api_articles)
    print("-" * 30)

    # Etapa 3: Clusterizar Notícias
    print("\n--- Etapa 3: Clusterizando Notícias ---")
    clusters = cluster_news_by_event(noticias_adaptadas)
    if clusters is None: # Erro grave no clustering
        print("Erro crítico no clustering de notícias. Abortando.")
        return
    print("-" * 30)

    # Etapa 4: Gerar HTML
    print("\n--- Etapa 4: Gerando HTML ---")
    html_completo = generate_page_html(clusters)
    print("-" * 30)

    # Etapa 5: Escrever Arquivo HTML
    print("\n--- Etapa 5: Escrevendo Arquivo HTML ---")
    success = write_html_file(html_completo, HTML_OUTPUT_PATH)
    print("-" * 30)

    end_time = time.time()
    print(f"[{datetime.now(TIMEZONE_LOCAL).isoformat()}] Pipeline finalizado em {end_time - start_time:.2f} segundos.")
    print("=" * 60)
    if not success:
        print("ATENÇÃO: Ocorreu um erro ao escrever o arquivo HTML final.")

if __name__ == "__main__":
    # Verifica se as dependências cruciais podem ser importadas (checa instalação)
    try:
        import pytz
        import requests
        from dotenv import load_dotenv
        import numpy
        from sentence_transformers import SentenceTransformer
        from sklearn.cluster import AgglomerativeClustering
        print("Verificação inicial de dependências: OK")
    except ImportError as e:
        print("="*60 + f"\n ERRO DE DEPENDÊNCIA: {e} ".center(60, "="))
        print("Verifique se o venv está ativo e se rodou 'pip install -r requirements.txt'.")
        print("Pode ser necessário instalar PyTorch separadamente.")
        print("="*60)
        exit(1)

    run_pipeline() # Chama a função que executa o pipeline