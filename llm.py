import os
import requests
from dotenv import load_dotenv

load_dotenv()

class OpenRouterLLM:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found in environment")

        self.url = "https://openrouter.ai/api/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:8501",
            "X-Title": "Policy Chatbot"
        }

    def generate(self, prompt: str) -> str:
        response = requests.post(
        self.url,
        headers=self.headers,
        json={
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "max_token":1000,
            "temperature": 0.2
        },
        timeout=60

    )

        response.raise_for_status()
        data = response.json()

        if "choices" not in data:
            error_msg = data.get("error", {}).get("message", "Unknown LLM error")
            return f"LLM Error: {error_msg}"

        return data["choices"][0]["message"]["content"].strip()

