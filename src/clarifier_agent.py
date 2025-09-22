# Import libraries
from agents import Agent
from pydantic import BaseModel, Field
from typing import List

# Define pydantic model to store questions for classifier agent
class ClassifyingQuestions(BaseModel):
    questions: List[str] = Field(description="Three classifying questions to better understand the user's query.")

# Define instructions for the classifier agent 
CLASSIFIER_INSTRUCTIONS = (
    "You are a research assistant. Your task is to ask 3 clarifying questions that help refine and understand "
    "a research query better. After the user answers them, hand off control to the Research Coordinator to perform the full research."
)

# Create the classifier_agent
classifier_agent = Agent(
    name="Classifier Agent",
    instructions=CLASSIFIER_INSTRUCTIONS,
    model="gpt-4o-mini"
)