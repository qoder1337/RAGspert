from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from src.shared.templates import templates

# from src.database import DBSessionDep_local


base_route = APIRouter(
    tags=["BASE ROUTE"],
    responses={404: {"description": "this entry is only relevant for /docs"}},
)


@base_route.get("/", response_class=HTMLResponse)
async def root(request: Request):
    flash_message = request.scope.get("flashMessage")

    return templates.TemplateResponse(
        name="info.html", context={"request": request, "flashMessage": flash_message}
    )
