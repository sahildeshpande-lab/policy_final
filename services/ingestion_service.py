import os
import asyncio
from typing import List, Dict, Any, Optional
from langchain_core.documents import Document
from core.interfaces import DocumentProcessorService, VectorStoreService
from core.exceptions import DocumentProcessingException, VectorStoreException
import logging

logger = logging.getLogger(__class__.__name__)

class IngestionService:
    def __init__(
        self, 
        document_processor: DocumentProcessorService,
        vector_store_service: VectorStoreService,
        pdf_dir: str = "pdfs"
    ):
        self.document_processor = document_processor
        self.vector_store_service = vector_store_service
        self.pdf_dir = pdf_dir

    async def ingest_single_pdf(self, file_path: str) -> Dict[str, Any]:
        """Ingest a single PDF file"""
        try:
            logger.info(f"Starting ingestion of {file_path}")
            
            # Process and split documents
            chunks = await self.document_processor.process_and_split(file_path)
            
            if not chunks:
                logger.warning(f"No chunks generated from {file_path}")
                return {"success": False, "message": "No content extracted", "chunks_count": 0}
            
            # Add to vector store
            success = await self.vector_store_service.add_documents(chunks)
            
            if success:
                logger.info(f"Successfully ingested {len(chunks)} chunks from {file_path}")
                return {
                    "success": True, 
                    "message": "PDF ingested successfully",
                    "chunks_count": len(chunks),
                    "file_path": file_path
                }
            else:
                logger.error(f"Failed to add documents to vector store for {file_path}")
                return {"success": False, "message": "Failed to store documents", "chunks_count": 0}
                
        except Exception as e:
            logger.error(f"Error ingesting PDF {file_path}: {str(e)}")
            raise DocumentProcessingException(f"Failed to ingest PDF: {str(e)}")

    async def ingest_all_pdfs(self) -> Dict[str, Any]:
        """Ingest all PDFs from the configured directory"""
        try:
            if not os.path.exists(self.pdf_dir):
                raise DocumentProcessingException(f"PDF directory not found: {self.pdf_dir}")
            
            pdf_files = [f for f in os.listdir(self.pdf_dir) if f.lower().endswith('.pdf')]
            
            if not pdf_files:
                logger.warning(f"No PDF files found in {self.pdf_dir}")
                return {"success": True, "message": "No PDF files found", "ingested_count": 0}
            
            total_chunks = 0
            successful_files = []
            failed_files = []
            
            for pdf_file in pdf_files:
                file_path = os.path.join(self.pdf_dir, pdf_file)
                try:
                    result = await self.ingest_single_pdf(file_path)
                    if result["success"]:
                        successful_files.append(pdf_file)
                        total_chunks += result["chunks_count"]
                    else:
                        failed_files.append(pdf_file)
                except Exception as e:
                    logger.error(f"Failed to ingest {pdf_file}: {str(e)}")
                    failed_files.append(pdf_file)
            
            logger.info(f"Batch ingestion completed: {len(successful_files)} successful, {len(failed_files)} failed")
            
            return {
                "success": len(failed_files) == 0,
                "message": f"Ingested {len(successful_files)} files with {total_chunks} total chunks",
                "successful_files": successful_files,
                "failed_files": failed_files,
                "total_chunks": total_chunks,
                "ingested_count": len(successful_files)
            }
            
        except Exception as e:
            logger.error(f"Error in batch ingestion: {str(e)}")
            raise DocumentProcessingException(f"Failed to batch ingest PDFs: {str(e)}")

    async def reindex_all(self) -> Dict[str, Any]:
        """Reindex all PDFs (clear and rebuild)"""
        try:
            # This would require implementing a clear method in vector store
            # For now, just ingest all
            logger.info("Starting reindex of all PDFs")
            result = await self.ingest_all_pdfs()
            result["message"] = "Reindex completed: " + result["message"]
            return result
        except Exception as e:
            logger.error(f"Error during reindex: {str(e)}")
            raise DocumentProcessingException(f"Failed to reindex: {str(e)}")

    async def get_ingestion_status(self) -> Dict[str, Any]:
        """Get status of ingestion process"""
        try:
            # Check if vector store exists
            vector_store_loaded = await self.vector_store_service.load()
            
            # Count PDF files
            pdf_count = 0
            if os.path.exists(self.pdf_dir):
                pdf_count = len([f for f in os.listdir(self.pdf_dir) if f.lower().endswith('.pdf')])
            
            return {
                "vector_store_loaded": vector_store_loaded,
                "pdf_directory": self.pdf_dir,
                "pdf_file_count": pdf_count,
                "directory_exists": os.path.exists(self.pdf_dir)
            }
            
        except Exception as e:
            logger.error(f"Error getting ingestion status: {str(e)}")
            return {"error": str(e)}

class IngestionServiceFactory:
    @staticmethod
    def create_ingestion_service(
        document_processor: DocumentProcessorService = None,
        vector_store_service: VectorStoreService = None,
        pdf_dir: str = "pdfs"
    ) -> IngestionService:
        """Factory method to create ingestion service"""
        if not document_processor or not vector_store_service:
            raise DocumentProcessingException("Document processor and vector store service are required")
        
        return IngestionService(document_processor, vector_store_service, pdf_dir)
