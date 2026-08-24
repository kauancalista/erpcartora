import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QFrame, QScrollArea,
                             QComboBox, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QCursor, QIcon

from database.conexao import SessionLocal
from database.crud import listar_todos_processos, atualizar_status_processo, listar_documentos_do_processo
from ui.dialogs.form_novo_processo import DialogNovoProcesso
from ui.dialogs.form_detalhes_processo import DialogDetalhesProcesso


# =========================================================
# TELA FLUTUANTE DE MIGRAÇÃO (Lógica Original Mantida)
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
        btn_entregue.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_entregue.setStyleSheet(
            "background-color: #27AE60; padding: 12px; font-size: 13px; border-radius: 6px; font-weight: bold;")
        btn_entregue.clicked.connect(lambda: self.escolher("Entregue"))

        btn_cras = QPushButton("🏢 Enviar para o CRAS")
        btn_cras.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cras.setStyleSheet(
            "background-color: #8E44AD; padding: 12px; font-size: 13px; border-radius: 6px; font-weight: bold;")
        btn_cras.clicked.connect(lambda: self.escolher("CRAS"))

        btn_arquivado = QPushButton("🗄️ Arquivar no Cartório")
        btn_arquivado.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_arquivado.setStyleSheet(
            "background-color: #2C364C; padding: 12px; font-size: 13px; border-radius: 6px; font-weight: bold;")
        btn_arquivado.clicked.connect(lambda: self.escolher("Arquivado"))

        layout.addWidget(btn_entregue)
        layout.addWidget(btn_cras)
        layout.addWidget(btn_arquivado)

    def escolher(self, destino):
        self.destino_escolhido = destino
        self.accept()


# =========================================================
# A TELA PRINCIPAL (Layout em Blocos + Lógica Avançada)
# =========================================================
class TelaProcessos(QWidget):
    def __init__(self):
        super().__init__()

        self.todos_processos = []
        self.carregando = False

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(20)

        # --- CABEÇALHO ---
        layout_topo = QHBoxLayout()
        box_titulo = QVBoxLayout()
        lbl_titulo = QLabel("📁 Central de Processos e Documentos")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        lbl_sub = QLabel("Gerencie os processos, visualize anexos rápidos e altere o status.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8A92A6;")
        box_titulo.addWidget(lbl_titulo)
        box_titulo.addWidget(lbl_sub)

        self.btn_novo = QPushButton("+ Novo Processo")
        self.btn_novo.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_novo.setStyleSheet(
            "background-color: #27AE60; color: white; font-weight: bold; padding: 12px 20px; border-radius: 6px; font-size: 14px;")
        self.btn_novo.clicked.connect(self.abrir_formulario)

        layout_topo.addLayout(box_titulo)
        layout_topo.addStretch()
        layout_topo.addWidget(self.btn_novo)
        layout_principal.addLayout(layout_topo)

        # --- BARRA DE PESQUISA E FILTROS ---
        painel_filtros = QFrame()
        painel_filtros.setStyleSheet("background-color: #11151F; border-radius: 8px; border: 1px solid #1E2532;")
        layout_filtros = QHBoxLayout(painel_filtros)
        layout_filtros.setContentsMargins(15, 10, 15, 10)
        layout_filtros.setSpacing(15)

        self.btn_atualizar = QPushButton("🔄 Atualizar")
        self.btn_atualizar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_atualizar.setStyleSheet(
            "background-color: #1A2133; color: white; padding: 8px 15px; border-radius: 6px;")
        self.btn_atualizar.clicked.connect(self.carregar_dados)

        self.combo_filtro = QComboBox()
        self.combo_filtro.addItems(
            ["Exibir: Ativos", "Exibir: Todos", "Exibir: Entregues", "Exibir: CRAS", "Exibir: Arquivados"])
        self.combo_filtro.setStyleSheet(
            "background-color: #0B0E14; border: 1px solid #2C364C; border-radius: 6px; color: white; padding: 8px;")
        self.combo_filtro.currentTextChanged.connect(self.filtrar_tabela)

        lbl_icone_busca = QLabel("🔍")
        lbl_icone_busca.setStyleSheet("border: none; font-size: 16px;")

        self.input_pesquisa = QLineEdit()
        self.input_pesquisa.setPlaceholderText("Pesquisar por nome ou protocolo...")
        self.input_pesquisa.setStyleSheet("background-color: transparent; border: none; color: white; font-size: 14px;")
        self.input_pesquisa.textChanged.connect(self.filtrar_tabela)

        layout_filtros.addWidget(self.btn_atualizar)
        layout_filtros.addWidget(self.combo_filtro)
        layout_filtros.addSpacing(20)
        layout_filtros.addWidget(lbl_icone_busca)
        layout_filtros.addWidget(self.input_pesquisa)
        layout_principal.addWidget(painel_filtros)

        # --- ÁREA DE SCROLL PARA OS BLOCOS (CARDS) ---
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        self.container_blocos = QWidget()
        self.container_blocos.setStyleSheet("background-color: transparent;")
        self.layout_blocos = QVBoxLayout(self.container_blocos)
        self.layout_blocos.setSpacing(15)
        self.layout_blocos.setContentsMargins(0, 10, 15, 10)

        self.scroll.setWidget(self.container_blocos)
        layout_principal.addWidget(self.scroll)

        # Inicia o carregamento
        self.carregar_dados()

    # ==========================================
    # LÓGICA DE DADOS E CONSTRUÇÃO DOS BLOCOS
    # ==========================================
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

        # Aplica os filtros da lógica original
        for p in self.todos_processos:
            protocolo_str = f"2026.08.{p.id:04d}"

            if termo_pesquisa:
                if termo_pesquisa in p.nome_cliente.lower() or termo_pesquisa in protocolo_str:
                    processos_filtrados.append(p)
                continue

            is_ativo = p.status not in ["Arquivado", "CRAS", "Entregue"]
            if filtro_aba == "Exibir: Ativos" and not is_ativo: continue
            if filtro_aba == "Exibir: Entregues" and p.status != "Entregue": continue
            if filtro_aba == "Exibir: CRAS" and p.status != "CRAS": continue
            if filtro_aba == "Exibir: Arquivados" and p.status != "Arquivado": continue

            processos_filtrados.append(p)

        self.renderizar_blocos(processos_filtrados)
        self.carregando = False

    def renderizar_blocos(self, processos_filtrados):
        # Limpa os blocos velhos da tela
        for i in reversed(range(self.layout_blocos.count())):
            widget_item = self.layout_blocos.itemAt(i)
            if widget_item.widget():
                widget_item.widget().setParent(None)

        if not processos_filtrados:
            lbl_vazio = QLabel("Nenhum processo encontrado com estes filtros.")
            lbl_vazio.setStyleSheet("color: #8A92A6; font-style: italic;")
            lbl_vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.layout_blocos.addWidget(lbl_vazio)
            self.layout_blocos.addStretch()
            return

        for p in processos_filtrados:
            bloco = QFrame()
            bloco.setStyleSheet("""
                QFrame { background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 10px; }
                QFrame:hover { border: 1px solid #2962FF; background-color: #11151F; }
            """)

            lay_bloco = QHBoxLayout(bloco)
            lay_bloco.setContentsMargins(20, 15, 20, 15)

            # ---> Info Cliente (Esquerda)
            info_lay = QVBoxLayout()
            lbl_nome = QLabel(p.nome_cliente)
            lbl_nome.setStyleSheet(
                "color: white; font-weight: bold; font-size: 15px; border: none; background: transparent;")
            lbl_detalhes = QLabel(f"Proc. 2026.08.{p.id:04d}   |   CPF: {p.cpf or '-'}")
            lbl_detalhes.setStyleSheet("color: #8A92A6; font-size: 11px; border: none; background: transparent;")
            info_lay.addWidget(lbl_nome)
            info_lay.addWidget(lbl_detalhes)
            lay_bloco.addLayout(info_lay)

            lay_bloco.addStretch()

            # ---> Documentos Anexados (Centro)
            db = SessionLocal()
            docs = listar_documentos_do_processo(db, p.id)
            db.close()

            docs_lay = QHBoxLayout()
            docs_lay.setSpacing(5)
            if docs:
                for doc in docs:
                    extensao = doc.caminho_arquivo.lower().split('.')[-1]
                    btn_doc = QPushButton("📄" if extensao == "pdf" else "🖼️")
                    btn_doc.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                    btn_doc.setToolTip(f"Abrir: {doc.nome_arquivo}")
                    btn_doc.setStyleSheet("""
                        QPushButton { background-color: #1A2133; border: 1px solid #2C364C; border-radius: 4px; padding: 6px; font-size: 14px; }
                        QPushButton:hover { background-color: #2962FF; }
                    """)
                    btn_doc.clicked.connect(lambda checked, caminho=doc.caminho_arquivo: self.abrir_documento(caminho))
                    docs_lay.addWidget(btn_doc)
            else:
                lbl_sem_doc = QLabel("Sem anexos")
                lbl_sem_doc.setStyleSheet("color: #4B5563; font-size: 11px; border: none; background: transparent;")
                docs_lay.addWidget(lbl_sem_doc)

            lay_bloco.addLayout(docs_lay)
            lay_bloco.addSpacing(30)

            # ---> Status Interativo (Direita)
            status_finais = ["Completo", "Entregue", "CRAS", "Arquivado"]
            if p.status in status_finais:
                opcoes = [p.status, "Completo", "Entregue", "CRAS", "Arquivado", "Devolução (Retornar)"]
            else:
                opcoes = [p.status, "Aguardando Documento", "Falta par", "Revisar", "Pendente", "Completo"]
            opcoes_limpas = list(dict.fromkeys(opcoes))

            combo_status = QComboBox()
            combo_status.addItems(opcoes_limpas)
            combo_status.setCurrentText(p.status)
            combo_status.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            combo_status.setStyleSheet("""
                QComboBox { background-color: #1A2133; color: white; border: 1px solid #2C364C; border-radius: 6px; padding: 5px 15px; font-weight: bold; }
                QComboBox::drop-down { border: none; }
            """)
            # Conecta a lógica de migração
            combo_status.currentTextChanged.connect(
                lambda texto, pid=p.id, combo=combo_status: self.mudar_status_logica(pid, texto, combo))
            lay_bloco.addWidget(combo_status)

            lay_bloco.addSpacing(15)

            # ---> Botão Abrir Ficha
            btn_acao = QPushButton("👁️ Ficha")
            btn_acao.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn_acao.setStyleSheet(
                "background-color: #2962FF; color: white; border-radius: 6px; padding: 8px 15px; font-weight: bold;")
            btn_acao.clicked.connect(lambda checked, pid=p.id: self.abrir_detalhes(pid))
            lay_bloco.addWidget(btn_acao)

            self.layout_blocos.addWidget(bloco)

        self.layout_blocos.addStretch()

    # ==========================================
    # LÓGICA DE STATUS E MIGRAÇÃO
    # ==========================================
    def mudar_status_logica(self, processo_id, novo_status, combo):
        if self.carregando: return

        if novo_status == "Devolução (Retornar)":
            resposta = QMessageBox.question(self, "Confirmação de Devolução",
                                            "Deseja retornar este documento para a lista de Ativos (Pendente)?\nIsso removerá ele dos arquivados.",
                                            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if resposta == QMessageBox.StandardButton.Yes:
                self.salvar_e_recarregar(processo_id, "Pendente")
            else:
                QTimer.singleShot(1, self.carregar_dados)
            return

        if novo_status == "Completo":
            dialog = DialogMigracao(self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                status_final = dialog.destino_escolhido
                self.salvar_e_recarregar(processo_id, status_final)
            else:
                self.salvar_e_recarregar(processo_id, "Completo")
        else:
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
            QMessageBox.warning(self, "Erro", "Arquivo não encontrado fisicamente na pasta.")