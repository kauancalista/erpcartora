import os
import random
from datetime import datetime
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
                             QPushButton, QScrollArea, QGridLayout, QComboBox,
                             QStackedWidget, QMessageBox, QGraphicsOpacityEffect,
                             QLineEdit, QFormLayout, QCheckBox, QRadioButton)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QCursor, QFont

from database.conexao import SessionLocal
from database.crud import (listar_todos_casamentos, criar_casamento,
                           atualizar_casamento_interativo, atualizar_status_casamento)
from ui.componentes import BarraPesquisa, LabelStatus, wrap_transparente, obter_estilo_status, notificar
from ui.modulo_impressao import DialogImpressao  # <-- O MOTOR DE IMPRESSÃO AQUI!


class TelaCasamentos(QWidget):
    def __init__(self):
        super().__init__()
        self.todos_casamentos = []

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ==========================================
        # PAINEL ESQUERDO (A Mágica da Transição)
        # ==========================================
        self.painel_esq_base = QWidget()
        self.painel_esq_base.setStyleSheet("background-color: #0B0E14;")
        layout_esq_base = QVBoxLayout(self.painel_esq_base)
        layout_esq_base.setContentsMargins(0, 0, 0, 0)

        self.stack_esq = QStackedWidget()
        self.efeito_fade_esq = QGraphicsOpacityEffect(self.stack_esq)
        self.stack_esq.setGraphicsEffect(self.efeito_fade_esq)
        self.animacao_esq = QPropertyAnimation(self.efeito_fade_esq, b"opacity")
        self.animacao_esq.setDuration(250)
        self.animacao_esq.setStartValue(0.0)
        self.animacao_esq.setEndValue(1.0)
        self.animacao_esq.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.pagina_lista = QWidget()
        self.pagina_form = QWidget()

        self.montar_pagina_lista()
        self.montar_pagina_form()

        self.stack_esq.addWidget(self.pagina_lista)
        self.stack_esq.addWidget(self.pagina_form)

        layout_esq_base.addWidget(self.stack_esq)

        # ==========================================
        # PAINEL DIREITO (DETALHES DA FICHA)
        # ==========================================
        self.painel_dir = QFrame()
        self.painel_dir.setStyleSheet("background-color: #11151F; border-left: 1px solid #1E2532;")
        # Removido setMinimumWidth para não quebrar a responsividade!

        self.efeito_opacidade_dir = QGraphicsOpacityEffect(self.painel_dir)
        self.painel_dir.setGraphicsEffect(self.efeito_opacidade_dir)
        self.animacao_dir = QPropertyAnimation(self.efeito_opacidade_dir, b"opacity")
        self.animacao_dir.setDuration(250)
        self.animacao_dir.setStartValue(0.0)
        self.animacao_dir.setEndValue(1.0)

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

        # Proporção de 60% Esquerda / 40% Direita
        layout_principal.addWidget(self.painel_esq_base, 6)
        layout_principal.addWidget(self.painel_dir, 4)

        self.carregar_dados_do_banco()

    # ==========================================
    # MONTAGEM DA LISTA E FORMULÁRIO (ESQUERDA)
    # ==========================================
    def montar_pagina_lista(self):
        layout = QVBoxLayout(self.pagina_lista)
        layout.setContentsMargins(30, 30, 20, 30)
        layout.setSpacing(20)

        box_topo = QHBoxLayout()
        lbl_titulo = QLabel("Casamentos")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")

        # --- NOVO BOTÃO DE IMPRIMIR AQUI ---
        btn_imprimir_form = QPushButton("🖨️ Formulário em Branco")
        btn_imprimir_form.setStyleSheet(
            "background-color: #151A27; color: white; font-weight: bold; padding: 10px 18px; border-radius: 6px; border: 1px solid #1E2532;")
        btn_imprimir_form.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_imprimir_form.clicked.connect(self.imprimir_requerimento)

        btn_novo = QPushButton("+ Formulário de Entrada")
        btn_novo.setStyleSheet(
            "background-color: #2962FF; color: white; font-weight: bold; padding: 10px 18px; border-radius: 6px;")
        btn_novo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_novo.clicked.connect(self.transicionar_para_form)

        box_botoes = QHBoxLayout()
        box_botoes.setSpacing(10)
        box_botoes.addWidget(btn_imprimir_form)
        box_botoes.addWidget(btn_novo)

        box_topo.addWidget(lbl_titulo)
        box_topo.addStretch()
        box_topo.addLayout(box_botoes)
        layout.addLayout(box_topo)

        self.lbl_kpi_total = QLabel("0")
        self.lbl_kpi_ativos = QLabel("0")
        self.lbl_kpi_pendencias = QLabel("0")
        self.lbl_kpi_concluidos = QLabel("0")

        layout_kpis = QHBoxLayout()
        layout_kpis.setSpacing(15)
        layout_kpis.addWidget(self.criar_kpi_card("Total", self.lbl_kpi_total, "Cadastros"))
        layout_kpis.addWidget(self.criar_kpi_card("Em Andamento", self.lbl_kpi_ativos, "Ativos", "#2962FF"))
        layout_kpis.addWidget(self.criar_kpi_card("Com Pendências", self.lbl_kpi_pendencias, "Atenção", "#e74c3c"))
        layout_kpis.addWidget(self.criar_kpi_card("Concluídos", self.lbl_kpi_concluidos, "Prontos", "#2ecc71"))
        layout.addLayout(layout_kpis)

        layout_filtros = QHBoxLayout()
        self.pesquisa = BarraPesquisa(placeholder="🔍 Pesquisar por noivos, protocolo...")
        self.pesquisa.textChanged.connect(self.filtrar_lista)

        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(["Exibir: Ativos", "Exibir: Todos", "Exibir: Arquivados"])
        self.combo_filtro.setStyleSheet(
            "background-color: #151A27; border: 1px solid #1E2532; padding: 8px 15px; border-radius: 6px; color: white;")
        self.combo_filtro.currentTextChanged.connect(self.filtrar_lista)

        layout_filtros.addWidget(self.pesquisa)
        layout_filtros.addWidget(self.combo_filtro)
        layout.addLayout(layout_filtros)

        self.tabela = QTableWidget()
        self.tabela.setColumnCount(6)
        self.tabela.setHorizontalHeaderLabels(["Protocolo", "Noivos", "Entrada", "Celebração", "Status", "Pend."])
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

        header = self.tabela.horizontalHeader()
        self.tabela.setColumnWidth(0, 115)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tabela.setColumnWidth(2, 85)
        self.tabela.setColumnWidth(3, 90)
        self.tabela.setColumnWidth(4, 130)
        self.tabela.setColumnWidth(5, 55)

        self.tabela.itemSelectionChanged.connect(self.ao_selecionar_casamento)
        layout.addWidget(self.tabela)

    def montar_pagina_form(self):
        layout = QVBoxLayout(self.pagina_form)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        box_topo = QHBoxLayout()
        btn_voltar = QPushButton("← Voltar")
        btn_voltar.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_voltar.setStyleSheet(
            "background-color: transparent; border: 1px solid #2C364C; color: #E2E8F0; padding: 8px 15px; border-radius: 6px;")
        btn_voltar.clicked.connect(self.transicionar_para_lista)

        lbl_titulo = QLabel("Formulário de Entrada de Casamento")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: white; margin-left: 10px;")

        box_topo.addWidget(btn_voltar)
        box_topo.addWidget(lbl_titulo)
        box_topo.addStretch()
        layout.addLayout(box_topo)

        scroll_form = QScrollArea()
        scroll_form.setWidgetResizable(True)
        scroll_form.setStyleSheet("border: none; background-color: transparent;")
        container_scroll = QWidget()
        layout_form = QVBoxLayout(container_scroll)
        layout_form.setSpacing(25)

        estilo_input = "background-color: #11151F; padding: 12px; border: 1px solid #1E2532; border-radius: 6px; color: white;"

        lbl_n = QLabel("DADOS DOS NOIVOS")
        lbl_n.setStyleSheet("color: #8A92A6; font-weight: bold;")
        layout_form.addWidget(lbl_n)

        grid_nomes = QGridLayout()
        grid_nomes.setSpacing(15)

        self.inp_noivo = QLineEdit()
        self.inp_noivo.setPlaceholderText("Nome completo do Noivo")
        self.inp_noivo.setStyleSheet(estilo_input)

        self.inp_noiva = QLineEdit()
        self.inp_noiva.setPlaceholderText("Nome completo da Noiva")
        self.inp_noiva.setStyleSheet(estilo_input)

        self.inp_tel = QLineEdit()
        self.inp_tel.setPlaceholderText("(00) 00000-0000")
        self.inp_tel.setStyleSheet(estilo_input)

        grid_nomes.addWidget(QLabel("Noivo:"), 0, 0)
        grid_nomes.addWidget(self.inp_noivo, 1, 0)
        grid_nomes.addWidget(QLabel("Noiva:"), 0, 1)
        grid_nomes.addWidget(self.inp_noiva, 1, 1)
        grid_nomes.addWidget(QLabel("Telefone / WhatsApp:"), 2, 0)
        grid_nomes.addWidget(self.inp_tel, 3, 0)
        layout_form.addLayout(grid_nomes)

        lbl_c = QLabel("COMPROVANTE DE AGENDAMENTO")
        lbl_c.setStyleSheet("color: #8A92A6; font-weight: bold; margin-top: 15px;")
        layout_form.addWidget(lbl_c)

        grid_agenda = QGridLayout()
        grid_agenda.setSpacing(15)

        self.inp_data = QLineEdit()
        self.inp_data.setPlaceholderText("DD/MM/AAAA")
        self.inp_data.setStyleSheet(estilo_input)

        self.inp_hora = QLineEdit()
        self.inp_hora.setPlaceholderText("HH:MM")
        self.inp_hora.setStyleSheet(estilo_input)

        grid_agenda.addWidget(QLabel("Data da Celebração:"), 0, 0)
        grid_agenda.addWidget(self.inp_data, 1, 0)
        grid_agenda.addWidget(QLabel("Horário:"), 0, 1)
        grid_agenda.addWidget(self.inp_hora, 1, 1)
        layout_form.addLayout(grid_agenda)

        lbl_d = QLabel("DOCUMENTOS EXIGIDOS")
        lbl_d.setStyleSheet("color: #8A92A6; font-weight: bold; margin-top: 15px;")
        layout_form.addWidget(lbl_d)

        self.checks_docs_iniciais = []
        nomes_docs = [
            "RG do Noivo", "CPF do Noivo", "RG da Noiva", "CPF da Noiva",
            "Comprovante de residência", "Certidão Noivo (Até 90 dias)",
            "Certidão Noiva (Até 90 dias)", "Documentos das Testemunhas",
            "Noivos assinaram os papéis", "Testemunhas assinaram os papéis"
        ]

        grid_docs = QGridLayout()
        estilo_check = "QCheckBox { color: white; font-size: 13px; } QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #2C364C; } QCheckBox::indicator:checked { background-color: #2962FF; border: none; }"

        row, col = 0, 0
        for doc in nomes_docs:
            chk = QCheckBox(doc)
            chk.setStyleSheet(estilo_check)
            self.checks_docs_iniciais.append(chk)
            grid_docs.addWidget(chk, row, col)
            col += 1
            if col > 1:
                col = 0
                row += 1
        layout_form.addLayout(grid_docs)

        layout_form.addStretch()
        scroll_form.setWidget(container_scroll)
        layout.addWidget(scroll_form)

        btn_salvar = QPushButton("Salvar e Gerar Protocolo")
        btn_salvar.setStyleSheet(
            "background-color: #27AE60; font-size: 15px; font-weight: bold; padding: 15px; border-radius: 8px;")
        btn_salvar.clicked.connect(self.salvar_requerimento)
        layout.addWidget(btn_salvar)

    def transicionar_para_form(self):
        self.stack_esq.setCurrentIndex(1)
        self.animacao_esq.start()

    def transicionar_para_lista(self):
        self.stack_esq.setCurrentIndex(0)
        self.animacao_esq.start()

    # ==========================================
    # CÉREBRO E BANCO DE DADOS
    # ==========================================
    def salvar_requerimento(self):
        if not self.inp_noivo.text() or not self.inp_noiva.text() or not self.inp_data.text():
            QMessageBox.warning(self, "Atenção", "Preencha os nomes e a data da celebração!")
            return

        faltando = sum(1 for chk in self.checks_docs_iniciais if not chk.isChecked())
        entregues = {chk.text(): chk.isChecked() for chk in self.checks_docs_iniciais}

        id_aleatorio = random.randint(1000, 9999)
        protocolo_gerado = f"CAS-{datetime.now().year}-{id_aleatorio:04d}"

        db = SessionLocal()
        criar_casamento(
            db, protocolo=protocolo_gerado,
            nome_noivo=self.inp_noivo.text().strip(),
            nome_noiva=self.inp_noiva.text().strip(),
            telefone=self.inp_tel.text().strip(),
            data_entrada=datetime.now().strftime("%d/%m/%Y"),
            data_celebracao=self.inp_data.text().strip(),
            horario=self.inp_hora.text().strip(),
            docs=json.dumps(entregues),
            pendencias=faltando
        )
        db.close()
        notificar(self, "Protocolo gerado com sucesso!", "sucesso")

        self.inp_noivo.clear();
        self.inp_noiva.clear()
        self.inp_tel.clear();
        self.inp_data.clear();
        self.inp_hora.clear()
        for chk in self.checks_docs_iniciais: chk.setChecked(False)

        self.transicionar_para_lista()
        self.carregar_dados_do_banco()
        self.tabela.selectRow(0)

    def carregar_dados_do_banco(self):
        db = SessionLocal()
        self.todos_casamentos = listar_todos_casamentos(db)
        db.close()

        total = len(self.todos_casamentos)
        ativos = sum(1 for c in self.todos_casamentos if c.status not in ["Concluído (OK)", "Arquivado"])
        com_pendencia = sum(1 for c in self.todos_casamentos if c.pendencias > 0 and c.status != "Arquivado")
        concluidos = sum(1 for c in self.todos_casamentos if c.status == "Concluído (OK)")

        self.lbl_kpi_total.setText(str(total))
        self.lbl_kpi_ativos.setText(str(ativos))
        self.lbl_kpi_pendencias.setText(str(com_pendencia))
        self.lbl_kpi_concluidos.setText(str(concluidos))

        self.filtrar_lista()

    def filtrar_lista(self):
        termo = self.pesquisa.text().lower().strip()
        filtro_aba = self.combo_filtro.currentText()
        self.tabela.setRowCount(0)

        dados_filtrados = []
        for c in self.todos_casamentos:
            is_ativo = c.status != "Arquivado"
            if filtro_aba == "Exibir: Ativos" and not is_ativo: continue
            if filtro_aba == "Exibir: Arquivados" and c.status != "Arquivado": continue

            noivos_texto = f"{c.nome_noivo} e {c.nome_noiva}"
            if termo in noivos_texto.lower() or termo in c.protocolo.lower():
                dados_filtrados.append(c)

        self.tabela.setRowCount(len(dados_filtrados))
        for linha, c in enumerate(dados_filtrados):
            noivos_texto = f"{c.nome_noivo} e {c.nome_noiva}"

            item_prot = QTableWidgetItem(c.protocolo)
            item_prot.setForeground(QColor("#8A92A6"))
            self.tabela.setItem(linha, 0, item_prot)

            item_noivos = QTableWidgetItem(noivos_texto)
            item_noivos.setForeground(QColor("white"))
            item_noivos.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.tabela.setItem(linha, 1, item_noivos)

            item_ent = QTableWidgetItem(c.data_entrada)
            item_ent.setForeground(QColor("#E2E8F0"))
            self.tabela.setItem(linha, 2, item_ent)

            item_prev = QTableWidgetItem(c.data_celebracao)
            item_prev.setForeground(QColor("#E2E8F0"))
            self.tabela.setItem(linha, 3, item_prev)

            self.tabela.setCellWidget(linha, 4, wrap_transparente(LabelStatus(c.status)))

            if c.pendencias > 0:
                badge_pend = LabelStatus(str(c.pendencias))
                badge_pend.setStyleSheet(
                    "background-color: rgba(231, 76, 60, 0.2); color: #e74c3c; border-radius: 12px; font-weight: bold; font-size: 11px;")
            else:
                badge_pend = LabelStatus("✓")
                badge_pend.setStyleSheet(
                    "background-color: rgba(46, 204, 113, 0.2); color: #2ecc71; border-radius: 12px; font-weight: bold; font-size: 11px;")

            self.tabela.setCellWidget(linha, 5, wrap_transparente(badge_pend))

        if dados_filtrados and self.tabela.currentRow() == -1:
            self.tabela.selectRow(0)

    # ==========================================
    # PAINEL DIREITO (AS ABAS)
    # ==========================================
    def ao_selecionar_casamento(self):
        linhas_selecionadas = self.tabela.selectedItems()
        if not linhas_selecionadas: return

        linha = self.tabela.currentRow()
        protocolo = self.tabela.item(linha, 0).text()

        casamento = next((c for c in self.todos_casamentos if c.protocolo == protocolo), None)
        if casamento:
            self.painel_dir.show()
            self.construir_painel_direito(casamento)
            self.animacao_dir.start()

    def construir_painel_direito(self, c):
        self.casamento_atual = c
        self.limpar_layout_interno(self.layout_dir)

        # CABEÇALHO
        layout_header = QHBoxLayout()
        lbl_prot = QLabel(c.protocolo)
        lbl_prot.setStyleSheet("font-size: 20px; font-weight: bold; color: white;")
        self.badge_status_direita = LabelStatus(c.status)
        layout_header.addWidget(lbl_prot)
        layout_header.addWidget(self.badge_status_direita)
        layout_header.addStretch()
        self.layout_dir.addLayout(layout_header)

        # AS ABAS (Agora todas ativas!)
        layout_abas = QHBoxLayout()
        abas = ["Geral", "Pagamentos", "Histórico"]
        self.botoes_abas = []
        for i, aba in enumerate(abas):
            btn = QPushButton(aba)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=i: self.trocar_aba(idx))
            self.botoes_abas.append(btn)
            layout_abas.addWidget(btn)
        layout_abas.addStretch()
        self.layout_dir.addLayout(layout_abas)

        # CONTAINER DAS ABAS
        self.stack_abas = QStackedWidget()

        # Página 1: GERAL
        page_geral = QWidget()
        layout_geral = QVBoxLayout(page_geral)
        layout_geral.setContentsMargins(0, 10, 0, 0)
        self.montar_aba_geral(layout_geral, c)
        self.stack_abas.addWidget(page_geral)

        # Página 2: PAGAMENTOS
        page_pag = QWidget()
        layout_pag = QVBoxLayout(page_pag)
        layout_pag.setContentsMargins(0, 10, 0, 0)
        self.montar_aba_pagamentos(layout_pag, c)
        self.stack_abas.addWidget(page_pag)

        # Página 3: HISTÓRICO
        page_hist = QWidget()
        layout_hist = QVBoxLayout(page_hist)
        layout_hist.setContentsMargins(0, 10, 0, 0)
        self.montar_aba_historico(layout_hist, c)
        self.stack_abas.addWidget(page_hist)

        self.layout_dir.addWidget(self.stack_abas)
        self.trocar_aba(0)

    def trocar_aba(self, index):
        self.stack_abas.setCurrentIndex(index)
        for i, btn in enumerate(self.botoes_abas):
            if i == index:
                btn.setStyleSheet(
                    "background: transparent; color: white; border-bottom: 2px solid #2962FF; padding-bottom: 5px; font-weight: bold; border-top: none; border-left: none; border-right: none; outline: none;")
            else:
                btn.setStyleSheet(
                    "background: transparent; color: #8A92A6; border-bottom: 2px solid transparent; padding-bottom: 5px; border-top: none; border-left: none; border-right: none; outline: none;")

    # ==========================================
    # CONTEÚDO DAS ABAS
    # ==========================================
    def montar_aba_geral(self, layout, c):
        lbl_info_tit = QLabel("Informações Gerais")
        lbl_info_tit.setStyleSheet("font-size: 14px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(lbl_info_tit)

        grid_info = QGridLayout()
        grid_info.setSpacing(20)
        tel = c.telefone_contato if c.telefone_contato else "Não informado"
        hora = c.horario_celebracao if c.horario_celebracao else "A definir"

        grid_info.addWidget(self.criar_bloco_info("👤 Noivos", f"{c.nome_noivo}\n{c.nome_noiva}"), 0, 0)
        grid_info.addWidget(self.criar_bloco_info("📞 Contato", tel), 0, 1)
        grid_info.addWidget(self.criar_bloco_info("📅 Celebração", c.data_celebracao), 1, 0)
        grid_info.addWidget(self.criar_bloco_info("🕒 Horário", hora), 1, 1)
        layout.addLayout(grid_info)

        # Checkboxes (Checklist)
        card_docs = QFrame()
        card_docs.setStyleSheet(
            "background-color: #151A27; border: 1px solid #1E2532; border-radius: 8px; margin-top: 15px;")
        layout_docs = QVBoxLayout(card_docs)
        lbl_doc_tit = QLabel("Documentos e Assinaturas (Checklist)")
        lbl_doc_tit.setStyleSheet("color: white; font-weight: bold; border: none; margin-bottom: 5px;")
        layout_docs.addWidget(lbl_doc_tit)

        try:
            dict_docs = json.loads(c.docs_entregues)
        except:
            dict_docs = {}

        self.checks_interativos = []
        estilo_check = "QCheckBox { color: #E2E8F0; font-size: 13px; margin: 4px 0; border: none; } QCheckBox::indicator { width: 18px; height: 18px; border-radius: 4px; border: 2px solid #2C364C; } QCheckBox::indicator:checked { background-color: #2962FF; border: none; }"

        for nome_doc, entregue in dict_docs.items():
            chk = QCheckBox(nome_doc)
            chk.setStyleSheet(estilo_check)
            chk.setChecked(entregue)
            chk.stateChanged.connect(self.recalcular_tudo_e_salvar)
            self.checks_interativos.append(chk)
            layout_docs.addWidget(chk)

            if c.status == "Arquivado":
                chk.setEnabled(False)

        layout.addWidget(card_docs)

        # Ações Finais (Arquivar)
        if c.status == "Concluído (OK)":
            btn_arq = QPushButton("🗄️ Arquivar / Finalizar Processo")
            btn_arq.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_arq.setStyleSheet(
                "background-color: #8E44AD; color: white; font-weight: bold; padding: 12px; border-radius: 6px; margin-top: 15px;")
            btn_arq.clicked.connect(self.arquivar_processo)
            layout.addWidget(btn_arq)
        elif c.status == "Arquivado":
            btn_rea = QPushButton("🔄 Reativar Processo (Desarquivar)")
            btn_rea.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_rea.setStyleSheet(
                "background-color: #e74c3c; color: white; font-weight: bold; padding: 12px; border-radius: 6px; margin-top: 15px;")
            btn_rea.clicked.connect(self.reativar_processo)
            layout.addWidget(btn_rea)

        layout.addStretch()


    def montar_aba_pagamentos(self, layout, c):
        lbl_pag = QLabel("Taxa do Processo e Pagamentos")
        lbl_pag.setStyleSheet("font-size: 14px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(lbl_pag)

        box_pag = QFrame()
        box_pag.setStyleSheet(
            "background-color: #151A27; border: 1px solid #1E2532; border-radius: 8px; padding: 10px;")
        layout_pag = QVBoxLayout(box_pag)

        # Instanciamos os botões aqui, mas eles vão interagir com o "recalcular_tudo_e_salvar" igual antes
        self.radio_aguardando = QRadioButton("Aguardando Pagamento")
        self.radio_pago = QRadioButton("Pago")
        self.radio_isento = QRadioButton("Isento de Taxa")

        estilo_radio = "QRadioButton { color: #E2E8F0; font-size: 14px; font-weight: bold; border: none; margin: 5px; } QRadioButton::indicator { width: 18px; height: 18px; border-radius: 9px; border: 2px solid #2C364C; background-color: transparent; } QRadioButton::indicator:checked { background-color: #27AE60; border: 2px solid #27AE60; }"
        self.radio_aguardando.setStyleSheet(estilo_radio)
        self.radio_pago.setStyleSheet(estilo_radio)
        self.radio_isento.setStyleSheet(estilo_radio)

        if c.taxa_status == "Pago":
            self.radio_pago.setChecked(True)
        elif c.taxa_status == "Isento":
            self.radio_isento.setChecked(True)
        else:
            self.radio_aguardando.setChecked(True)

        if c.status == "Arquivado":
            self.radio_aguardando.setEnabled(False)
            self.radio_pago.setEnabled(False)
            self.radio_isento.setEnabled(False)
        else:
            self.radio_aguardando.toggled.connect(self.recalcular_tudo_e_salvar)
            self.radio_pago.toggled.connect(self.recalcular_tudo_e_salvar)
            self.radio_isento.toggled.connect(self.recalcular_tudo_e_salvar)

        layout_pag.addWidget(self.radio_aguardando)
        layout_pag.addWidget(self.radio_pago)
        layout_pag.addWidget(self.radio_isento)
        layout.addWidget(box_pag)

        btn_recibo = QPushButton("🖨️ Imprimir Recibo")
        btn_recibo.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_recibo.setStyleSheet(
            "background-color: transparent; border: 1px solid #2C364C; color: white; padding: 10px; border-radius: 6px; margin-top: 10px;")
        btn_recibo.clicked.connect(lambda: notificar(self, "Recibo gerado e enviado para impressão.", "info"))
        layout.addWidget(btn_recibo)

        layout.addStretch()

    def montar_aba_historico(self, layout, c):
        lbl = QLabel("Linha do Tempo do Processo")
        lbl.setStyleSheet("font-size: 14px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(lbl)

        # O Cérebro: Constrói uma Timeline baseada no status atual e datas
        historico = []
        historico.append(f"🟢 {c.data_entrada} - Entrada do Processo (Protocolo {c.protocolo})")

        if c.taxa_status in ["Pago", "Isento"]:
            historico.append(f"💰 Situação financeira registrada como: {c.taxa_status}")

        if c.pendencias == 0:
            historico.append("📝 Todos os documentos e assinaturas foram recolhidos.")

        if c.status == "Concluído (OK)":
            historico.append("✅ Processo aprovado e pronto para arquivamento.")

        if c.status == "Arquivado":
            historico.append("🗄️ Processo finalizado e arquivado com sucesso.")

        for item in historico:
            lbl_item = QLabel(item)
            lbl_item.setStyleSheet(
                "color: #E2E8F0; font-size: 13px; padding: 10px; background-color: #151A27; border-left: 3px solid #2962FF; margin-bottom: 8px; border-radius: 4px;")
            lbl_item.setWordWrap(True)
            layout.addWidget(lbl_item)

        layout.addStretch()

    # ==========================================
    # CÉREBRO: RECALCULA STATUS
    # ==========================================
    def recalcular_tudo_e_salvar(self):
        if not hasattr(self, 'casamento_atual') or self.casamento_atual.status == "Arquivado":
            return

        entregues = {chk.text(): chk.isChecked() for chk in getattr(self, 'checks_interativos', [])}
        faltando = sum(1 for chk in getattr(self, 'checks_interativos', []) if not chk.isChecked())

        taxa = "Aguardando"
        if hasattr(self, 'radio_pago') and self.radio_pago.isChecked():
            taxa = "Pago"
        elif hasattr(self, 'radio_isento') and self.radio_isento.isChecked():
            taxa = "Isento"

        if faltando == 0 and taxa in ["Pago", "Isento"]:
            novo_status = "Concluído (OK)"
        elif faltando > 0:
            novo_status = "Aguardando Docs"
        else:
            novo_status = "Em Andamento"

        db = SessionLocal()
        atualizar_casamento_interativo(db, self.casamento_atual.id, json.dumps(entregues), faltando, taxa, novo_status)
        db.close()

        self.badge_status_direita.setText(novo_status)
        self.badge_status_direita.setStyleSheet(obter_estilo_status(novo_status))

        linha_selecionada = self.tabela.currentRow()
        self.tabela.blockSignals(True)
        self.carregar_dados_do_banco()
        if linha_selecionada >= 0: self.tabela.selectRow(linha_selecionada)
        self.tabela.blockSignals(False)

        # Atualiza o histórico em tempo real se a aba estiver aberta
        if self.stack_abas.currentIndex() == 2:
            self.trocar_aba(2)

    # ==========================================
    # IMPRESSÃO DO REQUERIMENTO
    # ==========================================
        # ==========================================
        # IMPRESSÃO DO REQUERIMENTO
        # ==========================================
    def imprimir_requerimento(self):


        # Procura o PDF na pasta 'modelos' na raiz do sistema
        caminho_pdf = os.path.join(os.getcwd(), "templates", "form_casamento_modelo.pdf")

        # Caso o arquivo tenha sido colocado dentro da pasta 'assets/modelos'
        if not os.path.exists(caminho_pdf):
            caminho_pdf = os.path.join(os.getcwd(), "assets", "templates", "form_casamento_modelo.pdf")

        # Trava de segurança: avisa se o arquivo PDF não estiver na pasta
        if not os.path.exists(caminho_pdf):
            QMessageBox.warning(self, "Arquivo Não Encontrado",
                                f"O sistema não achou o formulário físico em:\n{caminho_pdf}\n\nVerifique se o nome do PDF está exatamente como 'form_casamento_modelo.pdf'.")
            return

        try:
            # Comando nativo do Windows: manda imprimir silenciosamente na impressora padrão
            os.startfile(caminho_pdf, "print")

            # Aproveitando o seu próprio sistema de notificação visual!
            notificar(self, "Formulário enviado para a impressora padrão!", "sucesso")
        except Exception as e:
            QMessageBox.critical(self, "Erro na Impressora",
                                    f"Não foi possível iniciar a impressão. Verifique se a impressora está ligada.\n\nErro: {str(e)}")

    # ==========================================
    # ARQUIVAMENTO E UTILITÁRIOS
    # ==========================================
    def arquivar_processo(self):
        resp = QMessageBox.question(self, "Arquivar", "Deseja arquivar este processo?\nEle sairá da lista de Ativos.",
                                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if resp == QMessageBox.StandardButton.Yes:
            db = SessionLocal()
            atualizar_status_casamento(db, self.casamento_atual.id, "Arquivado")
            db.close()
            notificar(self, "Processo arquivado!", "sucesso")
            self.carregar_dados_do_banco()
            self.painel_dir.hide()

    def reativar_processo(self):
        db = SessionLocal()
        atualizar_status_casamento(db, self.casamento_atual.id, "Concluído (OK)")
        db.close()
        notificar(self, "Processo reativado com sucesso.", "info")
        self.combo_filtro.setCurrentText("Exibir: Ativos")
        self.carregar_dados_do_banco()

    def criar_kpi_card(self, titulo, label_valor, subtitulo, cor_destaque="#FFFFFF"):
        card = QFrame()
        card.setStyleSheet("background-color: #151A27; border: 1px solid #1E2532; border-radius: 8px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #8A92A6; font-size: 12px; font-weight: bold; border: none;")
        label_valor.setStyleSheet(f"color: {cor_destaque}; font-size: 28px; font-weight: bold; border: none;")
        lbl_sub = QLabel(subtitulo)
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 11px; border: none;")
        layout.addWidget(lbl_tit)
        layout.addWidget(label_valor)
        layout.addWidget(lbl_sub)
        return card

    def limpar_layout_interno(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self.limpar_layout_interno(item.layout())

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