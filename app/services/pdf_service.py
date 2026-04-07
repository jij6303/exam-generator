import fitz  # PyMuPDF


def extract_text(pdf_path: str) -> str:
    """PDF 파일에서 텍스트를 추출한다."""
    doc = fitz.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()
    return "\n".join(pages)


def get_pdf_info(pdf_path: str) -> dict:
    """PDF 총 페이지 수와 목차(챕터) 정보를 반환한다."""
    doc = fitz.open(pdf_path)
    page_count = len(doc)

    toc = doc.get_toc()  # [[level, title, page], ...]
    chapters = []

    if toc:
        # 최상위 레벨 항목만 챕터로 사용
        top_level = min(item[0] for item in toc)
        top_items = [item for item in toc if item[0] == top_level]
        for i, (_, title, page_start) in enumerate(top_items):
            if i + 1 < len(top_items):
                page_end = top_items[i + 1][2] - 1
            else:
                page_end = page_count
            chapters.append({
                "title": title,
                "page_start": page_start,
                "page_end": page_end,
            })

    doc.close()
    return {"page_count": page_count, "chapters": chapters}


def extract_text_by_pages(pdf_path: str, page_start: int, page_end: int) -> str:
    """특정 페이지 범위의 텍스트를 추출한다. (1-indexed, 양 끝 포함)"""
    doc = fitz.open(pdf_path)
    start = max(0, page_start - 1)
    end = min(len(doc), page_end)
    pages = [doc[i].get_text() for i in range(start, end)]
    doc.close()
    return "\n".join(pages)
