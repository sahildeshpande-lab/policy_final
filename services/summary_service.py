import asyncio
from typing import Dict, Any, Optional
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from core.interfaces import LLMService
from services.llm_service import LLMServiceFactory
from services.service_container import service_container
from services.logging_service import logging_service

logger = logging_service.get_logger(__name__)

class SummaryService:
    """Service for generating conversation summaries using LangGraph"""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        self.llm_service = llm_service
        self._summary_chain = None
    
    async def _get_summary_chain(self):
        """Get or create the summary chain"""
        if self._summary_chain is None:
            if not self.llm_service:
                self.llm_service = service_container.get(service_container.LLMService)
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_template("""
            You are a conversation summarization expert. Based on the AI response below, 
            create a concise and descriptive title for this conversation (max 50 characters).
            
            AI Response: {ai_response}
            
            Summary:
            """)
            
            # Create chain
            self._summary_chain = (
                {"ai_response": RunnablePassthrough()}
                | prompt
                | self.llm_service
                | StrOutputParser()
            )
        
        return self._summary_chain
    
    async def generate_summary(self, ai_response: str) -> str:
        """Generate conversation summary from AI response"""
        try:
            chain = await self._get_summary_chain()
            summary = await chain.invoke(ai_response)
            
            # Truncate if too long
            if len(summary) > 50:
                summary = summary[:47] + "..."
            
            logger.info(f"Generated summary: {summary}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating summary: {str(e)}")
            # Fallback to first few words of the response
            fallback = ai_response.split('.')[0][:47] + "..." if len(ai_response.split('.')[0]) > 50 else ai_response.split('.')[0]
            return fallback or "New Conversation"

class LangGraphSummaryService(SummaryService):
    """LangGraph-based summary service with workflow capabilities"""
    
    def __init__(self, llm_service: Optional[LLMService] = None):
        super().__init__(llm_service)
        self._graph = None
    
    async def _build_graph(self):
        """Build LangGraph workflow for summarization"""
        if self._graph is not None:
            return self._graph
        
        # This is where you would build more complex LangGraph workflows
        # For now, we'll use the simple chain approach
        chain = await self._get_summary_chain()
        
        # Create a simple graph-like structure
        self._graph = {
            'invoke': chain.invoke
        }
        
        return self._graph
    
    async def generate_summary_with_graph(self, ai_response: str) -> str:
        """Generate summary using LangGraph workflow"""
        try:
            graph = await self._build_graph()
            result = graph['invoke'](ai_response)
            
            # Truncate if too long
            if len(result) > 50:
                result = result[:47] + "..."
            
            logger.info(f"Generated graph summary: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error generating graph summary: {str(e)}")
            # Fallback to basic summary
            return await self.generate_summary(ai_response)

class SummaryServiceFactory:
    """Factory for creating summary service instances"""
    
    @staticmethod
    def create_summary_service(
        service_type: str = "basic",
        llm_service: Optional[LLMService] = None
    ) -> SummaryService:
        """Create summary service instance"""
        if service_type.lower() == "langgraph":
            return LangGraphSummaryService(llm_service)
        else:
            return SummaryService(llm_service)

# Global summary service for backward compatibility
_summary_service = None

async def build_summary_graph():
    """Build summary graph for backward compatibility"""
    global _summary_service
    if _summary_service is None:
        _summary_service = SummaryServiceFactory.create_summary_service("langgraph")
    return await _summary_service._build_graph()
