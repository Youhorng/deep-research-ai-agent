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
    "a research query better. After the user answers them, hand off control to the Research Coordinator to perform the full research.\n\n"
    "Return your response in this exact format:\n"
    "Question 1: [your first question]\n"
    "Question 2: [your second question]\n"
    "Question 3: [your third question]\n\n"
    "Do not use any markdown formatting, bullet points, or numbering other than the format shown above. "
    "Keep each question concise and focused on clarifying the research scope, methodology, or specific aspects of the query."
)
# Create the classifier_agent
clarifier_agent = Agent(
    name="Classifier Agent",
    instructions=CLASSIFIER_INSTRUCTIONS,
    output_type=ClassifyingQuestions,
    model="gpt-4o-mini"
)