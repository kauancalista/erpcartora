from sqlalchemy.orm import Session
from database.modelos import Processo, Documento, Tarefa

# ==========================================
# C - CREATE (Criar / Inserir)
# ==========================================
def criar_processo(db: Session, nome_cliente: str, tipo_servico: str, cpf: str = None, telefone_whatsapp: str = None):
    novo_processo = Processo(
        nome_cliente=nome_cliente,
        cpf=cpf,
        tipo_servico=tipo_servico,
        telefone_whatsapp=telefone_whatsapp
        # status e data_entrada já são preenchidos automaticamente pelo modelo!
    )
    db.add(novo_processo)
    db.commit()          # Salva definitivamente no banco
    db.refresh(novo_processo) # Atualiza o objeto com o ID gerado pelo banco
    return novo_processo

# ==========================================
# R - READ (Ler / Pesquisar)
# ==========================================
def listar_todos_processos(db: Session):
    return db.query(Processo).all()

def buscar_processos_por_nome(db: Session, nome: str):
    # O ilike permite buscar ignorando maiúsculas e minúsculas (Ex: "maria" acha "Maria")
    # O "%" faz buscar em qualquer parte do nome
    return db.query(Processo).filter(Processo.nome_cliente.ilike(f"%{nome}%")).all()

def obter_processo_por_id(db: Session, processo_id: int):
    return db.query(Processo).filter(Processo.id == processo_id).first()

# ==========================================
# U - UPDATE (Atualizar)
# ==========================================
def atualizar_status_processo(db: Session, processo_id: int, novo_status: str):
    processo = obter_processo_por_id(db, processo_id)
    if processo:
        processo.status = novo_status
        db.commit()
        db.refresh(processo)
        return processo
    return None # Retorna None se não achar o ID

# ==========================================
# D - DELETE (Apagar)
# ==========================================
def deletar_processo(db: Session, processo_id: int):
    processo = obter_processo_por_id(db, processo_id)
    if processo:
        db.delete(processo)
        db.commit()
        return True
    return False

# ==========================================
# GESTÃO DE DOCUMENTOS (O "Clipe" do Processo)
# ==========================================
def adicionar_documento(db: Session, processo_id: int, nome_arquivo: str, tipo_documento: str, caminho_arquivo: str):
    novo_doc = Documento(
        processo_id=processo_id,  # É aqui que amarramos o PDF à Maria!
        nome_arquivo=nome_arquivo,
        tipo_documento=tipo_documento,
        caminho_arquivo=caminho_arquivo
    )
    db.add(novo_doc)
    db.commit()
    db.refresh(novo_doc)
    return novo_doc

def listar_documentos_do_processo(db: Session, processo_id: int):
    # Busca todos os documentos onde o 'processo_id' seja igual ao do cliente
    return db.query(Documento).filter(Documento.processo_id == processo_id).all()


# ==========================================
# GESTÃO DE TAREFAS (O Dashboard / Kanban)
# ==========================================
def criar_tarefa(db: Session, processo_id: int, descricao: str, responsavel: str = None):
    nova_tarefa = Tarefa(
        processo_id=processo_id, # Amarra a tarefa à Maria
        descricao=descricao,
        responsavel=responsavel
    )
    db.add(nova_tarefa)
    db.commit()
    db.refresh(nova_tarefa)
    return nova_tarefa

def listar_tarefas_do_processo(db: Session, processo_id: int):
    return db.query(Tarefa).filter(Tarefa.processo_id == processo_id).all()


# (Adicione estas funções no final do seu crud.py)

def listar_todas_tarefas(db: Session):
    # Puxa todas as tarefas do cartório, ordenadas pelas mais antigas primeiro
    return db.query(Tarefa).order_by(Tarefa.id.asc()).all()

def atualizar_status_tarefa(db: Session, tarefa_id: int, concluida: bool):
    # Procura a tarefa pelo ID e muda o status dela
    tarefa = db.query(Tarefa).filter(Tarefa.id == tarefa_id).first()
    if tarefa:
        tarefa.status = "Concluída" if concluida else "Pendente"
        db.commit()
        db.refresh(tarefa)
    return tarefa


# (Adicione esta função no final do seu crud.py)

def obter_estatisticas_dashboard(db: Session):
    # Conta quantos processos existem no total
    total_processos = db.query(Processo).count()

    # Conta apenas as tarefas que ainda NÃO foram concluídas
    tarefas_pendentes = db.query(Tarefa).filter(Tarefa.status == "Pendente").count()

    # Conta quantos documentos físicos já foram salvos no banco
    total_documentos = db.query(Documento).count()

    return {
        "processos": total_processos,
        "tarefas_pendentes": tarefas_pendentes,
        "documentos": total_documentos
    }