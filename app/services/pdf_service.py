import fitz  # PyMuPDF


def extract_text(pdf_path: str) -> str:
    """PDF 파일에서 텍스트를 추출한다."""
    doc = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)
