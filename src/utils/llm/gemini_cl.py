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
model_name = "gemini-2.5-flash-lite"
gemini_model = GoogleModel(model_name=model_name, provider=gemini_provider)


async def gemini_response(
    system_prompt: str, prompt: str, response_mime_type: str = "text/plain"
):
    response = await gemini_client.aio.models.generate_content(
        model=model_name,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt, response_mime_type=response_mime_type
        ),
        contents=[prompt],
    )

    return response.text
