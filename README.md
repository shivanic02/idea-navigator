# 💡 IdeaForge AI

**Validate Startup Ideas with AI — Instantly.**  
A multi-agent system that deeply evaluates startup ideas across five strategic layers using Anthropic Claude, Serper, and CrewAI.

---

## 🚀 Overview

Startup founders often face uncertainty when validating their ideas, especially without access to expensive consulting or market research tools.  
**IdeaForge AI** bridges that gap by acting as a **real-time idea analyst agent** powered by **Claude 3** and web-search tools, giving structured and actionable feedback across five business-critical dimensions.

---

## 🧠 How It Works

Once a user submits their idea, the system walks through a structured, multi-layered analysis funnel:

1. **Vision & Philosophy** – Understands the big picture, market shifts, and JTBD.
2. **Market Fit & Strategy** – Determines if it’s a vitamin or painkiller and who the ICP is.
3. **Competitive Landscape** – Scans the market and positions your differentiation.
4. **Business Model & Execution** – Evaluates revenue models, GTM, risks, and feasibility.
5. **Validation & KPIs** – Suggests MVP, testing loops, and success metrics.

---

## 🛠️ Built With

- **Python**
- **Flask**
- **FastAPI**
- **CrewAI** – Multi-agent orchestration
- **Anthropic Claude 3** – LLM reasoning and analysis
- **Serper API** – Live web search
- **Langchain**
- **ChromaDB** (optional, for embedding future features)
- **Docker** (recommended for deployment)

---

## 📦 Setup Instructions

### 1. Clone the Repository

git clone https://github.com/yourusername/idea-navigator.git
cd ideaforge-ai

### 2. Install Dependencies 

pip install -r requirements.txt

### 3. Configure Environment

ANTHROPIC_API_KEY=your_anthropic_key
SERPER_API_KEY=your_serper_key

### 4. Run the Backend Server 

python backend_api.py

