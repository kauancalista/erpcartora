import os
import json
import re
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QPushButton, QMessageBox, QRadioButton, QHBoxLayout)
from database.conexao import SessionLocal
from database.crud import criar_processo, criar_tarefa
from utils_caminhos import obter_diretorio_base


class DialogNovoProcesso(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastrar Novo Processo")
        self.resize(450, 380)
        self.setStyleSheet("background-color: #0B0E14; color: white;")

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        input_style = "background-color: #11151F; border: 1px solid #1E2532; border-radius: 6px; color: white; padding: 8px;"

        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Ex: João da Silva")
        self.input_nome.setStyleSheet(input_style)

        self.input_cpf = QLineEdit()
        self.input_cpf.setPlaceholderText("000.000.000-00")
        self.input_cpf.setStyleSheet(input_style)

        self.input_whatsapp = QLineEdit()
        self.input_whatsapp.setPlaceholderText("(11) 99999-9999")
        self.input_whatsapp.setStyleSheet(input_style)

        self.combo_servico = QComboBox()
        self.combo_servico.addItems([
            "SEGUNDA VIA CERTIDÃO",
            "RETIFICAÇÃO",
            "RECONHECIMENTO PATERNIDADE",
            "OUTRO"
        ])
        self.combo_servico.setStyleSheet(input_style)

        # --- NOVA PARTE: ORIGEM DA SOLICITAÇÃO ---
        layout_radios = QHBoxLayout()
        layout_radios.setSpacing(10)

        self.radio_balcao = QRadioButton("BALCÃO")
        self.radio_cras = QRadioButton("CRAS")
        self.radio_crc = QRadioButton("CRC")
        self.radio_ap = QRadioButton("AP")

        estilo_pequeno = "QRadioButton { color: #E2E8F0; font-size: 12px; font-weight: bold; } QRadioButton::indicator { width: 14px; height: 14px; }"
        self.radio_balcao.setStyleSheet(estilo_pequeno)
        self.radio_cras.setStyleSheet(estilo_pequeno)
        self.radio_crc.setStyleSheet(estilo_pequeno)
        self.radio_ap.setStyleSheet(estilo_pequeno)

        self.radio_balcao.setChecked(True)  # Define BALCÃO como padrão

        layout_radios.addWidget(self.radio_balcao)
        layout_radios.addWidget(self.radio_cras)
        layout_radios.addWidget(self.radio_crc)
        layout_radios.addWidget(self.radio_ap)
        # -----------------------------------------

        self.input_prazo = QLineEdit()
        self.input_prazo.setPlaceholderText("DD/MM/AAAA")
        self.input_prazo.setStyleSheet(input_style)
        self.input_prazo.setInputMask("00/00/0000;_")

        form_layout.addRow("Nome Completo:", self.input_nome)
        form_layout.addRow("CPF:", self.input_cpf)
        form_layout.addRow("WhatsApp:", self.input_whatsapp)
        form_layout.addRow("Serviço:", self.combo_servico)
        form_layout.addRow("Origem:", layout_radios)  # INSERIDO DEBAIXO DE SERVIÇO
        form_layout.addRow("Prazo Limite:", self.input_prazo)

        layout.addLayout(form_layout)

        self.btn_salvar = QPushButton("💾 Salvar Processo")
        self.btn_salvar.setStyleSheet(
            "background-color: #27AE60; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        self.btn_salvar.clicked.connect(self.salvar_dados)
        layout.addWidget(self.btn_salvar)

    def salvar_dados(self):
        nome = self.input_nome.text().strip()
        cpf = self.input_cpf.text().strip()
        whatsapp = self.input_whatsapp.text().strip()
        servico = self.combo_servico.currentText()
        prazo_str = self.input_prazo.text().strip()

        # Captura qual bolinha está marcada
        origem = "BALCÃO"
        if self.radio_cras.isChecked():
            origem = "CRAS"
        elif self.radio_crc.isChecked():
            origem = "CRC"
        elif self.radio_ap.isChecked():
            origem = "AP"

        if not nome:
            QMessageBox.warning(self, "Aviso", "O campo 'Nome Completo' é obrigatório!")
            return

        try:
            if prazo_str and prazo_str != "//":
                prazo_tarefa = datetime.strptime(prazo_str, "%d/%m/%Y")
            else:
                prazo_tarefa = datetime.now() + timedelta(days=7)
        except ValueError:
            QMessageBox.warning(self, "Erro na Data", "A data digitada é inválida. Use um dia e mês que existam!")
            return

        db = SessionLocal()
        try:
            novo_processo = criar_processo(
                db,
                nome_cliente=nome,
                cpf=cpf,
                tipo_servico=servico,
                telefone_whatsapp=whatsapp,
                data_prazo=prazo_tarefa,
                origem_solicitacao=origem  # ENVIA A INFORMAÇÃO PARA O CRUD
            )

            criar_tarefa(
                db,
                descricao=f"Acompanhar {servico}: {nome}",
                responsavel="Equipe",
                data_limite=prazo_tarefa,
                processo_id=novo_processo.id
            )

            pasta_base = os.path.join(obter_diretorio_base(), "Arquivos_Cartorio")
            try:
                caminho_config = os.path.join(obter_diretorio_base(), "config", "app_config.json")
                if os.path.exists(caminho_config):
                    with open(caminho_config, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        if cfg.get("pasta_processos"):
                            pasta_base = cfg["pasta_processos"]
            except Exception:
                pass

            nome_seguro = re.sub(r'[\\/*?:"<>|]', "", nome)
            nome_pasta = f"Proc_{novo_processo.id:03d}_{nome_seguro.replace(' ', '_').upper()}"
            pasta_destino = os.path.join(pasta_base, nome_pasta)
            os.makedirs(pasta_destino, exist_ok=True)

        finally:
            db.close()

        QMessageBox.information(self, "Sucesso", "Processo salvo, tarefa gerada e pasta criada com segurança!")
        self.accept()