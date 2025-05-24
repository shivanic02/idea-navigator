
#!/usr/bin/env python3
"""
Idea Evaluation Agentic System - Hackathon MVP
A multi-agent system for comprehensive idea analysis using CrewAI, Anthropic Claude, and Serper.
"""

import os
import json
import uuid
from datetime import datetime, timezone # Added timezone
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import anthropic # Changed from google.generativeai
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import BaseTool
import time # For delays
import re   # For parsing (less relevant for Claude's retryDelay but kept for structure)
# Removed Google GenAI specific imports

import requests # For Serper API calls

# Configuration
class Config:
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', 'your-anthropic-api-key-here') # CHANGED
    SERPER_API_KEY = os.getenv('SERPER_API_KEY', 'your-serper-api-key-here')
    
    # CHOOSE YOUR CLAUDE MODEL:
    # Opus is most powerful, Sonnet is a balance, Haiku is fastest and most affordable.
    # Examples: "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"
    MODEL_NAME = os.getenv('claude-3-haiku-20240307',"claude-sonnet-4-20250514") # CHANGED
    
    CONFIDENCE_THRESHOLD = 0.7
    ANTHROPIC_API_VERSION = "2023-06-01" # Recommended by Anthropic

# Initialize Anthropic Client (globally or per tool call)
# For simplicity, we'll initialize it where needed or pass it.
# Setting the API key for LiteLLM (used by CrewAI)
if Config.ANTHROPIC_API_KEY and Config.ANTHROPIC_API_KEY != 'your-anthropic-api-key-here':
    os.environ['ANTHROPIC_API_KEY'] = Config.ANTHROPIC_API_KEY
else:
    print("Warning: ANTHROPIC_API_KEY not found or is placeholder. Claude-based features might not work.")

if not Config.SERPER_API_KEY or Config.SERPER_API_KEY == 'your-serper-api-key-here':
    print("Warning: SERPER_API_KEY not found or is placeholder. SerperSearchTool will not work.")


# Data Models (Unchanged)
@dataclass
class LayerData:
    status: str = "pending"
    data: Dict[str, Any] = None
    insights: List[str] = None
    confidence: float = 0.0
    last_updated: str = ""
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}
        if self.insights is None:
            self.insights = []
        if not self.last_updated:
            self.last_updated = datetime.now(timezone.utc).isoformat() # Use timezone aware

@dataclass
class AnalysisState:
    session_id: str
    user_idea: str
    current_layer: int = 1
    layers: Dict[int, LayerData] = None
    overall_confidence: float = 0.0
    
    def __post_init__(self):
        if self.layers is None:
            self.layers = {i: LayerData() for i in range(1, 6)}

# Utility function for retrying Anthropic calls (for tools) - SIGNIFICANTLY CHANGED
def generate_with_retry_claude(
    client: anthropic.Anthropic, 
    prompt: str, 
    tool_name: str, 
    max_retries: int = 3, 
    default_initial_delay: int = 10 # Claude models (esp Haiku) can be faster
) -> str:
    """
    Calls Anthropic client.messages.create with retry logic for rate limiting.
    """
    if not Config.ANTHROPIC_API_KEY or Config.ANTHROPIC_API_KEY == 'your-anthropic-api-key-here':
        return f"Tool '{tool_name}': Cannot execute. ANTHROPIC_API_KEY is not configured."

    current_delay = default_initial_delay
    for attempt in range(max_retries):
        try:
            response = client.messages.create(
                model=Config.MODEL_NAME,
                max_tokens=2048, # Adjust as needed
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7, # Consistent with CrewAI agent config
            )
            # Assuming the main content is in the first text block
            if response.content and isinstance(response.content, list) and len(response.content) > 0:
                if hasattr(response.content[0], 'text'):
                     return response.content[0].text
                else: # Fallback if structure is slightly different
                     return str(response.content[0])
            return "Error: No content returned from Claude." # Should ideally not happen
        
        except anthropic.RateLimitError as e:
            # Anthropic's RateLimitError doesn't typically give a specific 'retryDelay' in the message body.
            # We'll rely on exponential backoff or headers if available (more advanced).
            sleep_duration = current_delay
            print(f"Tool '{tool_name}': Rate limit hit (Anthropic). Retrying in {sleep_duration}s... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(sleep_duration)
            current_delay = int(current_delay * 1.5) # Exponential backoff

            if attempt == max_retries - 1:
                final_error_message = f"Tool '{tool_name}': Failed after {max_retries} retries due to Anthropic rate limiting. Last error: {e}"
                print(final_error_message)
                return f"Tool '{tool_name}': Research unavailable after retries due to Anthropic rate limiting: {str(e)}"
        
        except anthropic.APIStatusError as e: # Catch other API status errors
            # Check if it's a 429 (Too Many Requests) that wasn't caught as RateLimitError
            if e.status_code == 429:
                sleep_duration = current_delay
                print(f"Tool '{tool_name}': API Status Error 429 (Anthropic). Retrying in {sleep_duration}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_duration)
                current_delay = int(current_delay * 1.5)
                if attempt == max_retries - 1:
                    return f"Tool '{tool_name}': Research unavailable after retries (APIStatusError 429): {str(e)}"
                continue # Retry
            else:
                print(f"Tool '{tool_name}': Anthropic API Status error: {e.status_code} - {e.message}")
                return f"Tool '{tool_name}': Research failed with Anthropic API error {e.status_code}: {str(e.message)}"
        
        except anthropic.APIConnectionError as e:
            print(f"Tool '{tool_name}': Anthropic API Connection error: {e}")
            # Potentially retry for connection errors too, but for now, fail fast.
            if attempt < max_retries -1:
                time.sleep(current_delay)
                current_delay *= 1.5
                continue
            return f"Tool '{tool_name}': Research failed due to Anthropic API connection error: {str(e)}"
        
        except Exception as e: # General catch-all
            print(f"Tool '{tool_name}': Non-rate limit error with Anthropic: {e}")
            return f"Tool '{tool_name}': Research failed with unexpected Anthropic error: {str(e)}"
            
    return f"Tool '{tool_name}': Exited retry loop unexpectedly."


# Custom Tools
# SerperSearchTool remains largely the same as it doesn't use the LLM directly for its core function.
class SerperSearchTool(BaseTool):
    name: str = "internet_search"
    description: str = (
        "Performs a real-time internet search using Google via Serper API. "
        "Input should be a concise search query. "
        "Useful for finding current events, specific facts, market data, competitor information, "
        "product reviews, or any other information available on the public internet."
    )

    def _run(self, query: str) -> str:
        if not Config.SERPER_API_KEY or Config.SERPER_API_KEY == 'your-serper-api-key-here':
            return "Serper API key not configured. Internet search is unavailable."
        # ... (rest of SerperSearchTool._run is identical to your original)
        url = "https://google.serper.dev/search"
        payload = json.dumps({"q": query})
        headers = {
            'X-API-KEY': Config.SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        results_string = f"Search results for query: '{query}'\n"
        max_results_to_process = 5
        try:
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            search_results = response.json()
            if not search_results: return f"{results_string}No information found."
            if "answerBox" in search_results and search_results["answerBox"]:
                ab = search_results["answerBox"]
                title = ab.get("title", "")
                answer = ab.get("answer") or ab.get("snippet")
                if answer: results_string += f"\nAnswer Box: {title}\n{answer}\n"
            if "knowledgeGraph" in search_results and search_results["knowledgeGraph"]:
                kg = search_results["knowledgeGraph"]
                title = kg.get("title", "")
                description = kg.get("description", "")
                if title and description:
                    results_string += f"\nKnowledge Graph: {title}\n{description}\n"
                    if kg.get("attributes"):
                        results_string += "Attributes:\n"
                        for attr, val in kg["attributes"].items(): results_string += f"  - {attr}: {val}\n"
            if "organic" in search_results and search_results["organic"]:
                results_string += "\nOrganic Search Results:\n"
                for i, result in enumerate(search_results["organic"][:max_results_to_process]):
                    title = result.get("title", "N/A")
                    link = result.get("link", "N/A")
                    snippet = result.get("snippet", "N/A")
                    results_string += f"{i+1}. Title: {title}\n   Link: {link}\n   Snippet: {snippet}\n\n"
            if len(results_string) == len(f"Search results for query: '{query}'\n"):
                return f"{results_string}No specific organic results, answer box, or knowledge graph found."
            return results_string.strip()
        except requests.exceptions.Timeout: return f"Error: Search query timed out for '{query}'."
        except requests.exceptions.HTTPError as e: return f"Error: HTTP error during search for '{query}': {e.response.status_code} - {e.response.text}"
        except requests.exceptions.RequestException as e: return f"Error: Failed to perform search for '{query}': {str(e)}"
        except Exception as e: return f"An unexpected error occurred while searching for '{query}': {str(e)}"


# MarketResearchTool and TrendAnalysisTool now use Anthropic
class MarketResearchTool(BaseTool):
    name: str = "llm_market_research_synthesis"
    description: str = (
        "Synthesizes market data and competitive information based on a query, using its internal knowledge (Claude LLM). "
        "This tool does NOT perform live web searches. Use 'internet_search' for real-time data. "
        "Use this tool to get a general overview, identify potential areas for deeper live search, or to brainstorm."
    )
    
    def _run(self, query: str) -> str:
        if not Config.ANTHROPIC_API_KEY or Config.ANTHROPIC_API_KEY == 'your-anthropic-api-key-here':
            return "Anthropic API key not configured. LLM-based market research is unavailable."
        try:
            client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY) # Initialize client
            prompt = f"""
            Based on general knowledge, provide a synthesized analysis for: {query}
            
            Include insights on:
            1. Potential market trends and data points (general understanding)
            2. Possible key competitor archetypes or examples
            3. Broad market size considerations
            4. General growth opportunities
            
            Keep response concise but insightful. State that this is based on general knowledge and not live data.
            """
            return generate_with_retry_claude(client, prompt, self.name)
        except Exception as e:
            return f"LLM-based Market Research (Claude) unavailable: {str(e)}"

class TrendAnalysisTool(BaseTool):
    name: str = "llm_trend_analysis_synthesis"
    description: str = (
        "Analyzes potential future trends relevant to an idea using its internal knowledge (Claude LLM). "
        "This tool does NOT perform live web searches. Use 'internet_search' for real-time trend data. "
        "Use this tool for brainstorming future scenarios or understanding broad technological and market shifts."
    )
    
    def _run(self, idea: str) -> str:
        if not Config.ANTHROPIC_API_KEY or Config.ANTHROPIC_API_KEY == 'your-anthropic-api-key-here':
            return "Anthropic API key not configured. LLM-based trend analysis is unavailable."
        try:
            client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY) # Initialize client
            prompt = f"""
            Based on general knowledge, analyze potential future trends for: {idea}
            
            Focus on:
            1. Broad technology trends
            2. Potential market shifts
            3. Possible user behavior changes
            4. General opportunities and threats based on these trends
            
            Provide specific, actionable insights based on general understanding. State that this is based on general knowledge and not live data.
            """
            return generate_with_retry_claude(client, prompt, self.name)
        except Exception as e:
            return f"LLM-based Trend analysis (Claude) unavailable: {str(e)}"


# State Management - Simplified (Unchanged)
class StateManager:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, user_idea: str) -> str:
        session_id = str(uuid.uuid4())[:8]
        self.sessions[session_id] = AnalysisState(
            session_id=session_id,
            user_idea=user_idea
        )
        return session_id
    
    def get_session(self, session_id: str) -> Optional[AnalysisState]:
        return self.sessions.get(session_id)
    
    def update_layer(self, session_id: str, layer: int, data: Dict, insights: List[str], confidence: float):
        if session_id in self.sessions:
            self.sessions[session_id].layers[layer] = LayerData(
                status="completed",
                data=data,
                insights=insights,
                confidence=confidence,
                last_updated=datetime.now(timezone.utc).isoformat() # Use timezone aware
            )
            self._update_overall_confidence(session_id)
    
    def _update_overall_confidence(self, session_id: str):
        session = self.sessions[session_id]
        completed_layers = [l for l in session.layers.values() if l.status == "completed"]
        if completed_layers:
            session.overall_confidence = sum(l.confidence for l in completed_layers) / len(completed_layers)

# Agent Creation - Adapted for Claude
def create_agents():
    # LiteLLM (used by CrewAI) will pick up ANTHROPIC_API_KEY from environment variables
    # So, no need to pass api_key directly to LLM object if env var is set.
    claude_llm = LLM(
        model=Config.MODEL_NAME, # This should be the Claude model name, e.g., "claude-3-haiku-20240307"
                                   # LiteLLM prefixes like "anthropic/" might also work, e.g. "anthropic/claude-3-haiku-20240307"
                                   # Check LiteLLM documentation for exact model string if direct name doesn't work.
        temperature=0.7,
        # api_base=None, # Not needed for standard Anthropic
        # max_tokens=2000, # Can be set here if needed, otherwise agent/task might control
    )
    
    serper_search_tool = SerperSearchTool()
    llm_market_tool = MarketResearchTool()
    llm_trend_tool = TrendAnalysisTool()
    
    strategist = Agent(
        role='Business Strategist',
        goal='Analyze business opportunities, strategy, and business models for new ideas. Leverage real-time internet search for current data and LLM synthesis for broader concepts.',
        backstory='Expert strategist with deep business analysis experience, adept at combining real-time data with strategic foresight using Claude LLM.',
        verbose=False,
        tools=[llm_trend_tool, llm_market_tool, serper_search_tool],
        llm=claude_llm, # Using Claude LLM
        allow_delegation=False
    )
    
    analyst = Agent(
        role='Market Analyst', 
        goal='Research markets, validate opportunities, and analyze competition. Prioritize real-time internet search for factual data and competitor information, using Claude LLM for synthesis.',
        backstory='Senior analyst specializing in market research and validation, skilled in using web search for up-to-date insights and Claude LLM for analysis.',
        verbose=False,
        tools=[llm_market_tool, serper_search_tool],
        llm=claude_llm, # Using Claude LLM
        allow_delegation=False
    )
    
    return strategist, analyst

# Core Analysis System
class IdeaEvaluationSystem:
    def __init__(self):
        self.state_manager = StateManager()
        # Check for Anthropic key now
        if Config.ANTHROPIC_API_KEY and Config.ANTHROPIC_API_KEY != 'your-anthropic-api-key-here':
            self.strategist, self.analyst = create_agents()
        else:
            print("Critical: Agents not created due to missing ANTHROPIC_API_KEY. System will not function correctly.")
            self.strategist, self.analyst = None, None
        
    def start_analysis(self, user_idea: str) -> str:
        if not self.strategist or not self.analyst:
             return "Error: System not initialized properly due to missing API keys. Cannot start analysis."
        session_id = self.state_manager.create_session(user_idea)
        print(f"🚀 Starting analysis (Claude Engine): '{user_idea[:50]}...'") # Indicate Claude
        print(f"📋 Session: {session_id}")
        return session_id
    
    def analyze_layer(self, session_id: str, layer: int, user_input: str = "") -> Dict[str, Any]:
        if not self.strategist or not self.analyst:
             return {"error": "System not initialized properly. Agents are not available."}

        session = self.state_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        session.current_layer = layer
        session.layers[layer].status = "in_progress"
        
        layer_methods = {
            1: self._analyze_vision,
            2: self._analyze_strategy, 
            3: self._analyze_market,
            4: self._analyze_competition,
            5: self._analyze_business_model
        }
        
        if layer in layer_methods:
            return layer_methods[layer](session, user_input)
        else:
            session.layers[layer].status = "failed"
            return {"error": f"Layer {layer} not implemented"}

    # Layer analysis methods (_analyze_vision, _analyze_strategy, etc.)
    # The prompts inside these tasks are generally LLM-agnostic enough to work with Claude.
    # No direct changes needed in the task descriptions themselves unless specific Claude prompting techniques are desired.
    
    def _analyze_vision(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        task = Task(
            description=f"""
            Analyze the philosophical foundation and strategic vision for the user's idea: "{session.user_idea}"
            Additional context from user: "{user_input}"
            
            LAYER 1 - PHILOSOPHICAL & VISION (Highest Abstraction):
            1. What fundamental human need or desire are you addressing? (Jobs-to-be-Done analysis)
            2. What massive shifts (technological, social, economic) will reshape the world and support this idea? (Use internet_search for recent macro trends)
            3. Are you creating new market categories (Blue Ocean) or competing in existing ones (Red Ocean)?
            4. Which horizon of growth does this occupy: Core optimization, emerging opportunities, or transformational bets?
            
            LAYER 2 - STRATEGIC POSITIONING (High Abstraction):
            5. Are you building a standalone product or an ecosystem/platform others can build upon?
            6. Could this disrupt existing markets by serving overlooked segments first? (Disruption Theory)
            7. How does value flow in this ecosystem and can you reconfigure it? (Value Network Analysis)
            8. Is the market timing favorable for this solution now?
            
            Provide actionable insights and rate your confidence in this vision on a scale of 0.0 to 1.0 (e.g., "Confidence: 0.8").
            Clearly state if you used the 'internet_search' tool for any specific findings.
            """,
            agent=self.strategist,
            expected_output="A comprehensive analysis covering philosophical foundation (JTBD, macro trends, blue/red ocean, growth horizon) and strategic positioning (platform vs product, disruption potential, value network, market timing). Include actionable insights and confidence rating (e.g., Confidence: 0.X). Mention if internet search was used."
        )
        return self._execute_analysis(session, 1, task, "Vision & Strategic Positioning")
    
    def _analyze_strategy(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 1)
        task = Task(
            description=f"""
            Based on the user's idea: "{session.user_idea}" and previous analysis:
            {context}
            User input for this layer: "{user_input}"
            
            LAYER 3 - MARKET VALIDATION (Medium-High Abstraction):
            1. Is this solving an urgent problem (Painkiller) or providing incremental improvement (Vitamin)?
            2. Which customer segment are you targeting and what does adoption look like? (Crossing the Chasm)
            3. Define your Ideal Customer Profile (ICP) - who exactly is your target customer?
            4. Which features are basic expectations vs delighters? (Kano Model analysis)
            
            Use internet_search if needed to find supporting data about customer segments and market readiness.
            
            Provide actionable insights and rate your confidence (0-1 scale, e.g., "Confidence: 0.7").
            Clearly state if you used the 'internet_search' tool.
            """,
            agent=self.strategist,
            expected_output="Market validation analysis focusing on problem urgency (vitamin vs painkiller), target customer segments, ICP definition, and feature prioritization (Kano model). Include insights and confidence rating (e.g., Confidence: 0.X). Mention if internet search was used."
        )
        return self._execute_analysis(session, 2, task, "Market Validation & Customer Analysis")
    
    def _analyze_market(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 2)
        task = Task(
            description=f"""
            For the idea: "{session.user_idea}", considering previous analysis:
            {context}
            User input for this layer: "{user_input}"
            
            LAYER 4 - COMPETITIVE & DIFFERENTIATION (Medium Abstraction):
            You MUST use the 'internet_search' tool to analyze the competitive landscape:
            
            1. Identify 2-3 key direct and indirect competitors and their market positioning
            2. What unique resources or capabilities give you competitive advantage? (Resource-Based View)
            3. What prevents easy replication of your solution? (Competitive Moat & Defensibility)
            4. Are you (the founder/team) uniquely positioned to execute this? (Founder-Market Fit)
            5. What does it cost customers to switch to your solution vs alternatives? (Switching Cost Analysis)
            6. What opportunities exist for differentiation against these competitors?
            
            Provide actionable insights, cite sources or search queries used, and rate confidence (0-1 scale, e.g., "Confidence: 0.9").
            """,
            agent=self.analyst,
            expected_output="Competitive and differentiation analysis including key competitors (found via search), unique advantages (RBV), competitive moats, founder-market fit assessment, switching costs, and differentiation opportunities. Include insights and confidence rating (e.g., Confidence: 0.X)."
        )
        return self._execute_analysis(session, 3, task, "Competitive Analysis & Differentiation")
    
    def _analyze_competition(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 3)
        task = Task(
            description=f"""
            For the idea: "{session.user_idea}", considering previous analysis:
            {context}
            User input for this layer: "{user_input}"
            
            LAYER 5 - BUSINESS MODEL VIABILITY (Medium-Low Abstraction):
            Analyze the economic and operational feasibility:
            
            1. Suggest 1-2 viable revenue models and assess their scalability architecture
            2. What are the key unit economics: CAC, LTV, churn rates, path to profitability? 
            3. How much economic value do you create vs capture? (Economic Value Added analysis)
            4. Map out the Business Model Canvas: Revenue streams, cost structure, key partnerships
            5. What are the critical success metrics to track? (Use internet_search if specific industry metrics are relevant)
            
            LAYER 6 - TECHNICAL & EXECUTION (Low Abstraction):
            6. Assess technical feasibility vs market risk - Can it be built? Will people want it?
            7. What regulatory and compliance hurdles exist?
            8. Analyze the User/Buyer dynamic - Who uses vs who pays? What's the decision-making process?
            9. Outline go-to-market strategy: Specific channels, pricing, positioning
            
            Provide actionable insights and rate confidence (0-1 scale, e.g., "Confidence: 0.6").
            Clearly state if you used the 'internet_search' tool.
            """,
            agent=self.analyst,
            expected_output="Combined business model and execution analysis covering revenue models, unit economics, value creation/capture, business model canvas, technical feasibility, regulatory considerations, user/buyer dynamics, and GTM strategy. Include insights and confidence rating (e.g., Confidence: 0.X)."
        )
        return self._execute_analysis(session, 4, task, "Business Model & Execution Strategy")
    
    def _analyze_business_model(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 4)
        task = Task(
            description=f"""
            For the idea: "{session.user_idea}", considering previous analysis:
            {context}
            User input for this layer: "{user_input}"
            
            LAYER 7 - VALIDATION & METRICS (Lowest Abstraction):
            Create a concrete testing and measurement framework:
            
            1. Design specific Build-Measure-Learn loops: What hypotheses need testing and what experiments will you run?
            2. Define exact Key Performance Indicators (KPIs) that indicate success at each stage
            3. Outline the Minimum Viable Product (MVP): What's the smallest testable version?
            4. Create a customer development plan: Specific interview questions and validation criteria
            5. Establish validation gates: What metrics/feedback will indicate go/no-go decisions?
            6. Timeline and resource requirements for validation phases
            
            Use internet_search if needed to find industry-specific validation approaches or benchmarks.
            
            Provide actionable validation roadmap and rate confidence (0-1 scale, e.g., "Confidence: 0.8").
            Clearly state if you used the 'internet_search' tool.
            """,
            agent=self.strategist,
            expected_output="Comprehensive validation framework including build-measure-learn loops, specific KPIs, MVP definition, customer development plan, validation gates, and implementation timeline. Include actionable roadmap and confidence rating (e.g., Confidence: 0.X). Mention if internet search was used."
        )
        return self._execute_analysis(session, 5, task, "Validation & Metrics Framework")
    
    # _execute_analysis - Adapted retry logic for CrewAI calls to Claude
    def _execute_analysis(self, session: AnalysisState, layer: int, task: Task, layer_name: str) -> Dict[str, Any]:
        max_crew_retries = 2 
        # Adjust delay for Claude models. Haiku is fast, Sonnet/Opus might need more.
        # This is a general delay, tool-specific retries are handled by generate_with_retry_claude
        default_retry_delay_seconds = 15 # A general starting point
        if 'haiku' in Config.MODEL_NAME.lower():
            default_retry_delay_seconds = 10
        elif 'opus' in Config.MODEL_NAME.lower():
            default_retry_delay_seconds = 20


        for attempt in range(max_crew_retries):
            try:
                if not task.agent:
                    error_msg = f"Agent for task '{task.description[:50]}...' is None. Cannot execute."
                    print(f"❌ {error_msg}")
                    session.layers[layer].status = "failed"
                    return { "layer": layer, "layer_name": layer_name, "error": error_msg, "status": "failed" }

                crew = Crew(
                    agents=[task.agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False 
                )
                
                print(f"🔍 Analyzing {layer_name} with Claude (Crew Kickoff Attempt {attempt + 1}/{max_crew_retries})...")
                output = crew.kickoff()
                
                analysis_text = ""
                if isinstance(output, str): analysis_text = output
                elif hasattr(output, 'raw_output') and output.raw_output: analysis_text = output.raw_output
                elif hasattr(output, 'result') and output.result: analysis_text = output.result
                elif hasattr(output, 'raw') and output.raw: analysis_text = output.raw
                else: analysis_text = str(output)

                if not analysis_text or analysis_text.strip() == "":
                    print(f"⚠️ Warning: CrewAI kickoff for {layer_name} (Claude) returned empty. Output: '{output}'")
                    analysis_text = "No substantive analysis was generated by the Claude agent."

                insights = self._extract_insights(analysis_text)
                confidence = self._extract_confidence(analysis_text)
                questions = self._extract_questions(analysis_text)
                
                self.state_manager.update_layer(
                    session.session_id, layer,
                    {"analysis": analysis_text, "layer_name": layer_name},
                    insights, confidence
                )
                
                return {
                    "layer": layer, "layer_name": layer_name, "analysis": analysis_text,
                    "insights": insights, "confidence": confidence, "questions": questions, "status": "completed"
                }
            
            except Exception as e: # Catching exceptions from CrewAI kickoff (often LLM related)
                error_str = str(e).lower()
                is_rate_limit = "rate_limit_error" in error_str or \
                                "ratelimiterror" in e.__class__.__name__.lower() or \
                                "429" in error_str or \
                                "throttled" in error_str # Common for Anthropic via LiteLLM

                if not is_rate_limit and hasattr(e, '__cause__') and e.__cause__:
                    cause_str = str(e.__cause__).lower()
                    is_rate_limit = is_rate_limit or \
                                   "rate_limit_error" in cause_str or \
                                   "ratelimiterror" in e.__cause__.__class__.__name__.lower() or \
                                   "429" in cause_str or "throttled" in cause_str

                if is_rate_limit:
                    print(f"❌ Rate limit encountered during CrewAI (Claude) execution for {layer_name}.")
                    if attempt < max_crew_retries - 1:
                        current_sleep_duration = int(default_retry_delay_seconds * (1.5 ** attempt))
                        # Anthropic errors via LiteLLM might not have a "retry-after" header easily accessible here
                        # So, we rely on exponential backoff.
                        print(f"Using exponential backoff: {current_sleep_duration}s.")
                        print(f"Retrying {layer_name} in {current_sleep_duration} seconds... (Next attempt: {attempt + 2}/{max_crew_retries})")
                        time.sleep(current_sleep_duration)
                    else:
                        final_error_msg = f"Failed {layer_name} analysis with Claude after {max_crew_retries} attempts due to persistent rate limits. Last error: {str(e)}"
                        print(f"❌ {final_error_msg}")
                        session.layers[layer].status = "rate_limited"
                        return {
                            "layer": layer, "layer_name": layer_name, "error": final_error_msg,
                            "retry_suggestion": f"Wait significantly longer (e.g., 5-10 minutes or check Anthropic API quota dashboard) and try analyzing this layer again.",
                            "status": "rate_limited"
                        }
                else:
                    detailed_error = f"Non-rate-limit error in {layer_name} with Claude (Attempt {attempt + 1}): {str(e)}"
                    # import traceback; traceback.print_exc() # For debugging
                    print(f"❌ {detailed_error}")
                    if attempt == max_crew_retries - 1:
                        session.layers[layer].status = "failed"
                        return {"layer": layer, "layer_name": layer_name, "error": detailed_error, "status": "failed"}
                    # Optionally, retry for some non-rate-limit errors too with a short delay
                    # time.sleep(5) 

        session.layers[layer].status = "failed"
        return {
            "layer": layer, "layer_name": layer_name,
            "error": "Exited analysis execution loop (Claude) unexpectedly after all retries.", "status": "failed"
        }

    # _get_layer_context, _extract_insights, _extract_confidence, _extract_questions remain the same
    # as they operate on the text output, which should be structurally similar.
    def _get_layer_context(self, session: AnalysisState, up_to_layer: int) -> str:
        context = []
        for i in range(1, up_to_layer): 
            if session.layers[i].status == "completed" and session.layers[i].data:
                analysis = session.layers[i].data.get("analysis", "")
                layer_name_from_data = session.layers[i].data.get("layer_name", f"Layer {i}")
                insights_text = "; ".join(session.layers[i].insights) if session.layers[i].insights else "N/A"
                context.append(f"Summary from {layer_name_from_data}: Confidence {session.layers[i].confidence:.2f}. Key Insights: {insights_text}. Analysis snippet: {analysis[:150]}...")
            elif session.layers[i].status != "pending":
                 context.append(f"Note: Layer {i} ({session.layers[i].data.get('layer_name', 'Unknown') if session.layers[i].data else 'Unknown'}) was not successfully completed (status: {session.layers[i].status}).")
        return "\n".join(context) if context else "No prior completed layer context available."

    def _extract_insights(self, text: str) -> List[str]:
        lines = text.split('\n')
        insights = []
        for line in lines:
            line = line.strip()
            if re.match(r'^[•*-]\s+|^[1-9][\.\)]\s+', line) and '?' not in line:
                processed_line = re.sub(r'^(insight|key takeaway|important|actionable insight|finding)\s*[:\-•*]*\s*', '', line, flags=re.IGNORECASE)
                processed_line = re.sub(r'^[•*\-1-9][\.\)]?\s*', '', processed_line).strip()
                if len(processed_line) > 20 and len(processed_line) < 300: insights.append(processed_line)
            elif any(marker in line.lower() for marker in ["key insight:", "conclusion:", "finding:"]) and len(line) > 30:
                processed_line = re.sub(r'^(key insight:|conclusion:|finding:)\s*', '', line, flags=re.IGNORECASE).strip()
                if len(processed_line) > 20 and len(processed_line) < 300: insights.append(processed_line)
        if not insights and "summary:" in text.lower():
            summary_section = text.lower().split("summary:", 1)[-1]
            sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', summary_section)
            for sentence in sentences:
                sentence = sentence.strip()
                if len(sentence) > 20 and len(sentence) < 200 and '?' not in sentence: insights.append(sentence.capitalize())
        unique_insights = list(dict.fromkeys(insights))
        return unique_insights[:5]
    
    def _extract_confidence(self, text: str) -> float:
        text_lower = text.lower()
        explicit_confidence_match = re.search(r'confidence[:\s]*([0-1]?\.[0-9]+|[0-1])', text_lower)
        if explicit_confidence_match:
            try: return float(explicit_confidence_match.group(1))
            except ValueError: pass
        rating_patterns = [r'rating[:\s]*([0-1]?\.[0-9]+|[0-1])', r'score[:\s]*([0-1]?\.[0-9]+|[0-1])', r'confidence level[:\s]*([0-1]?\.[0-9]+|[0-1])']
        for pattern in rating_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    value = float(matches[-1])
                    return min(max(value, 0.0), 1.0)
                except ValueError: continue
        high_confidence_keywords = ['very confident', 'high confidence', 'strong case', 'highly likely', 'excellent prospect']
        medium_confidence_keywords = ['moderately confident', 'medium confidence', 'promising', 'likely', 'good chance']
        low_confidence_keywords = ['low confidence', 'uncertain', 'risky', 'challenging', 'unlikely', 'significant hurdles']
        if any(kw in text_lower for kw in high_confidence_keywords): return 0.85
        if any(kw in text_lower for kw in medium_confidence_keywords): return 0.65
        if any(kw in text_lower for kw in low_confidence_keywords): return 0.35
        return 0.5
    
    def _extract_questions(self, text: str) -> List[str]:
        question_matches = re.findall(r'([A-Z][^.?!]*\?)', text)
        questions = []
        for q_match in question_matches:
            q_clean = q_match.strip()
            if len(q_clean) > 15 and len(q_clean) < 250:
                q_clean = re.sub(r'^[•*-]\s*|^[1-9][\.\)]\s*', '', q_clean).strip()
                q_clean = re.sub(r'^(Question:|Further research needed on)\s*', '', q_clean, flags=re.IGNORECASE).strip()
                questions.append(q_clean)
        unique_questions = list(dict.fromkeys(questions))
        return unique_questions[:3]
    
    def get_summary(self, session_id: str) -> Dict[str, Any]:
        session = self.state_manager.get_session(session_id)
        if not session: return {"error": "Session not found"}
        completed_layers_data = { i: asdict(layer) for i, layer in session.layers.items() if layer.status == "completed" and layer.data }
        return {
            "session_id": session_id, "idea": session.user_idea, "overall_confidence": session.overall_confidence,
            "completed_layers_count": len(completed_layers_data), "total_layers": 5,
            "completion_percentage": (len(completed_layers_data) / 5) * 100,
            "layer_details": completed_layers_data, "summary_text": self._generate_summary_text(session)
        }
    
    def _generate_summary_text(self, session: AnalysisState) -> str:
        completed = [layer for layer_id, layer in sorted(session.layers.items()) if layer.status == "completed" and layer.data]
        if not completed: return "No analysis completed yet."
        summary_parts = [f"Analysis Summary for: {session.user_idea}\n"]
        confidence = session.overall_confidence
        confidence_text = "High" if confidence > 0.7 else "Medium" if confidence > 0.5 else "Low"
        summary_parts.append(f"Overall Confidence: {confidence_text} ({confidence:.2f})")
        summary_parts.append(f"Completed Layers: {len(completed)}/5\n")
        summary_parts.append("Key Insights per Layer:")
        for i, layer_data in enumerate(completed):
            layer_num = [k for k, v in session.layers.items() if v == layer_data][0]
            layer_name = layer_data.data.get('layer_name', f'Layer {layer_num}')
            summary_parts.append(f"\n--- {layer_name} (Confidence: {layer_data.confidence:.2f}) ---")
            if layer_data.insights:
                for insight in layer_data.insights: summary_parts.append(f"• {insight}")
            else: summary_parts.append("No specific insights extracted for this layer.")
        return "\n".join(summary_parts)

# Main Interface - IdeaEvaluator
class IdeaEvaluator:
    def __init__(self):
        self.system = IdeaEvaluationSystem()
        self.current_session_id = None
    
    def start(self, idea: str) -> str:
        # Check for Anthropic key now
        if not Config.ANTHROPIC_API_KEY or Config.ANTHROPIC_API_KEY == 'your-anthropic-api-key-here':
            return "🔴 Error: ANTHROPIC_API_KEY is not configured. Please set it as an environment variable."
        if not Config.SERPER_API_KEY or Config.SERPER_API_KEY == 'your-serper-api-key-here':
            print("🟡 Warning: SERPER_API_KEY is not configured. Internet search capabilities will be disabled.")

        start_message = self.system.start_analysis(idea)
        if "Error" in start_message:
            return f"🔴 {start_message}"
        # Correctly get session_id (assuming start_analysis returns it directly or from state_manager)
        # The previous way of getting session_id was a bit convoluted; assuming start_analysis returns the ID or it's easy to get.
        # For simplicity, let's assume the session ID is the last one added if start_analysis doesn't return it.
        if self.system.state_manager.sessions:
             # Get the session ID from the AnalysisState object after it's created
            self.current_session_id = list(self.system.state_manager.sessions.values())[-1].session_id
        else: # Should not happen if start_analysis was successful
            return "🔴 Error: Session ID could not be determined after starting analysis."

        return f"✅ Started analysis with Claude! Session ID: {self.current_session_id}"
    
    def analyze(self, layer: int = None, user_input: str = "") -> Dict[str, Any]:
        if not self.current_session_id:
            return {"error": "Start analysis first with start(idea)"}
        
        session = self.system.state_manager.get_session(self.current_session_id)
        if not session:
             return {"error": f"Session {self.current_session_id} not found unexpectedly."}

        if layer is None: 
            results = {}
            # Adjust delay based on Claude model type. Haiku can be faster.
            INTER_LAYER_DELAY_SECONDS = 15 # General default
            if 'haiku' in Config.MODEL_NAME.lower():
                INTER_LAYER_DELAY_SECONDS = 8
            elif 'opus' in Config.MODEL_NAME.lower(): # Opus might need more breathing room
                INTER_LAYER_DELAY_SECONDS = 25
            elif 'sonnet' in Config.MODEL_NAME.lower():
                 INTER_LAYER_DELAY_SECONDS = 15


            print(f"ℹ️ Using inter-layer delay of {INTER_LAYER_DELAY_SECONDS}s for Claude model {Config.MODEL_NAME}")

            for i in range(1, 6):
                current_layer_state = session.layers[i]
                layer_name_for_log = current_layer_state.data.get('layer_name', f'Layer {i}') if current_layer_state.data else f'Layer {i}'

                if current_layer_state.status == "completed":
                    print(f"⏭️ Layer {i} ({layer_name_for_log}) already completed. Skipping.")
                    results[i] = {"status": "skipped_completed", "layer": i, "data": asdict(current_layer_state)}
                    continue
                
                if i > 1:
                    prev_layer_state = session.layers[i-1]
                    if prev_layer_state.status not in ["completed", "skipped_completed"]:
                        print(f"⚠️ Previous layer {i-1} status is '{prev_layer_state.status}'. Stopping sequential analysis at Layer {i}.")
                        results[i] = {"status": "skipped_previous_issue", "layer": i, "reason": f"Previous layer {i-1} status: {prev_layer_state.status}"}
                        break 

                print(f"\n--- Processing Layer {i} ({layer_name_for_log if layer_name_for_log != f'Layer {i}' else ''}) with Claude ---")
                current_user_input_for_layer = user_input if i == (session.current_layer if session.current_layer > 0 else 1) else ""
                result = self.system.analyze_layer(self.current_session_id, i, current_user_input_for_layer)
                results[i] = result
                
                if result.get("layer_name") and not results[i].get("layer_name"):
                    results[i]["layer_name"] = result.get("layer_name")

                if result.get("status") == "rate_limited":
                    print(f"⏰ Layer {i} ({result.get('layer_name', '')}) with Claude hit rate limit, and retries were exhausted. Analysis paused.")
                    print(f"Suggestion: {result.get('retry_suggestion', 'Wait and try again.')}")
                    break 
                    
                if result.get("status") == "failed":
                    print(f"❌ Layer {i} ({result.get('layer_name', '')}) with Claude failed. Analysis paused. Error: {result.get('error')}")
                    break
                    
                if i < 5 and result.get("status") == "completed":
                    print(f"✅ Layer {i} ({result.get('layer_name', '')}) with Claude completed. Waiting {INTER_LAYER_DELAY_SECONDS} seconds before next layer...")
                    time.sleep(INTER_LAYER_DELAY_SECONDS)
            
            print("\n--- Full Sequential Analysis Attempt with Claude Completed ---")
            final_summary = self.summary()
            print("📊 Final Summary after sequential Claude run:")
            print(json.dumps(final_summary, indent=2))
            return {"all_layer_results": results, "final_summary": final_summary}
        else: 
            return self.system.analyze_layer(self.current_session_id, layer, user_input)
    
    def summary(self) -> Dict[str, Any]:
        if not self.current_session_id: return {"error": "No active session. Start an analysis first."}
        return self.system.get_summary(self.current_session_id)
    
    def status(self) -> Dict[str, Any]:
        if not self.current_session_id: return {"error": "No active session. Start an analysis first."}
        session = self.system.state_manager.get_session(self.current_session_id)
        if not session: return {"error": f"Session {self.current_session_id} not found, though an ID exists."}
        layer_statuses_with_names = {}
        for i, l_data in session.layers.items():
            name = "N/A"
            if l_data.data and l_data.data.get("layer_name"): name = l_data.data.get("layer_name")
            elif l_data.data and l_data.data.get("analysis"): name = f"Layer {i} (Details in analysis)"
            else: name = f"Layer {i}"
            layer_statuses_with_names[f"{i} - {name}"] = l_data.status
        return {
            "session_id": self.current_session_id, "idea": session.user_idea,
            "current_layer_processed_or_active": session.current_layer,
            "overall_confidence": f"{session.overall_confidence:.2f}",
            "layers_status": layer_statuses_with_names,
            "completed_layers_count": sum(1 for l in session.layers.values() if l.status == "completed")
        }

# Demo functions (demo and run_full_analysis_demo)
# Need to update API key checks and print messages to reflect Claude.

def demo_claude_partial(): # Renamed original demo
    print("🤖 Idea Evaluation System - Claude Partial Demo (Layers 1-3)")
    print("==========================================================")
    
    if not Config.ANTHROPIC_API_KEY or Config.ANTHROPIC_API_KEY == 'your-anthropic-api-key-here':
        print("🔴 Critical: ANTHROPIC_API_KEY is not set. Demo cannot run.")
        return
    # ... (Serper key check as before)

    evaluator = IdeaEvaluator()
    idea = "A personalized audiobook recommendation service powered by Claude AI, focusing on niche genres and independent authors."
    print(f"💡 Testing Idea with Claude: {idea}")

    start_message = evaluator.start(idea)
    print(start_message)
    if "Error" in start_message or not evaluator.current_session_id:
        print("Stopping demo due to initialization error.")
        return

    # Delays might need tuning for Claude
    delay = 15
    if 'haiku' in Config.MODEL_NAME.lower(): delay = 8
    elif 'opus' in Config.MODEL_NAME.lower(): delay = 25
    
    print("\n🔍 Analyzing Vision Layer (Layer 1) with Claude...")
    result_layer1 = evaluator.analyze(layer=1, user_input="Focus on user privacy and data ethics.")
    print(json.dumps(result_layer1, indent=2))
    if result_layer1.get("status") != "completed": # ... (error handling)
        print(f"Stopping demo due to issue in Layer 1: {result_layer1.get('error', 'Unknown error')}")
        return
    
    print(f"\n⏱️ Waiting {delay} seconds before next layer...")
    time.sleep(delay)

    print("\n🔍 Analyzing Strategy Layer (Layer 2) with Claude...")
    result_layer2 = evaluator.analyze(layer=2, user_input="Consider a freemium model with premium features.")
    print(json.dumps(result_layer2, indent=2))
    if result_layer2.get("status") != "completed": # ... (error handling)
        print(f"Stopping demo due to issue in Layer 2: {result_layer2.get('error', 'Unknown error')}")
        return
        
    print(f"\n⏱️ Waiting {delay} seconds before next layer...")
    time.sleep(delay)

    print("\n🔍 Analyzing Market Validation Layer (Layer 3) with Claude...")
    result_layer3 = evaluator.analyze(layer=3, user_input="Target avid readers who prefer audio content and discoverability of new authors.")
    print(json.dumps(result_layer3, indent=2))
    # ... (error handling)

    print("\n📊 Final Status (after partial Claude run):") # ... (status and summary prints)
    print(json.dumps(evaluator.status(), indent=2))
    print("\n📋 Final Summary (after partial Claude run):")
    print(json.dumps(evaluator.summary(), indent=2))
    
    return evaluator

def run_full_analysis_claude_demo(idea,initial_user_input):
    """
    Runs a demo that attempts to analyze an idea through all 5 layers sequentially
    using the Anthropic Claude LLM.
    """
    print("🤖 Idea Evaluation System - Claude Full Sequential Analysis Demo")
    print("================================================================")

    # 1. API Key Checks (Essential for Claude and Serper)
    if not Config.ANTHROPIC_API_KEY or Config.ANTHROPIC_API_KEY == 'your-anthropic-api-key-here':
        print("🔴 Critical: ANTHROPIC_API_KEY is not set. Demo cannot run.")
        print("Please set it as an environment variable (e.g., export ANTHROPIC_API_KEY='your_key').")
        return None # Return None to indicate failure
    if not Config.SERPER_API_KEY or Config.SERPER_API_KEY == 'your-serper-api-key-here':
        print("🟡 Warning: SERPER_API_KEY is not set. Internet search will not work fully.")
        print("Please set it as an environment variable for full functionality.")

    # 2. Create the IdeaEvaluator instance (now configured for Claude)
    evaluator = IdeaEvaluator()

    # 3. Define the single idea to be analyzed
    # You can change this idea to test with different concepts
    # idea = "A Gen AI application that automates startup idea validation by performing real-time market research, competitive analysis, and generating a preliminary business strategy report for entrepreneurs."
    print(f"💡 Testing Idea for Full Analysis with Claude: {idea}")

    # 4. Start the analysis session for the idea
    start_message = evaluator.start(idea)
    print(start_message)
    if "Error" in start_message or not evaluator.current_session_id:
        print("Stopping demo due to initialization error (e.g., session ID not created).")
        return None # Return None to indicate failure

    # 5. Inform the user and set up any initial input for the first layer
    print(f"\n🔍 Analyzing all 5 layers sequentially with Claude for idea: '{idea[:60]}...'")
    print("This may take several minutes depending on the Claude model and API rate limits.")
    print(f"The system uses an inter-layer delay (currently around {evaluator.system._execute_analysis.__defaults__[1] if evaluator.system._execute_analysis.__defaults__ else '10-20'}s, adjusted by model) to help manage API usage.") # A bit of introspection to show the delay

    # The `user_input` here will be passed to the first layer when sequential analysis starts.
    # initial_user_input = "The core problem this solves is the high failure rate of startups due to unvalidated ideas and lack of strategic direction. Focus the opportunity analysis on the market of aspiring and early-stage entrepreneurs seeking quick, affordable, and data-driven feedback before committing significant resources. Consider current trends in AI adoption by small businesses."
    if initial_user_input:
        print(f"ℹ️ Using initial user input for Layer 1: '{initial_user_input}'")
    
    # 6. Call analyze() without a specific layer to run all layers sequentially
    # This is the core of processing the single idea through all layers.
    # The `evaluator.analyze()` method handles the layer-by-layer progression internally.
    full_analysis_results = evaluator.analyze(user_input=initial_user_input)

    # 7. Summarize the results of the sequential analysis attempt
    print("\n--- Summary of Full Sequential Claude Analysis Attempt ---")
    if full_analysis_results and "all_layer_results" in full_analysis_results:
        print("Status of each layer after sequential run with Claude:")
        for layer_num_key in sorted(full_analysis_results["all_layer_results"].keys()): # Ensure ordered printing
            result = full_analysis_results["all_layer_results"][layer_num_key]
            layer_num_actual = result.get("layer", layer_num_key)
            layer_name = result.get("layer_name", f"Layer {layer_num_actual}")
            status = result.get("status", "unknown")
            
            print(f"\n  Layer {layer_num_actual} ({layer_name}) - Status: {status.upper()}")
            if status == "completed":
                print(f"    Confidence: {result.get('confidence', 'N/A')}")
                # Example: print first 100 chars of analysis
                # analysis_snippet = result.get('analysis', '')[:100]
                # if analysis_snippet: print(f"    Analysis Snippet: {analysis_snippet}...")
            elif status == "skipped_completed":
                print("    This layer was already completed and skipped during the sequential run.")
            elif status == "skipped_previous_issue":
                print(f"    Skipped because a previous layer ({result.get('reason', '')}) did not complete successfully.")
            elif status == "rate_limited":
                print(f"    Error: {result.get('error')}")
                print(f"    Suggestion: {result.get('retry_suggestion')}")
            elif status == "failed":
                print(f"    Error: {result.get('error')}")
            else: # For any other status
                print(f"    Details: {json.dumps(result, indent=2)}")
    elif full_analysis_results and "error" in full_analysis_results:
         print(f"🔴 An error occurred during the setup for sequential analysis with Claude: {full_analysis_results['error']}")
    else:
        print("Full analysis (Claude) did not produce the expected 'all_layer_results' structure.")
        print(f"Raw output from evaluator.analyze(): {json.dumps(full_analysis_results, indent=2)}")

    # 8. Print the overall system status and summary at the end
    print("\n📊 Current System Status (after full Claude run attempt):")
    status_info = evaluator.status()
    print(json.dumps(status_info, indent=2))

    print("\n📋 Current System Summary (after full Claude run attempt):")
    summary_info = evaluator.summary()
    print(json.dumps(summary_info, indent=2))
    
    print("\n✅ Full Sequential Claude Analysis Demo Finished.")
    return evaluator # Return the evaluator instance for potential further inspection

if __name__ == "__main__":
    print("🚀 Idea Evaluator - Now with Anthropic Claude & Serper Search 🚀")
    print("Ensure ANTHROPIC_API_KEY (and SERPER_API_KEY) environment variables are set.")
    print(f"Using Claude Model: {Config.MODEL_NAME}")
    print("-" * 60)

    # --- CHOOSE WHICH CLAUDE DEMO TO RUN ---
    # Option 1: Partial demo (first 3 layers)
    # print("\nStarting Claude Partial Demo...")
    # demo_claude_partial()
    # print("\nClaude Partial Demo Finished.")
    # print("-" * 60)
    idea = "A Gen AI application that automates startup idea validation by performing real-time market research, competitive analysis, and generating a preliminary business strategy report for entrepreneurs."
    initial_user_input = "The core problem this solves is the high failure rate of startups due to unvalidated ideas and lack of strategic direction. Focus the opportunity analysis on the market of aspiring and early-stage entrepreneurs seeking quick, affordable, and data-driven feedback before committing significant resources. Consider current trends in AI adoption by small businesses."


    # Option 2: Full sequential analysis demo (all 5 layers)
    print("\nStarting Claude Full Sequential Analysis Demo...")
    run_full_analysis_claude_demo(idea=idea, initial_user_input=initial_user_input)
    # print("\nClaude Full Sequential Analysis Demo Finished.")