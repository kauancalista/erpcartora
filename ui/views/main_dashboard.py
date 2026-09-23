import os
import threading
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame,
    QLineEdit, QListWidget, QListWidgetItem, QGraphicsOpacityEffect
)
from PyQt6.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, pyqtProperty, QParallelAnimationGroup
from PyQt6.QtGui import QCursor, QIcon, QShortcut, QKeySequence, QColor

# Importando as 9 telas originais do sistema
from ui.views.view_dashboard import TelaDashboard
from ui.views.view_processos import TelaProcessos
from ui.views.view_tarefas import TelaTarefas
from ui.views.view_requerimentos import TelaRequerimentos
from ui.views.view_casamentos import TelaCasamentos
from ui.views.view_agenda import TelaAgenda
from ui.views.view_configuracoes import TelaConfiguracoes
from ui.views.view_relatorios import TelaRelatorios
from ui.views.view_scanner import TelaScanner
from ui.views.view_livros import TelaLivros
from ui.dialogs.form_detalhes_processo import DialogDetalhesProcesso
from ui.componentes import notificar
from database.conexao import SessionLocal
from database.crud import listar_todos_processos, listar_todos_casamentos


class BotaoMenuAnimado(QPushButton):
    def __init__(self, texto, caminho_icone=None, parent=None):
        super().__init__(f"  {texto}", parent)
        if caminho_icone and os.path.exists(caminho_icone):
            self.setIcon(QIcon(caminho_icone))
            self.setIconSize(QSize(20, 20))
            
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setCheckable(True)

        self._bg_color = QColor(11, 14, 20, 0)
        self._text_color = QColor(138, 146, 166, 255)
        self._padding_left = 14
        
        self.anim_group = QParallelAnimationGroup(self)
        self.anim_bg = QPropertyAnimation(self, b"bgColor")
        self.anim_txt = QPropertyAnimation(self, b"textColor")
        self.anim_pad = QPropertyAnimation(self, b"paddingLeft")
        
        self.anim_bg.setDuration(150)
        self.anim_txt.setDuration(150)
        self.anim_pad.setDuration(150)
        self.anim_pad.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        self.anim_group.addAnimation(self.anim_bg)
        self.anim_group.addAnimation(self.anim_txt)
        self.anim_group.addAnimation(self.anim_pad)
        
        self.toggled.connect(self._ao_alterar_estado)
        self.atualizar_estilo()

    @pyqtProperty(QColor)
    def bgColor(self): return self._bg_color
    @bgColor.setter
    def bgColor(self, cor):
        self._bg_color = cor
        self.atualizar_estilo()

    @pyqtProperty(QColor)
    def textColor(self): return self._text_color
    @textColor.setter
    def textColor(self, cor):
        self._text_color = cor
        self.atualizar_estilo()

    @pyqtProperty(int)
    def paddingLeft(self): return self._padding_left
    @paddingLeft.setter
    def paddingLeft(self, pad):
        self._padding_left = pad
        self.atualizar_estilo()

    def atualizar_estilo(self):
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba({self._bg_color.red()}, {self._bg_color.green()}, {self._bg_color.blue()}, {self._bg_color.alpha()});
                color: rgba({self._text_color.red()}, {self._text_color.green()}, {self._text_color.blue()}, {self._text_color.alpha()});
                text-align: left;
                padding: 10px 14px 10px {self._padding_left}px;
                border: none;
                border-radius: 8px;
                font-size: 13px;
                font-weight: 600;
            }}
        """)

    def _animar(self, bg_target, txt_target, pad_target):
        self.anim_group.stop()
        self.anim_bg.setEndValue(bg_target)
        self.anim_txt.setEndValue(txt_target)
        self.anim_pad.setEndValue(pad_target)
        self.anim_group.start()

    def enterEvent(self, event):
        if not self.isChecked():
            self._animar(QColor(26, 33, 51, 255), QColor(255, 255, 255, 255), 20)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.isChecked():
            self._animar(QColor(11, 14, 20, 0), QColor(138, 146, 166, 255), 14)
        super().leaveEvent(event)

    def _ao_alterar_estado(self, checked):
        if checked:
            self._animar(QColor(41, 98, 255, 255), QColor(255, 255, 255, 255), 20)
        else:
            if self.underMouse():
                self._animar(QColor(26, 33, 51, 255), QColor(255, 255, 255, 255), 20)
            else:
                self._animar(QColor(11, 14, 20, 0), QColor(138, 146, 166, 255), 14)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Cartório - RCPN Feitosa ERP")
        self.resize(1280, 780)
        self.setMinimumSize(1024, 600)

        # Regra de ouro global: NENHUM QLabel herda bordas de QFrames
        self.setStyleSheet("""
            QMainWindow { background-color: #0B0E14; }
            QLabel { border: none; background: transparent; }
        """)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ==========================================
        # 1. BARRA LATERAL (ESTRITAMENTE AS 9 ABAS ORIGINAIS)
        # ==========================================
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(230)
        sidebar.setStyleSheet("""
            QFrame#sidebar {
                background-color: #0E121A;
                border-right: 1px solid #1A2133;
            }
            QLabel { border: none; background: transparent; }
        """)
        layout_sidebar = QVBoxLayout(sidebar)
        layout_sidebar.setContentsMargins(12, 18, 12, 18)
        layout_sidebar.setSpacing(4)

        # Logo / Marca
        lay_logo = QHBoxLayout()
        lay_logo.setContentsMargins(4, 0, 4, 15)
        lay_logo.setSpacing(10)
        lbl_icone_logo = QLabel("🏛️")
        lbl_icone_logo.setStyleSheet("font-size: 22px; border: none; background: transparent;")
        lay_txt_logo = QVBoxLayout()
        lay_txt_logo.setSpacing(0)
        lbl_logo_tit = QLabel("Cartório Feitosa")
        lbl_logo_tit.setStyleSheet("color: white; font-size: 15px; font-weight: bold; border: none;")
        lbl_logo_sub = QLabel("RCPN - Registro Civil")
        lbl_logo_sub.setStyleSheet("color: #8A92A6; font-size: 11px; border: none;")
        lay_txt_logo.addWidget(lbl_logo_tit)
        lay_txt_logo.addWidget(lbl_logo_sub)
        lay_logo.addWidget(lbl_icone_logo)
        lay_logo.addLayout(lay_txt_logo)
        lay_logo.addStretch()
        layout_sidebar.addLayout(lay_logo)

        # As 9 Abas Originais Necessárias
        self.btn_dashboard = self.criar_botao_menu("Dashboard", "assets/icons/icon_menu_dashboard.png")
        self.btn_processos = self.criar_botao_menu("Processos", "assets/icons/icon_menu_processos.png")
        self.btn_tarefas = self.criar_botao_menu("Tarefas", "assets/icons/icon_menu_tarefas.png")
        self.btn_requerimentos = self.criar_botao_menu("Requerimentos", "assets/icons/icon_menu_requerimentos.png")
        self.btn_relatorios = self.criar_botao_menu("Relatórios", "assets/icons/icon_menu_relatorios.png")
        self.btn_agenda = self.criar_botao_menu("Agenda", "assets/icons/icon_menu_agenda.png")
        self.btn_config = self.criar_botao_menu("Configurações", "assets/icons/icon_menu_config.png")
        self.btn_casamentos = self.criar_botao_menu("Casamentos", "assets/icons/icon_menu_casamentos.png")
        self.btn_scanner = self.criar_botao_menu("Scanner e OCR", "assets/icons/icon_menu_scanner.png")
        self.btn_livros = self.criar_botao_menu("Livros", "assets/icons/icon_menu_livros.png")

        # Conectar cliques às 9 telas
        self.btn_dashboard.clicked.connect(lambda: self.mudar_tela(0))
        self.btn_processos.clicked.connect(lambda: self.mudar_tela(1))
        self.btn_tarefas.clicked.connect(lambda: self.mudar_tela(2))
        self.btn_requerimentos.clicked.connect(lambda: self.mudar_tela(3))
        self.btn_relatorios.clicked.connect(lambda: self.mudar_tela(4))
        self.btn_agenda.clicked.connect(lambda: self.mudar_tela(5))
        self.btn_config.clicked.connect(lambda: self.mudar_tela(6))
        self.btn_casamentos.clicked.connect(lambda: self.mudar_tela(7))
        self.btn_scanner.clicked.connect(lambda: self.mudar_tela(8))
        self.btn_livros.clicked.connect(lambda: self.mudar_tela(9))

        # Adiciona na barra
        layout_sidebar.addWidget(self.btn_dashboard)
        layout_sidebar.addWidget(self.btn_processos)
        layout_sidebar.addWidget(self.btn_tarefas)
        layout_sidebar.addWidget(self.btn_requerimentos)
        layout_sidebar.addWidget(self.btn_relatorios)
        layout_sidebar.addWidget(self.btn_agenda)
        layout_sidebar.addWidget(self.btn_config)
        layout_sidebar.addWidget(self.btn_casamentos)
        layout_sidebar.addWidget(self.btn_scanner)
        layout_sidebar.addWidget(self.btn_livros)
        layout_sidebar.addStretch()

        # Card de Conexão do Servidor
        self.frame_status_banco = QFrame()
        self.frame_status_banco.setObjectName("card_status_banco")
        self.frame_status_banco.setStyleSheet("""
            QFrame#card_status_banco {
                background-color: #11151F;
                border: 1px solid #1E2532;
                border-radius: 8px;
                padding: 6px;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay_status = QVBoxLayout(self.frame_status_banco)
        lay_status.setContentsMargins(10, 10, 10, 10)
        lay_status.setSpacing(6)

        lay_dot_status = QHBoxLayout()
        self.dot_status = QLabel("●")
        self.dot_status.setFixedWidth(14)
        self.lbl_status_banco = QLabel("Servidor Conectado")
        self.lbl_status_banco.setStyleSheet("font-size: 11px; font-weight: bold; color: #2ECC71;")
        lay_dot_status.addWidget(self.dot_status)
        lay_dot_status.addWidget(self.lbl_status_banco, 1)
        lay_status.addLayout(lay_dot_status)

        self.lbl_servidor_host = QLabel("PostgreSQL Produção")
        self.lbl_servidor_host.setStyleSheet("color: #8A92A6; font-size: 10px;")
        lay_status.addWidget(self.lbl_servidor_host)

        lay_rodape_card = QHBoxLayout()
        self.lbl_versao = QLabel("v1.0.0")
        self.lbl_versao.setStyleSheet("color: #64748B; font-size: 10px;")
        self.btn_reconectar_banco = QPushButton("Sincronizar")
        self.btn_reconectar_banco.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_reconectar_banco.setStyleSheet("""
            QPushButton {
                background-color: #1A2133;
                color: #A9CCE3;
                font-size: 10px;
                border-radius: 4px;
                padding: 4px 8px;
                font-weight: bold;
                border: 1px solid #2C364C;
            }
            QPushButton:hover {
                background-color: #2962FF;
                color: white;
            }
        """)
        self.btn_reconectar_banco.clicked.connect(self.acao_reconectar_manual)
        lay_rodape_card.addWidget(self.lbl_versao)
        lay_rodape_card.addStretch()
        lay_rodape_card.addWidget(self.btn_reconectar_banco)
        lay_status.addLayout(lay_rodape_card)

        layout_sidebar.addWidget(self.frame_status_banco)
        layout_principal.addWidget(sidebar)

        # ==========================================
        # 2. ÁREA PRINCIPAL (HEADER + STACK DE TELAS)
        # ==========================================
        widget_direita = QWidget()
        layout_direita = QVBoxLayout(widget_direita)
        layout_direita.setContentsMargins(0, 0, 0, 0)
        layout_direita.setSpacing(0)

        # Header Superior (Limpo e Funcional, Sem login Cleverton)
        self._construir_header_topo(layout_direita)

        # Spotlight de Busca Global Flutuante
        self._construir_spotlight_busca(layout_direita)

        # Stack de Telas
        self.stack = QStackedWidget()

        # Instanciação das Telas
        self.tela_dash = TelaDashboard()
        self.tela_dash.solicitar_navegacao.connect(self.mudar_tela)

        tela_proc = TelaProcessos()
        tela_tar = TelaTarefas()
        tela_req = TelaRequerimentos()
        tela_relat = TelaRelatorios()
        tela_agenda = TelaAgenda()
        tela_config = TelaConfiguracoes()
        tela_cas = TelaCasamentos()
        tela_scan = TelaScanner()
        self.tela_livros = TelaLivros()

        self.stack.addWidget(self.tela_dash)    # 0 - dashboard
        self.stack.addWidget(tela_proc)         # 1 - processos
        self.stack.addWidget(tela_tar)          # 2 - tarefas
        self.stack.addWidget(tela_req)          # 3 - requerimentos
        self.stack.addWidget(tela_relat)        # 4 - Relatórios
        self.stack.addWidget(tela_agenda)       # 5 - Agenda
        self.stack.addWidget(tela_config)       # 6 - Configurações
        self.stack.addWidget(tela_cas)          # 7 - Casamentos
        self.stack.addWidget(tela_scan)         # 8 - Scanner
        self.stack.addWidget(self.tela_livros)  # 9 - Livros

        layout_direita.addWidget(self.stack)
        layout_principal.addWidget(widget_direita)

        # Configurações Iniciais
        self.btn_dashboard.setChecked(True)
        self.mudar_tela(0, force=True)
        self.atualizar_badge_status()

        # Timer de reconexão automática
        self.timer_reconectar = QTimer(self)
        self.timer_reconectar.timeout.connect(self.verificar_reconexao_automatica)
        self.timer_reconectar.start(30000)
        
        # Dispara a primeira checagem de rede em background 0.1s após a tela abrir
        QTimer.singleShot(100, self.verificar_reconexao_automatica)

        # Timer do Relógio Dinâmico
        self.timer_relogio = QTimer(self)
        self.timer_relogio.timeout.connect(self._atualizar_relogio)
        self.timer_relogio.start(1000)
        self._atualizar_relogio()

        # Atalho Ctrl+K para busca global
        self.atalho_busca = QShortcut(QKeySequence("Ctrl+K"), self)
        self.atalho_busca.activated.connect(self._focar_busca)

    # ==========================================
    # HEADER SUPERIOR: LIMPO, MODERNO E SEM LOGIN
    # ==========================================
    def _construir_header_topo(self, parent_layout):
        frame_header = QFrame()
        frame_header.setObjectName("topo_executivo")
        frame_header.setFixedHeight(44)
        frame_header.setStyleSheet("""
            QFrame#topo_executivo {
                background-color: #0B0E14;
                border-bottom: 1px solid #1E2532;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay_h = QHBoxLayout(frame_header)
        lay_h.setContentsMargins(18, 4, 18, 4)
        lay_h.setSpacing(16)

        # Barra de Busca Global Elástica com Ctrl+K
        frame_busca = QFrame()
        frame_busca.setObjectName("box_busca_global")
        frame_busca.setFixedHeight(32)
        frame_busca.setMinimumWidth(320)
        frame_busca.setMaximumWidth(520)
        frame_busca.setStyleSheet("""
            QFrame#box_busca_global {
                background-color: #11151F;
                border: 1px solid #1E2532;
                border-radius: 6px;
            }
            QLabel { border: none; background: transparent; }
        """)
        lay_b = QHBoxLayout(frame_busca)
        lay_b.setContentsMargins(10, 0, 10, 0)
        lay_b.setSpacing(8)

        lbl_lupa = QLabel("🔍")
        lbl_lupa.setStyleSheet("color: #8A92A6; font-size: 12px;")

        self.input_busca_global = QLineEdit()
        self.input_busca_global.setPlaceholderText("Buscar por nome, CPF, processo, protocolo... (Ctrl + K)")
        self.input_busca_global.setStyleSheet("""
            QLineEdit {
                background: transparent;
                border: none;
                color: white;
                font-size: 12px;
            }
        """)
        self.timer_busca = QTimer(self)
        self.timer_busca.setSingleShot(True)
        self.timer_busca.setInterval(250)
        self.timer_busca.timeout.connect(self._executar_busca_global)
        self.input_busca_global.textChanged.connect(lambda: self.timer_busca.start())

        lbl_badge_ctrlk = QLabel("Ctrl + K")
        lbl_badge_ctrlk.setStyleSheet("""
            background-color: #1A2133;
            color: #8A92A6;
            font-size: 10px;
            font-weight: bold;
            padding: 1px 5px;
            border-radius: 4px;
            border: 1px solid #2C364C;
        """)

        lay_b.addWidget(lbl_lupa)
        lay_b.addWidget(self.input_busca_global, 1)
        lay_b.addWidget(lbl_badge_ctrlk)

        lay_h.addWidget(frame_busca)
        lay_h.addStretch()

        # Direita: Relógio Dinâmico & Data Horizontal Compacto
        lay_relogio = QHBoxLayout()
        lay_relogio.setSpacing(12)
        self.lbl_data_topo = QLabel()
        self.lbl_data_topo.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_data_topo.setStyleSheet("color: #8A92A6; font-size: 11px;")

        self.lbl_hora_topo = QLabel()
        self.lbl_hora_topo.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_hora_topo.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")

        lay_relogio.addWidget(self.lbl_data_topo)
        lay_relogio.addWidget(self.lbl_hora_topo)
        lay_h.addLayout(lay_relogio)

        parent_layout.addWidget(frame_header)

    def _construir_spotlight_busca(self, parent_layout):
        self.lista_busca_spotlight = QListWidget()
        self.lista_busca_spotlight.setStyleSheet("""
            QListWidget {
                background-color: #151A27;
                border: 1px solid #2962FF;
                border-radius: 8px;
                padding: 5px;
                color: white;
                font-size: 13px;
                margin: 0 40px;
            }
            QListWidget::item { padding: 10px; border-bottom: 1px solid #1E2532; }
            QListWidget::item:hover { background-color: #1A2133; }
        """)
        self.lista_busca_spotlight.setMaximumHeight(220)
        self.lista_busca_spotlight.hide()
        self.lista_busca_spotlight.itemClicked.connect(self._ao_clicar_resultado_busca)
        parent_layout.addWidget(self.lista_busca_spotlight)

    def _focar_busca(self):
        self.input_busca_global.setFocus()
        self.input_busca_global.selectAll()

    def _executar_busca_global(self):
        termo = self.input_busca_global.text().lower().strip()
        self.lista_busca_spotlight.clear()

        if not termo:
            self.lista_busca_spotlight.hide()
            return

        db = SessionLocal()
        processos = listar_todos_processos(db)
        casamentos = listar_todos_casamentos(db)
        db.close()

        achados = 0
        ano = datetime.now().year

        for p in processos:
            prot = f"#{ano}-{p.id:04d}"
            nome = (p.nome_cliente or "").lower()
            cpf = (p.cpf or "").lower()
            servico = (p.tipo_servico or "").lower()

            if termo in nome or termo in prot or termo in cpf or termo in servico:
                item = QListWidgetItem(f"📄 PROCESSO {prot} - {p.nome_cliente} ({p.tipo_servico}) | Status: {p.status}")
                item.setData(Qt.ItemDataRole.UserRole, ("processo", p.id))
                self.lista_busca_spotlight.addItem(item)
                achados += 1

        for c in casamentos:
            noivos = f"{c.nome_noivo} & {c.nome_noiva}".lower()
            prot = (c.protocolo or "").lower()
            if termo in noivos or termo in prot:
                item = QListWidgetItem(f"💍 CASAMENTO: {c.nome_noivo} & {c.nome_noiva} ({c.protocolo})")
                item.setData(Qt.ItemDataRole.UserRole, ("casamento", c.id))
                self.lista_busca_spotlight.addItem(item)
                achados += 1

        if achados > 0:
            self.lista_busca_spotlight.show()
        else:
            item = QListWidgetItem("Nenhum resultado encontrado para esta busca...")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.lista_busca_spotlight.addItem(item)
            self.lista_busca_spotlight.show()

    def _ao_clicar_resultado_busca(self, item):
        dados = item.data(Qt.ItemDataRole.UserRole)
        if not dados:
            return
        tipo, item_id = dados
        if tipo == "processo":
            dlg = DialogDetalhesProcesso(item_id)
            dlg.exec()
        elif tipo == "casamento":
            self.mudar_tela(7)

        self.input_busca_global.clear()
        self.lista_busca_spotlight.hide()
        self.atualizar_todas_telas()

    def _atualizar_relogio(self):
        agora = datetime.now()
        nomes_meses = [
            "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
            "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
        ]
        self.lbl_data_topo.setText(f"{agora.day} de {nomes_meses[agora.month]} de {agora.year}")
        self.lbl_hora_topo.setText(agora.strftime("%H:%M:%S"))

    def criar_botao_menu(self, texto, caminho_icone):
        return BotaoMenuAnimado(texto, caminho_icone)

    def _dispensar_notificacao(self, notif_id):
        from database.conexao import get_db_session
        with get_db_session() as db:
            marcar_notificacao_lida(db, notif_id)
        self.carregar_dados_reais()

    def atualizar_todas_telas(self):
        """Atualiza todas as abas ativas e em segundo plano."""
        for i in range(self.stack.count()):
            tela = self.stack.widget(i)
            try:
                if hasattr(tela, 'carregar_dados_reais'):
                    tela.carregar_dados_reais()
                elif hasattr(tela, 'carregar_dados'):
                    tela.carregar_dados()
                elif hasattr(tela, 'carregar_dados_hub'):
                    tela.carregar_dados_hub()
                elif hasattr(tela, 'carregar_dados_do_banco'):
                    tela.carregar_dados_do_banco()
                elif hasattr(tela, 'carregar_dados_globais'):
                    tela.carregar_dados_globais()
            except Exception as e:
                print(f"[AVISO] Erro ao atualizar tela {i}: {e}")

    def mudar_tela(self, indice, force=False):
        if self.stack.currentIndex() == indice and not force:
            return

        botoes = [
            self.btn_dashboard, self.btn_processos, self.btn_tarefas,
            self.btn_requerimentos, self.btn_relatorios, self.btn_agenda,
            self.btn_config, self.btn_casamentos, self.btn_scanner,
            self.btn_livros
        ]
        for i, btn in enumerate(botoes):
            btn.setChecked(i == indice)

        # 1. Aplicar Efeito de Opacidade
        self.efeito_fade = QGraphicsOpacityEffect(self.stack)
        self.stack.setGraphicsEffect(self.efeito_fade)

        # 2. Fade Out
        self.anim_out = QPropertyAnimation(self.efeito_fade, b"opacity")
        self.anim_out.setDuration(100) # Rápido e responsivo
        self.anim_out.setStartValue(1.0)
        self.anim_out.setEndValue(0.0)
        self.anim_out.setEasingCurve(QEasingCurve.Type.OutQuad)

        # 3. Fade In
        self.anim_in = QPropertyAnimation(self.efeito_fade, b"opacity")
        self.anim_in.setDuration(150)
        self.anim_in.setStartValue(0.0)
        self.anim_in.setEndValue(1.0)
        self.anim_in.setEasingCurve(QEasingCurve.Type.InQuad)

        def ao_fadeOut_concluido():
            self.stack.setCurrentIndex(indice)
            self.anim_in.start()
            
            # Atualiza a tela que acabou de ficar visível (em background enquanto o fade in roda)
            tela_ativa = self.stack.widget(indice)
            try:
                if hasattr(tela_ativa, 'carregar_dados_reais'):
                    tela_ativa.carregar_dados_reais()
                elif hasattr(tela_ativa, 'carregar_dados'):
                    tela_ativa.carregar_dados()
                elif hasattr(tela_ativa, 'carregar_dados_do_banco'):
                    tela_ativa.carregar_dados_do_banco()
            except Exception:
                pass

        self.anim_out.finished.connect(ao_fadeOut_concluido)
        self.anim_out.start()

    def closeEvent(self, event):
        """Shutdown gracioso: para o servidor Flask antes de fechar."""
        try:
            self.tela_livros.parar_servidor()
        except Exception:
            pass
        super().closeEvent(event)


    def atualizar_badge_status(self):
        import database.conexao as conexao
        if conexao.STATUS_CONEXAO == "PRODUCAO":
            self.dot_status.setStyleSheet("color: #2ECC71; font-size: 14px; border: none; background: transparent;")
            self.lbl_status_banco.setText("Servidor Online")
            self.lbl_status_banco.setStyleSheet("color: #2ECC71; font-size: 11px; font-weight: bold; border: none;")
            self.lbl_servidor_host.setText("PostgreSQL Produção")
            self.btn_reconectar_banco.setText("Sincronizar")
        else:
            self.dot_status.setStyleSheet("color: #E67E22; font-size: 14px; border: none; background: transparent;")
            self.lbl_status_banco.setText("Modo Standby")
            self.lbl_status_banco.setStyleSheet("color: #E67E22; font-size: 11px; font-weight: bold; border: none;")
            self.lbl_servidor_host.setText("SQLite Local Temporário")
            self.btn_reconectar_banco.setText("⚡ Reconectar")

    def verificar_reconexao_automatica(self):
        import database.conexao as conexao
        if conexao.STATUS_CONEXAO != "PRODUCAO":
            threading.Thread(target=self._thread_tentar_reconexao, kwargs={"manual": False}, daemon=True).start()

    def _thread_tentar_reconexao(self, manual=False):
        import database.conexao as conexao
        sucesso, msg = conexao.tentar_reconectar_e_sincronizar()
        if sucesso:
            QTimer.singleShot(0, self._ao_reconectar_com_sucesso)
        elif manual:
            QTimer.singleShot(0, lambda: notificar(self, "PostgreSQL da empresa ainda fora do alcance.", "aviso"))

    def _ao_reconectar_com_sucesso(self):
        self.atualizar_badge_status()
        self.atualizar_todas_telas()
        notificar(self, "🎉 Conexão estabelecida! Dados temporários migrados para a produção.", "sucesso")

    def acao_reconectar_manual(self):
        self.btn_reconectar_banco.setEnabled(False)
        self.btn_reconectar_banco.setText("...")

        def tarefa():
            self._thread_tentar_reconexao(manual=True)
            QTimer.singleShot(1500, lambda: self.btn_reconectar_banco.setEnabled(True))
            QTimer.singleShot(1500, self.atualizar_badge_status)

        threading.Thread(target=tarefa, daemon=True).start()
