import sys
import os


def obter_diretorio_base():
    """
    Retorna o diretório base correto, resolvendo a diferença entre
    rodar via Python no VS Code e rodar no .exe pelo PyInstaller.
    """
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como executável (PyInstaller)
        return os.path.dirname(sys.executable)

    # Se estiver rodando como script normal (VS Code)
    return os.path.dirname(os.path.abspath(__file__))