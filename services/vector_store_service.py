import os
import asyncio
from typing import List, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from core.interfaces import VectorStoreService
from core.exceptions import VectorStoreException
from services.embedding_service import get_embeddings
from services.config_service import config_service
import logging

logger = logging.getLogger(__class__.__name__)

class FAISSVectorStoreService(VectorStoreService):
    def __init__(self, vector_db_path: str = None):
        self.vector_db_path = vector_db_path or config_service.get('vector_store.path')
        self.embeddings = get_embeddings()
        self._vector_db = None
        self._lock = asyncio.Lock()

    async def _load_vector_db(self):
        """Load vector database with thread safety"""
        if self._vector_db is None:
            async with self._lock:
                if self._vector_db is None:
                    try:
                        if os.path.exists(self.vector_db_path):
                            self._vector_db = await asyncio.get_event_loop().run_in_executor(
                                None, 
                                lambda: FAISS.load_local(
                                    self.vector_db_path,
                                    self.embeddings,
                                    allow_dangerous_deserialization=True
                                )
                            )
                            logger.info(f"Vector database loaded from {self.vector_db_path}")
                        else:
                            logger.warning(f"Vector database not found at {self.vector_db_path}")
                    except Exception as e:
                        logger.error(f"Error loading vector database: {str(e)}")
                        raise VectorStoreException(f"Failed to load vector database: {str(e)}")
        return self._vector_db

    async def add_documents(self, documents: List[Document]) -> bool:
        """Add documents to vector store"""
        try:
            vector_db = await self._load_vector_db()
            
            if vector_db is None:
                vector_db = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: FAISS.from_documents(documents, self.embeddings)
                )
            else:
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: vector_db.add_documents(documents)
                )
            
            self._vector_db = vector_db
            await self.save()
            logger.info(f"Added {len(documents)} documents to vector store")
            return True
            
        except Exception as e:
            logger.error(f"Error adding documents to vector store: {str(e)}")
            raise VectorStoreException(f"Failed to add documents: {str(e)}")

    async def similarity_search(self, query: str, k: int = 5) -> List[Document]:
        """Perform similarity search"""
        try:
            vector_db = await self._load_vector_db()
            
            if vector_db is None:
                logger.warning("Vector database not initialized")
                return []
            
            retriever = vector_db.as_retriever(search_kwargs={"k": k})
            docs = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: retriever.invoke(query)
            )
            
            logger.info(f"Retrieved {len(docs)} documents for query: {query[:50]}...")
            return docs
            
        except Exception as e:
            logger.error(f"Error performing similarity search: {str(e)}")
            raise VectorStoreException(f"Failed to perform search: {str(e)}")

    async def load(self) -> bool:
        """Load vector database"""
        try:
            await self._load_vector_db()
            return True
        except Exception as e:
            logger.error(f"Error loading vector database: {str(e)}")
            return False

    async def save(self) -> bool:
        """Save vector database"""
        try:
            if self._vector_db is not None:
                await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda: self._vector_db.save_local(self.vector_db_path)
                )
                logger.info(f"Vector database saved to {self.vector_db_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error saving vector database: {str(e)}")
            raise VectorStoreException(f"Failed to save vector database: {str(e)}")

    async def get_retriever(self, k: int = 5):
        """Get retriever instance"""
        vector_db = await self._load_vector_db()
        if vector_db is None:
            raise VectorStoreException("Vector database not initialized")
        return vector_db.as_retriever(search_kwargs={"k": k})
