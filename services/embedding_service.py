import asyncio
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from core.interfaces import LLMService
from core.exceptions import PolicyAssistantException
from services.logging_service import logging_service
from services.config_service import config_service

logger = logging_service.get_logger(__name__)

class EmbeddingService:
    """Production-ready embedding service with async support"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or config_service.get('vector_store.embedding_model', 'all-MiniLM-L6-v2')
        self._model = None
        self._lock = asyncio.Lock()
    
    async def _get_model(self):
        """Lazy loading of the model with thread safety"""
        if self._model is None:
            async with self._lock:
                if self._model is None:
                    self._model = await asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: SentenceTransformer(self.model_name)
                    )
                    logger.info(f"Loaded embedding model: {self.model_name}")
        return self._model
    
    async def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple documents asynchronously"""
        try:
            model = await self._get_model()
            embeddings = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.encode(texts)
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Error embedding documents: {str(e)}")
            raise PolicyAssistantException(f"Failed to embed documents: {str(e)}")
    
    async def embed_query(self, text: str) -> List[float]:
        """Embed a single query asynchronously"""
        try:
            model = await self._get_model()
            embedding = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: model.encode(text)
            )
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Error embedding query: {str(e)}")
            raise PolicyAssistantException(f"Failed to embed query: {str(e)}")
    
    def get_embeddings(self):
        """Get embedding service instance (for compatibility with LangChain)"""
        return self

class EmbeddingServiceFactory:
    """Factory for creating embedding service instances"""
    
    @staticmethod
    def create_embedding_service(model_name: Optional[str] = None) -> EmbeddingService:
        """Create embedding service instance"""
        return EmbeddingService(model_name)

# Global embedding service instance for backward compatibility
_embedding_service = None

def get_embeddings():
    """Get embeddings service instance (for backward compatibility)"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
