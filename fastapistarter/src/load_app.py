from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from starlette.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
from src.database import (
    sessionmanager_local,
    # sessionmanager_external,
    Base,
)
from src.routes.base import base_route
from src.routes.user import user_route
from zoneinfo import ZoneInfo
# from src import globals_mapping_loader
# import os
# PRIVATE_API_KEY = os.getenv("PRIVATE_API_KEY")


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
    engine = sessionmanager_local.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    ### i.e. load precached stuff into the appstate
    # globals_mapping = globals_mapping_loader()
    # async with sessionmanager_local.session() as db:
    #     app.state.data_cache = await preload_data_cache(db)
    #     app.state.AVAILABLE_NEWS_TABLES = {k for k in globals_mapping if "news" in k}

    yield

    # Shutdown logic HERE

    # close DB Sessions
    if sessionmanager_local._engine is not None:
        await sessionmanager_local.close()
    if sessionmanager_external._engine is not None:
        await sessionmanager_external.close()


### APP INIT
app = FastAPI(lifespan=lifespan)


### MIDDLEWARE
app.add_middleware(GZipMiddleware, minimum_size=1000)


@app.middleware("http")
async def add_current_time(request: Request, call_next):
    request.state.current_time = get_berlin_time()
    response = await call_next(request)
    return response


##### API KEY AUTH
# auth_middleware
# EXCLUDED_PATHS = ("/docs", "/openapi.json", "/redoc", "/favicon.ico")


# @app.middleware("http")
# async def auth_middleware(request: Request, call_next):
#     path = request.url.path

#     # Prefix-Check
#     if path.startswith(EXCLUDED_PATHS):
#         return await call_next(request)

#     # Header case-insensitive normalisiert
#     api_key = request.headers.get("x-api-key")

#     if not api_key or api_key != PRIVATE_API_KEY:  # <- Explicit None-Check
#         return Response(
#             content='{"detail":"Unauthorized"}',
#             status_code=401,
#             media_type="application/json",
#         )

#     return await call_next(request)


### ADD ROUTES
app.include_router(base_route)
app.include_router(user_route)


### ERRORS
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=404,
        content={
            "detail": f"Route '{request.url.path}' does not exist - (Error: {exc.detail})"
        },
    )
