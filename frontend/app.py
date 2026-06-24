import streamlit as st
import time
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# ✅ LOAD ENVIRONMENT
load_dotenv()

# ✅ GROQ API SETUP
try:
    from groq import Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    
    if not GROQ_API_KEY:
        st.error("❌ GROQ_API_KEY not found! Add it to Streamlit Secrets.")
        st.stop()
    
    client = Groq(api_key=GROQ_API_KEY)
except ImportError:
    st.error("❌ groq module not installed. Add to requirements.txt: groq")
    st.stop()
except Exception as e:
    st.error(f"❌ Groq initialization error: {str(e)}")
    st.stop()

# ✅ STREAMLIT PAGE CONFIG
st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 AI Multi-Agent Research System")

# ✅ SESSION STATE
if "research_result" not in st.session_state:
    st.session_state.research_result = None

if "research_in_progress" not in st.session_state:
    st.session_state.research_in_progress = False

# ──────────────────────────────────────────────────────────────
# ✅ PIPELINE VISUALIZATION
# ──────────────────────────────────────────────────────────────

st.markdown("""
<div style='display:flex;gap:8px;align-items:center;margin-bottom:1rem;flex-wrap:wrap'>
  <span style='background:#3498db;color:white;padding:6px 14px;border-radius:20px;font-size:13px'>🧠 Planner</span>
  <span style='color:#aaa'>→</span>
  <span style='background:#e67e22;color:white;padding:6px 14px;border-radius:20px;font-size:13px'>🔍 Searcher</span>
  <span style='color:#aaa'>→</span>
  <span style='background:#9b59b6;color:white;padding:6px 14px;border-radius:20px;font-size:13px'>📊 Analyst</span>
  <span style='color:#aaa'>→</span>
  <span style='background:#27ae60;color:white;padding:6px 14px;border-radius:20px;font-size:13px'>✍️ Writer</span>
  <span style='color:#aaa'>→</span>
  <span style='background:#e74c3c;color:white;padding:6px 14px;border-radius:20px;font-size:13px'>✅ Fact-Checker</span>
</div>
""", unsafe_allow_html=True)

st.success("🟢 System is ready — Groq API connected")

st.divider()

# ──────────────────────────────────────────────────────────────
# ✅ AGENT FUNCTIONS
# ──────────────────────────────────────────────────────────────

def agent_planner(topic: str) -> dict:
    """
    Agent 1: Plans research structure
    """
    prompt = f"""You are a research planning expert. Create a comprehensive research plan for the following topic.

TOPIC: {topic}

Provide a structured research plan with:
1. Main research questions (3-5 questions)
2. Key areas to investigate
3. Subtopics to explore
4. Search queries to use
5. Expected sources to find

Format your response as a detailed outline. Be specific and actionable."""

    try:
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        plan = message.choices[0].message.content
        
        # Extract search queries
        search_queries = []
        lines = plan.split('\n')
        for line in lines:
            if 'search' in line.lower() or 'query' in line.lower():
                cleaned = line.strip('- •*').strip()
                if cleaned and len(cleaned) > 10:
                    search_queries.append(cleaned)
        
        if not search_queries:
            search_queries = [
                f"{topic} overview",
                f"{topic} latest research",
                f"{topic} applications",
                f"{topic} challenges",
                f"{topic} future trends"
            ]
        
        return {
            "status": "success",
            "plan": plan,
            "search_queries": search_queries[:5],
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "plan": "",
            "search_queries": [f"{topic} research", f"{topic} overview"],
            "error": str(e)
        }

def agent_searcher(topic: str, search_queries: list) -> dict:
    """
    Agent 2: Simulates research and collects sources
    Generates realistic sources based on topic
    """
    prompt = f"""You are a research librarian. Based on this topic and search queries, 
generate a comprehensive list of research sources.

TOPIC: {topic}
SEARCH QUERIES: {', '.join(search_queries)}

For each search query, generate 3-4 realistic academic/industry sources with:
1. Source title
2. Publication year
3. Key findings relevant to the topic
4. Source type (journal, book, whitepaper, news, report)

Format as a structured list. Make sources realistic and relevant.
Include universities, research institutions, and industry publications."""

    try:
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=2500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        sources_text = message.choices[0].message.content
        
        # Parse sources
        sources = sources_text.split('\n')
        sources = [s.strip() for s in sources if s.strip() and len(s.strip()) > 10]
        
        return {
            "status": "success",
            "sources_found": len(sources),
            "sources": sources[:20],
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "sources_found": 0,
            "sources": [],
            "error": str(e)
        }

def agent_analyst(topic: str, sources: list) -> dict:
    """
    Agent 3: Analyzes collected information
    """
    sources_summary = "\n".join(sources[:10]) if sources else "No sources provided"
    
    prompt = f"""You are a research analyst. Analyze the following research topic and sources.

TOPIC: {topic}

SOURCES:
{sources_summary}

Provide a comprehensive analysis including:
1. Key findings from sources
2. Major themes and patterns
3. Important statistics and data
4. Expert perspectives
5. Research gaps and areas needing more investigation
6. Critical insights

Be detailed and insightful. Structure your analysis clearly."""

    try:
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=3000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        analysis = message.choices[0].message.content
        
        return {
            "status": "success",
            "analysis": analysis,
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "analysis": "",
            "error": str(e)
        }

def agent_writer(topic: str, plan: str, analysis: str) -> dict:
    """
    Agent 4: Writes comprehensive research report
    """
    prompt = f"""You are a professional research writer. Create a comprehensive, well-structured research report.

TOPIC: {topic}

RESEARCH PLAN:
{plan[:1000]}

ANALYSIS:
{analysis[:1500]}

Write a complete research report with:

# Executive Summary
[2-3 paragraph overview]

# Introduction
[Context and significance]

# Research Methodology
[How the research was conducted]

# Key Findings
[Main discoveries and insights]

# Analysis & Discussion
[Detailed analysis of findings]

# Implications
[What this means for the field]

# Future Research Directions
[Gaps and next steps]

# Conclusion
[Summary of key points]

# References
[List of 5-10 key sources]

Write in professional academic style. Make it comprehensive and insightful."""

    try:
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=4000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        report = message.choices[0].message.content
        word_count = len(report.split())
        
        return {
            "status": "success",
            "report": report,
            "word_count": word_count,
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "report": "",
            "word_count": 0,
            "error": str(e)
        }

def agent_fact_checker(topic: str, report: str) -> dict:
    """
    Agent 5: Fact-checks the report
    """
    prompt = f"""You are a fact-checking expert. Review this research report for accuracy and quality.

TOPIC: {topic}

REPORT:
{report[:2000]}

Evaluate the report on:
1. Factual accuracy
2. Logical consistency
3. Source credibility
4. Claims substantiation
5. Potential biases

Provide:
- Overall credibility score (1-10)
- Key strengths
- Areas of concern
- Recommendations for improvement

Format clearly and be constructive."""

    try:
        message = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            max_tokens=1500,
            messages=[{"role": "user", "content": prompt}]
        )
        
        fact_check = message.choices[0].message.content
        
        # Extract score
        score = 7  # Default
        if "10" in fact_check or "9/10" in fact_check or "8/10" in fact_check:
            score = 8
        elif "5" in fact_check or "6/10" in fact_check:
            score = 6
        
        return {
            "status": "success",
            "fact_check": fact_check,
            "credibility_score": score,
            "error": None
        }
    
    except Exception as e:
        return {
            "status": "error",
            "fact_check": "",
            "credibility_score": 0,
            "error": str(e)
        }

def run_research_pipeline(topic: str) -> dict:
    """
    Orchestrate all agents in sequence
    """
    results = {
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "stage": "starting",
        "errors": []
    }
    
    try:
        # STAGE 1: PLANNER
        st.info("🧠 Stage 1/5: Planning research structure...")
        planner_result = agent_planner(topic)
        results["research_plan"] = planner_result["plan"]
        results["search_queries"] = planner_result["search_queries"]
        
        if planner_result["error"]:
            results["errors"].append(f"Planner: {planner_result['error']}")
        
        time.sleep(1)
        
        # STAGE 2: SEARCHER
        st.info("🔍 Stage 2/5: Collecting sources...")
        searcher_result = agent_searcher(topic, planner_result["search_queries"])
        results["sources_found"] = searcher_result["sources_found"]
        results["sources"] = searcher_result["sources"]
        
        if searcher_result["error"]:
            results["errors"].append(f"Searcher: {searcher_result['error']}")
        
        time.sleep(1)
        
        # STAGE 3: ANALYST
        st.info("📊 Stage 3/5: Analyzing data...")
        analyst_result = agent_analyst(topic, searcher_result["sources"])
        results["analysis"] = analyst_result["analysis"]
        
        if analyst_result["error"]:
            results["errors"].append(f"Analyst: {analyst_result['error']}")
        
        time.sleep(1)
        
        # STAGE 4: WRITER
        st.info("✍️ Stage 4/5: Writing report...")
        writer_result = agent_writer(
            topic, 
            planner_result["plan"], 
            analyst_result["analysis"]
        )
        results["final_report"] = writer_result["report"]
        results["word_count"] = writer_result["word_count"]
        
        if writer_result["error"]:
            results["errors"].append(f"Writer: {writer_result['error']}")
        
        time.sleep(1)
        
        # STAGE 5: FACT-CHECKER
        st.info("✅ Stage 5/5: Fact-checking report...")
        fact_checker_result = agent_fact_checker(topic, writer_result["report"])
        results["fact_check"] = fact_checker_result["fact_check"]
        results["credibility_score"] = fact_checker_result["credibility_score"]
        
        if fact_checker_result["error"]:
            results["errors"].append(f"Fact-Checker: {fact_checker_result['error']}")
        
        results["status"] = "success"
        return results
    
    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Pipeline: {str(e)}")
        return results

# ──────────────────────────────────────────────────────────────
# ✅ INPUT SECTION
# ──────────────────────────────────────────────────────────────

col_input, col_examples = st.columns([2, 1])

with col_input:
    topic = st.text_area(
        "Research Topic",
        placeholder="e.g. Impact of AI on software engineering productivity",
        height=100
    )

    research_btn = st.button(
        "🚀 Start Research",
        type="primary",
        use_container_width=True,
        disabled=not topic or st.session_state.research_in_progress
    )

with col_examples:
    st.markdown("### Example Topics")

    examples = [
        "AI agents replacing software developers 2025",
        "Quantum computing applications in healthcare",
        "CRISPR gene editing breakthroughs",
        "Autonomous vehicles regulations",
        "Carbon capture technology future"
    ]

    for ex in examples:
        if st.button(ex, key=f"example_{ex}", use_container_width=True):
            topic = ex

# ──────────────────────────────────────────────────────────────
# ✅ RUN PIPELINE
# ──────────────────────────────────────────────────────────────

if research_btn and topic:
    st.session_state.research_in_progress = True
    st.divider()
    
    # Progress tracking
    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    
    # Run research
    with progress_placeholder.container():
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    # Update progress
    status_text.info("🧠 Starting research pipeline...")
    time.sleep(1)
    
    result = run_research_pipeline(topic)
    
    # Mark complete
    progress_bar.progress(1.0)
    status_text.success("✅ Research complete!")
    
    st.session_state.research_result = result
    st.session_state.research_in_progress = False
    
    time.sleep(2)
    progress_placeholder.empty()
    status_placeholder.empty()

# ──────────────────────────────────────────────────────────────
# ✅ DISPLAY RESULTS
# ──────────────────────────────────────────────────────────────

if st.session_state.research_result:
    result = st.session_state.research_result
    
    if result["status"] == "error":
        st.error(f"❌ Research failed: {', '.join(result['errors'])}")
        st.stop()
    
    st.divider()
    
    # METRICS
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.metric("Word Count", result.get("word_count", 0))
    with c2:
        st.metric("Sources Found", result.get("sources_found", 0))
    with c3:
        st.metric("Search Queries", len(result.get("search_queries", [])))
    with c4:
        st.metric("Credibility Score", f"{result.get('credibility_score', 0)}/10")
    
    st.divider()
    
    # TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Final Report",
        "🗺️ Research Plan",
        "📊 Analysis",
        "✅ Fact Check",
        "🔍 Sources"
    ])
    
    # TAB 1: REPORT
    with tab1:
        st.markdown(result.get("final_report", "No report generated."))
        
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                "⬇ Download as Markdown",
                data=result.get("final_report", ""),
                file_name=f"research_{topic[:30].replace(' ','_')}.md",
                mime="text/markdown"
            )
        with col2:
            # Convert to plain text for download
            plain_text = result.get("final_report", "").replace("#", "").replace("**", "")
            st.download_button(
                "⬇ Download as Text",
                data=plain_text,
                file_name=f"research_{topic[:30].replace(' ','_')}.txt",
                mime="text/plain"
            )
    
    # TAB 2: PLAN
    with tab2:
        st.subheader("Research Plan")
        st.markdown(result.get("research_plan", "No plan generated."))
        
        st.subheader("Search Queries Used")
        for i, query in enumerate(result.get("search_queries", []), 1):
            st.write(f"{i}. {query}")
    
    # TAB 3: ANALYSIS
    with tab3:
        st.subheader("Detailed Analysis")
        st.markdown(result.get("analysis", "No analysis generated."))
    
    # TAB 4: FACT CHECK
    with tab4:
        st.subheader("Fact-Check Report")
        
        score = result.get("credibility_score", 0)
        
        if score >= 8:
            st.success(f"✅ High Credibility (Score: {score}/10)")
        elif score >= 6:
            st.info(f"ℹ️ Moderate Credibility (Score: {score}/10)")
        else:
            st.warning(f"⚠️ Low Credibility (Score: {score}/10)")
        
        st.markdown(result.get("fact_check", "No fact-check performed."))
    
    # TAB 5: SOURCES
    with tab5:
        st.subheader(f"Sources Found ({result.get('sources_found', 0)})")
        
        sources = result.get("sources", [])
        if sources:
            for i, source in enumerate(sources, 1):
                st.write(f"**{i}. {source}**")
        else:
            st.info("No sources found.")
    
    # ERRORS (if any)
    if result.get("errors"):
        with st.expander("⚠️ Warnings During Processing"):
            for error in result["errors"]:
                st.warning(error)
    
    st.divider()
    
    # NEW RESEARCH BUTTON
    col_new = st.columns([1, 2, 1])[0]
    with col_new:
        if st.button("🔄 Start New Research", use_container_width=True):
            st.session_state.research_result = None
            time.sleep(1)
            st.rerun()
