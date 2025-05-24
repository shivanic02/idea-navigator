    #!/usr/bin/env python3
"""
Idea Evaluation Agentic System - Hackathon MVP
A multi-agent system for comprehensive idea analysis using CrewAI and Google Gemini
"""

import os
import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import google.generativeai as genai
from crewai import Agent, Task, Crew, Process, LLM # Added LLM
from crewai.tools import BaseTool
import time # For delays
import re   # For parsing retryDelay

# Configuration
class Config:
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-gemini-api-key-here')
    # IMPORTANT: 'gemini/gemini-1.5-pro' has VERY STRICT free tier limits (2 RPM).
    # Consider 'gemini/gemini-pro' (60 RPM) for faster free tier execution.
    MODEL_NAME = 'gemini/gemini-1.5-flash'
    CONFIDENCE_THRESHOLD = 0.7

# Initialize Gemini
genai.configure(api_key=Config.GEMINI_API_KEY)

# Set environment variables for CrewAI to use Gemini
os.environ['GOOGLE_API_KEY'] = Config.GEMINI_API_KEY

# Data Models
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
            self.last_updated = datetime.now().isoformat()

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

# Utility function for retrying genai calls (for tools)
def generate_with_retry(model: genai.GenerativeModel, prompt: str, tool_name: str, max_retries: int = 3, default_initial_delay: int = 35) -> str:
    """
    Calls model.generate_content with retry logic for rate limiting.
    Prioritizes retryDelay from error message. default_initial_delay is for gemini-1.5-pro (2 RPM).
    """
    current_delay = default_initial_delay
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            error_str = str(e)
            is_rate_limit_error = (
                "RESOURCE_EXHAUSTED" in error_str or
                "429" in error_str or
                "RateLimitError" in e.__class__.__name__ # Check class name too
            )

            if not is_rate_limit_error and hasattr(e, '__cause__') and e.__cause__: # Check underlying cause
                 cause_str = str(e.__cause__)
                 is_rate_limit_error = is_rate_limit_error or \
                                       "RESOURCE_EXHAUSTED" in cause_str or \
                                       "429" in cause_str or \
                                       "RateLimitError" in e.__cause__.__class__.__name__

            if is_rate_limit_error:
                sleep_duration = current_delay
                retry_delay_match = re.search(r'"retryDelay":\s*"(\d+)s"', error_str)
                if retry_delay_match:
                    api_suggested_delay = int(retry_delay_match.group(1))
                    sleep_duration = max(api_suggested_delay, 15) # Min 15s
                    print(f"Tool '{tool_name}': API suggested retry delay: {api_suggested_delay}s. Will wait {sleep_duration}s.")
                else:
                    # Exponential backoff for our default if no API suggestion
                    current_delay = int(current_delay * 1.5)

                print(f"Tool '{tool_name}': Rate limit hit. Retrying in {sleep_duration}s... (Attempt {attempt + 1}/{max_retries})")
                time.sleep(sleep_duration)

                if attempt == max_retries - 1:
                    final_error_message = f"Tool '{tool_name}': Failed after {max_retries} retries due to rate limiting. Last error: {e}"
                    print(final_error_message)
                    raise Exception(final_error_message) from e # Re-raise to be caught by tool's exception handler
            else:
                # Not a rate limit error, re-raise
                raise e
    # Fallback, should be caught by the raise in the loop
    raise Exception(f"Tool '{tool_name}': Exited retry loop unexpectedly.")


# Custom Tools - Simplified for hackathon
class MarketResearchTool(BaseTool):
    name: str = "market_research"
    description: str = "Research market data and competitive information"
    
    def _run(self, query: str) -> str:
        try:
            model = genai.GenerativeModel(Config.MODEL_NAME)
            prompt = f"""
            Research and analyze: {query}
            
            Provide insights on:
            1. Market trends and data
            2. Key competitors
            3. Market size estimates
            4. Growth opportunities
            
            Keep response concise but insightful.
            """
            return generate_with_retry(model, prompt, self.name)
        except Exception as e:
            return f"Research unavailable after retries: {str(e)}"

class TrendAnalysisTool(BaseTool):
    name: str = "trend_analysis" 
    description: str = "Analyze future trends relevant to the idea"
    
    def _run(self, idea: str) -> str:
        try:
            model = genai.GenerativeModel(Config.MODEL_NAME)
            prompt = f"""
            Analyze future trends for: {idea}
            
            Focus on:
            1. Technology trends
            2. Market shifts
            3. User behavior changes
            4. Opportunities and threats
            
            Provide specific, actionable insights.
            """
            return generate_with_retry(model, prompt, self.name)
        except Exception as e:
            return f"Trend analysis unavailable after retries: {str(e)}"

# State Management - Simplified
class StateManager:
    def __init__(self):
        self.sessions = {}
    
    def create_session(self, user_idea: str) -> str:
        session_id = str(uuid.uuid4())[:8]  # Shorter ID for hackathon
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
                last_updated=datetime.now().isoformat()
            )
            self._update_overall_confidence(session_id)
    
    def _update_overall_confidence(self, session_id: str):
        session = self.sessions[session_id]
        completed_layers = [l for l in session.layers.values() if l.status == "completed"]
        if completed_layers:
            session.overall_confidence = sum(l.confidence for l in completed_layers) / len(completed_layers)

# Agent Creation - Simplified with Gemini LLM
def create_agents():
    gemini_llm = LLM(
        model=Config.MODEL_NAME,
        google_api_key=Config.GEMINI_API_KEY,
        temperature=0.7
        # We can also pass generation_config to litellm via `config_list` for more control if needed
        # e.g., by preparing a custom config_list for litellm.
    )
    
    market_tool = MarketResearchTool()
    trend_tool = TrendAnalysisTool()
    
    strategist = Agent(
        role='Business Strategist',
        goal='Analyze business opportunities and strategy',
        backstory='Expert strategist with deep business analysis experience',
        verbose=False, # Set to True for detailed CrewAI logs
        tools=[trend_tool, market_tool],
        llm=gemini_llm
    )
    
    analyst = Agent(
        role='Market Analyst', 
        goal='Research markets and validate opportunities',
        backstory='Senior analyst specializing in market research and validation',
        verbose=False, # Set to True for detailed CrewAI logs
        tools=[market_tool],
        llm=gemini_llm
    )
    
    return strategist, analyst

# Core Analysis System
class IdeaEvaluationSystem:
    def __init__(self):
        self.state_manager = StateManager()
        self.strategist, self.analyst = create_agents()
        
    def start_analysis(self, user_idea: str) -> str:
        session_id = self.state_manager.create_session(user_idea)
        print(f"🚀 Starting analysis: '{user_idea[:50]}...'")
        print(f"📋 Session: {session_id}")
        return session_id
    
    def analyze_layer(self, session_id: str, layer: int, user_input: str = "") -> Dict[str, Any]:
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
    
    def _analyze_vision(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        task = Task(
            description=f"""
            Analyze the vision and opportunity for: {session.user_idea}
            Additional context: {user_input}
            
            Evaluate:
            1. What problem does this solve?
            2. What trends support this idea?
            3. What's the opportunity size?
            
            Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.8").
            """,
            agent=self.strategist,
            expected_output="Vision analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
        )
        return self._execute_analysis(session, 1, task, "Vision & Opportunity")
    
    def _analyze_strategy(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 1)
        task = Task(
            description=f"""
            Previous analysis: {context}
            
            Analyze strategy for: {session.user_idea}
            User input: {user_input}
            
            Focus on:
            1. Strategic positioning
            2. Market timing
            3. Competitive advantages
            
            Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.7").
            """,
            agent=self.strategist,
            expected_output="Strategic analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
        )
        return self._execute_analysis(session, 2, task, "Strategy & Positioning")
    
    def _analyze_market(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 2)
        task = Task(
            description=f"""
            Previous analysis: {context}
            
            Market validation for: {session.user_idea}
            User input: {user_input}
            
            Research using available tools:
            1. Target customers
            2. Market size
            3. Customer needs validation
            
            Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.9").
            """,
            agent=self.analyst,
            expected_output="Market validation analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
        )
        return self._execute_analysis(session, 3, task, "Market Validation")
    
    def _analyze_competition(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 3)
        task = Task(
            description=f"""
            Previous analysis: {context}
            
            Competitive analysis for: {session.user_idea}
            User input: {user_input}
            
            Analyze:
            1. Direct/indirect competitors
            2. Differentiation opportunities
            3. Competitive advantages
            
            Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.6").
            """,
            agent=self.analyst,
            expected_output="Competitive analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
        )
        return self._execute_analysis(session, 4, task, "Competition Analysis")
    
    def _analyze_business_model(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 4)
        task = Task(
            description=f"""
            Previous analysis: {context}
            
            Business model for: {session.user_idea}
            User input: {user_input}
            
            Evaluate:
            1. Revenue model
            2. Key metrics (CAC, LTV)
            3. Scalability potential
            
            Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.8").
            """,
            agent=self.strategist,
            expected_output="Business model analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
        )
        return self._execute_analysis(session, 5, task, "Business Model")
    
    def _execute_analysis(self, session: AnalysisState, layer: int, task: Task, layer_name: str) -> Dict[str, Any]:
        """Execute analysis task and update state with robust retry logic"""
        max_crew_retries = 3
        default_retry_delay_seconds = 60  # Start with 60s for gemini-1.5-pro due to 2 RPM limit

        for attempt in range(max_crew_retries):
            try:
                crew = Crew(
                    agents=[task.agent],
                    tasks=[task],
                    process=Process.sequential,
                    verbose=False # Set to True for more CrewAI output if needed
                )
                
                print(f"🔍 Analyzing {layer_name} (Attempt {attempt + 1}/{max_crew_retries})...")
                result = crew.kickoff()
                
                analysis_text = str(result.raw) if hasattr(result, 'raw') else str(result)
                insights = self._extract_insights(analysis_text)
                confidence = self._extract_confidence(analysis_text)
                questions = self._extract_questions(analysis_text)
                
                self.state_manager.update_layer(
                    session.session_id, layer,
                    {"analysis": analysis_text},
                    insights, confidence
                )
                
                return {
                    "layer": layer,
                    "layer_name": layer_name,
                    "analysis": analysis_text,
                    "insights": insights,
                    "confidence": confidence,
                    "questions": questions,
                    "status": "completed"
                }
            
            except Exception as e:
                error_str = str(e)
                is_rate_limit = (
                    "RESOURCE_EXHAUSTED" in error_str or 
                    "429" in error_str or
                    "RateLimitError" in e.__class__.__name__ # CrewAI might wrap it
                )
                
                # Check underlying cause if available (e.g., litellm wrapping VertexAIException)
                if not is_rate_limit and hasattr(e, '__cause__') and e.__cause__:
                    cause_str = str(e.__cause__)
                    is_rate_limit = is_rate_limit or \
                                   "RESOURCE_EXHAUSTED" in cause_str or \
                                   "429" in cause_str or \
                                   "RateLimitError" in e.__cause__.__class__.__name__


                if is_rate_limit:
                    print(f"❌ Rate limit encountered during CrewAI execution for {layer_name}.")
                    
                    if attempt < max_crew_retries - 1:
                        current_sleep_duration = default_retry_delay_seconds
                        
                        retry_delay_match = re.search(r'"retryDelay":\s*"(\d+)s"', error_str)
                        if retry_delay_match:
                            api_suggested_delay = int(retry_delay_match.group(1))
                            current_sleep_duration = max(api_suggested_delay, 30) # Use API delay, min 30s
                            print(f"API suggested retry delay: {api_suggested_delay}s. Will wait {current_sleep_duration}s.")
                        else:
                            # If no specific delay from API, slightly increase our default for the next attempt
                            default_retry_delay_seconds = int(default_retry_delay_seconds * 1.2)


                        print(f"Retrying {layer_name} in {current_sleep_duration} seconds... (Next attempt: {attempt + 2}/{max_crew_retries})")
                        time.sleep(current_sleep_duration)
                        # continue to the next attempt in the loop
                    else:
                        final_error_msg = f"Failed {layer_name} analysis after {max_crew_retries} attempts due to persistent rate limits. Last error: {str(e)}"
                        print(f"❌ {final_error_msg}")
                        session.layers[layer].status = "rate_limited"
                        return {
                            "layer": layer,
                            "layer_name": layer_name,
                            "error": final_error_msg,
                            "retry_suggestion": f"Wait significantly longer (e.g., 5-10 minutes or check API quota dashboard) and try analyzing this layer again: evaluator.analyze(layer={layer})",
                            "status": "rate_limited"
                        }
                else:
                    print(f"❌ Non-rate-limit error in {layer_name}: {str(e)}")
                    # import traceback # For debugging non-rate-limit errors
                    # traceback.print_exc()
                    session.layers[layer].status = "failed"
                    return {
                        "layer": layer,
                        "layer_name": layer_name,
                        "error": str(e),
                        "status": "failed"
                    }
        
        # Fallback if loop finishes (should be caught by logic above)
        session.layers[layer].status = "failed"
        return {
            "layer": layer,
            "layer_name": layer_name,
            "error": "Exited analysis execution loop unexpectedly after all retries.",
            "status": "failed"
        }

    def get_summary(self, session_id: str) -> Dict[str, Any]:
        session = self.state_manager.get_session(session_id)
        if not session:
            return {"error": "Session not found"}
        
        completed_layers_data = {i: asdict(layer) for i, layer in session.layers.items() 
                               if layer.status == "completed"}
        
        return {
            "session_id": session_id,
            "idea": session.user_idea,
            "overall_confidence": session.overall_confidence,
            "completed_layers_count": len(completed_layers_data),
            "total_layers": 5,
            "completion_percentage": (len(completed_layers_data) / 5) * 100,
            "layer_details": completed_layers_data, # More detailed layer info
            "summary_text": self._generate_summary_text(session)
        }
    
    def _generate_summary_text(self, session: AnalysisState) -> str:
        completed = [layer for layer in session.layers.values() if layer.status == "completed"]
        if not completed:
            return "No analysis completed yet."
        
        all_insights = []
        for layer_data in completed:
            if layer_data.insights:
                all_insights.extend(layer_data.insights)
        
        confidence = session.overall_confidence
        confidence_text = "High" if confidence > 0.7 else "Medium" if confidence > 0.5 else "Low"
        
        return f"""
        Analysis Summary for: {session.user_idea}
        
        Overall Confidence: {confidence_text} ({confidence:.2f})
        Completed Layers: {len(completed)}/5
        
        Key Insights:
        {chr(10).join(f"• {insight}" for insight in all_insights[:10])}
        """
    
    def _get_layer_context(self, session: AnalysisState, up_to_layer: int) -> str:
        context = []
        for i in range(1, up_to_layer + 1): # Iterate up to, but not including, the current layer for context
            if i < up_to_layer and session.layers[i].status == "completed": # Ensure it's actually completed
                analysis = session.layers[i].data.get("analysis", "")
                context.append(f"Context from Layer {i} ({session.layers[i].data.get('layer_name', 'Unknown')}): {analysis[:200]}...") # Shorter context
        return "\n".join(context) if context else "No prior context available."
    
    def _extract_insights(self, text: str) -> List[str]:
        lines = text.split('\n')
        insights = []
        for line in lines:
            line = line.strip()
            if line and any(marker in line.lower() for marker in ['•', '-', 'insight', 'key', 'important', '1.', '2.', '3.', '4.']):
                # Remove common prefixes like "Insight:", "Key takeaway:" etc.
                line = re.sub(r'^(insight|key takeaway|important)\s*[:\-•]*\s*', '', line, flags=re.IGNORECASE)
                line = re.sub(r'^[•\-1-9]\.?\s*', '', line) # Remove bullets/numbers
                if len(line) > 20:
                    insights.append(line.strip())
        return list(set(insights))[:5] # Unique insights, max 5
    
    def _extract_confidence(self, text: str) -> float:
        text_lower = text.lower()
        confidence_patterns = [
            r'confidence[:\s]*([0-9]*\.?[0-9]+)',
            r'rating[:\s]*([0-9]*\.?[0-9]+)',
            r'score[:\s]*([0-9]*\.?[0-9]+)'
        ]
        
        for pattern in confidence_patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                try:
                    value = float(matches[-1]) # Take the last found match
                    return min(value, 1.0) if 0.0 <= value <= 1.0 else (min(value, 10.0) / 10.0 if value > 1.0 else 0.5) # Normalize if out of 0-1
                except ValueError:
                    continue
        
        positive_words = ['strong', 'good', 'excellent', 'promising', 'viable', 'high confidence']
        negative_words = ['weak', 'poor', 'challenging', 'difficult', 'risky', 'low confidence']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count: return 0.75
        if negative_count > positive_count: return 0.45
        return 0.6 # Default if no explicit or strong sentiment
    
    def _extract_questions(self, text: str) -> List[str]:
        lines = text.split('\n')
        questions = []
        for line in lines:
            if '?' in line and len(line.strip()) > 15:
                questions.append(line.strip())
        return list(set(questions))[:3] # Unique questions, max 3

# Main Interface - Simplified for hackathon
class IdeaEvaluator:
    def __init__(self):
        self.system = IdeaEvaluationSystem()
        self.current_session_id = None # Changed to current_session_id
    
    def start(self, idea: str) -> str:
        self.current_session_id = self.system.start_analysis(idea)
        return f"✅ Started analysis! Session ID: {self.current_session_id}"
    
    def analyze(self, layer: int = None, user_input: str = "") -> Dict[str, Any]:
        if not self.current_session_id:
            return {"error": "Start analysis first with start(idea)"}
        
        session = self.system.state_manager.get_session(self.current_session_id)
        if not session: # Should not happen if current_session_id is set
             return {"error": f"Session {self.current_session_id} not found unexpectedly."}

        if layer is None:
            results = {}
            # For gemini-1.5-pro, a substantial delay between layers is crucial.
            # Each layer might make 1 (agent) + N (tools) calls. 2 RPM is very restrictive.
            # If using gemini-pro (60 RPM), this can be much shorter (e.g., 5-10 seconds)
            INTER_LAYER_DELAY_SECONDS = 65 # At least 60-65 seconds for gemini-1.5-pro to be safe
            if Config.MODEL_NAME == 'gemini/gemini-pro':
                INTER_LAYER_DELAY_SECONDS = 5 # Much shorter for the more permissive model

            print(f"ℹ️ Using inter-layer delay of {INTER_LAYER_DELAY_SECONDS}s due to model {Config.MODEL_NAME}")

            for i in range(1, 6):
                # Skip already completed layers if we are resuming
                if session.layers[i].status == "completed":
                    print(f"⏭️ Layer {i} ({session.layers[i].data.get('layer_name', 'N/A') if session.layers[i].data else 'N/A'}) already completed. Skipping.")
                    results[i] = {"status": "skipped_completed", "layer": i, "data": asdict(session.layers[i])}
                    continue
                # Also skip if a previous layer failed hard or was rate limited and not resolved
                if i > 1 and session.layers[i-1].status not in ["completed", "skipped_completed"]:
                    print(f"⚠️ Previous layer {i-1} status is {session.layers[i-1].status}. Stopping sequential analysis.")
                    results[i] = {"status": "skipped_previous_failed", "layer": i}
                    break


                print(f"\n--- Processing Layer {i} ---")
                result = self.system.analyze_layer(self.current_session_id, i, user_input)
                results[i] = result
                
                if result.get("status") == "rate_limited":
                    print(f"⏰ Layer {i} hit rate limit, and retries were exhausted. Analysis paused.")
                    print(f"Suggestion: {result.get('retry_suggestion', 'Wait a few minutes and try analyzing this layer or subsequent layers again.')}")
                    break 
                    
                if result.get("status") == "failed":
                    print(f"❌ Layer {i} failed with a non-recoverable error. Analysis paused. Error: {result.get('error')}")
                    break
                    
                if i < 5 and result.get("status") == "completed": # Don't delay after the last layer or if layer failed
                    print(f"✅ Layer {i} completed. Waiting {INTER_LAYER_DELAY_SECONDS} seconds before next layer...")
                    time.sleep(INTER_LAYER_DELAY_SECONDS)
            
            # Final summary after all layers attempt
            print("\n--- Full Analysis Attempt Completed ---")
            final_summary = self.summary()
            print(json.dumps(final_summary, indent=2))
            return {"all_layer_results": results, "final_summary": final_summary}
        else:
            # Analyzing a single layer
            return self.system.analyze_layer(self.current_session_id, layer, user_input)
    
    def summary(self) -> Dict[str, Any]:
        if not self.current_session_id:
            return {"error": "No active session"}
        return self.system.get_summary(self.current_session_id)
    
    def status(self) -> Dict[str, Any]:
        if not self.current_session_id:
            return {"error": "No active session"}
        
        session = self.system.state_manager.get_session(self.current_session_id)
        if not session:
            return {"error": f"Session {self.current_session_id} not found."}

        return {
            "session_id": self.current_session_id,
            "idea": session.user_idea,
            "current_layer_processed": session.current_layer, # Layer that was last attempted
            "overall_confidence": session.overall_confidence,
            "layers_status": {i: l.status for i, l in session.layers.items()},
            "completed_layers_count": sum(1 for l in session.layers.values() if l.status == "completed")
        }

# Usage Example
def demo():
    """Quick demo for hackathon"""
    print("🤖 Idea Evaluation System - Hackathon Demo")
    print("==================================================")
    
    evaluator = IdeaEvaluator()
    
    # Test idea
    idea = "Gen-AI-powered assistant that validates your start up idea and goes through market researching using googel searches and analyse the idea from a broder prerspecitve to being specific and narrow."
    print(f"💡 Testing Idea: {idea}")
    
    # Start analysis
    start_message = evaluator.start(idea)
    print(start_message)
    if "Error" in start_message: return

    # Analyze all layers sequentially (this will take a long time with gemini-1.5-pro)
    # You can also analyze layer by layer:
    print("\n🔍 Analyzing Vision Layer (Layer 1)...")
    result_layer1 = evaluator.analyze(layer=1, user_input="Focus on the Gen Z market and ethical fashion trends.")
    print(json.dumps(result_layer1, indent=2))
    if result_layer1.get("status") != "completed":
        print("Stopping demo due to issue in Layer 1.")
        return

    # print(f"\n⏱️ Waiting {65} seconds before next layer...")
    # time.sleep(65)

    # print("\n🔍 Analyzing Strategy Layer (Layer 2)...")
    # result_layer2 = evaluator.analyze(layer=2, user_input="Consider a freemium model with premium AI features.")
    # print(json.dumps(result_layer2, indent=2))
    # if result_layer2.get("status") != "completed":
    #     print("Stopping demo due to issue in Layer 2.")
    #     return

    # For the demo, let's try to run all layers.
    print("\n🔍 Analyzing all layers sequentially (this may take a while)...")
    full_analysis_results = evaluator.analyze() # This will now print its own summary at the end.
    # print("\n--- Full Analysis Results ---")
    # print(json.dumps(full_analysis_results, indent=2)) # Already printed by analyze()

    print("\n📊 Final Status:")
    status_info = evaluator.status()
    print(json.dumps(status_info, indent=2))
    
    print("\n📋 Final Summary:")
    summary_info = evaluator.summary()
    print(json.dumps(summary_info, indent=2))
    
    return evaluator

if __name__ == "__main__":
    print("🚀 Hackathon-Ready Idea Evaluator")
    print("Ensure GEMINI_API_KEY environment variable is set.")
    print("To use, create an instance and call methods:")
    print("  evaluator = IdeaEvaluator()")
    print("  evaluator.start('your amazing tech idea')")
    print("  # To analyze a specific layer:")
    print("  # result_layer1 = evaluator.analyze(layer=1, user_input='Focus on B2B market')")
    print("  # print(result_layer1)")
    print("  # To analyze all layers sequentially (WARNING: SLOW with gemini-1.5-pro free tier):")
    print("  # full_results = evaluator.analyze()")
    print("  # print(full_results)")
    print("  summary = evaluator.summary()")
    print("  print(summary)")
    print("-" * 50)
    
    # Uncomment to run the demo:
    print("\nStarting Demo...")
    demo_evaluator = demo()
    print("\nDemo Finished.")

    # Interactive Usage Example:
    # evaluator = IdeaEvaluator()
    # my_idea = input("Enter your idea: ")
    # evaluator.start(my_idea)
    # for i in range(1,6):
    #     print(f"\nAnalyzing layer {i}...")
    #     user_c = input(f"Any specific input for layer {i}? (Press Enter for none): ")
    #     res = evaluator.analyze(layer=i, user_input=user_c)
    #     print(json.dumps(res, indent=2))
    #     if res.get("status") != "completed":
    #         print(f"Layer {i} did not complete. Stopping.")
    #         break
    #     if i < 5 :
    #         delay = 65 if Config.MODEL_NAME == 'gemini/gemini-1.5-pro' else 5
    #         print(f"Waiting {delay}s for next layer...")
    #         time.sleep(delay)
    # print("\nFinal Summary:")
    # print(json.dumps(evaluator.summary(), indent=2))