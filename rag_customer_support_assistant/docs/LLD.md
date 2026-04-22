# Low-Level Design (LLD)

## 1. Module-Level Design

### 1.1 Document Processing Module (`src/ingest.py`)
- Load PDF using `PyPDFLoader`
- Validate path and page count
- Pass raw pages to chunking module

### 1.2 Chunking Module (`src/ingest.py`)
- `RecursiveCharacterTextSplitter`
- Defaults:
  - `chunk_size=800`
  - `chunk_overlap=120`

### 1.3 Embedding Module (`src/ingest.py`, `src/rag_graph.py`)
- `OpenAIEmbeddings`
- Model: configurable from `.env`

### 1.4 Vector Storage Module (`src/ingest.py`)
- `Chroma.from_documents(...)`
- Persists in `artifacts/chroma_db`

### 1.5 Retrieval Module (`src/rag_graph.py`)
- Similarity search with score
- Return top-k docs with metadata + score

### 1.6 Query Processing Module (`src/rag_graph.py`)
- Heuristic intent detection
- Context retrieval
- Prompt creation
- LLM invocation

### 1.7 Graph Execution Module (`src/rag_graph.py`)
- LangGraph `StateGraph`
- Nodes:
  - `process_node`
  - `output_node`
- Conditional edge decides route

### 1.8 HITL Module (`src/rag_graph.py`)
- Build escalation ticket payload
- Save in JSON file with timestamp + query + context snapshot

## 2. Data Structures

### 2.1 Document Representation
```python
Document(page_content: str, metadata: dict)
```

### 2.2 Chunk Format
```python
{
  "content": "...",
  "metadata": {
    "source": "data/knowledge_base.pdf",
    "page": 3,
    "chunk_id": "..."
  }
}
```

### 2.3 Embedding Structure
```python
List[float]  # embedding vector per chunk/query
```

### 2.4 Query-Response Schema
```json
{
  "query": "string",
  "answer": "string",
  "route": "auto_answer | hitl_escalation",
  "confidence": 0.0,
  "intent": "string",
  "sources": [
    {
      "content_preview": "string",
      "metadata": {}
    }
  ],
  "hitl_ticket_id": "string | null"
}
```

### 2.5 LangGraph State Object
```python
{
  "query": str,
  "intent": str,
  "retrieved_docs": list,
  "confidence": float,
  "answer": str,
  "route": str,
  "hitl_ticket_id": str | None
}
```

## 3. Workflow Design (LangGraph)

- Entry: `process_node`
- Conditional edge: `route_decision(state)`
- Destination:
  - If escalation -> `output_node` (hitl response)
  - Else -> `output_node` (auto answer)

State flows through both nodes.

## 4. Conditional Routing Logic

### 4.1 Auto Answer Criteria
- Confidence >= threshold (default 0.65)
- Retrieved docs available
- Intent not in sensitive/complex list

### 4.2 Escalation Criteria
- Confidence < threshold
- Retrieved docs empty
- Query flagged as complex/sensitive (threat, legal, urgent lockout)

## 5. HITL Design

### 5.1 Trigger
Inside `process_node` after confidence + intent evaluation.

### 5.2 Post-Trigger Actions
- Generate ticket id (`HITL-YYYYMMDD-HHMMSS`)
- Append record to `artifacts/hitl_tickets.json`
- Send user escalation message

### 5.3 Human Response Integration
Current phase: manual review using ticket file.
Future phase: CRM webhook callback to close loop.

## 6. API / Interface Design

### Input
`POST /query`
```json
{"query": "How can I cancel my subscription?"}
```

### Output
Structured JSON containing answer, route, confidence, sources, and ticket id.

### Interaction Flow
Client -> FastAPI -> LangGraph -> Retriever/LLM -> Router -> Response.

## 7. Error Handling

1. **Missing data / PDF not found**
   - Raise clear `FileNotFoundError`
2. **No relevant chunks found**
   - Route to HITL with fallback message
3. **LLM failure**
   - Catch exception and escalate safely
4. **Vector DB missing**
   - Return instruction to run ingestion first

