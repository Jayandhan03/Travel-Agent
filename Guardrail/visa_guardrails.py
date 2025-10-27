from pydantic import BaseModel, Field

class StructuredPlanOutput(BaseModel):
    summary: str = Field(..., description="A concise, one-sentence summary of the visa details, under 100 characters.")
    details: str = Field(..., description="A full, human-readable summary of all the visa details.")

