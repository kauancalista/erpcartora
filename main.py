import sys
from PyQt6.QtWidgets import QApplication
from ui.views.main_dashboard import MainWindow


def iniciar_sistema():
    app = QApplication(sys.argv)

    # Chama o chassi completo do ERP
    janela = MainWindow()
    janela.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    iniciar_sistema()