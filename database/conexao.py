from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

# 1. A Base precisa nascer AQUI para o modelos.py poder importar ela depois!
Base = declarative_base()

# 2. Configuração da conexão com o banco de dados SQLite
engine = create_engine("sqlite:///banco_cartorio.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def verificar_e_atualizar_banco():
    """Motor Automático de Migração: Lê os modelos e injeta colunas faltantes no banco físico."""

    # O PULO DO GATO: Importar os modelos AQUI DENTRO da função!
    # Isso quebra o "circular import" (o arquivo não fica preso num loop infinito)
    import database.modelos

    # 1. Cria as tabelas do zero caso seja a primeira vez rodando o app
    Base.metadata.create_all(bind=engine)

    # 2. Inspeciona o banco para ver se tem tabelas antigas precisando de colunas novas
    inspector = inspect(engine)
    with engine.begin() as conn:
        for nome_tabela, tabela_modelo in Base.metadata.tables.items():
            if inspector.has_table(nome_tabela):
                # Pega a lista de colunas que já existem no arquivo .db
                colunas_banco = [col['name'] for col in inspector.get_columns(nome_tabela)]

                # Compara com as colunas que você escreveu no modelos.py
                for coluna in tabela_modelo.columns:
                    if coluna.name not in colunas_banco:
                        # Se faltar a coluna, descobre o tipo dela e faz o ALTER TABLE via SQL nativo
                        tipo_coluna = coluna.type.compile(engine.dialect)
                        sql = f"ALTER TABLE {nome_tabela} ADD COLUMN {coluna.name} {tipo_coluna}"
                        conn.execute(text(sql))


# Aciona a blindagem sempre que o sistema conectar
verificar_e_atualizar_banco()