import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QGridLayout, QScrollArea, QListWidget, QListWidgetItem)
from PyQt6.QtCore import Qt, QRectF
from PyQt6.QtGui import QPainter, QColor, QPen, QFont
from database.conexao import SessionLocal
from database.crud import listar_todos_processos, listar_todas_tarefas

from ui.componentes import BarraPesquisa
from ui.dialogs.form_detalhes_processo import DialogDetalhesProcesso


class GraficoCircular(QWidget):
    """Anel de progresso verde neon centralizado cirurgicamente"""

    def __init__(self, percentual=0):
        super().__init__()
        self.percentual = percentual
        self.setFixedSize(140, 140)

    def atualizar_percentual(self, novo_percentual):
        self.percentual = novo_percentual
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(15, 15, 110, 110)

        # Fundo do anel
        pen_fundo = QPen(QColor("#1E2532"), 12)
        painter.setPen(pen_fundo)
        painter.drawArc(rect, 0, 360 * 16)

        # Anel Verde
        pen_verde = QPen(QColor("#00E676"), 12)
        pen_verde.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_verde)

        span_angle = int(-self.percentual * 3.6 * 16)
        painter.drawArc(rect, 90 * 16, span_angle)

        # Textos Centralizados com Caixas Absolutas (Adeus desalinhamento!)
        painter.setPen(QColor("white"))
        font = QFont("Segoe UI", 24, QFont.Weight.Bold)
        painter.setFont(font)
        # Caixa pro número (X:0, Y:40, Largura:140, Altura:35)
        painter.drawText(QRectF(0, 40, 140, 35), Qt.AlignmentFlag.AlignCenter, f"{self.percentual}%")

        painter.setPen(QColor("#8A92A6"))
        font_sub = QFont("Segoe UI", 11)
        painter.setFont(font_sub)
        # Caixa pro subtítulo (Logo abaixo do número)
        painter.drawText(QRectF(0, 75, 140, 25), Qt.AlignmentFlag.AlignCenter, "Concluído")


class TelaDashboard(QWidget):
    def __init__(self):
        super().__init__()

        # --- SCROLL E FUNDO ---
        layout_base = QVBoxLayout(self)
        layout_base.setContentsMargins(0, 0, 0, 0)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: #0B0E14; }")

        self.container = QWidget()
        self.container.setStyleSheet("background-color: #0B0E14;")
        layout_principal = QVBoxLayout(self.container)
        layout_principal.setContentsMargins(40, 40, 40, 40)
        layout_principal.setSpacing(25)

        # ==========================================
        # TOPO: TÍTULO E PESQUISA GLOBAL (CENTRALIZADA)
        # ==========================================
        layout_topo = QHBoxLayout()
        lbl_titulo = QLabel("Dashboard")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
         # lbl_titulo.setFixedWidth(180)  # Trava a largura para equilibrar a balança do layout

        self.input_pesquisa = BarraPesquisa(placeholder="🔍 Pesquisa Global: Buscar processos e tarefas...")
        self.input_pesquisa.setMaximumWidth(550)  # Barra largona e chamativa
        self.input_pesquisa.textChanged.connect(self.pesquisar_global)

        layout_topo.addWidget(lbl_titulo)
        layout_topo.addStretch()
        layout_topo.addWidget(self.input_pesquisa)
        layout_topo.addStretch()
        layout_topo.addSpacing(180)  # Peso invisível na direita para a barra ficar no meio exato

        layout_principal.addLayout(layout_topo)

        # --- O "SPOTLIGHT" (LISTA DE RESULTADOS FLUTUANTE) ---
        self.lista_resultados = QListWidget()
        self.lista_resultados.setStyleSheet("""
            QListWidget { background-color: #151A27; border: 1px solid #2962FF; border-radius: 8px; padding: 5px; color: white; font-size: 14px; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #1E2532; }
            QListWidget::item:hover { background-color: #1A2133; }
        """)
        self.lista_resultados.setMaximumHeight(200)
        self.lista_resultados.hide()  # Fica invisível até você digitar algo
        self.lista_resultados.itemClicked.connect(self.abrir_resultado_pesquisa)

        layout_principal.addWidget(self.lista_resultados)

        # ==========================================
        # LINHA 1: CARDS DE RESUMO (LADO A LADO)
        # ==========================================
        layout_cards = QHBoxLayout()
        layout_cards.setSpacing(25)

        self.lbl_tarefas = QLabel("0")
        self.lbl_pendencias = QLabel("0")
        self.lbl_prazos = QLabel("0")
        self.lbl_docs = QLabel("0")

        layout_cards.addWidget(
            self.criar_card("Tarefas ativas", self.lbl_tarefas, "rgba(41, 98, 255, 0.15)", "#2962FF", "📋"))
        layout_cards.addWidget(
            self.criar_card("Pendências", self.lbl_pendencias, "rgba(231, 76, 60, 0.15)", "#e74c3c", "⚠️"))
        layout_cards.addWidget(
            self.criar_card("Prazos próximos", self.lbl_prazos, "rgba(241, 196, 15, 0.15)", "#f1c40f", "⏳"))
        layout_cards.addWidget(
            self.criar_card("Documentos totais", self.lbl_docs, "rgba(39, 174, 96, 0.15)", "#2ecc71", "📄"))

        layout_principal.addLayout(layout_cards)

        # ==========================================
        # LINHA 2: GRID DE MÓDULOS (2x2)
        # ==========================================
        grid = QGridLayout()
        grid.setSpacing(25)

        card_pend, self.layout_pend = self.criar_card_modulo()
        self.layout_pend.addWidget(self.criar_titulo_modulo("Pendências", "Documentos travados"))
        self.container_lista_pend = QVBoxLayout()
        self.layout_pend.addLayout(self.container_lista_pend)
        self.layout_pend.addStretch()
        grid.addWidget(card_pend, 0, 0)

        card_grafico, layout_grafico = self.criar_card_modulo()
        layout_grafico.addWidget(self.criar_titulo_modulo("Produtividade Geral", "Baseado em Status"))
        container_circulo = QHBoxLayout()
        container_circulo.addStretch()
        self.grafico = GraficoCircular(0)
        container_circulo.addWidget(self.grafico)
        container_circulo.addStretch()
        layout_grafico.addLayout(container_circulo)
        layout_grafico.addStretch()
        grid.addWidget(card_grafico, 0, 1)

        card_recentes, self.layout_recentes = self.criar_card_modulo()
        self.layout_recentes.addWidget(self.criar_titulo_modulo("Processos Recentes", "Últimos cadastrados"))
        self.container_lista_recentes = QVBoxLayout()
        self.layout_recentes.addLayout(self.container_lista_recentes)
        self.layout_recentes.addStretch()
        grid.addWidget(card_recentes, 1, 0)

        card_prazos, self.layout_prazos = self.criar_card_modulo()
        self.layout_prazos.addWidget(self.criar_titulo_modulo("Próximas Tarefas", "Demandas do cartório"))
        self.container_lista_prazos = QVBoxLayout()
        self.layout_prazos.addLayout(self.container_lista_prazos)
        self.layout_prazos.addStretch()
        grid.addWidget(card_prazos, 1, 1)

        layout_principal.addLayout(grid)
        self.scroll.setWidget(self.container)
        layout_base.addWidget(self.scroll)

        # Carrega a Dashboard inteira
        self.carregar_dados_reais()

    # ==========================================
    # FUNÇÕES DE CONSTRUÇÃO DE UI
    # ==========================================
    def criar_card_modulo(self):
        card = QFrame()
        card.setProperty("class", "card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(15)
        return card, layout

    def criar_card(self, titulo, label_numero, cor_fundo, cor_icone, icone):
        """Card redesenhado: Número e Título agora moram lado a lado"""
        card = QFrame()
        card.setProperty("class", "card")
        layout = QHBoxLayout(card)
        layout.setContentsMargins(25, 20, 25, 20)

        frame_icone = QFrame()
        frame_icone.setFixedSize(54, 54)
        frame_icone.setStyleSheet(f"background-color: {cor_fundo}; border-radius: 12px;")
        layout_ic = QVBoxLayout(frame_icone)
        layout_ic.setContentsMargins(0, 0, 0, 0)
        lbl_ic = QLabel(icone)
        lbl_ic.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_ic.setStyleSheet(f"font-size: 24px; color: {cor_icone}; background: transparent;")
        layout_ic.addWidget(lbl_ic)

        # AQUI FOI A MUDANÇA: QHBoxLayout para colocar número e texto na mesma linha
        layout_txt = QHBoxLayout()
        layout_txt.setSpacing(12)

        label_numero.setStyleSheet("font-size: 26px; font-weight: bold; background: transparent;")
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("font-size: 14px; color: #8A92A6; font-weight: bold; background: transparent;")
        lbl_tit.setWordWrap(True)

        layout_txt.addWidget(label_numero)
        layout_txt.addWidget(lbl_tit)
        layout_txt.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(frame_icone)
        layout.addLayout(layout_txt)
        layout.addStretch()
        return card

    def criar_titulo_modulo(self, titulo, subtitulo=None):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 10)
        lbl_tit = QLabel(titulo)
        lbl_tit.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background: transparent;")
        layout.addWidget(lbl_tit)
        if subtitulo:
            lbl_sub = QLabel(subtitulo)
            lbl_sub.setStyleSheet("font-size: 13px; color: #8A92A6; background: transparent;")
            layout.addWidget(lbl_sub)
        return container

    def criar_linha_lista(self, icone, texto, info_direita):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 8)
        lbl_ic = QLabel(icone)
        lbl_ic.setFixedWidth(25)
        lbl_txt = QLabel(texto)
        lbl_txt.setStyleSheet("color: #E2E8F0; font-size: 13px;")
        lbl_txt.setWordWrap(True)
        lbl_dir = QLabel(info_direita)
        lbl_dir.setStyleSheet("color: #8A92A6; font-size: 12px; font-weight: bold;")
        layout.addWidget(lbl_ic)
        layout.addWidget(lbl_txt, 1)
        layout.addWidget(lbl_dir)
        return container

    def criar_linha_prazo(self, id_tarefa, icone, texto, responsavel):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 8)

        frame_data = QFrame()
        frame_data.setFixedSize(50, 55)
        frame_data.setStyleSheet("background-color: #1E2532; border-radius: 8px;")
        layout_data = QVBoxLayout(frame_data)
        layout_data.setSpacing(0)

        lbl_dia = QLabel(f"{id_tarefa:02d}")
        lbl_dia.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        lbl_dia.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_mes = QLabel(icone)
        lbl_mes.setStyleSheet("font-size: 11px; color: #8A92A6; font-weight: bold;")
        lbl_mes.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout_data.addWidget(lbl_dia)
        layout_data.addWidget(lbl_mes)

        layout_txt = QVBoxLayout()
        lbl_txt = QLabel(texto)
        lbl_txt.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold;")
        lbl_txt.setWordWrap(True)
        resp = responsavel if responsavel else "Sem responsável"
        lbl_sub = QLabel(f"Resp: {resp}")
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 12px;")

        layout_txt.addWidget(lbl_txt)
        layout_txt.addWidget(lbl_sub)

        layout.addWidget(frame_data)
        layout.addLayout(layout_txt, 1)
        return container

    # ==========================================
    # LÓGICA DO NOVO MOTOR DE PESQUISA GLOBAL
    # ==========================================
    def pesquisar_global(self):
        """Ao digitar na barra, abre a lista de resultados em tempo real"""
        termo = self.input_pesquisa.text().lower().strip()
        self.lista_resultados.clear()

        if not termo:
            self.lista_resultados.hide()
            return

        db = SessionLocal()
        processos = listar_todos_processos(db)
        tarefas = listar_todas_tarefas(db)
        db.close()

        resultados_encontrados = 0

        for p in processos:
            protocolo_str = f"2026.08.{p.id:04d}"
            if termo in p.nome_cliente.lower() or termo in protocolo_str:
                item = QListWidgetItem(f"📄 PROCESSO: {p.nome_cliente} ({protocolo_str})")
                item.setData(Qt.ItemDataRole.UserRole, ("processo", p.id))
                self.lista_resultados.addItem(item)
                resultados_encontrados += 1

        for t in tarefas:
            if termo in t.descricao.lower() or (t.responsavel and termo in t.responsavel.lower()):
                item = QListWidgetItem(f"📋 TAREFA: {t.descricao}")
                item.setData(Qt.ItemDataRole.UserRole, ("tarefa", t.id))
                self.lista_resultados.addItem(item)
                resultados_encontrados += 1

        if resultados_encontrados > 0:
            self.lista_resultados.show()
        else:
            item = QListWidgetItem("Nenhum resultado encontrado para esta busca...")
            item.setFlags(Qt.ItemFlag.NoItemFlags)  # Desativa o clique
            self.lista_resultados.addItem(item)
            self.lista_resultados.show()

    def abrir_resultado_pesquisa(self, item):
        """Dispara ao clicar em um item da lista flutuante"""
        dados = item.data(Qt.ItemDataRole.UserRole)
        if not dados: return

        tipo, item_id = dados
        if tipo == "processo":
            janela = DialogDetalhesProcesso(item_id)
            janela.exec()

        # Limpa e esconde a barra depois de abrir o detalhe
        self.input_pesquisa.clear()
        self.carregar_dados_reais()

    # ==========================================
    # CARREGAMENTO DO DASHBOARD
    # ==========================================
    def carregar_dados_reais(self):
        db = SessionLocal()
        processos = listar_todos_processos(db)
        tarefas = listar_todas_tarefas(db)
        db.close()

        total_docs = len(processos)
        self.lbl_docs.setText(str(total_docs))

        status_pendentes = ["Aguardando Documento", "Falta par", "Pendente", "Revisar"]
        self.lbl_pendencias.setText(str(sum(1 for p in processos if p.status in status_pendentes)))

        tarefas_pendentes = [t for t in tarefas if t.status != "Concluída"]
        self.lbl_tarefas.setText(str(len(tarefas_pendentes)))
        self.lbl_prazos.setText(str(len(tarefas_pendentes)))

        # Gráfico
        if total_docs > 0:
            finalizados = sum(1 for p in processos if p.status in ["Completo", "Entregue", "Arquivado", "CRAS"])
            self.grafico.atualizar_percentual(int((finalizados / total_docs) * 100))
        else:
            self.grafico.atualizar_percentual(0)

        # Pendências
        self.limpar_layout(self.container_lista_pend)
        lista_pend = [p for p in processos if p.status in status_pendentes]
        if not lista_pend:
            self.container_lista_pend.addWidget(QLabel("Tudo limpo! Sem pendências. 🎉"))
        else:
            for p in lista_pend[:4]:
                self.container_lista_pend.addWidget(self.criar_linha_lista("🔴", p.nome_cliente, p.status))

        # Recentes
        self.limpar_layout(self.container_lista_recentes)
        recentes = processos[-4:]
        recentes.reverse()
        if not recentes:
            self.container_lista_recentes.addWidget(QLabel("Nenhum processo listado."))
        else:
            for p in recentes:
                self.container_lista_recentes.addWidget(
                    self.criar_linha_lista("📄", p.nome_cliente, f"Proc. {p.id:03d}"))

        # Tarefas
        self.limpar_layout(self.container_lista_prazos)
        if not tarefas_pendentes:
            self.container_lista_prazos.addWidget(QLabel("Nenhuma tarefa ativa. Tudo tranquilo!"))
        else:
            for t in tarefas_pendentes[:3]:
                self.container_lista_prazos.addWidget(self.criar_linha_prazo(t.id, "TAR", t.descricao, t.responsavel))

    def limpar_layout(self, layout):
        for i in reversed(range(layout.count())):
            widget = layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()