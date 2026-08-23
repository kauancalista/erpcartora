import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QScrollArea, QGridLayout, QPushButton,
                             QComboBox, QSizePolicy, QDialog, QLineEdit, QFormLayout)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QColor, QCursor, QFont

from database.conexao import SessionLocal
from database.modelos import Casamento, Processo, Tarefa, Compromisso  # <--- Importamos Compromisso
from database.crud import criar_compromisso
from ui.componentes import LabelStatus, notificar
from ui.modulo_impressao import DialogImpressao

# ==========================================
# COMPONENTE: POP-UP DE NOVO COMPROMISSO
# ==========================================
class DialogNovoCompromisso(QDialog):
    def __init__(self, parent=None, tipo_pre_selecionado="Reunião"):
        super().__init__(parent)
        self.setWindowTitle("Novo Compromisso")
        self.setFixedSize(450, 420)
        self.setStyleSheet("background-color: #11151F; color: white; border-radius: 8px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        lbl_titulo = QLabel("Agendar Novo Compromisso")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_titulo)

        form = QFormLayout()
        form.setSpacing(15)

        estilo_input = "background-color: #0B0E14; padding: 10px; border: 1px solid #1E2532; border-radius: 6px; color: white;"

        self.inp_titulo = QLineEdit()
        self.inp_titulo.setPlaceholderText("Ex: Reunião com equipe de T.I")
        self.inp_titulo.setStyleSheet(estilo_input)

        self.cb_tipo = QComboBox()
        self.cb_tipo.addItems(["Reunião", "Atendimento", "Audiência", "Outros"])
        self.cb_tipo.setCurrentText(tipo_pre_selecionado)
        self.cb_tipo.setStyleSheet(estilo_input)

        box_data_hora = QHBoxLayout()
        self.inp_data = QLineEdit()
        self.inp_data.setPlaceholderText("DD/MM/AAAA")
        self.inp_data.setStyleSheet(estilo_input)

        self.inp_hora = QLineEdit()
        self.inp_hora.setPlaceholderText("HH:MM")
        self.inp_hora.setStyleSheet(estilo_input)

        box_data_hora.addWidget(self.inp_data)
        box_data_hora.addWidget(self.inp_hora)

        self.cb_lembrete = QComboBox()
        self.cb_lembrete.addItems(
            ["10 minutos antes", "30 minutos antes", "1 hora antes", "1 dia antes", "Sem lembrete"])
        self.cb_lembrete.setStyleSheet(estilo_input)

        self.inp_link = QLineEdit()
        self.inp_link.setPlaceholderText("Link do Meet/Zoom (Opcional)")
        self.inp_link.setStyleSheet(estilo_input)

        form.addRow(QLabel("Título:"), self.inp_titulo)
        form.addRow(QLabel("Tipo:"), self.cb_tipo)
        form.addRow(QLabel("Data e Hora:"), box_data_hora)
        form.addRow(QLabel("Lembrete:"), self.cb_lembrete)
        form.addRow(QLabel("Link / Local:"), self.inp_link)

        layout.addLayout(form)
        layout.addStretch()

        box_botoes = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(
            "background-color: transparent; border: 1px solid #2C364C; padding: 10px; border-radius: 6px;")
        btn_cancelar.clicked.connect(self.reject)

        btn_salvar = QPushButton("Salvar Compromisso")
        btn_salvar.setStyleSheet("background-color: #2962FF; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_salvar.clicked.connect(self.salvar)

        box_botoes.addWidget(btn_cancelar)
        box_botoes.addWidget(btn_salvar)
        layout.addLayout(box_botoes)

    def salvar(self):
        if not self.inp_titulo.text() or not self.inp_data.text() or not self.inp_hora.text():
            notificar(self, "Preencha o título, data e hora!", "erro")
            return

        db = SessionLocal()
        criar_compromisso(
            db,
            titulo=self.inp_titulo.text().strip(),
            data=self.inp_data.text().strip(),
            hora=self.inp_hora.text().strip(),
            tipo=self.cb_tipo.currentText(),
            lembrete=self.cb_lembrete.currentText(),
            link=self.inp_link.text().strip()
        )
        db.close()
        self.accept()


# ==========================================
# A TELA PRINCIPAL DE AGENDA
# ==========================================
class TelaAgenda(QWidget):
    def __init__(self):
        super().__init__()
        self.dicionario_eventos = {}
        self.data_hoje = QDate.currentDate()
        self.mes_atual = self.data_hoje.month()
        self.ano_atual = self.data_hoje.year()
        self.data_selecionada = self.data_hoje

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # --- COLUNA 1: GRID PRINCIPAL ---
        self.painel_esq = QWidget()
        self.painel_esq.setStyleSheet("background-color: #0B0E14;")
        layout_esq = QVBoxLayout(self.painel_esq)
        layout_esq.setContentsMargins(30, 30, 20, 30)
        layout_esq.setSpacing(15)

        box_topo = QHBoxLayout()
        box_titulos = QVBoxLayout()
        lbl_titulo = QLabel("Agenda do Cartório")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        box_titulos.addWidget(lbl_titulo)

        box_topo.addLayout(box_titulos)
        box_topo.addStretch()

        btn_hoje = QPushButton("Hoje")
        btn_hoje.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_hoje.setStyleSheet(
            "background-color: #151A27; color: white; border: 1px solid #1E2532; padding: 8px 15px; border-radius: 6px;")
        btn_hoje.clicked.connect(self.ir_para_hoje)

        self.btn_ant = QPushButton("❮")
        self.btn_ant.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ant.setStyleSheet(
            "background-color: #151A27; color: white; border: 1px solid #1E2532; padding: 8px 12px; border-radius: 6px;")
        self.btn_ant.clicked.connect(lambda: self.mudar_mes(-1))

        self.btn_prox = QPushButton("❯")
        self.btn_prox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_prox.setStyleSheet(
            "background-color: #151A27; color: white; border: 1px solid #1E2532; padding: 8px 12px; border-radius: 6px;")
        self.btn_prox.clicked.connect(lambda: self.mudar_mes(1))

        self.lbl_mes_ano = QLabel()
        self.lbl_mes_ano.setStyleSheet("font-size: 20px; font-weight: bold; color: white; margin-left: 10px;")

        box_topo.addWidget(btn_hoje)
        box_topo.addWidget(self.btn_ant)
        box_topo.addWidget(self.btn_prox)
        box_topo.addWidget(self.lbl_mes_ano)

        layout_esq.addLayout(box_topo)

        # KPIs
        self.lbl_kpi_total = QLabel("0")
        self.lbl_kpi_realizados = QLabel("0")
        self.lbl_kpi_pendentes = QLabel("0")
        self.lbl_kpi_cerimonias = QLabel("0")

        layout_kpis = QHBoxLayout()
        layout_kpis.setSpacing(10)
        layout_kpis.addWidget(self.criar_kpi_card("Total", self.lbl_kpi_total, "#2962FF"))
        layout_kpis.addWidget(self.criar_kpi_card("Realizados", self.lbl_kpi_realizados, "#27AE60"))
        layout_kpis.addWidget(self.criar_kpi_card("Pendentes", self.lbl_kpi_pendentes, "#F39C12"))
        layout_kpis.addWidget(self.criar_kpi_card("Casamentos", self.lbl_kpi_cerimonias, "#8E44AD"))
        layout_esq.addLayout(layout_kpis)

        # Calendário
        self.grid_calendario = QGridLayout()
        self.grid_calendario.setSpacing(5)
        dias_semana = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
        for col, dia in enumerate(dias_semana):
            lbl = QLabel(dia)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #8A92A6; font-weight: bold; font-size: 13px; margin-bottom: 5px;")
            self.grid_calendario.addWidget(lbl, 0, col)

        for i in range(7):
            self.grid_calendario.setColumnStretch(i, 1)

        layout_esq.addLayout(self.grid_calendario)
        layout_esq.addStretch()

        # --- COLUNA 2: DIREITA (Filtros, Ações e Timeline) ---
        self.painel_dir = QFrame()
        self.painel_dir.setStyleSheet("background-color: #11151F; border-left: 1px solid #1E2532;")
        layout_dir = QVBoxLayout(self.painel_dir)
        layout_dir.setContentsMargins(25, 30, 25, 30)
        layout_dir.setSpacing(20)

        # Ações Rápidas (AGORA CONECTADAS DE VERDADE!)
        box_acoes = QHBoxLayout()
        btn_novo = QPushButton("+ Novo Compromisso")
        btn_novo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_novo.setStyleSheet(
            "background-color: #2962FF; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_novo.clicked.connect(lambda: self.abrir_dialog_novo("Atendimento"))

        btn_reuniao = QPushButton("👥 Nova Reunião")
        btn_reuniao.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_reuniao.setStyleSheet(
            "background-color: #151A27; color: white; border: 1px solid #1E2532; padding: 10px; border-radius: 6px;")
        btn_reuniao.clicked.connect(lambda: self.abrir_dialog_novo("Reunião"))

        btn_imp = QPushButton("🖨️ Imprimir")
        btn_imp.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_imp.setStyleSheet(
            "background-color: #151A27; color: white; border: 1px solid #1E2532; padding: 10px; border-radius: 6px;")
        btn_imp.clicked.connect(self.imprimir_agenda_do_dia)
        box_acoes.addWidget(btn_novo)
        box_acoes.addWidget(btn_reuniao)
        box_acoes.addWidget(btn_imp)
        layout_dir.addLayout(box_acoes)

        linha = QFrame()
        linha.setFrameShape(QFrame.Shape.HLine)
        linha.setStyleSheet("color: #1E2532; border: none; background-color: #1E2532;")
        linha.setFixedHeight(2)
        layout_dir.addWidget(linha)

        # Timeline
        lbl_dir_tit = QLabel("Compromissos do dia selecionado")
        lbl_dir_tit.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout_dir.addWidget(lbl_dir_tit)

        self.lbl_data_selecionada = QLabel("Selecione uma data no calendário")
        self.lbl_data_selecionada.setStyleSheet("font-size: 13px; color: #8A92A6; margin-bottom: 5px;")
        layout_dir.addWidget(self.lbl_data_selecionada)

        scroll_dir = QScrollArea()
        scroll_dir.setWidgetResizable(True)
        scroll_dir.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.container_eventos = QWidget()
        self.container_eventos.setStyleSheet("background-color: transparent;")
        self.layout_eventos = QVBoxLayout(self.container_eventos)
        self.layout_eventos.setContentsMargins(0, 0, 0, 0)
        self.layout_eventos.setSpacing(15)
        self.layout_eventos.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_dir.setWidget(self.container_eventos)
        layout_dir.addWidget(scroll_dir)

        layout_principal.addWidget(self.painel_esq, 7)
        layout_principal.addWidget(self.painel_dir, 3)

        self.carregar_dados_globais()
        self.ir_para_hoje()

    # ==========================================
    # CÉREBRO DA AGENDA (LÊ AS 4 TABELAS!)
    # ==========================================
    def abrir_dialog_novo(self, tipo):
        dialog = DialogNovoCompromisso(self, tipo_pre_selecionado=tipo)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            notificar(self, "Compromisso agendado com sucesso!", "sucesso")
            self.carregar_dados_globais()  # Atualiza os dados
            self.renderizar_calendario()  # Redesenha o calendário
            self.ao_clicar_data(self.data_selecionada)  # Atualiza a timeline da direita

    def carregar_dados_globais(self):
        db = SessionLocal()
        casamentos = db.query(Casamento).all()
        processos = db.query(Processo).all()
        tarefas = db.query(Tarefa).all()
        compromissos = db.query(Compromisso).all()  # <--- Puxa a nova tabela!
        db.close()

        self.dicionario_eventos.clear()

        # 1. Casamentos
        for c in casamentos:
            data_str = c.data_celebracao.strip()
            if data_str and data_str != "A definir":
                hora = c.horario_celebracao if c.horario_celebracao else "A def."
                self.adicionar_ao_dicionario(data_str, {
                    "tipo": "Casamento", "hora": hora, "cor": "#8E44AD", "icone": "💍",
                    "titulo": f"{c.nome_noivo} & {c.nome_noiva}",
                    "subtitulo": f"Status: {c.status}", "status": c.status
                })

        # 2. Processos
        for p in processos:
            if p.data_entrada:
                data_str = p.data_entrada if isinstance(p.data_entrada, str) else p.data_entrada.strftime("%d/%m/%Y")
                self.adicionar_ao_dicionario(data_str, {
                    "tipo": "Processo", "hora": "09:00", "cor": "#27AE60", "icone": "📄",
                    "titulo": p.nome_cliente, "subtitulo": f"Serviço: {p.tipo_servico}", "status": p.status
                })

        # 3. Tarefas
        for t in tarefas:
            if t.data_criacao:
                data_str = t.data_criacao if isinstance(t.data_criacao, str) else t.data_criacao.strftime("%d/%m/%Y")
                resp = t.responsavel if t.responsavel else "Equipe"
                self.adicionar_ao_dicionario(data_str, {
                    "tipo": "Tarefa", "hora": "14:00", "cor": "#F39C12", "icone": "📋",
                    "titulo": t.descricao, "subtitulo": f"Resp: {resp}", "status": t.status
                })

        # 4. COMPROMISSOS NOVOS
        for comp in compromissos:
            cor = "#2962FF" if comp.tipo == "Reunião" else "#E67E22"
            icone = "👥" if comp.tipo == "Reunião" else "📌"
            sub = f"Link: {comp.link_reuniao}" if comp.link_reuniao else f"Lembrete: {comp.lembrete}"

            self.adicionar_ao_dicionario(comp.data, {
                "tipo": comp.tipo, "hora": comp.hora, "cor": cor, "icone": icone,
                "titulo": comp.titulo, "subtitulo": sub, "status": comp.status
            })

    def adicionar_ao_dicionario(self, data_str, evento_dict):
        if data_str not in self.dicionario_eventos:
            self.dicionario_eventos[data_str] = []
        self.dicionario_eventos[data_str].append(evento_dict)

    # ==========================================
    # NAVEGAÇÃO E RENDERIZAÇÃO
    # ==========================================
    def mudar_mes(self, offset):
        nova_data = QDate(self.ano_atual, self.mes_atual, 1).addMonths(offset)
        self.mes_atual = nova_data.month()
        self.ano_atual = nova_data.year()
        self.renderizar_calendario()

    def ir_para_hoje(self):
        self.mes_atual = self.data_hoje.month()
        self.ano_atual = self.data_hoje.year()
        self.renderizar_calendario()
        self.ao_clicar_data(self.data_hoje)

    def renderizar_calendario(self):
        meses = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro",
                 "Novembro", "Dezembro"]
        self.lbl_mes_ano.setText(f"{meses[self.mes_atual - 1]} de {self.ano_atual}")

        for i in reversed(range(self.grid_calendario.count())):
            item = self.grid_calendario.itemAt(i)
            if item.widget() and self.grid_calendario.getItemPosition(i)[0] > 0:
                item.widget().deleteLater()

        primeiro_dia = QDate(self.ano_atual, self.mes_atual, 1)
        dias_no_mes = primeiro_dia.daysInMonth()
        dia_semana_inicio = primeiro_dia.dayOfWeek()
        start_col = 0 if dia_semana_inicio == 7 else dia_semana_inicio

        row, col = 1, start_col
        total_eventos, realizados, pendentes, cerimonias = 0, 0, 0, 0

        for dia in range(1, dias_no_mes + 1):
            data_obj = QDate(self.ano_atual, self.mes_atual, dia)
            data_str = data_obj.toString("dd/MM/yyyy")
            eventos_hoje = self.dicionario_eventos.get(data_str, [])

            total_eventos += len(eventos_hoje)
            for e in eventos_hoje:
                if e['tipo'] == "Casamento": cerimonias += 1
                if "Concluíd" in e['status'] or "Confirmado" in e['status']:
                    realizados += 1
                else:
                    pendentes += 1

            frame_dia = QFrame()
            frame_dia.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
            frame_dia.setMinimumHeight(60)

            if data_obj == self.data_selecionada:
                frame_dia.setStyleSheet(
                    "QFrame { background-color: #1A2133; border: 1px solid #2962FF; border-radius: 6px; }")
            else:
                frame_dia.setStyleSheet(
                    "QFrame { background-color: #11151F; border: 1px solid #1E2532; border-radius: 6px; } QFrame:hover { background-color: #1A2133; }")

            frame_dia.mousePressEvent = lambda event, d=data_obj: self.ao_clicar_data(d)

            layout_dia = QVBoxLayout(frame_dia)
            layout_dia.setAlignment(Qt.AlignmentFlag.AlignTop)
            layout_dia.setContentsMargins(6, 6, 6, 6)
            layout_dia.setSpacing(2)

            lbl_num = QLabel(str(dia))
            lbl_num.setStyleSheet(
                "font-size: 13px; font-weight: bold; color: white; background: transparent; border: none;")
            if data_obj == self.data_hoje:
                lbl_num.setStyleSheet(
                    "font-size: 13px; font-weight: bold; color: white; background-color: #2962FF; border-radius: 10px; padding: 2px 6px;")
                lbl_num.setAlignment(Qt.AlignmentFlag.AlignCenter)
                lbl_num.setFixedSize(24, 24)
            layout_dia.addWidget(lbl_num)

            for ev in eventos_hoje[:2]:
                lbl_ev = QLabel(f"● {ev['hora']} {ev['tipo']}")
                lbl_ev.setStyleSheet(f"color: {ev['cor']}; font-size: 10px; background: transparent; border: none;")
                font_metrics = lbl_ev.fontMetrics()
                texto_elidido = font_metrics.elidedText(f"● {ev['hora']} {ev['tipo']}", Qt.TextElideMode.ElideRight,
                                                        100)
                lbl_ev.setText(texto_elidido)
                layout_dia.addWidget(lbl_ev)

            if len(eventos_hoje) > 2:
                layout_dia.addWidget(
                    QLabel(f"<span style='color:#8A92A6; font-size:10px;'>+ {len(eventos_hoje) - 2} mais</span>"))

            self.grid_calendario.addWidget(frame_dia, row, col)
            col += 1
            if col > 6:
                col = 0
                row += 1

        self.lbl_kpi_total.setText(str(total_eventos))
        self.lbl_kpi_realizados.setText(str(realizados))
        self.lbl_kpi_pendentes.setText(str(pendentes))
        self.lbl_kpi_cerimonias.setText(str(cerimonias))

    def ao_clicar_data(self, data_qdate):
        self.data_selecionada = data_qdate
        self.renderizar_calendario()

        data_str = data_qdate.toString("dd/MM/yyyy")
        dias_extenso = ["Domingo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado"]
        nome_dia = dias_extenso[data_qdate.dayOfWeek() % 7]

        meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        self.lbl_data_selecionada.setText(f"{nome_dia}, {data_qdate.toString('dd')} de {meses[data_qdate.month() - 1]}")

        self.limpar_layout_interno(self.layout_eventos)
        eventos_do_dia = self.dicionario_eventos.get(data_str, [])

        if not eventos_do_dia:
            lbl_vazio = QLabel("\n\n📅 Dia livre!\nNenhum compromisso marcado.")
            lbl_vazio.setStyleSheet("color: #8A92A6; font-size: 14px;")
            lbl_vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout_eventos.addWidget(lbl_vazio)
        else:
            eventos_do_dia.sort(key=lambda x: x["hora"])
            for evt in eventos_do_dia:
                self.criar_card_timeline(evt)

        self.layout_eventos.addStretch()

    # ==========================================
    # UTILITÁRIOS VISUAIS
    # ==========================================
    def criar_card_timeline(self, evt):
        container = QWidget()
        layout_linha = QHBoxLayout(container)
        layout_linha.setContentsMargins(0, 0, 0, 0)
        layout_linha.setAlignment(Qt.AlignmentFlag.AlignTop)

        lbl_hora = QLabel(evt["hora"])
        lbl_hora.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        lbl_hora.setFixedWidth(40)
        lbl_hora.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)

        card = QFrame()
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        card.setStyleSheet(
            f"background-color: #151A27; border-left: 3px solid {evt['cor']}; border-radius: 4px; padding: 5px;")
        layout_card = QVBoxLayout(card)
        layout_card.setContentsMargins(10, 5, 10, 5)

        box_topo = QHBoxLayout()
        lbl_tipo = QLabel(f"{evt['icone']} {evt['tipo']}")
        lbl_tipo.setStyleSheet(f"color: {evt['cor']}; font-size: 12px; font-weight: bold;")
        badge_status = LabelStatus(evt["status"])

        box_topo.addWidget(lbl_tipo)
        box_topo.addStretch()
        box_topo.addWidget(badge_status)
        layout_card.addLayout(box_topo)

        lbl_titulo = QLabel(evt["titulo"])
        lbl_titulo.setStyleSheet("color: white; font-size: 14px; font-weight: bold; margin-top: 2px;")
        lbl_titulo.setWordWrap(True)

        lbl_sub = QLabel(evt["subtitulo"])
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 11px;")
        lbl_sub.setWordWrap(True)

        layout_card.addWidget(lbl_titulo)
        layout_card.addWidget(lbl_sub)

        # O pulo do Gato: Link clicável
        if "Link:" in evt["subtitulo"]:
            link = evt["subtitulo"].replace("Link: ", "")
            if link:
                lbl_link = QLabel(
                    f"<a href='{link}' style='color: #2962FF; text-decoration: none;'>Participar da Reunião</a>")
                lbl_link.setOpenExternalLinks(True)
                layout_card.addWidget(lbl_link)

        layout_linha.addWidget(lbl_hora)
        layout_linha.addWidget(card, 1)
        self.layout_eventos.addWidget(container)

    def criar_kpi_card(self, titulo, label_valor, cor_destaque):
        card = QFrame()
        card.setStyleSheet("background-color: #151A27; border: 1px solid #1E2532; border-radius: 8px;")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(15, 15, 15, 15)

        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #8A92A6; font-size: 12px; font-weight: bold;")
        label_valor.setStyleSheet(f"color: {cor_destaque}; font-size: 26px; font-weight: bold;")

        layout.addWidget(lbl_tit)
        layout.addWidget(label_valor)
        return card

    def limpar_layout_interno(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self.limpar_layout_interno(item.layout())

    def imprimir_agenda_do_dia(self):
        data_str = self.data_selecionada.toString("dd/MM/yyyy")
        eventos_do_dia = self.dicionario_eventos.get(data_str, [])

        # Monta um HTML bonito para a folha A4
        html = f"""
        <h1 style='text-align: center; color: #2C3E50;'>Agenda do Cartório</h1>
        <p style='text-align: center; font-size: 16px; color: #7F8C8D;'>Data: {data_str}</p>
        <hr style='border: 1px solid #BDC3C7;'>
        <br>
        """

        if not eventos_do_dia:
            html += "<p style='text-align: center; font-size: 18px;'>Nenhum compromisso agendado para esta data.</p>"
        else:
            eventos_do_dia.sort(key=lambda x: x["hora"])
            for e in eventos_do_dia:
                html += f"""
                <div style='margin-bottom: 20px;'>
                    <b style='font-size: 18px;'>{e['hora']} - {e['tipo']}</b><br>
                    <span style='font-size: 16px;'>{e['titulo']}</span><br>
                    <span style='font-size: 14px; color: #555;'><i>{e['subtitulo']}</i></span>
                </div>
                """

        # Chama o Módulo de Impressão Global!
        dialogo = DialogImpressao(self, f"Agenda {data_str.replace('/', '-')}", html)
        dialogo.exec()