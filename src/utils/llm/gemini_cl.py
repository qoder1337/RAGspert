from google import genai
from src.config import SET_CONF
from google.genai import types
from functools import lru_cache
from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

api_key = SET_CONF.GEMINI_API_KEY


@lru_cache
def get_gemini_client() -> genai.Client:
    """Singleton für Gemini Client."""
    return genai.Client(api_key=api_key)


gemini_client = get_gemini_client()
gemini_provider = GoogleProvider(api_key=api_key)
model_name = "gemini-2.0-flash-lite"
model_name_ask = "gemini-2.5-flash"
gemini_model = GoogleModel(model_name=model_name, provider=gemini_provider)
gemini_model_ask = GoogleModel(model_name=model_name_ask, provider=gemini_provider)


async def gemini_response(
    system_prompt: str,
    prompt: str,
    response_mime_type: str = "text/plain",
    response_schema: dict = None,
    temperature: float = 1.0,
    max_output_tokens: int = 2048,
    model: str = model_name,
):
    """Enhanced Gemini response with configurable parameters."""

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type=response_mime_type,
        temperature=temperature,
        max_output_tokens=max_output_tokens,
    )

    if response_schema:
        config.response_schema = response_schema

    response = await gemini_client.aio.models.generate_content(
        model=model,
        config=config,
        contents=[prompt],
    )

    return response.text
