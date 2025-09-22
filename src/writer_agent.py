# Import libraries
from pydantic import BaseModel, Field
from agents import Agent 

# Define instructions for the writer agent 
WRITER_INSTRUCTIONS = (

)

# Create the pydantic model to store the final report
class ReportData(BaseModel):
    short_summary: str = Field(description="A short 2-3 sentence summary of the findings")
    markdown_report: str = Field(description="The final report")
    follow_up_questions: str = Field(description="Suggested topics to research further")

# Create the writer_agent 
writer_agent = Agent(
    name="Report Writing Agent",
    instructions=WRITER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=ReportData
)