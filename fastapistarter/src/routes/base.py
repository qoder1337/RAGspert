from fastapi import APIRouter
# from src.database import DBSessionDep_local


base_route = APIRouter(
    tags=["BASE ROUTE"],
    responses={404: {"description": "this entry is only relevant for /docs"}},
)


@base_route.get("/")
async def root():
    return {"message": "FastAPI async Starter"}
