import json
import requests
import streamlit as st

st.set_page_config(
    page_title="FinSentry Financial Intelligence",
    page_icon="🛡️️",
    layout="wide",
)

st.title("🛡️ FinSentry: Multi-Agent SEC Due Diligence Engine")
st.markdown(
    "Automated financial auditing across SEC EDGAR filings with **Deterministic Math Sandboxing**, "
    "**Hybrid RAG**, and **Material Narrative Discrepancy Detection**."
)

API_BASE_URL = "http://localhost:8000"

with st.sidebar:
    st.header("Audit Configuration")
    ticker = st.text_input("Ticker Symbol", value="AAPL").upper().strip()
    target_year = st.selectbox("Fiscal Year", options=["2024", "2023", "2022"], index=0)
    
    predefined_queries = [
        "Audit balance sheet working capital and evaluate if management claims regarding sufficient liquidity match reality.",
        "Verify total debt obligations, credit covenant terms, and senior note maturities.",
        "Evaluate inventory growth rate vs revenue growth to detect potential obsolescence risk.",
    ]
    query = st.text_area("Audit Objective / Inquiry", value=predefined_queries[0], height=120)
    start_audit_btn = st.button("🚀 Start Multi-Agent Audit", type="primary", use_container_width=True)

if start_audit_btn:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Agent Reasoning & Event Stream")
        event_container = st.container(height=420)
        progress_bar = st.progress(0)

    with col2:
        st.subheader("Deterministic Metrics & Audit Flags")
        results_container = st.container(height=420)

    payload = {
        "ticker": ticker,
        "target_year": str(target_year),
        "query": query,
    }

    try:
        with requests.post(
            f"{API_BASE_URL}/api/v1/audit/stream",
            json=payload,
            headers={"Accept": "text/event-stream"},
            stream=True,
            timeout=90,
        ) as response:
            if response.status_code != 200:
                st.error(f"Server returned error code: {response.status_code}")
            else:
                current_event = None
                step_counter = 0

                for raw_line in response.iter_lines(decode_unicode=True):
                    if not raw_line:
                        continue

                    if raw_line.startswith("event:"):
                        current_event = raw_line.replace("event:", "").strip()
                    elif raw_line.startswith("data:") and current_event:
                        data_str = raw_line.replace("data:", "").strip()
                        try:
                            data = json.loads(data_str)
                        except json.JSONDecodeError:
                            data = {"raw": data_str}

                        if current_event == "workflow_start":
                            with event_container:
                                st.info(f"Initiating audit for **{ticker}** (FY{target_year})...")
                            progress_bar.progress(10)

                        elif current_event == "node_update":
                            step_counter += 1
                            node_name = data.get("node", "Agent Node")
                            messages = data.get("messages", [])
                            last_msg = messages[-1]["content"] if messages else "Executing task..."

                            with event_container:
                                st.markdown(f"**[{node_name.upper()}]**: {last_msg}")

                            progress_bar.progress(min(20 + step_counter * 18, 90))

                            if "report" in data:
                                with results_container:
                                    st.success("Audit Memo Generated!")
                                    st.code(data["report"], language="markdown")

                        elif current_event == "workflow_complete":
                            progress_bar.progress(100)
                            st.toast("Multi-Agent Audit Completed Successfully!", icon="✅")

    except requests.exceptions.ConnectionError:
        st.error(
            "Cannot connect to the FastAPI Gateway at http://localhost:8000. "
            "Please ensure the backend is running with `make run`."
        )
