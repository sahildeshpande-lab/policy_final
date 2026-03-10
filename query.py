from langchain_community.vectorstores import FAISS
from embbeding import get_embeddings
from llm import OpenRouterLLM
from config import VECTOR_DB_PATH
import streamlit as st


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
        embeddings=get_embeddings(),
        allow_dangerous_deserialization=True
    )


def query_rag(question: str) -> dict:
    vector_db = load_vector_db()   
    retriever = vector_db.as_retriever(search_kwargs={"k": 5})

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

    llm = OpenRouterLLM()
    answer = llm.generate(prompt)

    return {
        "answer": answer,
        "sources": sources
    }


if __name__ == "__main__":
    user_question = input("Ask a policy question: ")
    query_rag(user_question)
