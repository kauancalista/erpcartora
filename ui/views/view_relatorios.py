import os
import fitz  # PyMuPDF
import json
import pandas as pd
import threading
from rapidfuzz import fuzz
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QLineEdit, QFileDialog,
                             QTextEdit, QMessageBox, QTreeView, QHeaderView)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QModelIndex, QDir
from PyQt6.QtGui import QCursor, QFileSystemModel


class LogSignal(QObject):
    update_log = pyqtSignal(str)


class TelaRelatorios(QWidget):
    def __init__(self):
        super().__init__()

        self.caminho_planilha = ""
        self.caminho_pasta_selecionada = ""
        self.pasta_saida = os.path.join(os.getcwd(), "Relatorios_Gerados")
        os.makedirs(self.pasta_saida, exist_ok=True)

        # =====================================================================
        # ⚠️ DEFINA AQUI O CAMINHO DA SUA PASTA RAIZ DO FERC
        # Exemplo: r"C:\Cartorio\FERC" ou r"D:\Documentos\Relatorios_Corregedoria"
        # =====================================================================
        self.diretorio_raiz = os.path.join(os.getcwd(), "Arquivos_Cartorio")  # Fallback padrão

        try:
            caminho_config = os.path.join(os.getcwd(), "config", "app_config.json")
            if os.path.exists(caminho_config):
                with open(caminho_config, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("pasta_ferc"):
                        self.diretorio_raiz = cfg["pasta_ferc"]
        except:
            pass

        os.makedirs(self.diretorio_raiz, exist_ok=True)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(20)

        # --- CABEÇALHO ---
        layout_topo = QVBoxLayout()
        lbl_titulo = QLabel("📊 Central de Relatórios e Auditoria (FERC / CRC)")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        lbl_sub = QLabel("Motor de fusão inteligente: resolve nomes duplos, mescla PDFs/Imagens e audita falhas.")
        lbl_sub.setStyleSheet("font-size: 13px; color: #8A92A6;")
        layout_topo.addWidget(lbl_titulo)
        layout_topo.addWidget(lbl_sub)
        layout_principal.addLayout(layout_topo)

        # --- CORPO DIVIDIDO EM DUAS COLUNAS ---
        layout_split = QHBoxLayout()
        layout_split.setSpacing(20)

        # COLUNA 1: NAVEGADOR DE ARQUIVOS (DIRETO NO APP)
        painel_arquivos = QFrame()
        painel_arquivos.setProperty("class", "painel")
        layout_arquivos = QVBoxLayout(painel_arquivos)
        layout_arquivos.setContentsMargins(15, 15, 15, 15)

        lbl_nav = QLabel("📁 Explorador do Cartório")
        lbl_nav.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-bottom: 5px;")
        layout_arquivos.addWidget(lbl_nav)

        # Modelo de Sistema de Arquivos
        self.modelo_fs = QFileSystemModel()
        self.modelo_fs.setRootPath(self.diretorio_raiz)
        self.modelo_fs.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files)

        # A Árvore de Arquivos (TreeView)
        self.tree_arquivos = QTreeView()
        self.tree_arquivos.setModel(self.modelo_fs)
        self.tree_arquivos.setRootIndex(self.modelo_fs.index(self.diretorio_raiz))
        self.tree_arquivos.setAnimated(True)
        self.tree_arquivos.setIndentation(20)
        self.tree_arquivos.setSortingEnabled(True)

        # --- O SEGREDO DO VISUAL LIMPO AQUI ---
        self.tree_arquivos.setHeaderHidden(True)  # Remove a barra cinza "Name"
        self.tree_arquivos.setColumnHidden(1, True)
        self.tree_arquivos.setColumnHidden(2, True)
        self.tree_arquivos.setColumnHidden(3, True)
        self.tree_arquivos.setStyleSheet("""
            QTreeView { background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 8px; color: white; padding: 5px; font-size: 13px; }
            QTreeView::item:selected { background-color: #2962FF; }
        """)
        self.tree_arquivos.clicked.connect(self.ao_clicar_na_arvore)
        layout_arquivos.addWidget(self.tree_arquivos)

        self.lbl_pasta_atual = QLabel("Nenhuma pasta/arquivo selecionado")
        self.lbl_pasta_atual.setStyleSheet("color: #E67E22; font-weight: bold; font-size: 12px;")
        self.lbl_pasta_atual.setWordWrap(True)
        layout_arquivos.addWidget(self.lbl_pasta_atual)

        layout_split.addWidget(painel_arquivos, 4)

        # COLUNA 2: CONFIGURAÇÕES E MOTOR DE FUSÃO
        painel_motor = QFrame()
        painel_motor.setProperty("class", "painel")
        layout_motor = QVBoxLayout(painel_motor)
        layout_motor.setContentsMargins(25, 25, 25, 25)
        layout_motor.setSpacing(15)

        lbl_tit_motor = QLabel("⚙️ Motor de Processamento")
        lbl_tit_motor.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        layout_motor.addWidget(lbl_tit_motor)

        # Seleção da Planilha
        layout_motor.addWidget(self.criar_label("1. Planilha Base (Excel):"))
        box_planilha = QHBoxLayout()
        self.inp_planilha = QLineEdit("Nenhuma selecionada")
        self.inp_planilha.setReadOnly(True)
        self.inp_planilha.setStyleSheet(
            "background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 6px; color: #8A92A6; padding: 10px;")
        btn_sel_planilha = QPushButton("Procurar Excel")
        btn_sel_planilha.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_sel_planilha.setStyleSheet(
            "background-color: #1A2133; color: white; border: 1px solid #2C364C; padding: 10px; border-radius: 6px;")
        btn_sel_planilha.clicked.connect(self.selecionar_planilha)
        box_planilha.addWidget(self.inp_planilha)
        box_planilha.addWidget(btn_sel_planilha)
        layout_motor.addLayout(box_planilha)

        layout_motor.addSpacing(10)

        # Botões de Ação
        btn_conferir = QPushButton("📋 2. Realizar Auditoria (Planilha vs Pasta Selecionada)")
        btn_conferir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_conferir.setStyleSheet(
            "background-color: #F39C12; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_conferir.clicked.connect(self.iniciar_auditoria)
        layout_motor.addWidget(btn_conferir)

        btn_gerar = QPushButton("📄 3. GERAR RELATÓRIO PDF (Com Motor Inteligente)")
        btn_gerar.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_gerar.setStyleSheet(
            "background-color: #27AE60; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_gerar.clicked.connect(self.iniciar_geracao)
        layout_motor.addWidget(btn_gerar)

        # Terminal Integrado
        layout_motor.addWidget(self.criar_label("Console do Motor:"))
        self.terminal = QTextEdit()
        self.terminal.setReadOnly(True)
        self.terminal.setStyleSheet(
            "background-color: #05070A; border: 1px solid #1E2532; border-radius: 6px; color: #A9CCE3; padding: 10px; font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;")
        layout_motor.addWidget(self.terminal)

        layout_split.addWidget(painel_motor, 6)
        layout_principal.addLayout(layout_split)

    # ==========================================
    # UTILITÁRIOS DA UI
    # ==========================================
    def criar_label(self, texto):
        lbl = QLabel(texto)
        lbl.setStyleSheet("color: #E2E8F0; font-size: 13px; font-weight: bold;")
        return lbl

    def escrever_log_na_tela(self, texto):
        self.terminal.append(texto)
        scrollbar = self.terminal.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def selecionar_planilha(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione a Planilha", "", "Excel (*.xlsx *.xls)")
        if arquivo:
            self.caminho_planilha = arquivo
            self.inp_planilha.setText(arquivo)

    def ao_clicar_na_arvore(self, index: QModelIndex):
        caminho = self.modelo_fs.filePath(index)
        if os.path.isdir(caminho):
            self.caminho_pasta_selecionada = caminho
            self.lbl_pasta_atual.setText(f"Pasta Alvo: {os.path.basename(caminho)}")
        else:
            self.caminho_pasta_selecionada = os.path.dirname(caminho)
            self.lbl_pasta_atual.setText(f"Pasta Alvo: {os.path.basename(self.caminho_pasta_selecionada)}")

    # ==========================================
    # O MOTOR INTELIGENTE EM PRODUÇÃO
    # ==========================================
    def extrair_nomes_da_planilha(self):
        try:
            df = pd.read_excel(self.caminho_planilha)
            coluna_alvo = None
            for col in df.columns:
                if 'NOME' in str(col).upper():
                    coluna_alvo = col
                    break
            if not coluna_alvo:
                coluna_alvo = df.columns[0]

            nomes_sujos = df[coluna_alvo].dropna().tolist()
            return [str(n).strip() for n in nomes_sujos if len(str(n).strip()) > 3 and str(n).upper() != 'NOME']
        except Exception as e:
            self.sinais.update_log.emit(f"❌ Erro ao ler planilha: {e}")
            return []

    def motor_de_busca(self, nome_planilha, pool_arquivos):
        """
        O coração do sistema. Usa token_set_ratio para encontrar todos os documentos
        que pertencem a este nome, mesmo sendo casamento ou tendo sufixos.
        """
        arquivos_encontrados = []
        nome_alvo = nome_planilha.upper()

        for arquivo in list(pool_arquivos):
            nome_arq = os.path.splitext(arquivo)[0].upper()

            score = fuzz.token_set_ratio(nome_alvo, nome_arq)

            if score >= 85:
                arquivos_encontrados.append(arquivo)

        arquivos_encontrados.sort(key=len)

        for f in arquivos_encontrados:
            pool_arquivos.remove(f)

        return arquivos_encontrados

    def verificar_pre_requisitos(self):
        if not self.caminho_planilha:
            QMessageBox.warning(self, "Erro", "Selecione a Planilha primeiro.")
            return False
        if not self.caminho_pasta_selecionada:
            QMessageBox.warning(self, "Erro", "Clique em uma PASTA no Explorador à esquerda.")
            return False
        return True

    # --- THREADS DE EXECUÇÃO ---
    def iniciar_auditoria(self):
        if self.verificar_pre_requisitos():
            self.terminal.clear()
            threading.Thread(target=self.thread_auditar, daemon=True).start()

    def iniciar_geracao(self):
        if self.verificar_pre_requisitos():
            self.terminal.clear()
            threading.Thread(target=self.thread_gerar_relatorio, daemon=True).start()

    def thread_auditar(self):
        self.sinais.update_log.emit(
            f"--- AUDITORIA: PLANILHA vs PASTA ({os.path.basename(self.caminho_pasta_selecionada)}) ---")

        nomes = self.extrair_nomes_da_planilha()
        extensoes_validas = ('.pdf', '.jpg', '.jpeg', '.png')
        pool_arquivos = [f for f in os.listdir(self.caminho_pasta_selecionada) if f.lower().endswith(extensoes_validas)]

        self.sinais.update_log.emit(f"📊 Registros na Planilha: {len(nomes)}")
        self.sinais.update_log.emit(f"📂 Arquivos na Pasta: {len(pool_arquivos)}\n")

        pendencias = 0

        for nome in nomes:
            achados = self.motor_de_busca(nome, pool_arquivos)
            if not achados:
                self.sinais.update_log.emit(f"❌ FALTANDO TUDO: {nome}")
                pendencias += 1
            else:
                self.sinais.update_log.emit(f"✅ {nome} -> Encontrados: {achados}")

        if pendencias == 0:
            self.sinais.update_log.emit(
                "\n✅ AUDITORIA PERFEITA! Todos os nomes da planilha têm arquivos correspondentes.")
        else:
            self.sinais.update_log.emit(f"\n⚠️ Auditoria concluída com {pendencias} pendências críticas.")

        if pool_arquivos:
            self.sinais.update_log.emit(f"\n👻 ARQUIVOS SOBRANDO NA PASTA (Não estão na planilha):")
            for f in pool_arquivos:
                self.sinais.update_log.emit(f"   -> {f}")

    def thread_gerar_relatorio(self):
        self.sinais.update_log.emit("--- INICIANDO GERAÇÃO INTELIGENTE DO RELATÓRIO PDF ---")

        nomes = self.extrair_nomes_da_planilha()
        extensoes_validas = ('.pdf', '.jpg', '.jpeg', '.png')
        pool_arquivos = [f for f in os.listdir(self.caminho_pasta_selecionada) if f.lower().endswith(extensoes_validas)]

        nome_pasta_atual = os.path.basename(self.caminho_pasta_selecionada)
        caminho_final = os.path.join(self.pasta_saida, f"RELATORIO_{nome_pasta_atual.upper()}_FECHAMENTO.pdf")

        try:
            doc_final = fitz.open()
            inseridos = 0

            for nome in nomes:
                achados = self.motor_de_busca(nome, pool_arquivos)

                for arquivo in achados:
                    caminho_arquivo = os.path.join(self.caminho_pasta_selecionada, arquivo)

                    try:
                        if arquivo.lower().endswith(('.jpg', '.jpeg', '.png')):
                            img_doc = fitz.open(caminho_arquivo)
                            pdf_bytes = img_doc.convert_to_pdf()
                            img_doc.close()
                            pdf_temp = fitz.open("pdf", pdf_bytes)
                            doc_final.insert_pdf(pdf_temp)
                            pdf_temp.close()
                        else:
                            doc = fitz.open(caminho_arquivo)
                            doc_final.insert_pdf(doc)
                            doc.close()

                        inseridos += 1

                    except Exception as e:
                        self.sinais.update_log.emit(f"   ⚠️ Erro ao mesclar {arquivo}: {e}")

            if inseridos > 0:
                doc_final.save(caminho_final)
                self.sinais.update_log.emit(f"\n🎉 RELATÓRIO GERADO COM SUCESSO!")
                self.sinais.update_log.emit(f"Foram agrupados {inseridos} documentos/imagens na ordem da planilha.")
                self.sinais.update_log.emit(f"Salvo em: {caminho_final}")
                os.startfile(os.path.abspath(caminho_final))
            else:
                self.sinais.update_log.emit("\n⚠️ Nenhum documento válido foi encontrado para montar o relatório.")

            doc_final.close()

        except Exception as e:
            self.sinais.update_log.emit(f"\n❌ Erro crítico na montagem do PDF: {e}")