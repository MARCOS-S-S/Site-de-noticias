import json
import os

DATA_FILE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'news_data.json')

def load_news_data(file_path):
    #Carrega os dados das notícias do arquivo JSON especificado.
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

def main():
    """
    Função principal do script.
    Carrega os dados e os exibe no console.
    """
    print(f"Tentando carregar notícias de: {DATA_FILE_PATH}")
    noticias = load_news_data(DATA_FILE_PATH)

    if noticias:
        print("\n--- Notícias Carregadas ---")
        # Itera sobre cada notícia na lista
        for i, noticia in enumerate(noticias):
            print(f"\nNotícia {i+1}:")
            print(f"  Título: {noticia.get('title', 'N/A')}") # Usa .get() para evitar erro se a chave não existir
            print(f"  Resumo: {noticia.get('summary', 'N/A')}")

            # Verifica se a chave 'sources' existe e é uma lista
            if 'sources' in noticia and isinstance(noticia['sources'], list):
                print("  Fontes:")
                # Itera sobre cada fonte na lista de fontes da notícia
                for j, fonte in enumerate(noticia['sources']):
                    label = fonte.get('label', 'N/A')
                    url = fonte.get('url', '#')
                    print(f"    {j+1}. [{label}]({url})")
            else:
                print("  Fontes: Nenhuma fonte encontrada ou formato inválido.")
        print("\n--- Fim das Notícias ---")
    else:
        print("Não foi possível carregar os dados das notícias.")

# Garante que a função main() só será executada quando o script for rodado diretamente
if __name__ == "__main__":
    main()