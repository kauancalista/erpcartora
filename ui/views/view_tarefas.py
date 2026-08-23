import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QScrollArea, QGridLayout, QPushButton,
                             QComboBox, QDialog, QLineEdit, QFormLayout, QSizePolicy)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from database.conexao import SessionLocal
from database.modelos import Tarefa, Processo, Casamento
from database.crud import criar_tarefa
from ui.componentes import LabelStatus, notificar


# ==========================================
# COMPONENTE: POP-UP DE NOVA TAREFA MANUAL
# ==========================================
class DialogNovaTarefa(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nova Tarefa")
        self.setFixedSize(400, 300)
        self.setStyleSheet("background-color: #11151F; color: white; border-radius: 8px;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(25, 25, 25, 25)
        layout.setSpacing(15)

        lbl_titulo = QLabel("Adicionar Tarefa Manual")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl_titulo)

        form = QFormLayout()
        form.setSpacing(15)

        estilo_input = "background-color: #0B0E14; padding: 10px; border: 1px solid #1E2532; border-radius: 6px; color: white;"

        self.inp_desc = QLineEdit()
        self.inp_desc.setPlaceholderText("Ex: Comprar papel ofício")
        self.inp_desc.setStyleSheet(estilo_input)

        self.inp_resp = QLineEdit()
        self.inp_resp.setPlaceholderText("Nome do responsável")
        self.inp_resp.setStyleSheet(estilo_input)

        self.inp_data = QLineEdit()
        self.inp_data.setPlaceholderText("DD/MM/AAAA (Prazo)")
        self.inp_data.setStyleSheet(estilo_input)

        form.addRow(QLabel("Descrição:"), self.inp_desc)
        form.addRow(QLabel("Responsável:"), self.inp_resp)
        form.addRow(QLabel("Data Limite:"), self.inp_data)

        layout.addLayout(form)
        layout.addStretch()

        box_botoes = QHBoxLayout()
        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.setStyleSheet(
            "background-color: transparent; border: 1px solid #2C364C; padding: 10px; border-radius: 6px;")
        btn_cancelar.clicked.connect(self.reject)

        btn_salvar = QPushButton("Salvar Tarefa")
        btn_salvar.setStyleSheet("background-color: #2962FF; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_salvar.clicked.connect(self.salvar)

        box_botoes.addWidget(btn_cancelar)
        box_botoes.addWidget(btn_salvar)
        layout.addLayout(box_botoes)

    def salvar(self):
        if not self.inp_desc.text():
            notificar(self, "A descrição é obrigatória!", "erro")
            return

        db = SessionLocal()
        criar_tarefa(
            db,
            descricao=self.inp_desc.text().strip(),
            responsavel=self.inp_resp.text().strip() or "Equipe",
            data_limite=self.inp_data.text().strip() or "Sem prazo"
        )
        db.close()
        self.accept()


# ==========================================
# TELA PRINCIPAL: O HUB DE TAREFAS
# ==========================================
class TelaTarefas(QWidget):
    def __init__(self):
        super().__init__()
        self.lista_todas_tarefas = []

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(0, 0, 0, 0)
        layout_principal.setSpacing(0)

        # --- PAINEL ESQUERDO: LISTA DE CARDS (60%) ---
        self.painel_esq = QWidget()
        self.painel_esq.setStyleSheet("background-color: #0B0E14;")
        layout_esq = QVBoxLayout(self.painel_esq)
        layout_esq.setContentsMargins(30, 30, 20, 30)
        layout_esq.setSpacing(20)

        box_topo = QHBoxLayout()
        box_titulos = QVBoxLayout()
        lbl_titulo = QLabel("Central de Ações e Tarefas")
        lbl_titulo.setStyleSheet("font-size: 26px; font-weight: bold; color: white;")
        lbl_sub = QLabel("Pendências automáticas de processos e casamentos unificadas.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8A92A6;")
        box_titulos.addWidget(lbl_titulo)
        box_titulos.addWidget(lbl_sub)

        box_topo.addLayout(box_titulos)
        box_topo.addStretch()
        layout_esq.addLayout(box_topo)

        # Área de Scroll com os Cards
        scroll_cards = QScrollArea()
        scroll_cards.setWidgetResizable(True)
        scroll_cards.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.container_cards = QWidget()
        self.container_cards.setStyleSheet("background-color: transparent;")
        self.layout_cards = QVBoxLayout(self.container_cards)
        self.layout_cards.setContentsMargins(0, 0, 10, 0)  # Margem pra barra de rolagem não morder o card
        self.layout_cards.setSpacing(15)
        self.layout_cards.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll_cards.setWidget(self.container_cards)
        layout_esq.addWidget(scroll_cards)

        # --- PAINEL DIREITO: FILTROS E AÇÕES (40%) ---
        self.painel_dir = QFrame()
        self.painel_dir.setStyleSheet("background-color: #11151F; border-left: 1px solid #1E2532;")
        layout_dir = QVBoxLayout(self.painel_dir)
        layout_dir.setContentsMargins(25, 30, 25, 30)
        layout_dir.setSpacing(20)

        # Ações Rápidas
        lbl_act = QLabel("Ações Rápidas")
        lbl_act.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout_dir.addWidget(lbl_act)

        box_acoes = QHBoxLayout()
        btn_novo = QPushButton("+ Nova Tarefa Manual")
        btn_novo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_novo.setStyleSheet(
            "background-color: #2962FF; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_novo.clicked.connect(self.abrir_dialog_novo)

        btn_imp = QPushButton("🖨️ Imprimir Pendências")
        btn_imp.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_imp.setStyleSheet(
            "background-color: #151A27; color: white; border: 1px solid #1E2532; padding: 12px; border-radius: 6px;")
        btn_imp.clicked.connect(lambda: notificar(self, "Módulo de impressão será conectado em breve!", "info"))

        box_acoes.addWidget(btn_novo)
        box_acoes.addWidget(btn_imp)
        layout_dir.addLayout(box_acoes)

        # Filtros
        box_filtros = QFrame()
        box_filtros.setStyleSheet(
            "background-color: #151A27; border: 1px solid #1E2532; border-radius: 8px; margin-top: 20px;")
        layout_f = QVBoxLayout(box_filtros)

        lbl_f_tit = QLabel("Filtrar Visão")
        lbl_f_tit.setStyleSheet("font-size: 14px; font-weight: bold; color: white; border: none; margin-bottom: 5px;")
        layout_f.addWidget(lbl_f_tit)

        self.cb_filtro = QComboBox()
        self.cb_filtro.addItems(
            ["Exibir Todas as Tarefas", "Mostrar só Processos", "Mostrar só Casamentos", "Mostrar só Manuais"])
        self.cb_filtro.setStyleSheet(
            "background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; padding: 8px; color: white;")
        self.cb_filtro.currentTextChanged.connect(self.renderizar_cards)
        layout_f.addWidget(self.cb_filtro)
        layout_dir.addWidget(box_filtros)

        # KPIs do Hub
        self.lbl_kpi_proc = QLabel("0")
        self.lbl_kpi_cas = QLabel("0")
        self.lbl_kpi_manuais = QLabel("0")

        grid_kpi = QGridLayout()
        grid_kpi.addWidget(self.criar_kpi_card("Processos", self.lbl_kpi_proc, "#27AE60"), 0, 0)
        grid_kpi.addWidget(self.criar_kpi_card("Casamentos", self.lbl_kpi_cas, "#8E44AD"), 0, 1)
        grid_kpi.addWidget(self.criar_kpi_card("Manuais", self.lbl_kpi_manuais, "#F39C12"), 1, 0, 1, 2)
        layout_dir.addLayout(grid_kpi)

        layout_dir.addStretch()

        # Junta tudo (60 / 40)
        layout_principal.addWidget(self.painel_esq, 6)
        layout_principal.addWidget(self.painel_dir, 4)

        self.carregar_dados_hub()

    # ==========================================
    # CÉREBRO: PUXANDO DAS 3 TABELAS
    # ==========================================
    def carregar_dados_hub(self):
        import json  # Garante a leitura do dicionário do banco
        db = SessionLocal()

        # 1. Puxa Processos (Que não estão concluídos)
        processos = db.query(Processo).filter(Processo.status.notin_(["Concluído", "Arquivado"])).all()

        # 2. Puxa todos os Casamentos Ativos para analisar o Checklist
        casamentos = db.query(Casamento).filter(Casamento.status != "Arquivado").all()

        # 3. Puxa Tarefas Manuais
        tarefas_manuais = db.query(Tarefa).filter(Tarefa.status != "Concluída").all()

        db.close()
        self.lista_todas_tarefas.clear()

        count_proc, count_cas, count_man = 0, 0, 0

        # Formata Processos para o formato do Card
        for p in processos:
            data_str = p.data_entrada if isinstance(p.data_entrada, str) else p.data_entrada.strftime("%d/%m/%Y")
            self.lista_todas_tarefas.append({
                "origem": "Processo", "cor": "#27AE60", "icone": "📄",
                "titulo": f"Andamento de Processo: {p.nome_cliente}",
                "data_texto": f"Entrega: {data_str}", "info_extra": p.tipo_servico,
                "status": p.status
            })
            count_proc += 1

        # LÓGICA REFINADA: Casamentos (Só aciona se faltar a Certidão específica)
        for c in casamentos:
            try:
                # Transforma a string do banco de volta num Dicionário Python
                docs_dict = json.loads(c.docs_entregues) if c.docs_entregues else {}
            except:
                docs_dict = {}

            # Pega o status exato das duas certidões (Se não achar, considera False/Faltando)
            cert_noivo = docs_dict.get("Certidão Noivo (Até 90 dias)", False)
            cert_noiva = docs_dict.get("Certidão Noiva (Até 90 dias)", False)

            # Se AO MENOS UMA estiver faltando (False), cria a Tarefa
            if not cert_noivo or not cert_noiva:
                faltando_cert = []
                if not cert_noivo: faltando_cert.append("Noivo")
                if not cert_noiva: faltando_cert.append("Noiva")

                # Se faltar dos dois, vira "Noivo e Noiva"
                txt_faltando = " e ".join(faltando_cert)

                data_str = c.data_celebracao.strip() if c.data_celebracao else "A definir"
                self.lista_todas_tarefas.append({
                    "origem": "Casamento", "cor": "#8E44AD", "icone": "💍",
                    "titulo": f"Pendência 2ª via Certidão ({txt_faltando}) - {c.nome_noivo} e {c.nome_noiva}",
                    "data_texto": f"Celebração: {data_str}", "info_extra": f"Protocolo: {c.protocolo}",
                    "status": "Aguardando Certidão"
                })
                count_cas += 1

        # Formata Tarefas Manuais
        for t in tarefas_manuais:
            data_str = t.data_criacao if isinstance(t.data_criacao, str) else t.data_criacao.strftime("%d/%m/%Y")
            self.lista_todas_tarefas.append({
                "origem": "Manual", "cor": "#F39C12", "icone": "📋",
                "titulo": t.descricao,
                "data_texto": f"Prazo: {data_str}", "info_extra": f"Responsável: {t.responsavel}",
                "status": t.status
            })
            count_man += 1

        self.lbl_kpi_proc.setText(str(count_proc))
        self.lbl_kpi_cas.setText(str(count_cas))
        self.lbl_kpi_manuais.setText(str(count_man))

        self.renderizar_cards()
    # ==========================================
    # RENDERIZAÇÃO DOS CARDS
    # ==========================================
    def renderizar_cards(self):
        # Limpa tudo
        while self.layout_cards.count():
            item = self.layout_cards.takeAt(0)
            if item.widget(): item.widget().deleteLater()

        filtro = self.cb_filtro.currentText()

        cards_exibidos = 0
        for t in self.lista_todas_tarefas:
            # Aplica o filtro
            if filtro == "Mostrar só Processos" and t["origem"] != "Processo": continue
            if filtro == "Mostrar só Casamentos" and t["origem"] != "Casamento": continue
            if filtro == "Mostrar só Manuais" and t["origem"] != "Manual": continue

            self.criar_card_tarefa(t)
            cards_exibidos += 1

        if cards_exibidos == 0:
            lbl_vazio = QLabel("\n\n✨ Tudo limpo!\nNenhuma tarefa ou pendência no momento.")
            lbl_vazio.setStyleSheet("color: #8A92A6; font-size: 16px;")
            lbl_vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout_cards.addWidget(lbl_vazio)

        self.layout_cards.addStretch()

    def criar_card_tarefa(self, t):
        card = QFrame()
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        card.setStyleSheet(
            f"background-color: #151A27; border: 1px solid #1E2532; border-left: 4px solid {t['cor']}; border-radius: 8px;")

        layout_card = QHBoxLayout(card)
        layout_card.setContentsMargins(15, 15, 15, 15)

        # Bloco de Textos (Esquerda)
        box_textos = QVBoxLayout()

        box_tags = QHBoxLayout()
        lbl_tipo = QLabel(f"{t['icone']} Origem: {t['origem']}")
        lbl_tipo.setStyleSheet(f"color: {t['cor']}; font-size: 11px; font-weight: bold; border: none;")

        badge_status = LabelStatus(t['status'])

        box_tags.addWidget(lbl_tipo)
        box_tags.addStretch()
        box_tags.addWidget(badge_status)
        box_textos.addLayout(box_tags)

        lbl_tit = QLabel(t['titulo'])
        lbl_tit.setStyleSheet("color: white; font-size: 16px; font-weight: bold; margin-top: 5px; border: none;")
        lbl_tit.setWordWrap(True)
        box_textos.addWidget(lbl_tit)

        lbl_sub = QLabel(f"{t['data_texto']}   •   {t['info_extra']}")
        lbl_sub.setStyleSheet("color: #8A92A6; font-size: 13px; border: none;")
        box_textos.addWidget(lbl_sub)

        layout_card.addLayout(box_textos, 8)

        # Botão Clicável (Direita) - Exatamente como você pediu!
        btn_acessar = QPushButton("Abrir Ficha ❯")
        btn_acessar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_acessar.setStyleSheet(
            "background-color: #11151F; color: #E2E8F0; font-weight: bold; padding: 15px 20px; border: 1px solid #1E2532; border-radius: 8px;")
        btn_acessar.clicked.connect(lambda: notificar(self, f"Acessando ficha: {t['origem']}", "info"))

        layout_card.addWidget(btn_acessar, 2)

        self.layout_cards.addWidget(card)

    def abrir_dialog_novo(self):
        dialog = DialogNovaTarefa(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            notificar(self, "Tarefa manual adicionada com sucesso!", "sucesso")
            self.carregar_dados_hub()  # Recarrega a tela lendo o banco de novo

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