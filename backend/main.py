from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List

from ingest import ingest_files
from query import stream_answer

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str


@app.post("/ingest")
async def ingest(files: List[UploadFile] = File(...)):
    texts = {}
    for f in files:
        content = await f.read()
        texts[f.filename] = content.decode("utf-8", errors="ignore")
    count = ingest_files(texts)
    return {"message": f"Indexed {count} chunks from {len(files)} file(s)"}


@app.post("/ask")
async def ask(req: AskRequest):
    return StreamingResponse(
        stream_answer(req.question),
        media_type="text/event-stream",
    )
