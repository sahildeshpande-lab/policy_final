from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
import re

class ChatRequest(BaseModel):
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")
    message: str = Field(..., min_length=1, description="User message")
    request_type: str = Field("Any Query", description="Type of request")

    @validator('message')
    def validate_message(cls, v):
        if not v or not v.strip():
            raise ValueError('Message cannot be empty')
        return v.strip()

class LeaveRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Employee name")
    empId: str = Field(..., min_length=1, description="Employee ID")
    leaveGrade: int = Field(..., ge=1, le=10, description="Leave grade")
    leaveStartDate: str = Field(..., description="Leave start date (YYYY-MM-DD)")
    leaveEndDate: str = Field(..., description="Leave end date (YYYY-MM-DD)")
    leaveType: int = Field(..., ge=1, description="Leave type ID")
    leaveCategory: int = Field(..., ge=1, description="Leave category ID")
    leaveContent: str = Field(..., min_length=1, description="Leave reason/content")
    managerId: str = Field(..., min_length=1, description="Manager ID")
    salt: str = Field(..., min_length=1, description="Security salt")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")

    @validator('leaveStartDate', 'leaveEndDate')
    def validate_date_format(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v

    @validator('leaveEndDate')
    def validate_end_date(cls, v, values):
        if 'leaveStartDate' in values and v < values['leaveStartDate']:
            raise ValueError('End date must be after start date')
        return v

class WfhRequest(BaseModel):
    empId: str = Field(..., min_length=1, description="Employee ID")
    wfhStartDate: str = Field(..., description="WFH start date (YYYY-MM-DD)")
    wfhEndDate: str = Field(..., description="WFH end date (YYYY-MM-DD)")
    reason: str = Field(..., min_length=1, description="WFH reason")
    is_extra_request: int = Field(..., ge=0, le=1, description="Is extra request (0 or 1)")
    managerId: str = Field(..., min_length=1, description="Manager ID")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")

    @validator('wfhStartDate', 'wfhEndDate')
    def validate_date_format(cls, v):
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            raise ValueError('Date must be in YYYY-MM-DD format')
        return v

    @validator('wfhEndDate')
    def validate_end_date(cls, v, values):
        if 'wfhStartDate' in values and v < values['wfhStartDate']:
            raise ValueError('End date must be after start date')
        return v

class ItTicketRequest(BaseModel):
    EmployeeId: str = Field(..., min_length=1, description="Employee ID")
    title: str = Field(..., min_length=1, max_length=200, description="Ticket title")
    description: str = Field(..., min_length=1, max_length=1000, description="Ticket description")
    attachment: str = Field("", description="Attachment path")
    category_id: int = Field(..., ge=1, description="Category ID")
    managerId: str = Field(..., min_length=1, description="Manager ID")
    thread_id: Optional[str] = Field(None, description="Thread ID for conversation continuity")

class ChatResponse(BaseModel):
    thread_id: str = Field(..., description="Thread ID")
    response: str = Field(..., description="AI response")
    sources: List[str] = Field(default_factory=list, description="Source documents")
    context: Optional[str] = Field(None, description="Retrieved context")
    num_docs_retrieved: Optional[int] = Field(None, description="Number of documents retrieved")

class FileUploadResponse(BaseModel):
    message: str = Field(..., description="Upload status message")
    path: Optional[str] = Field(None, description="File path")
    chunks_count: Optional[int] = Field(None, description="Number of chunks created")

class ConversationResponse(BaseModel):
    conversations: List[Dict[str, Any]] = Field(default_factory=list, description="User conversations")

class MessagesResponse(BaseModel):
    messages: List[Dict[str, Any]] = Field(default_factory=list, description="Conversation messages")

class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")

class HealthResponse(BaseModel):
    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Health check timestamp")
    services: Dict[str, str] = Field(default_factory=dict, description="Individual service status")

class IngestionStatusResponse(BaseModel):
    vector_store_loaded: bool = Field(..., description="Vector store status")
    pdf_directory: str = Field(..., description="PDF directory path")
    pdf_file_count: int = Field(..., description="Number of PDF files")
    directory_exists: bool = Field(..., description="Directory exists")
