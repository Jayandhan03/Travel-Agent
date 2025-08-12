# research_agent.py
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.chat_history import InMemoryChatMessageHistory

load_dotenv()
groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(
    model="llama3-8b-8192", 
    api_key=groq_api_key
)


# Prompt
prompt = ChatPromptTemplate.from_template("""
You are a research travel agent.
Your job: make sure the user provides all of these details before passing to supervisor:
1. Purpose of trip
2. Duration (in days)
3. Number of companions
4. Departure location
5. Preferred destination

If any detail is missing, ask follow-up questions.
Once all details are collected, respond with:
"ALL_DETAILS_COLLECTED: {{details_here_as_JSON}}"

Conversation so far:
{chat_history}

User: {input}
Agent:
""")

# Runnable with memory
store = {}  # simple dict to hold conversations

def get_session_history(session_id: str) -> InMemoryChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

research_chain = RunnableWithMessageHistory(
    prompt | llm,
    get_session_history,
    input_messages_key="input",
    history_messages_key="chat_history"
)

def run_research_agent(user_input, session_id="default"):
    response = research_chain.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}}
    )
    return response.content
