import json
import asyncio

from urllib.parse import urlparse

from src.utils.chunking import chunk_text, insert_chunk, ProcessedChunk
from src.utils.text_embedder import get_embeddings_batch
from src.load_app import get_berlin_time
from src.utils.llm.gemini_cl import gemini_response
from src.utils.ratelimiter import rate_limiter_gemini


async def process_and_store_document(url: str, markdown: str, source_name: str = None):
    """
    Process document with batch embeddings.

    Steps:
    1. Split into chunks
    2. Get titles/summaries in parallel
    3. Get embeddings in ONE batch
    4. Store all chunks in parallel
    """
    # 1. Split into chunks
    chunks = chunk_text(markdown)
    print(f"📄 Processing {len(chunks)} chunks from {url}")

    if not chunks:
        print("⚠️ No chunks to process")
        return

    # 2. Get titles & summaries in parallel
    title_summary_tasks = [get_title_and_summary(chunk, url) for chunk in chunks]
    titles_summaries = await asyncio.gather(*title_summary_tasks)

    # 3. Get embeddings in ONE batch (efficient!)
    print(f"🔄 Getting embeddings for {len(chunks)} chunks...")
    embeddings = await get_embeddings_batch(
        texts=chunks,
        task_type="RETRIEVAL_DOCUMENT",
        dimensions=768,
        batch_size=100,  # ✅ Max 100 per API call
    )

    # 4. Create ProcessedChunks
    crawl_time = get_berlin_time()
    processed_chunks = []

    for i, (chunk, title_summary, embedding) in enumerate(
        zip(chunks, titles_summaries, embeddings)
    ):
        meta_details = {
            "source": source_name or "unknown",
            "chunk_size": len(chunk),
            "crawled_at": crawl_time.isoformat(),
            "url_path": urlparse(url).path,
        }

        processed_chunks.append(
            ProcessedChunk(
                url=url,
                chunk_number=i,
                title=title_summary["title"],
                summary=title_summary["summary"],
                content=chunk,
                meta_details=meta_details,
                embedding=embedding,
            )
        )

    # 5. Store all chunks in parallel
    print(f"💾 Storing {len(processed_chunks)} chunks...")
    insert_tasks = [insert_chunk(chunk) for chunk in processed_chunks]
    await asyncio.gather(*insert_tasks)

    print(f"✅ Stored {len(processed_chunks)} chunks for {url}")


@rate_limiter_gemini
async def get_title_and_summary(chunk: str, url: str) -> dict[str, str]:
    """Extract with enforced JSON schema."""

    system_prompt = """Extract title and summary from documentation."""

    json_schema = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short descriptive title"},
            "summary": {"type": "string", "description": "Brief summary of content"},
        },
        "required": ["title", "summary"],
    }

    try:
        response_text = await gemini_response(
            system_prompt=system_prompt,
            prompt=f"URL: {url}\n\nContent:\n{chunk[:800]}",
            response_mime_type="application/json",  # ✅ JSON Mode
            response_schema=json_schema,  # ✅ enforce Schema
            temperature=0.3,  # ✅ Deterministic Response
            max_output_tokens=500,  # ✅ Short answer
        )

        parsed = json.loads(response_text)
        print(parsed)
        return parsed

    except Exception as e:
        print(f"❌ Error: {e}")
        # Fallback
        path_part = urlparse(url).path.strip("/").split("/")[-1] or "Doc"
        return {
            "title": f"{path_part}",
            "summary": chunk[:200].replace("\n", " ") + "...",
        }
