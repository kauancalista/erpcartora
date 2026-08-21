from PyQt6.QtWidgets import QLineEdit


class BarraPesquisa(QLineEdit):
    """
    Componente padronizado de barra de pesquisa.
    Use isso em qualquer tela do sistema para manter o design igual!
    """

    def __init__(self, placeholder="🔍 Buscar por nome, processo...", largura=300):
        super().__init__()
        self.setPlaceholderText(placeholder)
        self.setFixedWidth(largura)

        # Você pode atrelar uma classe CSS aqui se quiser um design diferentão só pra ela depois
        self.setProperty("class", "barra-pesquisa")