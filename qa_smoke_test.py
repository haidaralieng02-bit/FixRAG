"""Offline smoke tests that avoid optional runtime packages unavailable in this build environment.

The full application imports Streamlit, Sentence Transformers and Groq. Those packages are
intentionally not installed in this execution sandbox, so the network/model-backed tests
cannot be executed here. The tests below cover PDF extraction/chunking and prompt construction.
"""
import sys
import fitz

from core.pdf_processor import chunk_pages, extract_pages
from core.prompts import SYSTEM_PROMPT


def make_test_pdf() -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text(
        (72, 72),
        "Troubleshooting\nOverload fault\n"
        "If the motor overloads, inspect motor load and verify the motor current "
        "against the documented rating. Follow all safety procedures before inspection."
    )
    data = doc.tobytes()
    doc.close()
    return data


def main():
    pdf = make_test_pdf()

    pages = extract_pages(pdf)
    assert len(pages) == 1
    assert "Overload fault" in pages[0]["text"]

    chunks = chunk_pages(pages, chunk_size=200, overlap=30)
    assert chunks
    assert all("page" in c and "text" in c and "section" in c for c in chunks)

    context = (
        f"[SOURCE {chunks[0]['id']} | PAGE {chunks[0]['page']} | "
        f"SECTION {chunks[0]['section']}]\n{chunks[0]['text']}"
    )
    assert "PAGE 1" in context
    assert "Overload fault" in context

    assert "using ONLY" in SYSTEM_PROMPT
    assert "I could not find enough supporting information in the provided manual." in SYSTEM_PROMPT
    assert "source_ids" in SYSTEM_PROMPT

    print("PASS: PDF extraction")
    print("PASS: page-aware chunking")
    print("PASS: context/source construction")
    print("PASS: grounding prompt construction")
    print("NOT RUN: Sentence Transformer embedding/retrieval import (dependency not installed in sandbox)")
    print("NOT RUN: Streamlit startup (Streamlit not installed in sandbox)")
    print("NOT RUN: Groq API call (requires real secret/network)")
    print("NOT RUN: Streamlit Cloud deployment (external environment)")


if __name__ == "__main__":
    sys.exit(main())
