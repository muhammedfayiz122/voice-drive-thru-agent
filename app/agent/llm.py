
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

DEFAULT_LLM = "google-gemini"
    
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not set in environment variables")

def get_llm():
    return get_gemini_llm()

def get_gemini_llm():

    return ChatGoogleGenerativeAI(model="gemini-2.5-flash-preview-09-2025", api_key=google_api_key, temperature=0)