import os
from google import genai
from google.genai import types

GEMINI_API = os.getenv("GEMINI_API")

gemini_async = genai.Client(api_key=GEMINI_API)


async def gemini_response(
    system_prompt: str, prompt: str, response_mime_type: str = "text/plain"
):
    response = await gemini_async.aio.models.generate_content(
        model="gemini-2.5-flash-lite",
        config=types.GenerateContentConfig(
            system_instruction=system_prompt, response_mime_type=response_mime_type
        ),
        contents=[prompt],
    )

    return response.text
