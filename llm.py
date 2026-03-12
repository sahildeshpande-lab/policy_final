import os
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

class OpenRouterLLM:
    def __init__(self):
        self.api_key = os.getenv("OPENROUTER_API_KEY")

        if not self.api_key:
            self.api_key = st.secrets["OPENROUTER_API_KEY"]

        self.model = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not found")

        self.url = "https://openrouter.ai/api/v1/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://ai-in-hr-domain.streamlit.app",
            "X-Title": "Policy Chatbot"
    }
    def generate(self, prompt: str) -> str:
        response = requests.post(
            self.url,
            headers=self.headers,
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.2
            },
            timeout=60
        )

        if response.status_code != 200:
            return f"API Error {response.status_code}: {response.text}"

        data = response.json()

        if "choices" not in data:
            return f"LLM Error: {data}"
 
        return data["choices"][0]["message"]["content"].strip()