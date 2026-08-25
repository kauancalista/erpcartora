import os
import sys
from flask import Flask, jsonify, render_template, request
from werkzeug.serving import make_server


# Função para o PyInstaller achar a pasta templates quando virar .exe
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        # Aponta para a raiz onde está o main.py
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base_path, relative_path)


template_dir = resource_path("templates")
app = Flask(__name__, template_folder=template_dir)

UPLOAD_FOLDER = resource_path("documentos_recebidos")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# PIN de segurança para o celular
PIN_CARTORIO = "1234"


@app.route("/")
def index():
    return render_template("scanner.html")


@app.route("/upload", methods=["POST"])
def upload():
    # Valida a segurança
    if request.headers.get("X-Pin") != PIN_CARTORIO:
        return jsonify({"erro": "PIN inválido"}), 403

    if "imagem" not in request.files:
        return jsonify({"erro": "Nenhuma imagem recebida"}), 400

    arquivo = request.files["imagem"]

    # Pega o nome que o usuário digitou no celular
    nome_personalizado = request.form.get("nome", "doc_digitalizado")

    # Mantém a extensão como .jpg
    extensao = os.path.splitext(arquivo.filename)[1]
    if not extensao:
        extensao = ".jpg"

    nome_final = f"{nome_personalizado}{extensao}"

    # Salva na pasta para a TelaScanner puxar
    caminho_salvo = os.path.join(UPLOAD_FOLDER, nome_final)
    arquivo.save(caminho_salvo)

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