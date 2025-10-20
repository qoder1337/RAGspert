from sqlalchemy import select, distinct, cast, String
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models.agent_sitepage import SitePage


async def show_docs(db: AsyncSession) -> list[str]:
    """Get all available documentation sources."""
    source = cast(SitePage.meta_details["source"], String)

    result = await db.execute(
        select(distinct(source))
        .where(SitePage.meta_details["source"].isnot(None))
        .order_by(source)
    )

    return [row[0] for row in result.fetchall()]


async def url_exists(db: AsyncSession, url: str) -> bool:
    """Check if URL was already crawled."""
    result = await db.execute(select(1).where(SitePage.url == url).limit(1))
    return result.scalar() is not None
