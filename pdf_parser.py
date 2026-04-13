import io
import re
from typing import Optional

import fitz
import pdfplumber
import pytesseract
from PIL import Image

import os
import pytesseract

TESSERACT_CMD = os.getenv("TESSERACT_CMD")
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def only_digits(text: str) -> str:
    return re.sub(r"\D", "", text or "")


def find_boleto_number_in_text(text: str) -> Optional[str]:
    """
    Procura sequências compatíveis com:
    - boleto bancário: 44 ou 47 dígitos
    - arrecadação/convênios: 44 ou 48 dígitos
    """
    if not text:
        return None

    # procura blocos longos com dígitos, pontos e espaços
    candidates = re.findall(r"[\d\.\s]{30,100}", text)

    for item in candidates:
        digits = only_digits(item)
        if len(digits) in (44, 47, 48):
            return digits

    # fallback: procurar diretamente sequências contínuas
    direct = re.findall(r"\d{44}|\d{47}|\d{48}", only_digits(text))
    if direct:
        return direct[0]

    return None


def extract_text_from_pdf_digital(pdf_bytes: bytes) -> str:
    full_text = ""

    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text() or ""
            full_text += "\n" + page_text

    return full_text.strip()


def render_pdf_pages_to_images(pdf_bytes: bytes, dpi: int = 300) -> list[Image.Image]:
    """
    Converte páginas do PDF em imagens para OCR.
    """
    images = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    for page in doc:
        pix = page.get_pixmap(matrix=matrix, alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        images.append(img)

    doc.close()
    return images


def preprocess_image_for_ocr(image: Image.Image) -> Image.Image:
    """
    Pré-processamento básico para melhorar OCR.
    """
    gray = image.convert("L")
    # limiar simples
    bw = gray.point(lambda x: 0 if x < 180 else 255, "1")
    return bw.convert("L")


def extract_text_from_pdf_ocr(pdf_bytes: bytes) -> str:
    full_text = ""
    images = render_pdf_pages_to_images(pdf_bytes)

    for img in images:
        processed = preprocess_image_for_ocr(img)
        text = pytesseract.image_to_string(processed, lang="por")
        full_text += "\n" + text

    return full_text.strip()


def extract_boleto_from_pdf(pdf_file) -> dict:
    """
    Estratégia:
    1. tenta extrair do PDF digital
    2. se não achar linha digitável, cai para OCR
    """
    pdf_bytes = pdf_file.read()

    # tenta leitura digital
    text_digital = extract_text_from_pdf_digital(pdf_bytes)
    linha_digital = find_boleto_number_in_text(text_digital)

    if linha_digital:
        return {
            "metodo": "pdf_digital",
            "texto_extraido": text_digital[:5000],
            "linha_digitavel": linha_digital
        }

    # fallback OCR
    text_ocr = extract_text_from_pdf_ocr(pdf_bytes)
    linha_ocr = find_boleto_number_in_text(text_ocr)

    return {
        "metodo": "ocr",
        "texto_extraido": text_ocr[:5000],
        "linha_digitavel": linha_ocr
    }