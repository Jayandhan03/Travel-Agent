from pydantic import BaseModel, Field

class WeatherSummary(BaseModel):
    summary: str = Field(..., description="A concise, one-sentence summary of the weather details, under 100 characters.")  
    details: str = Field(..., description="A concise summary of the weather details.")   


