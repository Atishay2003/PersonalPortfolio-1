# High-Level Design (HLD)

## 1. System Overview

### Problem Definition
Customers ask support questions but response quality is inconsistent and expensive when every query needs a human agent. We need an assistant that answers from official policy documents and escalates hard cases to humans.

### Scope
- Ingest one or more customer-support PDFs
- Build embeddings and store in ChromaDB
- Retrieve relevant chunks per user query
- Generate grounded answer with LLM
- Use LangGraph workflow orchestration
- Route to auto-answer or HITL escalation

Out of scope (phase 1): multilingual support, CRM integrations, advanced analytics dashboard.

## 2. Architecture Diagram (Mandatory)

```text
+-------------------+        +------------------------------+
| User (CLI/Web/API)| -----> | LangGraph Workflow Orchestr. |
+-------------------+        +------------------------------+
                                      |
                                      v
                            +--------------------+
                            | Processing Node    |
                            | - Intent detect    |
                            | - Retrieve chunks  |
                            | - Generate answer  |
                            +--------------------+
                                      |
                      +---------------+----------------+
                      | Conditional Routing            |
                      v                                v
            +--------------------+            +--------------------+
            | Output: Auto Answer|            | Output: HITL Route |
            +--------------------+            +--------------------+
                                                      |
                                                      v
                                            +----------------------+
                                            | Human Support Queue  |
                                            | (Ticket Store/File)  |
                                            +----------------------+

Ingestion Pipeline (offline/background):
PDF Loader -> Chunker -> Embedding Model -> ChromaDB
```

## 3. Component Description

1. **Document Loader**: Reads PDF pages with metadata.
2. **Chunking Strategy**: Splits text into semantic chunks (size 800, overlap 120).
3. **Embedding Model**: Converts chunks into vectors (`text-embedding-3-small`).
4. **Vector Store**: ChromaDB persistent collection for chunk retrieval.
5. **Retriever**: Similarity search top-k chunks for query context.
6. **LLM**: Generates grounded response using retrieved context.
7. **Graph Workflow Engine**: LangGraph state machine for deterministic flow.
8. **Routing Layer**: Chooses `auto_answer` or `hitl_escalation`.
9. **HITL Module**: Creates escalation ticket and records context.

## 4. Data Flow

### PDF to Answer
1. PDF file uploaded/placed in data folder.
2. Loader reads pages.
3. Chunker splits content.
4. Embedder creates vectors.
5. Chroma stores vectors + metadata.
6. User query enters graph.
7. Query embedding created; retriever fetches relevant chunks.
8. LLM answers from context.
9. Router decides auto-answer vs escalation.
10. Response returned to user.

### Query Lifecycle
`Input -> Process Node -> Route Decision -> Output Node -> API Response`

## 5. Technology Choices

- **ChromaDB**: Local, lightweight, persistent, easy for internship demo.
- **LangGraph**: Explicit control flow + state management + easy conditional routing.
- **OpenAI LLM** (`gpt-4o-mini`): Strong instruction following, cost-effective.
- **FastAPI**: Quick API exposure and interactive docs.
- **Python**: Rich ecosystem for LLM and retrieval tools.

## 6. Scalability Considerations

1. **Large Documents**
   - Batch ingestion
   - Preprocessing cache
   - Multi-collection indexing
2. **High Query Load**
   - Add API worker scaling
   - Introduce Redis cache for repeat queries
3. **Latency**
   - Reduce `top_k`
   - Use hybrid retrieval strategy
   - Stream partial responses

