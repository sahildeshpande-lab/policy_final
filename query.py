from langchain_community.vectorstores import FAISS
from embbeding import get_embeddings
from llm import GroqLLM
from config import VECTOR_DB_PATH
import streamlit as st

embeddings = get_embeddings()


def format_docs(docs):
    formatted = []
    sources = set()

    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        page = doc.metadata.get("page", "N/A")

        sources.add(source)

        formatted.append(
            f"[Source: {source}, Page: {page}]\n{doc.page_content}"
        )

    return "\n\n".join(formatted), list(sources)


@st.cache_resource
def load_vector_db():
    return FAISS.load_local(
        VECTOR_DB_PATH,
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )


@st.cache_resource
def get_retriever():
    vector_db = load_vector_db()
    return vector_db.as_retriever(search_kwargs={"k": 5})


def query_rag(question: str) -> dict:
    retriever = get_retriever()

    docs = retriever.invoke(question)

    if not docs:
        return {
            "answer": "Connect to HR for more detail.",
            "sources": []
        }

    context, sources = format_docs(docs)

    prompt = f"""
You are a company policy assistant.

Answer the user's question using ONLY the policy context below.
If the information is not found, say:
"Connect to HR for more detail."

POLICY CONTEXT:
{context}

USER QUESTION:
{question}
"""

    llm = GroqLLM()
    answer = llm.generate(prompt)

    return {
        "answer": answer,
        "sources": sources
    }