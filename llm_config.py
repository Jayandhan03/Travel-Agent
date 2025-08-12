import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model="mixtral-8x7b-32768-free",  # ✅ Updated free version
    temperature=0,
    api_key=os.getenv("GROQ_API_KEY")
)

