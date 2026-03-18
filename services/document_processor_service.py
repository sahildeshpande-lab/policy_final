import os
import asyncio
from typing import List, Dict, Any
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from core.interfaces import DocumentProcessorService
from core.exceptions import DocumentProcessingException
import logging

logger = logging.getLogger(__class__.__name__)

class PDFDocumentProcessorService(DocumentProcessorService):
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )

    async def process_pdf(self, file_path: str) -> List[Document]:
        """Process PDF file and return documents"""
        try:
            if not os.path.exists(file_path):
                raise DocumentProcessingException(f"File not found: {file_path}")
            
            if not file_path.lower().endswith('.pdf'):
                raise DocumentProcessingException(f"Invalid file format: {file_path}")
            
            loader = PyPDFLoader(file_path)
            documents = await asyncio.get_event_loop().run_in_executor(
                None, 
                loader.load
            )
            
            if not documents:
                logger.warning(f"No documents extracted from {file_path}")
                return []
            
            # Add metadata to documents
            filename = os.path.basename(file_path)
            for doc in documents:
                if not doc.metadata:
                    doc.metadata = {}
                doc.metadata['source'] = filename
                doc.metadata['file_path'] = file_path
            
            logger.info(f"Processed {len(documents)} documents from {file_path}")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing PDF {file_path}: {str(e)}")
            raise DocumentProcessingException(f"Failed to process PDF: {str(e)}")

    async def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks"""
        try:
            if not documents:
                return []
            
            chunks = await asyncio.get_event_loop().run_in_executor(
                None, 
                self._text_splitter.split_documents,
                documents
            )
            
            # Ensure chunks have proper metadata
            for i, chunk in enumerate(chunks):
                if not chunk.metadata:
                    chunk.metadata = {}
                if 'chunk_id' not in chunk.metadata:
                    chunk.metadata['chunk_id'] = i
            
            logger.info(f"Split {len(documents)} documents into {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"Error splitting documents: {str(e)}")
            raise DocumentProcessingException(f"Failed to split documents: {str(e)}")

    async def process_and_split(self, file_path: str) -> List[Document]:
        """Process PDF and split into chunks in one operation"""
        documents = await self.process_pdf(file_path)
        return await self.split_documents(documents)

class DocumentProcessorFactory:
    @staticmethod
    def create_processor(processor_type: str = "pdf", **kwargs) -> DocumentProcessorService:
        """Factory method to create document processor instances"""
        if processor_type.lower() == "pdf":
            return PDFDocumentProcessorService(**kwargs)
        else:
            raise DocumentProcessingException(f"Unsupported processor type: {processor_type}")
