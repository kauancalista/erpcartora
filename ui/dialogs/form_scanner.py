import os
import shutil
import pythoncom
import win32com.client
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QMessageBox, QFrame, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QCursor


class DialogScannerPopUp(QDialog):
    def __init__(self, pasta_destino_processo, parent=None):
        super().__init__(parent)
        self.pasta_destino = pasta_destino_processo

        # Onde o sistema vai guardar o arquivo cru recém-saído do scanner
        self.arquivo_temp = os.path.join(os.getcwd(), "temp_scan_cartorio.jpg")

        self.setWindowTitle("🖨️ Scanner Digital (Controle de Hardware)")
        self.resize(800, 550)
        self.setStyleSheet("background-color: #0B0E14; color: white;")

        layout_principal = QHBoxLayout(self)
        layout_principal.setContentsMargins(15, 15, 15, 15)
        layout_principal.setSpacing(15)

        # ==========================================
        # LADO ESQUERDO: PRÉ-VISUALIZAÇÃO
        # ==========================================
        painel_preview = QFrame()
        painel_preview.setStyleSheet("border: 1px solid #1E2532; border-radius: 8px; background-color: #05070A;")
        layout_preview = QVBoxLayout(painel_preview)

        self.scroll = QScrollArea()
        self.scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.scroll.setStyleSheet("border: none; background-color: transparent;")

        self.lbl_imagem = QLabel("Coloque o papel no Scanner físico e\nclique em 'Iniciar Digitalização Nativa'.")
        self.lbl_imagem.setStyleSheet("color: #8A92A6; font-size: 14px;")
        self.lbl_imagem.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.scroll.setWidget(self.lbl_imagem)
        self.scroll.setWidgetResizable(True)
        layout_preview.addWidget(self.scroll)

        layout_principal.addWidget(painel_preview, 6)

        # ==========================================
        # LADO DIREITO: CONTROLES DO SCANNER
        # ==========================================
        painel_controles = QFrame()
        layout_controles = QVBoxLayout(painel_controles)
        layout_controles.setContentsMargins(10, 10, 10, 10)
        layout_controles.setSpacing(20)

        lbl_titulo = QLabel("Painel do Scanner")
        lbl_titulo.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        layout_controles.addWidget(lbl_titulo)

        # O BOTÃO MÁGICO QUE LIGA A MÁQUINA
        self.btn_acionar_scanner = QPushButton("🟢 Iniciar Digitalização Nativa")
        self.btn_acionar_scanner.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_acionar_scanner.setStyleSheet(
            "background-color: #8E44AD; color: white; font-weight: bold; padding: 15px; border-radius: 6px; font-size: 13px;")
        self.btn_acionar_scanner.clicked.connect(self.comunicar_com_hardware)
        layout_controles.addWidget(self.btn_acionar_scanner)

        # Campo de Renomear
        lbl_nome = QLabel("Nome do Documento (Ex: CNH, Certidão):")
        lbl_nome.setStyleSheet("color: #8A92A6; font-size: 13px;")
        layout_controles.addWidget(lbl_nome)

        self.input_nome = QLineEdit()
        self.input_nome.setPlaceholderText("Digite o nome para salvar...")
        self.input_nome.setStyleSheet(
            "background-color: #11151F; border: 1px solid #1E2532; border-radius: 6px; padding: 10px; color: white; font-size: 14px;")
        self.input_nome.setEnabled(False)
        layout_controles.addWidget(self.input_nome)

        layout_controles.addStretch()

        # Botão Salvar
        self.btn_salvar = QPushButton("💾 Salvar na Ficha do Cliente")
        self.btn_salvar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.btn_salvar.setStyleSheet(
            "background-color: #27AE60; color: white; font-weight: bold; padding: 15px; border-radius: 6px; font-size: 14px;")
        self.btn_salvar.setEnabled(False)
        self.btn_salvar.clicked.connect(self.salvar_no_processo)
        layout_controles.addWidget(self.btn_salvar)

        layout_principal.addWidget(painel_controles, 4)

        # ==========================================

    # CÉREBRO DA COMUNICAÇÃO COM O HARDWARE (WIA)
    # ==========================================
    def comunicar_com_hardware(self):
        try:
            # O Windows exige inicializar o COM para o PyQt não travar
            pythoncom.CoInitialize()

            # Deleta varreduras velhas para não bugar
            if os.path.exists(self.arquivo_temp):
                os.remove(self.arquivo_temp)

            # Chama o motor nativo do Windows (WIA)
            wia = win32com.client.Dispatch("WIA.CommonDialog")

            # Parâmetros: (DeviceType=Scanner(1), Intent=Color(1), Format=JPG, UI=True)
            # {B96B3CAE-0728-11D3-9D7B-0000F81EF32E} é o código universal para JPG
            imagem_bruta = wia.ShowAcquireImage(1, 1, 1, "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}", False, True, True)

            if imagem_bruta:
                # O Windows conseguiu scannear! Vamos salvar o arquivo
                imagem_bruta.SaveFile(self.arquivo_temp)

                # Gera o preview maravilhoso na tela
                pixmap = QPixmap(self.arquivo_temp)
                pixmap_ajustado = pixmap.scaled(450, 450, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
                self.lbl_imagem.setPixmap(pixmap_ajustado)

                # Libera pra secretária salvar
                self.input_nome.setEnabled(True)
                self.btn_salvar.setEnabled(True)
                self.input_nome.setFocus()
                self.btn_acionar_scanner.setText("🔄 Escanear Novamente")

        except Exception as e:
            msg = str(e)
            if "80210015" in msg or "dispositivo" in msg.lower():
                QMessageBox.critical(self, "Hardware não encontrado",
                                     "O Windows não conseguiu detectar nenhum scanner ligado/ativo via USB ou Wi-Fi.")
            else:
                QMessageBox.warning(self, "Aviso do Scanner",
                                    "A operação foi cancelada ou ocorreu um erro de conexão com a impressora.")

    # ==========================================
    # SALVAR E FECHAR
    # ==========================================
    def salvar_no_processo(self):
        nome_digitado = self.input_nome.text().strip()
        if not nome_digitado:
            QMessageBox.warning(self, "Aviso", "Por favor, digite um nome para o documento (ex: Identidade).")
            return

        import re
        nome_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_digitado)

        # Junta o nome digitado + .jpg (o WIA já escaneou em JPG)
        nome_final = f"{nome_limpo}.jpg"
        caminho_final = os.path.join(self.pasta_destino, nome_final)

        try:
            # Move o arquivo temporário para a pasta definitiva do cliente
            shutil.move(self.arquivo_temp, caminho_final)
            QMessageBox.information(self, "Sucesso", "Documento escaneado e anexado com sucesso!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar arquivo final:\n{e}")