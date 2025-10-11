import re
from typing import Any
from dataclasses import dataclass
from src.database import sessionmanager_pgvector
from src.database.models.agent_sitepage import (
    SitePage,
)
from sqlalchemy.exc import SQLAlchemyError


@dataclass
class ProcessedChunk:
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    meta_details: dict[str, Any]
    embedding: list[float]


# ### NEU MIT CODEBLOCK RESPECT
@dataclass
class TextSegment:
    content: str
    is_code: bool
    original_text: str = None


def chunk_text(
    text: str, max_chunk_size: int = 5000, min_chunk_size: int = 4000
) -> list[str]:
    """
    Split markdown text into chunks while preserving code blocks.

    Args:
        text: Input markdown text
        max_chunk_size: Maximum size of each chunk
        min_chunk_size: Minimum size of each chunk

    Returns:
        List of text chunks with preserved code blocks
    """

    def split_into_segments(text: str) -> list[TextSegment]:
        """Split text into alternating regular text and code block segments."""
        segments = []
        current_pos = 0

        # Find all code blocks (both fenced and indented)
        code_block_pattern = (
            r"(```[\s\S]*?```)|(?:(?:^|\n)(?:    |\t)[^\n]+(?:\n(?:    |\t)[^\n]+)*)"
        )
        for match in re.finditer(code_block_pattern, text, re.MULTILINE):
            start, end = match.span()

            # Add text before code block if exists
            if start > current_pos:
                segments.append(
                    TextSegment(content=text[current_pos:start], is_code=False)
                )

            # Add code block
            segments.append(
                TextSegment(
                    content=match.group(0), is_code=True, original_text=match.group(0)
                )
            )
            current_pos = end

        # Add remaining text if exists
        if current_pos < len(text):
            segments.append(TextSegment(content=text[current_pos:], is_code=False))

        return segments

    def find_break_point(text: str, start: int, end: int) -> int:
        """Find suitable break point in text between start and end."""
        # Prioritized break points
        break_patterns = [
            r"\n\n",  # Double newline
            r"^#\s|^\#{2}\s",  # Headers
            r"[\.\?\!]\s",  # Sentence endings
            r"(?<!\!)\[.*?\]\(.*?\)",  # Markdown links
            r"\n",  # Single newline
            r"\s",  # Space
        ]

        search_text = text[start:end]

        for pattern in break_patterns:
            matches = list(re.finditer(pattern, search_text))
            if matches:
                return start + matches[-1].end()

        return end

    def merge_small_chunks(chunks: list[str], min_chunk_size: int) -> list[str]:
        """Merge small chunks with previous chunks if possible."""
        merged_chunks = []

        for chunk in chunks:
            if merged_chunks and len(chunk) < min_chunk_size:
                if len(merged_chunks[-1]) + len(chunk) <= max_chunk_size:
                    merged_chunks[-1] += "\n" + chunk
                else:
                    merged_chunks.append(chunk)
            else:
                merged_chunks.append(chunk)

        return merged_chunks

    ###### NEW

    # Split text into regular text and code block segments
    segments = split_into_segments(text)

    chunks = []
    current_chunk = []
    current_size = 0

    for segment in segments:
        if segment.is_code:
            if current_size + len(segment.content) > max_chunk_size and current_chunk:
                chunks.append("".join(current_chunk))
                current_chunk = []
                current_size = 0

            if len(segment.content) > max_chunk_size:
                if current_chunk:
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                chunks.append(segment.content)
                continue

            current_chunk.append(segment.content)
            current_size += len(segment.content)

        else:
            text_to_process = segment.content
            start = 0

            while start < len(text_to_process):
                remaining_space = max_chunk_size - current_size

                if remaining_space < min_chunk_size and current_chunk:
                    # Finish current chunk
                    chunks.append("".join(current_chunk))
                    current_chunk = []
                    current_size = 0
                    remaining_space = max_chunk_size

                end = min(start + remaining_space, len(text_to_process))

                if end - start < min_chunk_size:
                    # Add remaining text to current chunk
                    current_chunk.append(text_to_process[start:])
                    current_size += len(text_to_process[start:])
                    break

                # Find break point
                break_point = find_break_point(text_to_process, start, end)

                current_chunk.append(text_to_process[start:break_point])
                current_size += break_point - start
                start = break_point

    # Add final chunk if exists
    if current_chunk:
        chunks.append("".join(current_chunk))

    # return [chunk.strip() for chunk in chunks if chunk.strip()]

    ##### TEST
    chunks = [chunk.strip() for chunk in chunks if chunk.strip()]
    chunks = merge_small_chunks(chunks, min_chunk_size=4000)
    return chunks


#############################
async def insert_chunk(chunk: ProcessedChunk):
    """Insert a processed chunk into the pgvector database using SQLAlchemy."""
    async with sessionmanager_pgvector.session() as db_session:
        try:
            # New SitePage-Objekt
            new_chunk = SitePage(
                url=chunk.url,
                chunk_number=chunk.chunk_number,
                title=chunk.title,
                summary=chunk.summary,
                content=chunk.content,
                meta_details=chunk.meta_details,
                embedding=chunk.embedding,
            )

            db_session.add(new_chunk)
            await db_session.commit()
            print(f"Inserted chunk {chunk.chunk_number} for {chunk.url}")
            return True
        except SQLAlchemyError as e:
            print(f"Error inserting chunk: {e}")
            await db_session.rollback()
            return False
