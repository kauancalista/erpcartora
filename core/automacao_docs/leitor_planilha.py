import pandas as pd


def ler_nomes(caminho_planilha):
    """
    Procura automaticamente a coluna 'Nome'
    e retorna uma lista com todos os nomes.
    """

    # Lê sem assumir cabeçalho
    df = pd.read_excel(
        caminho_planilha,
        sheet_name=0,
        header=None
    )

    coluna_nome = None
    linha_cabecalho = None

    # Procura onde está a célula "Nome"
    for linha in range(len(df)):
        for coluna in range(len(df.columns)):

            valor = df.iloc[linha, coluna]

            if pd.notna(valor):

                if str(valor).strip().upper() == "NOME":
                    coluna_nome = coluna
                    linha_cabecalho = linha
                    break

        if coluna_nome is not None:
            break

    if coluna_nome is None:
        raise Exception("Coluna 'Nome' não encontrada.")

    nomes = []

    for linha in range(linha_cabecalho + 1, len(df)):

        valor = df.iloc[linha, coluna_nome]

        if pd.notna(valor):

            nome = str(valor).strip()

            if nome:
                nomes.append(nome)

    return nomes