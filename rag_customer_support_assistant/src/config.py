from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
CHROMA_DIR = BASE_DIR / os.getenv("CHROMA_DIR", "artifacts/chroma_db")
PDF_PATH = BASE_DIR / os.getenv("PDF_PATH", "data/knowledge_base.pdf")
TOP_K = int(os.getenv("TOP_K", "4"))
CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", "0.65"))
HITL_FILE = BASE_DIR / "artifacts/hitl_tickets.json"

for path in [CHROMA_DIR, HITL_FILE.parent]:
    path.mkdir(parents=True, exist_ok=True)


def validate_env() -> None:
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is missing. Please configure your .env file.")
