from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QFrame, QComboBox, QTextEdit, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from ui.componentes import notificar


class DialogImpressao(QDialog):
    def __init__(self, parent, titulo_doc, conteudo_html):
        super().__init__(parent)
        self.setWindowTitle(f"Módulo de Impressão - {titulo_doc}")
        self.setFixedSize(1000, 700)  # Tela grande para ver o preview direito
        self.setStyleSheet("background-color: #0B0E14; color: white;")

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ==========================================
        # LADO ESQUERDO: CONFIGURAÇÕES E AÇÕES (30%)
        # ==========================================
        painel_esq = QFrame()
        painel_esq.setStyleSheet("background-color: #11151F; border-right: 1px solid #1E2532;")
        painel_esq.setFixedWidth(300)
        layout_esq = QVBoxLayout(painel_esq)
        layout_esq.setContentsMargins(25, 30, 25, 30)
        layout_esq.setSpacing(20)

        lbl_titulo = QLabel("Configurações\nde Impressão")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: white; border: none;")
        layout_esq.addWidget(lbl_titulo)

        lbl_sub = QLabel(f"Documento: {titulo_doc}")
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 13px; border: none; margin-bottom: 20px;")
        lbl_sub.setWordWrap(True)
        layout_esq.addWidget(lbl_sub)

        # Controles
        estilo_combo = "background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; padding: 10px; color: white;"

        layout_esq.addWidget(QLabel("Tamanho do Papel"))
        self.cb_papel = QComboBox()
        self.cb_papel.addItems(["A4 (Padrão)", "Carta", "Ofício"])
        self.cb_papel.setStyleSheet(estilo_combo)
        layout_esq.addWidget(self.cb_papel)

        layout_esq.addWidget(QLabel("Modo de Cor"))
        self.cb_cor = QComboBox()
        self.cb_cor.addItems(["Preto e Branco", "Colorido"])
        self.cb_cor.setStyleSheet(estilo_combo)
        layout_esq.addWidget(self.cb_cor)

        # O botão mágico de Editar
        self.btn_editar = QPushButton("✏️ Habilitar Edição")
        self.btn_editar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_editar.setStyleSheet(
            "background-color: #151A27; color: white; border: 1px solid #1E2532; padding: 12px; border-radius: 6px; font-weight: bold; margin-top: 20px;")
        self.btn_editar.clicked.connect(self.alternar_edicao)
        layout_esq.addWidget(self.btn_editar)

        layout_esq.addStretch()

        # Botões Principais
        btn_imprimir = QPushButton("🖨️ Imprimir Agora")
        btn_imprimir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_imprimir.setStyleSheet(
            "background-color: #2962FF; color: white; padding: 15px; border-radius: 6px; font-weight: bold; font-size: 14px;")
        btn_imprimir.clicked.connect(self.executar_impressao)

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancelar.setStyleSheet(
            "background-color: transparent; color: #8A92A6; border: 1px solid #2C364C; padding: 12px; border-radius: 6px; font-weight: bold;")
        btn_cancelar.clicked.connect(self.reject)

        layout_esq.addWidget(btn_imprimir)
        layout_esq.addWidget(btn_cancelar)

        # ==========================================
        # LADO DIREITO: PREVIEW (FOLHA A4 VIRTUAL)
        # ==========================================
        painel_dir = QFrame()
        painel_dir.setStyleSheet("background-color: #0B0E14;")
        layout_dir = QVBoxLayout(painel_dir)
        layout_dir.setContentsMargins(40, 40, 40, 40)

        # O Documento em si (Branco, como papel)
        self.preview_doc = QTextEdit()
        self.preview_doc.setHtml(conteudo_html)
        self.preview_doc.setReadOnly(True)  # Nasce bloqueado para não estragarem sem querer
        self.preview_doc.setStyleSheet("""
            QTextEdit {
                background-color: white; 
                color: black; 
                padding: 50px; 
                border-radius: 4px;
                font-family: 'Arial';
                font-size: 14px;
            }
        """)

        # Adiciona uma sombrinha pra parecer uma folha de papel flutuando
        efeito_sombra = QFrame()
        efeito_sombra.setStyleSheet("background-color: transparent; border: 1px solid #1E2532;")
        lay_sombra = QVBoxLayout(efeito_sombra)
        lay_sombra.setContentsMargins(0, 0, 0, 0)
        lay_sombra.addWidget(self.preview_doc)

        layout_dir.addWidget(efeito_sombra)

        layout_principal.addWidget(painel_esq)
        layout_principal.addWidget(painel_dir, 1)

    # ==========================================
    # CÉREBRO DA IMPRESSÃO
    # ==========================================
    def alternar_edicao(self):
        # Destrava ou trava a folha A4 virtual para o oficial arrumar textos errados
        if self.preview_doc.isReadOnly():
            self.preview_doc.setReadOnly(False)
            self.preview_doc.setStyleSheet("""
                QTextEdit { background-color: #F8F9FA; color: black; padding: 50px; border: 2px dashed #2962FF; font-family: 'Arial'; font-size: 14px; }
            """)
            self.btn_editar.setText("💾 Travar Edição")
            self.btn_editar.setStyleSheet(
                "background-color: #27AE60; color: white; padding: 12px; border-radius: 6px; font-weight: bold; margin-top: 20px;")
        else:
            self.preview_doc.setReadOnly(True)
            self.preview_doc.setStyleSheet("""
                QTextEdit { background-color: white; color: black; padding: 50px; border-radius: 4px; font-family: 'Arial'; font-size: 14px; }
            """)
            self.btn_editar.setText("✏️ Habilitar Edição")
            self.btn_editar.setStyleSheet(
                "background-color: #151A27; color: white; border: 1px solid #1E2532; padding: 12px; border-radius: 6px; font-weight: bold; margin-top: 20px;")

    def executar_impressao(self):
        # Chama a inteligência de impressão nativa do PyQt ligada aos drivers do Windows
        impressora = QPrinter(QPrinter.PrinterMode.HighResolution)

        # Aplica a cor escolhida
        if self.cb_cor.currentText() == "Colorido":
            impressora.setColorMode(QPrinter.ColorMode.Color)
        else:
            impressora.setColorMode(QPrinter.ColorMode.GrayScale)

        # Abre a caixa de diálogo invisível para selecionar a impressora física real
        dialogo = QPrintDialog(impressora, self)
        if dialogo.exec() == QPrintDialog.DialogCode.Accepted:
            self.preview_doc.print(impressora)
            notificar(self, "Documento enviado para a impressora!", "sucesso")
            self.accept()