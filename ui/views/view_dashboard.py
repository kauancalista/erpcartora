import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame)
from PyQt6.QtCore import Qt
from database.conexao import SessionLocal
from database.crud import listar_todos_processos, listar_todas_tarefas


class TelaDashboard(QWidget):
    def __init__(self):
        super().__init__()

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)
        layout_principal.setSpacing(20)

        # --- CABEÇALHO ---
        lbl_titulo = QLabel("Dashboard")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        layout_principal.addWidget(lbl_titulo)
        layout_principal.addSpacing(10)

        # ==========================================
        # LINHA 1: CARDS DE RESUMO (KPIs)
        # ==========================================
        layout_cards = QHBoxLayout()
        layout_cards.setSpacing(20)

        # Variáveis que vão guardar os números
        self.lbl_tarefas = QLabel("0")
        self.lbl_pendencias = QLabel("0")
        self.lbl_prazos = QLabel("0")
        self.lbl_docs = QLabel("0")

        # Criando os 4 cards com as cores e ícones da sua referência!
        # Parametros: Título, Label Numérica, Cor Fundo Ícone, Cor do Ícone, Emoji
        card1 = self.criar_card("Tarefas ativas", self.lbl_tarefas, "rgba(41, 98, 255, 0.15)", "#2962FF", "📋")
        card2 = self.criar_card("Pendências", self.lbl_pendencias, "rgba(231, 76, 60, 0.15)", "#e74c3c", "⚠️")
        card3 = self.criar_card("Prazos próximos", self.lbl_prazos, "rgba(241, 196, 15, 0.15)", "#f1c40f", "⏳")
        card4 = self.criar_card("Documentos totais", self.lbl_docs, "rgba(39, 174, 96, 0.15)", "#2ecc71", "📄")

        layout_cards.addWidget(card1)
        layout_cards.addWidget(card2)
        layout_cards.addWidget(card3)
        layout_cards.addWidget(card4)

        layout_principal.addLayout(layout_cards)
        layout_principal.addSpacing(20)

        # ==========================================
        # LINHA 2: ÁREA DE MÓDULOS (Esqueleto)
        # ==========================================
        # Aqui vão entrar os gráficos na próxima etapa!
        layout_modulos = QHBoxLayout()
        layout_modulos.setSpacing(20)

        # Módulo Esquerdo (Pendências e Atividades)
        mod_esq = QFrame()
        mod_esq.setProperty("class", "card")  # Puxa do estilo.qss
        mod_esq.setMinimumHeight(400)
        layout_esq = QVBoxLayout(mod_esq)
        lbl_mod_esq = QLabel("Módulo de Pendências\n(Faremos na próxima etapa)")
        lbl_mod_esq.setStyleSheet("color: #8A92A6; font-size: 16px;")
        lbl_mod_esq.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_esq.addWidget(lbl_mod_esq)

        # Módulo Direito (Gráfico de Produtividade)
        mod_dir = QFrame()
        mod_dir.setProperty("class", "card")
        mod_dir.setMinimumHeight(400)
        layout_dir = QVBoxLayout(mod_dir)
        lbl_mod_dir = QLabel("Gráfico Circular\n(Faremos na próxima etapa)")
        lbl_mod_dir.setStyleSheet("color: #8A92A6; font-size: 16px;")
        lbl_mod_dir.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_dir.addWidget(lbl_mod_dir)

        layout_modulos.addWidget(mod_esq, 1)  # Peso 1
        layout_modulos.addWidget(mod_dir, 1)  # Peso 1

        layout_principal.addLayout(layout_modulos)
        layout_principal.addStretch()

        # Calcula os números de verdade e joga nos cards
        self.carregar_dados_reais()

    def criar_card(self, titulo, label_numero, cor_fundo_icone, cor_icone, icone_texto):
        """Constrói um card responsivo com ícone estilizado"""
        card = QFrame()
        card.setProperty("class", "card")

        layout = QHBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Quadrado do Ícone (Com fundo translúcido)
        frame_icone = QFrame()
        frame_icone.setFixedSize(54, 54)
        frame_icone.setStyleSheet(f"background-color: {cor_fundo_icone}; border-radius: 12px;")
        layout_icone = QVBoxLayout(frame_icone)
        layout_icone.setContentsMargins(0, 0, 0, 0)

        lbl_icone = QLabel(icone_texto)
        lbl_icone.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icone.setStyleSheet(f"font-size: 24px; color: {cor_icone}; background: transparent;")
        layout_icone.addWidget(lbl_icone)

        # Textos (Número gigante e título)
        layout_textos = QVBoxLayout()
        layout_textos.setSpacing(2)

        label_numero.setStyleSheet("font-size: 26px; font-weight: bold; color: white; background: transparent;")
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setStyleSheet("font-size: 13px; color: #8A92A6; font-weight: bold; background: transparent;")

        layout_textos.addWidget(label_numero)
        layout_textos.addWidget(lbl_titulo)
        layout_textos.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(frame_icone)
        layout.addLayout(layout_textos)
        layout.addStretch()

        return card

    def carregar_dados_reais(self):
        """Consulta o banco de dados e atualiza os KPIs na tela"""
        db = SessionLocal()
        processos = listar_todos_processos(db)
        tarefas = listar_todas_tarefas(db)
        db.close()

        # 1. Total de Documentos
        total_docs = len(processos)
        self.lbl_docs.setText(str(total_docs))

        # 2. Pendências (Documentos travados aguardando algo)
        status_pendentes = ["Aguardando Documento", "Falta par", "Pendente", "Revisar"]
        qtd_pendencias = sum(1 for p in processos if p.status in status_pendentes)
        self.lbl_pendencias.setText(str(qtd_pendencias))

        # 3. Tarefas Ativas (Tudo que não for 'Concluída')
        qtd_tarefas = sum(1 for t in tarefas if t.status != "Concluída")
        self.lbl_tarefas.setText(str(qtd_tarefas))

        # 4. Prazos (Como ainda não temos datas no BD, deixei o número 3 fixo por enquanto)
        self.lbl_prazos.setText("3")