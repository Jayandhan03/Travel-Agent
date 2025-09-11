from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from typing import List

class FlightOffer(BaseModel):
    summary: str   
    details: str

# 2️⃣ Parser
flight_parser = PydanticOutputParser(pydantic_object=FlightOffer)

# 3️⃣ Simple prompt
flight_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Flight Information Instructor.\n"
     "Your job is to take flight data (from an API or any source) and present it cleanly for travelers.\n"
     "Include price, carrier, flight number, departure/arrival airports and times, and duration.\n"
     "Provide both a short summary and a detailed description for each offer.\n\n"
     "Output must strictly follow this JSON schema:\n"
     "{format_instructions}"
    ),
    ("user", "{json_tool_output}")
])

# 4️⃣ Summarizer
def summarize_flight_output(json_tool_output: dict, llm):
    chain = flight_prompt | llm | flight_parser
    return chain.invoke({
        "json_tool_output": json_tool_output,
        "format_instructions": flight_parser.get_format_instructions()
    })
