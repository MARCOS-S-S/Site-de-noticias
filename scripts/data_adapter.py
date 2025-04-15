def adapt_api_data(api_articles):
    """Adapta os dados da NewsAPI para o formato interno, incluindo idioma."""
    adapted_news = []
    if not api_articles:
        print("Nenhum artigo recebido para adaptar.")
        return adapted_news

    print(f"Adaptando {len(api_articles)} artigos únicos...")
    count_adapted = 0
    count_skipped = 0
    for article in api_articles:
        title = article.get('title')
        url = article.get('url')
        source_name = article.get('source', {}).get('name')
        lang = article.get('search_language', 'N/A')
        description = article.get('description')

        # Validação mais rigorosa para pular artigos de baixa qualidade
        if not title or not url or not source_name or title == '[Removed]' or len(title) < 20 or not description or len(description) < 30:
            count_skipped += 1
            continue # Pula se título/url/fonte ausente, título removido/curto, ou descrição ausente/curta

        adapted_news.append({
            "title": title.strip(),
            "summary": description.strip(),
            "language": lang,
            "sources": [{"label": source_name, "url": url}] # Mantém a estrutura original de sources por enquanto
        })
        count_adapted += 1

    print(f"{count_adapted} artigos adaptados com sucesso.")
    if count_skipped > 0:
        print(f"{count_skipped} artigos pulados devido a dados ausentes ou insuficientes.")
    return adapted_news