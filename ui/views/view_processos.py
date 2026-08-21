import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QDialog, QComboBox, QMessageBox, QLineEdit)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QIcon
from database.conexao import SessionLocal
from database.crud import listar_todos_processos, atualizar_status_processo, listar_documentos_do_processo
from ui.dialogs.form_novo_processo import DialogNovoProcesso
from ui.dialogs.form_detalhes_processo import DialogDetalhesProcesso
from ui.componentes import BarraPesquisa



# =========================================================
# TELA FLUTUANTE DE MIGRAÇÃO
# =========================================================
class DialogMigracao(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Migrar Processo")
        self.setFixedSize(320, 260)
        self.setStyleSheet("background-color: #11151F; color: white; border-radius: 12px;")

        self.destino_escolhido = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl = QLabel("Documento Completo! 🎉\nPara onde deseja migrar?")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 15px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(lbl)

        btn_entregue = QPushButton("✅ Entregar ao Cliente")
        btn_entregue.setStyleSheet("background-color: #27AE60; padding: 12px; font-size: 13px;")
        btn_entregue.clicked.connect(lambda: self.escolher("Entregue"))

        btn_cras = QPushButton("🏢 Enviar para o CRAS")
        btn_cras.setStyleSheet("background-color: #8E44AD; padding: 12px; font-size: 13px;")
        btn_cras.clicked.connect(lambda: self.escolher("CRAS"))

        btn_arquivado = QPushButton("🗄️ Arquivar no Cartório")
        btn_arquivado.setStyleSheet("background-color: #2C364C; padding: 12px; font-size: 13px;")
        btn_arquivado.clicked.connect(lambda: self.escolher("Arquivado"))

        layout.addWidget(btn_entregue)
        layout.addWidget(btn_cras)
        layout.addWidget(btn_arquivado)

    def escolher(self, destino):
        self.destino_escolhido = destino
        self.accept()


# =========================================================
# A TELA PRINCIPAL DE PROCESSOS
# =========================================================
class TelaProcessos(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- CABEÇALHO ---
        layout_topo = QHBoxLayout()
        titulo = QLabel("Documentos / Protocolos")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold;")

        self.input_pesquisa = BarraPesquisa()
        self.input_pesquisa.textChanged.connect(self.filtrar_tabela)

        layout_topo.addWidget(titulo)
        layout_topo.addStretch()
        layout_topo.addWidget(self.input_pesquisa)
        layout.addLayout(layout_topo)
        layout.addSpacing(15)

        # --- BOTÕES E FILTROS ---
        layout_botoes = QHBoxLayout()
        self.btn_carregar = QPushButton("🔄 Atualizar")
        self.btn_carregar.clicked.connect(self.carregar_dados)

        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(
            ["Exibir: Ativos", "Exibir: Todos", "Exibir: Entregues", "Exibir: CRAS", "Exibir: Arquivados"])
        self.combo_filtro.setFixedWidth(180)
        self.combo_filtro.currentTextChanged.connect(self.filtrar_tabela)

        self.btn_novo = QPushButton("+ Novo Documento")
        self.btn_novo.setObjectName("btn-novo")
        self.btn_novo.clicked.connect(self.abrir_formulario)

        layout_botoes.addWidget(self.btn_carregar)
        layout_botoes.addWidget(self.combo_filtro)
        layout_botoes.addStretch()
        layout_botoes.addWidget(self.btn_novo)
        layout.addLayout(layout_botoes)

        # === TABELA RESPONSIVA ===
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Nome / Processo", "Arquivos", "Situação", "Ações"])

        self.tabela.setAlternatingRowColors(True)
        self.tabela.verticalHeader().setDefaultSectionSize(75)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setShowGrid(False)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = self.tabela.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(0, 320)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(1, 120)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        layout.addWidget(self.tabela)

        self.carregando = False
        self.todos_processos = []
        self.carregar_dados()

    def abrir_formulario(self):
        janela = DialogNovoProcesso()
        if janela.exec() == QDialog.DialogCode.Accepted:
            self.carregar_dados()

    def abrir_detalhes(self, processo_id):
        janela_detalhes = DialogDetalhesProcesso(processo_id)
        if janela_detalhes.exec() == QDialog.DialogCode.Accepted:
            self.carregar_dados()

    def carregar_dados(self):
        db = SessionLocal()
        self.todos_processos = listar_todos_processos(db)
        db.close()
        self.filtrar_tabela()

    def filtrar_tabela(self):
        self.carregando = True
        termo_pesquisa = self.input_pesquisa.text().lower().strip()
        filtro_aba = self.combo_filtro.currentText()

        processos_filtrados = []

        for p in self.todos_processos:
            protocolo_str = f"2026.08.{p.id:04d}"

                # --- A MÁGICA DA PESQUISA GLOBAL (Ignora abas se tiver texto) ---
            if termo_pesquisa:
                if termo_pesquisa in p.nome_cliente.lower() or termo_pesquisa in protocolo_str:
                    processos_filtrados.append(p)
                continue  # Achou? Pula as regras de aba e vai pro próximo cliente!

                # --- LÓGICA DAS ABAS (Só roda se a barra de pesquisa estiver vazia) ---
            is_ativo = p.status not in ["Arquivado", "CRAS", "Entregue"]

            if filtro_aba == "Exibir: Ativos" and not is_ativo: continue
            if filtro_aba == "Exibir: Entregues" and p.status != "Entregue": continue
            if filtro_aba == "Exibir: CRAS" and p.status != "CRAS": continue
            if filtro_aba == "Exibir: Arquivados" and p.status != "Arquivado": continue

            processos_filtrados.append(p)


        self.tabela.setRowCount(len(processos_filtrados))
        for linha, p in enumerate(processos_filtrados):

            # 1. NOME / PROCESSO
            container_np = QWidget()
            layout_np = QVBoxLayout(container_np)
            layout_np.setContentsMargins(15, 5, 10, 5)
            layout_np.setSpacing(2)

            lbl_nome = QLabel(p.nome_cliente)
            lbl_nome.setStyleSheet("font-weight: bold; font-size: 14px; color: #E2E8F0;")
            lbl_nome.setWordWrap(True)
            lbl_protocolo = QLabel(f"Proc. 2026.08.{p.id:04d}")
            lbl_protocolo.setStyleSheet("font-size: 11px; color: #8A92A6;")

            layout_np.addWidget(lbl_nome)
            layout_np.addWidget(lbl_protocolo)
            layout_np.setAlignment(Qt.AlignmentFlag.AlignVCenter)
            self.tabela.setCellWidget(linha, 0, container_np)

            # 2. ARQUIVOS
            db = SessionLocal()
            docs = listar_documentos_do_processo(db, p.id)
            db.close()

            container_icones = QWidget()
            layout_icones = QHBoxLayout(container_icones)
            layout_icones.setContentsMargins(15, 0, 0, 0)
            layout_icones.setSpacing(5)
            layout_icones.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

            if docs:
                for doc in docs:
                    extensao = doc.caminho_arquivo.lower().split('.')[-1]
                    caminho_icone = f"assets/icones/{extensao}.png"
                    btn_doc = QPushButton()
                    btn_doc.setProperty("class", "btn-icone")
                    btn_doc.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_doc.setToolTip(f"Abrir: {doc.nome_arquivo}")

                    if os.path.exists(caminho_icone):
                        btn_doc.setIcon(QIcon(caminho_icone))
                        btn_doc.setIconSize(QSize(28, 28))
                    else:
                        btn_doc.setText("📄" if extensao == "pdf" else "🖼️")

                    btn_doc.clicked.connect(lambda checked, caminho=doc.caminho_arquivo: self.abrir_documento(caminho))
                    layout_icones.addWidget(btn_doc)
            else:
                lbl_vazio = QLabel("-")
                lbl_vazio.setStyleSheet("color: #8a8d98;")
                layout_icones.addWidget(lbl_vazio)
            self.tabela.setCellWidget(linha, 1, container_icones)

            # 3. SITUAÇÃO (CAIXA DE SELEÇÃO INTELIGENTE)
            combo_status = QComboBox()
            combo_status.setProperty("class", "combo-tabela")
            combo_status.setCursor(Qt.CursorShape.PointingHandCursor)
            combo_status.setMinimumWidth(180)

            # ====== A LÓGICA DE TRAVA DE SEGURANÇA ======
            status_finais = ["Completo", "Entregue", "CRAS", "Arquivado"]

            if p.status in status_finais:
                # Se já é um status final, mostra as abas finais + botão de emergência
                opcoes = [p.status, "Completo", "Entregue", "CRAS", "Arquivado", "Devolução (Retornar)"]
                # Tira duplicadas mantendo a ordem
                opcoes_limpas = list(dict.fromkeys(opcoes))
                combo_status.addItems(opcoes_limpas)
            else:
                # Se ainda é ativo, esconde as abas finais, permitindo apenas "Completo" para disparar o pop-up
                opcoes = [p.status, "Aguardando Documento", "Falta par", "Revisar", "Pendente", "Completo"]
                opcoes_limpas = list(dict.fromkeys(opcoes))
                combo_status.addItems(opcoes_limpas)

            combo_status.setCurrentText(p.status)
            self.aplicar_cor_status(combo_status, p.status)

            combo_status.currentTextChanged.connect(
                lambda texto, pid=p.id, combo=combo_status: self.mudar_status_logica(pid, texto, combo))

            container_status = QWidget()
            layout_status = QHBoxLayout(container_status)
            layout_status.setContentsMargins(15, 0, 0, 0)
            layout_status.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            layout_status.addWidget(combo_status)
            self.tabela.setCellWidget(linha, 2, container_status)

            # 4. AÇÕES
            container_acao = QWidget()
            layout_acao = QHBoxLayout(container_acao)
            layout_acao.setContentsMargins(0, 0, 15, 0)
            layout_acao.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

            btn_acao = QPushButton("👁️")
            btn_acao.setProperty("class", "btn-icone")
            btn_acao.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_acao.clicked.connect(lambda checked, pid=p.id: self.abrir_detalhes(pid))

            layout_acao.addWidget(btn_acao)
            self.tabela.setCellWidget(linha, 3, container_acao)

        self.carregando = False

    def aplicar_cor_status(self, combo, status):
        base_style = "border-radius: 12px; padding: 6px 12px; font-weight: bold; border: none; outline: none; font-size: 11px;"
        if status == "Completo" or status == "🟢 PRONTO":
            combo.setStyleSheet(base_style + "background-color: rgba(39, 174, 96, 0.15); color: #2ecc71;")
        elif status == "Entregue":
            combo.setStyleSheet(base_style + "background-color: rgba(39, 174, 96, 0.25); color: #27ae60;")
        elif status == "Falta par" or status == "Aguardando Documento":
            combo.setStyleSheet(base_style + "background-color: rgba(231, 76, 60, 0.15); color: #e74c3c;")
        elif status == "Revisar" or status == "Pendente":
            combo.setStyleSheet(base_style + "background-color: rgba(241, 196, 15, 0.15); color: #f1c40f;")
        elif status == "CRAS":
            combo.setStyleSheet(base_style + "background-color: rgba(142, 68, 173, 0.20); color: #9b59b6;")
        elif status == "Arquivado":
            combo.setStyleSheet(base_style + "background-color: rgba(149, 165, 166, 0.15); color: #95a5a6;")
        elif status == "Devolução (Retornar)":
            combo.setStyleSheet(
                base_style + "background-color: rgba(231, 76, 60, 0.35); color: #ff6b6b;")  # Vermelho alerta
        else:
            combo.setStyleSheet(base_style + "background-color: rgba(41, 98, 255, 0.15); color: #2962FF;")

    def mudar_status_logica(self, processo_id, novo_status, combo):
        if self.carregando: return

        # AÇÃO DE EMERGÊNCIA: DEVOLUÇÃO
        if novo_status == "Devolução (Retornar)":
            resposta = QMessageBox.question(self, "Confirmação de Devolução",
                                            "Deseja retornar este documento para a lista de Ativos (Pendente)?\nIsso removerá ele dos arquivados.",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if resposta == QMessageBox.StandardButton.Yes:
                self.salvar_e_recarregar(processo_id, "Pendente")
            else:
                QTimer.singleShot(1, self.carregar_dados)  # Cancela e volta como estava
            return

        # AÇÃO DE MIGRAÇÃO
        if novo_status == "Completo":
            dialog = DialogMigracao(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                status_final = dialog.destino_escolhido
                self.salvar_e_recarregar(processo_id, status_final)
            else:
                self.salvar_e_recarregar(processo_id, "Completo")
        else:
            # Qualquer outro status normal
            self.salvar_e_recarregar(processo_id, novo_status)

    def salvar_e_recarregar(self, processo_id, status_final):
        db = SessionLocal()
        atualizar_status_processo(db, processo_id, status_final)
        db.close()
        QTimer.singleShot(1, self.carregar_dados)

    def abrir_documento(self, caminho):
        if os.path.exists(caminho):
            os.startfile(caminho)
        else:
            QMessageBox.warning(self, "Erro", "Arquivo não encontrado.")