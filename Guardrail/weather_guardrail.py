from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate
import json

class WeatherSummary(BaseModel):
    summary: str   # short one-line summary
    details: str   # full human-readable summary of the JSON

weather_parser = PydanticOutputParser(pydantic_object=WeatherSummary)

weather_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Weather Summarizer.\n"
     "You will receive a JSON object from the weather tool.\n"
     "Your task:\n"
     "1. Convert the JSON exactly as-is into a human-readable string.\n"
     "2. Provide a one-line short summary and a full detailed summary.\n"
     "3. Do NOT hallucinate or validate; just summarize the JSON.\n\n"
     "{format_instructions}"),
    ("user", "{json_tool_output}")
])

def summarize_weather_output(json_tool_output: dict, llm):
    chain = weather_prompt | llm | weather_parser
    return chain.invoke({
        "json_tool_output": json_tool_output,
        "format_instructions": weather_parser.get_format_instructions()
    })
