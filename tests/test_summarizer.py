import unittest
from unittest.mock import patch

from src.llm.summarizer import LLMSummarizer


class LLMSummarizerTests(unittest.TestCase):
    @patch("src.llm.summarizer.AsyncOpenAI")
    def test_uses_explicit_api_key_for_a_dedicated_channel(self, openai_client):
        LLMSummarizer(api_key="dedicated-ai-key")

        openai_client.assert_called_once_with(
            api_key="dedicated-ai-key",
            base_url="https://api.deepseek.com",
        )


if __name__ == "__main__":
    unittest.main()
