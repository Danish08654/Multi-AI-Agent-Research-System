from pydantic import BaseModel
from typing import List, Optional


# REQUEST
class ResearchRequest(BaseModel):
    topic: str


# RESPONSE
class ResearchResponse(BaseModel):
    topic: str
    research_plan: str
    search_queries: List[str] = []
    sources_found: int = 0
    analysis: str = ""
    fact_check: str = ""
    final_report: str = ""
    current_step: str = "pending"
    errors: List[str] = []
    word_count: int = 0