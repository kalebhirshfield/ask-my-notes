import chromadb
import httpx
import json
from typing import AsyncGenerator

from ingest import embed, CHROMA_PATH, COLLECTION_NAME

OLLAMA_CHAT_URL = "http://localhost:11434/api/chat"
CHAT_MODEL = "llama3.2"
TOP_K = 4

_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(COLLECTION_NAME)


def retrieve(question: str) -> list[str]:
    """Embed the question and return the top-k most relevant chunks."""
    q_vector = embed(question)
    results = _collection.query(
        query_embeddings=[q_vector],
        n_results=TOP_K,
        include=["documents", "metadatas"],
    )
    return results["documents"][0]  # list of chunk strings


def build_prompt(question: str, context_chunks: list[str]) -> str:
    context = "\n\n---\n\n".join(context_chunks)
    return (
        f"You are a helpful assistant. Answer the question using ONLY the context below.\n"
        f"If the answer is not in the context, say 'I don't have that in my notes'.\n\n"
        f"CONTEXT:\n{context}\n\n"
        f"QUESTION: {question}\n\n"
        f"ANSWER:"
    )


async def stream_answer(question: str) -> AsyncGenerator[str, None]:
    """Retrieve context, call Ollama /api/chat with stream=true, yield SSE tokens."""
    chunks = retrieve(question)
    prompt = build_prompt(question, chunks)

    async with httpx.AsyncClient(timeout=120) as client:
        async with client.stream(
            "POST",
            OLLAMA_CHAT_URL,
            json={
                "model": CHAT_MODEL,
                "messages": [{"role": "user", "content": prompt}],
                "stream": True,
            },
        ) as response:
            async for line in response.aiter_lines():
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue
                token = data.get("message", {}).get("content", "")
                if token:
                    # Emit Server-Sent Event format
                    yield f"data: {token}\n\n"
                if data.get("done"):
                    break
