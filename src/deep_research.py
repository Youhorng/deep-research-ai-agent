# Import libraries
import gradio as gr
import logging
import time
from datetime import datetime
from collections import defaultdict
from typing import Optional, List, Tuple
from dotenv import load_dotenv

from clarifier_agent import clarifier_agent
from research_manager import ResearchManager
from agents import Runner


# Load environment variables
load_dotenv(override=True)

# Setup logging 
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Create RateLimiter class to manage user session within the deep research app
class RateLimiter:

    def __init__(self, requests_per_minute: int = 2, daily_limit: int = 4):
        self.requests_per_minute = requests_per_minute
        self.daily_limit = daily_limit
       
        # Track request timestamps and daily counts
        self.request_time = defaultdict(list)
        self.daily_counts = defaultdict(lambda: {"date": "", "count": 0})


    # Get today's date
    def get_today(self) -> str:
        return datetime.now().strftime("%Y-%m-%d")
    

    # Remove requests older than 1 minute
    def cleanup_old_requests(self, user_id: str) -> None:
        now = time.time()
        self.request_time[user_id] = [
            timestamp for timestamp in self.request_time[user_id]
            if now - timestamp < 60
        ]
    

    # Check if user can make a new request
    def check_limits(self, user_id: str) -> Tuple[bool, str]:
        # Clean up the old requests
        self.cleanup_old_requests(user_id)

        # Check limit of request per minute 
        recent_requests = len(self.request_time[user_id])
        if recent_requests >= self.requests_per_minute:
            return False, f"Rate limit exceeded: Max {self.requests_per_minute} requests per minute."
        
        # Check daily limit 
        today = self.get_today()
        user_data = self.daily_counts[user_id]

        if user_data["date"] != today:
            user_data["date"] = today
            user_data["count"] = 0
        
        if user_data["count"] >= self.daily_limit:
            return False, f"Daily limit exceeded: Max {self.daily_limit} requests per day."
        
        # Record if new day
        self.request_time[user_id].append(time.time())
        user_data["count"] += 1

        return True, "OK"
    

# Create global rate limiter
rate_limiter = RateLimiter(requests_per_minute=2, daily_limit=2)


# Define a function to get user_id 
def get_user_id(request: Optional[gr.Request] = None) -> str:

    if request is None:
        return "anonymous"

    try:
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        client_host = getattr(request, 'host', None)
        if client_host:
            return client_host
    except Exception as e:
        logger.error(f"Error getting user ID: {str(e)}")
    
    return "unknown_user"


# Define a function to generate clarifying questions from clarifier_agent
async def generate_clarification_questions(query: str, request: gr.Request = None) -> List[str]:

    # Input validation
    if not query or not query.strip():
        return ["Please enter a research query first."]
    
    # Rate limiting 
    user_id = get_user_id(request)
    allowed, message = rate_limiter.check_limits(user_id)

    if not allowed:
        logger.info(f"Rate limit exceeded for user {user_id}: {message}")
        return f"{message}"
    
    try: 
        result = await Runner.run(clarifier_agent, input=query.strip())
        questions = result.final_output.questions

        # Validate the results
        if not questions or len(questions) == 0:
            return ["Could not generate questions. Please try again."]
        
        logger.info(f"Generated {len(questions)} questions for user {user_id}")
        return questions
    except Exception as e:
        logger.error(f"Error generating questions for user {user_id}: {str(e)}")
        return ["Error generating questions. Please try again."]
    

# Define a function to run the full research pipeline
async def run_deep_research_pipeline(query: str, q1: str, q2: str, q3: str,
                                     a1: str, a2: str, a3: str,
                                     send_email: bool, recipient_email: str,
                                     request: gr.Request = None):
    
    # Input validation 
    if not query or not query.strip():
        yield "❌ Please enter a research query first."
        return 
    
    # Validate email
    if send_email and not recipient_email:
        yield "❌ Please enter a recipient email to send the report."
        return
    
    # Rate limiting 
    user_id = get_user_id(request)
    allowed, message = rate_limiter.check_limits(user_id)

    if not allowed:
        yield f"❌ {message}"
        return 
    
    # Collect questions and answers for research 
    questions = [q1.strip(), q2.strip(), q3.strip()]
    answers = [a1.strip(), a2.strip(), a3.strip()]

    # Keep only non-empty pairs
    valid_pairs = [(q, a) for q, a in zip(questions, answers) if q and a]

    # Run the research manager agent
    research_manager = ResearchManager()

    try:
        valid_questions = [q for q, a in valid_pairs]
        valid_answers = [a for q, a in valid_pairs]

        logger.info(f"Starting research for user {user_id} with {len(valid_questions)} question-answer pairs")

        async for step in research_manager.run_pipeline(
            query,
            questions,
            answers,
            send_email,
            recipient_email
        ):
            yield step
    except Exception as e:
        logger.error(f"Error during research for user {user_id}: {str(e)}")
        yield f"❌ Error during research: {str(e)}"
        return 
    

# Define a function for gradio ui
def create_ui() -> gr.Blocks:
    
    with gr.Blocks(
        theme=gr.themes.Default(primary_hue="blue"),
        title="Deep Research Assistant"
    ) as interface:
        
        # Header
        gr.Markdown("# 🔍 Deep Research Agent")
        gr.Markdown("**Step 1:** Enter query → **Step 2:** Answer questions → **Step 3:** Get research report")

        # Input section
        with gr.Group():
            query_input = gr.Textbox(
                label = "What would you like to reserach?",
                placeholder="Enter your research question here...",
                lines=2
            )

            generate_btn = gr.Button(
                "Generate Clarifying Questions",
                variant="primary",
                size="lg"
            )

        # Question section
        with gr.Group():
            gr.Markdown("### 📝 Clarifying Questions")

            question_1 = gr.Textbox(label="Question 1", interactive=False)
            answer_1 = gr.Textbox(label="Your Answer 1", placeholder="Enter your answer...")
            
            question_2 = gr.Textbox(label="Question 2", interactive=False)
            answer_2 = gr.Textbox(label="Your Answer 2", placeholder="Enter your answer...")
            
            question_3 = gr.Textbox(label="Question 3", interactive=False)
            answer_3 = gr.Textbox(label="Your Answer 3", placeholder="Enter your answer...")
            
        # Email options
        with gr.Group():
            gr.Markdown("### 📧 Email Options")
            
            send_email_checkbox = gr.Checkbox(label="Send report via email")
            email_input = gr.Textbox(
                label="Recipient Email",
                placeholder="recipient@example.com",
                visible=False
            )

        # Action button
        research_btn = gr.Button(
            "🚀 Start Research", 
            variant="secondary",
            size="lg"
        )

        # Results
        with gr.Group():
            gr.Markdown("### 📄 Results")
            results_output = gr.Markdown(
                value="Results will appear here...",
                height=400
            )
        
        # Event handlers
        generate_btn.click(
            fn=generate_clarification_questions,
            inputs=[query_input],
            outputs=[question_1, question_2, question_3]
        )
        
        send_email_checkbox.change(
            fn=lambda checked: gr.update(visible=checked),
            inputs=[send_email_checkbox],
            outputs=[email_input]
        )
        
        research_btn.click(
            fn=run_deep_research_pipeline,
            inputs=[
                query_input,
                question_1, question_2, question_3,
                answer_1, answer_2, answer_3,
                send_email_checkbox, email_input
            ],
            outputs=[results_output]
        )
    
    return interface


def main():
    """Main application entry point"""
    
    # Setup logging
    logger.info("Starting Deep Research Agent...")
    
    # Create and launch UI
    interface = create_ui()
    
    # Launch with sensible defaults
    interface.launch(
        server_name="127.0.0.1",  # Local access only (secure)
        server_port=7860,         # Standard Gradio port
        inbrowser=True,           # Open browser automatically
        share=False,              # Don't create public link (secure)
        show_error=True,          # Show detailed errors in UI
        quiet=False               # Show startup logs
    )

if __name__ == "__main__":
    main()
