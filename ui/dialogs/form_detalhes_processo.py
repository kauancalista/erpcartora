from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QMessageBox, QFrame, QFileDialog)
from PyQt6.QtCore import Qt
import os
from database.conexao import SessionLocal
from database.crud import obter_processo_por_id, atualizar_status_processo, listar_documentos_do_processo, \
    adicionar_documento


class DialogDetalhesProcesso(QDialog):
    def __init__(self, processo_id):
        super().__init__()
        self.processo_id = processo_id
        self.setWindowTitle(f"Ficha do Processo #{processo_id}")
        self.resize(650, 600)


        # Puxa os dados do banco
        self.carregar_dados_do_banco()
        self.montar_layout()

    def carregar_dados_do_banco(self):
        db = SessionLocal()
        self.processo = obter_processo_por_id(db, self.processo_id)
        self.documentos = listar_documentos_do_processo(db, self.processo_id)
        db.close()

    def montar_layout(self):
        # Se já existir um layout (quando atualizamos a tela), nós limpamos
        if self.layout():
            QWidget().setLayout(self.layout())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # --- CABEÇALHO ---
        lbl_nome = QLabel(self.processo.nome_cliente)
        lbl_nome.setProperty("class", "titulo")
        lbl_servico = QLabel(f"Proc. 2026.08.{self.processo.id:04d} | Serviço: {self.processo.tipo_servico}")
        lbl_servico.setProperty("class", "subtitulo")

        layout.addWidget(lbl_nome)
        layout.addWidget(lbl_servico)
        layout.addSpacing(15)

        # --- SEÇÃO DE ARQUIVOS ---
        layout_arq_topo = QHBoxLayout()
        lbl_arq_titulo = QLabel("Arquivos do processo")
        lbl_arq_titulo.setStyleSheet("font-weight: bold; font-size: 16px;")

        # O NOVO BOTÃO DE ANEXAR!
        btn_anexar = QPushButton("+ Anexar PDF")
        btn_anexar.setObjectName("btn-anexar")
        btn_anexar.clicked.connect(self.abrir_explorador_arquivos)

        # O NOVO BOTÃO DO SCANNER! 👇
        btn_scanner = QPushButton("🖨️ Digitalizar (Scanner)")
        btn_scanner.setObjectName("btn-scanner")
        btn_scanner.clicked.connect(self.acionar_scanner)

        layout_arq_topo.addWidget(lbl_arq_titulo)
        layout_arq_topo.addStretch()
        layout_arq_topo.addWidget(btn_anexar)
        layout_arq_topo.addWidget(btn_scanner)
        layout.addLayout(layout_arq_topo)

        # --- CARDS DE DOCUMENTOS ---
        layout_cards = QHBoxLayout()
        tem_documento = len(self.documentos) > 0
        nome_doc = self.documentos[-1].nome_arquivo if tem_documento else "Nenhum arquivo"

        card_principal = QFrame()
        card_principal.setProperty("class", "card-verde" if tem_documento else "card-vermelho")
        card_principal.setFixedSize(280, 150)
        layout_card_1 = QVBoxLayout(card_principal)

        lbl_titulo_c1 = QLabel("Documento principal")
        lbl_titulo_c1.setStyleSheet("font-weight: bold;")
        lbl_icone_c1 = QLabel("📄 PDF" if tem_documento else "❌")
        lbl_icone_c1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_icone_c1.setStyleSheet("font-size: 24px; color: #e74c3c;" if not tem_documento else "font-size: 24px;")
        lbl_nome_c1 = QLabel(nome_doc if tem_documento else "Arquivo não encontrado")
        lbl_nome_c1.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout_card_1.addWidget(lbl_titulo_c1)
        layout_card_1.addWidget(lbl_icone_c1)
        layout_card_1.addWidget(lbl_nome_c1)

        layout_cards.addWidget(card_principal)
        layout_cards.addStretch()
        layout.addLayout(layout_cards)
        layout.addSpacing(20)

        # --- STATUS ---
        lbl_status_titulo = QLabel("Status do Processo:")
        lbl_status_titulo.setStyleSheet("font-weight: bold; color: #8a8d98;")
        layout.addWidget(lbl_status_titulo)

        layout_status = QHBoxLayout()
        self.combo_status = QComboBox()
        self.combo_status.addItems(["Aguardando Documento", "Em Análise", "Pendente com o Cliente", "🟢 PRONTO"])
        self.combo_status.setCurrentText(self.processo.status)

        btn_salvar_status = QPushButton("Salvar Alterações")
        btn_salvar_status.clicked.connect(self.salvar_status)

        layout_status.addWidget(self.combo_status)
        layout_status.addWidget(btn_salvar_status)
        layout.addLayout(layout_status)
        layout.addStretch()

    # --- A MÁGICA DE LER O ARQUIVO DO COMPUTADOR ---
    def abrir_explorador_arquivos(self):
        # Abre a janela do Windows para escolher um arquivo PDF
        caminho_arquivo, _ = QFileDialog.getOpenFileName(
            self,
            "Selecione o Documento PDF",
            "",
            "Arquivos PDF (*.pdf);;Todos os Arquivos (*)"
        )

        if caminho_arquivo:
            # Extrai apenas o nome do arquivo (ex: "certidao.pdf")
            nome_arquivo = os.path.basename(caminho_arquivo)

            # Salva no Banco de Dados
            db = SessionLocal()
            adicionar_documento(
                db=db,
                processo_id=self.processo_id,
                nome_arquivo=nome_arquivo,
                tipo_documento="PDF Principal",
                caminho_arquivo=caminho_arquivo
            )
            db.close()

            QMessageBox.information(self, "Sucesso", f"Documento '{nome_arquivo}' anexado com sucesso!")

            # Recarrega a tela para o card vermelho virar verde imediatamente!
            self.carregar_dados_do_banco()
            self.montar_layout()

    def salvar_status(self):
        novo_status = self.combo_status.currentText()
        db = SessionLocal()
        atualizar_status_processo(db, self.processo_id, novo_status)
        db.close()
        self.accept()


    def acionar_scanner(self):
        try:
            import win32com.client
            import os

            QMessageBox.information(self, "Scanner",
                                    "Iniciando comunicação com o Scanner. Selecione seu aparelho na próxima janela.")

            # Abre a janela nativa do Windows para escanear
            wia = win32com.client.Dispatch("WIA.CommonDialog")
            imagem = wia.ShowAcquireImage()

            if imagem:
                caminho_temp = os.path.join(os.path.expanduser("~"), "digitalizacao_cartorio.jpg")
                # Remove arquivo antigo se existir
                if os.path.exists(caminho_temp):
                    os.remove(caminho_temp)

                imagem.SaveFile(caminho_temp)

                # AQUI VOCÊ PODE CONVERTER O JPG PARA PDF USANDO A BIBLIOTECA PIL (Pillow)
                QMessageBox.information(self, "Sucesso", f"Documento escaneado e salvo em: {caminho_temp}")

        except Exception as e:
            QMessageBox.critical(self, "Erro no Scanner",
                                 f"Não foi possível conectar ao scanner.\n\nDetalhes: {str(e)}")