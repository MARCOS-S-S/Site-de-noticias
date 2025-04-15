import json
import os
from datetime import datetime
import pytz # Biblioteca para lidar com fusos horários

# Define o fuso horário de Brasília
TIMEZONE_BR = pytz.timezone('America/Sao_Paulo')

# Caminho para o arquivo de dados JSON (entrada)
BASE_DIR = os.path.dirname(os.path.dirname(__file__)) # Raiz do projeto (geopolitica-news/)
DATA_FILE_PATH = os.path.join(BASE_DIR, 'data', 'news_data.json')
# Caminho para o arquivo HTML a ser gerado (saída)
HTML_OUTPUT_PATH = os.path.join(BASE_DIR, 'index.html')

def load_news_data(file_path):
    """Carrega os dados das notícias do arquivo JSON."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            news_data = json.load(f)
        return news_data
    except FileNotFoundError:
        print(f"Erro: Arquivo não encontrado em '{file_path}'")
        return None
    except json.JSONDecodeError:
        print(f"Erro: O arquivo '{file_path}' não contém JSON válido.")
        return None
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao ler o arquivo: {e}")
        return None

def generate_news_item_html(noticia):
    """Gera o bloco HTML para um único item de notícia."""
    title = noticia.get('title', 'Título Indisponível')
    summary = noticia.get('summary', '') # Pega o resumo, ou string vazia se não houver
    sources = noticia.get('sources', []) # Pega a lista de fontes, ou lista vazia

    # Inicia o HTML do artigo
    item_html = f'<article class="news-item">\n'
    item_html += f'  <h3 class="news-title">{title}</h3>\n'

    # Adiciona o resumo se ele existir
    if summary:
        item_html += f'  <p class="news-summary">{summary}</p>\n'

    # Adiciona a seção de fontes se houver fontes
    if sources:
        item_html += '  <div class="news-sources">\n'
        item_html += '    <h4>Fontes:</h4>\n'
        for source in sources:
            label = source.get('label', 'Fonte Desconhecida')
            url = source.get('url', '#')
            # Adiciona classe CSS específica para cada link de fonte (opcional)
            # source_class = f"source-{label.lower().replace(' ', '-')}-link" # Ex: source-reuters-link
            item_html += f'    <div class="source">\n'
            item_html += f'      <span class="source-label">{label}:</span>\n'
            item_html += f'      <a href="{url}" target="_blank" rel="noopener noreferrer" class="source-link">{label} - Ver artigo completo</a>\n'
            item_html += f'    </div>\n'
        item_html += '  </div>\n' # Fecha news-sources
    else:
         item_html += '  <p><em>Nenhuma fonte disponível para esta notícia.</em></p>\n' # Mensagem se não houver fontes

    item_html += '</article>\n' # Fecha news-item
    return item_html

def generate_page_html(noticias):
    """Gera o conteúdo HTML completo da página."""
    # Pega a data e hora atual no fuso horário de Brasília
    now_br = datetime.now(TIMEZONE_BR)
    update_date_str = now_br.strftime('%d/%m/%Y às %H:%M:%S %Z') # Formato: DD/MM/AAAA às HH:MM:SS Fuso
    current_year = now_br.year

    # Gera o HTML para cada notícia usando a função auxiliar
    news_items_html = "\n".join([generate_news_item_html(noticia) for noticia in noticias])

    # Monta a string do HTML completo da página
    # Usando f-string multi-linha para clareza
    html_content = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Notícias de geopolítica com múltiplas fontes e perspectivas.">
    <title>GeoNotícias - Perspectivas Múltiplas</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>

    <header class="site-header">
        <h1>GeoNotícias</h1>
        <p>Análise geopolítica com fontes diversificadas</p>
        <p class="update-info">Atualizado em: <span id="update-date">{update_date_str}</span></p>
    </header>

    <main class="news-container">
        <h2>Notícias do Dia</h2>

        {news_items_html if news_items_html else "<p>Nenhuma notícia encontrada hoje.</p>"}

    </main>

    <footer class="site-footer">
        <p>&copy; <span id="current-year">{current_year}</span> GeoNotícias. Código aberto no GitHub.</p>
        </footer>

    </body>
</html>"""
    return html_content

def write_html_file(html_content, output_path):
    """Escreve o conteúdo HTML no arquivo de saída especificado."""
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"Arquivo HTML gerado com sucesso em: '{output_path}'")
        return True
    except IOError as e:
        print(f"Erro ao escrever o arquivo HTML em '{output_path}': {e}")
        return False
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao escrever o arquivo: {e}")
        return False

def main():
    """Função principal: carrega dados, gera HTML e salva no arquivo."""
    print("Iniciando processo de geração do site...")
    print(f"Carregando notícias de: {DATA_FILE_PATH}")
    noticias = load_news_data(DATA_FILE_PATH)

    if noticias is not None: # Verifica se o carregamento foi bem-sucedido (não None)
        print(f"{len(noticias)} notícias carregadas.")
        # Gera o conteúdo HTML completo da página
        html_completo = generate_page_html(noticias)
        # Escreve o HTML gerado no arquivo index.html
        write_html_file(html_completo, HTML_OUTPUT_PATH)
    else:
        print("Não foi possível carregar dados das notícias. O arquivo HTML não será gerado/atualizado.")

    print("Processo finalizado.")

if __name__ == "__main__":
    # Antes de rodar, talvez seja necessário instalar pytz
    # No terminal, com o venv ativo: pip install pytz
    try:
        import pytz
    except ImportError:
        print("Biblioteca 'pytz' não encontrada. Tente instalar com: pip install pytz")
        # Opcionalmente, pode-se remover a dependência de pytz se a hora local for suficiente
        # e ajustar a formatação da data/hora
        exit() # Sai se a dependência estiver faltando

    main()