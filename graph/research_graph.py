import os
import json
from typing import TypedDict, List
from dotenv import load_dotenv

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
load_dotenv()


# STATE
class ResearchState(TypedDict):
    topic: str
    research_plan: str
    search_queries: List[str]
    raw_results: List[dict]
    analysis: str
    draft_report: str
    fact_check: str
    final_report: str
    current_step: str
    errors: List[str]


# LOCAL LLM (OLLAMA)
llm = ChatOllama(
    model="llama3",   # or mistral, deepseek-coder etc.
    temperature=0.3
)


# SEARCH TOOL 
def searcher_agent(state: ResearchState) -> ResearchState:
    print("🔍 Searcher Agent working (offline mode)...")

    queries = state.get("search_queries", [])

    results = []

    for q in queries:
        results.append({
            "query": q,
            "title": f"Research for {q}",
            "content": f"""
            Offline research placeholder generated locally using Ollama.
            This result simulates collected information about:
            {q}
            """,
            "url": ""
        })

    return {
        **state,
        "raw_results": results,
        "current_step": "analysing"
    }

# PLANNER AGENT
# 
def planner_agent(state: ResearchState) -> ResearchState:
    print("🧠 Planner Agent working...")

    messages = [
        SystemMessage(content="""
        You are a research planner.
        Create:
        1. Research plan (3-5 points)
        2. Exactly 5 search queries

        Return JSON:
        {
          "research_plan": "...",
          "search_queries": ["...", "...", "...", "...", "..."]
        }
        """),
        HumanMessage(content=state["topic"])
    ]

    try:
        response = llm.invoke(messages)
        content = response.content

        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]

        parsed = json.loads(content)

        return {
            **state,
            "research_plan": parsed.get("research_plan", ""),
            "search_queries": parsed.get("search_queries", []),
            "current_step": "searching"
        }

    except Exception as e:
        return {
            **state,
            "research_plan": f"Plan for {state['topic']}",
            "search_queries": [
                f"{state['topic']} overview",
                f"{state['topic']} trends",
                f"{state['topic']} analysis",
                f"{state['topic']} facts",
                f"{state['topic']} future"
            ],
            "errors": state.get("errors", []) + [str(e)],
            "current_step": "searching"
        }


# SEARCHER AGENT
def searcher_agent(state: ResearchState) -> ResearchState:
    print("🔍 Searcher Agent working...")

    results = []

    for q in state.get("search_queries", []):
        try:
            res = search_tool.invoke(q)

            for r in res:
                results.append({
                    "query": q,
                    "title": r.get("title", ""),
                    "content": r.get("content", ""),
                    "url": r.get("url", "")
                })

        except Exception as e:
            results.append({
                "query": q,
                "title": "error",
                "content": str(e),
                "url": ""
            })

    return {
        **state,
        "raw_results": results,
        "current_step": "analysing"
    }


# ANALYST
def analyst_agent(state: ResearchState) -> ResearchState:
    print("📊 Analyst Agent working...")

    text = "\n".join([
        f"{r['title']} - {r['content'][:300]}"
        for r in state.get("raw_results", [])[:10]
    ])

    messages = [
        SystemMessage(content="""
        Extract key insights, patterns, and facts.
        Be structured and analytical.
        """),
        HumanMessage(content=text)
    ]

    try:
        response = llm.invoke(messages)

        return {
            **state,
            "analysis": response.content,
            "current_step": "writing"
        }

    except Exception as e:
        return {
            **state,
            "analysis": "analysis failed",
            "errors": state.get("errors", []) + [str(e)],
            "current_step": "writing"
        }


# WRITER
def writer_agent(state: ResearchState) -> ResearchState:
    print("✍️ Writer Agent working...")

    messages = [
        SystemMessage(content="""
        Write a structured research report:
        - Executive Summary
        - Key Findings
        - Analysis
        - Conclusion
        """),
        HumanMessage(content=state["analysis"])
    ]

    response = llm.invoke(messages)

    return {
        **state,
        "draft_report": response.content,
        "current_step": "fact_checking"
    }


# FACT CHECKER
def fact_checker_agent(state: ResearchState) -> ResearchState:
    print("✅ Fact Checker working...")

    messages = [
        SystemMessage(content="""
        Review report and improve accuracy.
        Return:
        FACT CHECK + FINAL REPORT
        """),
        HumanMessage(content=state["draft_report"])
    ]

    response = llm.invoke(messages).content

    return {
        **state,
        "fact_check": response,
        "final_report": response,
        "current_step": "complete"
    }


# GRAPH
def build_research_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_agent)
    graph.add_node("searcher", searcher_agent)
    graph.add_node("analyst", analyst_agent)
    graph.add_node("writer", writer_agent)
    graph.add_node("fact_checker", fact_checker_agent)

    graph.set_entry_point("planner")

    graph.add_edge("planner", "searcher")
    graph.add_edge("searcher", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", "fact_checker")
    graph.add_edge("fact_checker", END)

    return graph.compile()


# RUN
def run_research(topic: str):
    graph = build_research_graph()

    state: ResearchState = {
        "topic": topic,
        "research_plan": "",
        "search_queries": [],
        "raw_results": [],
        "analysis": "",
        "draft_report": "",
        "fact_check": "",
        "final_report": "",
        "current_step": "planning",
        "errors": []
    }

    print("🚀 Starting:", topic)
    return graph.invoke(state)


# TEST
if __name__ == "__main__":
    result = run_research("Impact of AI on software engineering jobs")
    print(result["final_report"][:1000])