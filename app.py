import streamlit as st

from core.rag_pipeline import build_document_index, answer_question, clear_document_state
from utils.helpers import get_groq_api_key, safe_error_message

MODEL_NAME = "openai/gpt-oss-120b"

st.set_page_config(
    page_title="FixRAG — AI Technician Troubleshooting Assistant",
    page_icon="🔧",
    layout="wide",
)

st.markdown("""
<style>
.hero {
    padding: 1.4rem 1.6rem;
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 16px;
    background: linear-gradient(135deg, rgba(70,110,180,.12), rgba(80,180,150,.08));
    margin-bottom: 1rem;
}
.badge {
    display: inline-block;
    padding: .25rem .55rem;
    border-radius: 999px;
    border: 1px solid rgba(128,128,128,.35);
    font-size: .82rem;
}
.source-card {
    padding: .8rem 1rem;
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 12px;
    margin-bottom: .7rem;
}
.small { color: #666; font-size: .88rem; }
</style>
""", unsafe_allow_html=True)

if "document_index" not in st.session_state:
    st.session_state.document_index = None
if "document_name" not in st.session_state:
    st.session_state.document_name = None
if "last_answer" not in st.session_state:
    st.session_state.last_answer = None

st.markdown("""
<div class="hero">
<h1>🔧 FixRAG</h1>
<p><strong>From Fault to Fix, Grounded in the Manual.</strong></p>
<p>Upload a technical equipment manual and ask a troubleshooting question.
FixRAG retrieves the most relevant manual evidence and turns it into structured,
source-aware troubleshooting guidance.</p>
<span class="badge">Standard RAG</span>
&nbsp;
<span class="badge">Evidence-grounded</span>
&nbsp;
<span class="badge">Groq-powered</span>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.header("📘 Manual")
    uploaded = st.file_uploader(
        "Upload a technical PDF",
        type=["pdf"],
        help="Use a text-readable manufacturer/service manual for best results.",
    )

    if st.button("🗑️ Clear document", use_container_width=True):
        clear_document_state()
        st.session_state.document_index = None
        st.session_state.document_name = None
        st.session_state.last_answer = None
        st.rerun()

    st.divider()
    st.subheader("Try these questions")
    examples = [
        "The motor stops after several minutes and the drive shows an overload fault. What should I check first?",
        "What does the overload fault mean according to the manual?",
        "What safety precautions should I follow before inspecting the drive?",
        "What are the possible causes of repeated motor overload?",
    ]
    for example in examples:
        st.caption("• " + example)

    st.divider()
    st.caption("AI model: GPT-OSS 120B on Groq")
    st.caption("The model is fixed in application code; users cannot select or configure it.")

if uploaded is not None:
    file_bytes = uploaded.getvalue()

    if not file_bytes:
        st.error("The uploaded PDF is empty. Please upload a valid PDF.")
    elif not uploaded.name.lower().endswith(".pdf"):
        st.error("Unsupported file type. Please upload a PDF.")
    else:
        current_key = f"{uploaded.name}:{len(file_bytes)}"
        indexed_key = st.session_state.get("indexed_key")

        if indexed_key != current_key:
            try:
                with st.status("Processing manual…", expanded=True) as status:
                    st.write("Extracting text and page metadata…")
                    index = build_document_index(file_bytes, uploaded.name)
                    st.write(f"Created {index['chunk_count']} searchable chunks.")
                    st.write("Creating semantic embeddings…")
                    st.write("Building the in-memory vector index…")
                    status.update(label="Manual indexed successfully", state="complete")

                st.session_state.document_index = index
                st.session_state.document_name = uploaded.name
                st.session_state.indexed_key = current_key
                st.session_state.last_answer = None
            except Exception as exc:
                st.error(safe_error_message(exc))
                st.session_state.document_index = None
        else:
            index = st.session_state.document_index
            if index:
                st.success(
                    f"Manual ready: **{st.session_state.document_name}** · "
                    f"{index['page_count']} pages · {index['chunk_count']} chunks"
                )

st.divider()

st.header("🛠️ Ask FixRAG")

if st.session_state.document_index is None:
    st.info("Upload a technical PDF from the sidebar to start troubleshooting.")
else:
    question = st.text_area(
        "Troubleshooting question",
        placeholder="Example: The motor stops after 10 minutes and the drive shows an overload error. What should I check first?",
        height=110,
    )

    if st.button("🔍 Troubleshoot", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Enter a troubleshooting question first.")
        else:
            try:
                get_groq_api_key()
                with st.spinner("Retrieving manual evidence and generating a grounded answer…"):
                    result = answer_question(
                        st.session_state.document_index,
                        question.strip(),
                        MODEL_NAME,
                    )
                st.session_state.last_answer = result
            except Exception as exc:
                st.error(safe_error_message(exc))

if st.session_state.last_answer:
    result = st.session_state.last_answer
    st.divider()

    if result["supported"] is False:
        st.warning("The manual did not provide enough supporting evidence for this question.")
    else:
        st.success("Answer grounded in retrieved sections of the uploaded manual.")

    st.subheader("Troubleshooting guidance")
    st.markdown(result["answer"])

    if result.get("safety_note"):
        st.warning("⚠️ Safety: " + result["safety_note"])

    st.subheader("📖 Evidence from the manual")
    sources = result.get("sources", [])
    if not sources:
        st.info("No source metadata was returned.")
    else:
        for source in sources:
            page = source.get("page")
            section = source.get("section") or "Section not identified"
            score = source.get("score")
            with st.container():
                st.markdown(
                    f'<div class="source-card"><strong>Page {page if page else "N/A"}</strong> · '
                    f'{section}<br><span class="small">Similarity: {score:.3f}</span></div>',
                    unsafe_allow_html=True,
                )
                st.caption(source.get("text", "")[:1200])

    st.caption(
        "FixRAG is an AI-assisted documentation tool, not an autonomous repair system. "
        "Always follow the equipment manufacturer's safety procedures."
    )

st.divider()
st.caption(
    "⚠️ Safety notice: Technical equipment may contain high voltage, moving machinery, "
    "stored energy, heat, or other hazards. Do not bypass safety controls. For hazardous "
    "work, follow the manufacturer's procedures and use appropriately qualified personnel."
)
