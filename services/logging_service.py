import logging
import sys
from typing import Optional
from services.config_service import config_service

class LoggingService:
    """Logging configuration and management service"""
    
    def __init__(self):
        self._configured = False

    def setup_logging(self):
        """Setup logging configuration"""
        if self._configured:
            return
        
        try:
            log_config = config_service.get_section('logging')
            
            # Configure logging level
            level = getattr(logging, log_config.get('level', 'INFO').upper())
            
            # Configure format
            log_format = log_config.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            
            # Configure handlers
            handlers = []
            
            # Console handler
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(level)
            console_formatter = logging.Formatter(log_format)
            console_handler.setFormatter(console_formatter)
            handlers.append(console_handler)
            
            # File handler (if specified)
            log_file = log_config.get('file')
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(level)
                file_formatter = logging.Formatter(log_format)
                file_handler.setFormatter(file_formatter)
                handlers.append(file_handler)
            
            # Configure root logger
            logging.basicConfig(
                level=level,
                handlers=handlers,
                force=True
            )
            
            # Set specific logger levels
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("aiohttp").setLevel(logging.WARNING)
            logging.getLogger("urllib3").setLevel(logging.WARNING)
            
            self._configured = True
            logging.info("Logging configured successfully")
            
        except Exception as e:
            print(f"Error configuring logging: {str(e)}")
            # Fallback to basic configuration
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

    def get_logger(self, name: str) -> logging.Logger:
        """Get logger instance"""
        if not self._configured:
            self.setup_logging()
        return logging.getLogger(name)

# Global logging service instance
logging_service = LoggingService()
