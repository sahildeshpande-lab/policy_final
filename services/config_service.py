import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from core.exceptions import ConfigurationException
import logging

logger = logging.getLogger(__class__.__name__)

class ConfigService:
    """Configuration management service"""
    
    def __init__(self, env_file: Optional[str] = None):
        self.env_file = env_file
        self._config = {}
        self._load_config()

    def _load_config(self):
        """Load configuration from environment variables"""
        try:
            load_dotenv(self.env_file)
            
            # LLM Configuration
            self._config['llm'] = {
                'gemini_api_key': os.getenv("GEMINI_API_KEY"),
                'gemini_model': os.getenv("GEMINI_MODEL", "gemini-2.5-flash-lite"),
                'max_tokens': int(os.getenv("LLM_MAX_TOKENS", "1000")),
                'temperature': float(os.getenv("LLM_TEMPERATURE", "0.2")),
                'timeout': int(os.getenv("LLM_TIMEOUT", "60"))
            }
            
            # Vector Store Configuration
            self._config['vector_store'] = {
                'path': os.getenv("VECTOR_DB_PATH", "vector_db"),
                'embedding_model': os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
                'similarity_k': int(os.getenv("SIMILARITY_K", "5"))
            }
            
            # Document Processing Configuration
            self._config['document_processing'] = {
                'chunk_size': int(os.getenv("CHUNK_SIZE", "500")),
                'chunk_overlap': int(os.getenv("CHUNK_OVERLAP", "50")),
                'pdf_dir': os.getenv("PDF_DIR", "pdfs")
            }
            
            # API Configuration
            self._config['api'] = {
                'host': os.getenv("API_HOST", "127.0.0.1"),
                'port': int(os.getenv("API_PORT", "8001")),
                'debug': os.getenv("API_DEBUG", "false").lower() == "true"
            }
            
            # External APIs
            self._config['external_apis'] = {
                'openrouter_api_key': os.getenv("OPENROUTER_API_KEY"),
                'openrouter_base_url': os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
                'openrouter_model': os.getenv("OPENROUTER_MODEL"),
                'groq_api_key': os.getenv("GROQ_API_KEY")
            }
            
            # Database Configuration
            self._config['database'] = {
                'conversation_db_path': os.getenv("CONVERSATION_DB_PATH", "conversation_history.db")
            }
            
            # File Upload Configuration
            self._config['upload'] = {
                'max_file_size': int(os.getenv("MAX_FILE_SIZE", "50")), # MB
                'allowed_extensions': os.getenv("ALLOWED_EXTENSIONS", "pdf").split(","),
                'upload_dir': os.getenv("UPLOAD_DIR", "static/uploads")
            }
            
            # Logging Configuration
            self._config['logging'] = {
                'level': os.getenv("LOG_LEVEL", "INFO"),
                'format': os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
                'file': os.getenv("LOG_FILE", "policy_assistant.log")
            }
            
            # Validate required configurations
            self._validate_config()
            
            logger.info("Configuration loaded successfully")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            raise ConfigurationException(f"Failed to load configuration: {str(e)}")

    def _validate_config(self):
        """Validate required configuration values"""
        required_configs = [
            ('llm', 'gemini_api_key'),
        ]
        
        missing_configs = []
        for section, key in required_configs:
            if not self._config.get(section, {}).get(key):
                missing_configs.append(f"{section}.{key}")
        
        if missing_configs:
            raise ConfigurationException(f"Missing required configuration: {', '.join(missing_configs)}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'llm.gemini_model')"""
        try:
            keys = key.split('.')
            value = self._config
            
            for k in keys:
                value = value[k]
            
            return value if value is not None else default
            
        except (KeyError, TypeError):
            return default

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {})

    def get_all(self) -> Dict[str, Any]:
        """Get all configuration"""
        return self._config.copy()

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        try:
            keys = key.split('.')
            config = self._config
            
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            
            config[keys[-1]] = value
            logger.info(f"Configuration updated: {key}")
            
        except Exception as e:
            logger.error(f"Error setting configuration {key}: {str(e)}")
            raise ConfigurationException(f"Failed to set configuration: {str(e)}")

    def reload(self):
        """Reload configuration from environment"""
        logger.info("Reloading configuration...")
        self._config = {}
        self._load_config()

# Global configuration instance
config_service = ConfigService()
