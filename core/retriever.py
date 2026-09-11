from __future__ import annotations

from typing import Dict, List

import numpy as np

from core.embeddings import embed_query


def build_index(chunks: List[Dict]) -> Dict:
    from core.embeddings import embed_texts

    vectors = embed_texts([chunk["text"] for chunk in chunks])
    return {
        "chunks": chunks,
        "vectors": vectors,
    }


def retrieve(index: Dict, question: str, top_k: int = 5, min_score: float = 0.20) -> List[Dict]:
    if not index or not index.get("chunks") or index.get("vectors") is None:
        return []

    query_vector = embed_query(question)
    scores = index["vectors"] @ query_vector
    ranked = np.argsort(scores)[::-1]

    results = []
    for idx in ranked[:top_k]:
        score = float(scores[idx])
        if score >= min_score:
            item = dict(index["chunks"][idx])
            item["score"] = score
            results.append(item)

    return results


def build_context(results: List[Dict], max_chars: int = 9000) -> str:
    blocks = []
    total = 0

    for item in results:
        block = (
            f"[SOURCE {item['id']} | PAGE {item['page']} | SECTION {item['section']}]\n"
            f"{item['text']}\n"
        )
        if total + len(block) > max_chars:
            break
        blocks.append(block)
        total += len(block)

    return "\n".join(blocks)
