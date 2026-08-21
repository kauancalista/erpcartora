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
        self.setWindowTitle("Cartório - Tabela de Processos")

        self.setStyleSheet("""
            QWidget { background-color: #12141c; color: #ffffff; font-family: 'Segoe UI'; }
            QTableWidget {
                background-color: #1e212b; border: none; border-radius: 10px;
                gridline-color: #2c2f3f; font-size: 13px;
            }
            QTableWidget::item { padding: 5px; }
            QHeaderView::section {
                background-color: #2c2f3f; padding: 5px; font-weight: bold; border: none; color: #8a8d98;
            }
            QPushButton#btn-novo {
                background-color: #2962ff; color: white; font-weight: bold;
                border-radius: 6px; padding: 10px; font-size: 14px;
            }
            QPushButton#btn-novo:hover { background-color: #1e4bd8; }

            /* O "COMPONENTE VIVO" DO STATUS */
            QComboBox.combo-tabela {
                background-color: #12141c; 
                border: 1px solid #2c2f3f;
                border-radius: 6px; 
                color: white; 
                padding: 4px 8px;
                font-weight: bold;
            }
            /* Brilha ao passar o mouse! */
            QComboBox.combo-tabela:hover {
                border: 1px solid #00f3ff;
                background-color: #1a233a;
            }
            QComboBox.combo-tabela::drop-down { border: none; }

            /* Botão invisível só com o ícone do documento */
            QPushButton.btn-icone {
                background-color: transparent;
                border: none;
                font-size: 20px;
            }
            QPushButton.btn-icone:hover {
                background-color: #2c2f3f;
                border-radius: 4px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        titulo = QLabel("Protocolos / Documentos")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(titulo)

        # BOTOES DO TOPO
        layout_botoes = QHBoxLayout()
        self.btn_carregar = QPushButton("🔄 Atualizar")
        self.btn_carregar.setStyleSheet("background-color: #2c2f3f; color: white; border-radius: 6px; padding: 10px;")
        self.btn_carregar.clicked.connect(self.carregar_dados)

        self.btn_novo = QPushButton("+ Novo Protocolo")
        self.btn_novo.setObjectName("btn-novo")
        self.btn_novo.clicked.connect(self.abrir_formulario)

        layout_botoes.addWidget(self.btn_carregar)
        layout_botoes.addWidget(self.btn_novo)
        layout_botoes.addStretch()
        layout.addLayout(layout_botoes)

        # A NOVA ORDEM DA TABELA! (Documentos no meio)
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(5)
        self.tabela.setHorizontalHeaderLabels(["ID", "Cliente", "Documentos", "Serviço", "Situação"])

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Cliente
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Documentos
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Serviço
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Situação

        self.tabela.itemDoubleClicked.connect(self.abrir_detalhes)
        layout.addWidget(self.tabela)

        self.carregando = False
        self.carregar_dados()

    def abrir_formulario(self):
        janela = DialogNovoProcesso()
        if janela.exec() == QDialog.DialogCode.Accepted:
            self.carregar_dados()

    def abrir_detalhes(self, item):
        linha = item.row()
        processo_id = int(self.tabela.item(linha, 0).text())
        janela_detalhes = DialogDetalhesProcesso(processo_id)
        if janela_detalhes.exec() == QDialog.DialogCode.Accepted:
            self.carregar_dados()

    def carregar_dados(self):
        self.carregando = True
        db = SessionLocal()
        processos = listar_todos_processos(db)

        self.tabela.setRowCount(len(processos))
        for linha, p in enumerate(processos):
            # ID e Nome
            item_id = QTableWidgetItem(str(p.id))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tabela.setItem(linha, 0, item_id)
            self.tabela.setItem(linha, 1, QTableWidgetItem(p.nome_cliente))

            # === COLUNA 2: DOCUMENTOS (Com Ícones Inteligentes) ===
            docs = listar_documentos_do_processo(db, p.id)

            layout_icones = QHBoxLayout()
            layout_icones.setContentsMargins(0, 0, 0, 0)
            layout_icones.setAlignment(Qt.AlignmentFlag.AlignCenter)
            widget_docs = QWidget()

            if docs:
                for doc in docs:
                    # Pega o final do arquivo (ex: "pdf" ou "jpg")
                    extensao = doc.caminho_arquivo.lower().split('.')[-1]
                    caminho_icone = f"assets/icones/{extensao}.png"

                    btn_doc = QPushButton()
                    btn_doc.setProperty("class", "btn-icone")
                    btn_doc.setCursor(Qt.CursorShape.PointingHandCursor)
                    btn_doc.setToolTip(f"Abrir: {doc.nome_arquivo}")

                    # Se o ícone real (.png) existir na pasta, ele usa. Se não, usa um emoji temporário.
                    if os.path.exists(caminho_icone):
                        btn_doc.setIcon(QIcon(caminho_icone))
                        btn_doc.setIconSize(QSize(24, 24))
                    else:
                        if extensao == "pdf":
                            btn_doc.setText("📄")
                        elif extensao in ["jpg", "jpeg", "png"]:
                            btn_doc.setText("🖼️")
                        else:
                            btn_doc.setText("📁")

                    btn_doc.clicked.connect(lambda checked, caminho=doc.caminho_arquivo: self.abrir_documento(caminho))
                    layout_icones.addWidget(btn_doc)
            else:
                lbl_vazio = QLabel("-")
                lbl_vazio.setStyleSheet("color: #8a8d98;")
                layout_icones.addWidget(lbl_vazio)

            widget_docs.setLayout(layout_icones)
            self.tabela.setCellWidget(linha, 2, widget_docs)

            # === COLUNA 3: SERVIÇO ===
            self.tabela.setItem(linha, 3, QTableWidgetItem(p.tipo_servico))

            # === COLUNA 4: SITUAÇÃO (O "Componente Vivo") ===
            combo_status = QComboBox()
            combo_status.setProperty("class", "combo-tabela")
            combo_status.setCursor(Qt.CursorShape.PointingHandCursor)
            combo_status.addItems(["Aguardando Documento", "Em Análise", "Pendente com o Cliente", "🟢 PRONTO"])
            combo_status.setCurrentText(p.status)
            combo_status.currentTextChanged.connect(lambda texto, pid=p.id: self.mudar_status(pid, texto))

            self.tabela.setCellWidget(linha, 4, combo_status)

        db.close()
        self.carregando = False

    def mudar_status(self, processo_id, novo_status):
        if self.carregando: return
        db = SessionLocal()
        atualizar_status_processo(db, processo_id, novo_status)
        db.close()

    def abrir_documento(self, caminho):
        if os.path.exists(caminho):
            os.startfile(caminho)
        else:
            QMessageBox.warning(self, "Erro", "O arquivo físico não foi encontrado no computador.")