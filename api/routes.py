import os
import json
import uuid
import time
import hashlib
from typing import Optional, Dict, Any
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse

from api.schemas import (
    ChatRequest, ChatResponse, LeaveRequest, WfhRequest, 
    ItTicketRequest, FileUploadResponse, ConversationResponse,
    MessagesResponse, ErrorResponse, HealthResponse, IngestionStatusResponse
)
from services.service_container import service_container
from services.conversation_service import ConversationServiceFactory
from services.logging_service import logging_service
from core.exceptions import PolicyAssistantException, LLMServiceException, VectorStoreException

logger = logging_service.get_logger(__name__)

# Create router
router = APIRouter()

# Constants
PDF_DIR = "pdfs"
REGISTRY_FILE = "uploaded_pdfs.json"

# Ensure directories exist
os.makedirs(PDF_DIR, exist_ok=True)

def file_hash_bytes(data: bytes) -> str:
    """Generate SHA256 hash of file bytes"""
    return hashlib.sha256(data).hexdigest()

def sync_existing_pdfs():
    """Sync existing PDFs with registry"""
    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            registry = json.load(f)
    else:
        registry = {}

    updated = False
    for file in os.listdir(PDF_DIR):
        if not file.endswith(".pdf"):
            continue
        path = os.path.join(PDF_DIR, file)
        with open(path, "rb") as f:
            h = file_hash_bytes(f.read())
        if h not in registry:
            registry[h] = {"filename": file, "path": path}
            updated = True
    if updated:
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry, f, indent=2)

# Initialize
sync_existing_pdfs()

# Get guest user
async def get_guest_user():
    """Get or create guest user"""
    conv_service = ConversationServiceFactory.create_conversation_service()
    return await conv_service.get_or_create_user("guest@company.com", "Guest User")

@router.get("/", response_class=HTMLResponse)
async def read_index():
    """Serve index page"""
    try:
        with open("static/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Index page not found")

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {}
    
    try:
        # Check vector store
        vector_store = service_container.get(service_container.VectorStoreService)
        await vector_store.load()
        services_status["vector_store"] = "healthy"
    except Exception as e:
        services_status["vector_store"] = f"unhealthy: {str(e)}"
    
    try:
        # Check LLM service
        llm_service = service_container.get(service_container.LLMService)
        services_status["llm"] = "healthy"
    except Exception as e:
        services_status["llm"] = f"unhealthy: {str(e)}"
    
    overall_status = "healthy" if all("healthy" in status for status in services_status.values()) else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        services=services_status
    )

@router.post("/upload_pdf", response_model=FileUploadResponse)
async def upload_pdf(file: UploadFile = File(...)):
    """Upload and ingest PDF file"""
    try:
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")
        
        # Read file
        pdf_bytes = await file.read()
        pdf_hash = file_hash_bytes(pdf_bytes)
        
        # Check registry
        registry = {}
        if os.path.exists(REGISTRY_FILE):
            with open(REGISTRY_FILE, "r") as f:
                registry = json.load(f)
        
        if pdf_hash in registry:
            return FileUploadResponse(message="PDF already uploaded")
        
        # Save file
        save_path = os.path.join(PDF_DIR, file.filename)
        with open(save_path, "wb") as f:
            f.write(pdf_bytes)
        
        # Update registry
        registry[pdf_hash] = {
            "filename": file.filename,
            "path": save_path
        }
        
        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry, f, indent=2)
        
        # Ingest document
        ingestion_service = service_container.get_ingestion_service()
        result = await ingestion_service.ingest_single_pdf(save_path)
        
        if result["success"]:
            return FileUploadResponse(
                message="PDF indexed successfully",
                chunks_count=result["chunks_count"]
            )
        else:
            raise HTTPException(status_code=500, detail=result["message"])
            
    except PolicyAssistantException as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/upload_file", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload general file (e.g., attachments)"""
    try:
        user = await get_guest_user()
        user_id = user["user_id"]
        
        upload_dir = os.path.join("static", "uploads", f"emp_{user_id}")
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        return FileUploadResponse(
            message="File uploaded",
            path=f"/static/uploads/emp_{user_id}/{file.filename}"
        )
        
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload file")

@router.get("/conversations", response_model=ConversationResponse)
async def get_conversations():
    """Get user conversations"""
    try:
        user = await get_guest_user()
        user_id = user["user_id"]
        
        conv_service = ConversationServiceFactory.create_conversation_service()
        conversations = await conv_service.get_conversations(user_id)
        
        return ConversationResponse(conversations=conversations)
        
    except PolicyAssistantException as e:
        logger.error(f"Error getting conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations/{thread_id}/messages", response_model=MessagesResponse)
async def get_messages(thread_id: str):
    """Get conversation messages"""
    try:
        conv_service = ConversationServiceFactory.create_conversation_service()
        messages = await conv_service.get_messages(thread_id)
        
        return MessagesResponse(messages=messages)
        
    except PolicyAssistantException as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """Chat with the assistant"""
    try:
        user = await get_guest_user()
        user_id = user["user_id"]
        
        thread_id = req.thread_id
        is_first_message = False
        
        if not thread_id:
            thread_id = str(uuid.uuid4())
            is_first_message = True
        
        # Get services
        query_service = service_container.get(service_container.QueryService)
        conv_service = ConversationServiceFactory.create_conversation_service()
        
        # Process query
        result = await query_service.query(req.message, req.request_type)
        
        # Create conversation if first message
        if is_first_message:
            await conv_service.create_conversation(user_id, thread_id, "New Conversation")
            
            # Generate summary for title
            try:
                from services.summary_service import SummaryServiceFactory
                summary_service = SummaryServiceFactory.create_summary_service("langgraph")
                summary = await summary_service.generate_summary_with_graph(result["answer"])
                await conv_service.update_conversation_title(thread_id, summary)
            except Exception as e:
                logger.warning(f"Failed to generate conversation summary: {str(e)}")
        
        # Add message to conversation
        await conv_service.add_message(thread_id, req.message, result["answer"])
        
        return ChatResponse(
            thread_id=thread_id,
            response=result["answer"],
            sources=result.get("sources", []),
            context=result.get("context"),
            num_docs_retrieved=result.get("num_docs_retrieved")
        )
        
    except (LLMServiceException, VectorStoreException) as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except PolicyAssistantException as e:
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in chat: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/leave_apply")
async def apply_leave(req: LeaveRequest):
    """Apply for leave"""
    try:
        user = await get_guest_user()
        user_id = user["user_id"]
        
        thread_id = req.thread_id or str(uuid.uuid4())
        
        conv_service = ConversationServiceFactory.create_conversation_service()
        
        if not req.thread_id:
            await conv_service.create_conversation(user_id, thread_id, "Leave Application")
        
        collected_data = {
            "name": req.name,
            "empId": req.empId,
            "leaveGrade": req.leaveGrade,
            "leaveStartDate": req.leaveStartDate,
            "leaveEndDate": req.leaveEndDate,
            "leaveType": req.leaveType,
            "leaveCategory": req.leaveCategory,
            "leaveContent": req.leaveContent,
            "managerId": req.managerId,
            "salt": req.salt
        }
        
        user_msg = f"Submitted Leave Application for dates {req.leaveStartDate} to {req.leaveEndDate}."
        assistant_msg = f"Collected Data:\n```json\n{json.dumps(collected_data, indent=2)}\n```"
        
        await conv_service.add_message(thread_id, user_msg, assistant_msg)
        
        return {
            "thread_id": thread_id, 
            "message": "Leave Application Submitted", 
            "data": collected_data
        }
        
    except PolicyAssistantException as e:
        logger.error(f"Error applying leave: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/wfh_apply")
async def apply_wfh(req: WfhRequest):
    """Apply for work from home"""
    try:
        user = await get_guest_user()
        user_id = user["user_id"]
        
        thread_id = req.thread_id or str(uuid.uuid4())
        
        conv_service = ConversationServiceFactory.create_conversation_service()
        
        if not req.thread_id:
            await conv_service.create_conversation(user_id, thread_id, "WFH Application")
        
        status = 3 if req.is_extra_request == 1 else 0
        
        collected_data = {
            "empId": req.empId,
            "date": f"{req.wfhStartDate} to {req.wfhEndDate}",
            "reason": req.reason,
            "is_extra_request": req.is_extra_request,
            "status": status,
            "managerId": req.managerId,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        req_type_str = "Extra" if req.is_extra_request == 1 else "Normal"
        user_msg = f"Submitted {req_type_str} WFH Application for dates {req.wfhStartDate} to {req.wfhEndDate}."
        assistant_msg = f"Collected Data:\n```json\n{json.dumps(collected_data, indent=2)}\n```"
        
        await conv_service.add_message(thread_id, user_msg, assistant_msg)
        
        return {
            "thread_id": thread_id, 
            "message": "WFH Application Submitted", 
            "data": collected_data
        }
        
    except PolicyAssistantException as e:
        logger.error(f"Error applying WFH: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/it_ticket_apply")
async def apply_it_ticket(req: ItTicketRequest):
    """Apply for IT ticket"""
    try:
        user = await get_guest_user()
        user_id = user["user_id"]
        
        thread_id = req.thread_id or str(uuid.uuid4())
        
        conv_service = ConversationServiceFactory.create_conversation_service()
        
        if not req.thread_id:
            await conv_service.create_conversation(user_id, thread_id, "IT Ticket Raised")
        
        # Determine routing
        it_cats = [4, 5, 6, 7, 8, 10]
        hr_cats = [11, 12]
        
        if req.category_id in it_cats:
            routed_to = "IT Department"
            routed_to_email = "teamit@solacetechnologies.co.in"
        elif req.category_id in hr_cats:
            routed_to = "HR Department"
            routed_to_email = "hr.mgr@solacetechnologies.co.in"
        else:
            routed_to = "Direct Manager"
            routed_to_email = f"{req.managerId}@company.com"
        
        collected_data = {
            "EmployeeId": req.EmployeeId,
            "title": req.title,
            "description": req.description,
            "attachment": req.attachment,
            "category_id": req.category_id,
            "status": "Open",
            "routed_to": routed_to,
            "routed_to_email": routed_to_email,
            "managerId": req.managerId,
            "creation_date": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        user_msg = f"Submitted IT Ticket: '{req.title}'."
        assistant_msg = f"Collected Data:\n```json\n{json.dumps(collected_data, indent=2)}\n```"
        
        await conv_service.add_message(thread_id, user_msg, assistant_msg)
        
        return {
            "thread_id": thread_id, 
            "message": "IT Ticket Submitted", 
            "data": collected_data
        }
        
    except PolicyAssistantException as e:
        logger.error(f"Error applying IT ticket: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ingestion/status", response_model=IngestionStatusResponse)
async def get_ingestion_status():
    """Get ingestion service status"""
    try:
        ingestion_service = service_container.get_ingestion_service()
        status = await ingestion_service.get_ingestion_status()
        
        return IngestionStatusResponse(**status)
        
    except PolicyAssistantException as e:
        logger.error(f"Error getting ingestion status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
