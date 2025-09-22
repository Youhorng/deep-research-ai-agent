# Import libraries
import os
import requests
from mailjet_rest import Client
from agents import Agent, function_tool

# Create function tool to send email 
@function_tool
def send_email(subject: str, html_body: str, to:str):
    api_key = os.environ['MJ_APIKEY_PUBLIC']
    api_secret = os.environ['MJ_APIKEY_PRIVATE'] 

    # Create the mailjet client 
    mailjet = Client(auth=(api_key, api_secret), version='v3.1')

    # Define the payload 
    data = {
    'Messages': [
                    {
                            "From": {
                                    "Email": "youhorng.kean@gmail.com"
                            },
                            "To": [
                                    {
                                            "Email": "lolishi30@gmail.com"
                                    }
                            ],
                            "Subject": subject,
                            "HTMLPart": html_body
                    }
            ]
    }

    # Send the email
    result = mailjet.send.create(data=data)

    return result.json()


# Define instructions for the email agent
EMAIL_INSTRUCTIONS = """You are able to send a nicely formatted HTML email based on a detailed report.
You will be provided with a detailed report and a recipient email. Use your tool to send one email, 
providing the report as HTML with an appropriate subject line."""

# Create the email_agent
email_agent = Agent(
    name="Email Agent",
    instructions=EMAIL_INSTRUCTIONS,
    tools=[send_email],
    model="gpt-4o-mini"
)