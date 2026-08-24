import os
import shutil
import re
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

        # Onde o sistema vai guardar o arquivo cru
        self.arquivo_temp = os.path.join(os.getcwd(), "temp_scan_cartorio.jpg")

        self.setWindowTitle("🖨️ Scanner Digital (Integração Canon DR-C240 - 300 DPI A4)")
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

        self.lbl_imagem = QLabel("Coloque o documento no Canon DR-C240\ne clique em 'Puxar Folha'.")
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

        # O BOTÃO MÁGICO QUE LIGA A MÁQUINA DIRETO
        self.btn_acionar_scanner = QPushButton("🟢 Puxar Folha (Automático)")
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
    # CÉREBRO TURBO: CAÇA O CANON E CONFIGURA HARDWARE
    # ==========================================
    def comunicar_com_hardware(self):
        try:
            pythoncom.CoInitialize()

            if os.path.exists(self.arquivo_temp):
                os.remove(self.arquivo_temp)

            gerenciador = win32com.client.Dispatch("WIA.DeviceManager")

            canon_info = None
            for info in gerenciador.DeviceInfos:
                for prop in info.Properties:
                    if prop.PropertyID == 7:
                        nome = str(prop.Value).upper()
                        if "CANON" in nome or "C240" in nome or "DR" in nome:
                            canon_info = info
                            break
                if canon_info:
                    break

            if not canon_info:
                QMessageBox.warning(self, "Scanner Offline",
                                    "O sistema não localizou o Canon DR-C240. Verifique se ele está ligado.")
                return

            dispositivo = canon_info.Connect()
            item = dispositivo.Items[1]

            # --- INÍCIO DA MÁGICA: FORÇANDO OS PARÂMETROS DO SCANNER ---
            def set_config(prop_id, value):
                try:
                    for prop in item.Properties:
                        if prop.PropertyID == prop_id:
                            prop.Value = value
                            break
                except:
                    pass  # Alguns drivers bloqueiam certas propriedades, o 'pass' impede o sistema de travar

            # 1. Modo de Cor (6146: 1=Colorido, 2=Escala de Cinza, 4=Preto e Branco)
            set_config(6146, 1)

            # 2. Qualidade / DPI (6147=Horizontal, 6148=Vertical) - Padrão Cartório: 300 DPI
            set_config(6147, 300)
            set_config(6148, 300)

            # 3. Tamanho do Papel - Padrão A4
            set_config(3098, 1)  # Tenta forçar o código de página A4 padrão do Windows (1 = WIA_PAGE_A4)
            # Se a impressora não aceitar o 3098, forçamos pelas dimensões em pixels (A4 em 300 DPI):
            set_config(6151, 2480)  # Largura (Pixels)
            set_config(6152, 3508)  # Altura (Pixels)
            # --- FIM DA MÁGICA ---

            cd = win32com.client.Dispatch("WIA.CommonDialog")
            imagem_bruta = cd.ShowTransfer(item, "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}", False)

            if imagem_bruta:
                imagem_bruta.SaveFile(self.arquivo_temp)

                pixmap = QPixmap(self.arquivo_temp)
                pixmap_ajustado = pixmap.scaled(450, 450, Qt.AspectRatioMode.KeepAspectRatio,
                                                Qt.TransformationMode.SmoothTransformation)
                self.lbl_imagem.setPixmap(pixmap_ajustado)

                self.input_nome.setEnabled(True)
                self.btn_salvar.setEnabled(True)
                self.input_nome.setFocus()
                self.btn_acionar_scanner.setText("🔄 Puxar Próxima Folha")

        except Exception as e:
            msg = str(e)
            if "80210003" in msg:
                QMessageBox.warning(self, "Bandeja Vazia",
                                    "Não há papel no alimentador do Canon DR-C240.\nColoque o documento e tente de novo.")
            else:
                QMessageBox.critical(self, "Falha de Leitura",
                                     f"O Canon não respondeu ao comando de digitalização.\nDetalhe técnico: {msg}")

    # ==========================================
    # SALVA NA PASTA CORRETA
    # ==========================================
    def salvar_no_processo(self):
        nome_digitado = self.input_nome.text().strip()
        if not nome_digitado:
            QMessageBox.warning(self, "Aviso", "Por favor, digite um nome para o documento (ex: Identidade).")
            return

        nome_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_digitado)
        nome_final = f"{nome_limpo}.jpg"
        caminho_final = os.path.join(self.pasta_destino, nome_final)

        try:
            shutil.move(self.arquivo_temp, caminho_final)
            QMessageBox.information(self, "Sucesso", "Documento salvo na Ficha do Cliente!")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Falha ao salvar arquivo final:\n{e}")