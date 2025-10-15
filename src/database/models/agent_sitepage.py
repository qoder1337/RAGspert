from sqlalchemy import Column, Integer, String, Text, JSON, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base
from pgvector.sqlalchemy import Vector

Base = declarative_base()


class SitePage(Base):
    __tablename__ = "site_pages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    url = Column(String, nullable=False)
    chunk_number = Column(Integer, nullable=False)
    title = Column(String, nullable=False)
    summary = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    meta_details = Column(JSON, nullable=False, default={})
    embedding = Column(Vector(768))
    created_at = Column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
