import os
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from src.database import Base, sessionmanager_pgvector
from src.routes.base import base_route
from src.routes.user import user_route
from src.routes.agent import agent_route
from zoneinfo import ZoneInfo
from src.config import BASEDIR


# change accordingly for your own Timezone
def get_berlin_time():
    return datetime.now(ZoneInfo("Europe/Berlin"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    https://fastapi.tiangolo.com/advanced/events/
    """

    # Startup logic HERE

    # # Create Local Database Tables
    engine = sessionmanager_pgvector.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # Shutdown logic HERE

    # close DB Sessions
    if sessionmanager_pgvector._engine is not None:
        await sessionmanager_pgvector.close()


### APP INIT
app = FastAPI(lifespan=lifespan)

# Serve static files
app.mount(
    "/s", StaticFiles(directory=os.path.join(BASEDIR, "src", "static")), name="static"
)


### MIDDLEWARE
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_current_time(request: Request, call_next):
    request.state.current_time = get_berlin_time()
    response = await call_next(request)
    return response


### ADD ROUTES
app.include_router(base_route)
app.include_router(user_route)
app.include_router(agent_route)


### ERRORS
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Route '{request.url.path}' does not exist - (Error: {exc.detail})"
        },
    )
