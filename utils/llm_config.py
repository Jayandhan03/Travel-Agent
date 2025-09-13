import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()  # loads from .env file

LLMModel = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY")
)
