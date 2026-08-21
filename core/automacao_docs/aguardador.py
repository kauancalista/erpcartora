import time
from tkinter import messagebox
from localizador import localizar_documento, extrair_primeiro_conjuge, normalizar


def aguardar_documentos(nome, pasta, log_callback, modo="CPF", cache_pasta=None):
    while True:
        doc_principal = localizar_documento(nome, pasta, cache_pasta)

        # OTIMIZADO: reutiliza as funções do localizador em vez de duplicar a lógica
        nome_limpo = extrair_primeiro_conjuge(normalizar(nome))

        doc_secundario = None
        nome_secundario_exibicao = ""

        if modo == "CPF":
            doc_secundario = localizar_documento(f"{nome_limpo} CPF", pasta, cache_pasta)
            nome_secundario_exibicao = "CPF"

        elif modo == "CERTIDAO":
            sufixos = [" + FERC", " + CRAS", " + REGISTRE-SE", " FERC", " CRAS", " REGISTRE-SE"]
            for sufixo in sufixos:
                doc_secundario = localizar_documento(f"{nome_limpo}{sufixo}", pasta, cache_pasta)
                if doc_secundario:
                    break
            nome_secundario_exibicao = "Anexo (FERC/CRAS/REGISTRE-SE)"

        if doc_principal and doc_secundario:
            return doc_principal, doc_secundario

        status_principal = "✓ Documento Principal" if doc_principal else "✗ Documento Principal"
        status_sec = f"✓ {nome_secundario_exibicao}" if doc_secundario else f"✗ {nome_secundario_exibicao}"

        msg = f"Pendência encontrada para:\n{nome}\n\n{status_principal}\n{status_sec}\n\n"
        msg += "O que deseja fazer?\n"
        msg += "[Sim] = Tentar achar de novo (Coloque o arquivo na pasta)\n"
        msg += "[Não] = Ignorar o que falta e gerar mesmo assim\n"
        msg += "[Cancelar] = Parar a geração do relatório agora"

        resposta = messagebox.askyesnocancel("Documento Faltando", msg)

        if resposta is True:
            log_callback(f"Aguardando arquivos para: {nome}...")
            time.sleep(1)
            # OTIMIZAÇÃO: reconstrói o cache após o usuário adicionar arquivos
            from localizador import construir_cache_pasta
            cache_pasta = construir_cache_pasta(pasta)
            continue
        elif resposta is False:
            log_callback(f"⚠ Faltando documentos. Ignorando e avançando: {nome}.")
            return doc_principal, doc_secundario
        else:
            raise Exception("O processo foi cancelado pelo usuário.")
