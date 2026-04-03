# Ask My Notes

## About
- Self hosted retrieval-augmented generation (RAG) app

## Stack
- Next.js
- FastAPI
- ChromaDB
- Ollama

## Getting Started
- Install llama3.2 and nomic-embed-text using Ollama
```
ollama pull nomic-embed-text
ollama pull llama3.2
```
- Install python dependencies
```
pip install -r requirements.txt
```
- Open two terminals and navigate to the root of the project in both
- In the first activate the python environment that you used to install the requirements, then run 
```
cd backend
uvicorn main:app --reload --port 8000
```
- In the second, run
```
cd frontend
npm run dev
```
