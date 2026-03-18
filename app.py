import os
import json
import uuid
import hashlib
import time
from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional

from ingest import ingest_single_pdf
from db import (
    create_tables,
    create_conversation,
    add_message,
    get_user_conversations,
    get_conversation_messages,
    update_conversation_title,
    login_or_create_user
)

from query import query_rag
from langgraph_summarize import build_summary_graph

app = FastAPI(title="Policy Assistant API")

PDF_DIR = "pdfs"
REGISTRY_FILE = "uploaded_pdfs.json"

os.makedirs(PDF_DIR, exist_ok=True)
create_tables()

# Serve static files from static folder
app.mount("/static", StaticFiles(directory="static"), name="static")

def file_hash_bytes(data: bytes):
    return hashlib.sha256(data).hexdigest()

def sync_existing_pdfs():
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

sync_existing_pdfs()

GUEST_USER = login_or_create_user("guest@company.com", "Guest User")
USER_ID = GUEST_USER["user_id"]

class ChatRequest(BaseModel):
    thread_id: Optional[str] = None
    message: str
    request_type: str = "Any Query"

class LeaveRequest(BaseModel):
    name: str
    empId: str
    leaveGrade: int
    leaveStartDate: str
    leaveEndDate: str
    leaveType: int
    leaveCategory: int
    leaveContent: str
    managerId: str
    salt: str
    thread_id: Optional[str] = None

class WfhRequest(BaseModel):
    empId: str
    wfhStartDate: str
    wfhEndDate: str
    reason: str
    is_extra_request: int
    managerId: str
    thread_id: Optional[str] = None

class ItTicketRequest(BaseModel):
    EmployeeId: str
    title: str
    description: str
    attachment: str
    category_id: int
    managerId: str
    thread_id: Optional[str] = None

@app.get("/", response_class=HTMLResponse)
async def read_index():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/upload_pdf")
async def upload_pdf(file: UploadFile = File(...)):
    pdf_bytes = await file.read()
    pdf_hash = file_hash_bytes(pdf_bytes)

    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            registry = json.load(f)
    else:
        registry = {}

    if pdf_hash in registry:
        return {"message": "PDF already uploaded"}

    save_path = os.path.join(PDF_DIR, file.filename)
    with open(save_path, "wb") as f:
        f.write(pdf_bytes)

    registry[pdf_hash] = {
        "filename": file.filename,
        "path": save_path
    }

    with open(REGISTRY_FILE, "w") as f:
        json.dump(registry, f, indent=2)

    if os.getenv("RENDER") is None:
        ingest_single_pdf(save_path)
    return {"message": "PDF indexed successfully"}

@app.post("/upload_file")
async def upload_file(file: UploadFile = File(...)):
    # Simple upload for ticket attachments
    upload_dir = os.path.join("static", "uploads", f"emp_{USER_ID}")
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Return the relative path for the frontend
    return {"message": "File uploaded", "path": f"/static/uploads/emp_{USER_ID}/{file.filename}"}

@app.get("/conversations")
async def get_convos():
    return get_user_conversations(USER_ID)

@app.get("/conversations/{thread_id}/messages")
async def get_messages(thread_id: str):
    return get_conversation_messages(thread_id)

@app.post("/chat")
async def chat(req: ChatRequest):
    thread_id = req.thread_id
    is_first_message = False

    if not thread_id:
        thread_id = str(uuid.uuid4())
        create_conversation(USER_ID, thread_id, "New Conversation")
        is_first_message = True

    result = query_rag(req.message, req.request_type)
    answer = result["answer"]
    sources = result.get("sources", [])

    if is_first_message:
        graph = build_summary_graph()
        summary = graph.invoke({"ai_response": answer})
        update_conversation_title(thread_id, summary["summary"])

    add_message(thread_id, req.message, answer)
    return {"thread_id": thread_id, "response": answer, "sources": sources}

@app.post("/leave_apply")
async def apply_leave(req: LeaveRequest):
    thread_id = req.thread_id
    if not thread_id:
        thread_id = str(uuid.uuid4())
        create_conversation(USER_ID, thread_id, "Leave Application")

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

    add_message(thread_id, user_msg, assistant_msg)
    return {"thread_id": thread_id, "message": "Leave Application Submitted", "data": collected_data}

@app.post("/wfh_apply")
async def apply_wfh(req: WfhRequest):
    thread_id = req.thread_id
    if not thread_id:
        thread_id = str(uuid.uuid4())
        create_conversation(USER_ID, thread_id, "WFH Application")

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

    add_message(thread_id, user_msg, assistant_msg)
    return {"thread_id": thread_id, "message": "WFH Application Submitted", "data": collected_data}

@app.post("/it_ticket_apply")
async def apply_it_ticket(req: ItTicketRequest):
    thread_id = req.thread_id
    if not thread_id:
        thread_id = str(uuid.uuid4())
        create_conversation(USER_ID, thread_id, "IT Ticket Raised")

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
        routed_to_email = f"{req.managerId}@company.com" # Placeholder for manager email lookup

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

    add_message(thread_id, user_msg, assistant_msg)
    return {"thread_id": thread_id, "message": "IT Ticket Submitted", "data": collected_data}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)