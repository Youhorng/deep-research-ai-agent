# Import libraries
from pydantic import BaseModel, Field
from typing import List
from agents import Agent

# Define the number of web searches 
HOW_MANY_SEARCHES = 3

# Define instructions for the planner agent
PLANNER_INSTRUCTIONS = f"You are a helpful research assistant. Given a query, come up with a set of web searches \
to perform to best answer the query. Output {HOW_MANY_SEARCHES} terms to query for."


# Create the pydantic model to store the planned searches
class WebSearchItem(BaseModel):
    reason: str = Field(description="Your reasoning for why this search is important to the query")
    query: str = Field(description="The search term to use for the web search")


class WebSearchPlan(BaseModel):
    searches: List[WebSearchItem] = Field(description=f"A list of web searches to perform to best answer the query")


# Create the planner_agent
planner_agent = Agent(
    name="Planner Agent",
    instructions=PLANNER_INSTRUCTIONS,
    model="gpt-4o-mini",
    output_type=WebSearchPlan
)