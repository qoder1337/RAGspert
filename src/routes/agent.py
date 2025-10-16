import asyncio
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from src.shared.templates import templates


agent_route = APIRouter(prefix="/agent", tags=["AGENT"])


@agent_route.get("/crawl", response_class=HTMLResponse)
async def crawl_form(request: Request):
    """Display the agent interaction form."""
    return templates.TemplateResponse("crawl.html", {"request": request})


@agent_route.post("/crawl", response_class=HTMLResponse)
async def start_crawl(request: Request, url: str = Form(...), name: str = Form(...)):
    """Start crawling documentation."""
    from src.utils.crawl_site import init_crawling

    try:
        if not url.startswith(("http://", "https://")):
            return templates.TemplateResponse(
                "crawl.html",
                {
                    "request": request,
                    "error": "❌ URL must start with http:// oder https://",
                },
            )
        # TODO: Store name in metadata
        asyncio.create_task(init_crawling(url_or_sitemap=url, source_name=name))

        return templates.TemplateResponse(
            "crawl.html",
            {
                "request": request,
                "message": f"🕷️ Crawling started: '{name}' - ({url}) - This will take a while",
                "name": name,
            },
        )

    except Exception as e:
        return templates.TemplateResponse(
            "crawl.html", {"request": request, "error": f"❌ Fehler: {str(e)}"}
        )


@agent_route.get("/crawl/status/{name}")
async def get_crawl_status(name: str):
    """Get crawl status as JSON."""
    from src.utils.crawl_status import crawl_status

    status = crawl_status.get(name)
    print(f"📊 Status request for '{name}': {status}")
    return status


@agent_route.get("/ask", response_class=HTMLResponse, name="ask_form")
async def ask_form(request: Request):
    """Display ask form with available docs."""

    try:
        async with get_db() as session:
            result = await session.execute(
                select(distinct(SitePage.meta_details["source"].astext)).where(
                    SitePage.meta_details["source"].astext.isnot(None)
                )
            )
            available_docs = [row[0] for row in result.fetchall()]
    except Exception as e:
        print(f"Error loading docs: {e}")
        available_docs = []

    message = None
    if not available_docs:
        message = "⚠️ No documentation crawled yet. Go to /agent/crawl first!"

    return templates.TemplateResponse(
        "ask.html",
        {"request": request, "available_docs": available_docs, "message": message},
    )


@agent_route.post("/ask", response_class=HTMLResponse)
async def ask_question(
    request: Request, source: str = Form(...), question: str = Form(...)
):
    """Process question and return answer in same page."""

    # Hole Docs-Liste für Dropdown
    async with get_db() as session:
        result = await session.execute(
            select(distinct(SitePage.meta_details["source"].astext)).where(
                SitePage.meta_details["source"].astext.isnot(None)
            )
        )
        available_docs = [row[0] for row in result.fetchall()]

    try:
        print(f"❓ Question: '{question}' for source: '{source}'")

        # ✅ RAG Agent aufrufen
        answer_data = await search_and_answer(question=question, source_filter=source)

        # answer_data kann sein: {"answer": "...", "sources": [...]}
        # oder nur ein String
        if isinstance(answer_data, dict):
            answer = answer_data.get("answer", "")
            sources = answer_data.get("sources", [])
        else:
            answer = answer_data
            sources = []

        print(f"✅ Answer generated: {len(answer)} chars")

        return templates.TemplateResponse(
            "ask.html",
            {
                "request": request,
                "available_docs": available_docs,
                "question": question,
                "source": source,
                "answer": answer,  # ✅ Antwort im Template
                "sources": sources,
            },
        )

    except Exception as e:
        print(f"❌ Error: {e}")
        return templates.TemplateResponse(
            "ask.html",
            {
                "request": request,
                "available_docs": available_docs,
                "question": question,
                "source": source,
                "error": f"❌ Error: {str(e)}",
            },
        )
