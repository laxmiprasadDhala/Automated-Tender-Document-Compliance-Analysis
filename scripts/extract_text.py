import os
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
import tempfile


# import ollama    # or your chat API wrapper

def extract_text(pdf_path: str) -> str:
    """
    Return all text found in a PDF.
    Falls back to OCR if the PDF has no extractable text (i.e., scanned pages).
    """
    text = ""

    # --- 1. Try native text extraction with pdfplumber ----------------------
    with pdfplumber.open(pdf_path) as p:
        for page in p.pages:
            text += page.extract_text() or ""

    if text.strip():  # success → return early
        return text

    # --- 2. Fallback: OCR on page images ------------------------------------
    #   a) Render pages to images in a temp dir
    with tempfile.TemporaryDirectory() as tmpdir:
        images = convert_from_path(pdf_path, dpi=300, output_folder=tmpdir)

        #   b) Run Tesseract on each image
        for img in images:
            text += pytesseract.image_to_string(img, lang="eng")

    return text
