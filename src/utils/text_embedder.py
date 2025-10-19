import asyncio
from src.utils.llm.gemini_cl import gemini_client
from src.utils.ratelimiter import rate_limiter_gemini_embeddings


async def get_embeddings_batch(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    dimensions: int = 768,
    batch_size: int = 100,
) -> list[list[float]]:
    """Get embeddings in batches with automatic rate limiting."""
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        try:
            embedding_batch = await _get_batch_internal(batch, task_type, dimensions)
            all_embeddings.extend(embedding_batch)

            print(
                f"✅ Batch {i // batch_size + 1}/{(len(texts) - 1) // batch_size + 1}"
            )

        except Exception as e:
            print(f"❌ Error: {e}")
            all_embeddings.extend([[0.0] * dimensions] * len(batch))

    return all_embeddings


@rate_limiter_gemini_embeddings
async def _get_batch_internal(batch, task_type, dimensions):
    """Rate-limited API call."""
    result = await asyncio.to_thread(
        gemini_client.models.embed_content,
        model="gemini-embedding-001",
        contents=batch,
        config={"task_type": task_type, "output_dimensionality": dimensions},
    )
    return [emb.values for emb in result.embeddings]


@rate_limiter_gemini_embeddings
async def get_embedding_single(
    text: str,
    task_type: str = "QUESTION_ANSWERING",
    dimensions: int = 768,
) -> list[float]:
    """Get single embedding (for user queries)."""
    try:
        result = await asyncio.to_thread(
            gemini_client.models.embed_content,
            model="gemini-embedding-001",
            contents=text,
            config={"task_type": task_type, "output_dimensionality": dimensions},
        )
        return result.embeddings[0].values

    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0.0] * dimensions
