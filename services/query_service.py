import asyncio
from typing import Dict, List, Any, Optional
from langchain_core.documents import Document
from core.interfaces import QueryService, LLMService, VectorStoreService
from core.exceptions import QueryServiceException
import logging

logger = logging.getLogger(__class__.__name__)

class RAGQueryService(QueryService):
    def __init__(self, llm_service: LLMService, vector_store_service: VectorStoreService):
        self.llm_service = llm_service
        self.vector_store_service = vector_store_service

    def _format_docs(self, docs: List[Document]) -> tuple[str, List[str]]:
        """Format documents for prompt"""
        formatted = []
        sources = set()

        for doc in docs:
            source = doc.metadata.get("source", "unknown")
            page = doc.metadata.get("page", "N/A")
            sources.add(source)
            formatted.append(f"[Source: {source}, Page: {page}]\n{doc.page_content}")

        return "\n\n".join(formatted), list(sources)

    def _build_prompt(self, question: str, request_type: str, context: str) -> str:
        """Build prompt for LLM"""
        return f"""
You are a company policy assistant.
The user is asking for help regarding: {request_type}

Behavior rules:

1. If the user message is a greeting (hi, hello, hey, good morning, good evening, etc.):
   - Respond with a greeting.
   - Ask the user what policy question or use case they need help with.

2. If the user asks about your use case, role, or what you can do:
   - Explain that you are an assistant designed to help employees find information from company policy documents.
   - Mention that you can answer questions related to policies such as leave policy, HR rules, workplace guidelines, etc.
   - Inform them that if the information is not available, they should connect to HR.

3. If the user asks a policy question:
   - Answer using ONLY the policy context below.

4. If the answer is not present in the context:
   - Reply exactly with: "Connect to HR for more detail."

POLICY CONTEXT:
{context}

USER QUESTION:
{question}
"""

    async def query(self, question: str, request_type: str = "Any Query") -> Dict[str, Any]:
        """Perform RAG query"""
        try:
            # Retrieve relevant documents
            docs = await self.vector_store_service.similarity_search(question, k=5)
            
            if not docs:
                logger.warning(f"No documents found for query: {question[:50]}...")
                return {
                    "answer": "Connect to HR for more detail.",
                    "sources": [],
                    "context": None
                }

            # Format documents
            context, sources = self._format_docs(docs)
            
            # Build prompt
            prompt = self._build_prompt(question, request_type, context)
            
            # Generate response
            answer = await self.llm_service.generate(prompt)
            
            logger.info(f"Query processed successfully: {question[:50]}...")
            return {
                "answer": answer,
                "sources": sources,
                "context": context,
                "num_docs_retrieved": len(docs)
            }
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}")
            raise QueryServiceException(f"Failed to process query: {str(e)}")

class LangGraphQueryService(QueryService):
    def __init__(self, llm_service: LLMService, vector_store_service: VectorStoreService):
        self.llm_service = llm_service
        self.vector_store_service = vector_store_service
        self._rag_service = RAGQueryService(llm_service, vector_store_service)

    async def query(self, question: str, request_type: str = "Any Query") -> Dict[str, Any]:
        """Perform query with LangGraph workflow"""
        try:
            # For now, delegate to RAG service
            # Can be extended with LangGraph workflows for complex queries
            result = await self._rag_service.query(question, request_type)
            
            # Add LangGraph-specific processing if needed
            # This is where you would integrate LangGraph workflows
            
            return result
            
        except Exception as e:
            logger.error(f"Error in LangGraph query service: {str(e)}")
            raise QueryServiceException(f"Failed to process query: {str(e)}")

class QueryServiceFactory:
    @staticmethod
    def create_query_service(
        service_type: str = "rag", 
        llm_service: LLMService = None,
        vector_store_service: VectorStoreService = None
    ) -> QueryService:
        """Factory method to create query service instances"""
        if not llm_service or not vector_store_service:
            raise QueryServiceException("LLM service and vector store service are required")
        
        if service_type.lower() == "rag":
            return RAGQueryService(llm_service, vector_store_service)
        elif service_type.lower() == "langgraph":
            return LangGraphQueryService(llm_service, vector_store_service)
        else:
            raise QueryServiceException(f"Unsupported query service type: {service_type}")
