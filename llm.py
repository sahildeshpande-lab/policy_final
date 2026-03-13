import os
import requests
import streamlit as st
from dotenv import load_dotenv 

load_dotenv()

class GroqLLM :
    def __init__(self):
        self.api_key=os.getenv("GROQ_API_KEY")

        if not self.api_key :
            self.api_key = st.secrets["GROQ_API_KEY"]
        if not self.api_key :
            raise ValueError(" GROQ_API_KEY not found")
        
        self.model = "llama-3.3-70b-versatile"

        self.url = "https://api.groq.com/openai/v1/chat/completions"

        self.headers ={
            "Authorization":f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def generate(self,prompt:str) -> str :
        response= requests.post(
            self.url,
            headers=self.headers,
            json={
                "model":self.model ,
                "messages":[
                    {"role":"user","content":prompt}
                ],
                "max_tokens":1000,
                "temperature":0.2
            },
            timeout=60
        )

        if response.status_code != 200 :
            return f"API Error {response.status_code} : {response.text}"
        
        data = response.json()

        if "choices" not in data :
            return f"LLM Error : {data}"
        
        return data["choices"][0]["message"]["content"].strip()

