from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from typing import List, Optional

# 1️⃣ Define Hotel-specific schema
class HotelOffer(BaseModel):
    summary: str   
    details: str

# 2️⃣ Wrap in a parser
hotel_parser = PydanticOutputParser(pydantic_object=HotelOffer)

# 3️⃣ Build a strict summarizer prompt
hotel_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Hotel Information Summarizer.\n"
     "Input will always be JSON from a hotel API (SerpAPI Google Hotels).\n\n"
     "Your task:\n"
     "1. Extract ALL available fields from the hotel API response: name, star rating, overall rating, price, address, booking URL.\n"
     "2. Include only fields that are actually available.\n"
     "3. Provide a warning if fallback logic was triggered (price or star rating removed).\n"
     "4. Maintain a clear, structured output for end users.\n"
     "5. DO NOT invent missing information.\n\n"
     "Formatting:\n"
     "- Follow the HotelSummary schema strictly.\n"
     "- Output only JSON matching the schema, no extra commentary.\n\n"
     "{format_instructions}"
    ),
    ("user", "{json_tool_output}")
])

# 4️⃣ Define a reusable summarizer function for the Hotel agent
def summarize_hotel_output( json_tool_output: dict, llm):
    """Takes the raw hotel API output and returns validated JSON according to HotelSummary schema."""
    chain = hotel_prompt | llm | hotel_parser
    return chain.invoke({
        "json_tool_output": json_tool_output,
        "format_instructions": hotel_parser.get_format_instructions()
    })
