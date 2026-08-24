import sys
import os
from PyQt6.QtWidgets import QApplication
from ui.views.main_dashboard import MainWindow


def iniciar_sistema():
    app = QApplication(sys.argv)

    # ==========================================
    # CARREGANDO O ESTILO GLOBAL (QSS)
    # ==========================================
    caminho_qss = os.path.join(os.path.dirname(__file__), "assets", "estilo.qss")
    if os.path.exists(caminho_qss):
        with open(caminho_qss, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
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