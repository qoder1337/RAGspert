from functools import lru_cache
from sqlalchemy.orm import DeclarativeMeta

@lru_cache
def globals_mapping_loader() -> dict[str, DeclarativeMeta]:
    """
    Return a Dict {ModelName: ModelClass} of all SQL-Alchemy-Models.
    lazy loaded import prevents circular Import Error
    """
    # Local Import (lazy)
    from src.database import Base

    return {m.class_.__name__: m.class_ for m in Base.registry.mappers}
