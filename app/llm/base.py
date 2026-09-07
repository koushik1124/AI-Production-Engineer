from abc import ABC, abstractmethod


class LLM(ABC):

    @abstractmethod
    async def generate(self, prompt: str) -> str:
        """
        Generate a response from the language model.
        """
        pass