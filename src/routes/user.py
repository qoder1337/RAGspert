from fastapi import APIRouter, HTTPException, status
from src.database import DBSessionDep_pgvector
from src.schemas.user import User as UserSchema, UserCreate, UserUpdate
from src.utils.app_logger import logmsg
from src.crud import user as user_crud


user_route = APIRouter(prefix="/users", tags=["USERS"])


@user_route.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: DBSessionDep_pgvector):
    """NEW User"""
    db_user = await user_crud.get_user_by_username(db, username=user.username)
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already exists"
        )

    new_user = await user_crud.create_user(db=db, user=user)
    logmsg.info(f"new user created: {new_user.username}")
    return new_user


@user_route.get("/{user_id}", response_model=UserSchema)
async def get_user(user_id: int, db: DBSessionDep_pgvector):
    """GET User by ID"""
    user = await user_crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User nicht gefunden"
        )
    return user


@user_route.get("/", response_model=list[UserSchema])
async def list_users(db: DBSessionDep_pgvector, skip: int = 0, limit: int = 100):
    """Lists all Users"""
    users = await user_crud.get_users(db, skip=skip, limit=limit)
    return users


@user_route.patch("/{user_id}", response_model=UserSchema)
async def update_user(user_id: int, user_update: UserUpdate, db: DBSessionDep_pgvector):
    """Updates a User (partial update)"""
    user = await user_crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User nicht gefunden"
        )

    updated_user = await user_crud.update_user(
        db=db, user=user, user_update=user_update
    )
    return updated_user


@user_route.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: DBSessionDep_pgvector):
    """DELETE User"""
    user = await user_crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    await user_crud.delete_user(db=db, user=user)
    logmsg.info(f"user deleted: {user.username}")
