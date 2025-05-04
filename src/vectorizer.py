from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

pc = Pinecone(api_key="PINECONE_API_KEY")
