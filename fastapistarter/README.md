# FastAPI Starter (async)

A work in progress Starter Kit for async FastAPI without the fluff.
Debloated 3-Environment Setup with async sqlalchemy integration.
ENV-management with the handy pydantic-settings package.
Starting with 3 local sqlite DBs via aiosqlite-connector. (development, testing, production).
The template follows common best-practices and is an optimal debloated starting point.

## What's in it?

- 3 Stages / ENVIRONMENTs: development, testing, production
- real async DB-logic with sqlalchemy
- uvicorn with uvloop (faster async)
- logging
- prod-ready folder structure

## ! Important !
- a real PW Hashing function is missing: this is just for demonstrational purposes

## Installation
- uv sync
- rename example.env to .env and add external DB credentials and API-Key (optional)
- For Production you should at least switch the corresponding production-DB to mySQL (uv add aiomysql) or Postgres (uv add asyncpg)

## TODO

- implement a basic test suite
- add alembic
