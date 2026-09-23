import sys
import os
import traceback
from datetime import datetime
from PyQt6.QtWidgets import QApplication, QMessageBox
from ui.views.main_dashboard import MainWindow


from utils_caminhos import obter_diretorio_base


# ==========================================
# INTERCEPTADOR GLOBAL DE ERROS FATAIS
# ==========================================
def interceptador_erros(tipo_erro, valor_erro, traceback_erro):
    """Captura falhas críticas, salva no log e exibe alerta amigável na UI sem fechar o app à força."""
    if issubclass(tipo_erro, KeyboardInterrupt):
        sys.__excepthook__(tipo_erro, valor_erro, traceback_erro)
        return

    texto_erro = "".join(traceback.format_exception(tipo_erro, valor_erro, traceback_erro))

    # 1. Grava de forma segura no arquivo erros.log na raiz do projeto
    try:
        caminho_log = os.path.join(obter_diretorio_base(), "erros.log")
        with open(caminho_log, "a", encoding="utf-8") as arquivo_log:
            arquivo_log.write(f"\n{'=' * 40}\nDATA: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            arquivo_log.write(texto_erro)
            arquivo_log.write(f"{'=' * 40}\n")
    except Exception:
        pass

    # 2. Levanta a janela amigável (se a interface gráfica já estiver ativa)
    app = QApplication.instance()
    if app:
        try:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Critical)
            msg.setWindowTitle("Ops! Instabilidade no Sistema")
            msg.setText("Ocorreu uma falha inesperada durante a execução desta ação.")
            msg.setInformativeText(
                "Os detalhes técnicos foram gravados no arquivo 'erros.log'. O sistema continuará ativo.")

            # Cria o botão "Show Details..." para leitura rápida do erro
            msg.setDetailedText(texto_erro)
            msg.setStyleSheet("background-color: #11151F; color: white;")
            msg.exec()
        except Exception:
            pass
    else:
        # Se a interface nem abriu, encerra
        sys.exit(1)


# Liga o radar de erros no Python ANTES de qualquer tela abrir
sys.excepthook = interceptador_erros


# ==========================================
# INÍCIO DO SISTEMA
# ==========================================
def iniciar_sistema():
    # Puxa o app que já foi criado lá embaixo, em vez de criar duplicado!
    app = QApplication.instance()

    # ==========================================
    # CARREGANDO O ESTILO GLOBAL (QSS) E CSS
    # ==========================================
    estilo_base = app.styleSheet()  # Salva o CSS escuro que já configuramos

    caminho_qss = os.path.join(os.path.dirname(__file__), "assets", "estilo.qss")
    if os.path.exists(caminho_qss):
        with open(caminho_qss, "r", encoding="utf-8") as f:
            # Soma o CSS escuro com as regras do seu arquivo QSS
            app.setStyleSheet(estilo_base + f.read())
    else:
        print("⚠️ AVISO: Arquivo estilo.qss não encontrado na raiz do projeto!")

    # Inicia a janela principal
    janela = MainWindow()
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 1. Força o motor visual moderno (tira o visual de Windows 98)
    app.setStyle("Fusion")

    # 2. Força o fundo escuro globalmente para a janela principal não ficar branca!
    app.setStyleSheet("""
        QMainWindow { background-color: #05070A; }
        QWidget#centralWidget { background-color: #05070A; }
    """)

    iniciar_sistema()