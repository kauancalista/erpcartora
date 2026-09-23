import os
import sys
from flask import Flask, jsonify, render_template, request
from werkzeug.serving import make_server

# Função inteligente que descobre exatamente onde o .exe está salvo
def obter_pasta_base():
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como .exe, pega a pasta real do executável
        return os.path.dirname(sys.executable)
    else:
        # Se estiver rodando no código fonte (.py), pega a raiz do projeto
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PASTA_BASE = obter_pasta_base()

# Aponta para a pasta templates que você colou do lado do .exe
template_dir = os.path.join(PASTA_BASE, "templates")
app = Flask(__name__, template_folder=template_dir)

# Garante que as fotos também vão cair do lado do .exe
UPLOAD_FOLDER = os.path.join(PASTA_BASE, "documentos_recebidos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# PIN de segurança para o celular
PIN_CARTORIO = "1234"

@app.route("/")
def index():
    return render_template("scanner.html")

# (O resto do arquivo a partir do @app.route("/upload") continua igual...)

@app.route("/upload", methods=["POST"])
def upload():
    # Valida a segurança
    if request.headers.get("X-Pin") != PIN_CARTORIO:
        return jsonify({"erro": "PIN inválido"}), 403

    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem recebida"}), 400

    arquivo = request.files["imagem"]

    import re
    import time

    # Sanitiza o nome contra caracteres proibidos e Path Traversal
    nome_limpo = re.sub(r'[\\/*?:"<>|]', "", nome_personalizado)
    if not nome_limpo:
        nome_limpo = "DOC_DIGITALIZADO"

    # Mantém a extensão válida
    extensao = os.path.splitext(arquivo.filename)[1].lower()
    if extensao not in ['.jpg', '.jpeg', '.png']:
        extensao = ".jpg"

    timestamp = int(time.time() * 1000)
    nome_final = f"{nome_limpo}_{timestamp}{extensao}"

    # Salva primeiro como .uploading para evitar que o QTimer da UI
    # mova o arquivo enquanto o upload ainda está sendo transferido!
    caminho_temp = os.path.join(UPLOAD_FOLDER, f"{nome_final}.uploading")
    caminho_final = os.path.join(UPLOAD_FOLDER, nome_final)

    try:
        arquivo.save(caminho_temp)
        os.replace(caminho_temp, caminho_final)
    except Exception as e:
        if os.path.exists(caminho_temp):
            os.remove(caminho_temp)
        return jsonify({"erro": f"Falha ao salvar imagem: {str(e)}"}), 500

    return jsonify({"status": "sucesso"}), 200


# ==========================================
# CONTROLE DE LIGA/DESLIGA DO SERVIDOR
# ==========================================
server = None


def iniciar_flask():
    global server
    # O make_server permite que o servidor seja desligado depois
    server = make_server("0.0.0.0", 5000, app, ssl_context="adhoc")
    server.serve_forever()


def parar_flask():
    global server
    if server:
        server.shutdown()
        server = None