import os

# ---------------------------------------------------------
# Leitura de arquivo com proteção de encoding
# ---------------------------------------------------------
def ler_arquivo(caminho):
    """Lê arquivos de texto usando UTF-8 com fallback."""
    try:
        with open(caminho, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except Exception as e:
        return f"[Erro ao ler o arquivo: {e}]"


# ---------------------------------------------------------
# Gera a estrutura de pastas em formato de árvore
# ---------------------------------------------------------
def listar_estrutura(base_path):
    estrutura = []
    for root, dirs, files in os.walk(base_path):
        nivel = root.replace(base_path, "").count(os.sep)
        espaco = " " * 4 * nivel
        estrutura.append(f"{espaco}{os.path.basename(root)}/")
        subespaco = " " * 4 * (nivel + 1)

        for arquivo in files:
            estrutura.append(f"{subespaco}{arquivo}")

    return "\n".join(estrutura)


# ---------------------------------------------------------
# Extrai texto apenas de extensões permitidas
# ---------------------------------------------------------
EXTENSOES_SUPORTADAS = {
    ".txt", ".py", ".js", ".ts", ".json", ".md",
    ".html", ".css", ".java", ".c", ".cpp"
}

def extrair_textos(base_path):
    textos = {}

    for root, dirs, files in os.walk(base_path):
        for arquivo in files:
            if os.path.splitext(arquivo)[1].lower() in EXTENSOES_SUPORTADAS:
                caminho = os.path.join(root, arquivo)
                textos[caminho] = ler_arquivo(caminho)

    return textos


# ---------------------------------------------------------
# Impressão segura sem emojis (compatível com Windows cp1252)
# ---------------------------------------------------------
def imprimir_seguro(texto):
    """Limita caracteres incompatíveis com o terminal Windows."""
    try:
        texto_seguro = texto.encode("cp1252", errors="replace").decode("cp1252")
    except:
        texto_seguro = texto
    print(texto_seguro)


# ---------------------------------------------------------
# EXECUÇÃO PRINCIPAL
# ---------------------------------------------------------
if __name__ == "__main__":
    pasta = r"C:\Users\Borracharia\IdeaProjects\backendGB"

    if not os.path.isdir(pasta):
        print("Caminho inválido. Verifique o diretório informado.")
        exit()

    print("\nLendo arquivos...\n")

    textos_extraidos = extrair_textos(pasta)

    for caminho, conteudo in textos_extraidos.items():
        print("=" * 80)
        print(f"Arquivo: {caminho}")
        print("=" * 80)

        # Imprime somente os primeiros 2000 caracteres
        imprimir_seguro(conteudo[:2000])
        print("\n")

    print("\nEstrutura da pasta:")
    print("=" * 80)
    imprimir_seguro(listar_estrutura(pasta))
