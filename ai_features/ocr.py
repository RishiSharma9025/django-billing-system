from __future__ import annotations

from pathlib import Path


def extract_invoice_text(file_path: str) -> str:
    """
    Extract readable text from an uploaded receipt/invoice image.

    Returns extracted text or a helpful message (never returns an empty string).
    """
    path = Path(file_path)
    if not path.exists():
        return f"Uploaded file not found: {path.name}"

    # 1) If it's a PDF, try text extraction first.
    if path.suffix.lower() == ".pdf":
        try:
            import pdfplumber  # type: ignore

            with pdfplumber.open(str(path)) as pdf:
                out = []
                for page in pdf.pages:
                    txt = page.extract_text() or ""
                    if txt.strip():
                        out.append(txt.strip())
                text = "\n".join(out).strip()
                if text:
                    return text
        except Exception:
            # Fall back to OCR for images only (if dependencies exist).
            pass

    available = {"pytesseract": False, "easyocr": False}
    text = ""

    # 2) pytesseract path (good baseline).
    try:
        import pytesseract  # type: ignore
        from PIL import Image, ImageEnhance, ImageOps  # type: ignore

        available["pytesseract"] = True
        img = Image.open(str(path))
        img = ImageOps.exif_transpose(img)
        img = img.convert("L")
        img = ImageOps.autocontrast(img)

        # Upscale small images for better OCR.
        w, h = img.size
        if max(w, h) < 1400:
            scale = 2
            img = img.resize((w * scale, h * scale))

        # Mild denoise to reduce speckle.
        try:
            from PIL import ImageFilter  # type: ignore

            img = img.filter(ImageFilter.MedianFilter(size=3))
        except Exception:
            pass

        # Increase contrast a bit more.
        img = ImageEnhance.Contrast(img).enhance(2.0)

        text = pytesseract.image_to_string(img, config="--oem 3 --psm 6") or ""
        text = text.strip()
        if text:
            return text
    except Exception:
        # Continue to easyocr fallback.
        pass

    # 3) easyocr fallback.
    try:
        import easyocr  # type: ignore

        available["easyocr"] = True
        reader = easyocr.Reader(["en"], gpu=False)
        results = reader.readtext(str(path), detail=0)
        text = "\n".join([r for r in results if str(r).strip()]).strip()
        if text:
            return text
    except Exception:
        pass

    # 4) If dependencies were missing entirely, give install instructions.
    if not available["pytesseract"] and not available["easyocr"]:
        return (
            "OCR dependency not available.\n"
            "Install one of:\n"
            "  pip install pytesseract pillow\n"
            "  pip install easyocr\n"
            "If using pytesseract, also install the Tesseract engine on your OS."
        )

    # 5) Dependencies exist but OCR couldn't read anything.
    return (
        "No readable text detected from the uploaded file.\n"
        "Tips: use a clearer/higher-resolution photo, avoid blur, and crop to the invoice area."
    )

