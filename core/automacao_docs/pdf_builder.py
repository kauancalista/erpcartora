import os
import gc
import tempfile
from PIL import Image, ImageOps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pypdf import PdfWriter, PdfReader


def imagem_para_pdf(imagem_path):
    temp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")

    with Image.open(imagem_path) as img:
        img = ImageOps.exif_transpose(img)

        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            fundo_branco = Image.new('RGB', img.size, (255, 255, 255))
            fundo_branco.paste(img, mask=img.convert('RGBA').split()[3])
            img = fundo_branco
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Reduz resolução para 150 DPI antes de embutir — documentos de scanner
        # costumam vir com 300+ DPI, o que quadruplica o tamanho em RAM sem ganho visual
        largura_max = int(A4[0] * 150 / 72)   # ~311px largura A4 @ 150dpi
        altura_max  = int(A4[1] * 150 / 72)   # ~441px altura  A4 @ 150dpi
        img.thumbnail((largura_max, altura_max), Image.LANCZOS)

        img_reader = ImageReader(img)
        c = canvas.Canvas(temp_pdf.name, pagesize=A4)
        largura_a4, altura_a4 = A4
        largura_img, altura_img = img.size

        proporcao = min(largura_a4 / largura_img, altura_a4 / altura_img)
        nova_largura = largura_img * proporcao
        nova_altura  = altura_img * proporcao
        x = (largura_a4 - nova_largura) / 2
        y = (altura_a4 - nova_altura) / 2

        c.drawImage(img_reader, x, y, width=nova_largura, height=nova_altura)
        c.showPage()
        c.save()

    return temp_pdf.name


def gerar_relatorio(documentos, saida_pdf):
    temporarios = []

    try:
        writer = PdfWriter()

        for arquivo in documentos:
            if not arquivo or not os.path.exists(arquivo):
                continue

            extensao = os.path.splitext(arquivo)[1].lower()
            pdf_utilizado = arquivo
            temp_gerado = None

            if extensao in [".jpg", ".jpeg", ".png"]:
                pdf_utilizado = imagem_para_pdf(arquivo)
                temp_gerado = pdf_utilizado
                temporarios.append(pdf_utilizado)

            # Abre, copia páginas e fecha imediatamente — não mantém o reader em memória
            reader = PdfReader(pdf_utilizado)
            for pagina in reader.pages:
                writer.add_page(pagina)
            # Fecha o file handle explicitamente para liberar RAM
            reader.stream.close()
            del reader

            # Força coleta de lixo a cada documento para manter RAM baixa
            gc.collect()

        if len(writer.pages) > 0:
            with open(saida_pdf, "wb") as arquivo_saida:
                writer.write(arquivo_saida)
        else:
            raise Exception("Nenhum documento processado. Relatório vazio.")

    finally:
        del writer
        gc.collect()
        for temp in temporarios:
            if temp and os.path.exists(temp):
                try:
                    os.remove(temp)
                except OSError:
                    pass
