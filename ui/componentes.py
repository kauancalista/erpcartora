import os
import fitz
from PyQt6.QtWidgets import QLineEdit, QLabel, QComboBox, QWidget, QHBoxLayout
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QApplication
from PyQt6.QtCore import QPropertyAnimation, QEasingCurve, QTimer, QPoint, QParallelAnimationGroup
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QScrollArea, QWidget)
from PyQt6.QtGui import QPixmap, QImage, QCursor


class BarraPesquisa(QLineEdit):
    """Barra de pesquisa global padronizada"""

    def __init__(self, placeholder="🔍 Buscar por nome, processo...", largura=300):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setFixedWidth(largura)
        self.setProperty("class", "barra-pesquisa")


def obter_estilo_status(status):
    """Motor central de cores de status do sistema inteiro"""
    base_style = "border-radius: 12px; padding: 5px 12px; font-weight: bold; font-size: 11px;"
    status_lower = status.lower()

    if "concluíd" in status_lower or "pronto" in status_lower or "entregue" in status_lower:
        return base_style + "background-color: rgba(46, 204, 113, 0.15); color: #2ecc71;"  # Verde
    elif "aguardando" in status_lower or "revisar" in status_lower:
        return base_style + "background-color: rgba(243, 156, 18, 0.15); color: #f39c12;"  # Laranja / Amarelo
    elif "falta" in status_lower or "atrasad" in status_lower or "pendente" in status_lower:
        return base_style + "background-color: rgba(231, 76, 60, 0.15); color: #e74c3c;"  # Vermelho
    elif "cras" in status_lower:
        return base_style + "background-color: rgba(142, 68, 173, 0.20); color: #9b59b6;"  # Roxo
    elif "arquivad" in status_lower:
        return base_style + "background-color: rgba(149, 165, 166, 0.15); color: #95a5a6;"  # Cinza
    else:
        return base_style + "background-color: rgba(41, 98, 255, 0.15); color: #2962FF;"  # Azul (Em Andamento)


class LabelStatus(QLabel):
    """Pílula Colorida de Status (Para Leitura em Tabelas e Fichas)"""

    def __init__(self, status):
        super().__init__(status)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setStyleSheet(obter_estilo_status(status))


class ComboStatus(QComboBox):
    """Pílula Colorida Interativa (Para Alterar Status)"""

    def __init__(self, opcoes, status_atual):
        super().__init__()
        self.setProperty("class", "combo-tabela")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.addItems(opcoes)
        self.setCurrentText(status_atual)
        self.setStyleSheet(obter_estilo_status(status_atual))
        self.currentTextChanged.connect(self.atualizar_cor)

    def atualizar_cor(self, texto):
        self.setStyleSheet(obter_estilo_status(texto))


def wrap_transparente(widget, alinhamento=Qt.AlignmentFlag.AlignLeft):
    """MÁGICA: Envelopa widgets da tabela para remover o fundo cinza nativo do PyQt6"""
    container = QWidget()
    container.setStyleSheet("background-color: transparent;")
    layout = QHBoxLayout(container)
    layout.setContentsMargins(5, 0, 5, 0)
    layout.setAlignment(alinhamento | Qt.AlignmentFlag.AlignVCenter)
    layout.addWidget(widget)
    return container





class ToastNotification(QFrame):
    """A 'Ilha Dinâmica': Notificação flutuante e animada"""

    def __init__(self, parent, mensagem, tipo="sucesso"):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Cores baseadas no tipo
        if tipo == "sucesso":
            cor_borda = "#27AE60"
            icone = "✅"
        elif tipo == "erro":
            cor_borda = "#E74C3C"
            icone = "❌"
        else:
            cor_borda = "#2962FF"
            icone = "ℹ️"

        self.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(11, 14, 20, 0.95);
                border: 2px solid {cor_borda};
                border-radius: 20px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 10, 20, 10)

        lbl_icone = QLabel(icone)
        lbl_icone.setStyleSheet("font-size: 16px; background: transparent; border: none;")
        lbl_texto = QLabel(mensagem)
        lbl_texto.setStyleSheet(
            "color: white; font-weight: bold; font-size: 14px; background: transparent; border: none;")

        layout.addWidget(lbl_icone)
        layout.addWidget(lbl_texto)

        self.adjustSize()

    def show_toast(self):
        parent_rect = self.parent().rect()
        # Centraliza no topo
        x = int((parent_rect.width() - self.width()) / 2)
        y_start = -self.height() - 10
        y_end = 20  # 20px do topo

        self.setGeometry(x, y_start, self.width(), self.height())
        self.show()
        self.raise_()

        # Animação de descida (Ilha Dinâmica)
        self.anim_in = QPropertyAnimation(self, b"pos")
        self.anim_in.setDuration(600)
        self.anim_in.setStartValue(QPoint(x, y_start))
        self.anim_in.setEndValue(QPoint(x, y_end))
        self.anim_in.setEasingCurve(QEasingCurve.Type.OutBack)  # Efeito de "quique"
        self.anim_in.start()

        # Esconde após 5 segundos
        QTimer.singleShot(5000, self.hide_toast)

    def hide_toast(self):
        x = self.x()
        y_start = self.y()
        y_end = -self.height() - 10

        self.anim_out = QPropertyAnimation(self, b"pos")
        self.anim_out.setDuration(500)
        self.anim_out.setStartValue(QPoint(x, y_start))
        self.anim_out.setEndValue(QPoint(x, y_end))
        self.anim_out.setEasingCurve(QEasingCurve.Type.InBack)
        self.anim_out.finished.connect(self.deleteLater)
        self.anim_out.start()


def notificar(parent, mensagem, tipo="sucesso"):
    """Função global para chamar a Ilha Dinâmica. Destrói a anterior se houver."""
    try:
        janela_principal = parent.window()

        # Se já existe uma notificação, mata ela imediatamente
        if hasattr(janela_principal, "toast_ativo") and getattr(janela_principal, "toast_ativo", None):
            try:
                janela_principal.toast_ativo.hide()
                janela_principal.toast_ativo.deleteLater()
            except:
                pass

        # Cria a nova e salva a referência
        toast = ToastNotification(janela_principal, mensagem, tipo)
        janela_principal.toast_ativo = toast
        toast.show_toast()
    except Exception as e:
        print(f"Erro na notificação: {e}")


# =========================================================
# COMPONENTE: VISUALIZADOR DE DOCUMENTOS (PDF E IMAGENS)
# =========================================================
# =========================================================
# COMPONENTE: VISUALIZADOR DE DOCUMENTOS (AJUSTE AUTOMÁTICO)
# =========================================================
class VisualizadorDocumento(QDialog):
    def __init__(self, caminho_arquivo, parent=None):
        super().__init__(parent)
        self.caminho = caminho_arquivo
        self.pagina_atual = 0
        self.doc_pdf = None

        self.setWindowTitle(f"Pré-visualização: {os.path.basename(caminho_arquivo)}")
        # Tamanho amigável para a janela
        self.resize(850, 700)
        self.setStyleSheet("background-color: #0B0E14; color: white;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)

        # --- BARRA DE CONTROLES NO TOPO ---
        barra_topo = QHBoxLayout()
        self.lbl_info = QLabel("Carregando...")
        self.lbl_info.setStyleSheet("font-weight: bold; font-size: 14px;")

        self.btn_ant = QPushButton("⬅️ Anterior")
        self.btn_ant.clicked.connect(self.pagina_anterior)

        self.btn_prox = QPushButton("Próxima ➡️")
        self.btn_prox.clicked.connect(self.proxima_pagina)

        btn_abrir_os = QPushButton("🪟 Abrir Externamente")
        btn_abrir_os.clicked.connect(lambda: os.startfile(self.caminho))

        for btn in [self.btn_ant, self.btn_prox, btn_abrir_os]:
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.setStyleSheet("background-color: #1A2133; padding: 8px 15px; border-radius: 4px; font-weight: bold;")

        barra_topo.addWidget(self.lbl_info)
        barra_topo.addStretch()
        barra_topo.addWidget(self.btn_ant)
        barra_topo.addWidget(self.btn_prox)
        barra_topo.addSpacing(20)
        barra_topo.addWidget(btn_abrir_os)

        layout.addLayout(barra_topo)

        # --- ÁREA DE IMAGEM ---
        self.scroll = QScrollArea()
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setStyleSheet("border: 1px solid #1E2532; background-color: #05070A; border-radius: 8px;")

        self.lbl_imagem = QLabel()
        self.lbl_imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll.setWidget(self.lbl_imagem)
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)

        self.carregar_documento()

    def aplicar_reducao_para_caber(self, pixmap):
        """O Segredo do Shrink to Fit: Reduz a imagem para caber na janela, mantendo a proporção"""
        # Define um tamanho máximo confortável (pouco menor que a janela)
        largura_maxima = 800
        altura_maxima = 600

        # Escala a imagem mantendo a proporção (KeepAspectRatio) e suavizando os pixels
        pixmap_ajustado = pixmap.scaled(
            largura_maxima, altura_maxima,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        self.lbl_imagem.setPixmap(pixmap_ajustado)

    def carregar_documento(self):
        extensao = self.caminho.lower().split('.')[-1]

        try:
            if extensao == 'pdf':
                self.doc_pdf = fitz.open(self.caminho)
                self.renderizar_pagina_pdf()
            else:
                self.btn_ant.hide()
                self.btn_prox.hide()
                self.lbl_info.setText("Visualizando Imagem")

                # Carrega a foto crua
                pixmap_bruto = QPixmap(self.caminho)
                # Chama a nossa função mágica para amassar ela no tamanho certo
                self.aplicar_reducao_para_caber(pixmap_bruto)

        except Exception as e:
            self.lbl_info.setText("❌ Erro ao carregar arquivo.")
            self.lbl_imagem.setText(str(e))

    def renderizar_pagina_pdf(self):
        if not self.doc_pdf: return

        page = self.doc_pdf[self.pagina_atual]

        # Pega a página do PDF num tamanho generoso (matrix 2.0 garante qualidade)
        pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)

        pixmap_bruto = QPixmap.fromImage(img)

        # Aplica a mesma magia de reduzir para caber na tela
        self.aplicar_reducao_para_caber(pixmap_bruto)

        self.lbl_info.setText(f"Página {self.pagina_atual + 1} de {len(self.doc_pdf)}")

        self.btn_ant.setEnabled(self.pagina_atual > 0)
        self.btn_prox.setEnabled(self.pagina_atual < len(self.doc_pdf) - 1)

    def pagina_anterior(self):
        if self.pagina_atual > 0:
            self.pagina_atual -= 1
            self.renderizar_pagina_pdf()

    def proxima_pagina(self):
        if self.doc_pdf and self.pagina_atual < len(self.doc_pdf) - 1:
            self.pagina_atual += 1
            self.renderizar_pagina_pdf()