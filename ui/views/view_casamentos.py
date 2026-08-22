import os
import random
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QScrollArea, QGridLayout, QComboBox,
                             QStackedWidget, QMessageBox, QGraphicsOpacityEffect)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QIcon, QColor, QFont

from ui.componentes import BarraPesquisa

# ==========================================
# MOTOR DE DADOS EM MEMÓRIA (TOTALMENTE FUNCIONAL)
# ==========================================
DADOS_CASAMENTOS = [
    {
        "protocolo": "CAS-2026-0042", "noivos": "João Silva e Maria Santos",
        "data_entrada": "17/08/2026", "data_prevista": "20/09/2026",
        "status": "Em Andamento", "pendencias": 2,
        "detalhes": {
            "noivo_nome": "João Silva", "noivo_tel": "(81) 99999-1111", "noivo_email": "joaosilva@email.com",
            "noiva_nome": "Maria Santos", "noiva_tel": "(81) 99999-2222", "noiva_email": "mariasantos@email.com",
            "regime": "Comunhão Parcial", "data_casamento": "20/09/2026 às 16:00",
            "oficial": "Kauan Feitosa", "obs": "Casal veio por indicação da noiva."
        }
    },
    {
        "protocolo": "CAS-2026-0041", "noivos": "Lucas Lima e Ana Oliveira",
        "data_entrada": "16/08/2026", "data_prevista": "15/09/2026",
        "status": "Aguardando Docs", "pendencias": 3,
        "detalhes": {
            "noivo_nome": "Lucas Lima", "noivo_tel": "(81) 98888-1111", "noivo_email": "lucas@email.com",
            "noiva_nome": "Ana Oliveira", "noiva_tel": "(81) 98888-2222", "noiva_email": "ana@email.com",
            "regime": "Separação Total", "data_casamento": "15/09/2026 às 10:00",
            "oficial": "Kauan Feitosa", "obs": "Falta RG atualizado do noivo."
        }
    },
    {
        "protocolo": "CAS-2026-0039", "noivos": "Rafael Alves e Beatriz Ferreira",
        "data_entrada": "14/08/2026", "data_prevista": "12/09/2026",
        "status": "Concluído", "pendencias": 0,
        "detalhes": {
            "noivo_nome": "Rafael Alves", "noivo_tel": "(81) 97777-1111", "noivo_email": "rafael@email.com",
            "noiva_nome": "Beatriz Ferreira", "noiva_tel": "(81) 97777-2222", "noiva_email": "beatriz@email.com",
            "regime": "Comunhão Universal", "data_casamento": "12/09/2026 às 14:00",
            "oficial": "Kauan Feitosa", "obs": "Documentação 100% aprovada."
        }
    }
]


class TelaCasamentos(QWidget):
    def __init__(self):
        super().__init__()

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ==========================================
        # PAINEL ESQUERDO (LISTA MASTER)
        # ==========================================
        self.painel_esq = QWidget()
        self.painel_esq.setStyleSheet("background-color: #0B0E14;")
        layout_esq = QVBoxLayout(self.painel_esq)
        layout_esq.setContentsMargins(30, 30, 20, 30)
        layout_esq.setSpacing(20)

        # --- CABEÇALHO COM O BOTÃO DE ADICIONAR FORA ---
        box_topo_esq = QHBoxLayout()
        lbl_titulo = QLabel("Casamentos")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")

        btn_novo_casamento = QPushButton("+ Adicionar Casamento")
        btn_novo_casamento.setStyleSheet(
            "background-color: #2962FF; color: white; font-weight: bold; padding: 10px 18px; border-radius: 6px; font-size: 13px;")
        btn_novo_casamento.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_novo_casamento.clicked.connect(self.adicionar_novo_casamento)  # Ação real!

        box_topo_esq.addWidget(lbl_titulo)
        box_topo_esq.addStretch()
        box_topo_esq.addWidget(btn_novo_casamento)
        layout_esq.addLayout(box_topo_esq)

        # --- KPIs (4 CARDS) ---
        layout_kpis = QHBoxLayout()
        layout_kpis.setSpacing(15)
        layout_kpis.addWidget(self.criar_kpi_card("Total", "42", "Este mês"))
        layout_kpis.addWidget(self.criar_kpi_card("Em Andamento", "18", "42,8%", "#f39c12"))
        layout_kpis.addWidget(self.criar_kpi_card("Pendências", "9", "21,4%", "#e74c3c"))
        layout_kpis.addWidget(self.criar_kpi_card("Concluídos", "15", "35,7%", "#2ecc71"))
        layout_esq.addLayout(layout_kpis)

        # --- FILTROS E PESQUISA ---
        layout_filtros = QHBoxLayout()
        self.pesquisa = BarraPesquisa(placeholder="🔍 Pesquisar por nome, protocolo...")
        self.pesquisa.textChanged.connect(self.filtrar_lista)

        btn_filtro = QPushButton(" 🜲 Filtros")
        btn_filtro.setStyleSheet(
            "background-color: #151A27; border: 1px solid #1E2532; padding: 10px 15px; border-radius: 6px; color: white;")
        btn_filtro.setCursor(Qt.CursorShape.PointingHandCursor)

        combo_ordem = QComboBox()
        combo_ordem.addItems(["Mais recentes", "Mais antigos", "Urgentes"])
        combo_ordem.setStyleSheet(
            "background-color: #151A27; border: 1px solid #1E2532; padding: 10px; border-radius: 6px; color: white;")

        layout_filtros.addWidget(self.pesquisa)
        layout_filtros.addWidget(btn_filtro)
        layout_filtros.addWidget(combo_ordem)
        layout_esq.addLayout(layout_filtros)

        # --- TABELA DE CASAMENTOS (Layout Ajustado) ---
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(["Protocolo", "Noivos", "Entrada", "Prevista", "Status", "Pend."])
        self.tabela.setAlternatingRowColors(True)
        self.tabela.verticalHeader().setDefaultSectionSize(55)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setShowGrid(False)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.tabela.setStyleSheet("""
            QTableWidget { background-color: #0B0E14; alternate-background-color: #11151F; border: 1px solid #1E2532; border-radius: 8px; outline: none; }
            QTableWidget::item { border: none; padding-left: 5px; }
            QTableWidget::item:selected { background-color: #1A2133; color: white; }
            QHeaderView::section { background-color: transparent; color: #8A92A6; font-weight: bold; font-size: 12px; border: none; border-bottom: 1px solid #1E2532; padding: 12px 5px; text-align: left; }
        """)

        # Ajuste Fino Cirúrgico das Colunas (Evita esmagamento)
        header = self.tabela.horizontalHeader()
        self.tabela.setColumnWidth(0, 115)  # Protocolo
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Noivos estica
        self.tabela.setColumnWidth(2, 85)  # Entrada
        self.tabela.setColumnWidth(3, 85)  # Prevista
        self.tabela.setColumnWidth(4, 115)  # Status (Espaço para a pílula)
        self.tabela.setColumnWidth(5, 55)  # Pendências

        self.tabela.itemSelectionChanged.connect(self.ao_selecionar_casamento)
        layout_esq.addWidget(self.tabela)

        # ==========================================
        # PAINEL DIREITO (DETALHES COM ANIMAÇÃO)
        # ==========================================
        self.painel_dir = QFrame()
        self.painel_dir.setStyleSheet("background-color: #11151F; border-left: 1px solid #1E2532;")
        self.painel_dir.setMinimumWidth(500)
        self.painel_dir.setMaximumWidth(600)

        # --- EFEITO DE ANIMAÇÃO FADE-IN ---
        self.efeito_opacidade = QGraphicsOpacityEffect(self.painel_dir)
        self.painel_dir.setGraphicsEffect(self.efeito_opacidade)
        self.animacao_fade = QPropertyAnimation(self.efeito_opacidade, b"opacity")
        self.animacao_fade.setDuration(300)  # 300 milissegundos
        self.animacao_fade.setStartValue(0.0)
        self.animacao_fade.setEndValue(1.0)
        self.animacao_fade.setEasingCurve(QEasingCurve.Type.InOutQuad)

        layout_dir_base = QVBoxLayout(self.painel_dir)
        layout_dir_base.setContentsMargins(0, 0, 0, 0)

        scroll_dir = QScrollArea()
        scroll_dir.setWidgetResizable(True)
        scroll_dir.setStyleSheet("border: none; background-color: transparent;")

        self.container_dir = QWidget()
        self.layout_dir = QVBoxLayout(self.container_dir)
        self.layout_dir.setContentsMargins(30, 30, 30, 30)
        self.layout_dir.setSpacing(25)

        scroll_dir.setWidget(self.container_dir)
        layout_dir_base.addWidget(scroll_dir)

        # Divisão da tela
        layout_principal.addWidget(self.painel_esq, 6)
        layout_principal.addWidget(self.painel_dir, 4)

        self.carregar_tabela()

    # ==========================================
    # LÓGICA DE DADOS (LISTA ESQUERDA)
    # ==========================================
    def adicionar_novo_casamento(self):
        """Simula a criação de um processo real para testar a reatividade da tela"""
        id_aleatorio = random.randint(100, 999)
        novo = {
            "protocolo": f"CAS-2026-0{id_aleatorio}", "noivos": "Novo Casal Exemplo",
            "data_entrada": "21/08/2026", "data_prevista": "21/09/2026",
            "status": "Em Andamento", "pendencias": 1,
            "detalhes": {
                "noivo_nome": "Exemplo Noivo", "noivo_tel": "(00) 00000-0000", "noivo_email": "noivo@email.com",
                "noiva_nome": "Exemplo Noiva", "noiva_tel": "(00) 00000-0000", "noiva_email": "noiva@email.com",
                "regime": "Não Definido", "data_casamento": "A definir",
                "oficial": "Kauan Feitosa", "obs": "Criado via botão superior."
            }
        }
        DADOS_CASAMENTOS.insert(0, novo)  # Coloca no topo
        self.carregar_tabela()
        self.tabela.selectRow(0)  # Já foca no novo automaticamente
        QMessageBox.information(self, "Sucesso", "Novo processo de casamento iniciado com sucesso!")

    def carregar_tabela(self, termo=""):
        self.tabela.setRowCount(0)
        dados_filtrados = [c for c in DADOS_CASAMENTOS if
                           termo in c['noivos'].lower() or termo in c['protocolo'].lower()]

        self.tabela.setRowCount(len(dados_filtrados))
        for linha, c in enumerate(dados_filtrados):
            # Usando QTableWidgetItem nativo para evitar os quadrados cinzas de fundo
            item_prot = QTableWidgetItem(c['protocolo'])
            item_prot.setForeground(QColor("#8A92A6"))
            self.tabela.setItem(linha, 0, item_prot)

            item_noivos = QTableWidgetItem(c['noivos'])
            item_noivos.setForeground(QColor("white"))
            font = item_noivos.font()
            font.setBold(True)
            item_noivos.setFont(font)
            self.tabela.setItem(linha, 1, item_noivos)

            item_ent = QTableWidgetItem(c['data_entrada'])
            item_ent.setForeground(QColor("#E2E8F0"))
            self.tabela.setItem(linha, 2, item_ent)

            item_prev = QTableWidgetItem(c['data_prevista'])
            item_prev.setForeground(QColor("#E2E8F0"))
            self.tabela.setItem(linha, 3, item_prev)

            # Status Badge (Corrigido com fundo transparente no wrapper)
            lbl_status = QLabel(c['status'])
            lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if c['status'] == "Em Andamento":
                lbl_status.setStyleSheet(
                    "background-color: rgba(41, 98, 255, 0.15); color: #2962FF; padding: 4px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;")
            elif c['status'] == "Concluído":
                lbl_status.setStyleSheet(
                    "background-color: rgba(46, 204, 113, 0.15); color: #2ecc71; padding: 4px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;")
            else:
                lbl_status.setStyleSheet(
                    "background-color: rgba(243, 156, 18, 0.15); color: #f39c12; padding: 4px 10px; border-radius: 10px; font-weight: bold; font-size: 11px;")
            self.tabela.setCellWidget(linha, 4, self.wrap_widget(lbl_status))

            # Pendências
            if c['pendencias'] > 0:
                lbl_pend = QLabel(str(c['pendencias']))
                lbl_pend.setStyleSheet(
                    "background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border-radius: 10px; font-weight: bold; font-size: 11px; border: 1px solid #e74c3c;")
            else:
                lbl_pend = QLabel("✓")
                lbl_pend.setStyleSheet(
                    "background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border-radius: 10px; font-weight: bold; font-size: 11px; border: 1px solid #2ecc71;")

            lbl_pend.setFixedSize(20, 20)
            lbl_pend.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela.setCellWidget(linha, 5, self.wrap_widget(lbl_pend))

        if dados_filtrados:
            self.tabela.selectRow(0)

    def filtrar_lista(self):
        self.carregar_tabela(self.pesquisa.text().lower())

    def wrap_widget(self, widget):
        """O SEGREDO PARA EVITAR O QUADRADO CINZA: background-color: transparent!"""
        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout = QHBoxLayout(container)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(widget)
        return container

    # ==========================================
    # LÓGICA DO PAINEL DIREITO (FUNCIONAL E ANIMADO)
    # ==========================================
    def ao_selecionar_casamento(self):
        linhas_selecionadas = self.tabela.selectedItems()
        if not linhas_selecionadas and self.tabela.currentRow() == -1: return

        linha = self.tabela.currentRow()
        protocolo = self.tabela.item(linha, 0).text()

        dados = next((c for c in DADOS_CASAMENTOS if c["protocolo"] == protocolo), None)
        if dados:
            self.construir_painel_direito(dados)
            self.animacao_fade.start()  # 🎬 Dispara a animação Fade-in!

    def construir_painel_direito(self, dados):
        # Limpeza Total da área direita
        for i in reversed(range(self.layout_dir.count())):
            widget = self.layout_dir.itemAt(i).widget()
            if widget: widget.deleteLater()
            layout = self.layout_dir.itemAt(i).layout()
            if layout: self.limpar_layout_interno(layout)

        # --- HEADER DO PAINEL DIREITO ---
        layout_header = QHBoxLayout()
        lbl_prot = QLabel(dados['protocolo'])
        lbl_prot.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")

        lbl_status = QLabel(dados['status'])
        lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if dados['status'] == "Em Andamento":
            lbl_status.setStyleSheet(
                "background-color: rgba(41, 98, 255, 0.15); color: #2962FF; padding: 6px 12px; border-radius: 12px; font-weight: bold; font-size: 11px;")
        else:
            lbl_status.setStyleSheet(
                "background-color: rgba(243, 156, 18, 0.15); color: #f39c12; padding: 6px 12px; border-radius: 12px; font-weight: bold; font-size: 11px;")

        layout_header.addWidget(lbl_prot)
        layout_header.addWidget(lbl_status)
        layout_header.addStretch()
        self.layout_dir.addLayout(layout_header)

        # --- ABAS FUNCIONAIS (GERENCIADOR DE ESTADO) ---
        layout_abas = QHBoxLayout()
        abas = ["Geral", "Documentos", "Pagamentos", "Tarefas", "Histórico"]
        self.botoes_abas = []

        for i, aba in enumerate(abas):
            btn = QPushButton(aba)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            # O truque do lambda para passar o índice no clique
            btn.clicked.connect(lambda checked, idx=i: self.trocar_aba(idx))
            self.botoes_abas.append(btn)
            layout_abas.addWidget(btn)
        layout_abas.addStretch()
        self.layout_dir.addLayout(layout_abas)

        # --- CONTEÚDO MUTÁVEL (O STACKED WIDGET) ---
        self.stack_abas = QStackedWidget()

        # Página 0: Geral (Completa)
        page_geral = QWidget()
        layout_geral = QVBoxLayout(page_geral)
        layout_geral.setContentsMargins(0, 10, 0, 0)
        self.montar_aba_geral(layout_geral, dados)
        self.stack_abas.addWidget(page_geral)

        # Páginas Auxiliares (1 a 4) - Funcionais para demonstrar troca de abas
        for nome_aba in abas[1:]:
            page = QWidget()
            layout_page = QVBoxLayout(page)
            lbl_temp = QLabel(f"O módulo '{nome_aba}' está em construção.")
            lbl_temp.setStyleSheet("color: #8A92A6; font-size: 14px;")
            lbl_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_page.addWidget(lbl_temp)
            self.stack_abas.addWidget(page)

        self.layout_dir.addWidget(self.stack_abas)

        # Inicia na aba Geral (Índice 0)
        self.trocar_aba(0)
        self.layout_dir.addStretch()

    def trocar_aba(self, index):
        """Muda o widget visível e pinta o botão clicado de Azul"""
        self.stack_abas.setCurrentIndex(index)
        for i, btn in enumerate(self.botoes_abas):
            if i == index:
                btn.setStyleSheet(
                    "background: transparent; color: white; border-bottom: 2px solid #2962FF; padding-bottom: 5px; font-weight: bold; border-top: none; border-left: none; border-right: none; outline: none;")
            else:
                btn.setStyleSheet(
                    "background: transparent; color: #8A92A6; border-bottom: 2px solid transparent; padding-bottom: 5px; border-top: none; border-left: none; border-right: none; outline: none;")

    def montar_aba_geral(self, layout, dados):
        """Constrói todo o miolo do painel 'Geral'"""
        lbl_info_tit = QLabel("Informações do Casamento")
        lbl_info_tit.setStyleSheet("font-size: 14px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(lbl_info_tit)

        grid_info = QGridLayout()
        grid_info.setSpacing(20)

        grid_info.addWidget(
            self.criar_bloco_pessoa("👤 Noivo", dados['detalhes']['noivo_nome'], dados['detalhes']['noivo_tel'],
                                    dados['detalhes']['noivo_email']), 0, 0)
        grid_info.addWidget(
            self.criar_bloco_pessoa("👩 Noiva", dados['detalhes']['noiva_nome'], dados['detalhes']['noiva_tel'],
                                    dados['detalhes']['noiva_email']), 0, 1)
        grid_info.addWidget(self.criar_bloco_info("⚖️ Regime de Bens", dados['detalhes']['regime']), 1, 0)
        grid_info.addWidget(self.criar_bloco_info("📅 Data do Casamento", dados['detalhes']['data_casamento']), 1, 1)
        grid_info.addWidget(self.criar_bloco_info("📥 Data de Entrada", dados['data_entrada']), 2, 0)
        grid_info.addWidget(self.criar_bloco_info("🧑‍⚖️ Oficial Responsável", dados['detalhes']['oficial']), 2, 1)
        layout.addLayout(grid_info)

        layout_cards_inferiores = QHBoxLayout()
        layout_cards_inferiores.setSpacing(15)
        layout_cards_inferiores.setContentsMargins(0, 15, 0, 0)

        # Card Documentos
        card_docs = QFrame()
        card_docs.setStyleSheet("background-color: #151A27; border: 1px solid #1E2532; border-radius: 8px;")
        layout_docs = QVBoxLayout(card_docs)
        lbl_doc_tit = QLabel("Documentos Necessários")
        lbl_doc_tit.setStyleSheet("color: white; font-weight: bold; border: none;")
        layout_docs.addWidget(lbl_doc_tit)

        layout_docs.addWidget(self.criar_item_doc("Documentos Pessoais (RG e CPF)", "Entregue"))
        layout_docs.addWidget(self.criar_item_doc("Certidão de Nascimento", "Entregue"))
        layout_docs.addWidget(
            self.criar_item_doc("Comprovante de Residência", "Pendente" if dados['pendencias'] > 0 else "Entregue"))

        btn_gerenciar = QPushButton("Gerenciar Documentos")
        btn_gerenciar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_gerenciar.setStyleSheet(
            "background-color: transparent; border: 1px solid #2C364C; color: white; padding: 8px; border-radius: 6px; margin-top: 10px;")
        btn_gerenciar.clicked.connect(
            lambda: QMessageBox.information(self, "Ação", "Abrindo o gerenciador de documentos..."))
        layout_docs.addWidget(btn_gerenciar)

        # Card Ações
        card_acoes = QFrame()
        card_acoes.setStyleSheet("background-color: #151A27; border: 1px solid #1E2532; border-radius: 8px;")
        layout_acoes = QVBoxLayout(card_acoes)
        lbl_acoes_tit = QLabel("Ações Rápidas")
        lbl_acoes_tit.setStyleSheet("color: white; font-weight: bold; border: none;")
        layout_acoes.addWidget(lbl_acoes_tit)

        botoes = ["🖨️ Imprimir Requerimento", "📋 Gerar Check-list", "📅 Agendar Casamento"]
        for b in botoes:
            btn = QPushButton(b)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(
                "background-color: transparent; border: 1px solid #2C364C; color: #E2E8F0; text-align: left; padding: 10px; border-radius: 6px;")
            btn.clicked.connect(
                lambda checked, nome=b: QMessageBox.information(self, "Ação Disparada", f"Você clicou em: {nome}"))
            layout_acoes.addWidget(btn)

        layout_cards_inferiores.addWidget(card_docs, 6)
        layout_cards_inferiores.addWidget(card_acoes, 4)
        layout.addLayout(layout_cards_inferiores)

    def criar_kpi_card(self, titulo, valor, subtitulo, cor_destaque="#FFFFFF"):
        card = QFrame()
        card.setProperty("class", "card")
        card.setStyleSheet("background-color: #151A27; border: 1px solid #1E2532; border-radius: 8px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #8A92A6; font-size: 12px; font-weight: bold; border: none;")
        lbl_val = QLabel(valor)
        lbl_val.setStyleSheet(f"color: {cor_destaque}; font-size: 28px; font-weight: bold; border: none;")
        lbl_sub = QLabel(subtitulo)
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 11px; border: none;")
        layout.addWidget(lbl_tit)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)
        return card

    def limpar_layout_interno(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.limpar_layout_interno(item.layout())

    def criar_bloco_pessoa(self, titulo, nome, tel, email):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #8A92A6; font-size: 12px;")
        lbl_nome = QLabel(nome)
        lbl_nome.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        lbl_tel = QLabel(f"📞 {tel}")
        lbl_tel.setStyleSheet("color: #8A92A6; font-size: 11px;")
        lbl_email = QLabel(f"✉️ {email}")
        lbl_email.setStyleSheet("color: #8A92A6; font-size: 11px;")
        layout.addWidget(lbl_tit)
        layout.addWidget(lbl_nome)
        layout.addWidget(lbl_tel)
        layout.addWidget(lbl_email)
        return container

    def criar_bloco_info(self, titulo, valor):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #8A92A6; font-size: 12px;")
        lbl_val = QLabel(valor)
        lbl_val.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        layout.addWidget(lbl_tit)
        layout.addWidget(lbl_val)
        return container

    def criar_item_doc(self, nome, status):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        lbl_nome = QLabel(f"📄 {nome}")
        lbl_nome.setStyleSheet("color: #E2E8F0; font-size: 12px; border: none;")
        lbl_status = QLabel(status)
        if status == "Entregue":
            lbl_status.setStyleSheet("color: #2ecc71; font-weight: bold; font-size: 11px; border: none;")
        else:
            lbl_status.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 11px; border: none;")
        layout.addWidget(lbl_nome)
        layout.addStretch()
        layout.addWidget(lbl_status)
        return container