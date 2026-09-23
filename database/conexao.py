import os
import gc
from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

from utils_caminhos import obter_diretorio_base

# 1. Puxa as credenciais do .env com caminho absoluto
load_dotenv(os.path.join(obter_diretorio_base(), ".env"))

DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

URL_POSTGRES = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
PASTA_DB = os.path.join(obter_diretorio_base(), "database")
os.makedirs(PASTA_DB, exist_ok=True)
CAMINHO_SQLITE = os.path.join(PASTA_DB, "cartorio_local.db")
URL_SQLITE = f"sqlite:///{CAMINHO_SQLITE}"

Base = declarative_base()

# Status global: "PRODUCAO" ou "STANDBY_LOCAL"
STATUS_CONEXAO = "STANDBY_LOCAL"

engine = None
SessionLocal = sessionmaker(autocommit=False, autoflush=False)

from contextlib import contextmanager

@contextmanager
def get_db_session():
    """
    Context Manager seguro para conexões com o banco de dados.
    Garante que a conexão seja sempre fechada (db.close()), mesmo se ocorrer um erro no meio do caminho.
    Evita o vazamento de memória e exaustão do Pool do PostgreSQL.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def testar_conexao_postgres(timeout_segundos=3):
    """Testa se o PostgreSQL de produção responde em até N segundos."""
    try:
        engine_teste = create_engine(
            URL_POSTGRES,
            connect_args={"connect_timeout": timeout_segundos}
        )
        with engine_teste.connect() as conn:
            conn.execute(text("SELECT 1"))
        engine_teste.dispose()
        return True
    except Exception:
        return False


def criar_engine_postgres():
    """Cria engine configurado para o PostgreSQL de produção."""
    return create_engine(
        URL_POSTGRES,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={"connect_timeout": 5}
    )


def criar_engine_sqlite():
    """Cria engine configurado para o SQLite local temporário."""
    return create_engine(
        URL_SQLITE,
        connect_args={"check_same_thread": False}
    )


def sincronizar_dados_locais_para_producao():
    """
    Transfere todos os dados salvos temporariamente no SQLite local
    para o banco de dados PostgreSQL de produção, e apaga o arquivo
    cartorio_local.db após o sucesso absoluto.
    """
    if not os.path.exists(CAMINHO_SQLITE):
        return True, "Nenhum dado local pendente para sincronizar."

    import database.modelos as m

    engine_pg = criar_engine_postgres()
    engine_sql = criar_engine_sqlite()

    SessionPG = sessionmaker(bind=engine_pg)
    SessionSQL = sessionmaker(bind=engine_sql)

    db_pg = SessionPG()
    db_sql = SessionSQL()

    try:
        # Garante tabelas no PostgreSQL
        Base.metadata.create_all(bind=engine_pg)

        # 1. Sincroniza Processos
        processos_locais = db_sql.query(m.Processo).order_by(m.Processo.id.asc()).all()
        mapa_id_processos = {}

        for p_local in processos_locais:
            proc_remoto = m.Processo(
                nome_cliente=p_local.nome_cliente,
                cpf=p_local.cpf,
                tipo_servico=p_local.tipo_servico,
                status=p_local.status,
                data_entrada=p_local.data_entrada,
                data_prazo=p_local.data_prazo,
                telefone_whatsapp=p_local.telefone_whatsapp,
                origem_solicitacao=p_local.origem_solicitacao
            )
            db_pg.add(proc_remoto)
            db_pg.flush()
            mapa_id_processos[p_local.id] = proc_remoto.id

        # 2. Sincroniza Documentos
        documentos_locais = db_sql.query(m.Documento).all()
        for doc_local in documentos_locais:
            remoto_proc_id = mapa_id_processos.get(doc_local.processo_id, doc_local.processo_id)
            doc_remoto = m.Documento(
                processo_id=remoto_proc_id,
                nome_arquivo=doc_local.nome_arquivo,
                tipo_documento=doc_local.tipo_documento,
                caminho_arquivo=doc_local.caminho_arquivo
            )
            db_pg.add(doc_remoto)

        # 3. Sincroniza Tarefas
        tarefas_locais = db_sql.query(m.Tarefa).all()
        for t_local in tarefas_locais:
            remoto_proc_id = mapa_id_processos.get(t_local.processo_id, t_local.processo_id)
            tarefa_remota = m.Tarefa(
                descricao=t_local.descricao,
                responsavel=t_local.responsavel,
                status=t_local.status,
                data_criacao=t_local.data_criacao,
                processo_id=remoto_proc_id
            )
            db_pg.add(tarefa_remota)

        # 4. Sincroniza Casamentos
        casamentos_locais = db_sql.query(m.Casamento).all()
        for c_local in casamentos_locais:
            casamento_remoto = m.Casamento(
                protocolo=c_local.protocolo,
                nome_noivo=c_local.nome_noivo,
                nome_noiva=c_local.nome_noiva,
                telefone_contato=c_local.telefone_contato,
                data_entrada=c_local.data_entrada,
                data_celebracao=c_local.data_celebracao,
                horario_celebracao=c_local.horario_celebracao,
                docs_entregues=c_local.docs_entregues,
                taxa_status=c_local.taxa_status,
                status=c_local.status,
                pendencias=c_local.pendencias
            )
            db_pg.add(casamento_remoto)

        # 5. Sincroniza Compromissos
        compromissos_locais = db_sql.query(m.Compromisso).all()
        for comp_local in compromissos_locais:
            comp_remoto = m.Compromisso(
                titulo=comp_local.titulo,
                data=comp_local.data,
                hora=comp_local.hora,
                tipo=comp_local.tipo,
                lembrete=comp_local.lembrete,
                link_reuniao=comp_local.link_reuniao,
                status=comp_local.status
            )
            db_pg.add(comp_remoto)

        # 6. Sincroniza Notificações
        notificacoes_locais = db_sql.query(m.Notificacao).all()
        for notif_local in notificacoes_locais:
            notif_remota = m.Notificacao(
                titulo=notif_local.titulo,
                subtitulo=notif_local.subtitulo,
                tipo=notif_local.tipo,
                data_criacao=notif_local.data_criacao,
                lida=notif_local.lida
            )
            db_pg.add(notif_remota)

        # Salva tudo no banco de produção
        db_pg.commit()

        # Fecha conexões com SQLite para poder remover o arquivo com segurança
        db_sql.close()
        engine_sql.dispose()
        del db_sql
        del engine_sql
        gc.collect()

        # Remove o banco temporário do SQLite após a migração bem-sucedida!
        if os.path.exists(CAMINHO_SQLITE):
            try:
                os.remove(CAMINHO_SQLITE)
            except Exception:
                pass

        return True, "Dados temporários migrados com sucesso para a produção!"

    except Exception as e:
        db_pg.rollback()
        return False, f"Falha na sincronização: {str(e)}"
    finally:
        db_pg.close()
        engine_pg.dispose()


def alternar_para_producao():
    """Redireciona SessionLocal e engine globais para o PostgreSQL."""
    global engine, STATUS_CONEXAO
    if engine:
        engine.dispose()
    engine = criar_engine_postgres()
    SessionLocal.configure(bind=engine)
    STATUS_CONEXAO = "PRODUCAO"


def alternar_para_standby():
    """Redireciona SessionLocal e engine globais para o SQLite local temporário."""
    global engine, STATUS_CONEXAO
    if engine:
        engine.dispose()
    engine = criar_engine_sqlite()
    SessionLocal.configure(bind=engine)
    STATUS_CONEXAO = "STANDBY_LOCAL"
    import database.modelos
    Base.metadata.create_all(bind=engine)


def tentar_reconectar_e_sincronizar():
    """
    Chamado pelo monitor de segundo plano ou pelo usuário.
    Testa se o PostgreSQL voltou, migra dados locais e alterna o modo.
    """
    if testar_conexao_postgres(timeout_segundos=3):
        # 1. Se há banco SQLite com dados, migra para a produção
        sucesso, msg = sincronizar_dados_locais_para_producao()
        # 2. Alterna a engine para PostgreSQL
        alternar_para_producao()
        return True, "Conexão com a empresa restabelecida! Dados locais migrados para a produção."
    else:
        return False, "Banco de dados da empresa ainda inacessível."


def inicializar_banco_rapido():
    """
    Roda na inicialização do sistema de forma instantânea.
    Inicia direto no SQLite para não congelar a tela. O painel principal fará a checagem do Postgres em background logo em seguida.
    """
    global engine, STATUS_CONEXAO
    alternar_para_standby()

# Inicializa instantaneamente no import (Zero Lag no Startup)
inicializar_banco_rapido()