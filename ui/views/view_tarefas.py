from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QTableWidget, QTableWidgetItem, QHeaderView, QLabel,
                             QCheckBox)
from PyQt6.QtCore import Qt
from database.conexao import SessionLocal
from database.crud import listar_todas_tarefas, atualizar_status_tarefa


class TelaTarefas(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        titulo = QLabel("Tarefas")
        titulo.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 15px;")
        layout.addWidget(titulo)

        # TABELA COM NOVO ESTILO MODERNO
        self.tabela = QTableWidget()
        self.tabela.setColumnCount(4)
        self.tabela.setHorizontalHeaderLabels(["", "Descrição da Tarefa", "Status", "Responsável"])

        self.tabela.setAlternatingRowColors(True)
        self.tabela.verticalHeader().setDefaultSectionSize(65)
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setShowGrid(False)
        self.tabela.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.tabela.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        header = self.tabela.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Checkbox
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Descrição
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Status

        layout.addWidget(self.tabela)

        self.carregando = False
        self.carregar_dados()

    def carregar_dados(self):
        self.carregando = True
        db = SessionLocal()
        tarefas = listar_todas_tarefas(db)
        db.close()

        self.tabela.setRowCount(len(tarefas))

        for linha, t in enumerate(tarefas):
            # 1. CHECKBOX CENTRALIZADO
            container_check = QWidget()
            layout_check = QHBoxLayout(container_check)
            layout_check.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_check.setContentsMargins(15, 0, 0, 0)

            checkbox = QCheckBox()
            checkbox.setChecked(t.status == "Concluída")
            checkbox.stateChanged.connect(lambda state, tid=t.id: self.ao_alterar_checkbox(tid, state))
            layout_check.addWidget(checkbox)
            self.tabela.setCellWidget(linha, 0, container_check)

            # 2. DESCRIÇÃO
            item_desc = QTableWidgetItem(t.descricao)
            font = item_desc.font()
            font.setBold(True)
            item_desc.setFont(font)
            if t.status == "Concluída":
                item_desc.setForeground(Qt.GlobalColor.gray)
            self.tabela.setItem(linha, 1, item_desc)

            # 3. STATUS (BADGE)
            lbl_status = QLabel(t.status)
            lbl_status.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Mesma regra de CSS das pílulas!
            base_style = "border-radius: 12px; padding: 4px 12px; font-weight: bold; font-size: 11px;"
            if t.status == "Concluída":
                lbl_status.setStyleSheet(base_style + "background-color: rgba(39, 174, 96, 0.15); color: #2ecc71;")
            else:
                lbl_status.setStyleSheet(base_style + "background-color: rgba(241, 196, 15, 0.15); color: #f1c40f;")

            container_status = QWidget()
            layout_status = QHBoxLayout(container_status)
            layout_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout_status.addWidget(lbl_status)
            self.tabela.setCellWidget(linha, 2, container_status)

            # 4. RESPONSÁVEL
            resp = t.responsavel if t.responsavel else "Não atribuído"
            item_resp = QTableWidgetItem(resp)
            item_resp.setForeground(Qt.GlobalColor.gray)
            self.tabela.setItem(linha, 3, item_resp)

        self.carregando = False

    def ao_alterar_checkbox(self, tarefa_id, state):
        if self.carregando: return
        esta_concluido = (state == 2)  # 2 é o valor de Checked no PyQt
        db = SessionLocal()
        atualizar_status_tarefa(db, tarefa_id, esta_concluido)
        db.close()
        self.carregar_dados()  # Recarrega para pintar o texto de cinza e mudar a badge