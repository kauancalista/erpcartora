import os
import re
import unicodedata
from rapidfuzz import fuzz

EXTENSOES_VALIDAS = [".pdf", ".jpg", ".jpeg", ".png"]

# Sufixos que identificam um arquivo como ANEXO (não documento principal).
# Precisam bater exatamente com o texto residual após normalizar() —
# ou seja, já sem pontuação, com "-" virando espaço.
SUFIXOS_ANEXO_CONHECIDOS = ["CPF", "FERC", "CRAS", "REGISTRE SE"]


def _eh_apenas_sufixo_de_anexo(texto_extra):
    """
    True se o texto residual (a diferença entre dois nomes normalizados)
    é exatamente um dos sufixos de anexo conhecidos — nada mais.
    """
    texto_extra = texto_extra.replace("+", " ")
    texto_extra = re.sub(r'\s+', ' ', texto_extra).strip()
    return texto_extra in SUFIXOS_ANEXO_CONHECIDOS


def _sao_variantes_de_anexo(nome_a, nome_b):
    """
    True se nome_a e nome_b são o MESMO nome base, diferindo só pela
    presença de um sufixo de anexo (CPF / FERC / CRAS / REGISTRE-SE) em
    um dos dois — ex: "JOAO SILVA" vs "JOAO SILVA CPF".

    Isso NÃO deve contar como match por similaridade: são dois arquivos
    de TIPOS diferentes (documento principal x anexo), mesmo sendo da
    mesma pessoa. Sem essa checagem, a busca fuzzy confundia um pelo
    outro sempre que o nome era longo o bastante pra "CPF" sozinho não
    derrubar a % de similaridade abaixo do limiar.
    """
    maior, menor = (nome_a, nome_b) if len(nome_a) >= len(nome_b) else (nome_b, nome_a)
    if maior == menor or not maior.startswith(menor):
        return False
    return _eh_apenas_sufixo_de_anexo(maior[len(menor):])


def eh_mesmo_arquivo(doc_a, doc_b):
    """True se dois resultados de localizar_documento apontam pro mesmo arquivo físico."""
    if not doc_a or not doc_b:
        return False
    return doc_a["caminho"] == doc_b["caminho"]


def normalizar(texto):
    # 1. Tudo para maiúsculo e remove espaços nas pontas
    texto = str(texto).upper().strip()

    # 2. Remove acentos (Á vira A, Õ vira O)
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")

    # 3. Substitui pontuações por espaço (.-_())
    texto = re.sub(r'[.,\-_()]', ' ', texto)

    # 4. Remove espaços duplos
    texto = re.sub(r'\s+', ' ', texto).strip()

    return texto


def extrair_primeiro_conjuge(texto_normalizado):
    """Pega apenas o primeiro nome se houver ' E '"""
    if " E " in texto_normalizado:
        return texto_normalizado.split(" E ")[0].strip()
    return texto_normalizado


def construir_cache_pasta(pasta):
    """
    OTIMIZAÇÃO: lê e normaliza os arquivos da pasta uma única vez.
    Retorna lista de tuplas (nome_original, nome_normalizado, extensao).
    Deve ser chamado uma vez antes de processar todos os nomes da planilha,
    e o resultado passado para localizar_documento via cache_pasta.
    """
    cache = []
    for arquivo in os.listdir(pasta):
        nome_arquivo, extensao = os.path.splitext(arquivo)
        if extensao.lower() not in EXTENSOES_VALIDAS:
            continue
        cache.append((arquivo, normalizar(nome_arquivo), extensao.lower()))
    return cache


def localizar_documento(nome_original, pasta, cache_pasta=None):
    """
    Localiza um documento na pasta pelo nome.

    cache_pasta: resultado de construir_cache_pasta(pasta).
    Se não for fornecido, a pasta é lida na hora (comportamento original).
    Para processar muitos nomes, prefira passar o cache para evitar
    múltiplos os.listdir na mesma pasta.
    """
    nome_norm_completo = normalizar(nome_original)
    nome_primeiro_conjuge = extrair_primeiro_conjuge(nome_norm_completo)

    melhor_match = None
    maior_similaridade = 0
    arquivo_encontrado = None

    # Usa o cache se fornecido, senão lê a pasta na hora
    if cache_pasta is None:
        cache_pasta = construir_cache_pasta(pasta)

    for arquivo, nome_arquivo_norm, _ in cache_pasta:
        # CAMADA 1: Busca exata pelo casal (o PDF tem o nome dos dois)
        if nome_arquivo_norm == nome_norm_completo:
            return {
                "caminho": os.path.join(pasta, arquivo),
                "tipo": "Encontrado",
                "similaridade": 100,
                "arquivo": arquivo
            }

        # CAMADA 2: Busca exata pelo 1º cônjuge (o PDF só tem o nome de um)
        if nome_arquivo_norm == nome_primeiro_conjuge:
            return {
                "caminho": os.path.join(pasta, arquivo),
                "tipo": "Encontrado",
                "similaridade": 100,
                "arquivo": arquivo
            }

        # Um arquivo que é "nome + CPF" (ou + FERC/CRAS/REGISTRE-SE) é um
        # ANEXO, não o documento principal — mesmo que a diferença de texto
        # seja pequena o bastante pra passar no limiar de similaridade.
        # Sem essa checagem, buscar "JOAO SILVA" podia "achar" o arquivo
        # "JOAO SILVA CPF.pdf" e considerar o principal como entregue.
        if _sao_variantes_de_anexo(nome_primeiro_conjuge, nome_arquivo_norm):
            continue

        # CAMADA 3: Similaridade (usa o 1º cônjuge para não confundir)
        similaridade = fuzz.ratio(nome_primeiro_conjuge, nome_arquivo_norm)
        if similaridade > maior_similaridade:
            maior_similaridade = similaridade
            melhor_match = nome_arquivo_norm
            arquivo_encontrado = arquivo

    # CAMADA 4: Retorna se a similaridade for >= 90%
    if maior_similaridade >= 90:
        return {
            "caminho": os.path.join(pasta, arquivo_encontrado),
            "tipo": "Encontrado (similaridade)",
            "similaridade": round(maior_similaridade, 1),
            "arquivo": arquivo_encontrado
        }

    return None
