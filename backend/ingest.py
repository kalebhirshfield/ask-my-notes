import chromadb
import httpx
import hashlib

CHROMA_PATH = "./chroma_db"
COLLECTION_NAME = "notes"
OLLAMA_EMBED_URL = "http://localhost:11434/api/embeddings"
EMBED_MODEL = "nomic-embed-text"
CHUNK_SIZE = 400  # number of characters (approximation for tokens)
CHUNK_OVERLAP = 80

_client = chromadb.PersistentClient(path=CHROMA_PATH)
_collection = _client.get_or_create_collection(COLLECTION_NAME)


def chunk_text(text: str) -> list[str]:
    """Split text into overlapping fixed-size character chunks."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


def embed(text: str) -> list[float]:
    """Call Ollama's /api/embeddings endpoint and return the vector."""
    response = httpx.post(
        OLLAMA_EMBED_URL,
        json={"model": EMBED_MODEL, "prompt": text},
        timeout=60,  # raise on slower machines
    )
    response.raise_for_status()
    return response.json()["embedding"]


def ingest_files(texts: dict[str, str]) -> int:
    """Chunk, embed, and store all documents. Returns total chunk count."""
    total = 0
    for filename, content in texts.items():
        chunks = chunk_text(content)
        for i, chunk in enumerate(chunks):
            doc_id = hashlib.md5(f"{filename}:{i}:{chunk}".encode()).hexdigest()
            vector = embed(chunk)
            _collection.upsert(
                ids=[doc_id],
                documents=[chunk],
                embeddings=[vector],
                metadatas=[{"source": filename, "chunk_index": i}],
            )
            total += 1
    return total
