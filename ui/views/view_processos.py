import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QDialog, QComboBox, QMessageBox)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from database.conexao import SessionLocal
from database.crud import listar_todos_processos, atualizar_status_processo, listar_documentos_do_processo
from ui.dialogs.form_novo_processo import DialogNovoProcesso
from ui.dialogs.form_detalhes_processo import DialogDetalhesProcesso


class TelaProcessos(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        titulo = QLabel("Documentos / Protocolos")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(titulo)

        layout_botoes = QHBoxLayout()
        self.btn_carregar = QPushButton("🔄 Atualizar")
        self.btn_carregar.clicked.connect(self.carregar_dados)

        self.btn_novo = QPushButton("+ Novo Documento")
        self.btn_novo.setObjectName("btn-novo")
        self.btn_novo.clicked.connect(self.abrir_formulario)

        layout_botoes.addWidget(self.btn_carregar)
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

        # ALINHAMENTO DO CABEÇALHO (Tudo à esquerda para não ficar torto)
        header = self.tabela.horizontalHeader()
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)

        # === MÁGICA DA LARGURA DAS COLUNAS ===
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(0, 320)  # 1. Trava o Nome em 320px (Impede ele de engolir a tela)

        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        self.tabela.setColumnWidth(1, 120)  # 2. Arquivos fica coladinho no Nome com 120px

        header.setSectionResizeMode(2,
                                    QHeaderView.ResizeMode.Stretch)  # 3. Situação estica para preencher o vazio. Isso impede o texto de cortar!

        header.setSectionResizeMode(3,
                                    QHeaderView.ResizeMode.ResizeToContents)  # 4. Ações fica enxuto no cantinho direito

        layout.addWidget(self.tabela)

        self.carregando = False
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
        self.carregando = True
        db = SessionLocal()
        processos = listar_todos_processos(db)

        self.tabela.setRowCount(len(processos))
        for linha, p in enumerate(processos):

            # --- 1. NOME / PROCESSO ---
            container_np = QWidget()
            layout_np = QVBoxLayout(container_np)
            layout_np.setContentsMargins(15, 5, 10, 5)  # Margem alinhada com o cabeçalho
            layout_np.setSpacing(2)

            lbl_nome = QLabel(p.nome_cliente)
            lbl_nome.setStyleSheet("font-weight: bold; font-size: 14px; color: #E2E8F0;")
            lbl_nome.setWordWrap(True)  # Quebra linha se o nome for gigante

            lbl_protocolo = QLabel(f"Proc. 2026.08.{p.id:04d}")
            lbl_protocolo.setStyleSheet("font-size: 11px; color: #8A92A6;")

            layout_np.addWidget(lbl_nome)
            layout_np.addWidget(lbl_protocolo)
            layout_np.setAlignment(Qt.AlignmentFlag.AlignVCenter)

            self.tabela.setCellWidget(linha, 0, container_np)

            # --- 2. ARQUIVOS (Alinhado à esquerda para grudar no Nome) ---
            docs = listar_documentos_do_processo(db, p.id)
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

            # --- 3. SITUAÇÃO ---
            combo_status = QComboBox()
            combo_status.setProperty("class", "combo-tabela")
            combo_status.setCursor(Qt.CursorShape.PointingHandCursor)
            combo_status.setMinimumWidth(180)  # Trava o tamanho mínimo para nunca cortar o texto

            combo_status.addItems(["Aguardando Documento", "Falta par", "Revisar", "Completo", "Pendente"])
            combo_status.setCurrentText(p.status)

            self.aplicar_cor_status(combo_status, p.status)
            combo_status.currentTextChanged.connect(
                lambda texto, pid=p.id, combo=combo_status: self.mudar_status_e_cor(pid, texto, combo))

            container_status = QWidget()
            layout_status = QHBoxLayout(container_status)
            layout_status.setContentsMargins(15, 0, 0, 0)
            layout_status.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            layout_status.addWidget(combo_status)

            self.tabela.setCellWidget(linha, 2, container_status)

            # --- 4. AÇÕES (BOTÃO VISUALIZAR) ---
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

        db.close()
        self.carregando = False

    def aplicar_cor_status(self, combo, status):
        base_style = "border-radius: 12px; padding: 6px 12px; font-weight: bold; border: none; outline: none; font-size: 11px;"
        if status == "Completo" or status == "🟢 PRONTO":
            combo.setStyleSheet(base_style + "background-color: rgba(39, 174, 96, 0.15); color: #2ecc71;")
        elif status == "Falta par" or status == "Aguardando Documento":
            combo.setStyleSheet(base_style + "background-color: rgba(231, 76, 60, 0.15); color: #e74c3c;")
        elif status == "Revisar" or status == "Pendente":
            combo.setStyleSheet(base_style + "background-color: rgba(241, 196, 15, 0.15); color: #f1c40f;")
        else:
            combo.setStyleSheet(base_style + "background-color: rgba(41, 98, 255, 0.15); color: #2962FF;")

    def mudar_status_e_cor(self, processo_id, novo_status, combo):
        if self.carregando: return
        self.aplicar_cor_status(combo, novo_status)
        db = SessionLocal()
        atualizar_status_processo(db, processo_id, novo_status)
        db.close()

    def abrir_documento(self, caminho):
        if os.path.exists(caminho):
            os.startfile(caminho)
        else:
            QMessageBox.warning(self, "Erro", "Arquivo não encontrado.")