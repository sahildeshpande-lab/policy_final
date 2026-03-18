import os
import requests
from dotenv import load_dotenv 

load_dotenv()

class GeminiLLM :
    def __init__(self):
        self.api_key=os.getenv("GEMINI_API_KEY")

        if not self.api_key :
            raise ValueError(" GEMINI_API_KEY not found")
        
        self.model = "gemini-2.5-flash-lite"
        
        self.url = f"https://generativelanguage.googleapis.com/v1alpha/models/{self.model}:generateContent?key={self.api_key}"

        self.headers ={
            "Content-Type": "application/json"
        }

    def generate(self,prompt:str) -> str :
        response= requests.post(
            self.url,
            headers=self.headers,
            json={
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": 1000,
                    "temperature": 0.2
                }
            },
            timeout=60
        )

        if response.status_code != 200 :
            return f"API Error {response.status_code} : {response.text}"
        
        data = response.json()

        if "candidates" not in data or not data["candidates"] :
            return f"LLM Error : {data}"
        
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()

