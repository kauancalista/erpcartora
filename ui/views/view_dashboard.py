import os
from datetime import datetime, date, timedelta
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea, QPushButton, QDialog
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QCursor, QFont

from database.conexao import SessionLocal
from database.crud import (
    obter_metricas_dashboard_completas,
    marcar_notificacao_lida
)
from ui.dialogs.form_novo_processo import DialogNovoProcesso
from ui.dialogs.form_detalhes_processo import DialogDetalhesProcesso
from ui.componentes import notificar


class DialogCasamentosDoDia(QDialog):
    """Exibe os casamentos agendados para o dia clicado no calendário."""

    def __init__(self, data_str, casamentos, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Casamentos - {data_str}")
        self.setFixedSize(480, 360)
        self.setStyleSheet("""
            QDialog {
                background-color: #11151F;
                border: 1px solid #1E2532;
                border-radius: 10px;
            }
            QLabel { border: none; background: transparent; }
        """)
        self.ir_para_casamentos = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        lbl_tit = QLabel(f"📅 Casamentos em {data_str}")
        lbl_tit.setStyleSheet("color: white; font-size: 16px; font-weight: bold; border: none;")
        layout.addWidget(lbl_tit)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        container = QWidget()
        lay_cards = QVBoxLayout(container)
        lay_cards.setSpacing(10)

        if not casamentos:
            lbl_vazio = QLabel("Nenhum casamento agendado para esta data.")
            lbl_vazio.setStyleSheet("color: #8A92A6; font-size: 13px; font-style: italic; padding: 20px; border: none;")
            lbl_vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay_cards.addWidget(lbl_vazio)
        else:
            for c in casamentos:
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background-color: #1A2133;
                        border: 1px solid #2C364C;
                        border-radius: 8px;
                    }
                    QLabel { border: none; background: transparent; }
                """)
                lay_c = QVBoxLayout(card)
                lay_c.setContentsMargins(12, 10, 12, 10)
                lay_c.setSpacing(4)

                lbl_noivos = QLabel(f"💍 {c.nome_noivo} & {c.nome_noiva}")
                lbl_noivos.setStyleSheet("color: white; font-size: 13px; font-weight: bold; border: none;")

                lay_info = QHBoxLayout()
                lbl_prot = QLabel(f"Protocolo: {c.protocolo}")
                lbl_prot.setStyleSheet("color: #38BDF8; font-size: 11px; font-family: monospace; border: none;")
                lbl_hora = QLabel(f"Horário: {c.horario_celebracao or 'A definir'}")
                lbl_hora.setStyleSheet("color: #10B981; font-size: 11px; font-weight: bold; border: none;")
                lay_info.addWidget(lbl_prot)
                lay_info.addStretch()
                lay_info.addWidget(lbl_hora)

                lay_c.addWidget(lbl_noivos)
                lay_c.addLayout(lay_info)
                lay_cards.addWidget(card)

        scroll.setWidget(container)
        layout.addWidget(scroll)

        lay_btn = QHBoxLayout()
        btn_fechar = QPushButton("Fechar")
        btn_fechar.setStyleSheet("""
            QPushButton {
                background-color: #1A2133;
                color: #A9CCE3;
                border: 1px solid #2C364C;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #242E47; }
        """)
        btn_fechar.clicked.connect(self.reject)

        btn_ver_modulo = QPushButton("Ir para Módulo de Casamentos →")
        btn_ver_modulo.setStyleSheet("""
            QPushButton {
                background-color: #2962FF;
                color: white;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton:hover { background-color: #1E50D8; }
        """)
        btn_ver_modulo.clicked.connect(self._acao_ir_modulo)

        lay_btn.addWidget(btn_fechar)
        lay_btn.addStretch()
        lay_btn.addWidget(btn_ver_modulo)
        layout.addLayout(lay_btn)

    def _acao_ir_modulo(self):
        self.ir_para_casamentos = True
        self.accept()


class CalendarioCasamentosWidget(QFrame):
    """Widget de calendário compacto, responsivo e com números de dia 100% visíveis."""
    abrir_casamentos_solicitado = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card_calendario")
        self.setStyleSheet("""
            QFrame#card_calendario {
                background-color: #11151F;
                border: 1px solid #1E2532;
                border-radius: 10px;
            }
            QLabel { border: none; background: transparent; }
        """)
        self.ano_atual = datetime.now().year
        self.mes_atual = datetime.now().month
        self.mapa_casamentos = {}

        self.layout_principal = QVBoxLayout(self)
        self.layout_principal.setContentsMargins(12, 10, 12, 10)
        self.layout_principal.setSpacing(6)

        # Cabeçalho do Mês
        layout_header = QHBoxLayout()
        self.btn_ant = QPushButton("‹")
        self.btn_ant.setFixedSize(24, 24)
        self.btn_ant.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_ant.setStyleSheet("""
            QPushButton {
                background-color: #1A2133;
                color: #A9CCE3;
                border: 1px solid #2C364C;
                border-radius: 5px;
                font-weight: bold;
                font-size: 14px;
                padding: 0px;
            }
            QPushButton:hover { background-color: #2962FF; color: white; }
        """)
        self.btn_ant.clicked.connect(self.mes_anterior)

        self.lbl_mes_ano = QLabel()
        self.lbl_mes_ano.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_mes_ano.setStyleSheet("color: white; font-size: 13px; font-weight: bold; border: none;")

        self.btn_prox = QPushButton("›")
        self.btn_prox.setFixedSize(24, 24)
        self.btn_prox.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_prox.setStyleSheet(self.btn_ant.styleSheet())
        self.btn_prox.clicked.connect(self.proximo_mes)

        layout_header.addWidget(self.btn_ant)
        layout_header.addWidget(self.lbl_mes_ano, 1)
        layout_header.addWidget(self.btn_prox)
        self.layout_principal.addLayout(layout_header)

        # Grid dos dias
        self.grid_dias = QGridLayout()
        self.grid_dias.setSpacing(2)
        self.layout_principal.addLayout(self.grid_dias)

        # Legenda
        layout_legenda = QHBoxLayout()
        layout_legenda.setSpacing(10)
        layout_legenda.addWidget(self._criar_item_legenda("#10B981", "Casamento"))
        layout_legenda.addWidget(self._criar_item_legenda("#2962FF", "Hoje"))
        layout_legenda.addStretch()
        self.layout_principal.addLayout(layout_legenda)

        self.renderizar()

    def _criar_item_legenda(self, cor_hex, texto):
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(5)

        dot = QLabel()
        dot.setFixedSize(6, 6)
        dot.setStyleSheet(f"background-color: {cor_hex}; border-radius: 3px; border: none;")

        lbl = QLabel(texto)
        lbl.setStyleSheet("color: #8A92A6; font-size: 10px; border: none;")

        lay.addWidget(dot)
        lay.addWidget(lbl)
        return w

    def atualizar_casamentos(self, lista_casamentos):
        self.mapa_casamentos = {}
        for c in lista_casamentos:
            data_str = c.data_celebracao
            if data_str:
                partes = str(data_str).split("/")
                if len(partes) == 3:
                    try:
                        d, m, a = int(partes[0]), int(partes[1]), int(partes[2])
                        if m == self.mes_atual and a == self.ano_atual:
                            if d not in self.mapa_casamentos:
                                self.mapa_casamentos[d] = []
                            self.mapa_casamentos[d].append(c)
                    except ValueError:
                        pass
        self.renderizar()

    def mes_anterior(self):
        if self.mes_atual == 1:
            self.mes_atual = 12
            self.ano_atual -= 1
        else:
            self.mes_atual -= 1
        self.renderizar()

    def proximo_mes(self):
        if self.mes_atual == 12:
            self.mes_atual = 1
            self.ano_atual += 1
        else:
            self.mes_atual += 1
        self.renderizar()

    def renderizar(self):
        # Limpar grid anterior
        while self.grid_dias.count():
            item = self.grid_dias.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

        nomes_meses = [
            "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        self.lbl_mes_ano.setText(f"{nomes_meses[self.mes_atual]} {self.ano_atual}")

        dias_semana = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
        for col, dia in enumerate(dias_semana):
            lbl = QLabel(dia)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("color: #64748B; font-size: 10px; font-weight: bold; border: none; padding-bottom: 2px;")
            self.grid_dias.addWidget(lbl, 0, col)

        primeiro_dia = date(self.ano_atual, self.mes_atual, 1)
        col_inicio = primeiro_dia.weekday()

        if self.mes_atual == 12:
            proximo_mes_date = date(self.ano_atual + 1, 1, 1)
        else:
            proximo_mes_date = date(self.ano_atual, self.mes_atual + 1, 1)
        total_dias = (proximo_mes_date - timedelta(days=1)).day

        hoje = date.today()
        linha = 1
        coluna = col_inicio

        for dia in range(1, total_dias + 1):
            btn_dia = QPushButton(str(dia))
            btn_dia.setProperty("class", "btn-dia-calendario")
            btn_dia.setFixedSize(24, 24)
            btn_dia.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

            eh_hoje = (dia == hoje.day and self.mes_atual == hoje.month and self.ano_atual == hoje.year)
            tem_casamento = dia in self.mapa_casamentos

            if tem_casamento:
                btn_dia.setStyleSheet("""
                    QPushButton {
                        background-color: #10B981 !important;
                        color: #FFFFFF !important;
                        font-size: 11px !important;
                        font-weight: bold !important;
                        border-radius: 12px;
                        border: 1px solid #34D399;
                        padding: 0px !important;
                        margin: 0px !important;
                    }
                    QPushButton:hover { background-color: #059669 !important; }
                """)
            elif eh_hoje:
                btn_dia.setStyleSheet("""
                    QPushButton {
                        background-color: #2962FF !important;
                        color: #FFFFFF !important;
                        font-size: 11px !important;
                        font-weight: bold !important;
                        border-radius: 12px;
                        border: 1px solid #60A5FA;
                        padding: 0px !important;
                        margin: 0px !important;
                    }
                    QPushButton:hover { background-color: #1E50D8 !important; }
                """)
            else:
                btn_dia.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #FFFFFF !important;
                        font-size: 11px !important;
                        font-weight: bold !important;
                        border-radius: 12px;
                        border: none;
                        padding: 0px !important;
                        margin: 0px !important;
                    }
                    QPushButton:hover {
                        background-color: #1E2532;
                        color: #38BDF8 !important;
                    }
                """)

            btn_dia.clicked.connect(lambda _, d=dia: self._clique_dia(d))
            self.grid_dias.addWidget(btn_dia, linha, coluna)

            coluna += 1
            if coluna > 6:
                coluna = 0
                linha += 1

    def _clique_dia(self, dia):
        casamentos = self.mapa_casamentos.get(dia, [])
        data_str = f"{dia:02d}/{self.mes_atual:02d}/{self.ano_atual}"
        dlg = DialogCasamentosDoDia(data_str, casamentos, self)
        if dlg.exec() and dlg.ir_para_casamentos:
            self.abrir_casamentos_solicitado.emit()


class TelaDashboard(QWidget):
    """
    Dashboard Executivo Definitivo:
    - 100% Responsivo e sem corte de texto
    - Card de Ações Rápidas Azul Royal conforme mockup (media_1789159737667.png)
    - 3 Ações Verticais Espaçosas (Novo Processo, Novo Requerimento, Agendar Casamento)
    - Zero bordas retangulares em QLabels
    - Calendário com números em destaque 100% visíveis
    - Tabelas proporcionais sem travamento de largura
    - Deduplicação e carregamento instantâneo
    """
    solicitar_navegacao = pyqtSignal(int)

    def __init__(self):
        super().__init__()

        self.setStyleSheet("QLabel { border: none !important; background: transparent !important; }")

        layout_base = QVBoxLayout(self)
        layout_base.setContentsMargins(0, 0, 0, 0)
        layout_base.setSpacing(0)

        # Scroll principal elástico sem barra horizontal e responsivo
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #0B0E14; }")

        self.container = QWidget()
        self.container.setStyleSheet("background-color: #0B0E14;")
        self.layout_conteudo = QVBoxLayout(self.container)
        self.layout_conteudo.setContentsMargins(18, 12, 18, 12)
        self.layout_conteudo.setSpacing(10)

        # 1. Saudação
        self._construir_saudacao()

        # 2. 4 Top KPI Cards
        self._construir_top_kpis()

        # 3. Grid Principal em 2 Colunas Responsivas (62% / 38%)
        self._construir_duas_colunas()

        # 4. Rodapé Institucional
        self._construir_rodape()

        self.scroll.setWidget(self.container)
        layout_base.addWidget(self.scroll)

        # Carrega dados reais do banco
        self.carregar_dados_reais()

    # =========================================================================
    # 1. SAUDAÇÃO
    # =========================================================================
    def _construir_saudacao(self):
        lay = QVBoxLayout()
        lay.setSpacing(1)

        lbl_ola = QLabel("Painel Operacional do Cartório")
        lbl_ola.setStyleSheet("color: #FFFFFF; font-size: 17px; font-weight: bold; border: none;")

        lbl_sub = QLabel("Resumo dinâmico de demandas, prazos e celebrações em tempo real.")
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 11px; border: none;")

        lay.addWidget(lbl_ola)
        lay.addWidget(lbl_sub)
        self.layout_conteudo.addLayout(lay)

    # =========================================================================
    # 2. 4 TOP KPIS RESPONSIVOS (STRETCH = 1 EM CADA)
    # =========================================================================
    def _construir_top_kpis(self):
        layout_kpis = QHBoxLayout()
        layout_kpis.setSpacing(10)

        card1, self.lbl_kpi_total, self.lbl_kpi_total_tag = self._criar_kpi_card(
            "card_kpi_total", "Total de Processos", "📁", "#3B82F6", "rgba(59, 130, 246, 0.15)", "↑ 12% vs. ontem", "#10B981"
        )
        card2, self.lbl_kpi_pendentes, self.lbl_kpi_pendentes_tag = self._criar_kpi_card(
            "card_kpi_pend", "Processos Pendentes", "⏳", "#10B981", "rgba(16, 185, 129, 0.15)", "↑ 8% vs. ontem", "#10B981"
        )
        card3, self.lbl_kpi_certidoes, self.lbl_kpi_certidoes_tag = self._criar_kpi_card(
            "card_kpi_cert", "Certidões Emitidas", "📜", "#A855F7", "rgba(168, 85, 247, 0.15)", "↑ 15% vs. ontem", "#10B981"
        )
        card4, self.lbl_kpi_atendimentos, self.lbl_kpi_atendimentos_tag = self._criar_kpi_card(
            "card_kpi_atend", "Atendimentos Hoje", "👥", "#F59E0B", "rgba(245, 158, 11, 0.15)", "↑ 6% vs. ontem", "#10B981"
        )

        layout_kpis.addWidget(card1, 1)
        layout_kpis.addWidget(card2, 1)
        layout_kpis.addWidget(card3, 1)
        layout_kpis.addWidget(card4, 1)

        self.layout_conteudo.addLayout(layout_kpis)

    def _criar_kpi_card(self, obj_id, titulo, icone, cor_icone, cor_bg_icone, tag_texto, tag_cor):
        card = QFrame()
        card.setObjectName(obj_id)
        card.setStyleSheet(f"""
            QFrame#{obj_id} {{
                background-color: #11151F;
                border: 1px solid #1E2532;
                border-radius: 10px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(14, 8, 14, 8)
        lay.setSpacing(3)

        lay_topo = QHBoxLayout()
        frame_ic = QFrame()
        frame_ic.setFixedSize(28, 28)
        frame_ic.setStyleSheet(f"background-color: {cor_bg_icone}; border-radius: 6px; border: none;")
        lay_ic = QVBoxLayout(frame_ic)
        lay_ic.setContentsMargins(0, 0, 0, 0)
        lbl_ic = QLabel(icone)
        lbl_ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ic.setStyleSheet(f"font-size: 13px; color: {cor_icone}; border: none;")
        lay_ic.addWidget(lbl_ic)

        lbl_tag = QLabel(tag_texto)
        lbl_tag.setStyleSheet(f"""
            background-color: rgba(16, 185, 129, 0.1);
            color: {tag_cor};
            font-size: 9px;
            font-weight: bold;
            padding: 1px 6px;
            border-radius: 6px;
            border: none;
        """)

        lay_topo.addWidget(frame_ic)
        lay_topo.addStretch()
        lay_topo.addWidget(lbl_tag)
        lay.addLayout(lay_topo)

        lbl_num = QLabel("0")
        lbl_num.setStyleSheet("color: white; font-size: 20px; font-weight: bold; border: none;")
        lay.addWidget(lbl_num)

        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #8A92A6; font-size: 11px; font-weight: 500; border: none;")
        lay.addWidget(lbl_tit)

        return card, lbl_num, lbl_tag

    # =========================================================================
    # 3. DUAS COLUNAS RESPONSIVAS (62% / 38%)
    # =========================================================================
    def _construir_duas_colunas(self):
        lay_colunas = QHBoxLayout()
        lay_colunas.setSpacing(12)
        lay_colunas.setAlignment(Qt.AlignmentFlag.AlignTop)

        col_esquerda = QVBoxLayout()
        col_esquerda.setSpacing(12)

        # 1. Processos Mais Próximos
        self._construir_painel_proximos(col_esquerda)

        # 2. 4 Mini KPIs
        self._construir_mini_kpis(col_esquerda)

        # 3. Últimos Processos
        self._construir_painel_ultimos(col_esquerda)

        col_direita = QVBoxLayout()
        col_direita.setSpacing(12)

        # 4. Ações Rápidas (Card Azul Royal Fiel à Imagem 2)
        self._construir_acoes_rapidas_azul(col_direita)

        # 5. Calendário de Casamentos
        self._construir_calendario_casamentos(col_direita)

        # 6. Feed de Notificações
        self._construir_feed_notificacoes(col_direita)

        lay_colunas.addLayout(col_esquerda, 62)
        lay_colunas.addLayout(col_direita, 38)

        self.layout_conteudo.addLayout(lay_colunas)

    # -------------------------------------------------------------
    # Painel: Processos Mais Próximos
    # -------------------------------------------------------------
    def _construir_painel_proximos(self, parent_layout):
        self.card_proximos = QFrame()
        self.card_proximos.setObjectName("card_proximos")
        self.card_proximos.setStyleSheet("""
            QFrame#card_proximos {
                background-color: #11151F;
                border: 1px solid #1E2532;
                border-radius: 10px;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay = QVBoxLayout(self.card_proximos)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        lay_head = QHBoxLayout()
        lay_tit = QVBoxLayout()
        lay_tit.setSpacing(2)
        lbl_tit = QLabel("Processos Mais Próximos")
        lbl_tit.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;")
        lbl_sub = QLabel("Ordenados por data limite de entrega")
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 11px; border: none;")
        lay_tit.addWidget(lbl_tit)
        lay_tit.addWidget(lbl_sub)

        btn_ver_todos = QPushButton("Ver todos →")
        btn_ver_todos.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ver_todos.setStyleSheet("""
            QPushButton {
                color: #3B82F6;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QPushButton:hover { color: #60A5FA; text-decoration: underline; }
        """)
        btn_ver_todos.clicked.connect(lambda: self.solicitar_navegacao.emit(1))

        lay_head.addLayout(lay_tit)
        lay_head.addStretch()
        lay_head.addWidget(btn_ver_todos)
        lay.addLayout(lay_head)

        # Cabeçalho da Tabela com Stretches e Larguras Mínimas Seguras
        frame_th = QFrame()
        frame_th.setObjectName("th_proximos")
        frame_th.setStyleSheet("""
            QFrame#th_proximos {
                border-bottom: 1px solid #1E2532;
                background: transparent;
            }
            QLabel { border: none; color: #64748B; font-size: 10px; font-weight: bold; }
        """)
        lay_th = QHBoxLayout(frame_th)
        lay_th.setContentsMargins(10, 6, 10, 6)
        lay_th.setSpacing(10)

        th_prazo = QLabel("PRAZO")
        th_prazo.setMinimumWidth(110)
        th_proc = QLabel("PROCESSO")
        th_proc.setMinimumWidth(95)
        th_tipo = QLabel("TIPO")
        th_tipo.setMinimumWidth(130)
        th_interessado = QLabel("INTERESSADO")
        th_interessado.setMinimumWidth(140)
        th_status = QLabel("STATUS")
        th_status.setMinimumWidth(125)
        th_acao = QLabel("")
        th_acao.setFixedWidth(28)

        lay_th.addWidget(th_prazo, 2)
        lay_th.addWidget(th_proc, 2)
        lay_th.addWidget(th_tipo, 3)
        lay_th.addWidget(th_interessado, 4)
        lay_th.addWidget(th_status, 2)
        lay_th.addWidget(th_acao, 0)
        lay.addWidget(frame_th)

        # Container das Linhas
        self.container_linhas_proximos = QVBoxLayout()
        self.container_linhas_proximos.setSpacing(4)
        lay.addLayout(self.container_linhas_proximos)

        parent_layout.addWidget(self.card_proximos)

    # -------------------------------------------------------------
    # 4 Mini KPIs
    # -------------------------------------------------------------
    def _construir_mini_kpis(self, parent_layout):
        lay = QHBoxLayout()
        lay.setSpacing(8)

        card1, self.lbl_mini_certidoes, self.lbl_mini_certidoes_var = self._criar_mini_card("mini_1", "Certidões de Hoje", "18", "↑ 20%")
        card2, self.lbl_mini_obitos, self.lbl_mini_obitos_var = self._criar_mini_card("mini_2", "Óbitos de Hoje", "5", "↑ 25%")
        card3, self.lbl_mini_casamentos, self.lbl_mini_casamentos_var = self._criar_mini_card("mini_3", "Casamentos de Hoje", "3", "↑ 100%")
        card4, self.lbl_mini_reqs, self.lbl_mini_reqs_var = self._criar_mini_card("mini_4", "Requerimentos Pendentes", "7", "↓ 30%", cor_var="#EF4444")

        lay.addWidget(card1, 1)
        lay.addWidget(card2, 1)
        lay.addWidget(card3, 1)
        lay.addWidget(card4, 1)

        parent_layout.addLayout(lay)

    def _criar_mini_card(self, obj_id, titulo, valor_inicial, variacao, cor_var="#10B981"):
        card = QFrame()
        card.setObjectName(obj_id)
        card.setStyleSheet(f"""
            QFrame#{obj_id} {{
                background-color: #11151F;
                border: 1px solid #1E2532;
                border-radius: 8px;
            }}
            QLabel {{ border: none; background: transparent; }}
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(2)

        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: #8A92A6; font-size: 10px; border: none;")
        lbl_tit.setWordWrap(True)

        lay_val = QHBoxLayout()
        lbl_val = QLabel(valor_inicial)
        lbl_val.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;")

        lbl_var = QLabel(variacao)
        lbl_var.setStyleSheet(f"color: {cor_var}; font-size: 10px; font-weight: bold; border: none;")

        lay_val.addWidget(lbl_val)
        lay_val.addStretch()
        lay_val.addWidget(lbl_var)

        lay.addWidget(lbl_tit)
        lay.addLayout(lay_val)

        return card, lbl_val, lbl_var

    # -------------------------------------------------------------
    # Painel: Últimos Processos
    # -------------------------------------------------------------
    def _construir_painel_ultimos(self, parent_layout):
        self.card_ultimos = QFrame()
        self.card_ultimos.setObjectName("card_ultimos")
        self.card_ultimos.setStyleSheet("""
            QFrame#card_ultimos {
                background-color: #11151F;
                border: 1px solid #1E2532;
                border-radius: 10px;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay = QVBoxLayout(self.card_ultimos)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(6)

        lay_head = QHBoxLayout()
        lay_tit = QVBoxLayout()
        lay_tit.setSpacing(2)
        lbl_tit = QLabel("Últimos Processos")
        lbl_tit.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;")
        lbl_sub = QLabel("Histórico recente de entradas no sistema")
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 11px; border: none;")
        lay_tit.addWidget(lbl_tit)
        lay_tit.addWidget(lbl_sub)

        btn_ver_todos = QPushButton("Ver todos →")
        btn_ver_todos.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ver_todos.setStyleSheet("""
            QPushButton {
                color: #3B82F6;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QPushButton:hover { color: #60A5FA; text-decoration: underline; }
        """)
        btn_ver_todos.clicked.connect(lambda: self.solicitar_navegacao.emit(1))

        lay_head.addLayout(lay_tit)
        lay_head.addStretch()
        lay_head.addWidget(btn_ver_todos)
        lay.addLayout(lay_head)

        frame_th = QFrame()
        frame_th.setObjectName("th_ultimos")
        frame_th.setStyleSheet("""
            QFrame#th_ultimos {
                border-bottom: 1px solid #1E2532;
                background: transparent;
            }
            QLabel { border: none; color: #64748B; font-size: 10px; font-weight: bold; }
        """)
        lay_th = QHBoxLayout(frame_th)
        lay_th.setContentsMargins(10, 6, 10, 6)
        lay_th.setSpacing(10)

        th_data = QLabel("DATA/HORA")
        th_data.setMinimumWidth(110)
        th_proc = QLabel("PROCESSO")
        th_proc.setMinimumWidth(95)
        th_tipo = QLabel("TIPO")
        th_tipo.setMinimumWidth(130)
        th_interessado = QLabel("INTERESSADO")
        th_interessado.setMinimumWidth(140)
        th_status = QLabel("STATUS")
        th_status.setMinimumWidth(125)
        th_acao = QLabel("")
        th_acao.setFixedWidth(28)

        lay_th.addWidget(th_data, 2)
        lay_th.addWidget(th_proc, 2)
        lay_th.addWidget(th_tipo, 3)
        lay_th.addWidget(th_interessado, 4)
        lay_th.addWidget(th_status, 2)
        lay_th.addWidget(th_acao, 0)
        lay.addWidget(frame_th)

        self.container_linhas_ultimos = QVBoxLayout()
        self.container_linhas_ultimos.setSpacing(4)
        lay.addLayout(self.container_linhas_ultimos)

        parent_layout.addWidget(self.card_ultimos)

    # -------------------------------------------------------------
    # Painel Direita: AÇÕES RÁPIDAS (CARD AZUL ROYAL FIEL À IMAGEM 2)
    # -------------------------------------------------------------
    def _construir_acoes_rapidas_azul(self, parent_layout):
        card = QFrame()
        card.setObjectName("card_acoes_azul")
        card.setStyleSheet("""
            QFrame#card_acoes_azul {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #0D3B8E, stop:1 #09255E);
                border: 1px solid #1D4ED8;
                border-radius: 10px;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        # Cabeçalho com Raio
        lay_tit = QHBoxLayout()
        lay_tit.setSpacing(8)
        lbl_raio = QLabel("⚡")
        lbl_raio.setStyleSheet("color: #60A5FA; font-size: 15px; border: none;")
        lbl_tit = QLabel("Ações Rápidas")
        lbl_tit.setStyleSheet("color: white; font-size: 14px; font-weight: bold; border: none;")
        lay_tit.addWidget(lbl_raio)
        lay_tit.addWidget(lbl_tit)
        lay_tit.addStretch()
        lay.addLayout(lay_tit)

        # 3 Botões Verticais Espaçosos (Emitir Certidão foi unificado em Novo Processo)
        btn1 = self._criar_botao_acao_azul(
            titulo="Novo Processo",
            desc="Incluir um novo processo",
            icone="➕",
            callback=self._acao_novo_processo
        )
        btn2 = self._criar_botao_acao_azul(
            titulo="Novo Requerimento",
            desc="Cadastrar requerimento",
            icone="📋",
            callback=lambda: self.solicitar_navegacao.emit(3)
        )
        btn3 = self._criar_botao_acao_azul(
            titulo="Agendar Casamento",
            desc="Lançar nova habilitação",
            icone="💍",
            callback=lambda: self.solicitar_navegacao.emit(7)
        )

        lay.addWidget(btn1)
        lay.addWidget(btn2)
        lay.addWidget(btn3)

        parent_layout.addWidget(card)

    def _criar_botao_acao_azul(self, titulo, desc, icone, callback):
        btn = QPushButton()
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(8, 26, 68, 0.60);
                border: 1px solid rgba(59, 130, 246, 0.25);
                border-radius: 8px;
                padding: 6px 10px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(29, 78, 216, 0.45);
                border: 1px solid rgba(96, 165, 250, 0.55);
            }
        """)
        lay = QHBoxLayout(btn)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(10)

        # Círculo azul mais claro com o ícone
        frame_ic = QFrame()
        frame_ic.setFixedSize(30, 30)
        frame_ic.setStyleSheet("background-color: #1D4ED8; border-radius: 15px; border: none;")
        lay_ic = QVBoxLayout(frame_ic)
        lay_ic.setContentsMargins(0, 0, 0, 0)
        lbl_ic = QLabel(icone)
        lbl_ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ic.setStyleSheet("color: white; font-size: 13px; border: none;")
        lay_ic.addWidget(lbl_ic)

        # Textos em branco e azul claro
        lay_txt = QVBoxLayout()
        lay_txt.setSpacing(1)
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("color: white; font-size: 12px; font-weight: bold; border: none;")
        lbl_sub = QLabel(desc)
        lbl_sub.setStyleSheet("color: #93C5FD; font-size: 10px; border: none;")
        lay_txt.addWidget(lbl_tit)
        lay_txt.addWidget(lbl_sub)

        lay.addWidget(frame_ic)
        lay.addLayout(lay_txt, 1)

        btn.clicked.connect(callback)
        return btn

    def _acao_novo_processo(self):
        dlg = DialogNovoProcesso()
        if dlg.exec():
            self.carregar_dados_reais()

    # -------------------------------------------------------------
    # Painel Direita: Calendário de Casamentos
    # -------------------------------------------------------------
    def _construir_calendario_casamentos(self, parent_layout):
        self.calendario_casamentos = CalendarioCasamentosWidget()
        self.calendario_casamentos.abrir_casamentos_solicitado.connect(lambda: self.solicitar_navegacao.emit(7))
        parent_layout.addWidget(self.calendario_casamentos)

    # -------------------------------------------------------------
    # Painel Direita: Feed de Notificações
    # -------------------------------------------------------------
    def _construir_feed_notificacoes(self, parent_layout):
        card = QFrame()
        card.setObjectName("card_notif")
        card.setStyleSheet("""
            QFrame#card_notif {
                background-color: #11151F;
                border: 1px solid #1E2532;
                border-radius: 10px;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay = QVBoxLayout(card)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(6)

        lay_head = QHBoxLayout()
        lay_tit = QVBoxLayout()
        lay_tit.setSpacing(2)
        lbl_tit = QLabel("Notificações")
        lbl_tit.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;")
        lbl_sub = QLabel("Atividades e alertas recentes")
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 11px; border: none;")
        lay_tit.addWidget(lbl_tit)
        lay_tit.addWidget(lbl_sub)

        btn_ver_todas = QPushButton("Ver todas →")
        btn_ver_todas.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_ver_todas.setStyleSheet("""
            QPushButton {
                color: #3B82F6;
                font-size: 12px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QPushButton:hover { color: #60A5FA; text-decoration: underline; }
        """)
        btn_ver_todas.clicked.connect(lambda: self.solicitar_navegacao.emit(2))

        lay_head.addLayout(lay_tit)
        lay_head.addStretch()
        lay_head.addWidget(btn_ver_todas)
        lay.addLayout(lay_head)

        self.container_notificacoes = QVBoxLayout()
        self.container_notificacoes.setSpacing(4)
        lay.addLayout(self.container_notificacoes)

        parent_layout.addWidget(card)

    # =========================================================================
    # 4. RODAPÉ INSTITUCIONAL
    # =========================================================================
    def _construir_rodape(self):
        frame_rodape = QFrame()
        frame_rodape.setObjectName("rodape_institucional")
        frame_rodape.setStyleSheet("""
            QFrame#rodape_institucional {
                border-top: 1px solid #1E2532;
                padding-top: 4px;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay = QHBoxLayout(frame_rodape)
        lay.setContentsMargins(0, 4, 0, 0)

        lbl_esq = QLabel("Cartório Feitosa - RCPN | Sistema de Gestão Notarial e Registral")
        lbl_esq.setStyleSheet("color: #64748B; font-size: 10px; border: none;")

        lbl_dir = QLabel("Segurança • Organização • Agilidade")
        lbl_dir.setStyleSheet("color: #64748B; font-size: 10px; font-weight: 500; border: none;")

        lay.addWidget(lbl_esq)
        lay.addStretch()
        lay.addWidget(lbl_dir)

        self.layout_conteudo.addWidget(frame_rodape)

    # =========================================================================
    # RENDERIZADORES DE LINHA ELÁSTICOS E SEM CORTE DE TEXTO
    # =========================================================================
    def _criar_linha_tabela_proximo(self, proc):
        linha = QFrame()
        linha.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        linha.setStyleSheet("""
            QFrame {
                background-color: #151A27;
                border: 1px solid #1E2532;
                border-radius: 6px;
                min-height: 32px;
            }
            QFrame:hover {
                background-color: #1D2436;
                border-color: #2962FF;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay = QHBoxLayout(linha)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(10)

        # 1. Prazo
        prazo_txt, prazo_cor_bg, prazo_cor_txt = self._calcular_chip_prazo(proc.data_prazo)
        chip_prazo = QLabel(prazo_txt)
        chip_prazo.setMinimumWidth(110)
        chip_prazo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        chip_prazo.setStyleSheet(f"""
            background-color: {prazo_cor_bg};
            color: {prazo_cor_txt};
            font-size: 11px;
            font-weight: bold;
            padding: 4px 6px;
            border-radius: 4px;
            border: none;
        """)

        # 2. Processo
        lbl_id = QLabel(f"#{datetime.now().year}-{proc.id:04d}")
        lbl_id.setMinimumWidth(95)
        lbl_id.setStyleSheet("color: #38BDF8; font-family: monospace; font-size: 12px; font-weight: bold; border: none;")

        # 3. Tipo
        tipo = proc.tipo_servico or "Geral"
        lbl_tipo = QLabel(tipo)
        lbl_tipo.setMinimumWidth(130)
        lbl_tipo.setStyleSheet("color: #CBD5E1; font-size: 12px; border: none;")

        # 4. Interessado
        nome = proc.nome_cliente or "Sem nome"
        lbl_nome = QLabel(nome)
        lbl_nome.setMinimumWidth(140)
        lbl_nome.setStyleSheet("color: #F8FAFC; font-size: 12px; font-weight: 500; border: none;")

        # 5. Status Formatado sem Corte
        chip_status = self._criar_badge_status(proc.status)
        chip_status.setMinimumWidth(125)

        # 6. Ação
        btn_abrir = QPushButton("›")
        btn_abrir.setFixedSize(24, 24)
        btn_abrir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_abrir.setStyleSheet("""
            QPushButton {
                color: #8A92A6;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QPushButton:hover { color: #38BDF8; }
        """)
        btn_abrir.clicked.connect(lambda _, pid=proc.id: self._abrir_detalhes(pid))

        lay.addWidget(chip_prazo, 2)
        lay.addWidget(lbl_id, 2)
        lay.addWidget(lbl_tipo, 3)
        lay.addWidget(lbl_nome, 4)
        lay.addWidget(chip_status, 2)
        lay.addWidget(btn_abrir, 0)

        linha.mousePressEvent = lambda event, pid=proc.id: self._abrir_detalhes(pid)
        return linha

    def _criar_linha_tabela_ultimo(self, proc):
        linha = QFrame()
        linha.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        linha.setStyleSheet("""
            QFrame {
                background-color: #151A27;
                border: 1px solid #1E2532;
                border-radius: 6px;
                min-height: 32px;
            }
            QFrame:hover {
                background-color: #1D2436;
                border-color: #2962FF;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay = QHBoxLayout(linha)
        lay.setContentsMargins(8, 4, 8, 4)
        lay.setSpacing(10)

        dt_str = self._formatar_data_hora(proc.data_entrada)
        lbl_dt = QLabel(dt_str)
        lbl_dt.setMinimumWidth(110)
        lbl_dt.setStyleSheet("color: #8A92A6; font-size: 11px; border: none;")

        lbl_id = QLabel(f"#{datetime.now().year}-{proc.id:04d}")
        lbl_id.setMinimumWidth(95)
        lbl_id.setStyleSheet("color: #38BDF8; font-family: monospace; font-size: 12px; font-weight: bold; border: none;")

        tipo = proc.tipo_servico or "Geral"
        lbl_tipo = QLabel(tipo)
        lbl_tipo.setMinimumWidth(130)
        lbl_tipo.setStyleSheet("color: #CBD5E1; font-size: 12px; border: none;")

        nome = proc.nome_cliente or "Sem nome"
        lbl_nome = QLabel(nome)
        lbl_nome.setMinimumWidth(140)
        lbl_nome.setStyleSheet("color: #F8FAFC; font-size: 12px; font-weight: 500; border: none;")

        chip_status = self._criar_badge_status(proc.status)
        chip_status.setMinimumWidth(125)

        btn_abrir = QPushButton("›")
        btn_abrir.setFixedSize(24, 24)
        btn_abrir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_abrir.setStyleSheet("""
            QPushButton {
                color: #8A92A6;
                font-size: 18px;
                font-weight: bold;
                background: transparent;
                border: none;
            }
            QPushButton:hover { color: #38BDF8; }
        """)
        btn_abrir.clicked.connect(lambda _, pid=proc.id: self._abrir_detalhes(pid))

        lay.addWidget(lbl_dt, 2)
        lay.addWidget(lbl_id, 2)
        lay.addWidget(lbl_tipo, 3)
        lay.addWidget(lbl_nome, 4)
        lay.addWidget(chip_status, 2)
        lay.addWidget(btn_abrir, 0)

        linha.mousePressEvent = lambda event, pid=proc.id: self._abrir_detalhes(pid)
        return linha

    def _criar_item_notificacao(self, notif):
        item = QFrame()
        item.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        item.setStyleSheet("""
            QFrame {
                background-color: #151A27;
                border: 1px solid #1E2532;
                border-radius: 6px;
            }
            QFrame:hover {
                background-color: #1D2436;
                border-color: #2962FF;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay = QHBoxLayout(item)
        lay.setContentsMargins(8, 5, 8, 5)
        lay.setSpacing(8)

        tipo = (notif.tipo or "info").lower()
        if "sucesso" in tipo or "casamento" in tipo:
            ic_char, ic_bg, ic_cor = "✓", "rgba(16, 185, 129, 0.2)", "#10B981"
        elif "alerta" in tipo or "prazo" in tipo:
            ic_char, ic_bg, ic_cor = "⚠️", "rgba(245, 158, 11, 0.2)", "#F59E0B"
        else:
            ic_char, ic_bg, ic_cor = "ℹ️", "rgba(59, 130, 246, 0.2)", "#3B82F6"

        frame_ic = QFrame()
        frame_ic.setFixedSize(26, 26)
        frame_ic.setStyleSheet(f"background-color: {ic_bg}; border-radius: 13px; border: none;")
        lay_ic = QVBoxLayout(frame_ic)
        lay_ic.setContentsMargins(0, 0, 0, 0)
        lbl_ic = QLabel(ic_char)
        lbl_ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ic.setStyleSheet(f"color: {ic_cor}; font-size: 10px; font-weight: bold; border: none;")
        lay_ic.addWidget(lbl_ic)

        lay_txt = QVBoxLayout()
        lay_txt.setSpacing(1)
        lbl_tit = QLabel(notif.titulo)
        lbl_tit.setStyleSheet("color: white; font-size: 11px; font-weight: bold; border: none;")
        lbl_sub = QLabel(notif.subtitulo or "")
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 10px; border: none;")
        lay_txt.addWidget(lbl_tit)
        lay_txt.addWidget(lbl_sub)

        tempo_str = self._calcular_tempo_relativo(notif.data_criacao)
        lbl_tempo = QLabel(tempo_str)
        lbl_tempo.setStyleSheet("color: #64748B; font-size: 10px; border: none;")

        btn_fechar = QPushButton("✕")
        btn_fechar.setFixedSize(20, 20)
        btn_fechar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_fechar.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #64748B;
                border: none;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { color: #EF4444; }
        """)
        btn_fechar.clicked.connect(lambda _, nid=notif.id: self._dispensar_notificacao(nid))

        lay.addWidget(frame_ic)
        lay.addLayout(lay_txt, 1)
        lay.addWidget(lbl_tempo)
        lay.addWidget(btn_fechar)

        item.mousePressEvent = lambda event, n=notif: self._ao_clicar_notificacao(n)
        return item

    def _dispensar_notificacao(self, notif_id):
        db = SessionLocal()
        marcar_notificacao_lida(db, notif_id)
        db.close()
        self.carregar_dados_reais()

    def _ao_clicar_notificacao(self, notif):
        titulo_lower = (notif.titulo or "").lower()
        sub_lower = (notif.subtitulo or "").lower()

        if "casamento" in titulo_lower or "casamento" in sub_lower:
            self.solicitar_navegacao.emit(7)
        elif "processo" in titulo_lower or "processo" in sub_lower:
            self.solicitar_navegacao.emit(1)
        else:
            self.solicitar_navegacao.emit(2)

    def _criar_badge_status(self, status):
        status_norm = (status or "").strip()
        cor_bg = "rgba(100, 116, 139, 0.2)"
        cor_txt = "#94A3B8"
        texto_exibicao = status_norm or "Pendente"

        # Mapeamento elegante para evitar corte de palavras longas
        if "aguardando doc" in status_norm.lower():
            texto_exibicao = "Aguardando Doc."
            cor_bg = "rgba(245, 158, 11, 0.15)"
            cor_txt = "#F59E0B"
        elif status_norm in ["Completo", "Entregue", "Concluído", "Pronto para Celebração"]:
            texto_exibicao = "Concluído"
            cor_bg = "rgba(16, 185, 129, 0.15)"
            cor_txt = "#10B981"
        elif status_norm in ["Pendente", "Falta par", "Revisar"]:
            texto_exibicao = "Pendente"
            cor_bg = "rgba(245, 158, 11, 0.15)"
            cor_txt = "#F59E0B"
        elif status_norm in ["Em andamento", "Em análise", "Em Análise"]:
            texto_exibicao = "Em Análise"
            cor_bg = "rgba(59, 130, 246, 0.15)"
            cor_txt = "#3B82F6"
        elif status_norm in ["Urgente"]:
            texto_exibicao = "Urgente"
            cor_bg = "rgba(239, 68, 68, 0.15)"
            cor_txt = "#EF4444"

        lbl = QLabel(texto_exibicao)
        lbl.setToolTip(f"Status: {status_norm}")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet(f"""
            background-color: {cor_bg};
            color: {cor_txt};
            font-size: 11px;
            font-weight: bold;
            padding: 4px 8px;
            border-radius: 6px;
            border: none;
        """)
        return lbl

    def _calcular_chip_prazo(self, data_prazo):
        hoje = date.today()
        if not data_prazo:
            return "Em 3 dias", "rgba(59, 130, 246, 0.15)", "#38BDF8"

        dt_alvo = data_prazo.date() if isinstance(data_prazo, datetime) else hoje
        diff = (dt_alvo - hoje).days

        if diff <= 0:
            return f"Hoje ({hoje.strftime('%d/%m')})", "rgba(239, 68, 68, 0.15)", "#EF4444"
        elif diff == 1:
            amanha = hoje + timedelta(days=1)
            return f"Amanhã ({amanha.strftime('%d/%m')})", "rgba(245, 158, 11, 0.15)", "#F59E0B"
        else:
            return f"Em {diff} dias", "rgba(59, 130, 246, 0.15)", "#38BDF8"

    def _formatar_data_hora(self, dt):
        if not dt:
            return datetime.now().strftime("%d/%m %H:%M")
        if isinstance(dt, datetime):
            return dt.strftime("%d/%m %H:%M")
        return str(dt)[:16]

    def _calcular_tempo_relativo(self, dt):
        if not dt or not isinstance(dt, datetime):
            return "há pouco"
        delta = datetime.now() - dt
        segundos = delta.total_seconds()
        if segundos < 60:
            return "agora"
        elif segundos < 3600:
            minutos = int(segundos // 60)
            return f"há {minutos} min"
        elif segundos < 86400:
            horas = int(segundos // 3600)
            return f"há {horas} h"
        else:
            dias = int(segundos // 86400)
            return f"há {dias} d"

    def _abrir_detalhes(self, processo_id):
        dlg = DialogDetalhesProcesso(processo_id)
        dlg.exec()
        self.carregar_dados_reais()

    # =========================================================================
    # CARREGAMENTO COMPLETO DE DADOS
    # =========================================================================
    def carregar_dados_reais(self):
        """Carrega e sincroniza todas as métricas do banco de dados na tela sem duplicar."""
        db = SessionLocal()
        try:
            dados = obter_metricas_dashboard_completas(db)

            # 1. Top KPIs
            self.lbl_kpi_total.setText(str(dados["total_processos"]))
            self.lbl_kpi_pendentes.setText(str(dados["processos_pendentes"]))
            self.lbl_kpi_certidoes.setText(str(dados["certidoes_emitidas"]))
            self.lbl_kpi_atendimentos.setText(str(dados["atendimentos_hoje"]))

            # 2. Mini KPIs
            self.lbl_mini_certidoes.setText(str(dados["certidoes_hoje"]))
            self.lbl_mini_obitos.setText(str(dados["obitos_hoje"]))
            self.lbl_mini_casamentos.setText(str(dados["casamentos_hoje"]))
            self.lbl_mini_reqs.setText(str(dados["req_pendentes"]))

            # 3. Tabela: Processos Mais Próximos
            self._limpar_layout(self.container_linhas_proximos)
            if not dados["proximos"]:
                lbl_vazio = QLabel("Nenhum processo pendente com prazo cadastrado.")
                lbl_vazio.setStyleSheet("color: #64748B; font-size: 12px; padding: 10px; border: none;")
                self.container_linhas_proximos.addWidget(lbl_vazio)
            else:
                for proc in dados["proximos"][:4]:
                    self.container_linhas_proximos.addWidget(self._criar_linha_tabela_proximo(proc))

            # 4. Tabela: Últimos Processos
            self._limpar_layout(self.container_linhas_ultimos)
            if not dados["ultimos"]:
                lbl_vazio = QLabel("Nenhum processo recente no sistema.")
                lbl_vazio.setStyleSheet("color: #64748B; font-size: 12px; padding: 10px; border: none;")
                self.container_linhas_ultimos.addWidget(lbl_vazio)
            else:
                for proc in dados["ultimos"][:4]:
                    self.container_linhas_ultimos.addWidget(self._criar_linha_tabela_ultimo(proc))

            # 5. Calendário de Casamentos
            self.calendario_casamentos.atualizar_casamentos(dados["casamentos"])

            # 6. Feed de Notificações
            self._limpar_layout(self.container_notificacoes)
            notifs = [n for n in dados["notificacoes"] if not getattr(n, 'lida', 0)]
            if not notifs:
                lbl_limpo = QLabel("Sem notificações pendentes no momento. 🎉")
                lbl_limpo.setStyleSheet("color: #64748B; font-size: 11px; padding: 6px; border: none;")
                self.container_notificacoes.addWidget(lbl_limpo)
            else:
                for notif in notifs[:3]:
                    self.container_notificacoes.addWidget(self._criar_item_notificacao(notif))

        except Exception as e:
            print(f"[ERRO] Falha ao carregar métricas da Dashboard: {e}")
        finally:
            db.close()

    def _limpar_layout(self, layout):
        """Esvazia layout imediatamente com takeAt para evitar duplicatas de renderização."""
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
