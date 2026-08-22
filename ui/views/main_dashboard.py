from PyQt6.QtWidgets import (QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
                             QPushButton, QStackedWidget, QLabel, QFrame)
from PyQt6.QtCore import Qt

# Importando todas as nossas 4 telas!
from ui.views.view_dashboard import TelaDashboard
from ui.views.view_processos import TelaProcessos
from ui.views.view_tarefas import TelaTarefas
from ui.views.view_requerimentos import TelaRequerimentos
from ui.views.view_casamentos import TelaCasamentos



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sistema Cartório - ERP Desktop")
        self.resize(1150, 720)

        widget_central = QWidget()
        self.setCentralWidget(widget_central)

        layout_principal = QHBoxLayout(widget_central)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ==========================================
        # 1. BARRA LATERAL (SIDEBAR)
        # ==========================================
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(240)
        layout_sidebar = QVBoxLayout(sidebar)
        layout_sidebar.setContentsMargins(15, 25, 15, 25)
        layout_sidebar.setSpacing(10)

        lbl_logo = QLabel("🏛️ CARTÓRIO")
        lbl_logo.setStyleSheet(
            "color: white; font-size: 22px; font-weight: bold; padding-left: 10px; margin-bottom: 25px;")
        layout_sidebar.addWidget(lbl_logo)

        # Criando os  botões do menu
        self.btn_dashboard = self.criar_botao_menu("🏠 Dashboard")
        self.btn_processos = self.criar_botao_menu("📄 Documentos")
        self.btn_requerimentos = self.criar_botao_menu("📝 Requerimentos")
        self.btn_relatorios = self.criar_botao_menu("📊 Relatórios")
        self.btn_tarefas = self.criar_botao_menu("✅ Tarefas")
        self.btn_agenda = self.criar_botao_menu("📅 Agenda")
        self.btn_config = self.criar_botao_menu("⚙️ Configurações")
        self.btn_casamentos = self.criar_botao_menu("💍 Casamentos")

        # Ligando os cliques
        self.btn_dashboard.clicked.connect(lambda: self.mudar_tela(0))
        self.btn_processos.clicked.connect(lambda: self.mudar_tela(1))
        self.btn_tarefas.clicked.connect(lambda: self.mudar_tela(2))
        self.btn_requerimentos.clicked.connect(lambda: self.mudar_tela(3))
        # (As novas telas podem apontar para widgets em branco por enquanto)
        self.btn_relatorios.clicked.connect(lambda: self.mudar_tela(4))
        self.btn_agenda.clicked.connect(lambda: self.mudar_tela(5))
        self.btn_config.clicked.connect(lambda: self.mudar_tela(6))
        self.btn_casamentos.clicked.connect(lambda: self.mudar_tela(7))

        # Adicionando no menu lateral
        layout_sidebar.addWidget(self.btn_dashboard)
        layout_sidebar.addWidget(self.btn_processos)
        layout_sidebar.addWidget(self.btn_requerimentos)
        layout_sidebar.addWidget(self.btn_relatorios)
        layout_sidebar.addWidget(self.btn_tarefas)
        layout_sidebar.addWidget(self.btn_agenda)
        layout_sidebar.addWidget(self.btn_config)
        layout_sidebar.addWidget(self.btn_casamentos)
        layout_sidebar.addStretch()
        # ==========================================
        # 2. ÁREA CENTRAL (O Empilhador de Telas)
        # ==========================================
        self.stack = QStackedWidget()

        # Instanciando as telas reais
        tela_dash = TelaDashboard()
        tela_proc = TelaProcessos()
        tela_tar = TelaTarefas()
        tela_req = TelaRequerimentos()
        tela_cas = TelaCasamentos()

        # Adicionando na pilha exata (0 a 3)
        self.stack.addWidget(tela_dash)  # 0
        self.stack.addWidget(tela_proc)  # 1
        self.stack.addWidget(tela_tar)  # 2
        self.stack.addWidget(tela_req)  # 3
        self.stack.addWidget(QWidget())  # 4 - Relatórios (Placeholder)
        self.stack.addWidget(QWidget())  # 5 - Agenda (Placeholder)
        self.stack.addWidget(QWidget())  # 6 - Config (Placeholder)
        self.stack.addWidget(tela_cas)  # 7 - Config (Placeholder)

        layout_principal.addWidget(sidebar)
        layout_principal.addWidget(self.stack)

        # Inicia o programa abrindo o Dashboard por padrão
        self.btn_dashboard.setChecked(True)
        self.mudar_tela(0)

    def criar_botao_menu(self, texto):
        btn = QPushButton(texto)
        btn.setProperty("class", "menu-btn")
        btn.setCheckable(True)
        return btn

    def mudar_tela(self, indice):
        self.stack.setCurrentIndex(indice)

        # Atualiza a cor azul de qual aba está selecionada
        botoes = [self.btn_dashboard, self.btn_processos, self.btn_tarefas, self.btn_requerimentos]
        for i, btn in enumerate(botoes):
            btn.setChecked(i == indice)