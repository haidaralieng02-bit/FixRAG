from __future__ import annotations

import io
import re
from typing import Dict, List

import fitz


def _clean_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_pages(pdf_bytes: bytes) -> List[Dict]:
    if not pdf_bytes:
        raise ValueError("The PDF file is empty.")

    try:
        document = fitz.open(stream=io.BytesIO(pdf_bytes), filetype="pdf")
    except Exception as exc:
        raise ValueError("The uploaded file could not be opened as a valid PDF.") from exc

    pages = []
    try:
        for page_number, page in enumerate(document, start=1):
            text = _clean_text(page.get_text("text"))
            if text:
                pages.append(
                    {
                        "page": page_number,
                        "text": text,
                    }
                )
    finally:
        document.close()

    if not pages:
        raise ValueError(
            "No extractable text was found. This may be a scanned/image-only PDF. "
            "Please use a text-readable manual for this MVP."
        )

    return pages


def _guess_section(text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    for line in lines[:6]:
        candidate = line.strip(":- ")
        if 3 <= len(candidate) <= 120 and (
            candidate.isupper()
            or re.match(r"^(chapter|section|appendix|troubleshooting|fault|warning|maintenance)\b", candidate, re.I)
        ):
            return candidate
    return "Page content"


def chunk_pages(
    pages: List[Dict],
    chunk_size: int = 1200,
    overlap: int = 180,
) -> List[Dict]:
    if overlap >= chunk_size:
        raise ValueError("Chunk overlap must be smaller than chunk size.")

    chunks = []
    chunk_id = 0

    for page in pages:
        text = page["text"]
        section = _guess_section(text)
        start = 0

        while start < len(text):
            end = min(start + chunk_size, len(text))
            chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append(
                    {
                        "id": chunk_id,
                        "page": page["page"],
                        "section": section,
                        "text": chunk_text,
                    }
                )
                chunk_id += 1

            if end >= len(text):
                break
            start = end - overlap

    if not chunks:
        raise ValueError("The PDF contained no usable text chunks.")

    return chunks
