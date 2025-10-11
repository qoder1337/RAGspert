import contextlib
from fastapi import Depends
from typing import Annotated
from src.config import SET_CONF
from typing import Any, AsyncIterator
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    # https://docs.sqlalchemy.org/en/14/orm/extensions/asyncio.html#preventing-implicit-io-when-using-asyncsession
    __mapper_args__ = {"eager_defaults": True}


# Heavily inspired by https://praciano.com.br/fastapi-and-async-sqlalchemy-20-with-pytest-done-right.html
class DatabaseSessionManager:
    def __init__(self, host: str, engine_kwargs: dict[str, Any] = {}):
        self._engine = create_async_engine(host, **engine_kwargs)
        self._sessionmaker = async_sessionmaker(
            autocommit=False, bind=self._engine, expire_on_commit=False
        )

    # +++ NEW METHOD +++
    def get_engine(self):
        """Return underlying SQLAlchemy-Engine-Instance."""
        return self._engine

    async def close(self):
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")
        await self._engine.dispose()

        self._engine = None
        self._sessionmaker = None

    @contextlib.asynccontextmanager
    async def connect(self) -> AsyncIterator[AsyncConnection]:
        if self._engine is None:
            raise Exception("DatabaseSessionManager is not initialized")

        async with self._engine.begin() as connection:
            try:
                yield connection
            except Exception:
                await connection.rollback()
                raise

    @contextlib.asynccontextmanager
    async def session(self) -> AsyncIterator[AsyncSession]:
        if self._sessionmaker is None:
            raise Exception("DatabaseSessionManager is not initialized")

        session = self._sessionmaker()
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


#### fastAPI-DB (local)
sessionmanager_local = DatabaseSessionManager(
    SET_CONF.SQLALCHEMY_DATABASE_URI,
    {
        "echo": SET_CONF.DEBUG,
        "pool_size": 5,
        "max_overflow": 10,
        "pool_timeout": 30,
        "pool_pre_ping": True,
        "connect_args": {
            "check_same_thread": False,  # async SQLite-optimized
            "timeout": 20,  # SQLite-optimized
        },
    },
)

#### fastAPI-DB (external)
# sessionmanager_external = DatabaseSessionManager(
#     SET_CONF.EXT_DB,
#     {
#         "echo": SET_CONF.DEBUG,
#     },
# )


############## DB-SESSIONS for Dependency Injection.
async def get_db_session_local():
    async with sessionmanager_local.session() as session:
        yield session


# async def get_db_session_external():
#     async with sessionmanager_external.session() as session:
#         yield session


############## DB-DEPENDENCIES
DBSessionDep_local = Annotated[AsyncSession, Depends(get_db_session_local)]
# DBSessionDep_external = Annotated[AsyncSession, Depends(get_db_session_external)]
