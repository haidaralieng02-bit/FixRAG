from __future__ import annotations

from typing import Dict

from core.llm import generate_answer
from core.pdf_processor import chunk_pages, extract_pages
from core.retriever import build_context, build_index, retrieve

MAX_PDF_BYTES = 25 * 1024 * 1024


def build_document_index(pdf_bytes: bytes, filename: str) -> Dict:
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise ValueError("This MVP accepts PDFs up to 25 MB.")

    pages = extract_pages(pdf_bytes)
    chunks = chunk_pages(pages)
    vector_index = build_index(chunks)

    return {
        "filename": filename,
        "page_count": len(pages),
        "chunk_count": len(chunks),
        "chunks": vector_index["chunks"],
        "vectors": vector_index["vectors"],
    }


def answer_question(index: Dict, question: str, model_name: str) -> Dict:
    results = retrieve(index, question, top_k=5, min_score=0.20)

    if not results:
        return {
            "supported": False,
            "answer": "I could not find enough supporting information in the provided manual.",
            "safety_note": "",
            "sources": [],
        }

    context = build_context(results)
    generated = generate_answer(question, context, model_name)

    by_id = {item["id"]: item for item in results}
    sources = []

    for source_id in generated.get("source_ids", []):
        item = by_id.get(int(source_id))
        if item:
            sources.append(item)

    # If the model returns no valid IDs, show the retrieved evidence rather than
    # hiding it. The model still controls the grounded answer itself.
    if not sources:
        sources = results[:3]

    return {
        "supported": bool(generated.get("supported", False)),
        "answer": generated.get(
            "answer",
            "I could not find enough supporting information in the provided manual.",
        ),
        "safety_note": generated.get("safety_note", ""),
        "sources": sources,
    }


def clear_document_state() -> None:
    # Document data lives only in Streamlit session state and is cleared by app.py.
    return None
