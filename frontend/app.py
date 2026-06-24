import streamlit as st
import requests
import time
import threading

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="AI Research Agent",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 AI Multi-Agent Research System")

# PIPELINE UI
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


# HEALTH CHECK 
try:
    health = requests.get(f"{API_URL}/health", timeout=3).json()

    if health.get("status") == "missing keys":
        st.warning("⚠️ Some system components are missing (LLM or tools).")
    else:
        st.success("🟢 System is ready")

except:
    st.error("❌ Backend not running. Start it using:")
    st.code("uvicorn api.main:app --reload")


st.divider()


# INPUT SECTION
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
        disabled=not topic
    )

with col_examples:
    st.markdown("### Example Topics")

    examples = [
        "AI agents replacing software developers 2025",
        "Quantum computing applications",
        "CRISPR gene editing breakthroughs",
        "Autonomous vehicles regulations",
        "Carbon capture technology future"
    ]

    for ex in examples:
        if st.button(ex, key=ex):
            topic = ex
            research_btn = True


# RUN PIPELINE

if research_btn and topic:
    st.divider()

    progress_bar = st.progress(0)
    status_text = st.empty()

    steps = [
        (0.15, "🧠 Planning research structure..."),
        (0.35, "🔍 Collecting sources..."),
        (0.60, "📊 Analyzing data..."),
        (0.80, "✍️ Writing report..."),
        (1.00, "✅ Finalizing...")
    ]

    result_container = {}

    def call_api():
        try:
            resp = requests.post(
                f"{API_URL}/research",
                json={"topic": topic},
                timeout=300
            )
            result_container["result"] = resp.json()
            result_container["error"] = None
        except Exception as e:
            result_container["error"] = str(e)
            result_container["result"] = None

    thread = threading.Thread(target=call_api)
    thread.start()

    step_idx = 0
    while thread.is_alive():
        if step_idx < len(steps):
            prog, msg = steps[step_idx]
            progress_bar.progress(prog)
            status_text.info(msg)
            step_idx += 1
        time.sleep(5)

    thread.join()

    progress_bar.progress(1.0)
    status_text.success("✅ Research complete!")

    if result_container.get("error"):
        st.error(result_container["error"])
        st.stop()

    result = result_container["result"]

    # METRICS
    st.divider()

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Word Count", result.get("word_count", 0))
    c2.metric("Sources", result.get("sources_found", 0))
    c3.metric("Queries", len(result.get("search_queries", [])))
    c4.metric("Errors", len(result.get("errors", [])))

    
    # TABS
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📄 Report",
        "🗺️ Plan",
        "📊 Analysis",
        "✅ Fact Check",
        "🔍 Sources"
    ])

    with tab1:
        st.markdown(result.get("final_report", "No report generated."))

        st.download_button(
            "⬇ Download Report",
            data=result.get("final_report", ""),
            file_name=f"research_{topic[:30].replace(' ','_')}.md",
            mime="text/markdown"
        )

    with tab2:
        st.markdown(result.get("research_plan", "No plan"))
        st.write(result.get("search_queries", []))

    with tab3:
        st.markdown(result.get("analysis", "No analysis"))

    with tab4:
        fc = result.get("fact_check", "")

        if "APPROVE" in fc.upper():
            st.success(fc)
        elif "REJECT" in fc.upper():
            st.error(fc)
        else:
            st.info(fc)

    with tab5:
        st.info(f"Total sources: {result.get('sources_found', 0)}")

        for q in result.get("search_queries", []):
            st.markdown(f"- {q}")

    # ERRORS
    if result.get("errors"):
        with st.expander("⚠ Errors"):
            for e in result["errors"]:
                st.code(e)