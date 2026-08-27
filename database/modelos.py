from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from database.conexao import Base, engine


# ==========================================
# TABELA 1: PROCESSOS (A Ficha Principal)
# ==========================================
class Processo(Base):
    __tablename__ = "processos"

    id = Column(Integer, primary_key=True, index=True)
    nome_cliente = Column(String, index=True, nullable=False)
    cpf = Column(String, index=True, nullable=True)
    tipo_servico = Column(String, nullable=False)
    status = Column(String, default="Aguardando Documento")
    data_entrada = Column(DateTime, default=datetime.now)
    data_prazo = Column(DateTime, nullable=True)  # <--- NOVA GAVETA CRIADA AQUI!
    telefone_whatsapp = Column(String, nullable=True)

    # A MÁGICA: Liga o processo às suas tarefas e documentos.
    # cascade="all, delete-orphan" significa que se apagar a Maria, apaga os PDFs dela do banco junto.
    documentos = relationship("Documento", back_populates="processo", cascade="all, delete-orphan")
    tarefas = relationship("Tarefa", back_populates="processo", cascade="all, delete-orphan")


# ==========================================
# TABELA 2: DOCUMENTOS (Os Arquivos Físicos)
# ==========================================
class Documento(Base):
    __tablename__ = "documentos"

    id = Column(Integer, primary_key=True, index=True)
    nome_arquivo = Column(String, nullable=False)  # Ex: "maria_santos_principal.pdf"
    tipo_documento = Column(String)  # Ex: "Certidão", "Anexo CRAS"
    caminho_arquivo = Column(String, nullable=False)  # Ex: "C:/Cartorio/2026/Agosto/maria.pdf"

    # A Chave Estrangeira: "Eu pertenço ao Processo X"
    processo_id = Column(Integer, ForeignKey("processos.id"))

    processo = relationship("Processo", back_populates="documentos")


# ==========================================
# TABELA 3: TAREFAS (O Dashboard / Kanban)
# ==========================================
class Tarefa(Base):
    __tablename__ = "tarefas"

    id = Column(Integer, primary_key=True, index=True)
    descricao = Column(String, nullable=False)  # Ex: "Revisar assinatura"
    responsavel = Column(String, nullable=True)  # Ex: "Kauã"
    status = Column(String, default="Pendente")  # "Pendente" ou "Concluída"
    data_criacao = Column(DateTime, default=datetime.now)

    processo_id = Column(Integer, ForeignKey("processos.id"))

    processo = relationship("Processo", back_populates="tarefas")




# ==========================================
# TABELA 4: CASAMENTOS
# ==========================================
class Casamento(Base):
    __tablename__ = "casamentos"
    id = Column(Integer, primary_key=True, index=True)
    protocolo = Column(String, unique=True, index=True, nullable=False)

    # Dados dos Noivos
    nome_noivo = Column(String, nullable=False)
    nome_noiva = Column(String, nullable=False)
    telefone_contato = Column(String, nullable=True)

    # Informações do Processo
    data_entrada = Column(String, nullable=False)
    data_celebracao = Column(String, nullable=False)
    horario_celebracao = Column(String, nullable=True)

    # Controle e Status (A Mágica Interativa)
    docs_entregues = Column(String, nullable=True)  # Guarda o JSON com as checkboxes
    taxa_status = Column(String, default="Aguardando")  # Aguardando, Pago ou Isento
    status = Column(String, default="Aguardando Docs")
    pendencias = Column(Integer, default=0)

# ==========================================
# TABELA 5: COMPROMISSOS (Agenda)
# ==========================================
class Compromisso(Base):
    __tablename__ = "compromissos"
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String, nullable=False)
    data = Column(String, nullable=False) # Formato DD/MM/YYYY
    hora = Column(String, nullable=False) # Formato HH:MM
    tipo = Column(String, default="Reunião")
    lembrete = Column(String, nullable=True)
    link_reuniao = Column(String, nullable=True)
    status = Column(String, default="Confirmado")

# ==========================================
# ATUALIZA O BANCO DE DADOS
# ==========================================
# Ao rodar isso, o SQLAlchemy cria as duas novas tabelas automaticamente
Base.metadata.create_all(bind=engine)