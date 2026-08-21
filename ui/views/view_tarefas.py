from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel)
from PyQt6.QtCore import Qt
from database.conexao import SessionLocal
from database.crud import listar_todas_tarefas, atualizar_status_tarefa


class TelaTarefas(QWidget):
    def __init__(self):
        super().__init__()

        self.setStyleSheet("""
            QWidget { background-color: #12141c; color: #ffffff; font-family: 'Segoe UI'; }
            QTableWidget {
                background-color: #1e212b; border: none; border-radius: 10px;
                gridline-color: #2c2f3f; font-size: 14px;
            }
            QTableWidget::item { padding: 10px; border-bottom: 1px solid #2c2f3f; }
            QHeaderView::section {
                background-color: #2c2f3f; padding: 5px; font-weight: bold; border: none;
                color: #8a8d98;
            }
            QPushButton {
                background-color: #2962ff; color: white; font-weight: bold;
                border-radius: 6px; padding: 8px 15px; font-size: 13px;
            }
            QPushButton:hover { background-color: #1e4bd8; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- CABEÇALHO ---
        layout_topo = QHBoxLayout()
        titulo = QLabel("Tarefas da Equipe")
        titulo.setStyleSheet("font-size: 22px; font-weight: bold;")

        btn_atualizar = QPushButton("🔄 Atualizar")
        btn_atualizar.setStyleSheet("background-color: #2c2f3f;")
        btn_atualizar.clicked.connect(self.carregar_dados)

        layout_topo.addWidget(titulo)
        layout_topo.addStretch()
        layout_topo.addWidget(btn_atualizar)

        layout.addLayout(layout_topo)
        layout.addSpacing(10)

        # --- TABELA DE TAREFAS ---
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["Concluído", "Descrição da Tarefa", "Status", "Responsável"])

        # Ajusta a largura das colunas
        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0,
                                    QHeaderView.ResizeMode.ResizeToContents)  # Coluna do Checkbox ajusta ao tamanho dele
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Descrição estica para preencher a tela

        layout.addWidget(self.tabela)

        # Quando o usuário clicar no checkbox, o PyQt avisa a nossa função
        self.tabela.itemChanged.connect(self.ao_alterar_checkbox)

        # Variável de segurança para o sistema não salvar no banco enquanto ainda está desenhando a tela
        self.carregando_tela = False

        self.carregar_dados()

    def carregar_dados(self):
        self.carregando_tela = True  # Pausa o salvamento no banco
        self.tabela.setRowCount(0)  # Limpa a tabela

        db = SessionLocal()
        tarefas = listar_todas_tarefas(db)
        db.close()

        self.tabela.setRowCount(len(tarefas))

        for linha, t in enumerate(tarefas):
            # 1. Coluna do Checkbox (Escondendo o ID da tarefa dentro dele para o banco saber quem é)
            item_check = QTableWidgetItem("")
            item_check.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)

            if t.status == "Concluída":
                item_check.setCheckState(Qt.CheckState.Checked)
            else:
                item_check.setCheckState(Qt.CheckState.Unchecked)

            item_check.setData(Qt.ItemDataRole.UserRole, t.id)  # ⬅️ Guardamos o ID secretamente aqui!

            # 2. Descrição
            item_desc = QTableWidgetItem(t.descricao)

            # 3. Status (Visual com cores)
            item_status = QTableWidgetItem(t.status)
            if t.status == "Concluída":
                item_status.setForeground(Qt.GlobalColor.gray)
                item_desc.setForeground(Qt.GlobalColor.gray)  # Deixa o texto cinza se já acabou
            else:
                item_status.setForeground(Qt.GlobalColor.yellow)

            # 4. Responsável
            resp = t.responsavel if t.responsavel else "Não atribuído"
            item_resp = QTableWidgetItem(resp)
            item_resp.setForeground(Qt.GlobalColor.cyan)

            # Adiciona na tabela
            self.tabela.setItem(linha, 0, item_check)
            self.tabela.setItem(linha, 1, item_desc)
            self.tabela.setItem(linha, 2, item_status)
            self.tabela.setItem(linha, 3, item_resp)

        self.carregando_tela = False  # Libera o salvamento no banco

    def ao_alterar_checkbox(self, item):
        # Ignora se estivermos no meio do carregamento da tela
        if self.carregando_tela:
            return

        # O checkbox está sempre na coluna 0. Se clicar em outra, ignoramos.
        if item.column() == 0:
            # Resgata o ID secreto que guardamos
            tarefa_id = item.data(Qt.ItemDataRole.UserRole)

            # Descobre se está marcado ou desmarcado
            esta_concluido = (item.checkState() == Qt.CheckState.Checked)

            # Salva no Banco de Dados
            db = SessionLocal()
            atualizar_status_tarefa(db, tarefa_id, esta_concluido)
            db.close()

            # Recarrega a tela para atualizar as cores
            self.carregar_dados()