from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from .config import PDF_PATH, CHROMA_DIR, EMBEDDING_MODEL, validate_env


def ingest_pdf() -> None:
    validate_env()

    if not PDF_PATH.exists():
        raise FileNotFoundError(f"PDF not found at: {PDF_PATH}")

    loader = PyPDFLoader(str(PDF_PATH))
    pages = loader.load()
    print(f"Loaded pages: {len(pages)}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=120)
    chunks = splitter.split_documents(pages)
    print(f"Created chunks: {len(chunks)}")

    embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)

    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(CHROMA_DIR),
    )
    print(f"Persisted vector store to: {CHROMA_DIR}")


if __name__ == "__main__":
    ingest_pdf()
