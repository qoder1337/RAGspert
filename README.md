# RAGspert
A DEMO of best-practices to implement a personal local RAG into a Frontier-LLM.

## ! Important !
In real production, you should most likely go with three separate dbs for prod, dev, test instead of my TABLE_PREFIX approach.

## What's in it?
FastAPI, PostgreSQL (with pgvector), Gemini (Gemini Embedding, Gemini 2.0 Flash-Lite for summaries in pgvector & Gemini 2.5 Flash-Lite for Q&A), pydantic AI, Crawl4AI, curl-cffi, python-markdown

## Installation
- uv sync
- rename example.env to .env and add external DB credentials and API-Key (optional)

## TODO
- add crawling fallbacks, in case sitemap is not existing
- add Ollama and/or vllm for more privacy-focused llm inference
- user-based accounts
