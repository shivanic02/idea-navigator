# elaborated one 


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




# working one geminie



#     #!/usr/bin/env python3
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
# from crewai import Agent, Task, Crew, Process, LLM # Added LLM
# from crewai.tools import BaseTool
# import time # For delays
# import re   # For parsing retryDelay
# from google.genai.types import Tool, GenerateContentConfig, GoogleSearch


# # Configuration
# class Config:
#     GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-gemini-api-key-here')
#     # IMPORTANT: 'gemini/gemini-1.5-pro' has VERY STRICT free tier limits (2 RPM).
#     # Consider 'gemini/gemini-pro' (60 RPM) for faster free tier execution.
#     MODEL_NAME = 'gemini/gemini-2.5-flash-preview-05-20'
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

# # Utility function for retrying genai calls (for tools)
# def generate_with_retry(model: genai.GenerativeModel, prompt: str, tool_name: str, max_retries: int = 3, default_initial_delay: int = 35) -> str:
#     """
#     Calls model.generate_content with retry logic for rate limiting.
#     Prioritizes retryDelay from error message. default_initial_delay is for gemini-1.5-pro (2 RPM).
#     """
#     current_delay = default_initial_delay
#     for attempt in range(max_retries):
#         try:
#             response = model.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             error_str = str(e)
#             is_rate_limit_error = (
#                 "RESOURCE_EXHAUSTED" in error_str or
#                 "429" in error_str or
#                 "RateLimitError" in e.__class__.__name__ # Check class name too
#             )

#             if not is_rate_limit_error and hasattr(e, '__cause__') and e.__cause__: # Check underlying cause
#                  cause_str = str(e.__cause__)
#                  is_rate_limit_error = is_rate_limit_error or \
#                                        "RESOURCE_EXHAUSTED" in cause_str or \
#                                        "429" in cause_str or \
#                                        "RateLimitError" in e.__cause__.__class__.__name__

#             if is_rate_limit_error:
#                 sleep_duration = current_delay
#                 retry_delay_match = re.search(r'"retryDelay":\s*"(\d+)s"', error_str)
#                 if retry_delay_match:
#                     api_suggested_delay = int(retry_delay_match.group(1))
#                     sleep_duration = max(api_suggested_delay, 15) # Min 15s
#                     print(f"Tool '{tool_name}': API suggested retry delay: {api_suggested_delay}s. Will wait {sleep_duration}s.")
#                 else:
#                     # Exponential backoff for our default if no API suggestion
#                     current_delay = int(current_delay * 1.5)

#                 print(f"Tool '{tool_name}': Rate limit hit. Retrying in {sleep_duration}s... (Attempt {attempt + 1}/{max_retries})")
#                 time.sleep(sleep_duration)

#                 if attempt == max_retries - 1:
#                     final_error_message = f"Tool '{tool_name}': Failed after {max_retries} retries due to rate limiting. Last error: {e}"
#                     print(final_error_message)
#                     raise Exception(final_error_message) from e # Re-raise to be caught by tool's exception handler
#             else:
#                 # Not a rate limit error, re-raise
#                 raise e
#     # Fallback, should be caught by the raise in the loop
#     raise Exception(f"Tool '{tool_name}': Exited retry loop unexpectedly.")


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
#             return generate_with_retry(model, prompt, self.name)
#         except Exception as e:
#             return f"Research unavailable after retries: {str(e)}"

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
#             return generate_with_retry(model, prompt, self.name)
#         except Exception as e:
#             return f"Trend analysis unavailable after retries: {str(e)}"

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
#     gemini_llm = LLM(
#         model=Config.MODEL_NAME,
#         google_api_key=Config.GEMINI_API_KEY,
#         temperature=0.7
#         # We can also pass generation_config to litellm via `config_list` for more control if needed
#         # e.g., by preparing a custom config_list for litellm.
#     )
    
#     market_tool = MarketResearchTool()
#     trend_tool = TrendAnalysisTool()
    
#     strategist = Agent(
#         role='Business Strategist',
#         goal='Analyze business opportunities and strategy',
#         backstory='Expert strategist with deep business analysis experience',
#         verbose=False, # Set to True for detailed CrewAI logs
#         tools=[trend_tool, market_tool],
#         llm=gemini_llm
#     )
    
#     analyst = Agent(
#         role='Market Analyst', 
#         goal='Research markets and validate opportunities',
#         backstory='Senior analyst specializing in market research and validation',
#         verbose=False, # Set to True for detailed CrewAI logs
#         tools=[market_tool],
#         llm=gemini_llm
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
#             session.layers[layer].status = "failed"
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
            
#             Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.8").
#             """,
#             agent=self.strategist,
#             expected_output="Vision analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
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
            
#             Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.7").
#             """,
#             agent=self.strategist,
#             expected_output="Strategic analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
#         )
#         return self._execute_analysis(session, 2, task, "Strategy & Positioning")
    
#     def _analyze_market(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         context = self._get_layer_context(session, 2)
#         task = Task(
#             description=f"""
#             Previous analysis: {context}
            
#             Market validation for: {session.user_idea}
#             User input: {user_input}
            
#             Research using available tools:
#             1. Target customers
#             2. Market size
#             3. Customer needs validation
            
#             Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.9").
#             """,
#             agent=self.analyst,
#             expected_output="Market validation analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
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
            
#             Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.6").
#             """,
#             agent=self.analyst,
#             expected_output="Competitive analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
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
            
#             Provide insights and rate confidence (0-1 scale, e.g., "Confidence: 0.8").
#             """,
#             agent=self.strategist,
#             expected_output="Business model analysis with insights and a clear confidence rating (e.g., Confidence: 0.X)."
#         )
#         return self._execute_analysis(session, 5, task, "Business Model")
    
#     def _execute_analysis(self, session: AnalysisState, layer: int, task: Task, layer_name: str) -> Dict[str, Any]:
#         """Execute analysis task and update state with robust retry logic"""
#         max_crew_retries = 3
#         default_retry_delay_seconds = 60  # Start with 60s for gemini-1.5-pro due to 2 RPM limit

#         for attempt in range(max_crew_retries):
#             try:
#                 crew = Crew(
#                     agents=[task.agent],
#                     tasks=[task],
#                     process=Process.sequential,
#                     verbose=False # Set to True for more CrewAI output if needed
#                 )
                
#                 print(f"🔍 Analyzing {layer_name} (Attempt {attempt + 1}/{max_crew_retries})...")
#                 result = crew.kickoff()
                
#                 analysis_text = str(result.raw) if hasattr(result, 'raw') else str(result)
#                 insights = self._extract_insights(analysis_text)
#                 confidence = self._extract_confidence(analysis_text)
#                 questions = self._extract_questions(analysis_text)
                
#                 self.state_manager.update_layer(
#                     session.session_id, layer,
#                     {"analysis": analysis_text},
#                     insights, confidence
#                 )
                
#                 return {
#                     "layer": layer,
#                     "layer_name": layer_name,
#                     "analysis": analysis_text,
#                     "insights": insights,
#                     "confidence": confidence,
#                     "questions": questions,
#                     "status": "completed"
#                 }
            
#             except Exception as e:
#                 error_str = str(e)
#                 is_rate_limit = (
#                     "RESOURCE_EXHAUSTED" in error_str or 
#                     "429" in error_str or
#                     "RateLimitError" in e.__class__.__name__ # CrewAI might wrap it
#                 )
                
#                 # Check underlying cause if available (e.g., litellm wrapping VertexAIException)
#                 if not is_rate_limit and hasattr(e, '__cause__') and e.__cause__:
#                     cause_str = str(e.__cause__)
#                     is_rate_limit = is_rate_limit or \
#                                    "RESOURCE_EXHAUSTED" in cause_str or \
#                                    "429" in cause_str or \
#                                    "RateLimitError" in e.__cause__.__class__.__name__


#                 if is_rate_limit:
#                     print(f"❌ Rate limit encountered during CrewAI execution for {layer_name}.")
                    
#                     if attempt < max_crew_retries - 1:
#                         current_sleep_duration = default_retry_delay_seconds
                        
#                         retry_delay_match = re.search(r'"retryDelay":\s*"(\d+)s"', error_str)
#                         if retry_delay_match:
#                             api_suggested_delay = int(retry_delay_match.group(1))
#                             current_sleep_duration = max(api_suggested_delay, 30) # Use API delay, min 30s
#                             print(f"API suggested retry delay: {api_suggested_delay}s. Will wait {current_sleep_duration}s.")
#                         else:
#                             # If no specific delay from API, slightly increase our default for the next attempt
#                             default_retry_delay_seconds = int(default_retry_delay_seconds * 1.2)


#                         print(f"Retrying {layer_name} in {current_sleep_duration} seconds... (Next attempt: {attempt + 2}/{max_crew_retries})")
#                         time.sleep(current_sleep_duration)
#                         # continue to the next attempt in the loop
#                     else:
#                         final_error_msg = f"Failed {layer_name} analysis after {max_crew_retries} attempts due to persistent rate limits. Last error: {str(e)}"
#                         print(f"❌ {final_error_msg}")
#                         session.layers[layer].status = "rate_limited"
#                         return {
#                             "layer": layer,
#                             "layer_name": layer_name,
#                             "error": final_error_msg,
#                             "retry_suggestion": f"Wait significantly longer (e.g., 5-10 minutes or check API quota dashboard) and try analyzing this layer again: evaluator.analyze(layer={layer})",
#                             "status": "rate_limited"
#                         }
#                 else:
#                     print(f"❌ Non-rate-limit error in {layer_name}: {str(e)}")
#                     # import traceback # For debugging non-rate-limit errors
#                     # traceback.print_exc()
#                     session.layers[layer].status = "failed"
#                     return {
#                         "layer": layer,
#                         "layer_name": layer_name,
#                         "error": str(e),
#                         "status": "failed"
#                     }
        
#         # Fallback if loop finishes (should be caught by logic above)
#         session.layers[layer].status = "failed"
#         return {
#             "layer": layer,
#             "layer_name": layer_name,
#             "error": "Exited analysis execution loop unexpectedly after all retries.",
#             "status": "failed"
#         }

#     def get_summary(self, session_id: str) -> Dict[str, Any]:
#         session = self.state_manager.get_session(session_id)
#         if not session:
#             return {"error": "Session not found"}
        
#         completed_layers_data = {i: asdict(layer) for i, layer in session.layers.items() 
#                                if layer.status == "completed"}
        
#         return {
#             "session_id": session_id,
#             "idea": session.user_idea,
#             "overall_confidence": session.overall_confidence,
#             "completed_layers_count": len(completed_layers_data),
#             "total_layers": 5,
#             "completion_percentage": (len(completed_layers_data) / 5) * 100,
#             "layer_details": completed_layers_data, # More detailed layer info
#             "summary_text": self._generate_summary_text(session)
#         }
    
#     def _generate_summary_text(self, session: AnalysisState) -> str:
#         completed = [layer for layer in session.layers.values() if layer.status == "completed"]
#         if not completed:
#             return "No analysis completed yet."
        
#         all_insights = []
#         for layer_data in completed:
#             if layer_data.insights:
#                 all_insights.extend(layer_data.insights)
        
#         confidence = session.overall_confidence
#         confidence_text = "High" if confidence > 0.7 else "Medium" if confidence > 0.5 else "Low"
        
#         return f"""
#         Analysis Summary for: {session.user_idea}
        
#         Overall Confidence: {confidence_text} ({confidence:.2f})
#         Completed Layers: {len(completed)}/5
        
#         Key Insights:
#         {chr(10).join(f"• {insight}" for insight in all_insights[:10])}
#         """
    
#     def _get_layer_context(self, session: AnalysisState, up_to_layer: int) -> str:
#         context = []
#         for i in range(1, up_to_layer + 1): # Iterate up to, but not including, the current layer for context
#             if i < up_to_layer and session.layers[i].status == "completed": # Ensure it's actually completed
#                 analysis = session.layers[i].data.get("analysis", "")
#                 context.append(f"Context from Layer {i} ({session.layers[i].data.get('layer_name', 'Unknown')}): {analysis[:200]}...") # Shorter context
#         return "\n".join(context) if context else "No prior context available."
    
#     def _extract_insights(self, text: str) -> List[str]:
#         lines = text.split('\n')
#         insights = []
#         for line in lines:
#             line = line.strip()
#             if line and any(marker in line.lower() for marker in ['•', '-', 'insight', 'key', 'important', '1.', '2.', '3.', '4.']):
#                 # Remove common prefixes like "Insight:", "Key takeaway:" etc.
#                 line = re.sub(r'^(insight|key takeaway|important)\s*[:\-•]*\s*', '', line, flags=re.IGNORECASE)
#                 line = re.sub(r'^[•\-1-9]\.?\s*', '', line) # Remove bullets/numbers
#                 if len(line) > 20:
#                     insights.append(line.strip())
#         return list(set(insights))[:5] # Unique insights, max 5
    
#     def _extract_confidence(self, text: str) -> float:
#         text_lower = text.lower()
#         confidence_patterns = [
#             r'confidence[:\s]*([0-9]*\.?[0-9]+)',
#             r'rating[:\s]*([0-9]*\.?[0-9]+)',
#             r'score[:\s]*([0-9]*\.?[0-9]+)'
#         ]
        
#         for pattern in confidence_patterns:
#             matches = re.findall(pattern, text_lower)
#             if matches:
#                 try:
#                     value = float(matches[-1]) # Take the last found match
#                     return min(value, 1.0) if 0.0 <= value <= 1.0 else (min(value, 10.0) / 10.0 if value > 1.0 else 0.5) # Normalize if out of 0-1
#                 except ValueError:
#                     continue
        
#         positive_words = ['strong', 'good', 'excellent', 'promising', 'viable', 'high confidence']
#         negative_words = ['weak', 'poor', 'challenging', 'difficult', 'risky', 'low confidence']
        
#         positive_count = sum(1 for word in positive_words if word in text_lower)
#         negative_count = sum(1 for word in negative_words if word in text_lower)
        
#         if positive_count > negative_count: return 0.75
#         if negative_count > positive_count: return 0.45
#         return 0.6 # Default if no explicit or strong sentiment
    
#     def _extract_questions(self, text: str) -> List[str]:
#         lines = text.split('\n')
#         questions = []
#         for line in lines:
#             if '?' in line and len(line.strip()) > 15:
#                 questions.append(line.strip())
#         return list(set(questions))[:3] # Unique questions, max 3

# # Main Interface - Simplified for hackathon
# class IdeaEvaluator:
#     def __init__(self):
#         self.system = IdeaEvaluationSystem()
#         self.current_session_id = None # Changed to current_session_id
    
#     def start(self, idea: str) -> str:
#         self.current_session_id = self.system.start_analysis(idea)
#         return f"✅ Started analysis! Session ID: {self.current_session_id}"
    
#     def analyze(self, layer: int = None, user_input: str = "") -> Dict[str, Any]:
#         if not self.current_session_id:
#             return {"error": "Start analysis first with start(idea)"}
        
#         session = self.system.state_manager.get_session(self.current_session_id)
#         if not session: # Should not happen if current_session_id is set
#              return {"error": f"Session {self.current_session_id} not found unexpectedly."}

#         if layer is None:
#             results = {}
#             # For gemini-1.5-pro, a substantial delay between layers is crucial.
#             # Each layer might make 1 (agent) + N (tools) calls. 2 RPM is very restrictive.
#             # If using gemini-pro (60 RPM), this can be much shorter (e.g., 5-10 seconds)
#             INTER_LAYER_DELAY_SECONDS = 65 # At least 60-65 seconds for gemini-1.5-pro to be safe
#             if Config.MODEL_NAME == 'gemini/gemini-pro':
#                 INTER_LAYER_DELAY_SECONDS = 5 # Much shorter for the more permissive model

#             print(f"ℹ️ Using inter-layer delay of {INTER_LAYER_DELAY_SECONDS}s due to model {Config.MODEL_NAME}")

#             for i in range(1, 6):
#                 # Skip already completed layers if we are resuming
#                 if session.layers[i].status == "completed":
#                     print(f"⏭️ Layer {i} ({session.layers[i].data.get('layer_name', 'N/A') if session.layers[i].data else 'N/A'}) already completed. Skipping.")
#                     results[i] = {"status": "skipped_completed", "layer": i, "data": asdict(session.layers[i])}
#                     continue
#                 # Also skip if a previous layer failed hard or was rate limited and not resolved
#                 if i > 1 and session.layers[i-1].status not in ["completed", "skipped_completed"]:
#                     print(f"⚠️ Previous layer {i-1} status is {session.layers[i-1].status}. Stopping sequential analysis.")
#                     results[i] = {"status": "skipped_previous_failed", "layer": i}
#                     break


#                 print(f"\n--- Processing Layer {i} ---")
#                 result = self.system.analyze_layer(self.current_session_id, i, user_input)
#                 results[i] = result
                
#                 if result.get("status") == "rate_limited":
#                     print(f"⏰ Layer {i} hit rate limit, and retries were exhausted. Analysis paused.")
#                     print(f"Suggestion: {result.get('retry_suggestion', 'Wait a few minutes and try analyzing this layer or subsequent layers again.')}")
#                     break 
                    
#                 if result.get("status") == "failed":
#                     print(f"❌ Layer {i} failed with a non-recoverable error. Analysis paused. Error: {result.get('error')}")
#                     break
                    
#                 if i < 5 and result.get("status") == "completed": # Don't delay after the last layer or if layer failed
#                     print(f"✅ Layer {i} completed. Waiting {INTER_LAYER_DELAY_SECONDS} seconds before next layer...")
#                     time.sleep(INTER_LAYER_DELAY_SECONDS)
            
#             # Final summary after all layers attempt
#             print("\n--- Full Analysis Attempt Completed ---")
#             final_summary = self.summary()
#             print(json.dumps(final_summary, indent=2))
#             return {"all_layer_results": results, "final_summary": final_summary}
#         else:
#             # Analyzing a single layer
#             return self.system.analyze_layer(self.current_session_id, layer, user_input)
    
#     def summary(self) -> Dict[str, Any]:
#         if not self.current_session_id:
#             return {"error": "No active session"}
#         return self.system.get_summary(self.current_session_id)
    
#     def status(self) -> Dict[str, Any]:
#         if not self.current_session_id:
#             return {"error": "No active session"}
        
#         session = self.system.state_manager.get_session(self.current_session_id)
#         if not session:
#             return {"error": f"Session {self.current_session_id} not found."}

#         return {
#             "session_id": self.current_session_id,
#             "idea": session.user_idea,
#             "current_layer_processed": session.current_layer, # Layer that was last attempted
#             "overall_confidence": session.overall_confidence,
#             "layers_status": {i: l.status for i, l in session.layers.items()},
#             "completed_layers_count": sum(1 for l in session.layers.values() if l.status == "completed")
#         }

# # Usage Example
# def demo():
#     """Quick demo for hackathon"""
#     print("🤖 Idea Evaluation System - Hackathon Demo")
#     print("==================================================")
    
#     evaluator = IdeaEvaluator()
    
#     # Test idea
#     idea = "Gen-AI-powered assistant that validates your start up idea and goes through market researching using googel searches and analyse the idea from a broder prerspecitve to being specific and narrow."
#     print(f"💡 Testing Idea: {idea}")
    
#     # Start analysis
#     start_message = evaluator.start(idea)
#     print(start_message)
#     if "Error" in start_message: return

#     # Analyze all layers sequentially (this will take a long time with gemini-1.5-pro)
#     # You can also analyze layer by layer:
#     print("\n🔍 Analyzing Vision Layer (Layer 1)...")
#     result_layer1 = evaluator.analyze(layer=1, user_input="Focus on the Gen Z market and ethical fashion trends.")
#     print(json.dumps(result_layer1, indent=2))
#     if result_layer1.get("status") != "completed":
#         print("Stopping demo due to issue in Layer 1.")
#         return

#     # print(f"\n⏱️ Waiting {65} seconds before next layer...")
#     # time.sleep(65)

#     # print("\n🔍 Analyzing Strategy Layer (Layer 2)...")
#     # result_layer2 = evaluator.analyze(layer=2, user_input="Consider a freemium model with premium AI features.")
#     # print(json.dumps(result_layer2, indent=2))
#     # if result_layer2.get("status") != "completed":
#     #     print("Stopping demo due to issue in Layer 2.")
#     #     return

#     # For the demo, let's try to run all layers.
#     print("\n🔍 Analyzing all layers sequentially (this may take a while)...")
#     full_analysis_results = evaluator.analyze() # This will now print its own summary at the end.
#     # print("\n--- Full Analysis Results ---")
#     # print(json.dumps(full_analysis_results, indent=2)) # Already printed by analyze()

#     print("\n📊 Final Status:")
#     status_info = evaluator.status()
#     print(json.dumps(status_info, indent=2))
    
#     print("\n📋 Final Summary:")
#     summary_info = evaluator.summary()
#     print(json.dumps(summary_info, indent=2))
    
#     return evaluator

# if __name__ == "__main__":
#     print("🚀 Hackathon-Ready Idea Evaluator")
#     print("Ensure GEMINI_API_KEY environment variable is set.")
#     print("To use, create an instance and call methods:")
#     print("  evaluator = IdeaEvaluator()")
#     print("  evaluator.start('your amazing tech idea')")
#     print("  # To analyze a specific layer:")
#     print("  # result_layer1 = evaluator.analyze(layer=1, user_input='Focus on B2B market')")
#     print("  # print(result_layer1)")
#     print("  # To analyze all layers sequentially (WARNING: SLOW with gemini-1.5-pro free tier):")
#     print("  # full_results = evaluator.analyze()")
#     print("  # print(full_results)")
#     print("  summary = evaluator.summary()")
#     print("  print(summary)")
#     print("-" * 50)
    
#     # Uncomment to run the demo:
#     print("\nStarting Demo...")
#     demo_evaluator = demo()
#     print("\nDemo Finished.")

#     # Interactive Usage Example:
#     # evaluator = IdeaEvaluator()
#     # my_idea = input("Enter your idea: ")
#     # evaluator.start(my_idea)
#     # for i in range(1,6):
#     #     print(f"\nAnalyzing layer {i}...")
#     #     user_c = input(f"Any specific input for layer {i}? (Press Enter for none): ")
#     #     res = evaluator.analyze(layer=i, user_input=user_c)
#     #     print(json.dumps(res, indent=2))
#     #     if res.get("status") != "completed":
#     #         print(f"Layer {i} did not complete. Stopping.")
#     #         break
#     #     if i < 5 :
#     #         delay = 65 if Config.MODEL_NAME == 'gemini/gemini-1.5-pro' else 5
#     #         print(f"Waiting {delay}s for next layer...")
#     #         time.sleep(delay)
#     # print("\nFinal Summary:")
#     # print(json.dumps(evaluator.summary(), indent=2))














# #!/usr/bin/env python3
# """
# Idea Evaluation Agentic System - Hackathon MVP
# A multi-agent system for comprehensive idea analysis using CrewAI, Google Gemini, and Serper.
# """

# import os
# import json
# import uuid
# from datetime import datetime
# from typing import Dict, List, Any, Optional
# from dataclasses import dataclass, asdict
# import google.generativeai as genai
# from crewai import Agent, Task, Crew, Process, LLM
# from crewai.tools import BaseTool
# import time # For delays
# import re   # For parsing retryDelay
# from google.genai.types import Tool as GoogleGenAITool, GenerateContentConfig # Renamed to avoid conflict with crewai.Tool
# # Removed GoogleSearch as we are implementing Serper

# import requests # For Serper API calls

# # Configuration
# class Config:
#     GEMINI_API_KEY = os.getenv('GEMINI_API_KEY', 'your-gemini-api-key-here')
#     SERPER_API_KEY = os.getenv('SERPER_API_KEY', 'your-serper-api-key-here') # Added Serper API Key
#     # IMPORTANT: 'gemini/gemini-1.5-pro' has VERY STRICT free tier limits (2 RPM).
#     # Consider 'gemini/gemini-pro' (60 RPM) for faster free tier execution.
#     MODEL_NAME = 'gemini/gemini-2.5-flash-preview-05-20' # Corrected model name if there was a typo
#     CONFIDENCE_THRESHOLD = 0.7

# # Initialize Gemini
# if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != 'your-gemini-api-key-here':
#     genai.configure(api_key=Config.GEMINI_API_KEY)
#     os.environ['GOOGLE_API_KEY'] = Config.GEMINI_API_KEY # For CrewAI LiteLLM
# else:
#     print("Warning: GEMINI_API_KEY not found or is placeholder. Gemini-based features might not work.")

# if not Config.SERPER_API_KEY or Config.SERPER_API_KEY == 'your-serper-api-key-here':
#     print("Warning: SERPER_API_KEY not found or is placeholder. SerperSearchTool will not work.")


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

# # Utility function for retrying genai calls (for tools)
# def generate_with_retry(model: genai.GenerativeModel, prompt: str, tool_name: str, max_retries: int = 3, default_initial_delay: int = 35) -> str:
#     """
#     Calls model.generate_content with retry logic for rate limiting.
#     Prioritizes retryDelay from error message. default_initial_delay is for gemini-1.5-pro (2 RPM).
#     """
#     if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY == 'your-gemini-api-key-here':
#         return f"Tool '{tool_name}': Cannot execute. GEMINI_API_KEY is not configured."

#     current_delay = default_initial_delay
#     for attempt in range(max_retries):
#         try:
#             response = model.generate_content(prompt)
#             return response.text
#         except Exception as e:
#             error_str = str(e)
#             is_rate_limit_error = (
#                 "RESOURCE_EXHAUSTED" in error_str or
#                 "429" in error_str or
#                 "RateLimitError" in e.__class__.__name__ # Check class name too
#             )

#             if not is_rate_limit_error and hasattr(e, '__cause__') and e.__cause__: # Check underlying cause
#                  cause_str = str(e.__cause__)
#                  is_rate_limit_error = is_rate_limit_error or \
#                                        "RESOURCE_EXHAUSTED" in cause_str or \
#                                        "429" in cause_str or \
#                                        "RateLimitError" in e.__cause__.__class__.__name__

#             if is_rate_limit_error:
#                 sleep_duration = current_delay
#                 retry_delay_match = re.search(r'"retryDelay":\s*"(\d+)s"', error_str)
#                 if retry_delay_match:
#                     api_suggested_delay = int(retry_delay_match.group(1))
#                     sleep_duration = max(api_suggested_delay, 15) # Min 15s
#                     print(f"Tool '{tool_name}': API suggested retry delay: {api_suggested_delay}s. Will wait {sleep_duration}s.")
#                 else:
#                     # Exponential backoff for our default if no API suggestion
#                     current_delay = int(current_delay * 1.5)

#                 print(f"Tool '{tool_name}': Rate limit hit. Retrying in {sleep_duration}s... (Attempt {attempt + 1}/{max_retries})")
#                 time.sleep(sleep_duration)

#                 if attempt == max_retries - 1:
#                     final_error_message = f"Tool '{tool_name}': Failed after {max_retries} retries due to rate limiting. Last error: {e}"
#                     print(final_error_message)
#                     # Return error message instead of raising to allow agent to handle it
#                     return f"Tool '{tool_name}': Research unavailable after retries due to rate limiting: {str(e)}"
#             else:
#                 # Not a rate limit error, re-raise
#                 print(f"Tool '{tool_name}': Non-rate limit error: {e}")
#                 return f"Tool '{tool_name}': Research failed with non-rate-limit error: {str(e)}"
#     # Fallback, should be caught by the return in the loop
#     return f"Tool '{tool_name}': Exited retry loop unexpectedly."


# # Custom Tools
# class SerperSearchTool(BaseTool):
#     name: str = "internet_search"
#     description: str = (
#         "Performs a real-time internet search using Google via Serper API. "
#         "Input should be a concise search query. "
#         "Useful for finding current events, specific facts, market data, competitor information, "
#         "product reviews, or any other information available on the public internet."
#     )

#     def _run(self, query: str) -> str:
#         if not Config.SERPER_API_KEY or Config.SERPER_API_KEY == 'your-serper-api-key-here':
#             return "Serper API key not configured. Internet search is unavailable."

#         url = "https://google.serper.dev/search"
#         payload = json.dumps({"q": query})
#         headers = {
#             'X-API-KEY': Config.SERPER_API_KEY,
#             'Content-Type': 'application/json'
#         }
        
#         results_string = f"Search results for query: '{query}'\n"
#         max_results_to_process = 5 # Limit number of results to keep context concise

#         try:
#             response = requests.post(url, headers=headers, data=payload, timeout=10)
#             response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)
            
#             search_results = response.json()
            
#             if not search_results:
#                 return f"{results_string}No information found."

#             # Answer Box
#             if "answerBox" in search_results and search_results["answerBox"]:
#                 ab = search_results["answerBox"]
#                 title = ab.get("title", "")
#                 answer = ab.get("answer") or ab.get("snippet")
#                 if answer:
#                     results_string += f"\nAnswer Box: {title}\n{answer}\n"
            
#             # Knowledge Graph
#             if "knowledgeGraph" in search_results and search_results["knowledgeGraph"]:
#                 kg = search_results["knowledgeGraph"]
#                 title = kg.get("title", "")
#                 description = kg.get("description", "")
#                 if title and description:
#                     results_string += f"\nKnowledge Graph: {title}\n{description}\n"
#                     if kg.get("attributes"):
#                         results_string += "Attributes:\n"
#                         for attr, val in kg["attributes"].items():
#                              results_string += f"  - {attr}: {val}\n"


#             # Organic Results
#             if "organic" in search_results and search_results["organic"]:
#                 results_string += "\nOrganic Search Results:\n"
#                 for i, result in enumerate(search_results["organic"][:max_results_to_process]):
#                     title = result.get("title", "N/A")
#                     link = result.get("link", "N/A")
#                     snippet = result.get("snippet", "N/A")
#                     results_string += f"{i+1}. Title: {title}\n   Link: {link}\n   Snippet: {snippet}\n\n"
            
#             if len(results_string) == len(f"Search results for query: '{query}'\n"): # No useful data added
#                 return f"{results_string}No specific organic results, answer box, or knowledge graph found."

#             return results_string.strip()

#         except requests.exceptions.Timeout:
#             return f"Error: Search query timed out for '{query}'."
#         except requests.exceptions.HTTPError as e:
#             return f"Error: HTTP error during search for '{query}': {e.response.status_code} - {e.response.text}"
#         except requests.exceptions.RequestException as e:
#             return f"Error: Failed to perform search for '{query}': {str(e)}"
#         except Exception as e:
#             return f"An unexpected error occurred while searching for '{query}': {str(e)}"


# class MarketResearchTool(BaseTool):
#     name: str = "llm_market_research_synthesis" # Renamed to clarify its function
#     description: str = (
#         "Synthesizes market data and competitive information based on a query, using its internal knowledge. "
#         "This tool does NOT perform live web searches. Use 'internet_search' for real-time data. "
#         "Use this tool to get a general overview, identify potential areas for deeper live search, or to brainstorm."
#     )
    
#     def _run(self, query: str) -> str:
#         try:
#             model = genai.GenerativeModel(Config.MODEL_NAME)
#             prompt = f"""
#             Based on general knowledge, provide a synthesized analysis for: {query}
            
#             Include insights on:
#             1. Potential market trends and data points (general understanding)
#             2. Possible key competitor archetypes or examples
#             3. Broad market size considerations
#             4. General growth opportunities
            
#             Keep response concise but insightful. State that this is based on general knowledge and not live data.
#             """
#             return generate_with_retry(model, prompt, self.name)
#         except Exception as e: # Should be caught by generate_with_retry, but as a fallback
#             return f"LLM-based Market Research unavailable: {str(e)}"

# class TrendAnalysisTool(BaseTool):
#     name: str = "llm_trend_analysis_synthesis" # Renamed
#     description: str = (
#         "Analyzes potential future trends relevant to an idea using its internal knowledge. "
#         "This tool does NOT perform live web searches. Use 'internet_search' for real-time trend data. "
#         "Use this tool for brainstorming future scenarios or understanding broad technological and market shifts."
#     )
    
#     def _run(self, idea: str) -> str:
#         try:
#             model = genai.GenerativeModel(Config.MODEL_NAME)
#             prompt = f"""
#             Based on general knowledge, analyze potential future trends for: {idea}
            
#             Focus on:
#             1. Broad technology trends
#             2. Potential market shifts
#             3. Possible user behavior changes
#             4. General opportunities and threats based on these trends
            
#             Provide specific, actionable insights based on general understanding. State that this is based on general knowledge and not live data.
#             """
#             return generate_with_retry(model, prompt, self.name)
#         except Exception as e: # Should be caught by generate_with_retry
#             return f"LLM-based Trend analysis unavailable: {str(e)}"


# # State Management - Simplified
# class StateManager:
#     def __init__(self):
#         self.sessions = {}
    
#     def create_session(self, user_idea: str) -> str:
#         session_id = str(uuid.uuid4())[:8]
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

# # Agent Creation
# def create_agents():
#     gemini_llm = LLM(
#         model=Config.MODEL_NAME, # Corrected parameter name based on CrewAI documentation
#         # google_api_key=Config.GEMINI_API_KEY, # GOOGLE_API_KEY env var is used by LiteLLM
#         temperature=0.7
#     )
    
#     # Instantiate all tools
#     serper_search_tool = SerperSearchTool()
#     llm_market_tool = MarketResearchTool() # Using renamed tool
#     llm_trend_tool = TrendAnalysisTool()   # Using renamed tool
    
#     strategist = Agent(
#         role='Business Strategist',
#         goal='Analyze business opportunities, strategy, and business models for new ideas. Leverage real-time internet search for current data and LLM synthesis for broader concepts.',
#         backstory='Expert strategist with deep business analysis experience, adept at combining real-time data with strategic foresight.',
#         verbose=False,
#         tools=[llm_trend_tool, llm_market_tool, serper_search_tool], # Added Serper tool
#         llm=gemini_llm,
#         allow_delegation=False # For simplicity in hackathon
#     )
    
#     analyst = Agent(
#         role='Market Analyst', 
#         goal='Research markets, validate opportunities, and analyze competition. Prioritize real-time internet search for factual data and competitor information.',
#         backstory='Senior analyst specializing in market research and validation, skilled in using web search for up-to-date insights.',
#         verbose=False,
#         tools=[llm_market_tool, serper_search_tool], # Added Serper tool, llm_market_tool is secondary
#         llm=gemini_llm,
#         allow_delegation=False
#     )
    
#     return strategist, analyst

# # Core Analysis System
# class IdeaEvaluationSystem:
#     def __init__(self):
#         self.state_manager = StateManager()
#         if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != 'your-gemini-api-key-here':
#             self.strategist, self.analyst = create_agents()
#         else:
#             print("Critical: Agents not created due to missing GEMINI_API_KEY. System will not function correctly.")
#             self.strategist, self.analyst = None, None # Or handle more gracefully
        
#     def start_analysis(self, user_idea: str) -> str:
#         if not self.strategist or not self.analyst:
#              return "Error: System not initialized properly due to missing API keys. Cannot start analysis."
#         session_id = self.state_manager.create_session(user_idea)
#         print(f"🚀 Starting analysis: '{user_idea[:50]}...'")
#         print(f"📋 Session: {session_id}")
#         return session_id
    
#     def analyze_layer(self, session_id: str, layer: int, user_input: str = "") -> Dict[str, Any]:
#         if not self.strategist or not self.analyst:
#              return {"error": "System not initialized properly. Agents are not available."}

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
#             session.layers[layer].status = "failed"
#             return {"error": f"Layer {layer} not implemented"}
    
#     def _analyze_vision(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         task = Task(
#             description=f"""
#             Analyze the vision and opportunity for the user's idea: "{session.user_idea}"
#             Additional context from user: "{user_input}"
            
#             Evaluate:
#             1. What core problem does this idea aim to solve?
#             2. What current trends (social, technological, economic) might support or challenge this idea? (Use internet_search for recent trends if needed).
#             3. What is the potential scale or size of the opportunity? (Provide a qualitative assessment).
            
#             Provide actionable insights and rate your confidence in this vision on a scale of 0.0 to 1.0 (e.g., "Confidence: 0.8").
#             Clearly state if you used the 'internet_search' tool for any specific findings.
#             """,
#             agent=self.strategist,
#             expected_output="A concise analysis of the idea's vision and opportunity, key supporting/challenging trends, qualitative opportunity size, actionable insights, and a clear confidence rating (e.g., Confidence: 0.X). Mention if internet search was used."
#         )
#         return self._execute_analysis(session, 1, task, "Vision & Opportunity")
    
#     def _analyze_strategy(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         context = self._get_layer_context(session, 1)
#         task = Task(
#             description=f"""
#             Based on the user's idea: "{session.user_idea}" and previous analysis:
#             {context}
#             User input for this layer: "{user_input}"
            
#             Develop a high-level strategy:
#             1. How should this idea be strategically positioned in the market?
#             2. Is the market timing favorable, or what factors affect timing? (Use internet_search for recent market signals if needed).
#             3. What are potential unique selling propositions or competitive advantages?
            
#             Provide actionable insights and rate your confidence (0-1 scale, e.g., "Confidence: 0.7").
#             Clearly state if you used the 'internet_search' tool.
#             """,
#             agent=self.strategist,
#             expected_output="Strategic analysis focusing on positioning, market timing, and competitive advantages, with insights and a confidence rating (e.g., Confidence: 0.X). Mention if internet search was used."
#         )
#         return self._execute_analysis(session, 2, task, "Strategy & Positioning")
    
#     def _analyze_market(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         context = self._get_layer_context(session, 2)
#         task = Task(
#             description=f"""
#             For the idea: "{session.user_idea}", considering previous analysis:
#             {context}
#             User input for this layer: "{user_input}"
            
#             Validate the market. You MUST use the 'internet_search' tool to find supporting data for the following, then synthesize:
#             1. Identify and describe the primary target customer segments.
#             2. Find any available data or estimations on the market size for these segments.
#             3. Search for evidence validating the needs of these target customers related to the idea.
            
#             Provide actionable insights, cite sources or search queries used, and rate confidence (0-1 scale, e.g., "Confidence: 0.9").
#             """,
#             agent=self.analyst,
#             expected_output="Market validation analysis including target customers, market size estimations (with sources/queries if found via search), customer needs validation, insights, and a confidence rating (e.g., Confidence: 0.X)."
#         )
#         return self._execute_analysis(session, 3, task, "Market Validation")
    
#     def _analyze_competition(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         context = self._get_layer_context(session, 3)
#         task = Task(
#             description=f"""
#             For the idea: "{session.user_idea}", considering previous analysis:
#             {context}
#             User input for this layer: "{user_input}"
            
#             Analyze the competitive landscape. You MUST use the 'internet_search' tool to identify competitors:
#             1. Identify 2-3 key direct and indirect competitors.
#             2. For each, briefly note their strengths and weaknesses.
#             3. What opportunities exist for differentiation against these competitors?
            
#             Provide actionable insights, cite search queries or specific competitors found, and rate confidence (0-1 scale, e.g., "Confidence: 0.6").
#             """,
#             agent=self.analyst,
#             expected_output="Competitive analysis identifying key competitors (with specifics if found via search), their S&W, differentiation opportunities, insights, and a confidence rating (e.g., Confidence: 0.X)."
#         )
#         return self._execute_analysis(session, 4, task, "Competition Analysis")
    
#     def _analyze_business_model(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
#         context = self._get_layer_context(session, 4)
#         task = Task(
#             description=f"""
#             For the idea: "{session.user_idea}", considering previous analysis:
#             {context}
#             User input for this layer: "{user_input}"
            
#             Outline a potential business model:
#             1. Suggest 1-2 viable revenue models (e.g., subscription, freemium, transaction fees).
#             2. What are the key metrics to track for success (e.g., CAC, LTV, churn)? (Use internet_search if specific industry metrics are relevant).
#             3. Assess the scalability potential of this business model.
            
#             Provide actionable insights and rate confidence (0-1 scale, e.g., "Confidence: 0.8").
#             Clearly state if you used the 'internet_search' tool.
#             """,
#             agent=self.strategist,
#             expected_output="Business model analysis suggesting revenue models, key metrics, scalability assessment, insights, and a confidence rating (e.g., Confidence: 0.X). Mention if internet search was used."
#         )
#         return self._execute_analysis(session, 5, task, "Business Model")
    
#     def _execute_analysis(self, session: AnalysisState, layer: int, task: Task, layer_name: str) -> Dict[str, Any]:
#         """Execute analysis task and update state with robust retry logic"""
#         max_crew_retries = 2 # Reduced retries as tool retries are separate
#         # default_retry_delay_seconds = 60 if Config.MODEL_NAME == 'gemini/gemini-1.5-pro' else 10 # For CrewAI level retries
#         # Use a slightly shorter delay for CrewAI-level retries, as tool-level retries handle the stricter Gemini limits
#         default_retry_delay_seconds = 35 
#         if 'flash' in Config.MODEL_NAME or 'pro' == Config.MODEL_NAME.split('/')[-1]: # gemini-pro or flash
#             default_retry_delay_seconds = 10


#         for attempt in range(max_crew_retries):
#             try:
#                 # Ensure agent is available for the task
#                 if not task.agent:
#                     error_msg = f"Agent for task '{task.description[:50]}...' is None. Cannot execute."
#                     print(f"❌ {error_msg}")
#                     session.layers[layer].status = "failed"
#                     return { "layer": layer, "layer_name": layer_name, "error": error_msg, "status": "failed" }

#                 crew = Crew(
#                     agents=[task.agent],
#                     tasks=[task],
#                     process=Process.sequential,
#                     verbose=False # Set to True for more CrewAI output if needed
#                 )
                
#                 print(f"🔍 Analyzing {layer_name} (Crew Kickoff Attempt {attempt + 1}/{max_crew_retries})...")
#                 # result = crew.kickoff() # This is the old way, now returns a richer object.
#                 # For newer CrewAI, result might be an object with attributes like `raw` or `result`.
#                 # Let's assume `crew.kickoff()` returns a string or an object that can be stringified.
#                 # If it returns a `TaskOutput` object, `result.exported_output` or `result.raw_output` is often used.
#                 # Let's assume for now `kickoff` returns a string or an object whose string representation is the main output.
                
#                 output = crew.kickoff() # This is the primary method.
                
#                 # The output of kickoff() can vary. Often it's a string, or an object
#                 # from which you extract the string (e.g., result.raw, result.description for TaskOutput)
#                 # Let's try to be robust:
#                 analysis_text = ""
#                 if isinstance(output, str):
#                     analysis_text = output
#                 elif hasattr(output, 'raw_output') and output.raw_output: # New CrewAI TaskOutput
#                     analysis_text = output.raw_output
#                 elif hasattr(output, 'result') and output.result: # Another common pattern
#                      analysis_text = output.result
#                 elif hasattr(output, 'raw') and output.raw: # Older CrewAI
#                     analysis_text = output.raw
#                 else: # Fallback
#                     analysis_text = str(output)


#                 if not analysis_text or analysis_text.strip() == "":
#                     print(f"⚠️ Warning: CrewAI kickoff for {layer_name} returned empty or whitespace-only result. Output: '{output}'")
#                     # Consider this a failure or handle as appropriate
#                     analysis_text = "No substantive analysis was generated by the agent."


#                 insights = self._extract_insights(analysis_text)
#                 confidence = self._extract_confidence(analysis_text)
#                 questions = self._extract_questions(analysis_text)
                
#                 self.state_manager.update_layer(
#                     session.session_id, layer,
#                     {"analysis": analysis_text, "layer_name": layer_name}, # Added layer_name here
#                     insights, confidence
#                 )
                
#                 return {
#                     "layer": layer,
#                     "layer_name": layer_name,
#                     "analysis": analysis_text,
#                     "insights": insights,
#                     "confidence": confidence,
#                     "questions": questions,
#                     "status": "completed"
#                 }
            
#             except Exception as e:
#                 error_str = str(e)
#                 # Enhanced rate limit detection
#                 is_rate_limit = "rate limit" in error_str.lower() or \
#                                 "resourcemanager.projects.get" in error_str.lower() or \
#                                 "RESOURCE_EXHAUSTED" in error_str or \
#                                 "429" in error_str or \
#                                 "RateLimitError" in e.__class__.__name__

#                 if not is_rate_limit and hasattr(e, '__cause__') and e.__cause__:
#                     cause_str = str(e.__cause__)
#                     is_rate_limit = is_rate_limit or \
#                                    "RESOURCE_EXHAUSTED" in cause_str or \
#                                    "429" in cause_str or \
#                                    "RateLimitError" in e.__cause__.__class__.__name__ or \
#                                    "rate limit" in cause_str.lower()


#                 if is_rate_limit:
#                     print(f"❌ Rate limit encountered during CrewAI execution for {layer_name}.")
                    
#                     if attempt < max_crew_retries - 1:
#                         current_sleep_duration = default_retry_delay_seconds
                        
#                         retry_delay_match = re.search(r'"retryDelay":\s*"(\d+)s"', error_str) # For Gemini errors
#                         api_suggested_match_google = re.search(r'retry after (\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z)', error_str) # Google specific format

#                         if retry_delay_match:
#                             api_suggested_delay_seconds = int(retry_delay_match.group(1))
#                             current_sleep_duration = max(api_suggested_delay_seconds, 15) # Min 15s
#                             print(f"API (JSON retryDelay) suggested retry delay: {api_suggested_delay_seconds}s. Will wait {current_sleep_duration}s.")
#                         elif api_suggested_match_google:
#                             retry_time_str = api_suggested_match_google.group(1)
#                             try:
#                                 retry_time_dt = datetime.strptime(retry_time_str.split('.')[0] + 'Z', "%Y-%m-%dT%H:%M:%SZ") # Handling potential fractional seconds
#                                 wait_seconds = (retry_time_dt - datetime.utcnow()).total_seconds() + 5 # add 5s buffer
#                                 current_sleep_duration = max(int(wait_seconds), 15)
#                                 print(f"API (Google text) suggested retry after {retry_time_str}. Will wait {current_sleep_duration}s.")
#                             except ValueError:
#                                 print(f"Could not parse retry timestamp: {retry_time_str}. Using default backoff.")
#                                 current_sleep_duration = int(default_retry_delay_seconds * (1.5 ** attempt))
#                         else:
#                             # Exponential backoff if no specific delay from API
#                             current_sleep_duration = int(default_retry_delay_seconds * (1.5 ** attempt))
#                             print(f"No specific API retry delay found. Using exponential backoff: {current_sleep_duration}s.")


#                         print(f"Retrying {layer_name} in {current_sleep_duration} seconds... (Next attempt: {attempt + 2}/{max_crew_retries})")
#                         time.sleep(current_sleep_duration)
#                     else:
#                         final_error_msg = f"Failed {layer_name} analysis after {max_crew_retries} attempts due to persistent rate limits. Last error: {str(e)}"
#                         print(f"❌ {final_error_msg}")
#                         session.layers[layer].status = "rate_limited"
#                         return {
#                             "layer": layer,
#                             "layer_name": layer_name,
#                             "error": final_error_msg,
#                             "retry_suggestion": f"Wait significantly longer (e.g., 5-10 minutes or check API quota dashboard) and try analyzing this layer again: evaluator.analyze(layer={layer})",
#                             "status": "rate_limited"
#                         }
#                 else:
#                     # This handles other errors, e.g. API key not valid for project, permission errors etc.
#                     detailed_error = f"Non-rate-limit error in {layer_name} (Attempt {attempt + 1}): {str(e)}"
#                     # import traceback # For deeper debugging
#                     # traceback.print_exc()
#                     print(f"❌ {detailed_error}")
                    
#                     # If it's the last attempt, then fail the layer
#                     if attempt == max_crew_retries - 1:
#                         session.layers[layer].status = "failed"
#                         return {
#                             "layer": layer,
#                             "layer_name": layer_name,
#                             "error": detailed_error,
#                             "status": "failed"
#                         }
#                     # If not the last attempt, maybe a short delay and retry for transient non-rate-limit issues?
#                     # For now, let's fail fast on non-rate-limit errors unless we want to retry them too.
#                     # If we want to retry, add a short sleep and continue:
#                     # print(f"Retrying {layer_name} after non-rate-limit error in 10s...")
#                     # time.sleep(10)
#                     # continue
#                     # For now, let's just propagate the error if it's not a rate limit.
#                     session.layers[layer].status = "failed"
#                     return {
#                         "layer": layer,
#                         "layer_name": layer_name,
#                         "error": detailed_error, # Return the error from the first non-rate-limit failure
#                         "status": "failed"
#                     }

#         # Fallback if loop finishes (should be caught by logic above)
#         session.layers[layer].status = "failed"
#         return {
#             "layer": layer,
#             "layer_name": layer_name,
#             "error": "Exited analysis execution loop unexpectedly after all retries.",
#             "status": "failed"
#         }

#     def get_summary(self, session_id: str) -> Dict[str, Any]:
#         session = self.state_manager.get_session(session_id)
#         if not session:
#             return {"error": "Session not found"}
        
#         completed_layers_data = {
#             i: asdict(layer) for i, layer in session.layers.items() 
#             if layer.status == "completed" and layer.data # Ensure data exists
#         }
        
#         return {
#             "session_id": session_id,
#             "idea": session.user_idea,
#             "overall_confidence": session.overall_confidence,
#             "completed_layers_count": len(completed_layers_data),
#             "total_layers": 5,
#             "completion_percentage": (len(completed_layers_data) / 5) * 100,
#             "layer_details": completed_layers_data,
#             "summary_text": self._generate_summary_text(session)
#         }
    
#     def _generate_summary_text(self, session: AnalysisState) -> str:
#         completed = [layer for layer_id, layer in sorted(session.layers.items()) if layer.status == "completed" and layer.data]
#         if not completed:
#             return "No analysis completed yet."
        
#         summary_parts = [f"Analysis Summary for: {session.user_idea}\n"]
        
#         confidence = session.overall_confidence
#         confidence_text = "High" if confidence > 0.7 else "Medium" if confidence > 0.5 else "Low"
#         summary_parts.append(f"Overall Confidence: {confidence_text} ({confidence:.2f})")
#         summary_parts.append(f"Completed Layers: {len(completed)}/5\n")
        
#         summary_parts.append("Key Insights per Layer:")
#         for i, layer_data in enumerate(completed):
#             layer_num = [k for k, v in session.layers.items() if v == layer_data][0] # Get original layer number
#             layer_name = layer_data.data.get('layer_name', f'Layer {layer_num}')
#             summary_parts.append(f"\n--- {layer_name} (Confidence: {layer_data.confidence:.2f}) ---")
#             if layer_data.insights:
#                 for insight in layer_data.insights:
#                     summary_parts.append(f"• {insight}")
#             else:
#                 summary_parts.append("No specific insights extracted for this layer.")
        
#         return "\n".join(summary_parts)
    
#     def _get_layer_context(self, session: AnalysisState, up_to_layer: int) -> str:
#         context = []
#         # Iterate from layer 1 up to (but not including) the current layer
#         for i in range(1, up_to_layer): 
#             if session.layers[i].status == "completed" and session.layers[i].data:
#                 analysis = session.layers[i].data.get("analysis", "")
#                 layer_name_from_data = session.layers[i].data.get("layer_name", f"Layer {i}") # Get layer name from stored data
#                 # Shorter context, focusing on insights if available
#                 insights_text = "; ".join(session.layers[i].insights) if session.layers[i].insights else "N/A"
#                 context.append(f"Summary from {layer_name_from_data}: Confidence {session.layers[i].confidence:.2f}. Key Insights: {insights_text}. Analysis snippet: {analysis[:150]}...")
#             elif session.layers[i].status != "pending": # Include info about non-completed prior layers
#                  context.append(f"Note: Layer {i} ({session.layers[i].data.get('layer_name', 'Unknown') if session.layers[i].data else 'Unknown'}) was not successfully completed (status: {session.layers[i].status}).")

#         return "\n".join(context) if context else "No prior completed layer context available."

    
#     def _extract_insights(self, text: str) -> List[str]:
#         lines = text.split('\n')
#         insights = []
#         # More robust extraction logic
#         for line in lines:
#             line = line.strip()
#             # Check for bullet points or numbered lists that aren't questions
#             if re.match(r'^[•*-]\s+|^[1-9][\.\)]\s+', line) and '?' not in line:
#                 # Remove common prefixes and bullets/numbers
#                 processed_line = re.sub(r'^(insight|key takeaway|important|actionable insight|finding)\s*[:\-•*]*\s*', '', line, flags=re.IGNORECASE)
#                 processed_line = re.sub(r'^[•*\-1-9][\.\)]?\s*', '', processed_line).strip()
#                 if len(processed_line) > 20 and len(processed_line) < 300: # Filter for meaningful length
#                     insights.append(processed_line)
#             # Check for sentences explicitly marked as insights/conclusions if not caught by bullets
#             elif any(marker in line.lower() for marker in ["key insight:", "conclusion:", "finding:"]) and len(line) > 30:
#                 processed_line = re.sub(r'^(key insight:|conclusion:|finding:)\s*', '', line, flags=re.IGNORECASE).strip()
#                 if len(processed_line) > 20 and len(processed_line) < 300:
#                     insights.append(processed_line)

#         # Fallback if no structured insights: look for declarative sentences in summaries
#         if not insights and "summary:" in text.lower():
#             summary_section = text.lower().split("summary:", 1)[-1]
#             sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', summary_section) # sentence tokenizer
#             for sentence in sentences:
#                 sentence = sentence.strip()
#                 if len(sentence) > 20 and len(sentence) < 200 and '?' not in sentence:
#                     insights.append(sentence.capitalize())
        
#         unique_insights = list(dict.fromkeys(insights)) # Preserve order while making unique
#         return unique_insights[:5] # Max 5
    
#     def _extract_confidence(self, text: str) -> float:
#         text_lower = text.lower()
#         # Prioritize explicit "Confidence: X.Y"
#         explicit_confidence_match = re.search(r'confidence[:\s]*([0-1]?\.[0-9]+|[0-1])', text_lower)
#         if explicit_confidence_match:
#             try:
#                 return float(explicit_confidence_match.group(1))
#             except ValueError:
#                 pass
        
#         # Look for other ratings/scores if explicit confidence is not found
#         rating_patterns = [
#             r'rating[:\s]*([0-1]?\.[0-9]+|[0-1])', # 0.0 to 1.0
#             r'score[:\s]*([0-1]?\.[0-9]+|[0-1])',   # 0.0 to 1.0
#             r'confidence level[:\s]*([0-1]?\.[0-9]+|[0-1])'
#         ]
#         for pattern in rating_patterns:
#             matches = re.findall(pattern, text_lower)
#             if matches:
#                 try:
#                     value = float(matches[-1]) # Take the last found match
#                     return min(max(value, 0.0), 1.0) # Clamp to 0.0-1.0
#                 except ValueError:
#                     continue
        
#         # Fallback to keyword sentiment if no numeric score
#         # (Simplified: could be much more sophisticated)
#         high_confidence_keywords = ['very confident', 'high confidence', 'strong case', 'highly likely', 'excellent prospect']
#         medium_confidence_keywords = ['moderately confident', 'medium confidence', 'promising', 'likely', 'good chance']
#         low_confidence_keywords = ['low confidence', 'uncertain', 'risky', 'challenging', 'unlikely', 'significant hurdles']

#         if any(kw in text_lower for kw in high_confidence_keywords): return 0.85
#         if any(kw in text_lower for kw in medium_confidence_keywords): return 0.65
#         if any(kw in text_lower for kw in low_confidence_keywords): return 0.35
        
#         return 0.5 # Default if nothing specific found
    
#     def _extract_questions(self, text: str) -> List[str]:
#         # Regex to find full sentences ending with a question mark
#         # It tries to avoid splitting mid-sentence if there are other punctuation.
#         question_matches = re.findall(r'([A-Z][^.?!]*\?)', text)
#         questions = []
#         for q_match in question_matches:
#             q_clean = q_match.strip()
#             if len(q_clean) > 15 and len(q_clean) < 250: # Filter for reasonable length
#                  # Further clean up if it starts with list markers or unwanted phrases
#                 q_clean = re.sub(r'^[•*-]\s*|^[1-9][\.\)]\s*', '', q_clean).strip()
#                 q_clean = re.sub(r'^(Question:|Further research needed on)\s*', '', q_clean, flags=re.IGNORECASE).strip()
#                 questions.append(q_clean)
        
#         unique_questions = list(dict.fromkeys(questions)) # Preserve order, unique
#         return unique_questions[:3] # Max 3

# # Main Interface
# class IdeaEvaluator:
#     def __init__(self):
#         self.system = IdeaEvaluationSystem()
#         self.current_session_id = None
    
#     def start(self, idea: str) -> str:
#         if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY == 'your-gemini-api-key-here':
#             return "🔴 Error: GEMINI_API_KEY is not configured. Please set it as an environment variable."
#         if not Config.SERPER_API_KEY or Config.SERPER_API_KEY == 'your-serper-api-key-here':
#             print("🟡 Warning: SERPER_API_KEY is not configured. Internet search capabilities will be disabled.")

#         start_message = self.system.start_analysis(idea)
#         if "Error" in start_message:
#             return f"🔴 {start_message}"
#         self.current_session_id = self.system.state_manager.sessions[list(self.system.state_manager.sessions.keys())[-1]].session_id # Get actual ID
#         return f"✅ Started analysis! Session ID: {self.current_session_id}"
    
#     def analyze(self, layer: int = None, user_input: str = "") -> Dict[str, Any]:
#         if not self.current_session_id:
#             return {"error": "Start analysis first with start(idea)"}
        
#         session = self.system.state_manager.get_session(self.current_session_id)
#         if not session:
#              return {"error": f"Session {self.current_session_id} not found unexpectedly."}

#         if layer is None: # Analyze all layers sequentially
#             results = {}
#             # Determine delay based on model type (flash/pro vs 1.5-pro)
#             is_slower_model = '1.5-pro' in Config.MODEL_NAME 
#             INTER_LAYER_DELAY_SECONDS = 65 if is_slower_model else 10
#             if 'flash' in Config.MODEL_NAME: # Flash models are faster
#                 INTER_LAYER_DELAY_SECONDS = 5


#             print(f"ℹ️ Using inter-layer delay of {INTER_LAYER_DELAY_SECONDS}s for model {Config.MODEL_NAME}")

#             for i in range(1, 6):
#                 current_layer_state = session.layers[i]
#                 layer_name_for_log = current_layer_state.data.get('layer_name', f'Layer {i}') if current_layer_state.data else f'Layer {i}'

#                 if current_layer_state.status == "completed":
#                     print(f"⏭️ Layer {i} ({layer_name_for_log}) already completed. Skipping.")
#                     results[i] = {"status": "skipped_completed", "layer": i, "data": asdict(current_layer_state)}
#                     continue
                
#                 if i > 1:
#                     prev_layer_state = session.layers[i-1]
#                     if prev_layer_state.status not in ["completed", "skipped_completed"]:
#                         print(f"⚠️ Previous layer {i-1} status is '{prev_layer_state.status}'. Stopping sequential analysis at Layer {i}.")
#                         results[i] = {"status": "skipped_previous_issue", "layer": i, "reason": f"Previous layer {i-1} status: {prev_layer_state.status}"}
#                         break # Stop processing further layers

#                 print(f"\n--- Processing Layer {i} ({layer_name_for_log if layer_name_for_log != f'Layer {i}' else ''}) ---")
#                 # Pass user_input for the current layer if it's the first one being actively processed
#                 # or if we want to allow fresh input for each sequential step (current design reuses initial user_input for all)
#                 current_user_input_for_layer = user_input if i == (session.current_layer if session.current_layer > 0 else 1) else ""

#                 result = self.system.analyze_layer(self.current_session_id, i, current_user_input_for_layer)
#                 results[i] = result
                
#                 # Update layer_name in results if it's fetched during analysis
#                 if result.get("layer_name") and not results[i].get("layer_name"):
#                     results[i]["layer_name"] = result.get("layer_name")

#                 if result.get("status") == "rate_limited":
#                     print(f"⏰ Layer {i} ({result.get('layer_name', '')}) hit rate limit, and retries were exhausted. Analysis paused.")
#                     print(f"Suggestion: {result.get('retry_suggestion', 'Wait and try again.')}")
#                     break 
                    
#                 if result.get("status") == "failed":
#                     print(f"❌ Layer {i} ({result.get('layer_name', '')}) failed. Analysis paused. Error: {result.get('error')}")
#                     break
                    
#                 if i < 5 and result.get("status") == "completed":
#                     print(f"✅ Layer {i} ({result.get('layer_name', '')}) completed. Waiting {INTER_LAYER_DELAY_SECONDS} seconds before next layer...")
#                     time.sleep(INTER_LAYER_DELAY_SECONDS)
            
#             print("\n--- Full Sequential Analysis Attempt Completed ---")
#             final_summary = self.summary()
#             print("📊 Final Summary after sequential run:")
#             print(json.dumps(final_summary, indent=2))
#             return {"all_layer_results": results, "final_summary": final_summary}
#         else: # Analyzing a single specified layer
#             return self.system.analyze_layer(self.current_session_id, layer, user_input)
    
#     def summary(self) -> Dict[str, Any]:
#         if not self.current_session_id:
#             return {"error": "No active session. Start an analysis first."}
#         return self.system.get_summary(self.current_session_id)
    
#     def status(self) -> Dict[str, Any]:
#         if not self.current_session_id:
#             return {"error": "No active session. Start an analysis first."}
        
#         session = self.system.state_manager.get_session(self.current_session_id)
#         if not session: # Should be caught by current_session_id check, but as a safeguard
#             return {"error": f"Session {self.current_session_id} not found, though an ID exists."}

#         # Get names for layers that have data
#         layer_statuses_with_names = {}
#         for i, l_data in session.layers.items():
#             name = "N/A"
#             if l_data.data and l_data.data.get("layer_name"):
#                 name = l_data.data.get("layer_name")
#             elif l_data.data and l_data.data.get("analysis"): # Fallback if layer_name not explicitly stored
#                  name = f"Layer {i} (Details in analysis)"
#             else:
#                 name = f"Layer {i}"
#             layer_statuses_with_names[f"{i} - {name}"] = l_data.status


#         return {
#             "session_id": self.current_session_id,
#             "idea": session.user_idea,
#             "current_layer_processed_or_active": session.current_layer,
#             "overall_confidence": f"{session.overall_confidence:.2f}",
#             "layers_status": layer_statuses_with_names,
#             "completed_layers_count": sum(1 for l in session.layers.values() if l.status == "completed")
#         }

# # Usage Example
# def demo():
#     print("🤖 Idea Evaluation System - Hackathon Demo with Serper")
#     print("==================================================")
    
#     # ENSURE API KEYS ARE SET AS ENVIRONMENT VARIABLES:
#     # export GEMINI_API_KEY="your_gemini_key"
#     # export SERPER_API_KEY="your_serper_key"
    
#     if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY == 'your-gemini-api-key-here':
#         print("🔴 Critical: GEMINI_API_KEY is not set. Demo cannot run.")
#         print("Please set it as an environment variable.")
#         return
#     if not Config.SERPER_API_KEY or Config.SERPER_API_KEY == 'your-serper-api-key-here':
#         print("🟡 Warning: SERPER_API_KEY is not set. Internet search will not work.")
#         print("Please set it as an environment variable for full functionality.")

#     evaluator = IdeaEvaluator()
    
#     idea = "An Gen AI driven Platform where user can give their start-up idea and agent can do the market research, evaluates and validate the idea usig the internet and infomration availabel"
#     print(f"💡 Testing Idea: {idea}")

#     start_message = evaluator.start(idea)
#     print(start_message)
#     if "Error" in start_message or not evaluator.current_session_id:
#         print("Stopping demo due to initialization error.")
#         return

#     # --- Option 1: Analyze all layers sequentially ---
#     # print("\n🔍 Analyzing all layers sequentially (this may take a while)...")
#     # full_analysis_results = evaluator.analyze(user_input="Initial focus on eco-tourism and adventure travel for millennials.") 
#     # # The user_input here will be passed to the first layer when sequential analysis starts.
#     # # Subsequent layers in the sequential run will primarily use context from prior layers.

#     # # --- Option 2: Analyze layer by layer (better for debugging/observing) ---
#     # print("\n🔍 Analyzing Vision Layer (Layer 1)...")
#     # result_layer1 = evaluator.analyze(layer=1, user_input="Focus on solo female travelers and sustainable tourism.")
#     # print(json.dumps(result_layer1, indent=2))
#     # if result_layer1.get("status") != "completed":
#     #     print(f"Stopping demo due to issue in Layer 1: {result_layer1.get('error', 'Unknown error')}")
#     #     print("Status:", evaluator.status())
#     #     return
    
#     delay = 65 if '1.5-pro' in Config.MODEL_NAME else (5 if 'flash' in Config.MODEL_NAME else 10)
#     print(f"\n⏱️ Waiting {delay} seconds before next layer (simulating user pause or system delay)...")
#     time.sleep(delay)

#     print("\n🔍 Analyzing Strategy Layer (Layer 2)...")
#     result_layer2 = evaluator.analyze(layer=2, user_input="Consider partnerships with local ethical tour operators.")
#     print(json.dumps(result_layer2, indent=2))
#     if result_layer2.get("status") != "completed":
#         print(f"Stopping demo due to issue in Layer 2: {result_layer2.get('error', 'Unknown error')}")
#         print("Status:", evaluator.status())
#         return
        
#     print(f"\n⏱️ Waiting {delay} seconds before next layer...")
#     time.sleep(delay)

#     print("\n🔍 Analyzing Market Validation Layer (Layer 3)...")
#     result_layer3 = evaluator.analyze(layer=3, user_input="Target market: Europe and North America, age 25-45. Search for market size of personalized travel planning.")
#     print(json.dumps(result_layer3, indent=2))
#     if result_layer3.get("status") != "completed":
#         print(f"Stopping demo due to issue in Layer 3: {result_layer3.get('error', 'Unknown error')}")
#         print("Status:", evaluator.status())
#         return

#     # Continue for layer 4 and 5 if desired for a full manual run.
#     # For brevity of demo, stopping after 3 successful layers.
#     # To run all, uncomment the "Option 1" block above and comment out layer-by-layer.

#     print("\n📊 Final Status (after partial run):")
#     status_info = evaluator.status()
#     print(json.dumps(status_info, indent=2))
    
#     print("\n📋 Final Summary (after partial run):")
#     summary_info = evaluator.summary()
#     print(json.dumps(summary_info, indent=2))
    
#     return evaluator



# def run_full_analysis_demo():
#     """
#     Runs a demo that attempts to analyze an idea through all 5 layers sequentially.
#     """
#     print("🤖 Idea Evaluation System - Full Sequential Analysis Demo")
#     print("========================================================")

#     # ENSURE API KEYS ARE SET AS ENVIRONMENT VARIABLES:
#     # export GEMINI_API_KEY="your_gemini_key"
#     # export SERPER_API_KEY="your_serper_key"

#     if not Config.GEMINI_API_KEY or Config.GEMINI_API_KEY == 'your-gemini-api-key-here':
#         print("🔴 Critical: GEMINI_API_KEY is not set. Demo cannot run.")
#         print("Please set it as an environment variable.")
#         return None # Return None to indicate failure
#     if not Config.SERPER_API_KEY or Config.SERPER_API_KEY == 'your-serper-api-key-here':
#         print("🟡 Warning: SERPER_API_KEY is not set. Internet search will not work fully.")
#         print("Please set it as an environment variable for full functionality.")

#     evaluator = IdeaEvaluator()

#     # You can change this idea to test with different concepts
#     idea = "An Gen AI driven Platform where user can give their start-up idea and agent can do the market research, evaluates and validate the idea usig the internet and infomration availabel"
#     print(f"💡 Testing Idea for Full Analysis: {idea}")

#     start_message = evaluator.start(idea)
#     print(start_message)
#     if "Error" in start_message or not evaluator.current_session_id:
#         print("Stopping demo due to initialization error.")
#         return None # Return None to indicate failure

#     print(f"\n🔍 Analyzing all 5 layers sequentially for idea: '{idea[:60]}...'")
#     print("This may take several minutes depending on the model and API rate limits.")
#     print("The system has built-in delays between layers to help manage API usage.")

#     # The `user_input` here will be passed to the first layer when sequential analysis starts.
#     # Subsequent layers in the sequential run will primarily use context from prior layers.
#     # You can provide an initial guiding input if desired, or leave it empty.
#     initial_user_input = "Consider integration with local experience providers and carbon footprint tracking."
#     if initial_user_input:
#         print(f"ℹ️ Using initial user input for Layer 1: '{initial_user_input}'")
    
#     # Call analyze() without a specific layer to run all layers
#     # This method within IdeaEvaluator already handles printing progress for each layer.
#     full_analysis_results = evaluator.analyze(user_input=initial_user_input)

#     print("\n--- Summary of Full Sequential Analysis Attempt ---")
#     # The `evaluator.analyze()` method when running all layers returns a dictionary
#     # that includes "all_layer_results" and "final_summary".
#     # We can re-iterate through "all_layer_results" here for a clean final status print.

#     if full_analysis_results and "all_layer_results" in full_analysis_results:
#         print("Status of each layer after sequential run:")
#         for layer_num_key in sorted(full_analysis_results["all_layer_results"].keys()): # Ensure ordered printing
#             result = full_analysis_results["all_layer_results"][layer_num_key]
#             layer_num_actual = result.get("layer", layer_num_key) # Use actual layer number from result if available
#             layer_name = result.get("layer_name", f"Layer {layer_num_actual}")
#             status = result.get("status", "unknown")
            
#             print(f"\n  Layer {layer_num_actual} ({layer_name}) - Status: {status.upper()}")
#             if status == "completed":
#                 print(f"    Confidence: {result.get('confidence', 'N/A')}")
#                 # You could print more details from 'result' if desired, e.g., result.get('analysis')[:100]
#             elif status == "skipped_completed":
#                 print("    This layer was already completed and skipped during the sequential run.")
#             elif status == "skipped_previous_issue":
#                 print(f"    Skipped because a previous layer ({result.get('reason', '')}) did not complete successfully.")
#             elif status == "rate_limited":
#                 print(f"    Error: {result.get('error')}")
#                 print(f"    Suggestion: {result.get('retry_suggestion')}")
#             elif status == "failed":
#                 print(f"    Error: {result.get('error')}")
#             else:
#                 # For any other status, print the result dictionary for more info
#                 print(f"    Details: {json.dumps(result, indent=2)}")
#     elif full_analysis_results and "error" in full_analysis_results:
#          print(f"🔴 An error occurred during the setup for sequential analysis: {full_analysis_results['error']}")
#     else:
#         print("Full analysis did not produce the expected 'all_layer_results' structure.")
#         print(f"Raw output from evaluator.analyze(): {json.dumps(full_analysis_results, indent=2)}")

#     print("\n📊 Current System Status (after full sequential run attempt):")
#     status_info = evaluator.status()
#     print(json.dumps(status_info, indent=2))

#     print("\n📋 Current System Summary (after full sequential run attempt):")
#     # This will generate a summary based on the current state of all layers
#     summary_info = evaluator.summary()
#     print(json.dumps(summary_info, indent=2))
    
#     print("\n✅ Full Sequential Analysis Demo Finished.")
#     return evaluator # Return the evaluator instance for potential further inspection


# if __name__ == "__main__":
#     print("🚀 Hackathon-Ready Idea Evaluator with Serper Search")
#     print("Ensure GEMINI_API_KEY and SERPER_API_KEY environment variables are set.")
#     print("-" * 50)
    
#     # print("\nStarting Demo...")
#     # demo_evaluator = demo()
#     # print("\nDemo Finished.")

#     # Option 2: Run the new full sequential analysis demo (all 5 layers)
#     print("\nStarting Full Sequential Analysis Demo (all 5 layers)...")
#     demo_evaluator_full = run_full_analysis_demo() # Call the new function
#     # print("\nFull Sequential Analysis Demo Finished.") # Already printed inside the function

#     # Example of how to potentially resume or analyze another layer later:
#     # if demo_evaluator and demo_evaluator.current_session_id:
#     #     print("\nSuppose we want to analyze Layer 4 now for the previous session:")
#     #     # session_id = demo_evaluator.current_session_id # or load from somewhere
#     #     # evaluator_resumed = IdeaEvaluator() # Create new instance
#     #     # evaluator_resumed.current_session_id = session_id # Set session
#     #     # # You might need to load session state properly if it's not in memory
#     #
#     #     # For this example, assuming demo_evaluator still holds the state:
#     #     status_before_l4 = demo_evaluator.status()
#     #     if status_before_l4.get("layers_status", {}).get("4 - Layer 4", "") != "completed": # Check if not already done
#     #         print("\n🔍 Analyzing Competition Layer (Layer 4)...")
#     #         result_layer4 = demo_evaluator.analyze(layer=4, user_input="Look for competitors in AI travel planning focusing on experiences, not just flights/hotels.")
#     #         print(json.dumps(result_layer4, indent=2))
#     #         print("\n📋 Summary after Layer 4:")
#     #         print(json.dumps(demo_evaluator.summary(), indent=2))
#     #     else:
#     #         print("Layer 4 was already completed or demo didn't reach this stage.")














# claud internet working 


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
    MODEL_NAME = os.getenv('CLAUDE_MODEL_NAME', 'claude-3-haiku-20240307') # CHANGED
    
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
            Analyze the vision and opportunity for the user's idea: "{session.user_idea}"
            Additional context from user: "{user_input}"
            
            Evaluate:
            1. What core problem does this idea aim to solve?
            2. What current trends (social, technological, economic) might support or challenge this idea? (Use internet_search for recent trends if needed).
            3. What is the potential scale or size of the opportunity? (Provide a qualitative assessment).
            
            Provide actionable insights and rate your confidence in this vision on a scale of 0.0 to 1.0 (e.g., "Confidence: 0.8").
            Clearly state if you used the 'internet_search' tool for any specific findings.
            """,
            agent=self.strategist,
            expected_output="A concise analysis of the idea's vision and opportunity, key supporting/challenging trends, qualitative opportunity size, actionable insights, and a clear confidence rating (e.g., Confidence: 0.X). Mention if internet search was used."
        )
        return self._execute_analysis(session, 1, task, "Vision & Opportunity")
    
    def _analyze_strategy(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 1)
        task = Task(
            description=f"""
            Based on the user's idea: "{session.user_idea}" and previous analysis:
            {context}
            User input for this layer: "{user_input}"
            
            Develop a high-level strategy:
            1. How should this idea be strategically positioned in the market?
            2. Is the market timing favorable, or what factors affect timing? (Use internet_search for recent market signals if needed).
            3. What are potential unique selling propositions or competitive advantages?
            
            Provide actionable insights and rate your confidence (0-1 scale, e.g., "Confidence: 0.7").
            Clearly state if you used the 'internet_search' tool.
            """,
            agent=self.strategist,
            expected_output="Strategic analysis focusing on positioning, market timing, and competitive advantages, with insights and a confidence rating (e.g., Confidence: 0.X). Mention if internet search was used."
        )
        return self._execute_analysis(session, 2, task, "Strategy & Positioning")
    
    def _analyze_market(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 2)
        task = Task(
            description=f"""
            For the idea: "{session.user_idea}", considering previous analysis:
            {context}
            User input for this layer: "{user_input}"
            
            Validate the market. You MUST use the 'internet_search' tool to find supporting data for the following, then synthesize:
            1. Identify and describe the primary target customer segments.
            2. Find any available data or estimations on the market size for these segments.
            3. Search for evidence validating the needs of these target customers related to the idea.
            
            Provide actionable insights, cite sources or search queries used, and rate confidence (0-1 scale, e.g., "Confidence: 0.9").
            """,
            agent=self.analyst,
            expected_output="Market validation analysis including target customers, market size estimations (with sources/queries if found via search), customer needs validation, insights, and a confidence rating (e.g., Confidence: 0.X)."
        )
        return self._execute_analysis(session, 3, task, "Market Validation")
    
    def _analyze_competition(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 3)
        task = Task(
            description=f"""
            For the idea: "{session.user_idea}", considering previous analysis:
            {context}
            User input for this layer: "{user_input}"
            
            Analyze the competitive landscape. You MUST use the 'internet_search' tool to identify competitors:
            1. Identify 2-3 key direct and indirect competitors.
            2. For each, briefly note their strengths and weaknesses.
            3. What opportunities exist for differentiation against these competitors?
            
            Provide actionable insights, cite search queries or specific competitors found, and rate confidence (0-1 scale, e.g., "Confidence: 0.6").
            """,
            agent=self.analyst,
            expected_output="Competitive analysis identifying key competitors (with specifics if found via search), their S&W, differentiation opportunities, insights, and a confidence rating (e.g., Confidence: 0.X)."
        )
        return self._execute_analysis(session, 4, task, "Competition Analysis")
    
    def _analyze_business_model(self, session: AnalysisState, user_input: str) -> Dict[str, Any]:
        context = self._get_layer_context(session, 4)
        task = Task(
            description=f"""
            For the idea: "{session.user_idea}", considering previous analysis:
            {context}
            User input for this layer: "{user_input}"
            
            Outline a potential business model:
            1. Suggest 1-2 viable revenue models (e.g., subscription, freemium, transaction fees).
            2. What are the key metrics to track for success (e.g., CAC, LTV, churn)? (Use internet_search if specific industry metrics are relevant).
            3. Assess the scalability potential of this business model.
            
            Provide actionable insights and rate confidence (0-1 scale, e.g., "Confidence: 0.8").
            Clearly state if you used the 'internet_search' tool.
            """,
            agent=self.strategist,
            expected_output="Business model analysis suggesting revenue models, key metrics, scalability assessment, insights, and a confidence rating (e.g., Confidence: 0.X). Mention if internet search was used."
        )
        return self._execute_analysis(session, 5, task, "Business Model")

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


