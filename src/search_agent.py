from tavily import TavilyClient
from dotenv import load_dotenv
import os 

load_dotenv()
tavily_api_key = os.getenv("TAVILY_API_KEY")

def search_agent(query):
    tavily_client = TavilyClient(tavily_api_key)
    response = tavily_client.search(query)
    return response