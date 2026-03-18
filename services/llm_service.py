import os
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from core.interfaces import LLMService
from core.exceptions import LLMServiceException
import logging

load_dotenv()
logger = logging.getLogger(__name__)

class GeminiLLMService(LLMService):
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-2.5-flash-lite"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise LLMServiceException("GEMINI_API_KEY not found in environment")
        
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1alpha"
        self.timeout = 60
        self.max_tokens = 1000
        self.temperature = 0.2

    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate response from Gemini LLM"""
        try:
            url = f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}"
            
            payload = {
                "contents": [{
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "maxOutputTokens": kwargs.get("max_tokens", self.max_tokens),
                    "temperature": kwargs.get("temperature", self.temperature)
                }
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                async with session.post(url, headers=headers, json=payload) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Gemini API error {response.status}: {error_text}")
                        raise LLMServiceException(f"API Error {response.status}: {error_text}")
                    
                    data = await response.json()
                    
                    if "candidates" not in data or not data["candidates"]:
                        logger.error(f"Invalid response from Gemini: {data}")
                        raise LLMServiceException(f"LLM Error: {data}")
                    
                    return data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    
        except asyncio.TimeoutError:
            logger.error("Request to Gemini API timed out")
            raise LLMServiceException("Request timed out")
        except aiohttp.ClientError as e:
            logger.error(f"Network error calling Gemini API: {str(e)}")
            raise LLMServiceException(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error in LLM generation: {str(e)}")
            raise LLMServiceException(f"Unexpected error: {str(e)}")

class LLMServiceFactory:
    @staticmethod
    def create_llm_service(provider: str = "gemini", **kwargs) -> LLMService:
        """Factory method to create LLM service instances"""
        if provider.lower() == "gemini":
            return GeminiLLMService(**kwargs)
        else:
            raise LLMServiceException(f"Unsupported LLM provider: {provider}")
