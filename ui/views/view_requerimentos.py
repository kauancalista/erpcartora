import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QMessageBox, QFrame,
                             QLineEdit, QFormLayout)
from PyQt6.QtCore import Qt
from core.gerador_requerimentos import gerar_docx_requerimento

CONFIG_MODELOS = {
    "Retificação de Registro": {
        "arquivo_docx": "modelo_retificacao.docx",
        "campos": [
            {"label": "Nome do Requerente", "tag": "nome_cliente"},
            {"label": "CPF", "tag": "cpf"},
            {"label": "O que deseja retificar?", "tag": "item_retificacao"},
            {"label": "Motivo da retificação", "tag": "motivo"}
        ]
    },
    "Declaração de Hipossuficiência": {
        "arquivo_docx": "modelo_declaracao.docx",
        "campos": [
            {"label": "Nome Completo", "tag": "nome_cliente"},
            {"label": "CPF", "tag": "cpf"},
            {"label": "Profissão", "tag": "profissao"},
            {"label": "Renda Mensal (R$)", "tag": "renda"}
        ]
    }
}


class TelaRequerimentos(QWidget):
    def __init__(self):
        super().__init__()

        # Dando um nome à tela para o CSS não vazar para os filhos
        self.setObjectName("tela-requerimentos")

        # CSS Nível Produção
        self.setStyleSheet("""
            QWidget#tela-requerimentos { 
                background-color: #0d0f14; 
                font-family: 'Segoe UI', sans-serif; 
            }

            QFrame#painel-form { 
                background-color: #12141c; 
                border-radius: 12px; 
                border: 1px solid #1e212b;
            }

            /* A CORREÇÃO DA CAIXA PRETA: Fundo Transparente! */
            QLabel { 
                background-color: transparent; 
                color: #ffffff; 
            }

            QLabel.titulo-secao { font-size: 18px; font-weight: bold; margin-bottom: 5px; }
            QLabel.label-campo { font-size: 13px; color: #8a8d98; font-weight: bold; }

            /* Campos de Texto Modernos (Estilo Web) */
            QComboBox, QLineEdit { 
                background-color: #1a1d27; /* Fundo mais claro que o painel para dar destaque */
                border: 1px solid #2c2f3f; 
                border-radius: 8px; 
                padding: 12px 15px; 
                color: white; 
                font-size: 14px; 
            }
            QComboBox:focus, QLineEdit:focus { 
                border: 1px solid #2962ff; 
                background-color: #1e212b;
            }

            /* Retirando aquela seta feia padrão do ComboBox se quiser (Opcional) */
            QComboBox::drop-down { border: none; }

            QPushButton#btn-gerar { 
                background-color: #2962ff; 
                color: white; 
                font-weight: bold; 
                border-radius: 8px; 
                padding: 15px; 
                font-size: 15px; 
            }
            QPushButton#btn-gerar:hover { background-color: #1e4bd8; }
        """)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 40, 40, 40)  # Respiro nas bordas

        titulo = QLabel("Novo Requerimento")
        titulo.setStyleSheet("font-size: 26px; font-weight: bold; margin-bottom: 25px;")
        layout_principal.addWidget(titulo)

        # O Card Principal
        painel = QFrame()
        painel.setObjectName("painel-form")
        layout_painel = QVBoxLayout(painel)
        layout_painel.setContentsMargins(35, 35, 35, 35)
        layout_painel.setSpacing(25)  # Espaço entre os blocos

        # --- SEÇÃO 1: TIPO ---
        layout_tipo = QVBoxLayout()
        layout_tipo.setSpacing(8)
        lbl_tipo = QLabel("1. Selecione o tipo de documento")
        lbl_tipo.setProperty("class", "label-campo")

        self.combo_modelos = QComboBox()
        self.combo_modelos.addItems(CONFIG_MODELOS.keys())
        self.combo_modelos.currentTextChanged.connect(self.desenhar_formulario_dinamico)

        layout_tipo.addWidget(lbl_tipo)
        layout_tipo.addWidget(self.combo_modelos)
        layout_painel.addLayout(layout_tipo)

        # Divisória mais sutil
        linha = QFrame()
        linha.setFrameShape(QFrame.Shape.HLine)
        linha.setStyleSheet("background-color: #2c2f3f; margin-top: 10px; margin-bottom: 10px;")
        layout_painel.addWidget(linha)

        # --- SEÇÃO 2: DADOS (O Form Dinâmico) ---
        lbl_dados = QLabel("2. Preencha os dados do requerente")
        lbl_dados.setProperty("class", "titulo-secao")
        layout_painel.addWidget(lbl_dados)

        self.layout_campos = QFormLayout()
        self.layout_campos.setVerticalSpacing(20)  # Espaço generoso entre os campos verticais
        layout_painel.addLayout(self.layout_campos)

        # --- SEÇÃO 3: BOTÃO ---
        self.btn_gerar = QPushButton("Gerar e Imprimir Documento")
        self.btn_gerar.setObjectName("btn-gerar")
        self.btn_gerar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_gerar.clicked.connect(self.gerar_documento)

        layout_painel.addStretch()
        layout_painel.addWidget(self.btn_gerar)

        layout_principal.addWidget(painel)

        self.inputs_criados = {}
        self.desenhar_formulario_dinamico(self.combo_modelos.currentText())

    def desenhar_formulario_dinamico(self, nome_requerimento):
        for i in reversed(range(self.layout_campos.count())):
            widget = self.layout_campos.itemAt(i).widget()
            if widget:
                widget.deleteLater()

        self.inputs_criados.clear()

        if nome_requerimento not in CONFIG_MODELOS:
            return

        config = CONFIG_MODELOS[nome_requerimento]

        for campo in config["campos"]:
            # Labels agora vão puxar o fundo transparente do CSS global
            lbl = QLabel(campo["label"])
            lbl.setProperty("class", "label-campo")

            input_box = QLineEdit()
            input_box.setPlaceholderText(f"Digite aqui...")

            self.inputs_criados[campo["tag"]] = input_box
            self.layout_campos.addRow(lbl, input_box)

    def gerar_documento(self):
        nome_requerimento = self.combo_modelos.currentText()
        config = CONFIG_MODELOS[nome_requerimento]
        arquivo_template = config["arquivo_docx"]

        dados_preenchidos = {}
        for tag, input_box in self.inputs_criados.items():
            dados_preenchidos[tag] = input_box.text().strip()

        try:
            caminho = gerar_docx_requerimento(arquivo_template, dados_preenchidos)
            QMessageBox.information(self, "Sucesso", "Requerimento gerado com sucesso!")
            os.startfile(os.path.abspath(caminho))

        except FileNotFoundError:
            QMessageBox.warning(self, "Aviso", f"O arquivo '{arquivo_template}' não foi encontrado.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro: {str(e)}")