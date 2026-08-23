import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QMessageBox, QFrame,
                             QLineEdit, QFormLayout, QStackedWidget, QRadioButton,
                             QTextEdit, QScrollArea, QCompleter)
from PyQt6.QtCore import Qt
from core.gerador_requerimentos import gerar_docx_requerimento


class TelaRequerimentos(QWidget):
    def __init__(self):
        super().__init__()
        self.inputs_criados = {}
        self.radios_criados = []
        self.passo_atual = 0
        self.config_modelos = self.carregar_json_config()

        self.setStyleSheet("""
            QPushButton.stepper-btn {
                background-color: transparent; color: #8A92A6; text-align: left;
                padding: 12px 15px; font-size: 14px; font-weight: 600; border: none; border-radius: 8px;
            }
            QPushButton.stepper-btn:checked { background-color: #2962FF; color: #FFFFFF; }
            QPushButton.stepper-btn:disabled { color: #4A5568; }
            QFrame#box-descricao { background-color: #151A27; border: 1px solid #1E2532; border-radius: 8px; }
            QRadioButton { color: white; font-size: 13px; font-weight: bold; margin-right: 15px; }
            QRadioButton::indicator { width: 16px; height: 16px; border-radius: 8px; border: 2px solid #2c2f3f; background-color: transparent; }
            QRadioButton::indicator:checked { background-color: #2962FF; border: 2px solid #2962FF; }
            QTextEdit { background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; color: white; padding: 10px; font-size: 13px; }
            QTextEdit:focus { border: 1px solid #2962FF; }
        """)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)

        # --- CABEÇALHO ---
        layout_topo = QVBoxLayout()
        lbl_titulo = QLabel("📝 Novo Requerimento")
        lbl_titulo.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        lbl_sub = QLabel("Selecione a modalidade e preencha os dados rigorosamente")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8A92A6; margin-bottom: 20px;")
        layout_topo.addWidget(lbl_titulo)
        layout_topo.addWidget(lbl_sub)
        layout_principal.addLayout(layout_topo)

        # --- ÁREA DIVIDIDA ---
        layout_split = QHBoxLayout()
        menu_stepper = QVBoxLayout()
        menu_stepper.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.btn_passo1 = self.criar_botao_stepper("1. Tipo de requerimento")
        self.btn_passo2 = self.criar_botao_stepper("2. Dados do requerente")
        self.btn_passo3 = self.criar_botao_stepper("3. Informações adicionais")
        self.btn_passo4 = self.criar_botao_stepper("4. Revisão e geração")

        menu_stepper.addWidget(self.btn_passo1)
        menu_stepper.addWidget(self.btn_passo2)
        menu_stepper.addWidget(self.btn_passo3)
        menu_stepper.addWidget(self.btn_passo4)
        layout_split.addLayout(menu_stepper, 1)

        self.painel_direito = QFrame()
        self.painel_direito.setProperty("class", "painel")
        layout_painel = QVBoxLayout(self.painel_direito)
        layout_painel.setContentsMargins(30, 30, 30, 30)

        self.stack_passos = QStackedWidget()
        self.criar_passo_1()
        self.criar_passo_2()
        self.criar_passo_3()
        self.criar_passo_4()
        layout_painel.addWidget(self.stack_passos)

        # Navegação
        layout_nav = QHBoxLayout()
        self.btn_cancelar = QPushButton("Cancelar")
        self.btn_cancelar.setStyleSheet("background-color: #1A2133; color: white; border: 1px solid #2C364C;")
        self.btn_cancelar.clicked.connect(self.cancelar_fluxo)

        self.btn_voltar = QPushButton("Voltar")
        self.btn_voltar.setStyleSheet("background-color: #1A2133; color: white; border: 1px solid #2C364C;")
        self.btn_voltar.clicked.connect(self.voltar_passo)
        self.btn_voltar.hide()

        self.btn_proximo = QPushButton("Próximo")
        self.btn_proximo.clicked.connect(self.avancar_passo)

        layout_nav.addWidget(self.btn_cancelar)
        layout_nav.addStretch()
        layout_nav.addWidget(self.btn_voltar)
        layout_nav.addWidget(self.btn_proximo)
        layout_painel.addLayout(layout_nav)

        layout_split.addWidget(self.painel_direito, 3)
        layout_principal.addLayout(layout_split)
        self.atualizar_tela()

    def carregar_json_config(self):
        """Lê as configurações direto do arquivo externo"""
        caminho_json = os.path.join(os.getcwd(), "config", "modelos_requerimentos.json")
        try:
            with open(caminho_json, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            QMessageBox.critical(None, "Erro Crítico", f"Falha ao carregar arquivo JSON de configuração:\n{str(e)}")
            return {}

    def limpar_layout_interno(self, layout):
        """O caçador de fantasmas: apaga recursivamente tudo dentro de um layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    self.limpar_layout_interno(item.layout())
                    item.layout().deleteLater()

    def criar_botao_stepper(self, texto):
        btn = QPushButton(texto)
        btn.setProperty("class", "stepper-btn")
        btn.setCheckable(True)
        btn.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        return btn

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
        self.combo_modelos.addItems(self.config_modelos.keys())
        self.combo_modelos.currentTextChanged.connect(self.atualizar_descricao_e_form)
        layout.addWidget(self.combo_modelos)
        layout.addSpacing(15)

        lbl_mod = QLabel("Modalidade")
        lbl_mod.setProperty("class", "label-campo")
        layout.addWidget(lbl_mod)

        self.layout_radios = QHBoxLayout()
        layout.addLayout(self.layout_radios)
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

        self.lbl_texto_desc = QLabel()
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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")

        container_form = QWidget()
        container_form.setStyleSheet("background-color: transparent;")
        self.layout_campos_dinamicos = QVBoxLayout(container_form)
        self.layout_campos_dinamicos.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.layout_campos_dinamicos.setSpacing(15)

        # AQUI RESOLVE O ERRO DOS CAMPOS VAZANDO: Adicionamos 15px de margem na direita!
        self.layout_campos_dinamicos.setContentsMargins(0, 0, 15, 0)

        scroll.setWidget(container_form)
        layout.addWidget(scroll)
        self.stack_passos.addWidget(page)
        self.atualizar_descricao_e_form(self.combo_modelos.currentText())

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

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background-color: transparent;")

        self.painel_resumo = QFrame()
        self.painel_resumo.setObjectName("box-descricao")
        self.layout_resumo = QFormLayout(self.painel_resumo)
        self.layout_resumo.setContentsMargins(20, 20, 20, 20)
        self.layout_resumo.setVerticalSpacing(10)

        scroll.setWidget(self.painel_resumo)
        layout.addWidget(scroll)
        self.stack_passos.addWidget(page)

    # ==========================================
    # CÉREBRO DE MONTAGEM E MÁSCARAS
    # ==========================================
    def atualizar_descricao_e_form(self, nome_requerimento):
        if not nome_requerimento or nome_requerimento not in self.config_modelos: return
        config = self.config_modelos[nome_requerimento]

        if hasattr(self, 'lbl_texto_desc'):
            self.lbl_texto_desc.setText(config.get("descricao", ""))

        # 1. ATUALIZA AS MODALIDADES DINÂMICAS
        if hasattr(self, 'layout_radios'):
            self.limpar_layout_interno(self.layout_radios)
            self.radios_criados.clear()

            for i, mod in enumerate(config.get("modalidades", [])):
                radio = QRadioButton(mod.capitalize() if mod != "CRC" else "CRC")
                if i == 0: radio.setChecked(True)
                self.layout_radios.addWidget(radio)
                self.radios_criados.append(radio)
            self.layout_radios.addStretch()

        # 2. ATUALIZA OS CAMPOS LADO A LADO E MÁSCARAS
        if hasattr(self, 'layout_campos_dinamicos'):
            # AQUI RESOLVE OS GHOST WIDGETS (Letras sobrepostas):
            self.limpar_layout_interno(self.layout_campos_dinamicos)
            self.inputs_criados.clear()

            for linha in config.get("linhas", []):
                layout_linha = QHBoxLayout()
                layout_linha.setSpacing(15)

                for campo in linha:
                    layout_coluna = QVBoxLayout()
                    layout_coluna.setSpacing(5)

                    lbl = QLabel(campo["label"])
                    lbl.setProperty("class", "label-campo")

                    input_box = QLineEdit()
                    input_box.setPlaceholderText("Digite aqui...")
                    input_box.setMinimumHeight(36)
                    input_box.setStyleSheet(
                        "background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; color: white; padding: 5px 10px; font-size: 13px;")

                    # MÁSCARAS
                    mascara = campo.get("mask")
                    if mascara == "cpf":
                        input_box.setInputMask("000.000.000-00;_")
                    elif mascara == "data":
                        input_box.setInputMask("00/00/0000;_")
                    elif mascara == "estado_civil":
                        completer = QCompleter(["Solteiro(a)", "Casado(a)", "Divorciado(a)", "Viúvo(a)", "Separado(a)"])
                        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
                        input_box.setCompleter(completer)
                    elif mascara == "livro":
                        def formatar_livro(texto, widget=input_box):
                            widget.blockSignals(True)
                            if not texto.startswith("A-"):
                                numeros = "".join(filter(str.isdigit, texto))
                                widget.setText("A-" + numeros)
                            widget.blockSignals(False)

                        input_box.textEdited.connect(formatar_livro)
                        input_box.setText("A-")

                    self.inputs_criados[campo["tag"]] = input_box
                    layout_coluna.addWidget(lbl)
                    layout_coluna.addWidget(input_box)

                    layout_linha.addLayout(layout_coluna, campo.get("flex", 1))

                self.layout_campos_dinamicos.addLayout(layout_linha)

    # ==========================================
    # CÉREBRO DE NAVEGAÇÃO E REVISÃO
    # ==========================================
    def obter_modalidade_selecionada(self):
        for radio in self.radios_criados:
            if radio.isChecked():
                return radio.text()
        return ""

    def montar_tela_revisao(self):
        self.limpar_layout_interno(self.layout_resumo)

        self.adicionar_linha_resumo("Documento:", self.combo_modelos.currentText())
        self.adicionar_linha_resumo("Modalidade:", self.obter_modalidade_selecionada())

        config = self.config_modelos[self.combo_modelos.currentText()]

        campos_flat = [campo for linha in config.get("linhas", []) for campo in linha]

        for campo in campos_flat:
            valor_digitado = self.inputs_criados[campo["tag"]].text()
            if not valor_digitado or valor_digitado == "A-": valor_digitado = "(Em branco)"
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
        if self.passo_atual == 3: self.montar_tela_revisao()
        self.atualizar_tela()

    def voltar_passo(self):
        if self.passo_atual > 0:
            self.passo_atual -= 1
            self.atualizar_tela()

    def cancelar_fluxo(self):
        self.passo_atual = 0
        for input_box in self.inputs_criados.values():
            if "A-" in input_box.text():
                input_box.setText("A-")
            elif input_box.inputMask():
                input_box.clear()
            else:
                input_box.clear()
        self.texto_obs.clear()
        if self.radios_criados: self.radios_criados[0].setChecked(True)
        self.atualizar_tela()

    def atualizar_tela(self):
        self.stack_passos.setCurrentIndex(self.passo_atual)
        botoes = [self.btn_passo1, self.btn_passo2, self.btn_passo3, self.btn_passo4]
        for i, btn in enumerate(botoes):
            btn.setChecked(i == self.passo_atual)

        self.btn_voltar.setVisible(self.passo_atual > 0)
        if self.passo_atual == 3:
            self.btn_proximo.setText("Gerar no Word")
            self.btn_proximo.setStyleSheet("background-color: #27AE60; font-size: 15px;")
        else:
            self.btn_proximo.setText("Próximo")
            self.btn_proximo.setStyleSheet("background-color: #2962FF;")

    def gerar_documento(self):
        nome_requerimento = self.combo_modelos.currentText()
        config = self.config_modelos.get(nome_requerimento)
        if not config: return
        modalidade = self.obter_modalidade_selecionada()

        dados_preenchidos = {}
        for tag, input_box in self.inputs_criados.items():
            dados_preenchidos[tag] = input_box.text().strip()

        meses = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro",
                 "novembro", "dezembro"]
        hoje = datetime.now()
        dados_preenchidos["data"] = f"{hoje.day:02d} de {meses[hoje.month - 1]} de {hoje.year}"

        if nome_requerimento == "Reconhecimento paternidade voluntário":
            linha_tracos = "__________________________________________________"

            dados_preenchidos["linha"] = ""
            dados_preenchidos["assinatura_adicional"] = ""
            dados_preenchidos["linha1"] = ""
            dados_preenchidos["assinatura_adicional1"] = ""
            dados_preenchidos["linha2"] = ""
            dados_preenchidos["assinatura_adicional2"] = ""

            nome_filho = dados_preenchidos.get("nome_registrado", "Registrado")

            if modalidade == "Reg. assina":
                dados_preenchidos["linha"] = linha_tracos
                dados_preenchidos["assinatura_adicional"] = f"Assinatura do Registrado: {nome_filho}"

            elif modalidade == "Crc":
                dados_preenchidos["linha1"] = linha_tracos
                dados_preenchidos["assinatura_adicional1"] = "Assinatura do Anuente 1"
                dados_preenchidos["linha2"] = linha_tracos
                dados_preenchidos["assinatura_adicional2"] = "Assinatura do Anuente 2"

        try:
            caminho_docx = gerar_docx_requerimento(config["arquivo_docx"], dados_preenchidos)
            QMessageBox.information(self, "Sucesso", "Requerimento gerado com sucesso!")

            # Abre o Word final direto na tela do usuário
            os.startfile(os.path.abspath(caminho_docx))

            self.cancelar_fluxo()

        except FileNotFoundError:
            QMessageBox.warning(self, "Aviso",
                                f"O arquivo '{config['arquivo_docx']}' não foi encontrado na pasta 'assets/templates'.")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro: {str(e)}")