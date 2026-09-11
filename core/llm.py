from __future__ import annotations

import json
from typing import Dict, List

from groq import Groq

from core.prompts import SYSTEM_PROMPT
from utils.helpers import get_groq_api_key

ANSWER_SCHEMA = {
    "name": "fixrag_answer",
    "strict": True,
    "schema": {
        "type": "object",
        "properties": {
            "supported": {"type": "boolean"},
            "answer": {"type": "string"},
            "safety_note": {"type": "string"},
            "source_ids": {
                "type": "array",
                "items": {"type": "integer"},
            },
        },
        "required": ["supported", "answer", "safety_note", "source_ids"],
        "additionalProperties": False,
    },
}


def generate_answer(question: str, context: str, model_name: str) -> Dict:
    if not context.strip():
        return {
            "supported": False,
            "answer": "I could not find enough supporting information in the provided manual.",
            "safety_note": "",
            "source_ids": [],
        }

    client = Groq(api_key=get_groq_api_key())

    user_prompt = f"""
USER QUESTION:
{question}

RETRIEVED MANUAL CONTEXT:
{context}

Use only the retrieved manual context. Do not use outside knowledge.
"""

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_completion_tokens=1200,
        reasoning_effort="low",
        response_format={
            "type": "json_schema",
            "json_schema": ANSWER_SCHEMA,
        },
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("The Groq model returned an empty response.")

    try:
        result = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError("The AI response was not valid structured data.") from exc

    required = {"supported", "answer", "safety_note", "source_ids"}
    if not required.issubset(result):
        raise RuntimeError("The AI response was missing required fields.")

    return result
