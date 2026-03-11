import os
import json
import uuid
import hashlib
import subprocess
import streamlit as st            
from ingest import ingest_single_pdf
import sys 


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


PDF_DIR = "pdfs"
REGISTRY_FILE = "uploaded_pdfs.json"

os.makedirs(PDF_DIR, exist_ok=True)

import streamlit as st

@st.cache_resource
def load_query_function():
    from query import query_rag
    return query_rag

@st.cache_resource
def load_summary_graph():
    from langgraph_summarize import build_summary_graph
    return build_summary_graph


st.set_page_config(page_title="Policy Assistant", layout="wide")
create_tables()


def file_hash_bytes(data: bytes):
    return hashlib.sha256(data).hexdigest()

def sync_existing_pdfs():
    """Register PDFs already present on disk but missing in JSON"""
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

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None

if "is_first_message" not in st.session_state:
    st.session_state.is_first_message = True


def login_screen():
    st.title("🔐 Login")
    email = st.text_input("Company Email")
    name = st.text_input("Name (optional)")

    if st.button("Login"):
        if not email:
            st.error("Email is required")
            return
        st.session_state.user = login_or_create_user(email, name)
        st.success("Logged in")

if "user" not in st.session_state:
    login_screen()
    st.stop()

USER_ID = st.session_state.user["user_id"]

st.sidebar.title("📄 PDF Upload")

uploaded_file = st.sidebar.file_uploader("Upload policy PDF", type=["pdf"])

if uploaded_file:
    pdf_bytes = uploaded_file.read()
    pdf_hash = file_hash_bytes(pdf_bytes)

    if os.path.exists(REGISTRY_FILE):
        with open(REGISTRY_FILE, "r") as f:
            registry = json.load(f)
    else:
        registry = {}

    if pdf_hash in registry:
        st.sidebar.warning(" !--- PDF already uploaded ---- ! ")
    else:
        save_path = os.path.join(PDF_DIR, uploaded_file.name)
        with open(save_path, "wb") as f:
            f.write(pdf_bytes)

        registry[pdf_hash] = {
            "filename": uploaded_file.name,
            "path": save_path
        }

        with open(REGISTRY_FILE, "w") as f:
            json.dump(registry, f, indent=2)

        with st.sidebar:
            progress = st.progress(0)
            st.write(" Indexing PDF...")



            progress.progress(30)
            ingest_single_pdf(save_path)
            progress.progress(100)

            st.success("PDF indexed successfully")

st.title(" Policy Chatbot")

st.sidebar.divider()
st.sidebar.title("💬 Conversations")

if st.sidebar.button("🚪 Logout"):
    st.session_state.clear()
    st.stop()

for convo in get_user_conversations(USER_ID):
    if st.sidebar.button(convo["title"], key=convo["thread_id"]):
        st.session_state.thread_id = convo["thread_id"]
        st.session_state.is_first_message = False


if st.session_state.thread_id:
    for msg in get_conversation_messages(st.session_state.thread_id):
        st.chat_message("user").write(msg["user_message"])
        st.chat_message("assistant").write(msg["assistant_message"])
else:
    st.info("Start a new conversation by asking a question.")

user_input = st.chat_input("Ask a question about company policies...")

if user_input:
    if not st.session_state.thread_id:
        st.session_state.thread_id = str(uuid.uuid4())
        create_conversation(
            user_id=USER_ID,
            thread_id=st.session_state.thread_id,
            title="New Conversation"
        )
        st.session_state.is_first_message = True

    st.chat_message("user").write(user_input)

    with st.spinner("Thinking..."):
        result = query_rag(user_input)
        answer = result["answer"]
        sources = result.get("sources", [])

    with st.chat_message("assistant"):
        st.write(answer)
        if sources:
            st.markdown("📄 **Source policies:**")
            for src in sources:
                st.markdown(f"- {src}")

    if st.session_state.is_first_message:
        graph = build_summary_graph()
        summary = graph.invoke({"ai_response": answer})
        update_conversation_title(
            st.session_state.thread_id,
            summary["summary"]
        )
        st.session_state.is_first_message = False

    add_message(
        thread_id=st.session_state.thread_id,
        user_message=user_input,
        assistant_message=answer
    )
