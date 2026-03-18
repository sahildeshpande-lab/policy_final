class PolicyAssistantException(Exception):
    """Base exception for policy assistant"""
    pass

class LLMServiceException(PolicyAssistantException):
    """LLM service related exceptions"""
    pass

class VectorStoreException(PolicyAssistantException):
    """Vector store related exceptions"""
    pass

class DocumentProcessingException(PolicyAssistantException):
    """Document processing related exceptions"""
    pass

class QueryServiceException(PolicyAssistantException):
    """Query service related exceptions"""
    pass

class ConfigurationException(PolicyAssistantException):
    """Configuration related exceptions"""
    pass
