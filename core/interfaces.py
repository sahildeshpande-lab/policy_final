from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from langchain_core.documents import Document

class LLMService(ABC):
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        pass

class VectorStoreService(ABC):
    @abstractmethod
    async def add_documents(self, documents: List[Document]) -> bool:
        pass
    
    @abstractmethod
    async def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        pass
    
    @abstractmethod
    async def load(self) -> bool:
        pass
    
    @abstractmethod
    async def save(self) -> bool:
        pass

class DocumentProcessorService(ABC):
    @abstractmethod
    async def process_pdf(self, file_path: str) -> List[Document]:
        pass
    
    @abstractmethod
    async def split_documents(self, documents: List[Document]) -> List[Document]:
        pass

class QueryService(ABC):
    @abstractmethod
    async def query(self, question: str, request_type: str = "Any Query") -> Dict[str, Any]:
        pass

class ConversationService(ABC):
    @abstractmethod
    async def create_conversation(self, user_id: str, thread_id: str, title: str) -> bool:
        pass
    
    @abstractmethod
    async def add_message(self, thread_id: str, user_message: str, ai_response: str) -> bool:
        pass
    
    @abstractmethod
    async def get_conversations(self, user_id: str) -> List[Dict]:
        pass
    
    @abstractmethod
    async def get_messages(self, thread_id: str) -> List[Dict]:
        pass
