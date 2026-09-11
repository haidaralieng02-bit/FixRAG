from __future__ import annotations

import streamlit as st


def get_groq_api_key() -> str:
    try:
        key = st.secrets["GROQ_API_KEY"]
    except Exception as exc:
        raise RuntimeError(
            "GROQ_API_KEY is missing. Add it to Streamlit Secrets before asking a question."
        ) from exc

    if not isinstance(key, str) or not key.strip():
        raise RuntimeError("GROQ_API_KEY is empty. Add a valid Groq API key to Streamlit Secrets.")

    return key.strip()


def safe_error_message(exc: Exception) -> str:
    message = str(exc).lower()

    if "rate limit" in message or "429" in message:
        return "Groq rate limit reached. Please wait briefly and try again."
    if "401" in message or "authentication" in message or "invalid api key" in message:
        return "Groq authentication failed. Check the GROQ_API_KEY configured in Streamlit Secrets."
    if "403" in message or "permission" in message:
        return "The configured Groq account does not have permission to use the selected model."
    if "timeout" in message or "connection" in message or "network" in message:
        return "The AI service could not be reached. Check the network connection and try again."
    if "25 mb" in message:
        return str(exc)
    if "pdf" in message or "extractable text" in message:
        return str(exc)

    return "FixRAG could not complete this operation. Please try again or upload a different PDF."
