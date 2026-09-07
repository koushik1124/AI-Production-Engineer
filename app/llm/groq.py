from groq import AsyncGroq

from app.core.config import settings
from app.llm.base import LLM


class GroqLLM(LLM):
    def __init__(self):
        self.client = AsyncGroq(api_key=settings.groq_api_key)

    async def generate(self, prompt: str) -> str:
        response = await self.client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            max_tokens=800,
        )

        return response.choices[0].message.content