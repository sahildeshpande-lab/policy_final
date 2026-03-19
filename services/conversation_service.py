import asyncio
from typing import Dict, List, Any, Optional
from core.interfaces import ConversationService
from core.exceptions import PolicyAssistantException
from repositories.database import database_manager
from services.logging_service import logging_service

logger = logging_service.get_logger(__class__.__name__)

class DatabaseConversationService(ConversationService):
    """Database-backed conversation service using repository pattern"""
    
    def __init__(self):
        self._initialized = False

    async def _ensure_initialized(self):
        """Ensure database is initialized"""
        if not self._initialized:
            try:
                await database_manager.initialize()
                self._initialized = True
                logger.info("Database conversation service initialized")
            except Exception as e:
                logger.error(f"Error initializing conversation service: {str(e)}")
                raise PolicyAssistantException(f"Failed to initialize conversation service: {str(e)}")

    async def create_conversation(self, user_id: str, thread_id: str, title: str) -> bool:
        """Create a new conversation"""
        await self._ensure_initialized()
        
        try:
            success = await database_manager.conversation_repository.create_conversation(
                user_id, thread_id, title
            )
            if success:
                logger.info(f"Created conversation {thread_id} for user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise PolicyAssistantException(f"Failed to create conversation: {str(e)}")

    async def add_message(self, thread_id: str, user_message: str, ai_response: str) -> bool:
        """Add message to conversation"""
        await self._ensure_initialized()
        
        try:
            success = await database_manager.conversation_repository.add_message(
                thread_id, user_message, ai_response
            )
            if success:
                logger.debug(f"Added message to conversation {thread_id}")
            return success
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            raise PolicyAssistantException(f"Failed to add message: {str(e)}")

    async def get_conversations(self, user_id: str) -> List[Dict]:
        """Get user conversations"""
        await self._ensure_initialized()
        
        try:
            conversations = await database_manager.conversation_repository.get_conversations(user_id)
            logger.debug(f"Retrieved {len(conversations)} conversations for user {user_id}")
            return conversations
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            raise PolicyAssistantException(f"Failed to get conversations: {str(e)}")

    async def get_messages(self, thread_id: str) -> List[Dict]:
        """Get conversation messages"""
        await self._ensure_initialized()
        
        try:
            messages = await database_manager.conversation_repository.get_messages(thread_id)
            logger.debug(f"Retrieved {len(messages)} messages for conversation {thread_id}")
            return messages
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            raise PolicyAssistantException(f"Failed to get messages: {str(e)}")

    async def update_conversation_title(self, thread_id: str, title: str) -> bool:
        """Update conversation title"""
        await self._ensure_initialized()
        
        try:
            success = await database_manager.conversation_repository.update_conversation_title(
                thread_id, title
            )
            if success:
                logger.info(f"Updated title for conversation {thread_id}")
            return success
        except Exception as e:
            logger.error(f"Error updating conversation title: {str(e)}")
            raise PolicyAssistantException(f"Failed to update conversation title: {str(e)}")

    async def get_or_create_user(self, email: str, name: str) -> Dict[str, Any]:
        """Get or create user"""
        await self._ensure_initialized()
        
        try:
            user = await database_manager.user_repository.login_or_create_user(email, name)
            logger.debug(f"Retrieved/created user {email}")
            return user
        except Exception as e:
            logger.error(f"Error getting/creating user: {str(e)}")
            raise PolicyAssistantException(f"Failed to get/create user: {str(e)}")

class ConversationServiceFactory:
    @staticmethod
    def create_conversation_service(service_type: str = "database") -> ConversationService:
        """Factory method to create conversation service instances"""
        if service_type.lower() == "database":
            return DatabaseConversationService()
        else:
            raise PolicyAssistantException(f"Unsupported conversation service type: {service_type}")
