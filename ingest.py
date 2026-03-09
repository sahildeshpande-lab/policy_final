import os
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from embbeding import get_embeddings
from config import VECTOR_DB_PATH


def _get_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )


def ingest_single_pdf(pdf_path: str):
    """
    Incrementally add ONE PDF to FAISS
    """
    loader = PyPDFLoader(pdf_path)
    documents = loader.load()

    splitter = _get_splitter()
    chunks = splitter.split_documents(documents)

    embeddings = get_embeddings()

    if os.path.exists(VECTOR_DB_PATH):
        vector_db = FAISS.load_local(
            VECTOR_DB_PATH,
            embeddings,
            allow_dangerous_deserialization=True
        )
        vector_db.add_documents(chunks)
    else:
        vector_db = FAISS.from_documents(chunks, embeddings)

    vector_db.save_local(VECTOR_DB_PATH)

    return len(chunks)


def ingest_all_pdfs(pdf_dir="pdfs"):
    """
    Full rebuild (CLI / first run only)
    """
    documents = []

    for file in os.listdir(pdf_dir):
        if file.endswith(".pdf"):
            loader = PyPDFLoader(os.path.join(pdf_dir, file))
            documents.extend(loader.load())

    splitter = _get_splitter()
    chunks = splitter.split_documents(documents)

    vector_db = FAISS.from_documents(chunks, get_embeddings())
    vector_db.save_local(VECTOR_DB_PATH)

    print(f" ! ---  Ingested {len(chunks)} chunks from PDFs  --- ! ")


if __name__ == "__main__":
    ingest_all_pdfs()
