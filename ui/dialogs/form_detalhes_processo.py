import os
import shutil
import json
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QPushButton, QMessageBox, QFrame,
                             QFileDialog, QScrollArea, QWidget)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor

from database.conexao import SessionLocal
from database.crud import (obter_processo_por_id, atualizar_status_processo,
                           listar_documentos_do_processo, adicionar_documento)


class DialogDetalhesProcesso(QDialog):
    def __init__(self, processo_id):
        super().__init__()
        self.processo_id = processo_id
        self.setWindowTitle(f"Ficha do Processo #{processo_id}")
        self.resize(700, 650)
        self.setStyleSheet("background-color: #0B0E14; color: white;")

        self.carregar_dados_do_banco()
        self.montar_layout()

    def carregar_dados_do_banco(self):
        db = SessionLocal()
        self.processo = obter_processo_por_id(db, self.processo_id)
        self.documentos = listar_documentos_do_processo(db, self.processo_id)
        db.close()

    def montar_layout(self):
        if self.layout():
            QWidget().setLayout(self.layout())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        # --- CABEÇALHO ---
        lbl_nome = QLabel(self.processo.nome_cliente)
        lbl_nome.setStyleSheet("font-size: 22px; font-weight: bold;")
        lbl_servico = QLabel(f"Proc. 2026.08.{self.processo.id:04d} | Serviço: {self.processo.tipo_servico}")
        lbl_servico.setStyleSheet("font-size: 13px; color: #8A92A6; margin-bottom: 15px;")
        layout.addWidget(lbl_nome)
        layout.addWidget(lbl_servico)

        # --- SEÇÃO DE ARQUIVOS (O CORE DMS) ---
        layout_arq_topo = QHBoxLayout()
        lbl_arq_titulo = QLabel("Arquivos do Processo")
        lbl_arq_titulo.setStyleSheet("font-weight: bold; font-size: 16px;")

        btn_anexar = QPushButton("+ Anexar Manualmente")
        btn_anexar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_anexar.setStyleSheet(
            "background-color: #2962FF; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_anexar.clicked.connect(self.abrir_explorador_arquivos)

        btn_scanner = QPushButton("🖨️ Ir para o Scanner OCR")
        btn_scanner.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_scanner.setStyleSheet(
            "background-color: #8E44AD; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_scanner.clicked.connect(self.avisar_scanner)

        layout_arq_topo.addWidget(lbl_arq_titulo)
        layout_arq_topo.addStretch()
        layout_arq_topo.addWidget(btn_anexar)
        layout_arq_topo.addWidget(btn_scanner)
        layout.addLayout(layout_arq_topo)

        # --- LISTA DE DOCUMENTOS COM SCROLL ---
        scroll_docs = QScrollArea()
        scroll_docs.setWidgetResizable(True)
        scroll_docs.setStyleSheet(
            "QScrollArea { border: 1px solid #1E2532; border-radius: 8px; background-color: #11151F; }")

        container_docs = QWidget()
        container_docs.setStyleSheet("background-color: transparent;")
        lay_docs = QVBoxLayout(container_docs)
        lay_docs.setSpacing(10)
        lay_docs.setContentsMargins(15, 15, 15, 15)

        if not self.documentos:
            lbl_vazio = QLabel("Nenhum arquivo anexado ainda.\nUtilize o Scanner OCR ou anexe manualmente.")
            lbl_vazio.setStyleSheet("color: #8A92A6; font-style: italic;")
            lbl_vazio.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lay_docs.addWidget(lbl_vazio)
        else:
            for doc in self.documentos:
                card_doc = QFrame()
                card_doc.setStyleSheet(
                    "background-color: #1A2133; border: 1px solid #2C364C; border-radius: 8px; padding: 10px;")
                lay_card = QHBoxLayout(card_doc)

                lbl_icone = QLabel("📄")
                lbl_icone.setStyleSheet("font-size: 24px; border: none;")

                info_layout = QVBoxLayout()
                lbl_nome_doc = QLabel(doc.nome_arquivo)
                lbl_nome_doc.setStyleSheet("font-weight: bold; color: white; border: none; font-size: 14px;")
                lbl_tipo_doc = QLabel(doc.tipo_documento)
                lbl_tipo_doc.setStyleSheet("font-size: 12px; color: #8A92A6; border: none;")
                info_layout.addWidget(lbl_nome_doc)
                info_layout.addWidget(lbl_tipo_doc)

                btn_abrir = QPushButton("Abrir Arquivo")
                btn_abrir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
                btn_abrir.setStyleSheet(
                    "background-color: #27AE60; color: white; padding: 8px 15px; border-radius: 6px; font-weight: bold;")
                btn_abrir.clicked.connect(lambda checked, c=doc.caminho_arquivo: self.abrir_doc(c))

                lay_card.addWidget(lbl_icone)
                lay_card.addLayout(info_layout, 1)
                lay_card.addWidget(btn_abrir)

                lay_docs.addWidget(card_doc)

        lay_docs.addStretch()
        scroll_docs.setWidget(container_docs)
        layout.addWidget(scroll_docs)
        layout.addSpacing(20)

        # --- STATUS DO PROCESSO ---
        lbl_status_titulo = QLabel("Status do Processo:")
        lbl_status_titulo.setStyleSheet("font-weight: bold; color: #8a8d98;")
        layout.addWidget(lbl_status_titulo)

        layout_status = QHBoxLayout()
        self.combo_status = QComboBox()
        self.combo_status.addItems(["Aguardando Documento", "Em Análise", "Revisar", "Pendente", "Completo"])
        self.combo_status.setCurrentText(self.processo.status)
        self.combo_status.setStyleSheet(
            "background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; padding: 10px; color: white;")

        btn_salvar_status = QPushButton("Salvar Alterações")
        btn_salvar_status.setStyleSheet(
            "background-color: #2962FF; color: white; padding: 10px; border-radius: 6px; font-weight: bold;")
        btn_salvar_status.clicked.connect(self.salvar_status)

        layout_status.addWidget(self.combo_status)
        layout_status.addWidget(btn_salvar_status)
        layout.addLayout(layout_status)

    # --- A MÁGICA: COPIA O ARQUIVO PRA PASTA DO PROCESSO E SALVA NO BANCO ---
    def abrir_explorador_arquivos(self):
        caminho_arquivo, _ = QFileDialog.getOpenFileName(
            self, "Selecione o Documento", "", "PDF e Imagens (*.pdf *.jpg *.jpeg *.png);;Todos (*)"
        )
        if caminho_arquivo:
            nome_arquivo_original = os.path.basename(caminho_arquivo)

            # 1. Puxa a Configuração da Pasta
            pasta_base = os.path.join(os.getcwd(), "Arquivos_Cartorio")
            try:
                caminho_config = os.path.join(os.getcwd(), "config", "app_config.json")
                if os.path.exists(caminho_config):
                    with open(caminho_config, "r", encoding="utf-8") as f:
                        cfg = json.load(f)
                        if cfg.get("pasta_processos"): pasta_base = cfg["pasta_processos"]
            except:
                pass

            # 2. Reconstrói o Caminho da Pasta deste Cliente
            nome_pasta = f"Proc_{self.processo.id:03d}_{self.processo.nome_cliente.replace(' ', '_').upper()}"
            pasta_destino = os.path.join(pasta_base, nome_pasta)
            os.makedirs(pasta_destino, exist_ok=True)  # Garante que a pasta existe

            # 3. Faz a Cópia do Arquivo
            caminho_final = os.path.join(pasta_destino, nome_arquivo_original)
            shutil.copy2(caminho_arquivo, caminho_final)

            # 4. Grava no Banco
            db = SessionLocal()
            adicionar_documento(
                db=db,
                processo_id=self.processo_id,
                nome_arquivo=nome_arquivo_original,
                tipo_documento="Anexo Manual",
                caminho_arquivo=caminho_final
            )
            db.close()

            QMessageBox.information(self, "Sucesso", "Documento anexado e copiado para a pasta do processo!")
            self.carregar_dados_do_banco()
            self.montar_layout()

    def salvar_status(self):
        novo_status = self.combo_status.currentText()
        db = SessionLocal()
        atualizar_status_processo(db, self.processo_id, novo_status)
        db.close()
        self.accept()

    def abrir_doc(self, caminho):
        if os.path.exists(caminho):
            os.startfile(caminho)
        else:
            QMessageBox.warning(self, "Erro",
                                "Arquivo físico não encontrado na pasta. Ele pode ter sido movido ou excluído.")

    def avisar_scanner(self):
        QMessageBox.information(self, "Dica",
                                "Para usar o OCR com Inteligência Artificial, feche esta janela e acesse a aba 'Scanner e OCR' no menu lateral esquerdo.")