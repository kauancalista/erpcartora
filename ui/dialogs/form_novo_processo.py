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
        criar_processo(db, nome_cliente=nome, cpf=cpf, tipo_servico=servico, telefone_whatsapp=whatsapp)
        db.close()

        QMessageBox.information(self, "Sucesso", "Processo salvo com sucesso!")
        self.accept()