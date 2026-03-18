import sqlite3
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional
from contextlib import asynccontextmanager
from services.logging_service import logging_service
from services.config_service import config_service

logger = logging_service.get_logger(__name__)

class DatabaseConnection:
    """Database connection manager"""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = Path(db_path or config_service.get('database.conversation_db_path'))
        self._connection = None
    
    def get_connection(self):
        """Get database connection"""
        if self._connection is None:
            self._connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False
            )
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON;")
        return self._connection
    
    def close(self):
        """Close database connection"""
        if self._connection:
            self._connection.close()
            self._connection = None

class UserRepository:
    """User repository for database operations"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    async def create_user(self, user_id: str, email: str, name: Optional[str] = None) -> bool:
        """Create a new user"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.db.get_connection().execute(
                    "INSERT OR IGNORE INTO users (user_id, email, name) VALUES (?, ?, ?)",
                    (user_id, email, name)
                )
            )
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.db.get_connection().commit
            )
            logger.info(f"Created user: {email}")
            return True
        except Exception as e:
            logger.error(f"Error creating user: {str(e)}")
            return False
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.db.get_connection().cursor()
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: cursor.execute(
                    "SELECT user_id, email, name FROM users WHERE email = ?",
                    (email,)
                )
            )
            
            row = await asyncio.get_event_loop().run_in_executor(
                None,
                cursor.fetchone
            )
            
            if row:
                return {
                    "user_id": row["user_id"],
                    "email": row["email"],
                    "name": row["name"]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {str(e)}")
            return None
    
    async def login_or_create_user(self, email: str, name: Optional[str] = None) -> Dict[str, Any]:
        """Login or create user"""
        user = await self.get_user_by_email(email)
        
        if user:
            return user
        
        import uuid
        user_id = str(uuid.uuid4())
        await self.create_user(user_id, email, name)
        
        return {
            "user_id": user_id,
            "email": email,
            "name": name
        }

class ConversationRepository:
    """Conversation repository for database operations"""
    
    def __init__(self, db_connection: DatabaseConnection):
        self.db = db_connection
    
    async def create_conversation(self, user_id: str, thread_id: str, title: str) -> bool:
        """Create a new conversation"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.db.get_connection().execute(
                    "INSERT INTO conversations (user_id, thread_id, title) VALUES (?, ?, ?)",
                    (user_id, thread_id, title)
                )
            )
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.db.get_connection().commit
            )
            logger.info(f"Created conversation: {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            return False
    
    async def add_message(
        self, 
        thread_id: str, 
        user_message: str, 
        assistant_message: str, 
        policies_used: Optional[List[str]] = None
    ) -> bool:
        """Add message to conversation"""
        try:
            policies_text = ",".join(policies_used) if policies_used else None
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.db.get_connection().execute(
                    """INSERT INTO conversation_messages 
                       (thread_id, user_message, assistant_message, policies_used) 
                       VALUES (?, ?, ?, ?)""",
                    (thread_id, user_message, assistant_message, policies_text)
                )
            )
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.db.get_connection().commit
            )
            logger.debug(f"Added message to conversation: {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Error adding message: {str(e)}")
            return False
    
    async def get_conversations(self, user_id: str) -> List[Dict[str, Any]]:
        """Get user conversations"""
        try:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.db.get_connection().cursor()
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: cursor.execute(
                    """SELECT thread_id, title, created_at 
                       FROM conversations 
                       WHERE user_id = ? 
                       ORDER BY created_at DESC""",
                    (user_id,)
                )
            )
            
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                cursor.fetchall
            )
            
            return [
                {
                    "thread_id": row["thread_id"],
                    "title": row["title"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting conversations: {str(e)}")
            return []
    
    async def get_messages(self, thread_id: str) -> List[Dict[str, Any]]:
        """Get conversation messages"""
        try:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.db.get_connection().cursor()
            )
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: cursor.execute(
                    """SELECT user_message, assistant_message, created_at 
                       FROM conversation_messages 
                       WHERE thread_id = ? 
                       ORDER BY created_at ASC""",
                    (thread_id,)
                )
            )
            
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                cursor.fetchall
            )
            
            return [
                {
                    "user_message": row["user_message"],
                    "assistant_message": row["assistant_message"],
                    "created_at": row["created_at"]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f"Error getting messages: {str(e)}")
            return []
    
    async def update_conversation_title(self, thread_id: str, title: str) -> bool:
        """Update conversation title"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: self.db.get_connection().execute(
                    "UPDATE conversations SET title = ? WHERE thread_id = ?",
                    (title, thread_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(
                None,
                self.db.get_connection().commit
            )
            logger.info(f"Updated conversation title: {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Error updating conversation title: {str(e)}")
            return False

class DatabaseManager:
    """Database manager with initialization and connection management"""
    
    def __init__(self):
        self.db_connection = DatabaseConnection()
        self.user_repository = UserRepository(self.db_connection)
        self.conversation_repository = ConversationRepository(self.db_connection)
        self._initialized = False
    
    async def initialize(self):
        """Initialize database tables"""
        if self._initialized:
            return
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None,
                self._create_tables
            )
            self._initialized = True
            logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def _create_tables(self):
        """Create database tables"""
        conn = self.db_connection.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        # Conversations table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversations (
            conversation_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            thread_id TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id)
                REFERENCES users(user_id)
                ON DELETE CASCADE
        );
        """)
        
        # Messages table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS conversation_messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id TEXT NOT NULL,
            user_message TEXT,
            assistant_message TEXT,
            policies_used TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (thread_id)
                REFERENCES conversations(thread_id)
                ON DELETE CASCADE
        );
        """)
        
        conn.commit()
        logger.info("Database tables created")
    
    def close(self):
        """Close database connection"""
        self.db_connection.close()

# Global database manager instance
database_manager = DatabaseManager()
