import os
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

OPENROUTER_MODEL=os.getenv("OPENROUTER_MODEL")

VECTOR_DB_PATH = "vector_db"
