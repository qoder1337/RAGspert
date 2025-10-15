# RAGspert

A work in progress DEMO of best-practices to implement a local RAG into a Frontier-LLM.


## ! Important !
In real prodcution, you should most likely go with three separate dbs for prod, dev, test instead of my TABLE_PREFIX approach.

## What's in it?
FastAPI, PostgreSQL (with pgvector), Gemini (2.5 Flash-Lite & Embedding), pydantic AI, Crawl4AI

## Installation
- uv sync
- rename example.env to .env and add external DB credentials and API-Key (optional)

## TODO

- add Ollama and/or vllm for more privacy
