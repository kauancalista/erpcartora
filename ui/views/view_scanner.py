import os
import re
import fitz  # PyMuPDF
import winocr
import asyncio
from PIL import Image
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QListWidget, QListWidgetItem,
                             QComboBox, QLineEdit, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QImage, QPixmap, QCursor

from database.conexao import SessionLocal
from database.modelos import Processo
from rapidfuzz import fuzz


class TelaScanner(QWidget):
    def __init__(self):
        super().__init__()

        self.arquivos_na_fila = []
        self.arquivo_selecionado = None
        self.processos_ativos_cache = []

        self.setStyleSheet("""
            QListWidget { background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 8px; color: white; padding: 5px; outline: none; font-size: 13px; }
            QListWidget::item { padding: 12px; border-bottom: 1px solid #1E2532; }
            QListWidget::item:selected { background-color: #2962FF; border-radius: 4px; font-weight: bold; }
            QLineEdit, QComboBox { background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; color: white; padding: 10px; font-size: 13px; }
            QLineEdit:focus, QComboBox:focus { border: 1px solid #2962FF; }
        """)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(30, 30, 30, 30)

        # --- CABEÇALHO ---
        layout_topo = QVBoxLayout()
        lbl_titulo = QLabel("🖨️ Central de Digitalização e OCR Lote (Windows Nativo)")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        lbl_sub = QLabel(
            "Digitalize dezenas de documentos. O sistema lê os títulos, renomeia e arquiva nos processos ativos usando o motor do Windows.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8A92A6; margin-bottom: 15px;")
        layout_topo.addWidget(lbl_titulo)
        layout_topo.addWidget(lbl_sub)
        layout_principal.addLayout(layout_topo)

        # --- CORPO (3 COLUNAS) ---
        layout_corpo = QHBoxLayout()

        # COLUNA 1: FILA DE ENTRADA (INBOX)
        painel_inbox = QFrame()
        painel_inbox.setStyleSheet("background-color: #11151F; border-radius: 12px; border: 1px solid #1E2532;")
        layout_inbox = QVBoxLayout(painel_inbox)

        lbl_inbox = QLabel("📥 Caixa de Entrada (Scanner)")
        lbl_inbox.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout_inbox.addWidget(lbl_inbox)

        box_botoes_scan = QHBoxLayout()
        btn_scan = QPushButton("Escanear Páginas")
        btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_scan.setStyleSheet(
            "background-color: #8E44AD; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_scan.clicked.connect(self.acionar_scanner_fisico)

        btn_processar_fila = QPushButton("🧠 Processar Fila (OCR)")
        btn_processar_fila.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_processar_fila.setStyleSheet(
            "background-color: #E67E22; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_processar_fila.clicked.connect(self.processar_fila_ocr)

        box_botoes_scan.addWidget(btn_scan)
        box_botoes_scan.addWidget(btn_processar_fila)
        layout_inbox.addLayout(box_botoes_scan)

        self.lista_inbox = QListWidget()
        self.lista_inbox.itemClicked.connect(self.selecionar_documento)
        layout_inbox.addWidget(self.lista_inbox)

        layout_corpo.addWidget(painel_inbox, 3)

        # COLUNA 2: INTELIGÊNCIA E ROTEAMENTO
        painel_ocr = QFrame()
        painel_ocr.setStyleSheet("background-color: #11151F; border-radius: 12px; border: 1px solid #1E2532;")
        layout_ocr = QVBoxLayout(painel_ocr)

        lbl_roteamento = QLabel("📂 Triagem Automática")
        lbl_roteamento.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout_ocr.addWidget(lbl_roteamento)

        layout_ocr.addWidget(QLabel("Novo Nome do Arquivo:"))
        self.inp_nome_doc = QLineEdit()
        self.inp_nome_doc.setPlaceholderText("Ex: CERTIDAO_DE_CASAMENTO_ADAILTON_SEVERINA")
        layout_ocr.addWidget(self.inp_nome_doc)

        layout_ocr.addWidget(QLabel("Vincular ao Processo (Se Ativo):"))
        self.combo_processos = QComboBox()
        self.carregar_processos_ativos()
        layout_ocr.addWidget(self.combo_processos)

        layout_ocr.addSpacing(15)
        layout_ocr.addWidget(QLabel("Texto Identificado (OCR):"))
        self.txt_ocr_preview = QLabel("Nenhum texto extraído ainda.")
        self.txt_ocr_preview.setStyleSheet(
            "color: #8A92A6; font-size: 11px; font-family: Consolas; border: 1px dashed #2C364C; padding: 10px; border-radius: 4px;")
        self.txt_ocr_preview.setWordWrap(True)
        self.txt_ocr_preview.setFixedHeight(120)
        self.txt_ocr_preview.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout_ocr.addWidget(self.txt_ocr_preview)

        layout_ocr.addStretch()

        self.btn_salvar = QPushButton("💾 Arquivar (Pressione ENTER)")
        self.btn_salvar.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_salvar.setStyleSheet(
            "background-color: #27AE60; color: white; font-weight: bold; padding: 15px; border-radius: 6px; font-size: 14px;")
        self.btn_salvar.clicked.connect(self.salvar_e_arquivar)
        layout_ocr.addWidget(self.btn_salvar)

        layout_corpo.addWidget(painel_ocr, 3)

        # COLUNA 3: PREVIEW DO DOCUMENTO
        painel_preview = QFrame()
        painel_preview.setStyleSheet("background-color: #0B0E14; border-radius: 12px; border: 1px solid #1E2532;")
        layout_preview = QVBoxLayout(painel_preview)

        self.scroll_preview = QScrollArea()
        self.scroll_preview.setWidgetResizable(True)
        self.scroll_preview.setStyleSheet("border: none;")

        self.lbl_imagem_preview = QLabel("Selecione um arquivo na fila para visualizar.")
        self.lbl_imagem_preview.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_imagem_preview.setStyleSheet("color: #8A92A6;")

        self.scroll_preview.setWidget(self.lbl_imagem_preview)
        layout_preview.addWidget(self.scroll_preview)

        layout_corpo.addWidget(painel_preview, 4)

        layout_principal.addLayout(layout_corpo)

    # Captura o ENTER do teclado para agilizar o trabalho
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.arquivo_selecionado:
                self.salvar_e_arquivar()
        else:
            super().keyPressEvent(event)

    # ==========================================
    # BANCO DE DADOS E SCANNER
    # ==========================================
    def carregar_processos_ativos(self):
        """Busca no banco APENAS processos ativos"""
        self.combo_processos.clear()
        self.processos_ativos_cache = []

        db = SessionLocal()
        ativos = db.query(Processo).filter(Processo.status.notin_(["Arquivado", "CRAS", "Entregue"])).all()
        db.close()

        self.combo_processos.addItem("Nenhum (Salvar em Documentos Avulsos)", None)
        for p in ativos:
            texto = f"Proc. {p.id:03d} - {p.nome_cliente}"
            self.combo_processos.addItem(texto, p)
            self.processos_ativos_cache.append(p)

    def acionar_scanner_fisico(self):
        """Conecta no Scanner pelo Windows WIA"""
        try:
            import win32com.client
            QMessageBox.information(self, "Scanner", "Aguardando Scanner... Selecione a impressora na janela a seguir.")

            wia = win32com.client.Dispatch("WIA.CommonDialog")
            # Loop para permitir escanear várias páginas seguidas
            while True:
                imagem = wia.ShowAcquireImage()
                if not imagem: break  # O usuário cancelou ou terminou

                pasta_temp = os.path.join(os.getcwd(), "temp_scanner")
                os.makedirs(pasta_temp, exist_ok=True)

                nome_arq = f"Scan_{int(datetime.now().timestamp())}.jpg"
                caminho_completo = os.path.join(pasta_temp, nome_arq)

                if os.path.exists(caminho_completo): os.remove(caminho_completo)
                imagem.SaveFile(caminho_completo)

                # Adiciona na fila com um dicionário de metadados
                self.arquivos_na_fila.append(
                    {"caminho": caminho_completo, "nome_sugerido": nome_arq, "ocr_feito": False, "processo_index": 0})

            self.atualizar_lista_inbox()

        except Exception as e:
            QMessageBox.warning(self, "Aviso", f"Não foi possível conectar ao Scanner.\nDetalhe: {e}")

    # ==========================================
    # A INTELIGÊNCIA ARTIFICIAL (REGEX + WIN OCR)
    # ==========================================
    def processar_fila_ocr(self):
        """Roda a inteligência do Windows OCR em todos os documentos da fila de uma vez"""
        if not self.arquivos_na_fila: return
        self.txt_ocr_preview.setText("Processando fila inteira... Aguarde.")

        for item in self.arquivos_na_fila:
            if item["ocr_feito"]: continue

            # 1. Abre a Imagem
            caminho = item["caminho"]
            try:
                if caminho.lower().endswith(".pdf"):
                    doc = fitz.open(caminho)
                    pix = doc[0].get_pixmap()
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                else:
                    img = Image.open(caminho)
            except:
                continue

            # 2. LÊ O TEXTO COM O OCR NATIVO DO WINDOWS (100% Offline)
            try:
                # O winocr exige que a chamada seja assíncrona, então usamos asyncio
                resultado_ocr = asyncio.run(winocr.recognize_pil_image(img))
                texto_extraido = resultado_ocr.text if resultado_ocr else ""
            except Exception as e:
                texto_extraido = ""

            texto_limpo = " ".join(texto_extraido.split()).upper()
            item["texto_ocr"] = texto_limpo

            # 3. REGEX PARA ACHAR O TÍTULO FIXO (Ex: CERTIDÃO DE NASCIMENTO)
            padrao_titulo = r'(CERTIDÃO DE NASCIMENTO|CERTIDÃO DE CASAMENTO|CERTIDÃO DE ÓBITO|CERTIDAO DE NASCIMENTO|CERTIDAO DE CASAMENTO|CERTIDAO DE OBITO)'
            busca_titulo = re.search(padrao_titulo, texto_limpo, re.IGNORECASE)

            tipo_doc = "DOCUMENTO_DIGITALIZADO"
            if busca_titulo:
                tipo_doc = busca_titulo.group(0).replace(" ", "_").upper()
                tipo_doc = tipo_doc.replace("CERTIDÃO", "CERTIDAO").replace("ÓBITO", "OBITO")

            # 4. ACHAR O PROCESSO ATIVO CORRESPONDENTE (Fuzzy Match)
            melhor_score = 0
            melhor_index = 0
            nome_cliente_achado = ""

            for i, proc in enumerate(self.processos_ativos_cache, start=1):  # start=1 porque o 0 é o "Avulsos"
                score = fuzz.partial_ratio(proc.nome_cliente.upper(), texto_limpo)
                if score > 80:  # Se bater mais de 80%, achou o cliente!
                    if score > melhor_score:
                        melhor_score = score
                        melhor_index = i
                        nome_cliente_achado = proc.nome_cliente.replace(" ", "_").upper()

            # 5. MONTA O NOME FINAL SUGERIDO
            if nome_cliente_achado:
                item["nome_sugerido"] = f"{tipo_doc}_{nome_cliente_achado}"
                item["processo_index"] = melhor_index
            else:
                item["nome_sugerido"] = f"{tipo_doc}_NOME_NAO_IDENTIFICADO"
                item["processo_index"] = 0  # Fica no Documentos Avulsos

            item["ocr_feito"] = True

        self.atualizar_lista_inbox()
        self.txt_ocr_preview.setText("Processamento concluído! Clique nos itens para arquivar.")

        # Auto-seleciona o primeiro da lista
        if self.lista_inbox.count() > 0:
            self.lista_inbox.setCurrentRow(0)
            self.selecionar_documento(self.lista_inbox.item(0))

    def atualizar_lista_inbox(self):
        self.lista_inbox.clear()
        for item_data in self.arquivos_na_fila:
            icone = "✅" if item_data["ocr_feito"] else "⏳"
            item = QListWidgetItem(f"{icone} {item_data['nome_sugerido']}")
            item.setData(Qt.ItemDataRole.UserRole, item_data)
            self.lista_inbox.addItem(item)

    def selecionar_documento(self, item):
        item_data = item.data(Qt.ItemDataRole.UserRole)
        self.arquivo_selecionado = item_data

        # Preenche os campos do meio com o que a IA achou
        self.inp_nome_doc.setText(item_data["nome_sugerido"])
        self.combo_processos.setCurrentIndex(item_data["processo_index"])

        if "texto_ocr" in item_data:
            amostra = item_data["texto_ocr"][:200] + "..."
            self.txt_ocr_preview.setText(amostra)
            self.txt_ocr_preview.setStyleSheet(
                "color: #2ECC71; font-size: 11px; font-family: Consolas; border: 1px dashed #27AE60; padding: 10px; border-radius: 4px;")
        else:
            self.txt_ocr_preview.setText("Clique em 'Processar Fila' para ler o texto.")
            self.txt_ocr_preview.setStyleSheet(
                "color: #8A92A6; font-size: 11px; font-family: Consolas; border: 1px dashed #2C364C; padding: 10px; border-radius: 4px;")

        # Renderiza a Imagem Gigante na Direita
        try:
            doc = fitz.open(item_data["caminho"])
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)

            self.lbl_imagem_preview.setPixmap(QPixmap.fromImage(img))
            self.lbl_imagem_preview.setScaledContents(True)
        except:
            self.lbl_imagem_preview.setText("Erro ao carregar visualização.")

    # ==========================================
    # ARQUIVAMENTO FINAL
    # ==========================================

    def salvar_e_arquivar(self):
        if not self.arquivo_selecionado: return

        nome_doc = self.inp_nome_doc.text().strip()
        if not nome_doc:
            QMessageBox.warning(self, "Aviso", "O documento precisa ter um nome.")
            return

        processo = self.combo_processos.currentData()

        # === A PONTE: PUXA DA TELA DE CONFIGURAÇÕES ===
        import json
        pasta_base_cartorio = os.path.join(os.getcwd(), "Arquivos_Cartorio")
        try:
            with open(os.path.join(os.getcwd(), "config", "app_config.json"), "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if cfg.get("pasta_processos"): pasta_base_cartorio = cfg["pasta_processos"]
        except:
            pass
        # ===============================================

        if processo:
            nome_pasta_destino = f"Proc_{processo.id:03d}_{processo.nome_cliente.replace(' ', '_').upper()}"
            pasta_destino = os.path.join(pasta_base_cartorio, nome_pasta_destino)
            tipo_no_banco = "Documento Digitalizado (Anexo)"
        else:
            pasta_destino = os.path.join(pasta_base_cartorio, "Documentos_Avulsos")
            tipo_no_banco = None

        os.makedirs(pasta_destino, exist_ok=True)

        # Trata o nome do PDF (Para não sobrescrever se tiver 2 com mesmo nome)
        caminho_pdf_final = os.path.join(pasta_destino, f"{nome_doc}.pdf")
        contador = 1
        while os.path.exists(caminho_pdf_final):
            caminho_pdf_final = os.path.join(pasta_destino, f"{nome_doc}_pg{contador}.pdf")
            contador += 1

        try:
            # Converte a Foto escaneada para PDF Oficial
            doc = fitz.open()
            caminho_original = self.arquivo_selecionado["caminho"]

            if caminho_original.lower().endswith(('.png', '.jpg', '.jpeg')):
                img_pdf = fitz.open(caminho_original)
                pdf_bytes = img_pdf.convert_to_pdf()
                img_pdf.close()
                pdf_temporario = fitz.open("pdf", pdf_bytes)
                doc.insert_pdf(pdf_temporario)
            else:
                pdf_existente = fitz.open(caminho_original)
                doc.insert_pdf(pdf_existente)

            doc.save(caminho_pdf_final)
            doc.close()

            # Deleta a foto temporária original
            if os.path.exists(caminho_original):
                os.remove(caminho_original)

            # Só vincula no banco de dados se for um processo ativo!
            if processo:
                from database.crud import adicionar_documento
                db = SessionLocal()
                # Salva no banco apontando pro novo PDF renomeado
                adicionar_documento(db, processo.id, os.path.basename(caminho_pdf_final), tipo_no_banco,
                                    caminho_pdf_final)
                db.close()

            # Remove da Fila e Pula pro próximo
            self.arquivos_na_fila.remove(self.arquivo_selecionado)
            self.arquivo_selecionado = None
            self.lbl_imagem_preview.clear()
            self.inp_nome_doc.clear()
            self.txt_ocr_preview.setText("Arquivado com sucesso!")
            self.combo_processos.setCurrentIndex(0)

            self.atualizar_lista_inbox()

            # Se ainda tiver arquivo na fila, seleciona o próximo automaticamente!
            if self.lista_inbox.count() > 0:
                self.lista_inbox.setCurrentRow(0)
                self.selecionar_documento(self.lista_inbox.item(0))

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar arquivo:\n{str(e)}")