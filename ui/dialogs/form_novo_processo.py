import os
import json
import re
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QPushButton, QMessageBox)
from database.conexao import SessionLocal
from database.crud import criar_processo, criar_tarefa

class DialogNovoProcesso(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cadastrar Novo Processo")
        self.resize(400, 350) # Aumentei um pouco a tela para caber o novo campo
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

        # NOVO CAMPO: PRAZO DA TAREFA
        self.input_prazo = QLineEdit()
        self.input_prazo.setPlaceholderText("DD/MM/AAAA")
        self.input_prazo.setStyleSheet(input_style)
        self.input_prazo.setInputMask("00/00/0000;_") # Máscara para obrigar a digitar a data certinha

        form_layout.addRow("Nome Completo:", self.input_nome)
        form_layout.addRow("CPF:", self.input_cpf)
        form_layout.addRow("WhatsApp:", self.input_whatsapp)
        form_layout.addRow("Serviço:", self.combo_servico)
        form_layout.addRow("Prazo Limite:", self.input_prazo)

        layout.addLayout(form_layout)

        self.btn_salvar = QPushButton("💾 Salvar Processo")
        self.btn_salvar.setStyleSheet("background-color: #27AE60; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        self.btn_salvar.clicked.connect(self.salvar_dados)
        layout.addWidget(self.btn_salvar)

    def salvar_dados(self):
        nome = self.input_nome.text().strip()
        cpf = self.input_cpf.text().strip()
        whatsapp = self.input_whatsapp.text().strip()
        servico = self.combo_servico.currentText()
        prazo_str = self.input_prazo.text().strip()

        if not nome:
            QMessageBox.warning(self, "Aviso", "O campo 'Nome Completo' é obrigatório!")
            return

        # ---------------------------------------------------------
        # CÉREBRO DA DATA: Converte o texto para objeto DateTime
        # ---------------------------------------------------------
        try:
            # A máscara deixa o campo como "//" se estiver vazio
            if prazo_str and prazo_str != "//":
                prazo_tarefa = datetime.strptime(prazo_str, "%d/%m/%Y")
            else:
                # Se a secretária não preencher, assume 7 dias de prazo padrão
                prazo_tarefa = datetime.now() + timedelta(days=7)
        except ValueError:
            QMessageBox.warning(self, "Erro na Data", "A data digitada é inválida. Use um dia e mês que existam!")
            return

        db = SessionLocal()
        novo_processo = criar_processo(
            db,
            nome_cliente=nome,
            cpf=cpf,
            tipo_servico=servico,
            telefone_whatsapp=whatsapp,
            data_prazo=prazo_tarefa
        )

        # CRIAÇÃO AUTOMÁTICA DA TAREFA NO PAINEL COM A DATA ESCOLHIDA
        criar_tarefa(db, descricao=f"Acompanhar {servico}: {nome}", responsavel="Equipe", data_limite=prazo_tarefa,
                     processo_id=novo_processo.id)

        # O db.close() foi REMOVIDO daqui e jogado lá pro final!

        pasta_base = os.path.join(os.getcwd(), "Arquivos_Cartorio")
        try:
            caminho_config = os.path.join(os.getcwd(), "config", "app_config.json")
            if os.path.exists(caminho_config):
                with open(caminho_config, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("pasta_processos"):
                        pasta_base = cfg["pasta_processos"]
        except:
            pass

        nome_seguro = re.sub(r'[\\/*?:"<>|]', "", nome)
        nome_pasta = f"Proc_{novo_processo.id:03d}_{nome_seguro.replace(' ', '_').upper()}"
        pasta_destino = os.path.join(pasta_base, nome_pasta)
        os.makedirs(pasta_destino, exist_ok=True)

        # AGORA SIM! Fechamos o banco só depois de usar o novo_processo.id para criar a pasta
        db.close()

        QMessageBox.information(self, "Sucesso", "Processo salvo, tarefa gerada e pasta criada com segurança!")
        self.accept()