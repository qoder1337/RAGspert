import json
import asyncio

from urllib.parse import urlparse

from src.utils.chunking import chunk_text, insert_chunk, ProcessedChunk
from src.utils.text_embedder import get_embeddings_batch
from src.load_app import get_berlin_time
from src.utils.llm.gemini_cl import gemini_response


async def process_and_store_document(url: str, markdown: str):
    """Process a document and store its chunks in parallel."""
    # Split into chunks
    chunks = chunk_text(markdown)

    # Process chunks in parallel
    tasks = [process_chunk(chunk, i, url) for i, chunk in enumerate(chunks)]
    processed_chunks = await asyncio.gather(*tasks)

    # Store chunks in parallel
    insert_tasks = [insert_chunk(chunk) for chunk in processed_chunks]
    await asyncio.gather(*insert_tasks)


async def get_title_and_summary(chunk: str, url: str) -> dict[str, str]:
    """Extract title and summary using the selected model."""

    system_prompt = """You are an AI that extracts titles and summaries from documentation chunks.
    Return a JSON object with 'title' and 'summary' keys.
    For the title: If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.
    For the summary: Create a concise summary of the main points in this chunk.
    Keep both title and summary concise but informative."""
    try:
        response_text = await gemini_response(
            system_prompt, prompt=f"URL: {url}\n\nContent:\n{chunk[:1000]}..."
        )

        return json.loads(response_text)

    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Raw response: {response_text}")
        return {
            "title": "Error parsing title",
            "summary": "Error parsing summary",
        }

    except Exception as e:
        print(f"Error getting title and summary: {e}")
        return {
            "title": "Error processing title",
            "summary": "Error processing summary",
        }


async def process_chunk(chunk: str, chunk_number: int, url: str) -> ProcessedChunk:
    """Process a single chunk of text."""
    crawl_time = get_berlin_time()

    # Get title and summary
    extracted = await get_title_and_summary(chunk, url)

    # Get embedding
    embedding = await get_embedding(chunk)

    # Create metadata
    meta_details = {
        "source": "pydantic_ai_docs",
        "chunk_size": len(chunk),
        "crawled_at": crawl_time.isoformat(),
        "url_path": urlparse(url).path,
    }

    return ProcessedChunk(
        url=url,
        chunk_number=chunk_number,
        title=extracted["title"],
        summary=extracted["summary"],
        content=chunk,  # Store the original chunk content
        meta_details=meta_details,
        embedding=embedding,
    )
