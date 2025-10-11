import asyncio
from google import genai
from functools import lru_cache
from src.config import SET_CONF


@lru_cache
def get_gemini_client() -> genai.Client:
    """Singleton für Gemini Client."""
    return genai.Client(api_key=SET_CONF.GEMINI_API_KEY)


async def get_embeddings_batch(
    texts: list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    dimensions: int = 768,
    batch_size: int = 100,
) -> list[list[float]]:
    """Get embeddings for multiple texts in batches.

    Args:
        texts: List of texts to embed (max 2048 per batch)
        task_type: "RETRIEVAL_DOCUMENT" or "QUESTION_ANSWERING"
        dimensions: Output dimensionality (768, 1536, 3072)
        batch_size: Texts per API request (max 2048)

    Returns:
        List of embedding vectors
    """

    client = get_gemini_client()

    all_embeddings = []

    # In Batches aufteilen
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]

        try:
            result = await asyncio.to_thread(
                client.models.embed_content,
                model="models/gemini-embedding-001",
                contents=batch,
                config={"task_type": task_type, "output_dimensionality": dimensions},
            )

            batch_embeddings = [emb.values for emb in result.embeddings]
            all_embeddings.extend(batch_embeddings)

        except Exception as e:
            print(f"Error in batch {i}-{i + batch_size}: {e}")
            all_embeddings.extend([[0.0] * dimensions] * len(batch))

    return all_embeddings
