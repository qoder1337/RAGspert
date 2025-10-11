from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models.user import User
from src.schemas.user import UserCreate, UserUpdate


async def create_user(db: AsyncSession, user: UserCreate) -> User:
    """Creates a new user in the database."""
    db_user = User(
        username=user.username,
        hashed_password=f"hashed_{user.password}",  # TODO: real Hashing
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user(db: AsyncSession, user_id: int) -> User | None:
    """Fetches a user by their ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Fetches a user by their username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> list[User]:
    """Fetches a list of users with pagination."""
    result = await db.execute(select(User).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_user(db: AsyncSession, user: User, user_update: UserUpdate) -> User:
    """Updates a user's information."""
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = f"hashed_{update_data.pop('password')}"

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    """Deletes a user from the database."""
    await db.delete(user)
    await db.commit()
