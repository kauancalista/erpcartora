import os
from docxtpl import DocxTemplate
from datetime import datetime
import locale


def gerar_documento_word(caminho_template, dados, nome_arquivo_saida):
    """
    Lê um template .docx, substitui as tags {{ }} pelos valores do dicionário 'dados'
    e salva o novo documento gerado na pasta 'documentos_gerados'.
    """
    # Tenta deixar a data em português se o SO permitir
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.utf8')
    except:
        pass

    # Garante que a pasta de saída exista
    pasta_saida = "documentos_gerados"
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)

    caminho_saida = os.path.join(pasta_saida, nome_arquivo_saida)

    try:
        # 1. Abre o modelo do Word
        doc = DocxTemplate(caminho_template)

        # 2. Injeta a data atual automaticamente, caso o template tenha a tag {{data}}
        if "data" not in dados:
            dados["data"] = datetime.now().strftime("%d de %B de %Y")

        # 3. Substitui as variáveis mágicas
        doc.render(dados)

        # 4. Salva o documento final
        doc.save(caminho_saida)

        return True, caminho_saida
    except Exception as e:
        return False, str(e)