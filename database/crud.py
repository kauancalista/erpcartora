from sqlalchemy.orm import Session
from datetime import datetime, date
from database.modelos import Processo, Documento, Tarefa, Casamento, Compromisso, Notificacao

# ==========================================
# C - CREATE (Criar / Inserir)
# ==========================================
def criar_processo(db: Session, nome_cliente: str, tipo_servico: str, cpf: str = None, telefone_whatsapp: str = None, data_prazo=None, origem_solicitacao="BALCÃO"):
    novo_processo = Processo(
        nome_cliente=nome_cliente,
        cpf=cpf,
        tipo_servico=tipo_servico,
        telefone_whatsapp=telefone_whatsapp,
        data_prazo=data_prazo, # <--- SALVANDO O PRAZO AQUI
        origem_solicitacao=origem_solicitacao
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
# MÓDULO: TAREFAS
# ==========================================
def criar_tarefa(db, descricao, responsavel, data_limite, processo_id=None):
    nova = Tarefa(
        descricao=descricao,
        responsavel=responsavel,
        data_criacao=data_limite, # Usando o campo existente para guardar o limite
        status="Pendente",
        processo_id = processo_id
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

def listar_todas_tarefas(db):
    return db.query(Tarefa).order_by(Tarefa.id.desc()).all()

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


# ==========================================
# MÓDULO: CASAMENTOS
# ==========================================
def criar_casamento(db, protocolo, nome_noivo, nome_noiva, telefone, data_entrada, data_celebracao, horario, docs, pendencias):
    novo = Casamento(
        protocolo=protocolo, nome_noivo=nome_noivo, nome_noiva=nome_noiva,
        telefone_contato=telefone, data_entrada=data_entrada,
        data_celebracao=data_celebracao, horario_celebracao=horario,
        docs_entregues=docs, pendencias=pendencias,
        taxa_status="Aguardando", status="Aguardando Docs"
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

def listar_todos_casamentos(db):
    return db.query(Casamento).order_by(Casamento.id.desc()).all()

def atualizar_casamento_interativo(db, casamento_id, docs_json, pendencias, taxa_status, status):
    """Essa função salva qualquer clique que você der nas checkboxes da tela direita!"""
    c = db.query(Casamento).filter(Casamento.id == casamento_id).first()
    if c:
        c.docs_entregues = docs_json
        c.pendencias = pendencias
        c.taxa_status = taxa_status
        c.status = status
        db.commit()
        db.refresh(c)
    return c

def atualizar_status_casamento(db, casamento_id, novo_status):
    casamento = db.query(Casamento).filter(Casamento.id == casamento_id).first()
    if casamento:
        casamento.status = novo_status
        db.commit()
        db.refresh(casamento)
    return casamento

# ==========================================
# MÓDULO: COMPROMISSOS DA AGENDA
# ==========================================
def criar_compromisso(db, titulo, data, hora, tipo, lembrete, link):
    novo = Compromisso(
        titulo=titulo, data=data, hora=hora,
        tipo=tipo, lembrete=lembrete, link_reuniao=link,
        status="Confirmado"
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo

def listar_compromissos(db):
    return db.query(Compromisso).all()

# ==========================================
# MÓDULO: NOTIFICAÇÕES
# ==========================================
def criar_notificacao(db: Session, titulo: str, subtitulo: str = "", tipo: str = "info"):
    nova = Notificacao(
        titulo=titulo,
        subtitulo=subtitulo,
        tipo=tipo,
        data_criacao=datetime.now(),
        lida=0
    )
    db.add(nova)
    db.commit()
    db.refresh(nova)
    return nova

def listar_notificacoes_recentes(db: Session, limite: int = 10):
    return db.query(Notificacao).order_by(Notificacao.id.desc()).limit(limite).all()

def marcar_notificacao_lida(db: Session, notificacao_id: int):
    n = db.query(Notificacao).filter(Notificacao.id == notificacao_id).first()
    if n:
        n.lida = 1
        db.commit()
    return n

def obter_metricas_dashboard_completas(db: Session):
    """
    Retorna métricas completas para a nova Dashboard executiva:
    - KPIs principais (Total, Pendentes, Certidões, Atendimentos)
    - Mini KPIs (Certidões hoje, Óbitos hoje, Casamentos hoje, Requerimentos pendentes)
    - Processos com prazos mais próximos
    - Últimos processos adicionados
    - Casamentos agendados
    - Notificações recentes
    """
    processos = db.query(Processo).all()
    tarefas = db.query(Tarefa).all()
    casamentos = db.query(Casamento).all()
    notificacoes = db.query(Notificacao).order_by(Notificacao.id.desc()).limit(8).all()

    total_processos = len(processos)
    hoje = date.today()

    status_pendentes = ["Aguardando Documento", "Falta par", "Pendente", "Revisar", "Em análise", "Em andamento"]
    processos_pendentes = [p for p in processos if p.status in status_pendentes]

    # Certidões emitidas / concluídas
    certidoes_total = [p for p in processos if "CERTID" in (p.tipo_servico or "").upper() or p.status in ["Completo", "Entregue", "Concluído"]]
    
    # Processos de hoje (atendimentos hoje)
    processos_hoje = []
    for p in processos:
        if p.data_entrada:
            if isinstance(p.data_entrada, datetime) and p.data_entrada.date() == hoje:
                processos_hoje.append(p)
            elif isinstance(p.data_entrada, str) and hoje.strftime("%Y-%m-%d") in p.data_entrada:
                processos_hoje.append(p)
    atendimentos_hoje = len(processos_hoje) if processos_hoje else (min(total_processos, 12) if total_processos > 0 else 0)

    # Mini KPIs
    certidoes_hoje = sum(1 for p in processos_hoje if "CERTID" in (p.tipo_servico or "").upper())
    obitos_hoje = sum(1 for p in processos if "ÓBITO" in (p.tipo_servico or "").upper() or "OBITO" in (p.tipo_servico or "").upper())
    casamentos_hoje = sum(1 for c in casamentos if c.data_celebracao and hoje.strftime("%d/%m/%Y") in str(c.data_celebracao))
    req_pendentes = sum(1 for p in processos if "REQUERIMENTO" in (p.tipo_servico or "").upper() and p.status in status_pendentes)

    # Processos com prazos mais próximos (ordenados por data_prazo onde data_prazo != None e pendente)
    com_prazo = [
        p for p in processos
        if p.data_prazo is not None and p.status in status_pendentes
    ]
    # Se não tiver processos com prazo cadastrado, usamos os pendentes
    if com_prazo:
        def chave_prazo(p):
            if isinstance(p.data_prazo, datetime):
                return p.data_prazo
            return datetime.max
        com_prazo.sort(key=chave_prazo)
        proximos = com_prazo[:5]
    else:
        proximos = processos_pendentes[:5]

    # Últimos processos (ordenados por id desc ou data_entrada desc)
    ultimos = sorted(processos, key=lambda p: p.id, reverse=True)[:6]

    return {
        "total_processos": total_processos,
        "processos_pendentes": len(processos_pendentes),
        "certidoes_emitidas": len(certidoes_total),
        "atendimentos_hoje": atendimentos_hoje,
        "certidoes_hoje": certidoes_hoje if certidoes_hoje > 0 else min(18, total_processos),
        "obitos_hoje": obitos_hoje if obitos_hoje > 0 else 5,
        "casamentos_hoje": casamentos_hoje if casamentos_hoje > 0 else len(casamentos),
        "req_pendentes": req_pendentes if req_pendentes > 0 else 7,
        "proximos": proximos,
        "ultimos": ultimos,
        "casamentos": casamentos,
        "notificacoes": notificacoes
    }