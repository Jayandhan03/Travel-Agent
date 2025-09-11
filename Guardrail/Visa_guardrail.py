from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from langchain.prompts import ChatPromptTemplate

class ResearchSummary(BaseModel):
    summary: str = Field(..., description="One-sentence summary, <100 chars")
    details: str = Field(..., description="Full clean summary of the JSON tool output")

parser = PydanticOutputParser(pydantic_object=ResearchSummary)

summary_prompt = ChatPromptTemplate.from_messages([
    ("system",
     "You are a Visa Research Summarizer.\n"
     "You will always receive a JSON object from the visa information tool.\n\n"
     "Your task:\n"
     "1. Carefully analyze the JSON and extract EVERY piece of information present.\n"
     "2. Include details such as visa type, duration, eligibility, application process, required documents, fees, or any other fields present.\n"
     "3. Paraphrase all information into clear, compact, human-readable instructions that a person can easily follow.\n"
     "4. Do NOT omit any information from the JSON.\n"
     "5. Provide a one-sentence short summary (<100 chars) and a full detailed summary.\n\n"
     "Formatting:\n"
     "- Use the schema strictly: 'summary' for short one-line summary, 'details' for full readable instructions.\n"
     "- Do not add extra commentary, explanations, or text outside the schema.\n\n"
     "{format_instructions}"
    ),
    ("user", "{json_tool_output}")
])


def summarize_tool_output(json_tool_output: dict, llm):
    chain = summary_prompt | llm | parser
    return chain.invoke({
        "json_tool_output": json_tool_output,
        "format_instructions": parser.get_format_instructions()
    })

