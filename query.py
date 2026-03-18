from langchain_community.vectorstores import FAISS
from embbeding import get_embeddings
from llm import GeminiLLM
from config import VECTOR_DB_PATH
from functools import lru_cache
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


@lru_cache(maxsize=None)
def load_vector_db():
    return FAISS.load_local(
        VECTOR_DB_PATH,
        embeddings=embeddings,
        allow_dangerous_deserialization=True
    )


@lru_cache(maxsize=None)
def get_retriever():
    vector_db = load_vector_db()
    return vector_db.as_retriever(search_kwargs={"k": 5})


def query_rag(question: str, request_type: str = "Any Query") -> dict:
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
The user is asking for help regarding: {request_type}

Behavior rules:

1. If the user message is a greeting (hi, hello, hey, good morning, good evening, etc.):
   - Respond with a greeting.
   - Ask the user what policy question or use case they need help with.

2. If the user asks about your use case, role, or what you can do:
   - Explain that you are an assistant designed to help employees find information from company policy documents.
   - Mention that you can answer questions related to policies such as leave policy, HR rules, workplace guidelines, etc.
   - Inform them that if the information is not available, they should connect to HR.

3. If the user asks a policy question:
   - Answer using ONLY the policy context below.

4. If the answer is not present in the context:
   - Reply exactly with: "Connect to HR for more detail."

POLICY CONTEXT:
{context}

USER QUESTION:
{question}
"""

    llm = GeminiLLM()
    answer = llm.generate(prompt)

    return {
        "answer": answer,
        "sources": sources
    }