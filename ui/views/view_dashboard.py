# ui/views/view_dashboard.py
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame)
from PyQt6.QtCore import Qt
from database.conexao import SessionLocal
from database.crud import obter_estatisticas_dashboard


class TelaDashboard(QWidget):
    def __init__(self):
        super().__init__()


        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_titulo = QLabel("Dashboard")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(lbl_titulo)

        layout_cards = QHBoxLayout()
        layout_cards.setSpacing(20)

        db = SessionLocal()
        stats = obter_estatisticas_dashboard(db)
        db.close()

        card1 = self.criar_card("card-vermelho", "⏳ Tarefas Pendentes", str(stats["tarefas_pendentes"]))
        card2 = self.criar_card("card-azul", "📂 Total de Processos", str(stats["processos"]))
        card3 = self.criar_card("card-verde", "📄 Documentos Arquivados", str(stats["documentos"]))

        layout_cards.addWidget(card1)
        layout_cards.addWidget(card2)
        layout_cards.addWidget(card3)
        layout_cards.addStretch()

        layout.addLayout(layout_cards)

        layout.addSpacing(40)
        lbl_mensagem = QLabel(
            "🚀 Bem-vindo ao sistema! Você está no controle.\n\n(No futuro, adicionaremos gráficos de produtividade aqui.)")
        lbl_mensagem.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        lbl_mensagem.setStyleSheet("color: #4a4d5e; font-size: 18px;")
        layout.addWidget(lbl_mensagem)

        layout.addStretch()

    def criar_card(self, classe_css, titulo, valor):
        card = QFrame()
        card.setProperty("class", f"card {classe_css}")
        card.setFixedSize(220, 130)
        card.setCursor(Qt.CursorShape.PointingHandCursor)

        card.mousePressEvent = lambda event: print(f"Você clicou no card: {titulo}")

        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 20, 20, 20)

        # AQUI ESTÁ A CORREÇÃO: Criamos o texto primeiro, aplicamos o CSS na linha de baixo
        lbl_titulo = QLabel(titulo)
        lbl_titulo.setProperty("class", "titulo-card")

        lbl_valor = QLabel(valor)
        lbl_valor.setProperty("class", "numero")

        layout.addWidget(lbl_titulo)
        layout.addWidget(lbl_valor)
        layout.addStretch()

        return card


