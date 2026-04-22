from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .rag_graph import run_query


app = FastAPI(title="RAG Customer Support Assistant", version="1.0.0")


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Customer support question")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.post("/query")
def query_assistant(payload: QueryRequest):
    try:
        return run_query(payload.query)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
