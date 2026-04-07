from __future__ import annotations


def extract_invoice_text(file_path: str) -> str:
    """
    Try pytesseract first, then easyocr.
    Returns extracted text or helpful fallback message.
    """
    try:
        import pytesseract  # type: ignore
        from PIL import Image  # type: ignore

        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        return (text or "").strip()
    except Exception:
        pass

    try:
        import easyocr  # type: ignore

        reader = easyocr.Reader(["en"], gpu=False)
        results = reader.readtext(file_path, detail=0)
        return "\n".join(results).strip()
    except Exception:
        return (
            "OCR dependency not available.\n"
            "Install one of:\n"
            "  pip install pytesseract pillow\n"
            "  pip install easyocr\n"
            "If using pytesseract, also install the Tesseract engine on your OS."
        )

