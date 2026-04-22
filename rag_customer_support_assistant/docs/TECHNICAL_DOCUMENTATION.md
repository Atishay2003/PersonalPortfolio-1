# Technical Documentation

## 1. Introduction

### What is RAG?
Retrieval-Augmented Generation (RAG) combines:
1. Retrieval from an external knowledge source (PDF chunks in vector DB)
2. Generation by an LLM using retrieved context

This reduces hallucinations and improves factual consistency.

### Why needed?
Customer support requires policy-consistent answers. Pure LLM chat can invent policies. RAG ensures answers are grounded in official support docs.

### Use Case Overview
A customer asks a question; system retrieves relevant policy content; LLM replies with grounded response; difficult cases escalate to humans.

## 2. System Architecture Explanation

The architecture has two pipelines:
1. **Offline ingestion pipeline**
   - PDF load -> chunk -> embed -> Chroma persist
2. **Online query pipeline**
   - query -> LangGraph process -> retrieval + generation -> route -> output

Components interact through typed state and structured response objects.

## 3. Design Decisions

### Chunk size choice
- 800 chars with 120 overlap
- Balances semantic completeness and retrieval precision

### Embedding strategy
- `text-embedding-3-small`
- Good price/performance for internship project scale

### Retrieval approach
- Similarity top-k (k=4)
- Score-based confidence estimation

### Prompt design logic
- Force model to answer only from context
- If context missing, instruct conservative response

## 4. Workflow Explanation

### LangGraph usage
LangGraph manages deterministic routing and state transitions.

### Node responsibilities
- `process_node`: intent detect, retrieval, confidence estimation, answer drafting
- `output_node`: finalize message and format result

### State transitions
`query -> process_node -> conditional route -> output_node -> response`

## 5. Conditional Logic

### Intent detection
Simple rule-based keyword detector:
- Billing/refund
- Password/account
- Technical issue
- Complex/sensitive

### Routing decisions
Escalate when:
- Confidence low
- No context
- Sensitive/complex intent

Else auto-answer.

## 6. HITL Implementation

### Role of human intervention
- Resolve policy ambiguity
- Handle high-risk customer issues
- Ensure legal/compliance safeguards

### Benefits
- Better safety
- Better trust
- Prevents incorrect automated decisions

### Limitations
- Human queue adds delay
- Needs operational support team

## 7. Challenges & Trade-offs

1. **Retrieval accuracy vs speed**
   - Higher top-k improves recall but increases latency.
2. **Chunk size vs context quality**
   - Larger chunks preserve meaning but can dilute precision.
3. **Cost vs performance**
   - Larger LLMs improve quality but raise cost.

## 8. Testing Strategy

### Approach
- Unit checks for config and ingestion path
- Functional tests for query routes
- Manual CLI/API scenario tests

### Sample queries
1. “How do I reset password?” -> auto-answer
2. “I have legal dispute and urgent account lock” -> HITL escalation
3. “What is your spaceship refund policy?” (if not in doc) -> low confidence escalation

## 9. Future Enhancements

- Multi-document collections
- Hybrid search (keyword + vector)
- Re-ranking model
- Feedback loop from resolved tickets
- Session memory + personalization
- Cloud deployment (Docker + managed vector DB)

