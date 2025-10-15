from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from src.shared.templates import templates
from src.agent.rag import RAGAgent

agent_route = APIRouter(prefix="/agent", tags=["AGENT"])


class AgentQuery(BaseModel):
    library_name: str
    query: str


@agent_route.get("/", response_class=HTMLResponse)
async def agent_form(request: Request):
    """Display the agent interaction form."""
    return templates.TemplateResponse("agent.html", {"request": request})


@agent_route.post("/run", response_class=HTMLResponse)
async def run_agent(
    request: Request,
    library_name: str = Form(...),
    query: str = Form(...),
):
    """Run the RAG agent with the given query and library name."""
    try:
        # Here you would typically handle the URL to crawl and process the documentation.
        # For now, we assume the documentation for the library_name is already in the database.

        agent = RAGAgent(library_name=library_name, language="de")
        result = await agent.run(query)

        return templates.TemplateResponse(
            "agent.html",
            {
                "request": request,
                "result": result,
                "library_name": library_name,
                "query": query,
            },
        )
    except Exception as e:
        return templates.TemplateResponse(
            "agent.html",
            {
                "request": request,
                "error": f"An error occurred: {e}",
                "library_name": library_name,
                "query": query,
            },
        )
