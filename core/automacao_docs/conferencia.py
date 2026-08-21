from localizador import localizar_documento, extrair_primeiro_conjuge, normalizar, construir_cache_pasta, eh_mesmo_arquivo


def conferir_documentos(nomes, pasta, modo="CPF"):
    completos = []
    pendentes = []

    # Cache da pasta construído uma única vez para toda a conferência
    cache_pasta = construir_cache_pasta(pasta)

    for nome in nomes:
        doc = localizar_documento(nome, pasta, cache_pasta)

        # Reutiliza as funções do localizador em vez de duplicar a lógica de split
        nome_limpo = extrair_primeiro_conjuge(normalizar(nome))

        doc_secundario = None

        if modo == "CPF":
            doc_secundario = localizar_documento(f"{nome_limpo} CPF", pasta, cache_pasta)
        elif modo == "CERTIDAO":
            sufixos = [" + FERC", " + CRAS", " + REGISTRE-SE", " FERC", " CRAS", " REGISTRE-SE"]
            for sufixo in sufixos:
                doc_secundario = localizar_documento(f"{nome_limpo}{sufixo}", pasta, cache_pasta)
                if doc_secundario:
                    break

        # Proteção extra: mesmo com a busca do localizador já filtrando
        # variantes de anexo, se por algum motivo os dois apontarem pro
        # MESMO arquivo físico, isso não pode contar como "completo" —
        # só existe 1 arquivo na pasta, então falta o outro de verdade.
        if doc and doc_secundario and eh_mesmo_arquivo(doc, doc_secundario):
            doc_secundario = None

        if doc and doc_secundario:
            completos.append(nome)
        else:
            pendente = {
                "nome": nome,
                "documento": bool(doc),
                "anexo": bool(doc_secundario),
                "modo": modo,
            }
            pendentes.append(pendente)

    return completos, pendentes
