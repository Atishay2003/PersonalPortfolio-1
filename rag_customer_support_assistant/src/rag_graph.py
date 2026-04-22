from __future__ import annotations

from datetime import datetime
import json
from typing import Dict, List, Literal, TypedDict, Optional

from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.graph import StateGraph, END

from .config import (
    CHROMA_DIR,
    EMBEDDING_MODEL,
    MODEL_NAME,
    TOP_K,
    CONFIDENCE_THRESHOLD,
    HITL_FILE,
    validate_env,
)


class GraphState(TypedDict):
    query: str
    intent: str
    retrieved_docs: List[Dict]
    confidence: float
    answer: str
    route: Literal["auto_answer", "hitl_escalation"]
    hitl_ticket_id: Optional[str]


def detect_intent(query: str) -> str:
    q = query.lower()
    if any(k in q for k in ["refund", "charged", "billing", "invoice"]):
        return "billing"
    if any(k in q for k in ["password", "login", "account", "locked"]):
        return "account"
    if any(k in q for k in ["error", "bug", "not working", "failed"]):
        return "technical"
    if any(k in q for k in ["legal", "sue", "lawyer", "urgent", "threat", "complaint"]):
        return "complex"
    return "general"


def get_vector_store() -> Chroma:
    validate_env()
    embedding = OpenAIEmbeddings(model=EMBEDDING_MODEL)
    return Chroma(persist_directory=str(CHROMA_DIR), embedding_function=embedding)


def save_hitl_ticket(state: GraphState) -> str:
    ticket_id = datetime.utcnow().strftime("HITL-%Y%m%d-%H%M%S")
    payload = {
        "ticket_id": ticket_id,
        "created_at_utc": datetime.utcnow().isoformat(),
        "query": state["query"],
        "intent": state["intent"],
        "confidence": state["confidence"],
        "retrieved_docs": state["retrieved_docs"],
    }

    existing = []
    if HITL_FILE.exists():
        with HITL_FILE.open("r", encoding="utf-8") as f:
            try:
                existing = json.load(f)
            except json.JSONDecodeError:
                existing = []

    existing.append(payload)
    with HITL_FILE.open("w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2)

    return ticket_id


def process_node(state: GraphState) -> GraphState:
    query = state["query"]
    intent = detect_intent(query)

    vector_store = get_vector_store()
    docs_with_scores = vector_store.similarity_search_with_score(query, k=TOP_K)

    retrieved_docs: List[Dict] = []
    for doc, score in docs_with_scores:
        retrieved_docs.append(
            {
                "content_preview": doc.page_content[:240],
                "metadata": doc.metadata,
                "score": float(score),
            }
        )

    if not docs_with_scores:
        confidence = 0.0
    else:
        avg_score = sum(float(score) for _, score in docs_with_scores) / len(docs_with_scores)
        confidence = max(0.0, min(1.0, 1.0 / (1.0 + avg_score)))

    should_escalate = (
        confidence < CONFIDENCE_THRESHOLD
        or len(retrieved_docs) == 0
        or intent == "complex"
    )

    if should_escalate:
        answer = "I have escalated this issue to a human support agent."
        route: Literal["auto_answer", "hitl_escalation"] = "hitl_escalation"
        hitl_ticket_id = save_hitl_ticket(
            {
                "query": query,
                "intent": intent,
                "retrieved_docs": retrieved_docs,
                "confidence": confidence,
                "answer": answer,
                "route": route,
                "hitl_ticket_id": None,
            }
        )
    else:
        llm = ChatOpenAI(model=MODEL_NAME, temperature=0)
        context = "\n\n".join(d["content_preview"] for d in retrieved_docs)
        prompt = (
            "You are a customer support assistant. Answer ONLY from the provided context. "
            "If context is not sufficient, clearly say so.\n\n"
            f"Context:\n{context}\n\n"
            f"User Query: {query}\n\n"
            "Answer in a concise and friendly way."
        )
        answer = llm.invoke(prompt).content
        route = "auto_answer"
        hitl_ticket_id = None

    return {
        **state,
        "intent": intent,
        "retrieved_docs": retrieved_docs,
        "confidence": confidence,
        "answer": answer,
        "route": route,
        "hitl_ticket_id": hitl_ticket_id,
    }


def output_node(state: GraphState) -> GraphState:
    return state


def route_decision(state: GraphState) -> str:
    return state["route"]


def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("process", process_node)
    workflow.add_node("output", output_node)
    workflow.set_entry_point("process")
    workflow.add_conditional_edges(
        "process",
        route_decision,
        {
            "auto_answer": "output",
            "hitl_escalation": "output",
        },
    )
    workflow.add_edge("output", END)
    return workflow.compile()


def run_query(query: str) -> Dict:
    app = build_graph()
    result = app.invoke(
        {
            "query": query,
            "intent": "",
            "retrieved_docs": [],
            "confidence": 0.0,
            "answer": "",
            "route": "auto_answer",
            "hitl_ticket_id": None,
        }
    )

    return {
        "answer": result["answer"],
        "route": result["route"],
        "confidence": round(result["confidence"], 3),
        "intent": result["intent"],
        "sources": [
            {
                "content_preview": d["content_preview"],
                "metadata": d["metadata"],
            }
            for d in result["retrieved_docs"]
        ],
        "hitl_ticket_id": result["hitl_ticket_id"],
    }
