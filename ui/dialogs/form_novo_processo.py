import os
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QPushButton, QMessageBox)
from database.conexao import SessionLocal
from database.crud import criar_processo


class DialogNovoProcesso(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastrar Novo Processo")
        self.resize(400, 300)

        layout = QVBoxLayout(self)
        form_layout = QFormLayout()

        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Ex: João da Silva")
        self.input_cpf = QLineEdit()
        self.input_cpf.setPlaceholderText("000.000.000-00")
        self.input_whatsapp = QLineEdit()
        self.input_whatsapp.setPlaceholderText("(11) 99999-9999")

        self.combo_servico = QComboBox()
        self.combo_servico.addItems([
            "Certidão de Nascimento",
            "Certidão de Casamento",
            "Retificação de Registro",
            "Reconhecimento de Paternidade"
        ])

        form_layout.addRow("Nome Completo:", self.input_nome)
        form_layout.addRow("CPF:", self.input_cpf)
        form_layout.addRow("WhatsApp:", self.input_whatsapp)
        form_layout.addRow("Serviço:", self.combo_servico)
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

        if not nome:
            QMessageBox.warning(self, "Aviso", "O campo 'Nome Completo' é obrigatório!")
            return

        db = SessionLocal()
        # Salva no banco e pega a ficha criada
        novo_processo = criar_processo(db, nome_cliente=nome, cpf=cpf, tipo_servico=servico, telefone_whatsapp=whatsapp)
        db.close()

        # =========================================================
        # A PONTE: CRIA A PASTA FÍSICA LENDO O ARQUIVO DE CONFIGURAÇÃO
        # =========================================================
        pasta_base = os.path.join(os.getcwd(), "Arquivos_Cartorio")  # Pasta padrão
        try:
            caminho_config = os.path.join(os.getcwd(), "config", "app_config.json")
            if os.path.exists(caminho_config):
                with open(caminho_config, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("pasta_processos"):
                        pasta_base = cfg["pasta_processos"]
        except:
            pass

        # Formato Padrão: Proc_001_NOME_DO_CLIENTE
        nome_pasta = f"Proc_{novo_processo.id:03d}_{nome.replace(' ', '_').upper()}"
        pasta_destino = os.path.join(pasta_base, nome_pasta)
        os.makedirs(pasta_destino, exist_ok=True)

        QMessageBox.information(self, "Sucesso", "Processo salvo e Pasta de Arquivos criada com sucesso!")
        self.accept()