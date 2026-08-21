import os
import time
from docxtpl import DocxTemplate


def gerar_docx_requerimento(nome_arquivo_template, dicionario_dados):
    """
    Pega o template Word e preenche com as tags enviadas pela tela dinâmica.
    """
    caminho_template = f"assets/templates/{nome_arquivo_template}"

    os.makedirs("assets/templates", exist_ok=True)
    os.makedirs("documentos_gerados", exist_ok=True)

    if not os.path.exists(caminho_template):
        raise FileNotFoundError()

    # Carrega o Word
    doc = DocxTemplate(caminho_template)

    # Faz a substituição mágica usando exatamente o dicionário que a tela montou!
    doc.render(dicionario_dados)

    # Cria um nome de arquivo único para não sobrescrever
    timestamp = int(time.time())
    caminho_final = f"documentos_gerados/{nome_arquivo_template.split('.')[0]}_Gerado_{timestamp}.docx"

    doc.save(caminho_final)

    return caminho_final