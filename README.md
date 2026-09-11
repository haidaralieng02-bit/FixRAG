# FixRAG — AI Technician Troubleshooting Assistant

**From Fault to Fix, Grounded in the Manual.**

FixRAG is an evidence-grounded troubleshooting assistant for technical equipment manuals.
A user uploads a PDF, asks a natural-language troubleshooting question, and receives a
structured answer based on semantically retrieved sections of that manual.

## Problem

Technicians and equipment operators often know the symptom but not the exact terminology
used by a manufacturer manual. Searching hundreds of pages with keyword search is slow,
fragmented, and makes it difficult to tell whether the answer is actually supported by
the documentation.

## Solution

FixRAG uses standard Retrieval-Augmented Generation (RAG):

**PDF → page-aware text extraction → chunking → embeddings → vector similarity retrieval
→ grounded context → Groq LLM → structured answer + evidence**

The application deliberately does not use agents, multi-agent workflows, fine-tuning,
IoT, computer vision, or autonomous repair.

## Features

- Upload a technical PDF
- Page-aware text extraction
- Semantic embeddings with `all-MiniLM-L6-v2`
- In-memory cosine-similarity retrieval
- Fixed Groq model: `openai/gpt-oss-120b`
- Grounded troubleshooting response
- Structured model output
- Source/page evidence
- Explicit insufficient-evidence behavior
- Safety-aware response instructions
- Processing/chunk counts
- Reset document
- Helpful demo questions
- Streamlit Community Cloud friendly configuration

## Architecture

```text
                 ┌─────────────────────┐
                 │ Technical PDF       │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ PyMuPDF extraction  │
                 │ + page metadata     │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Page-aware chunks   │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Sentence embeddings │
                 │ MiniLM              │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ In-memory vectors   │
                 └──────────┬──────────┘
                            │
             User question │
                            ↓
                 ┌─────────────────────┐
                 │ Question embedding  │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Cosine similarity   │
                 │ Top-K retrieval     │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Grounded context    │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Groq GPT-OSS 120B   │
                 └──────────┬──────────┘
                            ↓
                 ┌─────────────────────┐
                 │ Answer + evidence   │
                 └─────────────────────┘
```

## RAG workflow

1. User uploads one PDF.
2. PyMuPDF extracts text page by page.
3. Text is cleaned and split into overlapping chunks while retaining page metadata.
4. Sentence Transformers creates normalized semantic embeddings.
5. The embeddings are kept in memory for the current Streamlit session.
6. The question is embedded using the same model.
7. Cosine similarity ranks the most relevant chunks.
8. Only the top retrieved context is sent to Groq; the full PDF is never sent to the LLM.
9. The fixed Groq model generates structured JSON under a strict schema.
10. The app displays the answer and the supporting manual evidence.

## Tech stack

- Python
- Streamlit
- Groq API
- `openai/gpt-oss-120b`
- PyMuPDF
- Sentence Transformers
- NumPy
- GitHub
- Streamlit Community Cloud

### Groq model note

FixRAG uses `openai/gpt-oss-120b`, directly defined in `app.py`.
There is intentionally no model selector.

Groq currently lists GPT-OSS 120B as a production model, and its free-plan rate-limit
table currently includes 30 RPM, 1K requests/day, 8K tokens/minute, and 200K tokens/day.
Limits are account/platform dependent and can change, so check Groq's current documentation
before a live hackathon demo.

## Installation

Recommended Python version: **3.11**.

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd FixRAG

python -m venv .venv
```

Activate the environment:

### Windows PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

### macOS/Linux

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## Local secrets setup

Create:

```text
.streamlit/secrets.toml
```

with:

```toml
GROQ_API_KEY = "PASTE_YOUR_REAL_KEY_HERE"
```

Never commit this file.

The repository contains only:

```text
.streamlit/secrets.toml.example
```

which contains a placeholder.

## Run locally

```bash
streamlit run app.py
```

Open the local Streamlit URL shown in the terminal.

## GitHub

1. Create a new GitHub repository.
2. Copy the FixRAG project into the repository.
3. Confirm `.streamlit/secrets.toml` is not tracked.
4. Confirm no API key appears in source code, README, screenshots, or commit history.
5. Commit and push.

Example:

```bash
git init
git add .
git commit -m "Initial FixRAG hackathon project"
git branch -M main
git remote add origin <YOUR_GITHUB_REPOSITORY_URL>
git push -u origin main
```

## Streamlit Community Cloud deployment

1. Push the repository to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app from the GitHub repository.
4. Select `app.py` as the entrypoint.
5. In the app's Secrets settings, add:

```toml
GROQ_API_KEY = "YOUR_REAL_KEY"
```

6. Deploy.
7. Test with the same manual and demo question used locally.

No API key belongs in GitHub.

## Security notes

- The Groq API key is read from Streamlit Secrets.
- The key is never displayed by the UI.
- The key is never written to application files.
- `.streamlit/secrets.toml` is ignored by Git.
- Errors are converted into user-friendly messages rather than displaying credentials.
- Uploaded documents and vectors are held in the current Streamlit session; this MVP does
  not create a permanent document database.

## Safety

FixRAG is an AI-assisted documentation tool, not an autonomous repair system.

Technical manuals can describe high voltage, electrical panels, moving machinery,
stored energy, heat, pressure, or other hazards. Users must follow the manufacturer's
safety procedures. Hazardous work should be performed by appropriately qualified personnel.

FixRAG never intentionally invents safety procedures. If the retrieved manual does not
support a safety claim, the model is instructed not to present it as manufacturer guidance.

## Limitations

- Scanned/image-only PDFs without a text layer are not supported in this MVP.
- Complex tables and diagrams may not extract perfectly.
- Retrieval quality depends on the quality of extracted text and chunking.
- The in-memory index is rebuilt when the document changes.
- The app uses a single technical document at a time.
- The model can still make mistakes; source evidence should be checked before acting.
- Groq free-plan limits can change and are not guaranteed indefinitely.
- This MVP is not intended for autonomous machine control or autonomous repair.

## Demo instructions

### Best demo

Use a text-readable VFD or motor-drive service manual.

Upload it, then ask:

> The motor stops after several minutes and the drive shows an overload fault.
> What should I check first, and what are the possible causes according to the manual?

Show:

1. The PDF is indexed.
2. The number of pages/chunks.
3. The troubleshooting answer.
4. Source pages and retrieved excerpts.
5. The safety note.

### Grounding demo

Then ask a question that the manual clearly does not answer, for example:

> Can this drive operate underwater?

FixRAG should explicitly say:

> I could not find enough supporting information in the provided manual.

This demonstrates that the application is designed not to fabricate unsupported answers.

## Hackathon positioning

FixRAG is **not simply Chat with PDF**.

It is a documentation-grounded troubleshooting workflow:

**Manual → Evidence → Troubleshooting guidance → Source/page**

The core value is turning a long technical manual into a fast, evidence-aware troubleshooting
interface.

## Project structure

```text
FixRAG/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── secrets.toml.example
├── core/
│   ├── __init__.py
│   ├── pdf_processor.py
│   ├── embeddings.py
│   ├── retriever.py
│   ├── llm.py
│   ├── prompts.py
│   └── rag_pipeline.py
├── utils/
│   ├── __init__.py
│   └── helpers.py
└── sample/
    └── README.md
```
