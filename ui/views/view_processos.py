import os
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QFrame, QScrollArea,
                             QComboBox, QDialog, QMessageBox)
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QCursor, QIcon
from database.conexao import SessionLocal
from database.crud import listar_todos_processos, atualizar_status_processo, listar_documentos_do_processo
from ui.dialogs.form_novo_processo import DialogNovoProcesso
from ui.dialogs.form_detalhes_processo import DialogDetalhesProcesso
from ui.componentes import VisualizadorDocumento


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

        btn_entregue = QPushButton("🟢 Entregar ao Cliente")
        btn_entregue.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_entregue.setStyleSheet(
            "background-color: #27AE60; padding: 12px; font-size: 13px; border-radius: 6px; font-weight: bold;")
        btn_entregue.clicked.connect(lambda: self.escolher("Entregue"))

        btn_cras = QPushButton("🟣 Enviar para o CRAS")
        btn_cras.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_cras.setStyleSheet(
            "background-color: #8E44AD; padding: 12px; font-size: 13px; border-radius: 6px; font-weight: bold;")
        btn_cras.clicked.connect(lambda: self.escolher("CRAS"))

        btn_arquivado = QPushButton("📁 Arquivar no Cartório")
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
        lbl_titulo = QLabel("📂 Central de Processos e Documentos")
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

        # Timer de debounce para não travar a interface a cada letra digitada
        self.timer_busca = QTimer(self)
        self.timer_busca.setSingleShot(True)
        self.timer_busca.setInterval(300)
        self.timer_busca.timeout.connect(self.filtrar_tabela)
        self.input_pesquisa.textChanged.connect(lambda: self.timer_busca.start())

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

        self.docs_por_processo = {}
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
        self.filtrar_tabela()

    def filtrar_tabela(self):
        self.carregando = True
        termo_pesquisa = self.input_pesquisa.text().lower().strip()
        filtro_aba = self.combo_filtro.currentText()
        
        db = SessionLocal()
        try:
            from database.modelos import Processo, Documento
            query = db.query(Processo)
            
            # Aplica os Filtros no Banco de Dados (Velocidade e Memória otimizadas)
            if termo_pesquisa:
                # Busca flexível por ID ou Nome
                if termo_pesquisa.isnumeric() or "2026" in termo_pesquisa:
                    numero = ''.join(filter(str.isdigit, termo_pesquisa))
                    if numero:
                        query = query.filter(Processo.id == int(numero[-4:]))
                else:
                    query = query.filter(Processo.nome_cliente.ilike(f"%{termo_pesquisa}%"))
            else:
                if filtro_aba == "Exibir: Ativos":
                    query = query.filter(~Processo.status.in_(["Arquivado", "CRAS", "Entregue"]))
                elif filtro_aba == "Exibir: Entregues":
                    query = query.filter(Processo.status == "Entregue")
                elif filtro_aba == "Exibir: CRAS":
                    query = query.filter(Processo.status == "CRAS")
                elif filtro_aba == "Exibir: Arquivados":
                    query = query.filter(Processo.status == "Arquivado")
            
            # Limita a 100 resultados recentes para nunca travar a UI (Paginação / Virtualização visual)
            processos_filtrados = query.order_by(Processo.id.desc()).limit(100).all()
            
            # Busca os documentos apenas para os 100 processos que aparecerão na tela
            self.docs_por_processo = {}
            ids_filtrados = [p.id for p in processos_filtrados]
            if ids_filtrados:
                docs = db.query(Documento).filter(Documento.processo_id.in_(ids_filtrados)).all()
                for d in docs:
                    self.docs_por_processo.setdefault(d.processo_id, []).append(d)
                    
            self.renderizar_blocos(processos_filtrados)
        finally:
            db.close()
            self.carregando = False

    def renderizar_blocos(self, processos_filtrados):
        # O BUG ESTAVA AQUI! Limpando os widgets e os espaços (stretches) corretamente:
        while self.layout_blocos.count():
            item = self.layout_blocos.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

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

            try:
                data_formatada = p.data_entrada.strftime("%d/%m/%Y")
            except:
                data_formatada = str(p.data_entrada).split()[0]

            prazo_str = p.data_prazo.strftime("%d/%m/%Y") if p.data_prazo else "Sem prazo"

            origem = getattr(p, 'origem_solicitacao', 'BALCÃO')
            lbl_detalhes = QLabel(f"Proc. 2026.08.{p.id:04d}   |   Origem: {origem}   |   Entrada: {data_formatada}   |   Prazo: {prazo_str}   |   CPF: {p.cpf or '-'}")
            lbl_detalhes.setStyleSheet("color: #8A92A6; font-size: 11px; border: none; background: transparent;")

            info_lay.addWidget(lbl_nome)
            info_lay.addWidget(lbl_detalhes)
            lay_bloco.addLayout(info_lay)
            lay_bloco.addStretch()

            # ---> Documentos Anexados (Centro - Obtidos da memória sem N+1 consultas ao banco)
            docs = self.docs_por_processo.get(p.id, [])

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

        # Adiciona apenas UMA mola no final
        self.layout_blocos.addStretch()

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
        try:
            atualizar_status_processo(db, processo_id, status_final)
        finally:
            db.close()
        # Atualiza a view atual (remove da lista se foi concluído), mas não trava o app inteiro
        QTimer.singleShot(1, self.carregar_dados)

    def abrir_documento(self, caminho):
        if os.path.exists(caminho):
            visualizador = VisualizadorDocumento(caminho, self)
            visualizador.exec()
        else:
            QMessageBox.warning(self, "Erro", "Arquivo não encontrado fisicamente na pasta.")