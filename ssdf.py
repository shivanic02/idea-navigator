# #!/usr/bin/env python3
# """
# Idea Evaluation Agentic System - Core MVP
# A collaborative multi-agent system for comprehensive idea analysis using CrewAI and Google Gemini
# """

# import os
# import json
# import uuid
# from datetime import datetime
# from typing import Dict, List, Any, Optional
# from dataclasses import dataclass, asdict
# import google.generativeai as genai
# from crewai import Agent, Task, Crew, Process
# from crewai.tools import BaseTool
# from pydantic import BaseModel, Field

# # Configuration
# class Config:
#     GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-gemini-api-key-here')
#     MODEL_NAME = 'gemini-1.5-pro'
#     MAX_SEARCH_RESULTS = 5
#     CONFIDENCE_THRESHOLD = 0.7

# # Initialize Gemini
# genai.configure(api_key=Config.GEMINI_API_KEY)

# # Data Models
# @dataclass
# class LayerData:
#     status: str = "pending"  # pending, in_progress, completed
#     data: Dict[str, Any] = None
#     insights: List[str] = None
#     confidence: float = 0.0
#     last_updated: str = ""
    
#     def __post_init__(self):
#         if self.data is None:
#             self.data = {}
#         if self.insights is None:
#             self.insights = []
#         if not self.last_updated:
#             self.last_updated = datetime.now().isoformat()

# @dataclass
# class AnalysisState:
#     session_id: str
#     user_idea: str
#     current_layer: int = 1
#     layers: Dict[int, LayerData] = None
#     analysis_history: List[Dict] = None
#     current_insights: Dict[str, Any] = None
#     overall_confidence: float = 0.0
    
#     def __post_init__(self):
#         if self.layers is None:
#             self.layers = {i: LayerData() for i in range(1, 6)}
#         if self.analysis_history is None:
#             self.analysis_history = []
#         if self.current_insights is None:
#             self.current_insights = {}

# # Custom Tools
# class MarketResearchTool(BaseTool):
#     name: str = "market_research"
#     description: str = "Search the internet for market data, trends, and competitive information"
    
#     def _run(self, query: str, context: str = "") -> str:
#         try:
#             model = genai.GenerativeModel(Config.MODEL_NAME)
            
#             # Enhanced search prompt
#             search_prompt = f"""
#             You are a market research expert. Search for and analyze information about: {query}
            
#             Context: {context}
            
#             Please provide:
#             1. Current market data and trends
#             2. Key competitors and market players
#             3. Recent developments and news
#             4. Market size and growth projections
#             5. Expert opinions and analysis
            
#             Format your response as structured insights with sources when possible.
#             """
            
#             response = model.generate_content(search_prompt)
#             return response.text
            
#         except Exception as e:
#             return f"Research error: {str(e)}"
    
#     async def _arun(self, query: str, context: str = "") -> str:
#         return self._run(query, context)

# class TrendAnalysisTool(BaseTool):
#     name: str = "trend_analysis"
#     description: str = "Analyze future trends and macro forces relevant to the idea"
    
#     def _run(self, idea: str, timeframe: str = "5 years") -> str:
#         try:
#             model = genai.GenerativeModel(Config.MODEL_NAME)
            
#             trend_prompt = f"""
#             Analyze future trends and macro forces for the next {timeframe} that could impact this idea: {idea}
            
#             Focus on:
#             1. Technological trends and disruptions
#             2. Social and demographic shifts
#             3. Economic patterns and changes
#             4. Regulatory and policy trends
#             5. Environmental and sustainability factors
            
#             Provide specific, actionable insights about how these trends create opportunities or challenges.
#             """
            
#             response = model.generate_content(trend_prompt)
#             return response.text
            
#         except Exception as e:
#             return f"Trend analysis error: {str(e)}"
    
#     async def _arun(self, idea: str, timeframe: str = "5 years") -> str:
#         return self._run(idea, timeframe)

# # State Management
# class StateManager:
#     def __init__(self):
#         self.sessions = {}
    
#     def create_session(self, user_idea: str) -> str:
#         session_id = str(uuid.uuid4())
#         self.sessions[session_id] = AnalysisState(
#             session_id=session_id,
#             user_idea=user_idea
#         )
#         return session_id
    
#     def get_session(self, session_id: str) -> Optional[AnalysisState]:
#         return self.sessions.get(session_id)
    
#     def update_layer(self, session_id: str, layer: int, data: Dict, insights: List[str], confidence: float):
#         if session_id in self.sessions:
#             layer_data = LayerData(
#                 status="completed",
#                 data=data,
#                 insights=insights,
#                 confidence=confidence,
#                 last_updated=datetime.now().isoformat()
#             )
#             self.sessions[session_id].layers[layer] = layer_data
#             self._update_overall_confidence(session_id)
    
#     def _update_overall_confidence(self, session_id: str):
#         session = self.sessions[session_id]
#         completed_layers = [l for l in session.layers.values() if l.status == "completed"]
#         if completed_layers:
#             session.overall_confidence = sum(l.confidence for l in completed_layers) / len(completed_layers)

# # Dependency Engine
# class DependencyEngine:
#     DEPENDENCIES = {
#         1: [2, 3, 4, 5],  # Layer 1 affects layers 2-5
#         2: [3, 4, 5],     # Layer 2 affects layers 3-5
#         3: [4, 5],        # Layer 3 affects layers 4-5
#         4: [5],           # Layer 4 affects layer 5
#         5: []             # Layer 5 affects none
#     }
    
#     @classmethod
#     def get_affected_layers(cls, changed_layer: int) -> List[int]:
#         return cls.DEPENDENCIES.get(changed_layer, [])
    
#     @classmethod
#     def should_trigger_review(cls, changed_layer: int, target_layer: int) -> bool:
#         return target_layer in cls.get_affected_layers(changed_layer)

# # Agent Definitions
# def create_orchestrator_agent(state_manager: StateManager) -> Agent:
#     return Agent(
#         role='Analysis Orchestrator',
#         goal='Coordinate the comprehensive analysis of business ideas through structured evaluation layers',
#         backstory="""You are a seasoned business strategist and venture capital analyst with 15+ years 
#         of experience evaluating startups and business opportunities. You excel at asking the right 
#         questions, identifying blind spots, and ensuring thorough analysis. You coordinate other 
#         specialists to provide comprehensive insights.""",
#         verbose=True,
#         allow_delegation=True,
#         tools=[MarketResearchTool(), TrendAnalysisTool()]
#     )

# def create_philosopher_agent() -> Agent:
#     return Agent(
#         role='Vision & Strategy Philosopher',
#         goal='Analyze the fundamental vision, market opportunities, and strategic positioning of ideas',
#         backstory="""You are a visionary strategist who thinks deeply about future trends, market 
#         evolution, and strategic positioning. You have a PhD in Strategic Management and have 
#         advised Fortune 500 companies on digital transformation. You excel at identifying 
#         blue ocean opportunities and understanding jobs-to-be-done.""",
#         verbose=True,
#         tools=[TrendAnalysisTool(), MarketResearchTool()]
#     )

# def create_market_analyst_agent() -> Agent:
#     return Agent(
#         role='Market Research Analyst',
#         goal='Conduct thorough market validation and competitive analysis',
#         backstory="""You are a senior market research analyst with expertise in consumer behavior, 
#         market sizing, and competitive intelligence. You've worked at top consulting firms like 
#         McKinsey and have deep experience in market entry strategies. You're skilled at identifying 
#         target customers and assessing market readiness.""",
#         verbose=True,
#         tools=[MarketResearchTool()]
#     )

# def create_business_strategist_agent() -> Agent:
#     return Agent(
#         role='Business Model Strategist',
#         goal='Analyze business model viability, unit economics, and scalability potential',
#         backstory="""You are a business model expert and former startup founder who has built 
#         and scaled multiple successful companies. You understand unit economics, revenue models, 
#         and operational scaling challenges. You've raised over $50M in venture capital and 
#         have deep insights into what makes businesses successful.""",
#         verbose=True,
#         tools=[MarketResearchTool()]
#     )

# # Core Analysis System
# class IdeaEvaluationSystem:
#     def __init__(self):
#         self.state_manager = StateManager()
#         self.dependency_engine = DependencyEngine()
#         self.orchestrator = create_orchestrator_agent(self.state_manager)
#         self.philosopher = create_philosopher_agent()
#         self.market_analyst = create_market_analyst_agent()
#         self.business_strategist = create_business_strategist_agent()
        
#     def start_analysis(self, user_idea: str) -> str:
#         """Initialize a new analysis session"""
#         session_id = self.state_manager.create_session(user_idea)
#         print(f"🚀 Starting analysis for idea: {user_idea}")
#         print(f"📋 Session ID: {session_id}")
#         return session_id
    
#     def analyze_layer(self, session_id: str, layer: int, user_input: str = "") -> Dict[str, Any]:
#         """Analyze a specific layer with collaborative approach"""
#         session = self.state_manager.get_session(session_id)
#         if not session:
#             return {"error": "Session not found"}
        
#         # Update current layer
#         session.current_layer = layer
#         session.layers[layer].status = "in_progress"
        
#         # Create layer-specific tasks
#         if layer == 1:
#             return self._analyze_vision_layer(session, user_input)
#         elif layer == 2:
#             return self._analyze_strategy_layer(session, user_input)
#         elif layer == 3:
#             return self._analyze_market_layer(session, user_input)
#         elif layer == 4:
#             return self._analyze_competition_layer(session, user_input)
#         elif layer == 5:
#             return self._analyze_business_model_layer(session, user_input)
#         else:
#             return {"error": "Layer not implemented in MVP"}
    
#     def _analyze_vision_layer(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         """Layer 1: Vision & Trends Analysis"""
#         task = Task(
#             description=f"""
#             Analyze the vision and strategic opportunity for this idea: {session.user_idea}
            
#             User additional input: {user_input}
            
#             Focus on:
#             1. Future Trends & Macro Forces - What trends support this idea?
#             2. Jobs-to-be-Done - What fundamental need does this address?
#             3. Blue Ocean vs Red Ocean - Is this creating new market space?
            
#             Provide specific insights and ask 2-3 thoughtful follow-up questions to deepen understanding.
#             Rate your confidence level (0-1) in the opportunity.
#             """,
#             agent=self.philosopher,
#             expected_output="Structured analysis with insights, questions, and confidence rating"
#         )
        
#         crew = Crew(
#             agents=[self.philosopher],
#             tasks=[task],
#             process=Process.sequential,
#             verbose=True
#         )
        
#         result = crew.kickoff()
        
#         # Extract insights and update state
#         insights = self._extract_insights(result.raw, layer=1)
#         confidence = self._extract_confidence(result.raw)
        
#         self.state_manager.update_layer(
#             session.session_id, 1, 
#             {"analysis": result.raw}, 
#             insights, 
#             confidence
#         )
        
#         return {
#             "layer": 1,
#             "analysis": result.raw,
#             "insights": insights,
#             "confidence": confidence,
#             "next_questions": self._extract_questions(result.raw)
#         }
    
#     def _analyze_strategy_layer(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         """Layer 2: Strategic Positioning Analysis"""
#         context = session.layers[1].data.get("analysis", "") if session.layers[1].status == "completed" else ""
        
#         task = Task(
#             description=f"""
#             Based on the vision analysis: {context}
            
#             Analyze strategic positioning for: {session.user_idea}
#             User input: {user_input}
            
#             Focus on:
#             1. Platform vs Product Strategy - Are you building an ecosystem or standalone solution?
#             2. Market Timing & Readiness - Is the market ready for this now?
#             3. Disruption Potential - Could this disrupt existing markets?
            
#             Provide strategic insights and ask follow-up questions.
#             Rate confidence (0-1).
#             """,
#             agent=self.philosopher,
#             expected_output="Strategic positioning analysis with recommendations"
#         )
        
#         crew = Crew(
#             agents=[self.philosopher],
#             tasks=[task],
#             process=Process.sequential,
#             verbose=True
#         )
        
#         result = crew.kickoff()
#         insights = self._extract_insights(result.raw, layer=2)
#         confidence = self._extract_confidence(result.raw)
        
#         self.state_manager.update_layer(
#             session.session_id, 2,
#             {"analysis": result.raw},
#             insights,
#             confidence
#         )
        
#         return {
#             "layer": 2,
#             "analysis": result.raw,
#             "insights": insights,
#             "confidence": confidence,
#             "next_questions": self._extract_questions(result.raw)
#         }
    
#     def _analyze_market_layer(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         """Layer 3: Market Validation Analysis"""
#         context = self._get_previous_context(session, 3)
        
#         task = Task(
#             description=f"""
#             Previous analysis context: {context}
            
#             Conduct market validation for: {session.user_idea}
#             User input: {user_input}
            
#             Focus on:
#             1. Vitamin vs Painkiller - Is this solving urgent problems or nice-to-have?
#             2. Target Customer Definition - Who exactly is your ideal customer?
#             3. Market Size Estimation - What's the addressable market size?
            
#             Use market research tools to gather current data.
#             Provide market insights and validation recommendations.
#             Rate confidence (0-1).
#             """,
#             agent=self.market_analyst,
#             expected_output="Market validation analysis with data-driven insights"
#         )
        
#         crew = Crew(
#             agents=[self.market_analyst],
#             tasks=[task],
#             process=Process.sequential,
#             verbose=True
#         )
        
#         result = crew.kickoff()
#         insights = self._extract_insights(result.raw, layer=3)
#         confidence = self._extract_confidence(result.raw)
        
#         self.state_manager.update_layer(
#             session.session_id, 3,
#             {"analysis": result.raw},
#             insights,
#             confidence
#         )
        
#         return {
#             "layer": 3,
#             "analysis": result.raw,
#             "insights": insights,
#             "confidence": confidence,
#             "next_questions": self._extract_questions(result.raw)
#         }
    
#     def _analyze_competition_layer(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         """Layer 4: Competitive Analysis"""
#         context = self._get_previous_context(session, 4)
        
#         task = Task(
#             description=f"""
#             Previous analysis: {context}
            
#             Analyze competitive landscape for: {session.user_idea}
#             User input: {user_input}
            
#             Focus on:
#             1. Competitive Landscape - Who are direct and indirect competitors?
#             2. Differentiation Strategy - How will you stand out?
#             3. Competitive Moat - What prevents easy replication?
            
#             Research current competitors and market positioning.
#             Rate confidence (0-1).
#             """,
#             agent=self.market_analyst,
#             expected_output="Competitive analysis with differentiation strategy"
#         )
        
#         crew = Crew(
#             agents=[self.market_analyst],
#             tasks=[task],
#             process=Process.sequential,
#             verbose=True
#         )
        
#         result = crew.kickoff()
#         insights = self._extract_insights(result.raw, layer=4)
#         confidence = self._extract_confidence(result.raw)
        
#         self.state_manager.update_layer(
#             session.session_id, 4,
#             {"analysis": result.raw},
#             insights,
#             confidence
#         )
        
#         return {
#             "layer": 4,
#             "analysis": result.raw,
#             "insights": insights,
#             "confidence": confidence,
#             "next_questions": self._extract_questions(result.raw)
#         }
    
#     def _analyze_business_model_layer(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         """Layer 5: Business Model Analysis"""
#         context = self._get_previous_context(session, 5)
        
#         task = Task(
#             description=f"""
#             Previous analysis: {context}
            
#             Analyze business model viability for: {session.user_idea}
#             User input: {user_input}
            
#             Focus on:
#             1. Revenue Model - How will you make money?
#             2. Unit Economics - What are the key metrics (CAC, LTV, etc.)?
#             3. Scalability Assessment - Can this scale efficiently?
            
#             Provide business model recommendations and financial projections.
#             Rate confidence (0-1).
#             """,
#             agent=self.business_strategist,
#             expected_output="Business model analysis with financial insights"
#         )
        
#         crew = Crew(
#             agents=[self.business_strategist],
#             tasks=[task],
#             process=Process.sequential,
#             verbose=True
#         )
        
#         result = crew.kickoff()
#         insights = self._extract_insights(result.raw, layer=5)
#         confidence = self._extract_confidence(result.raw)
        
#         self.state_manager.update_layer(
#             session.session_id, 5,
#             {"analysis": result.raw},
#             insights,
#             confidence
#         )
        
#         return {
#             "layer": 5,
#             "analysis": result.raw,
#             "insights": insights,
#             "confidence": confidence,
#             "next_questions": self._extract_questions(result.raw)
#         }
    
#     def get_full_analysis(self, session_id: str) -> Dict[str, Any]:
#         """Generate comprehensive analysis summary"""
#         session = self.state_manager.get_session(session_id)
#         if not session:
#             return {"error": "Session not found"}
        
#         # Create synthesis task
#         synthesis_task = Task(
#             description=f"""
#             Create a comprehensive analysis summary for: {session.user_idea}
            
#             Layer analyses:
#             {self._format_all_layers(session)}
            
#             Provide:
#             1. Executive Summary
#             2. Key Strengths and Opportunities
#             3. Main Concerns and Risks
#             4. Overall Recommendation
#             5. Next Steps and Action Items
#             6. Confidence Assessment
            
#             Be specific and actionable.
#             """,
#             agent=self.orchestrator,
#             expected_output="Executive summary with actionable recommendations"
#         )
        
#         crew = Crew(
#             agents=[self.orchestrator],
#             tasks=[synthesis_task],
#             process=Process.sequential,
#             verbose=True
#         )
        
#         result = crew.kickoff()
        
#         return {
#             "session_id": session_id,
#             "idea": session.user_idea,
#             "overall_confidence": session.overall_confidence,
#             "synthesis": result.raw,
#             "layer_summary": self._get_layer_summary(session),
#             "completion_status": self._get_completion_status(session)
#         }
    
#     def navigate_to_layer(self, session_id: str, target_layer: int) -> Dict[str, Any]:
#         """Navigate to specific layer for modifications"""
#         session = self.state_manager.get_session(session_id)
#         if not session:
#             return {"error": "Session not found"}
        
#         if target_layer < 1 or target_layer > 5:
#             return {"error": "Invalid layer number"}
        
#         session.current_layer = target_layer
#         current_analysis = session.layers[target_layer].data.get("analysis", "No analysis yet")
        
#         return {
#             "current_layer": target_layer,
#             "current_analysis": current_analysis,
#             "status": session.layers[target_layer].status,
#             "confidence": session.layers[target_layer].confidence,
#             "message": f"You're now at Layer {target_layer}. What would you like to explore or modify?"
#         }
    
#     # Helper Methods
#     def _get_previous_context(self, session: AnalysisState, current_layer: int) -> str:
#         """Get context from previous layers"""
#         context_parts = []
#         for i in range(1, current_layer):
#             if session.layers[i].status == "completed":
#                 analysis = session.layers[i].data.get("analysis", "")
#                 context_parts.append(f"Layer {i}: {analysis[:500]}...")  # Truncate for context
#         return "\n\n".join(context_parts)
    
#     def _extract_insights(self, text: str, layer: int) -> List[str]:
#         """Extract key insights from analysis text"""
#         # Simple extraction - in production, use more sophisticated NLP
#         lines = text.split('\n')
#         insights = []
#         for line in lines:
#             if any(keyword in line.lower() for keyword in ['insight:', 'key finding:', '• ', '- ']):
#                 insights.append(line.strip())
#         return insights[:5]  # Limit to top 5 insights
    
#     def _extract_confidence(self, text: str) -> float:
#         """Extract confidence rating from text"""
#         # Look for confidence indicators
#         text_lower = text.lower()
#         if 'confidence' in text_lower:
#             # Simple regex to find confidence numbers
#             import re
#             matches = re.findall(r'confidence[:\s]+([0-9.]+)', text_lower)
#             if matches:
#                 try:
#                     return min(float(matches[0]), 1.0)
#                 except:
#                     pass
#         return 0.7  # Default confidence
    
#     def _extract_questions(self, text: str) -> List[str]:
#         """Extract follow-up questions from analysis"""
#         lines = text.split('\n')
#         questions = []
#         for line in lines:
#             if '?' in line and len(line.strip()) > 10:
#                 questions.append(line.strip())
#         return questions[:3]  # Limit to 3 questions
    
#     def _format_all_layers(self, session: AnalysisState) -> str:
#         """Format all completed layers for synthesis"""
#         formatted = []
#         layer_names = {
#             1: "Vision & Trends",
#             2: "Strategic Positioning", 
#             3: "Market Validation",
#             4: "Competitive Analysis",
#             5: "Business Model"
#         }
        
#         for i in range(1, 6):
#             if session.layers[i].status == "completed":
#                 analysis = session.layers[i].data.get("analysis", "")
#                 formatted.append(f"## {layer_names[i]}\n{analysis}\n")
        
#         return "\n".join(formatted)
    
#     def _get_layer_summary(self, session: AnalysisState) -> Dict[int, Dict]:
#         """Get summary of all layers"""
#         summary = {}
#         for i in range(1, 6):
#             layer = session.layers[i]
#             summary[i] = {
#                 "status": layer.status,
#                 "confidence": layer.confidence,
#                 "insights_count": len(layer.insights),
#                 "last_updated": layer.last_updated
#             }
#         return summary
    
#     def _get_completion_status(self, session: AnalysisState) -> Dict[str, Any]:
#         """Get overall completion status"""
#         completed = sum(1 for layer in session.layers.values() if layer.status == "completed")
#         return {
#             "completed_layers": completed,
#             "total_layers": 5,
#             "completion_percentage": (completed / 5) * 100,
#             "is_complete": completed == 5
#         }

# # Main Interface Class
# class IdeaEvaluationInterface:
#     def __init__(self):
#         self.system = IdeaEvaluationSystem()
#         self.current_session = None
    
#     def start_new_analysis(self, idea: str) -> str:
#         """Start a new idea analysis"""
#         self.current_session = self.system.start_analysis(idea)
#         return f"✅ Analysis started! Session ID: {self.current_session}"
    
#     def continue_analysis(self, layer: int = None, user_input: str = "") -> Dict[str, Any]:
#         """Continue analysis at specific layer"""
#         if not self.current_session:
#             return {"error": "No active session. Start a new analysis first."}
        
#         session = self.system.state_manager.get_session(self.current_session)
#         if layer is None:
#             layer = session.current_layer
        
#         return self.system.analyze_layer(self.current_session, layer, user_input)
    
#     def navigate_to_layer(self, layer: int) -> Dict[str, Any]:
#         """Navigate to specific layer"""
#         if not self.current_session:
#             return {"error": "No active session"}
        
#         return self.system.navigate_to_layer(self.current_session, layer)
    
#     def get_full_analysis(self) -> Dict[str, Any]:
#         """Get comprehensive analysis"""
#         if not self.current_session:
#             return {"error": "No active session"}
        
#         return self.system.get_full_analysis(self.current_session)
    
#     def get_session_status(self) -> Dict[str, Any]:
#         """Get current session status"""
#         if not self.current_session:
#             return {"error": "No active session"}
        
#         session = self.system.state_manager.get_session(self.current_session)
#         return {
#             "session_id": self.current_session,
#             "idea": session.user_idea,
#             "current_layer": session.current_layer,
#             "overall_confidence": session.overall_confidence,
#             "layer_status": self.system._get_layer_summary(session),
#             "completion": self.system._get_completion_status(session)
#         }

# # Usage Example and Testing
# def main():
#     """Example usage of the Idea Evaluation System"""
#     print("🤖 Idea Evaluation System - Core MVP")
#     print("=" * 50)
    
#     # Initialize system
#     evaluator = IdeaEvaluationInterface()
    
#     # Example idea
#     sample_idea = "Realtime Voice based AI agents in the domain of realestate"
    
#     print(f"📝 Testing with idea: {sample_idea}")
#     print()
    
#     # Start analysis
#     result = evaluator.start_new_analysis(sample_idea)
#     print(result)
#     print()
    
#     # Analyze each layer
#     for layer in range(1, 6):
#         print(f"🔍 Analyzing Layer {layer}...")
#         result = evaluator.continue_analysis(layer, f"I'm particularly interested in understanding the market opportunity for layer {layer}")
#         print(f"✅ Layer {layer} completed with confidence: {result.get('confidence', 0)}")
#         print()
    
#     # Get final analysis
#     print("📊 Generating final analysis...")
#     final = evaluator.get_full_analysis()
#     print("✅ Analysis complete!")
#     print(f"Overall confidence: {final.get('overall_confidence', 0)}")
    
#     return evaluator

# if __name__ == "__main__":
#     # Set up your Gemini API key as environment variable:
#     # export GEMINI_API_KEY="your-actual-api-key"
    
#     print("To use this system:")
#     print("1. Set your GEMINI_API_KEY environment variable")
#     print("2. Install required packages: pip install crewai google-generativeai")
#     print("3. Run: evaluator = main()")
#     print()
    
#     # Uncomment to test:
#     evaluator = main()




# #!/usr/bin/env python3
# """
# Idea Evaluation Agentic System - Hackathon MVP
# A multi-agent system for comprehensive idea analysis using CrewAI and Google Gemini
# """

# import os
# import json
# import uuid
# from datetime import datetime
# from typing import Dict, List, Any, Optional
# from dataclasses import dataclass, asdict
# import google.generativeai as genai
# from crewai import Agent, Task, Crew, Process
# from crewai.tools import BaseTool

# # Configuration
# class Config:
#     GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-gemini-api-key-here')
#     MODEL_NAME = 'gemini/gemini-1.5-pro'  # Proper CrewAI format
#     CONFIDENCE_THRESHOLD = 0.7

# # Initialize Gemini
# genai.configure(api_key=Config.GEMINI_API_KEY)

# # Set environment variables for CrewAI to use Gemini
# os.environ['GOOGLE_API_KEY'] = Config.GEMINI_API_KEY

# # Data Models
# @dataclass
# class LayerData:
#     status: str = "pending"
#     data: Dict[str, Any] = None
#     insights: List[str] = None
#     confidence: float = 0.0
#     last_updated: str = ""
    
#     def __post_init__(self):
#         if self.data is None:
#             self.data = {}
#         if self.insights is None:
#             self.insights = []
#         if not self.last_updated:
#             self.last_updated = datetime.now().isoformat()

# @dataclass
# class AnalysisState:
#     session_id: str
#     user_idea: str
#     current_layer: int = 1
#     layers: Dict[int, LayerData] = None
#     overall_confidence: float = 0.0
    
#     def __post_init__(self):
#         if self.layers is None:
#             self.layers = {i: LayerData() for i in range(1, 6)}

# # Custom Tools - Simplified for hackathon
# class MarketResearchTool(BaseTool):
#     name: str = "market_research"
#     description: str = "Research market data and competitive information"
    
#     def _run(self, query: str) -> str:
#         try:
#             model = genai.GenerativeModel(Config.MODEL_NAME)
            
#             prompt = f"""
#             Research and analyze: {query}
            
#             Provide insights on:
#             1. Market trends and data
#             2. Key competitors
#             3. Market size estimates
#             4. Growth opportunities
            
#             Keep response concise but insightful.
#             """
            
#             response = model.generate_content(prompt)
#             return response.text
            
#         except Exception as e:
#             return f"Research unavailable: {str(e)}"

# class TrendAnalysisTool(BaseTool):
#     name: str = "trend_analysis" 
#     description: str = "Analyze future trends relevant to the idea"
    
#     def _run(self, idea: str) -> str:
#         try:
#             model = genai.GenerativeModel(Config.MODEL_NAME)
            
#             prompt = f"""
#             Analyze future trends for: {idea}
            
#             Focus on:
#             1. Technology trends
#             2. Market shifts
#             3. User behavior changes
#             4. Opportunities and threats
            
#             Provide specific, actionable insights.
#             """
            
#             response = model.generate_content(prompt)
#             return response.text
            
#         except Exception as e:
#             return f"Trend analysis unavailable: {str(e)}"

# # State Management - Simplified
# class StateManager:
#     def __init__(self):
#         self.sessions = {}
    
#     def create_session(self, user_idea: str) -> str:
#         session_id = str(uuid.uuid4())[:8]  # Shorter ID for hackathon
#         self.sessions[session_id] = AnalysisState(
#             session_id=session_id,
#             user_idea=user_idea
#         )
#         return session_id
    
#     def get_session(self, session_id: str) -> Optional[AnalysisState]:
#         return self.sessions.get(session_id)
    
#     def update_layer(self, session_id: str, layer: int, data: Dict, insights: List[str], confidence: float):
#         if session_id in self.sessions:
#             self.sessions[session_id].layers[layer] = LayerData(
#                 status="completed",
#                 data=data,
#                 insights=insights,
#                 confidence=confidence,
#                 last_updated=datetime.now().isoformat()
#             )
#             self._update_overall_confidence(session_id)
    
#     def _update_overall_confidence(self, session_id: str):
#         session = self.sessions[session_id]
#         completed_layers = [l for l in session.layers.values() if l.status == "completed"]
#         if completed_layers:
#             session.overall_confidence = sum(l.confidence for l in completed_layers) / len(completed_layers)

# # Agent Creation - Simplified with Gemini LLM
# def create_agents():
#     # Configure Gemini LLM for CrewAI
#     from crewai import LLM
    
#     # Configure Gemini LLM for CrewAI
#     gemini_llm = LLM(
#         model="gemini/gemini-1.5-pro",  # Note the "gemini/" prefix
#         google_api_key=Config.GEMINI_API_KEY,
#         temperature=0.7
#     )
    
#     market_tool = MarketResearchTool()
#     trend_tool = TrendAnalysisTool()
    
#     strategist = Agent(
#         role='Business Strategist',
#         goal='Analyze business opportunities and strategy',
#         backstory='Expert strategist with deep business analysis experience',
#         verbose=False,
#         tools=[trend_tool, market_tool],
#         llm=gemini_llm  # Explicitly set Gemini LLM
#     )
    
#     analyst = Agent(
#         role='Market Analyst', 
#         goal='Research markets and validate opportunities',
#         backstory='Senior analyst specializing in market research and validation',
#         verbose=False,
#         tools=[market_tool],
#         llm=gemini_llm  # Explicitly set Gemini LLM
#     )
    
#     return strategist, analyst

# # Core Analysis System
# class IdeaEvaluationSystem:
#     def __init__(self):
#         self.state_manager = StateManager()
#         self.strategist, self.analyst = create_agents()
        
#     def start_analysis(self, user_idea: str) -> str:
#         session_id = self.state_manager.create_session(user_idea)
#         print(f"🚀 Starting analysis: '{user_idea[:50]}...'")
#         print(f"📋 Session: {session_id}")
#         return session_id
    
#     def analyze_layer(self, session_id: str, layer: int, user_input: str = "") -> Dict[str, Any]:
#         session = self.state_manager.get_session(session_id)
#         if not session:
#             return {"error": "Session not found"}
        
#         session.current_layer = layer
#         session.layers[layer].status = "in_progress"
        
#         layer_methods = {
#             1: self._analyze_vision,
#             2: self._analyze_strategy, 
#             3: self._analyze_market,
#             4: self._analyze_competition,
#             5: self._analyze_business_model
#         }
        
#         if layer in layer_methods:
#             return layer_methods[layer](session, user_input)
#         else:
#             return {"error": f"Layer {layer} not implemented"}
    
#     def _analyze_vision(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         task = Task(
#             description=f"""
#             Analyze the vision and opportunity for: {session.user_idea}
#             Additional context: {user_input}
            
#             Evaluate:
#             1. What problem does this solve?
#             2. What trends support this idea?
#             3. What's the opportunity size?
            
#             Provide insights and rate confidence (0-1).
#             """,
#             agent=self.strategist,
#             expected_output="Vision analysis with confidence rating"
#         )
        
#         return self._execute_analysis(session, 1, task, "Vision & Opportunity")
    
#     def _analyze_strategy(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         context = self._get_layer_context(session, 1)
        
#         task = Task(
#             description=f"""
#             Previous analysis: {context}
            
#             Analyze strategy for: {session.user_idea}
#             User input: {user_input}
            
#             Focus on:
#             1. Strategic positioning
#             2. Market timing
#             3. Competitive advantages
            
#             Rate confidence (0-1).
#             """,
#             agent=self.strategist,
#             expected_output="Strategic analysis"
#         )
        
#         return self._execute_analysis(session, 2, task, "Strategy & Positioning")
    
#     def _analyze_market(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         context = self._get_layer_context(session, 2)
        
#         task = Task(
#             description=f"""
#             Previous analysis: {context}
            
#             Market validation for: {session.user_idea}
#             User input: {user_input}
            
#             Research:
#             1. Target customers
#             2. Market size
#             3. Customer needs validation
            
#             Use market research tools. Rate confidence (0-1).
#             """,
#             agent=self.analyst,
#             expected_output="Market validation analysis"
#         )
        
#         return self._execute_analysis(session, 3, task, "Market Validation")
    
#     def _analyze_competition(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         context = self._get_layer_context(session, 3)
        
#         task = Task(
#             description=f"""
#             Previous analysis: {context}
            
#             Competitive analysis for: {session.user_idea}
#             User input: {user_input}
            
#             Analyze:
#             1. Direct/indirect competitors
#             2. Differentiation opportunities
#             3. Competitive advantages
            
#             Rate confidence (0-1).
#             """,
#             agent=self.analyst,
#             expected_output="Competitive analysis"
#         )
        
#         return self._execute_analysis(session, 4, task, "Competition Analysis")
    
#     def _analyze_business_model(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         context = self._get_layer_context(session, 4)
        
#         task = Task(
#             description=f"""
#             Previous analysis: {context}
            
#             Business model for: {session.user_idea}
#             User input: {user_input}
            
#             Evaluate:
#             1. Revenue model
#             2. Key metrics (CAC, LTV)
#             3. Scalability potential
            
#             Rate confidence (0-1).
#             """,
#             agent=self.strategist,
#             expected_output="Business model analysis"
#         )
        
#         return self._execute_analysis(session, 5, task, "Business Model")
    
#     def _execute_analysis(self, session: AnalysisState, layer: int, task: Task, layer_name: str) -> Dict[str, Any]:
#         """Execute analysis task and update state"""
#         try:
#             # Add delay between API calls to respect rate limits
#             import time
#             time.sleep(2)  # 2 second delay
            
#             crew = Crew(
#                 agents=[task.agent],
#                 tasks=[task],
#                 process=Process.sequential,
#                 verbose=False
#             )
            
#             print(f"🔍 Analyzing {layer_name}...")
#             result = crew.kickoff()
            
#             # Extract data
#             analysis_text = str(result.raw) if hasattr(result, 'raw') else str(result)
#             insights = self._extract_insights(analysis_text)
#             confidence = self._extract_confidence(analysis_text)
#             questions = self._extract_questions(analysis_text)
            
#             # Update state
#             self.state_manager.update_layer(
#                 session.session_id, layer,
#                 {"analysis": analysis_text},
#                 insights, confidence
#             )
            
#             return {
#                 "layer": layer,
#                 "layer_name": layer_name,
#                 "analysis": analysis_text,
#                 "insights": insights,
#                 "confidence": confidence,
#                 "questions": questions,
#                 "status": "completed"
#             }
            
#         except Exception as e:
#             print(f"❌ Error in {layer_name}: {str(e)}")
            
#             # If rate limited, suggest waiting
#             if "RESOURCE_EXHAUSTED" in str(e) or "429" in str(e):
#                 return {
#                     "layer": layer,
#                     "error": "Rate limit hit. Wait 60 seconds and try again.",
#                     "retry_suggestion": "Use: evaluator.analyze(layer=" + str(layer) + ")",
#                     "status": "rate_limited"
#                 }
            
#             return {
#                 "layer": layer,
#                 "error": str(e),
#                 "status": "failed"
#             }
    
#     def get_summary(self, session_id: str) -> Dict[str, Any]:
#         """Get analysis summary"""
#         session = self.state_manager.get_session(session_id)
#         if not session:
#             return {"error": "Session not found"}
        
#         completed_layers = {i: layer for i, layer in session.layers.items() 
#                           if layer.status == "completed"}
        
#         return {
#             "session_id": session_id,
#             "idea": session.user_idea,
#             "overall_confidence": session.overall_confidence,
#             "completed_layers": len(completed_layers),
#             "total_layers": 5,
#             "completion_percentage": (len(completed_layers) / 5) * 100,
#             "layer_insights": {i: layer.insights for i, layer in completed_layers.items()},
#             "summary": self._generate_summary(session)
#         }
    
#     def _generate_summary(self, session: AnalysisState) -> str:
#         """Generate overall summary"""
#         completed = [layer for layer in session.layers.values() if layer.status == "completed"]
#         if not completed:
#             return "No analysis completed yet."
        
#         all_insights = []
#         for layer in completed:
#             all_insights.extend(layer.insights)
        
#         confidence = session.overall_confidence
#         confidence_text = "High" if confidence > 0.7 else "Medium" if confidence > 0.5 else "Low"
        
#         return f"""
#         Analysis Summary for: {session.user_idea}
        
#         Overall Confidence: {confidence_text} ({confidence:.1f})
#         Completed Layers: {len(completed)}/5
        
#         Key Insights:
#         {chr(10).join(f"• {insight}" for insight in all_insights[:10])}
#         """
    
#     # Helper methods
#     def _get_layer_context(self, session: AnalysisState, up_to_layer: int) -> str:
#         context = []
#         for i in range(1, up_to_layer + 1):
#             if session.layers[i].status == "completed":
#                 analysis = session.layers[i].data.get("analysis", "")
#                 context.append(f"Layer {i}: {analysis[:300]}...")
#         return "\n".join(context)
    
#     def _extract_insights(self, text: str) -> List[str]:
#         lines = text.split('\n')
#         insights = []
#         for line in lines:
#             line = line.strip()
#             if line and any(marker in line.lower() for marker in ['•', '-', 'insight', 'key', 'important']):
#                 if len(line) > 20:  # Filter out short lines
#                     insights.append(line)
#         return insights[:5]
    
#     def _extract_confidence(self, text: str) -> float:
#         import re
#         text_lower = text.lower()
        
#         # Look for explicit confidence ratings
#         confidence_patterns = [
#             r'confidence[:\s]*([0-9]*\.?[0-9]+)',
#             r'rating[:\s]*([0-9]*\.?[0-9]+)',
#             r'score[:\s]*([0-9]*\.?[0-9]+)'
#         ]
        
#         for pattern in confidence_patterns:
#             matches = re.findall(pattern, text_lower)
#             if matches:
#                 try:
#                     value = float(matches[0])
#                     return min(value, 1.0) if value <= 1.0 else value / 10.0
#                 except:
#                     continue
        
#         # Default confidence based on text sentiment
#         positive_words = ['strong', 'good', 'excellent', 'promising', 'viable']
#         negative_words = ['weak', 'poor', 'challenging', 'difficult', 'risky']
        
#         positive_count = sum(1 for word in positive_words if word in text_lower)
#         negative_count = sum(1 for word in negative_words if word in text_lower)
        
#         if positive_count > negative_count:
#             return 0.75
#         elif negative_count > positive_count:
#             return 0.45
#         else:
#             return 0.6
    
#     def _extract_questions(self, text: str) -> List[str]:
#         lines = text.split('\n')
#         questions = []
#         for line in lines:
#             if '?' in line and len(line.strip()) > 15:
#                 questions.append(line.strip())
#         return questions[:3]

# # Main Interface - Simplified for hackathon
# class IdeaEvaluator:
#     def __init__(self):
#         self.system = IdeaEvaluationSystem()
#         self.current_session = None
    
#     def start(self, idea: str) -> str:
#         self.current_session = self.system.start_analysis(idea)
#         return f"✅ Started analysis! Session: {self.current_session}"
    
#     def analyze(self, layer: int = None, user_input: str = "") -> Dict[str, Any]:
#         if not self.current_session:
#             return {"error": "Start analysis first with start(idea)"}
        
#         if layer is None:
#             # Analyze layers one by one with delays
#             results = {}
#             for i in range(1, 6):
#                 print(f"\n--- Layer {i} ---")
#                 result = self.system.analyze_layer(self.current_session, i, user_input)
#                 results[i] = result
                
#                 # Stop if rate limited
#                 if result.get("status") == "rate_limited":
#                     print("⏰ Rate limit hit. Try again in 60 seconds.")
#                     break
                    
#                 # Add delay between layers
#                 if i < 5:  # Don't delay after last layer
#                     print("⏱️  Waiting 3 seconds before next layer...")
#                     import time
#                     time.sleep(3)
                    
#             return results
#         else:
#             return self.system.analyze_layer(self.current_session, layer, user_input)
    
#     def summary(self) -> Dict[str, Any]:
#         if not self.current_session:
#             return {"error": "No active session"}
#         return self.system.get_summary(self.current_session)
    
#     def status(self) -> Dict[str, Any]:
#         if not self.current_session:
#             return {"error": "No active session"}
        
#         session = self.system.state_manager.get_session(self.current_session)
#         return {
#             "session_id": self.current_session,
#             "idea": session.user_idea,
#             "current_layer": session.current_layer,
#             "confidence": session.overall_confidence,
#             "completed": sum(1 for l in session.layers.values() if l.status == "completed")
#         }

# # Usage Example
# def demo():
#     """Quick demo for hackathon"""
#     print("🤖 Idea Evaluation System - Hackathon Demo")
#     print("=" * 50)
    
#     evaluator = IdeaEvaluator()
    
#     # Test idea
#     idea = "AI-powered voice assistants for real estate agents"
#     print(f"💡 Testing: {idea}")
    
#     # Start analysis
#     print(evaluator.start(idea))
    
#     # Analyze specific layer
#     print("\n🔍 Analyzing Vision Layer...")
#     result = evaluator.analyze(layer=1, user_input="Focus on the real estate market")
#     print(f"✅ Confidence: {result.get('confidence', 0):.2f}")
    
#     # Get status
#     print("\n📊 Status:")
#     status = evaluator.status()
#     print(f"Completed layers: {status['completed']}/5")
    
#     return evaluator

# if __name__ == "__main__":
#     print("🚀 Hackathon-Ready Idea Evaluator")
#     print("Set GEMINI_API_KEY environment variable")
#     print("Install: pip install crewai google-generativeai langchain-google-genai")
#     print("\nQuick start:")
#     print("evaluator = IdeaEvaluator()")
#     print("evaluator.start('your idea here')")
#     print("evaluator.analyze()")
#     print("evaluator.summary()")
    
#     # Uncomment for demo:
#     demo()



