from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from typing import List, Optional
from langchain.prompts import ChatPromptTemplate

# 1️⃣ Define schema
class DayPlan(BaseModel):
    summary: str   
    details: str

# 2️⃣ Wrap in a parser
itinerary_parser = PydanticOutputParser(pydantic_object=DayPlan)

# 3️⃣ Prompt for Itinerary Guardrail
itinerary_guardrail_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are an Itinerary Generator.\n"
     "Input context will come from research, weather, flights, hotels, and activities.\n"
     "Your task:\n"
     "1. Merge all inputs into a consistent trip plan.\n"
     "2. DO NOT invent details not provided in state data.\n"
     "3. Ensure each day has a proper set of activities, linked to hotels/notes if available.\n"
     "4. If data is missing (e.g., no weather), leave that field empty instead of making things up.\n\n"
     "Output strictly in the JSON schema below.\n\n"
     "{format_instructions}"
    ),
    ("user", "{state_data}")
])

# 4️⃣ Usage example in itinerary_node
def summarize_itinerary_output(state_data: dict, llm):
    chain = itinerary_guardrail_prompt | llm | itinerary_parser
    return chain.invoke({
        "state_data": state_data,
        "format_instructions": itinerary_parser.get_format_instructions()
    })
