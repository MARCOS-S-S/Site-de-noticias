from datetime import datetime
from .config import TIMEZONE_LOCAL

# Função para gerar HTML de item único (singleton)
def generate_news_item_html(noticia):
    title = noticia.get('title', 'Título Indisponível')
    summary = noticia.get('summary', '')
    sources = noticia.get('sources', [])
    lang = noticia.get('language', '').upper()

    item_html = f'    <article class="news-item news-item-single lang-{lang.lower()}">\n'
    item_html += f'      <h3 class="news-title">{title} <span class="lang-indicator">[{lang}]</span></h3>\n'
    if summary:
        item_html += f'      <p class="news-summary">{summary}</p>\n'
    if sources:
        source = sources[0]
        label = source.get('label', 'Fonte Desconhecida')
        url = source.get('url', '#')
        item_html += '      <div class="news-sources">\n'
        item_html += f'        <div class="source"><a href="{url}" target="_blank" rel="noopener noreferrer" class="source-link">Ver artigo completo em {label}</a></div>\n'
        item_html += '      </div>\n'
    item_html += '    </article>\n'
    return item_html

# Função para gerar HTML de evento agrupado (cluster)
def generate_grouped_event_html(cluster):
    if not cluster: return ""
    group_title = cluster[0].get('title', 'Evento Agrupado')
    group_summary = cluster[0].get('summary', '')
    group_lang_codes = sorted(list(set([n.get('language', '').upper() for n in cluster])))

    event_html = f'  <section class="news-event-grouped">\n'
    event_html += f'    <h3 class="event-title">{group_title} <span class="lang-indicator">[{",".join(group_lang_codes)}]</span> ({len(cluster)} fontes)</h3>\n'
    if group_summary:
         event_html += f'    <p class="event-summary"><em>(Resumo de uma das fontes):</em> {group_summary}</p>\n'
    event_html += '    <div class="event-sources-list">\n'
    event_html += '      <h4>Fontes sobre este evento:</h4>\n'
    for i, noticia in enumerate(cluster):
        source = noticia.get('sources', [{}])[0]
        label = source.get('label', 'Fonte Desconhecida')
        url = source.get('url', '#')
        lang = noticia.get('language', '').upper()
        item_title = noticia.get('title', '')

        event_html += f'      <div class="source-item">\n'
        event_html += f'          <span class="source-label">{i+1}. {label} [{lang}]:</span>\n'
        event_html += f'          <a href="{url}" target="_blank" rel="noopener noreferrer" class="source-link" title="{item_title}">Ver artigo</a>\n'
        event_html += f'      </div>\n'
    event_html += '    </div>\n'
    event_html += '  </section>\n'
    return event_html

# Função principal de geração da página HTML
def generate_page_html(clusters_or_news):
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
            # Ignorar outros tipos por segurança
    else:
         items_html = "    <p>Nenhuma notícia encontrada ou ocorreu um erro durante o processamento.</p>"

    # Template HTML da página (mantido igual)
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
        <p><a href="https://github.com/SEU_USUARIO/geopolitica-news" target="_blank" rel="noopener">Ver código no GitHub</a> (Substitua)</p>
    </footer>
</body>
</html>"""
    return html_content