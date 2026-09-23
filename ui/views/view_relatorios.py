import os
import fitz  # PyMuPDF
import json
import pandas as pd
import threading
from rapidfuzz import fuzz
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QLineEdit, QFileDialog,
                             QTextEdit, QMessageBox, QTreeView, QHeaderView, QComboBox)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QModelIndex, QDir
from PyQt6.QtGui import QCursor, QFileSystemModel

from utils_caminhos import obter_diretorio_base


class LogSignal(QObject):
    update_log = pyqtSignal(str)
    toggle_loading = pyqtSignal(bool)


class TelaRelatorios(QWidget):
    def __init__(self):
        super().__init__()

        # Inicializa o transmissor de logs para a interface (evita AttributeError)
        self.sinais = LogSignal()
        self.sinais.update_log.connect(self.escrever_log_na_tela)
        self.sinais.toggle_loading.connect(self._alternar_loading)

        self.caminho_planilha = ""
        self.pasta_saida = os.path.join(obter_diretorio_base(), "Relatorios_Gerados")
        os.makedirs(self.pasta_saida, exist_ok=True)

        # Pastas onde o sistema VAI PROCURAR os documentos automaticamente
        self.pasta_processos = os.path.join(obter_diretorio_base(), "Arquivos_Cartorio")
        self.pasta_scanner = os.path.join(obter_diretorio_base(), "Scanner_Entrada")
        os.makedirs(self.pasta_processos, exist_ok=True)
        os.makedirs(self.pasta_scanner, exist_ok=True)
        
        self.pastas_de_busca = [self.pasta_processos, self.pasta_scanner]

        # Pasta DESTINO (onde os arquivos avulsos serão armazenados)
        self.pasta_ferc = os.path.join(obter_diretorio_base(), "Pasta_FERC")
        try:
            caminho_config = os.path.join(obter_diretorio_base(), "config", "app_config.json")
            if os.path.exists(caminho_config):
                with open(caminho_config, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("pasta_ferc"):
                        self.pasta_ferc = cfg["pasta_ferc"]
        except:
            pass
        os.makedirs(self.pasta_ferc, exist_ok=True)

        layout_principal = QVBoxLayout(self)
        layout_principal.setContentsMargins(40, 30, 40, 30)
        layout_principal.setSpacing(20)

        # --- CABEÇALHO ---
        layout_topo = QVBoxLayout()
        lbl_titulo = QLabel("📊 Central de Relatórios e Auditoria (FERC / CRC)")
        lbl_titulo.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        lbl_sub = QLabel("Motor de fusão automático: busca nos processos e scanner, audita falhas e gera o PDF final.")
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

        lbl_nav = QLabel("📁 Destino: Pasta FERC")
        lbl_nav.setStyleSheet("font-size: 16px; font-weight: bold; color: white; margin-bottom: 5px;")
        layout_arquivos.addWidget(lbl_nav)

        # Modelo de Sistema de Arquivos apontando para a pasta FERC
        self.modelo_fs = QFileSystemModel()
        self.modelo_fs.setRootPath(self.pasta_ferc)
        self.modelo_fs.setFilter(QDir.Filter.NoDotAndDotDot | QDir.Filter.AllDirs | QDir.Filter.Files)

        # A Árvore de Arquivos (TreeView)
        self.tree_arquivos = QTreeView()
        self.tree_arquivos.setModel(self.modelo_fs)
        self.tree_arquivos.setRootIndex(self.modelo_fs.index(self.pasta_ferc))
        self.tree_arquivos.setAnimated(True)
        self.tree_arquivos.setIndentation(20)
        self.tree_arquivos.setSortingEnabled(True)

        # --- O SEGREDO DO VISUAL LIMPO AQUI ---
        self.tree_arquivos.setHeaderHidden(True)
        self.tree_arquivos.setColumnHidden(1, True)
        self.tree_arquivos.setColumnHidden(2, True)
        self.tree_arquivos.setColumnHidden(3, True)
        self.tree_arquivos.setStyleSheet("""
            QTreeView { background-color: #0B0E14; border: 1px solid #1E2532; border-radius: 8px; color: white; padding: 5px; font-size: 13px; }
            QTreeView::item:selected { background-color: #2962FF; }
        """)
        layout_arquivos.addWidget(self.tree_arquivos)

        self.lbl_pasta_atual = QLabel("Essa pasta contém os PDFs agrupados e cópias de documentos coletados automaticamente.")
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

        # --- Seleção do Modo de Geração ---
        layout_motor.addWidget(self.criar_label("2. Modo de Operação:"))
        self.combo_modo = QComboBox()
        self.combo_modo.addItems(["Gerar com CPF", "Gerar com Certidões (FERC/CRAS)"])
        self.combo_modo.setStyleSheet(
            "background-color: #1A2133; border: 1px solid #2C364C; border-radius: 6px; color: white; padding: 10px; font-weight: bold;")
        layout_motor.addWidget(self.combo_modo)

        layout_motor.addSpacing(10)

        # Botões de Ação
        btn_conferir = QPushButton("📋 3. Realizar Auditoria (Planilha vs Pasta Selecionada)")
        btn_conferir.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        btn_conferir.setStyleSheet(
            "background-color: #F39C12; color: white; font-weight: bold; padding: 12px; border-radius: 6px;")
        btn_conferir.clicked.connect(self.iniciar_auditoria)
        layout_motor.addWidget(btn_conferir)

        btn_gerar = QPushButton("📄 4. GERAR RELATÓRIO PDF (Com Motor Inteligente)")
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

        # Loading (Cobrinha)
        from PyQt6.QtWidgets import QProgressBar
        self.barra_progresso = QProgressBar()
        self.barra_progresso.setRange(0, 0)  # Modo indeterminado (cobrinha)
        self.barra_progresso.setTextVisible(False)
        self.barra_progresso.setStyleSheet("""
            QProgressBar {
                border: none;
                background-color: #1A2133;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #2962FF;
                border-radius: 4px;
            }
        """)
        self.barra_progresso.hide()
        layout_motor.addWidget(self.barra_progresso)

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

    def _alternar_loading(self, mostrar):
        if mostrar:
            self.barra_progresso.show()
        else:
            self.barra_progresso.hide()

    def selecionar_planilha(self):
        arquivo, _ = QFileDialog.getOpenFileName(self, "Selecione a Planilha", "", "Excel (*.xlsx *.xls)")
        if arquivo:
            self.caminho_planilha = arquivo
            self.inp_planilha.setText(arquivo)

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

    def verificar_pre_requisitos(self):
        if not self.caminho_planilha:
            QMessageBox.warning(self, "Erro", "Selecione a Planilha primeiro.")
            return False
        return True

    def obter_pasta_destino_ferc(self, modo):
        import datetime
        agora = datetime.datetime.now()
        ano = agora.strftime("%Y")
        
        meses_pt = {
            1: "JANEIRO", 2: "FEVEREIRO", 3: "MARCO", 4: "ABRIL",
            5: "MAIO", 6: "JUNHO", 7: "JULHO", 8: "AGOSTO",
            9: "SETEMBRO", 10: "OUTUBRO", 11: "NOVEMBRO", 12: "DEZEMBRO"
        }
        mes_numero = agora.month
        mes_nome = meses_pt.get(mes_numero, "")
        mes_pasta = f"{mes_numero:02d} - {mes_nome}"
        
        ato = "AVB_CPF" if modo == "CPF" else "CERTIDAO"
        
        caminho_completo = os.path.join(self.pasta_ferc, ano, mes_pasta, ato)
        os.makedirs(caminho_completo, exist_ok=True)
        return caminho_completo

    # ==========================================
    # THREADS DE EXECUÇÃO (USANDO O MOTOR LEGADO)
    # ==========================================
    def iniciar_auditoria(self):
        if self.verificar_pre_requisitos():
            self.terminal.clear()
            threading.Thread(target=self.thread_auditar, daemon=True).start()

    def iniciar_geracao(self):
        if self.verificar_pre_requisitos():
            self.terminal.clear()
            threading.Thread(target=self.thread_gerar_relatorio, daemon=True).start()

    def thread_auditar(self):
        try:
            self.sinais.toggle_loading.emit(True)
            from core.automacao_docs.conferencia import conferir_documentos
            
            self.sinais.update_log.emit(f"--- AUDITORIA: PLANILHA vs CARTÓRIO GLOBAL ---")

            nomes = self.extrair_nomes_da_planilha()
            modo = "CPF" if self.combo_modo.currentIndex() == 0 else "CERTIDAO"
            
            self.sinais.update_log.emit(f"🔍 Analisando {len(nomes)} nomes no modo '{modo}'...")
            
            completos, pendentes = conferir_documentos(nomes, self.pastas_de_busca, modo)
            
            self.sinais.update_log.emit(f"📊 Registros na Planilha: {len(nomes)}")
            self.sinais.update_log.emit(f"✅ Encontrados Completos: {len(completos)}\n")

            for p in pendentes:
                doc_str = "OK" if p["documento"] else "FALTA"
                anexo_str = "OK" if p["anexo"] else "FALTA"
                self.sinais.update_log.emit(f"❌ PENDENTE: {p['nome']} (Principal: {doc_str} | Anexo: {anexo_str})")

            if len(pendentes) == 0:
                self.sinais.update_log.emit("\n✅ AUDITORIA PERFEITA! Todos os nomes da planilha têm arquivos correspondentes.")
            else:
                self.sinais.update_log.emit(f"\n⚠️ Auditoria concluída com {len(pendentes)} pendências críticas.")
        except Exception as e:
            self.sinais.update_log.emit(f"\n❌ Erro na auditoria: {e}")
        finally:
            self.sinais.toggle_loading.emit(False)

    def thread_gerar_relatorio(self):
        try:
            self.sinais.toggle_loading.emit(True)
            from core.automacao_docs.localizador import localizar_documento, construir_cache_pastas, extrair_primeiro_conjuge, normalizar
            from core.automacao_docs.pdf_builder import gerar_relatorio
            import shutil
            
            self.sinais.update_log.emit("--- INICIANDO COLETA E GERAÇÃO INTELIGENTE ---")

            nomes = self.extrair_nomes_da_planilha()
            modo = "CPF" if self.combo_modo.currentIndex() == 0 else "CERTIDAO"
            
            # Obtém dinamicamente a pasta do mês e ato (Ex: FERC/2026/09 - SETEMBRO/AVB_CPF)
            pasta_destino_atual = self.obter_pasta_destino_ferc(modo)
            
            self.sinais.update_log.emit("Construindo cache do sistema de arquivos para ultra-velocidade...")
            cache_pasta = construir_cache_pastas(self.pastas_de_busca)
            
            documentos_finais = []
            arquivos_copiados = 0
            
            for nome in nomes:
                doc_principal = localizar_documento(nome, self.pastas_de_busca, cache_pasta)
                
                nome_limpo = extrair_primeiro_conjuge(normalizar(nome))
                doc_secundario = None
                if modo == "CPF":
                    doc_secundario = localizar_documento(f"{nome_limpo} CPF", self.pastas_de_busca, cache_pasta)
                elif modo == "CERTIDAO":
                    for sufixo in [" + FERC", " + CRAS", " + REGISTRE-SE", " FERC", " CRAS", " REGISTRE-SE"]:
                        doc_secundario = localizar_documento(f"{nome_limpo}{sufixo}", self.pastas_de_busca, cache_pasta)
                        if doc_secundario: break
                
                if doc_principal:
                    documentos_finais.append(doc_principal["caminho"])
                    # Copia para a subpasta do mês/ato
                    destino_principal = os.path.join(pasta_destino_atual, doc_principal["arquivo"].upper())
                    if not os.path.exists(destino_principal):
                        shutil.copy2(doc_principal["caminho"], destino_principal)
                        arquivos_copiados += 1
                    self.sinais.update_log.emit(f"📎 Anexando Principal: {doc_principal['arquivo']}")
                else:
                    self.sinais.update_log.emit(f"⚠️ Principal faltando para: {nome}")
                    
                if doc_secundario:
                    documentos_finais.append(doc_secundario["caminho"])
                    # Copia para a subpasta do mês/ato
                    destino_secundario = os.path.join(pasta_destino_atual, doc_secundario["arquivo"].upper())
                    if not os.path.exists(destino_secundario):
                        shutil.copy2(doc_secundario["caminho"], destino_secundario)
                        arquivos_copiados += 1
                    self.sinais.update_log.emit(f"📎 Anexando Secundário: {doc_secundario['arquivo']}")
                else:
                    self.sinais.update_log.emit(f"⚠️ Anexo faltando para: {nome}")
                    
            if not documentos_finais:
                self.sinais.update_log.emit("\n❌ Nenhum documento encontrado para gerar o PDF!")
                return
                
            self.sinais.update_log.emit(f"\n📁 {arquivos_copiados} arquivos foram copiados/atualizados em:\n{pasta_destino_atual}")
                
            # O relatório final PDF também vai pra essa mesma subpasta organizada
            caminho_final = os.path.join(pasta_destino_atual, f"RELATORIO_FINAL_COMPLETO_{modo}.pdf")
            
            self.sinais.update_log.emit(f"\nMesclando {len(documentos_finais)} documentos com otimização de RAM (ReportLab)...")
            
            try:
                gerar_relatorio(documentos_finais, caminho_final)
                self.sinais.update_log.emit(f"\n🎉 RELATÓRIO GERADO COM SUCESSO!")
                self.sinais.update_log.emit(f"Salvo em: {caminho_final}")
                os.startfile(os.path.abspath(caminho_final))
            except Exception as e:
                self.sinais.update_log.emit(f"\n❌ Erro crítico na montagem do PDF: {e}")
        finally:
            self.sinais.toggle_loading.emit(False)
