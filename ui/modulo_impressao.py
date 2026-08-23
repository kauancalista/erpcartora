import fitz  # PyMuPDF
from PyQt6.QtWidgets import (QDialog, QHBoxLayout, QVBoxLayout, QLabel,
                             QPushButton, QFrame, QScrollArea, QSizePolicy)
from PyQt6.QtCore import Qt, QRect
from PyQt6.QtGui import QCursor, QImage, QPixmap, QPainter
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog

from ui.componentes import notificar


class DialogImpressao(QDialog):
    def __init__(self, parent, titulo_doc, caminho_pdf):
        super().__init__(parent)
        self.caminho_pdf = caminho_pdf
        self.setWindowTitle(f"Visualizador de Impressão - {titulo_doc}")
        self.setFixedSize(1100, 800)  # Tela grande para caber a folha A4 em alta qualidade
        self.setStyleSheet("background-color: #0B0E14; color: white;")

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # ==========================================
        # LADO ESQUERDO: PAINEL DE AÇÕES
        # ==========================================
        painel_esq = QFrame()
        painel_esq.setStyleSheet("background-color: #11151F; border-right: 1px solid #1E2532;")
        painel_esq.setFixedWidth(300)
        layout_esq = QVBoxLayout(painel_esq)
        layout_esq.setContentsMargins(25, 30, 25, 30)
        layout_esq.setSpacing(20)

        lbl_titulo = QLabel("Visualização\nFiel do Documento")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: white; border: none;")
        layout_esq.addWidget(lbl_titulo)

        lbl_sub = QLabel("O documento está bloqueado para edição para garantir a formatação exata do Microsoft Word.")
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 13px; border: none;")
        lbl_sub.setWordWrap(True)
        layout_esq.addWidget(lbl_sub)

        layout_esq.addStretch()

        btn_imprimir = QPushButton("🖨️ Imprimir Documento")
        btn_imprimir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_imprimir.setStyleSheet(
            "background-color: #2962FF; color: white; padding: 15px; border-radius: 6px; font-weight: bold; font-size: 14px;")
        btn_imprimir.clicked.connect(self.executar_impressao)

        btn_cancelar = QPushButton("Voltar")
        btn_cancelar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cancelar.setStyleSheet(
            "background-color: transparent; color: #8A92A6; border: 1px solid #2C364C; padding: 12px; border-radius: 6px; font-weight: bold;")
        btn_cancelar.clicked.connect(self.reject)

        layout_esq.addWidget(btn_imprimir)
        layout_esq.addWidget(btn_cancelar)

        # ==========================================
        # LADO DIREITO: PREVIEW DO PDF
        # ==========================================
        painel_dir = QFrame()
        painel_dir.setStyleSheet("background-color: #0B0E14;")
        layout_dir = QVBoxLayout(painel_dir)
        layout_dir.setContentsMargins(20, 20, 20, 20)

        self.scroll_preview = QScrollArea()
        self.scroll_preview.setWidgetResizable(True)
        self.scroll_preview.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.container_paginas = QWidget()
        self.container_paginas.setStyleSheet("background-color: transparent;")
        self.layout_paginas = QVBoxLayout(self.container_paginas)
        self.layout_paginas.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.layout_paginas.setSpacing(20)

        self.scroll_preview.setWidget(self.container_paginas)
        layout_dir.addWidget(self.scroll_preview)

        layout_principal.addWidget(painel_esq)
        layout_principal.addWidget(painel_dir, 1)

        self.renderizar_pdf()

    def renderizar_pdf(self):
        """Lê o PDF e desenha as páginas na tela como imagens em alta resolução"""
        doc = fitz.open(self.caminho_pdf)
        for page in doc:
            # Multiplica por 2 para ficar com qualidade Retina/HD
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)

            lbl_pagina = QLabel()
            lbl_pagina.setPixmap(QPixmap.fromImage(img))
            lbl_pagina.setStyleSheet("border: 1px solid #1E2532; background-color: white;")

            # Adiciona sombra
            sombra = QFrame()
            sombra.setStyleSheet("background-color: transparent; border-radius: 4px;")
            lay_s = QVBoxLayout(sombra)
            lay_s.setContentsMargins(0, 0, 0, 0)
            lay_s.addWidget(lbl_pagina)

            self.layout_paginas.addWidget(sombra)

    def executar_impressao(self):
        """Envia o PDF desenhado exatamente para a impressora física"""
        impressora = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialogo = QPrintDialog(impressora, self)

        if dialogo.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter()
            painter.begin(impressora)

            doc = fitz.open(self.caminho_pdf)
            rect_impressora = impressora.pageRect(QPrinter.Unit.DevicePixel)

            for i, page in enumerate(doc):
                if i > 0:
                    impressora.newPage()

                # Renderiza página para imagem
                pix = page.get_pixmap(matrix=fitz.Matrix(3, 3))  # Qualidade máxima para impressão
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)

                # Desenha na impressora respeitando a margem do papel
                target_rect = QRect(0, 0, int(rect_impressora.width()), int(rect_impressora.height()))
                painter.drawImage(target_rect, img)

            painter.end()
            notificar(self, "Documento enviado para a impressora com sucesso!", "sucesso")
            self.accept()