import os
import re
import fitz  # PyMuPDF
import asyncio
import threading
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QListWidget, QListWidgetItem,
                             QComboBox, QLineEdit, QMessageBox, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap, QCursor
from database.conexao import SessionLocal
from database.modelos import Processo
from rapidfuzz import fuzz

# Import do nosso servidor Flask com a função de LIGAR e PARAR
from core.servidor_mobile import iniciar_flask, parar_flask

# Bibliotecas do Windows Native OCR (Motor Oficial da Microsoft)
from winsdk.windows.media.ocr import OcrEngine
from winsdk.windows.storage import StorageFile
from winsdk.windows.graphics.imaging import BitmapDecoder


class TelaScanner(QWidget):
    def __init__(self):
        super().__init__()
        self.arquivos_na_fila = []
        self.arquivo_selecionado = None
        self.processos_ativos_cache = []

        # Variáveis de controle do Celular
        self.servidor_ligado = False
        self.timer_mobile = QTimer()
        self.timer_mobile.timeout.connect(self.puxar_fotos_do_celular)

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
        lbl_titulo = QLabel("🖨️ Central de Digitalização e OCR Lote (Canon & Mobile)")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        lbl_sub = QLabel("Digitalize via alimentador ou celular. Nomes extraídos limpos e com espaçamento padrão.")
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

        lbl_inbox = QLabel("📥 Caixa de Entrada")
        lbl_inbox.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout_inbox.addWidget(lbl_inbox)

        box_botoes_scan = QHBoxLayout()
        btn_scan = QPushButton("🖨️ Escanear Lote")
        btn_scan.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_scan.setStyleSheet(
            "background-color: #8E44AD; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_scan.clicked.connect(self.acionar_scanner_fisico)

        self.btn_mobile = QPushButton("📱 Ligar Celular")
        self.btn_mobile.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_mobile.setStyleSheet(
            "background-color: #2980B9; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        self.btn_mobile.clicked.connect(self.toggle_servidor)

        box_botoes_scan.addWidget(btn_scan)
        box_botoes_scan.addWidget(self.btn_mobile)
        layout_inbox.addLayout(box_botoes_scan)

        btn_processar_fila = QPushButton("🧠 Processar Fila (OCR)")
        btn_processar_fila.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_processar_fila.setStyleSheet(
            "background-color: #E67E22; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
        btn_processar_fila.clicked.connect(self.processar_fila_ocr)
        layout_inbox.addWidget(btn_processar_fila)

        self.lbl_status_mobile = QLabel("")
        self.lbl_status_mobile.setStyleSheet("color: #8A92A6; font-size: 11px; font-weight: bold;")
        self.lbl_status_mobile.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout_inbox.addWidget(self.lbl_status_mobile)

        self.lista_inbox = QListWidget()
        self.lista_inbox.itemClicked.connect(self.selecionar_documento)
        layout_inbox.addWidget(self.lista_inbox)
        layout_corpo.addWidget(painel_inbox, 3)

        # COLUNA 2: INTELIGÊNCIA E ROTEAMENTO
        painel_ocr = QFrame()
        painel_ocr.setStyleSheet("background-color: #11151F; border-radius: 12px; border: 1px solid #1E2532;")
        layout_ocr = QVBoxLayout(painel_ocr)

        lbl_roteamento = QLabel("🔄 Triagem Automática")
        lbl_roteamento.setStyleSheet("font-size: 16px; font-weight: bold; border: none;")
        layout_ocr.addWidget(lbl_roteamento)

        layout_ocr.addWidget(QLabel("Novo Nome do Arquivo:"))
        self.inp_nome_doc = QLineEdit()
        self.inp_nome_doc.setPlaceholderText("Ex: CERTIDÃO DE CASAMENTO - MARIA SILVA E JOÃO SOUZA")
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
        self.txt_ocr_preview.setFixedHeight(140)
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

    # ==========================================
    # LÓGICA DE INTEGRAÇÃO COM O CELULAR
    # ==========================================

    def obter_ip_local(self):
        import socket
        try:
            # Cria uma conexão fantasma com o DNS do Google para forçar o Windows a revelar o IP real da rede local
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"  # IP de segurança caso o PC esteja sem internet

    def toggle_servidor(self):
        if not self.servidor_ligado:
            # LIGAR
            self.thread_servidor = threading.Thread(target=iniciar_flask, daemon=True)
            self.thread_servidor.start()

            self.timer_mobile.start(2000)
            self.servidor_ligado = True

            # Puxa o IP real da máquina na rede na hora H
            ip_atual = self.obter_ip_local()

            self.btn_mobile.setText("📱 Desativar Celular")
            self.btn_mobile.setStyleSheet(
                "background-color: #E74C3C; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")

            # Mostra o endereço exato que deve ser digitado no celular
            self.lbl_status_mobile.setText(f"Acesse no celular:\nhttps://{ip_atual}:5000")
            self.lbl_status_mobile.setStyleSheet("color: #2ECC71; font-size: 13px; font-weight: bold;")
        else:
            # DESLIGAR
            self.timer_mobile.stop()
            parar_flask()  # Desliga o servidor Flask
            self.servidor_ligado = False

            self.btn_mobile.setText("📱 Ligar Celular")
            self.btn_mobile.setStyleSheet(
                "background-color: #2980B9; color: white; font-weight: bold; padding: 10px; border-radius: 6px;")
            self.lbl_status_mobile.setText("Celular desativado.")
            self.lbl_status_mobile.setStyleSheet("color: #8A92A6; font-size: 11px; font-weight: bold;")

    def puxar_fotos_do_celular(self):
        pasta_recebidos = os.path.join(os.getcwd(), "documentos_recebidos")
        pasta_temp = os.path.join(os.getcwd(), "temp_scanner")
        os.makedirs(pasta_recebidos, exist_ok=True)
        os.makedirs(pasta_temp, exist_ok=True)

        arquivos_na_pasta = [f for f in os.listdir(pasta_recebidos) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

        if arquivos_na_pasta:
            novos = False
            for arq in arquivos_na_pasta:
                caminho_origem = os.path.join(pasta_recebidos, arq)
                nome_arq_seguro = f"Mobile_{int(datetime.now().timestamp())}_{arq}"
                caminho_destino = os.path.join(pasta_temp, nome_arq_seguro)

                try:
                    shutil.move(caminho_origem, caminho_destino)
                    # Pega apenas o que o cara digitou no app sem a extensão
                    nome_limpo = arq.rsplit('.', 1)[0]

                    self.arquivos_na_fila.append({
                        "caminho": caminho_destino,
                        "nome_sugerido": nome_limpo,
                        "origem": "mobile",
                        "ocr_feito": False,
                        "processo_index": 0
                    })
                    novos = True
                except Exception:
                    pass
            if novos:
                self.atualizar_lista_inbox()

    # ==========================================
    # EVENTOS BÁSICOS
    # ==========================================
    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            if self.arquivo_selecionado:
                self.salvar_e_arquivar()
        else:
            super().keyPressEvent(event)

    def carregar_processos_ativos(self):
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
        self.inp_nome_doc.setText(item_data["nome_sugerido"])
        self.combo_processos.setCurrentIndex(item_data["processo_index"])

        if "texto_ocr" in item_data:
            amostra = item_data["texto_ocr"][:200] + "..."
            nome_fisgado = item_data.get("nome_extraido", "")
            if nome_fisgado:
                amostra = f"🎯 [NOME EXTRAÍDO DO PAPEL: {nome_fisgado}]\n\n" + amostra

            self.txt_ocr_preview.setText(amostra)
            if "ERRO" in item_data["texto_ocr"] or "FALHA" in item_data["texto_ocr"]:
                self.txt_ocr_preview.setStyleSheet(
                    "color: #E74C3C; font-size: 11px; font-family: Consolas; border: 1px dashed #E74C3C; padding: 10px; border-radius: 4px;")
            else:
                self.txt_ocr_preview.setStyleSheet(
                    "color: #2ECC71; font-size: 11px; font-family: Consolas; border: 1px dashed #27AE60; padding: 10px; border-radius: 4px;")
        else:
            self.txt_ocr_preview.setText("Clique em 'Processar Fila' para ler o texto.")
            self.txt_ocr_preview.setStyleSheet(
                "color: #8A92A6; font-size: 11px; font-family: Consolas; border: 1px dashed #2C364C; padding: 10px; border-radius: 4px;")

        try:
            import fitz
            doc = fitz.open(item_data["caminho"])
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5))
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            self.lbl_imagem_preview.setPixmap(QPixmap.fromImage(img))
            self.lbl_imagem_preview.setScaledContents(True)
        except:
            self.lbl_imagem_preview.setText("Erro ao carregar visualização.")

    # ==========================================
    # LÓGICA DO SCANNER FÍSICO
    # ==========================================
    def acionar_scanner_fisico(self):
        try:
            import pythoncom
            import win32com.client
            pythoncom.CoInitialize()

            gerenciador = win32com.client.Dispatch("WIA.DeviceManager")
            canon_info = None

            for info in gerenciador.DeviceInfos:
                for prop in info.Properties:
                    if prop.PropertyID == 7:
                        nome = str(prop.Value).upper()
                        if "CANON" in nome or "C240" in nome or "DR" in nome:
                            canon_info = info
                            break
                if canon_info: break

            if not canon_info:
                QMessageBox.warning(self, "Scanner Offline", "Canon DR-C240 não encontrado na rede/USB.")
                return

            dispositivo = canon_info.Connect()
            item = dispositivo.Items[1]

            def set_config(prop_id, value):
                try:
                    for prop in item.Properties:
                        if prop.PropertyID == prop_id:
                            prop.Value = value
                            break
                except:
                    pass

            set_config(6146, 1)
            set_config(6147, 300)
            set_config(6148, 300)
            set_config(3098, 1)
            set_config(6151, 2480)
            set_config(6152, 3508)

            cd = win32com.client.Dispatch("WIA.CommonDialog")
            pasta_temp = os.path.join(os.getcwd(), "temp_scanner")
            os.makedirs(pasta_temp, exist_ok=True)

            paginas_lidas = 0
            while True:
                try:
                    imagem = cd.ShowTransfer(item, "{B96B3CAE-0728-11D3-9D7B-0000F81EF32E}", False)
                    if not imagem: break

                    nome_arq = f"Scan_{int(datetime.now().timestamp())}_{paginas_lidas}.jpg"
                    caminho_completo = os.path.join(pasta_temp, nome_arq)

                    if os.path.exists(caminho_completo): os.remove(caminho_completo)
                    imagem.SaveFile(caminho_completo)

                    self.arquivos_na_fila.append({
                        "caminho": caminho_completo,
                        "nome_sugerido": nome_arq,
                        "origem": "canon",
                        "ocr_feito": False,
                        "processo_index": 0
                    })
                    paginas_lidas += 1

                except Exception as ex:
                    msg_erro = str(ex).lower()
                    if "80210003" in msg_erro or "-2145320957" in msg_erro or "alimentador" in msg_erro:
                        break
                    else:
                        raise ex

            self.atualizar_lista_inbox()

            if paginas_lidas > 0:
                QMessageBox.information(self, "Sucesso",
                                        f"Digitalização em lote concluída!\n{paginas_lidas} página(s).")
            else:
                QMessageBox.warning(self, "Bandeja Vazia", "Não havia papel no alimentador do Canon.")

        except Exception as e:
            QMessageBox.warning(self, "Aviso do Scanner", f"Falha de comunicação:\n{e}")

    # ==========================================
    # LÓGICA DO OCR DA MICROSOFT
    # ==========================================
    async def extrair_texto_winsdk(self, caminho_imagem):
        try:
            arquivo = await StorageFile.get_file_from_path_async(os.path.abspath(caminho_imagem))
            stream = await arquivo.open_async(0)
            decoder = await BitmapDecoder.create_async(stream)
            software_bitmap = await decoder.get_software_bitmap_async()
            engine = OcrEngine.try_create_from_user_profile_languages()
            if not engine:
                return "[ERRO: Motor de OCR do Windows não encontrado]"
            resultado = await engine.recognize_async(software_bitmap)

            if resultado and resultado.lines:
                texto_formatado = "\n".join([linha.text.strip() for linha in resultado.lines if linha.text.strip()])
                return texto_formatado
            return ""
        except Exception as e:
            return f"[ERRO INTERNO WINSDK: {str(e)}]"

    # ==========================================
    # INTELIGÊNCIA: ROTEAMENTO OCR
    # ==========================================
    def processar_fila_ocr(self):
        if not self.arquivos_na_fila: return
        self.txt_ocr_preview.setText("Lendo lote inteiro... Aguarde.")

        if os.name == 'nt': asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        for item in self.arquivos_na_fila:
            if item["ocr_feito"]: continue

            caminho_jpg = item["caminho"]
            if caminho_jpg.lower().endswith(".pdf"):
                try:
                    doc = fitz.open(caminho_jpg)
                    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
                    caminho_jpg = caminho_jpg.replace(".pdf", "_temp_ocr.jpg")
                    pix.save(caminho_jpg)
                except:
                    pass

            try:
                texto_extraido = asyncio.run(self.extrair_texto_winsdk(caminho_jpg))
            except Exception as e:
                texto_extraido = f"[FALHA NA INTEGRAÇÃO: {str(e)}]"

            texto_multilinha = texto_extraido.upper()
            linhas_reais = [linha.strip() for linha in texto_multilinha.split('\n') if linha.strip()]
            texto_limpo = " ".join(linhas_reais)
            item["texto_ocr"] = texto_limpo

            texto_busca_processo = item["nome_sugerido"].upper() if item.get("origem") == "mobile" else texto_limpo

            melhor_score = 0
            melhor_index = 0

            # 1. TENTA ACHAR NO BANCO DE DADOS PRIMEIRO
            for i, proc in enumerate(self.processos_ativos_cache, start=1):
                nome_proc = proc.nome_cliente.upper()

                # PROTEÇÃO CONTRA O "BUG DO S": Ignora processos com nome de teste muito curto (ex: "S", "A")
                if len(nome_proc) <= 3: continue

                # Usamos token_set_ratio! Ele é imune a falhas de OCR (mistura de palavras).
                score = fuzz.token_set_ratio(nome_proc, texto_busca_processo)
                if score > 80 and score > melhor_score:
                    melhor_score = score
                    melhor_index = i

            # 2. SE NÃO TEM PROCESSO (OU VEIO DO SCANNER CANON), EXTRAI O NOME DO PAPEL
            if item.get("origem") != "mobile":
                if melhor_index > 0:
                    nome_final_arquivo = self.processos_ativos_cache[melhor_index - 1].nome_cliente.upper()
                else:
                    nome_final_arquivo = ""
                    # Filtro anti-sujeira de cartório
                    termos_ignorados = {
                        "REPUBLICA", "REPÚBLICA", "FEDERATIVA", "BRASIL", "REGISTRO", "CIVIL",
                        "PESSOAS", "NATURAIS", "CERTIDAO", "CERTIDÃO", "CASAMENTO", "NASCIMENTO",
                        "OBITO", "ÓBITO", "NUMERO", "NÚMERO", "CPF", "MATRICULA", "MATRÍCULA",
                        "LIVRO", "FOLHA", "FOLHAS", "TERMO", "NOME", "ATUAL", "CONJUGE", "CÔNJUGE",
                        "CONJUGES", "CÔNJUGES", "CON", "CÔN", "VARA", "JUIZO", "JUÍZO",
                        "COMARCA", "MUNICIPIO", "MUNICÍPIO", "ESTADO", "CARTORIO", "CARTÓRIO",
                        "DOC", "DOCUMENTO", "DOS", "DAS", "AOS", "DIAS", "MES", "MÊS", "ANO",
                        "JANEIRO", "FEVEREIRO", "MARCO", "MARÇO", "ABRIL", "MAIO", "JUNHO",
                        "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO", "DATA",
                        "LAVRADO", "SOB", "LOCAL"
                    }

                    for linha in linhas_reais:
                        l_limpa = re.sub(r'[^A-ZÀ-Ÿ ]', '', linha).strip()
                        l_limpa = re.sub(r'\s+', ' ', l_limpa)
                        if len(l_limpa) < 8: continue  # Linhas curtas demais são ignoradas

                        palavras = l_limpa.split()
                        boilers = [p for p in palavras if p in termos_ignorados or len(p) <= 2]

                        # Se mais da metade da linha for burocracia, essa linha é descartada
                        if len(boilers) >= len(palavras) / 2: continue

                        # Se a linha sobreviveu ao filtro e parece um nome, CAPTURA!
                        if len(palavras) >= 3 or " DE " in l_limpa or " DA " in l_limpa or " DOS " in l_limpa:
                            nome_final_arquivo = l_limpa
                            break

                    if not nome_final_arquivo:
                        nome_final_arquivo = "NAO IDENTIFICADO"

                item["nome_sugerido"] = nome_final_arquivo

            item["processo_index"] = melhor_index
            item["ocr_feito"] = True

        self.atualizar_lista_inbox()
        self.txt_ocr_preview.setText("Lote processado! Nomes extraídos inteligentemente.")

        if self.lista_inbox.count() > 0:
            self.lista_inbox.setCurrentRow(0)
            self.selecionar_documento(self.lista_inbox.item(0))
    # ==========================================
    # SALVAMENTO FINAL
    # ==========================================
# ==========================================
    # SALVAMENTO FINAL (CORRIGIDO OS UNDERLINES)
    # ==========================================
    def salvar_e_arquivar(self):
        if not self.arquivo_selecionado: return

        nome_doc = self.inp_nome_doc.text().strip()
        if not nome_doc:
            QMessageBox.warning(self, "Aviso", "O documento precisa ter um nome.")
            return

        processo = self.combo_processos.currentData()
        import json
        pasta_base_cartorio = os.path.join(os.getcwd(), "Arquivos_Cartorio")
        try:
            with open(os.path.join(os.getcwd(), "config", "app_config.json"), "r", encoding="utf-8") as f:
                cfg = json.load(f)
                if cfg.get("pasta_processos"): pasta_base_cartorio = cfg["pasta_processos"]
        except:
            pass

        if processo:
            # Mantém underscore apenas no nome da pasta para o sistema organizar melhor
            nome_pasta_destino = f"Proc_{processo.id:03d}_{processo.nome_cliente.replace(' ', '_').upper()}"
            pasta_destino = os.path.join(pasta_base_cartorio, nome_pasta_destino)
            tipo_no_banco = "Documento Digitalizado"
        else:
            pasta_destino = os.path.join(pasta_base_cartorio, "Documentos_Avulsos")
            tipo_no_banco = None

        os.makedirs(pasta_destino, exist_ok=True)

        # CORREÇÃO AQUI: Tira apenas caracteres proibidos do Windows, MAS MANTÉM OS ESPAÇOS!
        nome_arquivo_seguro = re.sub(r'[\\/*?:"<>|]', "", nome_doc)
        caminho_pdf_final = os.path.join(pasta_destino, f"{nome_arquivo_seguro}.pdf")

        contador = 1
        while os.path.exists(caminho_pdf_final):
            # Se houver repetido, adiciona número separado por espaço (ex: FULANO 1.pdf)
            caminho_pdf_final = os.path.join(pasta_destino, f"{nome_arquivo_seguro} {contador}.pdf")
            contador += 1

        try:
            import fitz
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

            if os.path.exists(caminho_original):
                os.remove(caminho_original)

            if processo:
                from database.crud import adicionar_documento
                db = SessionLocal()
                # Salva no banco de dados com espaços normais
                adicionar_documento(db, processo.id, f"{nome_arquivo_seguro}.pdf", tipo_no_banco, caminho_pdf_final)
                db.close()

            self.arquivos_na_fila.remove(self.arquivo_selecionado)
            self.arquivo_selecionado = None
            self.lbl_imagem_preview.clear()
            self.inp_nome_doc.clear()
            self.txt_ocr_preview.setText("Arquivado com sucesso!")
            self.combo_processos.setCurrentIndex(0)
            self.atualizar_lista_inbox()

            if self.lista_inbox.count() > 0:
                self.lista_inbox.setCurrentRow(0)
                self.selecionar_documento(self.lista_inbox.item(0))

        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar arquivo:\n{str(e)}")