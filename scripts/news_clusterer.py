import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import AgglomerativeClustering
# Importa configurações do mesmo pacote
from .config import EMBEDDING_MODEL_NAME, CLUSTER_DISTANCE_THRESHOLD

# --- Carregar Modelo de Embedding (nível do módulo) ---
print(f"Carregando modelo de embedding: '{EMBEDDING_MODEL_NAME}'...")
embedding_model = None
try:
    device = 'cuda'
    try:
        import torch
        if not torch.cuda.is_available(): device = 'cpu'
    except ImportError: device = 'cpu'
    embedding_model = SentenceTransformer(EMBEDDING_MODEL_NAME, device=device)
    print(f"Modelo carregado. Usando device: {embedding_model.device}")
except Exception as e:
    print(f"Erro CRÍTICO ao carregar modelo de embedding '{EMBEDDING_MODEL_NAME}': {e}")
    # embedding_model permanecerá None

def cluster_news_by_event(noticias):
    """Agrupa notícias baseadas na similaridade semântica."""
    if embedding_model is None:
        print("Erro: Modelo de embedding não disponível para clustering.")
        return None # Retorna None se o modelo não carregou
    if not noticias:
        print("Nenhuma notícia para clusterizar.")
        return []

    print(f"\nIniciando clustering de {len(noticias)} notícias...")
    # Usar Título + Resumo para embeddings
    texts_to_embed = [f"{n.get('title', '')} [SEP] {n.get('summary', '')}" for n in noticias]

    print("Gerando embeddings...")
    try:
        embeddings = embedding_model.encode(texts_to_embed, show_progress_bar=True, normalize_embeddings=True)
        print(f"Embeddings gerados com shape: {embeddings.shape}")
    except Exception as e:
        print(f"Erro ao gerar embeddings: {e}")
        return None # Erro durante embedding

    print(f"Executando Agglomerative Clustering com distance_threshold={CLUSTER_DISTANCE_THRESHOLD}...")
    clustering = AgglomerativeClustering(
        n_clusters=None,
        metric='cosine',
        linkage='average',
        distance_threshold=CLUSTER_DISTANCE_THRESHOLD
    )

    try:
        labels = clustering.fit_predict(embeddings)
        n_clusters_found = clustering.n_clusters_ if hasattr(clustering, 'n_clusters_') else len(set(labels)) - (1 if -1 in labels else 0)
        print(f"Clustering concluído. Encontrados {n_clusters_found} clusters.")
    except Exception as e:
        print(f"Erro durante o clustering: {e}")
        return None # Erro durante clustering

    # Organiza as notícias em clusters
    clusters = {}
    for i, label in enumerate(labels):
        if label == -1: continue # Ignorar ruído se aplicável
        if label not in clusters: clusters[label] = []
        clusters[label].append(noticias[i])

    grouped_news = sorted(list(clusters.values()), key=len, reverse=True)
    final_clusters = [cluster for cluster in grouped_news if len(cluster) > 1]
    singletons = [item for cluster in grouped_news if len(cluster) == 1 for item in cluster]

    print(f"-> {len(final_clusters)} clusters com mais de 1 notícia.")
    print(f"-> {len(singletons)} notícias não agrupadas (singletons).")

    # Retorna a lista combinada: clusters reais + singletons como listas individuais
    return final_clusters + [[singleton] for singleton in singletons]