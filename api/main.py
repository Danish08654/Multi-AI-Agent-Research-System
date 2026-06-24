import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from schema import ResearchRequest, ResearchResponse
from graph.research_graph import run_research

load_dotenv()

app = FastAPI(
    title="LangGraph Multi-Agent Research System (Ollama)",
    description="5-agent research pipeline: Planner → Searcher → Analyst → Writer → Fact-Checker",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# Root
@app.get("/")
def root():
    return {
        "service": "Multi-Agent Research System (Ollama)",
        "agents": ["Planner", "Searcher", "Analyst", "Writer", "Fact-Checker"],
        "version": "1.0.0"
    }


# Research Endpoint
@app.post("/research", response_model=ResearchResponse)
def conduct_research(request: ResearchRequest):
    if not request.topic or len(request.topic.strip()) < 5:
        raise HTTPException(
            status_code=400,
            detail="Topic must be at least 5 characters"
        )

    try:
        result = run_research(request.topic.strip())

        word_count = len(result.get("final_report", "").split())

        return ResearchResponse(
            topic=result["topic"],
            research_plan=result["research_plan"],
            search_queries=result["search_queries"],
            sources_found=len(result.get("raw_results", [])),
            analysis=result["analysis"],
            fact_check=result["fact_check"],
            final_report=result["final_report"],
            current_step=result["current_step"],
            errors=result.get("errors", []),
            word_count=word_count
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Health Check (NO KEYS NEEDED NOW)
@app.get("/health")
def health():
    return {
        "status": "ok",
        "llm": "ollama (local)"
    }