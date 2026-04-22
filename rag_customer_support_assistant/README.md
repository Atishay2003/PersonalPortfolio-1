# RAG Internship Project: Customer Support Assistant (LangGraph + HITL)

This folder contains a complete **beginner-friendly, end-to-end implementation** of your internship assignment.

It includes:
- ✅ High-Level Design (HLD)
- ✅ Low-Level Design (LLD)
- ✅ Technical Documentation
- ✅ Working Python project using **RAG + ChromaDB + LangGraph + HITL**
- ✅ Windows CMD step-by-step setup and run guide
- ✅ Local API server ("live server") + CLI chatbot

---

## 1) Folder Structure

```text
rag_customer_support_assistant/
├── README.md
├── requirements.txt
├── .env.example
├── docs/
│   ├── HLD.md
│   ├── LLD.md
│   └── TECHNICAL_DOCUMENTATION.md
├── data/
│   └── knowledge_base.pdf   # You add your support PDF here
├── artifacts/
│   ├── chroma_db/           # Auto-created after ingestion
│   └── hitl_tickets.json    # Auto-created after first escalation
└── src/
    ├── config.py
    ├── ingest.py
    ├── rag_graph.py
    ├── api.py
    └── cli_chat.py
```

---

## 2) End-to-End Setup (Windows CMD)

Open **Command Prompt** and run commands exactly in this order.

### Step A: Go to project folder

```cmd
cd /d C:\path\to\PersonalPortfolio-1\rag_customer_support_assistant
```

### Step B: Create virtual environment

```cmd
python -m venv .venv
```

### Step C: Activate virtual environment

```cmd
.venv\Scripts\activate
```

### Step D: Install dependencies

```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Step E: Configure environment variables

```cmd
copy .env.example .env
```

Then open `.env` and set:

```env
OPENAI_API_KEY=your_openai_api_key_here
MODEL_NAME=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
CHROMA_DIR=artifacts/chroma_db
PDF_PATH=data/knowledge_base.pdf
TOP_K=4
```

### Step F: Add your PDF knowledge base

Place your support PDF in:

```text
data\knowledge_base.pdf
```

### Step G: Build vector DB (Ingestion)

```cmd
python -m src.ingest
```

Expected output (similar):

```text
Loaded pages: 24
Created chunks: 180
Persisted vector store to: artifacts/chroma_db
```

### Step H: Run CLI chatbot

```cmd
python -m src.cli_chat
```

Try sample inputs:

```text
User: How can I reset my account password?
User: My payment failed twice and account is locked, can you urgently escalate?
User: quit
```

### Step I: Run live API server (local)

```cmd
uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

Open docs in browser:

```text
http://127.0.0.1:8000/docs
```

---

## 3) API Input/Output Format

### Endpoint

`POST /query`

### Example Input JSON

```json
{
  "query": "I was charged twice. How do I request a refund?"
}
```

### Example Output JSON

```json
{
  "answer": "Based on policy, duplicate charges can be refunded within 7 days...",
  "route": "auto_answer",
  "confidence": 0.86,
  "intent": "refund",
  "sources": [
    {
      "content_preview": "Refund requests must be raised within 7 days...",
      "metadata": {
        "source": "data/knowledge_base.pdf",
        "page": 7
      }
    }
  ],
  "hitl_ticket_id": null
}
```

If escalation happens:

```json
{
  "answer": "I have escalated this issue to a human support agent.",
  "route": "hitl_escalation",
  "confidence": 0.41,
  "intent": "complex",
  "sources": [],
  "hitl_ticket_id": "HITL-20260422-120301"
}
```

---

## 4) How HITL Works

Escalation is triggered when any of the following is true:
1. Low retrieval confidence
2. No relevant context found
3. Complex / sensitive query intent (legal, threat, urgent account lock, etc.)

When escalated:
- A ticket is written to `artifacts/hitl_tickets.json`
- User receives a safe response
- Human agent can later review ticket and update customer

---

## 5) Generate PDF Deliverables

You need PDF files for submission.

Use any one method:

### Option 1 (recommended): VS Code print to PDF
1. Open each doc in `docs/`
2. `Ctrl + Shift + P` → **Markdown: Open Preview**
3. Print → Save as PDF

### Option 2: Pandoc (if installed)

```cmd
pandoc docs\HLD.md -o docs\HLD.pdf
pandoc docs\LLD.md -o docs\LLD.pdf
pandoc docs\TECHNICAL_DOCUMENTATION.md -o docs\TECHNICAL_DOCUMENTATION.pdf
```

---

## 6) Quick Demo Flow for Interview

1. Ingest PDF
2. Ask a normal FAQ → system auto-answers with context
3. Ask a risky/complex question → system escalates to HITL
4. Show `artifacts/hitl_tickets.json` entry
5. Show API docs at `/docs`

---

## 7) Troubleshooting

- **Error: OPENAI_API_KEY missing**
  - Ensure `.env` exists and has valid key.

- **Error: no module named src**
  - Run commands from `rag_customer_support_assistant` folder.

- **No chunks found / bad retrieval**
  - Ensure `data/knowledge_base.pdf` has readable text (not scanned image only).

- **Slow responses**
  - Reduce `TOP_K` to 3 and use smaller model.

