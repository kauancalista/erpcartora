import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QMessageBox, QFrame,
                             QLineEdit, QFormLayout, QStackedWidget, QRadioButton,
                             QTextEdit)
from PyQt6.QtCore import Qt
from core.gerador_requerimentos import gerar_docx_requerimento

CONFIG_MODELOS = {
    "Retificação de Registro Civil": {
        "arquivo_docx": "modelo_retificacao.docx",
        "descricao": "Utilizado para corrigir erros materiais em certidões de nascimento, casamento ou óbito.",
        "campos": [
            {"label": "Nome do Requerente", "tag": "nome_cliente"},
            {"label": "CPF", "tag": "cpf"},
            {"label": "O que deseja retificar?", "tag": "item_retificacao"},
            {"label": "Motivo da retificação", "tag": "motivo"}
        ]
    },
    "Declaração de Hipossuficiência": {
        "arquivo_docx": "modelo_declaracao.docx",
        "descricao": "Declaração de pobreza para solicitação de gratuidade nos atos cartorários.",
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

        self.inputs_criados = {}
        self.passo_atual = 0

        # Estilo específico para o Stepper desta tela
        self.setStyleSheet("""
            /* Botões do Menu de Passos (Stepper) */
            QPushButton.stepper-btn {
                background-color: transparent;
                color: #8A92A6;
                text-align: left;
                padding: 12px 15px;
                font-size: 14px;
                font-weight: 600;
                border: none;
                border-radius: 8px;
            }
            QPushButton.stepper-btn:checked {
                background-color: #2962FF;
                color: #FFFFFF;
            }
            QPushButton.stepper-btn:disabled {
                color: #4A5568;
            }

            /* Box de Descrição no Passo 1 */
            QFrame#box-descricao {
                background-color: #151A27;
                border: 1px solid #1E2532;
                border-radius: 8px;
            }

            /* Radio Buttons (Modalidade) */
            QRadioButton { color: white; font-size: 13px; font-weight: bold; }
            QRadioButton::indicator { width: 16px; height: 16px; border-radius: 8px; border: 2px solid #2c2f3f; background-color: transparent; }
            QRadioButton::indicator:checked { background-color: #2962FF; border: 2px solid #2962FF; }

            /* Área de Texto (Passo 3) */
            QTextEdit { background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; color: white; padding: 10px; font-size: 13px; }
            QTextEdit:focus { border: 1px solid #2962FF; }
        """)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)

        # --- CABEÇALHO ---
        layout_topo = QVBoxLayout()
        lbl_titulo = QLabel("← Novo Requerimento")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        lbl_sub = QLabel("Preencha os dados e gere o requerimento")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8A92A6; margin-bottom: 20px;")
        layout_topo.addWidget(lbl_titulo)
        layout_topo.addWidget(lbl_sub)
        layout_principal.addLayout(layout_topo)

        # --- ÁREA DIVIDIDA (Menu lateral + Conteúdo) ---
        layout_split = QHBoxLayout()

        # 1. MENU LATERAL DO STEPPER (Esquerda)
        menu_stepper = QVBoxLayout()
        menu_stepper.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_passo1 = self.criar_botao_stepper("1  Tipo de requerimento")
        self.btn_passo2 = self.criar_botao_stepper("2. Dados do requerente")
        self.btn_passo3 = self.criar_botao_stepper("3. Informações adicionais")
        self.btn_passo4 = self.criar_botao_stepper("4. Revisão e geração")

        menu_stepper.addWidget(self.btn_passo1)
        menu_stepper.addWidget(self.btn_passo2)
        menu_stepper.addWidget(self.btn_passo3)
        menu_stepper.addWidget(self.btn_passo4)

        layout_split.addLayout(menu_stepper, 1)  # Peso 1 para menu

        # 2. PAINEL DE CONTEÚDO (Direita)
        self.painel_direito = QFrame()
        self.painel_direito.setProperty("class", "painel")  # Puxa do QSS Global
        layout_painel = QVBoxLayout(self.painel_direito)
        layout_painel.setContentsMargins(30, 30, 30, 30)

        # O Empilhador de Páginas interno
        self.stack_passos = QStackedWidget()
        self.criar_passo_1()
        self.criar_passo_2()
        self.criar_passo_3()
        self.criar_passo_4()
        layout_painel.addWidget(self.stack_passos)

        # Botões de Navegação (Inferior)
        layout_nav = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("background-color: #1A2133; color: white; border: 1px solid #2C364C;")
        self.btn_cancelar.clicked.connect(self.cancelar_fluxo)

        self.btn_voltar = QPushButton("Voltar")
        self.btn_voltar.setStyleSheet("background-color: #1A2133; color: white; border: 1px solid #2C364C;")
        self.btn_voltar.clicked.connect(self.voltar_passo)
        self.btn_voltar.hide()  # Esconde no passo 1

        self.btn_proximo = QPushButton("Próximo")
        self.btn_proximo.clicked.connect(self.avancar_passo)

        layout_nav.addWidget(self.btn_cancelar)
        layout_nav.addStretch()
        layout_nav.addWidget(self.btn_voltar)
        layout_nav.addWidget(self.btn_proximo)

        layout_painel.addLayout(layout_nav)
        layout_split.addWidget(self.painel_direito, 3)  # Peso 3 para o conteúdo (mais largo)

        layout_principal.addLayout(layout_split)

        # Inicia estado

        self.atualizar_tela()

    def criar_botao_stepper(self, texto):
        btn = QPushButton(texto)
        btn.setProperty("class", "stepper-btn")
        btn.setCheckable(True)
        # Desabilita o clique direto para forçar o usuário a usar o botão "Próximo"
        btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        return btn

    # ==========================================
    # CONSTRUÇÃO DAS PÁGINAS (PASSOS 1 A 4)
    # ==========================================
    def criar_passo_1(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        lbl = QLabel("Tipo de requerimento")
        lbl.setProperty("class", "titulo-secao")
        layout.addWidget(lbl)

        lbl_sel = QLabel("Selecione o tipo")
        lbl_sel.setProperty("class", "label-campo")
        layout.addWidget(lbl_sel)

        self.combo_modelos = QComboBox()
        self.combo_modelos.addItems(CONFIG_MODELOS.keys())
        self.combo_modelos.currentTextChanged.connect(self.atualizar_descricao_e_form)
        layout.addWidget(self.combo_modelos)
        layout.addSpacing(15)

        lbl_mod = QLabel("Modalidade")
        lbl_mod.setProperty("class", "label-campo")
        layout.addWidget(lbl_mod)

        layout_radios = QHBoxLayout()
        self.radio_pago = QRadioButton("Pago")
        self.radio_pago.setChecked(True)
        self.radio_hipo = QRadioButton("Hipossuficiência")
        layout_radios.addWidget(self.radio_pago)
        layout_radios.addWidget(self.radio_hipo)
        layout_radios.addStretch()
        layout.addLayout(layout_radios)
        layout.addSpacing(20)

        lbl_desc = QLabel("Descrição")
        lbl_desc.setProperty("class", "label-campo")
        layout.addWidget(lbl_desc)

        box_desc = QFrame()
        box_desc.setObjectName("box-descricao")
        box_layout = QHBoxLayout(box_desc)
        box_layout.setContentsMargins(15, 15, 15, 15)

        lbl_icone = QLabel("📄")
        lbl_icone.setStyleSheet("font-size: 24px; padding-right: 10px;")
        self.lbl_texto_desc = QLabel(CONFIG_MODELOS[self.combo_modelos.currentText()]["descricao"])
        self.lbl_texto_desc.setWordWrap(True)
        self.lbl_texto_desc.setStyleSheet("color: #E2E8F0; line-height: 1.5;")

        box_layout.addWidget(lbl_icone)
        box_layout.addWidget(self.lbl_texto_desc, 1)
        layout.addWidget(box_desc)
        layout.addStretch()

        self.stack_passos.addWidget(page)

    def criar_passo_2(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        lbl = QLabel("Dados do requerente")
        lbl.setProperty("class", "titulo-secao")
        layout.addWidget(lbl)

        self.layout_campos_dinamicos = QFormLayout()
        self.layout_campos_dinamicos.setVerticalSpacing(15)
        layout.addLayout(self.layout_campos_dinamicos)
        layout.addStretch()

        self.stack_passos.addWidget(page)
        self.atualizar_descricao_e_form(self.combo_modelos.currentText())  # Desenha a primeira vez

    def criar_passo_3(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        lbl = QLabel("Informações adicionais")
        lbl.setProperty("class", "titulo-secao")
        layout.addWidget(lbl)

        lbl_obs = QLabel("Observações ou notas para o documento (Opcional)")
        lbl_obs.setProperty("class", "label-campo")
        layout.addWidget(lbl_obs)

        self.texto_obs = QTextEdit()
        self.texto_obs.setPlaceholderText("Digite informações complementares aqui...")
        layout.addWidget(self.texto_obs)

        self.stack_passos.addWidget(page)

    def criar_passo_4(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        lbl = QLabel("Revisão e geração")
        lbl.setProperty("class", "titulo-secao")
        layout.addWidget(lbl)

        lbl_sub = QLabel("Confira os dados antes de gerar o documento:")
        lbl_sub.setStyleSheet("color: #8A92A6; margin-bottom: 15px;")
        layout.addWidget(lbl_sub)

        # Painel que vai segurar o resumo gerado dinamicamente
        self.painel_resumo = QFrame()
        self.painel_resumo.setObjectName("box-descricao")
        self.layout_resumo = QFormLayout(self.painel_resumo)
        self.layout_resumo.setContentsMargins(20, 20, 20, 20)
        self.layout_resumo.setVerticalSpacing(10)

        layout.addWidget(self.painel_resumo)
        layout.addStretch()

        self.stack_passos.addWidget(page)

    # ==========================================
    # LÓGICAS DE ATUALIZAÇÃO E NAVEGAÇÃO
    # ==========================================
    def atualizar_descricao_e_form(self, nome_requerimento):
        if nome_requerimento not in CONFIG_MODELOS: return
        config = CONFIG_MODELOS[nome_requerimento]

        # Atualiza o box de descrição no Passo 1
        if hasattr(self, 'lbl_texto_desc'):
            self.lbl_texto_desc.setText(config["descricao"])

        # Refaz o formulário do Passo 2
        if hasattr(self, 'layout_campos_dinamicos'):
            for i in reversed(range(self.layout_campos_dinamicos.count())):
                widget = self.layout_campos_dinamicos.itemAt(i).widget()
                if widget: widget.deleteLater()

            self.inputs_criados.clear()
            for campo in config["campos"]:
                lbl = QLabel(campo["label"])
                lbl.setProperty("class", "label-campo")
                input_box = QLineEdit()
                input_box.setPlaceholderText("Digite aqui...")
                self.inputs_criados[campo["tag"]] = input_box
                self.layout_campos_dinamicos.addRow(lbl, input_box)

    def montar_tela_revisao(self):
        """Puxa tudo que foi digitado e exibe no Passo 4"""
        for i in reversed(range(self.layout_resumo.count())):
            widget = self.layout_resumo.itemAt(i).widget()
            if widget: widget.deleteLater()

        # Adiciona Tipo e Modalidade
        self.adicionar_linha_resumo("Documento:", self.combo_modelos.currentText())
        mod = "Pago" if self.radio_pago.isChecked() else "Hipossuficiência"
        self.adicionar_linha_resumo("Modalidade:", mod)

        # Adiciona os Dados Dinâmicos
        config = CONFIG_MODELOS[self.combo_modelos.currentText()]
        for campo in config["campos"]:
            valor_digitado = self.inputs_criados[campo["tag"]].text()
            if not valor_digitado: valor_digitado = "(Em branco)"
            self.adicionar_linha_resumo(campo["label"] + ":", valor_digitado)

    def adicionar_linha_resumo(self, titulo, valor):
        lbl_t = QLabel(titulo)
        lbl_t.setStyleSheet("color: #8A92A6; font-weight: bold; font-size: 13px;")
        lbl_v = QLabel(valor)
        lbl_v.setStyleSheet("color: white; font-weight: bold; font-size: 13px;")
        self.layout_resumo.addRow(lbl_t, lbl_v)

    def avancar_passo(self):
        if self.passo_atual == 3:
            self.gerar_documento()
            return

        self.passo_atual += 1

        if self.passo_atual == 3:  # Vai entrar no passo de revisão
            self.montar_tela_revisao()

        self.atualizar_tela()

    def voltar_passo(self):
        if self.passo_atual > 0:
            self.passo_atual -= 1
            self.atualizar_tela()

    def cancelar_fluxo(self):
        self.passo_atual = 0
        # Limpa os campos
        for input_box in self.inputs_criados.values():
            input_box.clear()
        self.texto_obs.clear()
        self.radio_pago.setChecked(True)
        self.atualizar_tela()

    def atualizar_tela(self):
        self.stack_passos.setCurrentIndex(self.passo_atual)

        # Atualiza a cor dos botões da esquerda
        botoes = [self.btn_passo1, self.btn_passo2, self.btn_passo3, self.btn_passo4]
        for i, btn in enumerate(botoes):
            btn.setChecked(i == self.passo_atual)

        # Configura os botões de baixo
        self.btn_voltar.setVisible(self.passo_atual > 0)

        if self.passo_atual == 3:
            self.btn_proximo.setText("Gerar Documento")
            self.btn_proximo.setStyleSheet("background-color: #27AE60; font-size: 15px;")  # Fica Verde na confirmação!
        else:
            self.btn_proximo.setText("Próximo")
            self.btn_proximo.setStyleSheet("background-color: #2962FF;")

    def gerar_documento(self):
        nome_requerimento = self.combo_modelos.currentText()
        config = CONFIG_MODELOS[nome_requerimento]

        dados_preenchidos = {}
        for tag, input_box in self.inputs_criados.items():
            dados_preenchidos[tag] = input_box.text().strip()

        try:
            caminho = gerar_docx_requerimento(config["arquivo_docx"], dados_preenchidos)
            QMessageBox.information(self, "Sucesso", "Requerimento gerado com sucesso!")
            os.startfile(os.path.abspath(caminho))
            self.cancelar_fluxo()  # Reseta a tela para o próximo cliente

        except FileNotFoundError:
            QMessageBox.warning(self, "Aviso", f"O arquivo modelo Word não foi encontrado na pasta 'assets/templates'.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro: {str(e)}")