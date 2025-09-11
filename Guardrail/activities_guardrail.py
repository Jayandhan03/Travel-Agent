from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
from typing import List, Optional

# 1️⃣ Define Activity-specific schema
class Activity(BaseModel):
    summary: str   
    details: str

# 2️⃣ Wrap in a parser
activity_parser = PydanticOutputParser(pydantic_object=Activity)

# 3️⃣ Build a strict summarizer prompt
activity_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Tourist Activity Summarizer.\n"
     "Input will be any format from the OpenTripMap API.\n\n"
     "Your task:\n"
     "1. Extract ALL available fields from the API response: name, kinds, distance from city center.\n"
     "2. Include only fields that are actually available.\n"
     "3. Maintain a clear, structured output for end users.\n"
     "4. DO NOT invent missing information.\n\n"
     "Formatting:\n"
     "- Follow the ActivitySummary schema strictly.\n"
     "- Output only JSON matching the schema, no extra commentary.\n\n"
     "{format_instructions}"
    ),
    ("user", "{json_tool_output}")
])

# 4️⃣ Define a reusable summarizer function for the Activities agent
def summarize_activities_output(json_tool_output: dict, llm):
    """Takes the raw OpenTripMap API output and returns validated JSON according to ActivitySummary schema."""
    chain = activity_prompt | llm | activity_parser
    return chain.invoke({
        "json_tool_output": json_tool_output,
        "format_instructions": activity_parser.get_format_instructions()
    })
