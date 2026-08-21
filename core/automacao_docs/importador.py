import os
import shutil

from localizador import (
    construir_cache_pasta,
    localizar_documento,
    extrair_primeiro_conjuge,
    normalizar,
)


def _nomes_candidatos(nome, modo):
    """
    Monta a lista de nomes que devem ser procurados na origem para
    cobrir um único item pendente: o documento principal e, dependendo
    do modo, o(s) anexo(s) (CPF ou FERC/CRAS/REGISTRE-SE).

    Reaproveita exatamente a mesma regra de sufixos usada em
    conferencia.py / aguardador.py, para não haver divergência entre
    "o que é considerado pendente" e "o que o coletor procura".
    """
    nome_limpo = extrair_primeiro_conjuge(normalizar(nome))
    candidatos = [nome]

    if modo == "CPF":
        candidatos.append(f"{nome_limpo} CPF")
    elif modo == "CERTIDAO":
        for sufixo in [" + FERC", " + CRAS", " + REGISTRE-SE", " FERC", " CRAS", " REGISTRE-SE"]:
            candidatos.append(f"{nome_limpo}{sufixo}")

    return candidatos


def importar_arquivos(pasta_origem, pasta_destino, mover=True, pendentes=None, modo="CPF"):
    """
    Move/copia arquivos de pasta_origem (ex: pasta do scanner) para pasta_destino.

    Comportamento:
    - Se `pendentes` for fornecido (lista de nomes ou de dicts no formato
      retornado por conferir_documentos, com chave "nome"), o coletor busca
      em pasta_origem, usando a mesma lógica de match de localizador.py,
      apenas os arquivos que correspondem a cada nome pendente (documento
      principal + anexo). Esse é o uso recomendado: copiar só o que falta.
    - Se `pendentes` for None, mantém o comportamento de utilitário genérico
      (copia/move tudo que está em pasta_origem). Use isso conscientemente,
      sabendo que NÃO há filtro por pendência nesse modo.

    Retorna (processados, ignorados, nao_encontrados).
    """
    processados = []
    ignorados = []
    nao_encontrados = []

    if pendentes is None:
        caminhos_origem = [
            os.path.join(pasta_origem, arquivo)
            for arquivo in os.listdir(pasta_origem)
            if os.path.isfile(os.path.join(pasta_origem, arquivo))
        ]
    else:
        cache_origem = construir_cache_pasta(pasta_origem)
        caminhos_origem = []

        for item in pendentes:
            nome = item["nome"] if isinstance(item, dict) else item
            modo_item = item.get("modo", modo) if isinstance(item, dict) else modo

            encontrou_algum = False
            for candidato in _nomes_candidatos(nome, modo_item):
                doc = localizar_documento(candidato, pasta_origem, cache_origem)
                if doc:
                    caminhos_origem.append(doc["caminho"])
                    encontrou_algum = True

            if not encontrou_algum:
                nao_encontrados.append(nome)

    # Remove duplicatas (ex: mesmo arquivo cobrindo principal e anexo)
    caminhos_origem = list(dict.fromkeys(caminhos_origem))

    for caminho_origem in caminhos_origem:
        arquivo = os.path.basename(caminho_origem)

        # strip antes de upper para remover espaços originais do nome
        novo_nome = arquivo.strip().upper()
        caminho_destino = os.path.join(pasta_destino, novo_nome)

        # Pula se o arquivo já existe no destino (evita duplicatas)
        if os.path.exists(caminho_destino):
            ignorados.append(novo_nome)
            continue

        if mover:
            shutil.move(caminho_origem, caminho_destino)
        else:
            shutil.copy2(caminho_origem, caminho_destino)

        processados.append(novo_nome)

    return processados, ignorados, nao_encontrados
