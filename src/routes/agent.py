import asyncio
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from src.shared.templates import templates
from src.crud.agent import show_docs, url_exists
from src.database import DBSessionDep_pgvector
from src.agent.rag import RAGAgent, AnswerAgent
from markdown import markdown


agent_route = APIRouter(prefix="/agent", tags=["AGENT"])


@agent_route.get("/crawl", response_class=HTMLResponse)
async def crawl_form(request: Request):
    """Display the agent interaction form."""
    return templates.TemplateResponse("crawl.html", {"request": request})


@agent_route.post("/crawl", response_class=HTMLResponse)
async def start_crawl(
    request: Request,
    db: DBSessionDep_pgvector,
    url: str = Form(...),
    name: str = Form(...),
):
    """Start crawling documentation."""
    from src.utils.crawl_site import init_crawling

    try:
        print(f"🔍 Checking URL: {url}")

        if not url.startswith(("http://", "https://")):
            return templates.TemplateResponse(
                "crawl.html",
                {
                    "request": request,
                    "error": "❌ URL must start with http:// oder https://",
                },
            )

        if await url_exists(db, url):
            print("already crawled")
            return templates.TemplateResponse(
                "crawl.html",
                {
                    "request": request,
                    "flash_msg": "URL already crawled: go for 'ask'",
                    "error": "Already crawled",
                },
            )

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
async def ask_form(request: Request, db: DBSessionDep_pgvector):
    """Display ask form with available docs."""

    try:
        available_docs = await show_docs(db)
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
    request: Request,
    db: DBSessionDep_pgvector,
    source: str = Form(...),
    question: str = Form(...),
    use_german: bool = Form(False),
):
    """Process question and return answer."""

    try:
        available_docs = await show_docs(db)
    except Exception as e:
        print(e)
        available_docs = []

    try:
        language = "de" if use_german else "en"

        tool_agent = RAGAgent(library_name=source, language=language)
        tool_result = await tool_agent.run(
            query=question,
            source_filter=source,
        )

        answer_agent = AnswerAgent(library_name=source, language=language)

        answer = await answer_agent.run(
            query=question,
            source_filter=source,
            message_history=tool_result.new_messages(),  # Passes Tool-Results
        )

        answer_html = markdown(answer, extensions=["fenced_code", "codehilite"])

        return templates.TemplateResponse(
            "ask.html",
            {
                "request": request,
                "available_docs": available_docs,
                "question": question,
                "source": source,
                "use_german": use_german,
                "answer": answer_html,
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
