import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from services.service_container import service_container
from services.logging_service import logging_service
from api.routes import router
from api.middleware import RequestLoggingMiddleware, ErrorHandlingMiddleware, SecurityHeadersMiddleware
from services.config_service import config_service

# Initialize logging
logging_service.setup_logging()
logger = logging_service.get_logger(__name__)

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    # Initialize service container
    service_container.initialize()
    
    # Create FastAPI app
    app_config = config_service.get_section('api')
    app = FastAPI(
        title="Policy Assistant API",
        description="Production-ready policy assistant with RAG capabilities",
        version="2.0.0",
        debug=app_config.get('debug', False)
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Add custom middleware
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(ErrorHandlingMiddleware)
    app.add_middleware(RequestLoggingMiddleware)
    
    # Include routes
    app.include_router(router, prefix="/api/v1")
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Root redirect to API docs
    @app.get("/", include_in_schema=False)
    async def root():
        return {"message": "Policy Assistant API", "docs": "/docs", "version": "2.0.0"}
    
    # Initialize vector store and database on startup
    @app.on_event("startup")
    async def startup_event():
        try:
            logger.info("Starting up Policy Assistant API...")
            
            # Initialize database
            from repositories.database import database_manager
            await database_manager.initialize()
            
            # Initialize vector store
            vector_store = service_container.get(service_container.VectorStoreService)
            await vector_store.load()
            
            logger.info("Policy Assistant API started successfully")
            
        except Exception as e:
            logger.error(f"Error during startup: {str(e)}")
            raise
    
    @app.on_event("shutdown")
    async def shutdown_event():
        try:
            logger.info("Shutting down Policy Assistant API...")
            
            # Save vector store
            vector_store = service_container.get(service_container.VectorStoreService)
            await vector_store.save()
            
            # Close database
            from repositories.database import database_manager
            database_manager.close()
            
            logger.info("Policy Assistant API shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
    
    return app

# Create app instance
app = create_app()

if __name__ == "__main__":
    api_config = config_service.get_section('api')
    uvicorn.run(
        "main:app",
        host=api_config.get('host', '127.0.0.1'),
        port=api_config.get('port', 8001),
        reload=api_config.get('debug', False),
        log_level="info"
    )
