# Import libraries
from agents import Runner, trace, gen_trace_id
from serach_agent import search_agent
from writer_agent import writer_agent, ReportData
from email_agent import email_agent
from planner_agent import planner_agent, WebSearchItem, WebSearchPlan
import asyncio
from typing import Optional, List, Dict


# Define the ResearchManager class
class ResearchManager():

    def __init__(self):
        self.stats = {
            "total_searches": 0
        }

    # Method to run the pipeline 
    async def run_pipeline(self, query: str, questions: List[str], answers: List[str], recipient_email: str, send_email: bool = False):
        # Validate the input
        is_valid, error_message = self.validate_input(query, questions, answers)
        if not is_valid:
            yield f"❌ Input validation failed: {error_message}"
            return

        # Email validation
        if send_email and not recipient_email:
            yield "❌ Email sending requested but no recipient email provided."
            return
        
        self.stats["total_searches"] += 1

        # Execute the research pipeline
        try: 
            async for step in self.execute_pipeline_research(query, questions, answers, recipient_email, send_email):
                yield step
        except Exception as e:  
            yield f"❌ Research pipeline failed: {str(e)}"
            return


    # Method to execute the research 
    async def execute_pipeline_research(self, query: str, questions: List[str], answers: List[str], recipient_email: str, send_email: bool = False):
        # Setup tracing 
        trace_id = gen_trace_id()
        with trace("Research Pipeline", trace_id=trace_id):
            yield f"Trace: https://platform.openai.com/traces/trace?trace_id={trace_id}"
            async for step in self.run_agents_step(query, questions, answers, recipient_email, send_email):
                yield step
            

    # Method to run each agent in the research pipeline
    async def run_agents_step(self, query: str, questions: List[str], answers: List[str], recipient_email: str, send_email: bool = False):
        # Execute individual pipeline steps

        # Step 1: Planning 
        yield "Planning searches based on clarifications..."
        search_plan = await self.plan_searches(query, questions, answers)

        # Step 2: Searching
        yield f"Starting {len(search_plan.searches)} searches..."
        search_results = await self.perform_searches(search_plan)

        # Step 3: Writing Report
        yield "Analyzing search results and writing report..."
        report = await self.write_report(query, search_results)

        # Step 4: Sending Email (optional)
        if send_email and recipient_email:
            yield f"Sending report to {recipient_email}..."
            await self.send_report_email(report, recipient_email)
            yield f"Report sent to {recipient_email}."
        else:
            yield "Email sending skipped."

        # Return final report
        yield report.markdown_report


    # Method to validate the input
    def validate_input(self, query: str, questions: List[str], answers: List[str]) -> tuple[bool, str]: # Return a tuple of (is_valid, error_message)
        # Validate input parameters
        if not query or not query.strip():
            return False, "Query cannot be empty"
        
        if len(questions) != len(answers):
            return False, f"Mismatch: {len(questions)} questions but {len(answers)} answers"
        
        # Check for empty items
        for i, (q, a) in enumerate(zip(questions, answers)):
            if not q.strip():
                return False, f"Question {i+1} is empty"
            if not a.strip():
                return False, f"Answer {i+1} is empty"

        return True, ""


    # Method to plan the searches
    async def plan_searches(self, query: str, questions: List[str], answers: List[str]):
        # Build structure prompt for the planner_agent 
        clarifying_context = "\n".join(f"Q: {q}\nA: {a}" for q, a in zip(questions, answers))
        final_prompt = f"Query: {query}\n\nClarifications:\n{clarifying_context}"

        try:
            result = await Runner.run(planner_agent, final_prompt)
            search_plan = result.final_output

            # Validate the result of search plan
            if not search_plan.searches:
                raise ValueError("Planner agent returned no searches")
            
            print(f"Planned Searches: {len(search_plan.searches)} searches")
            return search_plan
        except Exception as e:
            raise Exception(f"Search Planner failed: {str(e)}")
        

    # Method to perform all searches concurrently
    async def perform_searches(self, search_plan: WebSearchPlan) -> List[str]:
        # Define the total number of searches based on the search plan
        num_searches = len(search_plan.searches)
        
        # Create tasks for concurrent execution
        tasks = [asyncio.create_task(self.search_web(item)) for item in search_plan.searches]
        results = []
        completed = 0

        # Gather results as they complete
        for task in asyncio.as_completed(tasks):
            result = await task 
            if result is not None:
                results.append(result)
            completed += 1
            print(f"Seraching... {completed}/{num_searches} completed")
            self.stats["total_searches"] += 1
        
        print("Finished all searches.")

        return results

    
    # Method to search the web for a single search item
    async def search_web(self, item: WebSearchItem) -> Optional[str]:
        # Perform single search based on the WebSearchItem (query, reason)
        input_text = f"Search: {item.query}\nReason: {item.reason}"

        try:
            result = await Runner.run(search_agent, input_text)
            result = result.final_output
            return str(result)
        except Exception as e:
            print(f"Search failed for '{item.query}': {str(e)}")
        return None
    

    # Method to synthesize the report
    async def write_report(self, query: str, search_results: List[str]) -> ReportData:
        # Define input message for the writer agent
        input_text = f"Original query: {query}\n\nSearch Results:\n" + "\n---\n".join(search_results)

        try:
            result  = await Runner.run(writer_agent, input_text)
            report = result.final_output

            # Validate the result
            if not report.markdown_report or not report.short_summary:
                raise ValueError("Writer agent returned incomplete report")
            
            return report
        except Exception as e:
            raise Exception(f"Report Writing failed: {str(e)}")


    # Method to send the report via email
    async def send_report_email(self, report: ReportData, recipient_email: str) -> None:
        # Define input message
        input_text = f"""
            Send the following research report as an email:
            To: {recipient_email}

            Body (HTML):
            {report.markdown_report}
        """

        try:
            await Runner.run(email_agent, input_text)
            print(f"✅ Email sent to {recipient_email}")
        except Exception as e:
            raise Exception(f"Email sending failed: {str(e)}")
            