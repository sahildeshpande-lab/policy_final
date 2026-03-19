from typing import Dict, Any, Optional, TypeVar, Type
from core.interfaces import LLMService, VectorStoreService, DocumentProcessorService, QueryService
from services.llm_service import LLMServiceFactory
from services.vector_store_service import FAISSVectorStoreService
from services.document_processor_service import DocumentProcessorFactory
from services.query_service import QueryServiceFactory
from services.ingestion_service import IngestionServiceFactory
from services.config_service import config_service
from services.logging_service import logging_service
from core.exceptions import ConfigurationException

T = TypeVar('T')

class ServiceContainer:
    """Dependency injection container for managing services"""
    
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self.logger = logging_service.get_logger(__name__)
        self._initialized = False

    def initialize(self):
        """Initialize core services"""
        if self._initialized:
            return
        
        try:
            self.logger.info("Initializing service container...")
            
            # Initialize logging first
            logging_service.setup_logging()
            
            # Configuration is already loaded in config_service
            
            self._initialized = True
            self.logger.info("Service container initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing service container: {str(e)}")
            raise ConfigurationException(f"Failed to initialize service container: {str(e)}")

    def register(self, name: str, service: Any, singleton: bool = True):
        """Register a service"""
        if singleton:
            self._singletons[name] = service
        else:
            self._services[name] = service
        self.logger.info(f"Registered service: {name}")

    def get(self, service_type: type[T]) -> T:
        """Get service instance by type"""
        service_name = service_type.__name__
        
        # Check singletons first
        if service_name in self._singletons:
            return self._singletons[service_name]
        
        # Create and cache singleton instances for core services
        if service_name == 'LLMService':
            service = self._create_llm_service()
            self._singletons[service_name] = service
            return service
        
        elif service_name == 'VectorStoreService':
            service = self._create_vector_store_service()
            self._singletons[service_name] = service
            return service
        
        elif service_name == 'DocumentProcessorService':
            service = self._create_document_processor_service()
            self._singletons[service_name] = service
            return service
        
        elif service_name == 'QueryService':
            service = self._create_query_service()
            self._singletons[service_name] = service
            return service
        
        else:
            raise ValueError(f"Unknown service type: {service_name}")

    def _create_llm_service(self) -> LLMService:
        """Create LLM service instance"""
        llm_config = config_service.get_section('llm')
        return LLMServiceFactory.create_llm_service(
            provider="gemini",
            api_key=llm_config.get('gemini_api_key'),
            model=llm_config.get('gemini_model')
        )

    def _create_vector_store_service(self) -> VectorStoreService:
        """Create vector store service instance"""
        vector_config = config_service.get_section('vector_store')
        return FAISSVectorStoreService(vector_db_path=vector_config.get('path'))

    def _create_document_processor_service(self) -> DocumentProcessorService:
        """Create document processor service instance"""
        doc_config = config_service.get_section('document_processing')
        return DocumentProcessorFactory.create_processor(
            processor_type="pdf",
            chunk_size=doc_config.get('chunk_size'),
            chunk_overlap=doc_config.get('chunk_overlap')
        )

    def _create_query_service(self) -> QueryService:
        """Create query service instance"""
        llm_service = self.get(LLMService)
        vector_store_service = self.get(VectorStoreService)
        
        return QueryServiceFactory.create_query_service(
            service_type="rag",
            llm_service=llm_service,
            vector_store_service=vector_store_service
        )

    def get_ingestion_service(self) -> 'IngestionService':
        """Get ingestion service instance"""
        doc_processor = self.get(DocumentProcessorService)
        vector_store = self.get(VectorStoreService)
        pdf_dir = config_service.get('document_processing.pdf_dir')
        
        return IngestionServiceFactory.create_ingestion_service(
            document_processor=doc_processor,
            vector_store_service=vector_store,
            pdf_dir=pdf_dir
        )

    def clear(self):
        """Clear all registered services"""
        self._services.clear()
        self._singletons.clear()
        self.logger.info("Service container cleared")

# Global service container instance
service_container = ServiceContainer()
