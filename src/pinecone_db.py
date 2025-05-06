from pinecone import Pinecone
from file_utils import extract_text
from chunk_util import chunk_text
from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer
from langchain_ollama.llms import OllamaLLM
import os

# Load environment variables from .env file
load_dotenv()

# Load LLM
llm_for_relevance = OllamaLLM(model="gemma3:4b-it-qat")

# Create embedding of user input
embed_model = SentenceTransformer("intfloat/multilingual-e5-large")

pc = Pinecone(os.getenv("PINECONE_API_KEY"))

index_name = "ace-vectors"

if not pc.has_index(index_name):
    pc.create_index_for_model(
        name = index_name,
        cloud = "aws",
        region = "us-east-1", # DO NOT CHANGE THE REGION
        embed = {
            "model": "multilingual-e5-large",
            "field_map": {"text": "chunk_text"}
        }
    )

index = pc.Index(index_name)    

def upload_file_to_pinecone(uid, session_id, file_path):
    raw_text = extract_text(file_path)
    chunks = chunk_text(raw_text)

    payload = []

    for i, chunk in enumerate(chunks):
        doc_id = f"{uid}_{session_id}_{i}"
        embedding = embed_model.encode(f"passage: {chunk}", normalize_embeddings=True)
        payload.append({
            "id": doc_id,
            "values": embedding.tolist(),
            "metadata": {
                "chunk_text": chunk,
                "uid": uid,
                "session_id": session_id,
                "file_name": os.path.basename(file_path)
            }
        })
    
    try:
        # Push to pinecone
        index.upsert(vectors=payload)
        print(f"{file_path} uploaded successfully!")
    except Exception as e:
        print(f"An error occured while uploading the file: {e}")


def embed_query(text: str, embed_model) -> list:
    embedding = embed_model.encode(f"query: {text}", normalize_embeddings=True)
    return embedding.tolist()

def retrieve_and_verify_relevance(user_input, uid, session_id):
    query_embedding = embed_query(user_input, embed_model)

    results = index.query(
        vector=query_embedding,
        filter={"uid": uid, "session_id": session_id},
        top_k=10,
        include_metadata=True
    )

    retrieved_docs = [match['metadata']['chunk_text'] for match in results['matches']]
    
    if retrieved_docs:
        joined_docs = "\n\n".join(retrieved_docs)
        relevance_prompt = f"""
        You are ACE, an academic assistant that helps students from school to PhD level.
        User's Question: {user_input}
        Here are some documents retrieved from the user's uploaded files: {joined_docs}
        If you find any information which can be used to answer the user's query, then reply with only "yes"; otherwise, reply with only "no".
        """
        decision = llm_for_relevance.invoke(relevance_prompt).strip().lower()
        return decision.startswith("yes"), retrieved_docs

    return False, []
