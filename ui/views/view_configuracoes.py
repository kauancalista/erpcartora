import os
import json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QLineEdit, QFileDialog,
                             QMessageBox, QTextEdit, QScrollArea)
from PyQt6.QtCore import Qt


class TelaConfiguracoes(QWidget):
    def __init__(self):
        super().__init__()

        # Caminhos dos arquivos de configuração
        self.caminho_config_app = os.path.join(os.getcwd(), "config", "app_config.json")
        self.caminho_modelos = os.path.join(os.getcwd(), "config", "modelos_requerimentos.json")

        self.garantir_arquivos_existem()

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(20)

        # --- CABEÇALHO ---
        layout_topo = QVBoxLayout()
        lbl_titulo = QLabel("⚙️ Configurações do Sistema")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        lbl_sub = QLabel("Gerencie os diretórios do cartório e as estruturas de documentos.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8A92A6;")
        layout_topo.addWidget(lbl_titulo)
        layout_topo.addWidget(lbl_sub)
        layout_principal.addLayout(layout_topo)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")

        container = QWidget()
        container.setStyleSheet("background-color: transparent;")
        layout_scroll = QVBoxLayout(container)
        layout_scroll.setContentsMargins(0, 0, 15, 0)
        layout_scroll.setSpacing(25)

        # ==========================================
        # BLOCO 1: DIRETÓRIOS DO SISTEMA
        # ==========================================
        painel_dirs = QFrame()
        painel_dirs.setProperty("class", "painel")
        layout_dirs = QVBoxLayout(painel_dirs)
        layout_dirs.setContentsMargins(25, 25, 25, 25)
        layout_dirs.setSpacing(15)

        lbl_tit_dirs = QLabel("📁 Diretórios e Pastas Base")
        lbl_tit_dirs.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout_dirs.addWidget(lbl_tit_dirs)

        # Pasta do Scanner
        layout_dirs.addWidget(self.criar_label("Pasta de Entrada do Scanner (Onde as fotos caem):"))
        box_scanner = QHBoxLayout()
        self.inp_scanner = QLineEdit()
        self.inp_scanner.setReadOnly(True)
        self.inp_scanner.setStyleSheet(
            "background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; color: white; padding: 10px;")
        btn_scanner = QPushButton("Procurar")
        btn_scanner.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_scanner.setStyleSheet(
            "background-color: #1A2133; color: white; border: 1px solid #2C364C; padding: 10px; border-radius: 6px;")
        btn_scanner.clicked.connect(lambda: self.selecionar_pasta(self.inp_scanner))
        box_scanner.addWidget(self.inp_scanner)
        box_scanner.addWidget(btn_scanner)
        layout_dirs.addLayout(box_scanner)

        # Pasta dos Processos
        layout_dirs.addWidget(self.criar_label("Pasta Raiz dos Processos (Onde o ERP cria as subpastas):"))
        box_processos = QHBoxLayout()
        self.inp_processos = QLineEdit()
        self.inp_processos.setReadOnly(True)
        self.inp_processos.setStyleSheet(
            "background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; color: white; padding: 10px;")
        btn_processos = QPushButton("Procurar")
        btn_processos.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_processos.setStyleSheet(
            "background-color: #1A2133; color: white; border: 1px solid #2C364C; padding: 10px; border-radius: 6px;")
        btn_processos.clicked.connect(lambda: self.selecionar_pasta(self.inp_processos))
        box_processos.addWidget(self.inp_processos)
        box_processos.addWidget(btn_processos)
        layout_dirs.addLayout(box_processos)

        # NOVA PASTA: Relatórios / FERC
        layout_dirs.addWidget(self.criar_label("Pasta Raiz de Auditoria e Relatórios (FERC / CRAS):"))
        box_ferc = QHBoxLayout()
        self.inp_ferc = QLineEdit()
        self.inp_ferc.setReadOnly(True)
        self.inp_ferc.setStyleSheet(
            "background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; color: white; padding: 10px;")
        btn_ferc = QPushButton("Procurar")
        btn_ferc.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_ferc.setStyleSheet(
            "background-color: #1A2133; color: white; border: 1px solid #2C364C; padding: 10px; border-radius: 6px;")
        btn_ferc.clicked.connect(lambda: self.selecionar_pasta(self.inp_ferc))
        box_ferc.addWidget(self.inp_ferc)
        box_ferc.addWidget(btn_ferc)
        layout_dirs.addLayout(box_ferc)

        btn_salvar_dirs = QPushButton("💾 Salvar Diretórios")
        btn_salvar_dirs.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salvar_dirs.setStyleSheet(
            "background-color: #2962FF; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_salvar_dirs.clicked.connect(self.salvar_diretorios)

        box_btn_dirs = QHBoxLayout()
        box_btn_dirs.addStretch()
        box_btn_dirs.addWidget(btn_salvar_dirs)
        layout_dirs.addLayout(box_btn_dirs)

        layout_scroll.addWidget(painel_dirs)

        # ==========================================
        # BLOCO 2: EDITOR DE MODELOS (JSON)
        # ==========================================
        painel_json = QFrame()
        painel_json.setProperty("class", "painel")
        layout_json = QVBoxLayout(painel_json)
        layout_json.setContentsMargins(25, 25, 25, 25)
        layout_json.setSpacing(15)

        lbl_tit_json = QLabel("🛠️ Editor de Modelos de Requerimento (Avançado)")
        lbl_tit_json.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        lbl_sub_json = QLabel("Edite a estrutura dos requerimentos. Cuidado com vírgulas e aspas!")
        lbl_sub_json.setStyleSheet("font-size: 12px; color: #8A92A6; margin-bottom: 5px;")
        layout_json.addWidget(lbl_tit_json)
        layout_json.addWidget(lbl_sub_json)

        self.editor_json = QTextEdit()
        self.editor_json.setStyleSheet("""
            QTextEdit {
                background-color: #05070A; border: 1px solid #1E2532; border-radius: 6px;
                color: #A9CCE3; padding: 15px; font-family: 'Consolas', 'Courier New', monospace; font-size: 13px;
            }
            QTextEdit:focus { border: 1px solid #E67E22; }
        """)
        self.editor_json.setMinimumHeight(400)
        layout_json.addWidget(self.editor_json)

        btn_salvar_json = QPushButton("💾 Validar e Salvar Modelos")
        btn_salvar_json.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_salvar_json.setStyleSheet(
            "background-color: #E67E22; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_salvar_json.clicked.connect(self.salvar_modelos)

        box_btn_json = QHBoxLayout()
        box_btn_json.addStretch()
        box_btn_json.addWidget(btn_salvar_json)
        layout_json.addLayout(box_btn_json)

        layout_scroll.addWidget(painel_json)

        layout_scroll.addStretch()
        scroll.setWidget(container)
        layout_principal.addWidget(scroll)

        self.carregar_dados_na_tela()

    # ==========================================
    # CÉREBRO: LÓGICA DE ARQUIVOS E SALVAMENTO
    # ==========================================
    def garantir_arquivos_existem(self):
        """Cria o config base se for a primeira vez rodando"""
        if not os.path.exists("config"):
            os.makedirs("config")

        if not os.path.exists(self.caminho_config_app):
            padrao = {"pasta_scanner": "", "pasta_processos": ""}
            with open(self.caminho_config_app, "w", encoding="utf-8") as f:
                json.dump(padrao, f, indent=4)

    def carregar_dados_na_tela(self):
        """Lê os arquivos reais e joga nos inputs"""

        def carregar_dados_na_tela(self):
            try:
                with open(self.caminho_config_app, "r", encoding="utf-8") as f:
                    config_app = json.load(f)
                    self.inp_scanner.setText(config_app.get("pasta_scanner", ""))
                    self.inp_processos.setText(config_app.get("pasta_processos", ""))
                    self.inp_ferc.setText(config_app.get("pasta_ferc", ""))  # PUXA DO JSON
            except:
                pass

        # 2. Carrega JSON dos Modelos
        try:
            if os.path.exists(self.caminho_modelos):
                with open(self.caminho_modelos, "r", encoding="utf-8") as f:
                    conteudo = json.load(f)
                    # Formata bonitão com indentação
                    texto_formatado = json.dumps(conteudo, indent=4, ensure_ascii=False)
                    self.editor_json.setText(texto_formatado)
        except Exception as e:
            self.editor_json.setText(f"Erro ao ler JSON: {e}")

    def criar_label(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold;")
        return lbl

    def selecionar_pasta(self, input_alvo):
        pasta = QFileDialog.getExistingDirectory(self, "Selecione a Pasta")
        if pasta:
            input_alvo.setText(pasta)

    def salvar_diretorios(self):
        dados = {
            "pasta_scanner": self.inp_scanner.text().strip(),
            "pasta_processos": self.inp_processos.text().strip(),
            "pasta_ferc": self.inp_ferc.text().strip()  # SALVA NO JSON
        }
        try:
            with open(self.caminho_config_app, "w", encoding="utf-8") as f:
                json.dump(dados, f, indent=4, ensure_ascii=False)
            QMessageBox.information(self, "Sucesso", "Diretórios salvos com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar:\n{str(e)}")

    def salvar_modelos(self):
        texto_digitado = self.editor_json.toPlainText()
        try:
            # A TRAVA DE SEGURANÇA: Tenta converter o texto em objeto Python
            # Se a pessoa esqueceu uma aspa ou vírgula, vai dar erro aqui e não salva!
            dados_json = json.loads(texto_digitado)

            with open(self.caminho_modelos, "w", encoding="utf-8") as f:
                json.dump(dados_json, f, indent=4, ensure_ascii=False)

            QMessageBox.information(self, "Sucesso",
                                    "Modelos atualizados e validados com sucesso!\nAs mudanças já estão ativas na tela de Requerimentos.")
        except json.JSONDecodeError as e:
            # Mostra exatamente a linha onde está o erro de digitação
            QMessageBox.warning(self, "Erro de Sintaxe JSON",
                                f"Você cometeu um erro de digitação no código JSON.\n\nDetalhe do erro: {e.msg}\nLinha: {e.lineno}, Coluna: {e.colno}\n\nO sistema NÃO salvou para evitar falhas. Corrija e tente novamente.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar:\n{str(e)}")