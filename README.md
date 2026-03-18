# Policy Assistant API - Production Architecture

A production-ready policy assistant with RAG capabilities, built with FastAPI, LangChain, and modern service architecture.

## Architecture Overview

This application follows a clean, production-level architecture with:

- **Service Layer**: Modular services with dependency injection
- **Repository Pattern**: Data access abstraction
- **Async/Await**: Non-blocking operations throughout
- **Error Handling**: Comprehensive exception management
- **Logging**: Structured logging with proper levels
- **Configuration**: Environment-based configuration management
- **API Layer**: RESTful API with validation and middleware

## Features

- **RAG (Retrieval-Augmented Generation)**: Query policy documents with LLM
- **Document Ingestion**: Process and index PDF documents
- **Conversation Management**: Track user conversations
- **Form Processing**: Handle leave, WFH, and IT ticket applications
- **Health Monitoring**: Service health checks
- **Security**: Request validation, security headers, error handling

## Project Structure

```
policy_final/
├── api/                          # API layer
│   ├── schemas.py               # Pydantic models for validation
│   ├── middleware.py            # Custom middleware
│   └── routes.py                # API route definitions
├── core/                         # Core interfaces and exceptions
│   ├── interfaces.py            # Abstract base classes
│   └── exceptions.py            # Custom exceptions
├── services/                     # Business logic layer
│   ├── llm_service.py          # LLM abstraction
│   ├── vector_store_service.py  # Vector database operations
│   ├── document_processor_service.py  # Document processing
│   ├── query_service.py         # RAG query handling
│   ├── ingestion_service.py     # Document ingestion
│   ├── conversation_service.py  # Conversation management
│   ├── config_service.py        # Configuration management
│   ├── logging_service.py       # Logging setup
│   └── service_container.py     # Dependency injection
├── main.py                      # Application entry point
├── config.py                    # Legacy config (deprecated)
├── llm.py                       # Legacy LLM (deprecated)
├── query.py                     # Legacy query (deprecated)
├── ingest.py                    # Legacy ingest (deprecated)
└── requirements.txt             # Dependencies
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd policy_final
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Create directories**
   ```bash
   mkdir -p pdfs static/uploads
   ```

## Configuration

### Required Environment Variables

- `GEMINI_API_KEY`: Google Gemini API key for LLM functionality

### Optional Configuration

See `.env.example` for all available configuration options.

## Usage

### Running the Application

```bash
# Development mode
python main.py

# Or with uvicorn directly
uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```

### API Endpoints

- `GET /` - API information
- `GET /api/v1/health` - Health check
- `POST /api/v1/upload_pdf` - Upload and ingest PDF
- `POST /api/v1/chat` - Chat with the assistant
- `GET /api/v1/conversations` - Get user conversations
- `GET /api/v1/conversations/{thread_id}/messages` - Get conversation messages
- `POST /api/v1/leave_apply` - Apply for leave
- `POST /api/v1/wfh_apply` - Apply for WFH
- `POST /api/v1/it_ticket_apply` - Submit IT ticket
- `GET /api/v1/ingestion/status` - Get ingestion status

### API Documentation

Visit `http://localhost:8001/docs` for interactive API documentation (Swagger UI).

## Development

### Adding New Services

1. Create interface in `core/interfaces.py`
2. Implement service in `services/`
3. Register in `services/service_container.py`
4. Add to factory if needed

### Error Handling

All services should raise appropriate exceptions from `core/exceptions.py`. The middleware handles these and returns proper HTTP error responses.

### Logging

Use the logging service for consistent logging:

```python
from services.logging_service import logging_service

logger = logging_service.get_logger(__name__)
logger.info("This is an info message")
```

## Production Deployment

### Environment Setup

1. Set proper environment variables
2. Configure CORS origins appropriately
3. Set up reverse proxy (nginx/Apache)
4. Configure SSL/TLS
5. Set up monitoring and logging

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Monitoring

- Use `/api/v1/health` endpoint for health checks
- Monitor logs for errors and performance
- Track response times and error rates

## Migration from Legacy Code

The new architecture maintains backward compatibility with existing functionality while providing:

- Better error handling
- Async operations
- Dependency injection
- Configuration management
- Structured logging
- API validation

Legacy files (`config.py`, `llm.py`, `query.py`, `ingest.py`) are kept for reference but should not be used in new development.

## License

[Your License Here]
