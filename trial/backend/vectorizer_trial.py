from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import ( 
    UnstructuredPDFLoader,
    UnstructuredPowerPointLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredFileLoader,
    TextLoader
)
import os

def get_loader(file_path):
    if file_path.endswith(".pdf"):
        return UnstructuredPDFLoader(file_path)
    elif file_path.endswith(".pptx"):
        return UnstructuredPowerPointLoader(file_path)
    elif file_path.endswith(".docx"):
        return UnstructuredWordDocumentLoader(file_path)
    elif file_path.endswith(".txt"):
        return TextLoader(file_path)
    elif file_path.endswith(".jpg") or file_path.endswith(".jpeg"):
        return UnstructuredFileLoader(file_path)
    else:
        raise ValueError("Unsupported file type. Please upload a PDF, PPTX, DOCX, TXT, or JPG file.")

def vectorize(file_path):
    loader = get_loader(file_path)
    documents = loader.load()

    # 🔹 Chunk the documents into smaller pieces
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    split_docs = splitter.split_documents(documents)

    embeddings = OllamaEmbeddings(model="mxbai-embed-large")
    db_location = "./backend/chroma_db"
    os.makedirs(db_location, exist_ok=True)

    vector_store = Chroma(
        collection_name="User_docs",
        persist_directory=db_location,
        embedding_function=embeddings,
    )

    # Assign unique string IDs for each chunk
    ids = [str(i) for i in range(len(split_docs))]
    vector_store.add_documents(documents=split_docs, ids=ids)

    retriever = vector_store.as_retriever(search_kwargs={"k": min(10, len(split_docs))})
    return retriever
