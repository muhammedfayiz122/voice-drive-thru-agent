
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from dotenv import load_dotenv

DEFAULT_LLM = "google-gemini"
    
load_dotenv()
google_api_key = os.getenv("GOOGLE_API_KEY")
if not google_api_key:
    raise ValueError("GOOGLE_API_KEY not set in environment variables")

def get_llm():
    return get_groq_llm()

def get_gemini_llm():
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", api_key=google_api_key, temperature=0)

def get_groq_llm():
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY not set in environment variables")
    return ChatGroq(model="openai/gpt-oss-120b", api_key=groq_api_key, temperature=0)