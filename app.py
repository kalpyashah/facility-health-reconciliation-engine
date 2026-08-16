import streamlit as st
import pandas as pd
import json
import os
from src.ingestion import EventIngestor
from src.reconciliation import ReconciliationEngine
from src.visualization import StateVisualizer

st.set_page_config(
    page_title="Facility Health Reconciliation Engine",
    page_icon="🏢",
    layout="wide"
)

st.title("🏢 Facility Health Reconciliation Engine")
st.markdown("Deterministic, time-aware state reconstruction pipeline for multi-source facility telemetry (**IoT**, **Manual**, **Contractor**).")

st.sidebar.header("Control Panel")
uploaded_file = st.sidebar.file_uploader("Upload CSV Fixture", type=["csv"])

fixture_path = "data/fixtures/sample_events.csv"
if uploaded_file is not None:
    temp_path = "data/fixtures/temp_uploaded.csv"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    target_file = temp_path
else:
    target_file = fixture_path

ingestor = EventIngestor()
events, stats = ingestor.parse_csv(target_file)

engine = ReconciliationEngine(window_hours=1.0)
state_history, audit_logs = engine.reconcile_events(events)

# Metric Row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Events Ingested", len(events))
col2.metric("Skipped Rows", stats["skipped_rows"])
col3.metric("Subsystems Tracked", len(state_history))
col4.metric("Audit Decisions", len(audit_logs))

st.markdown("---")

# Tab Layout
tab1, tab2, tab3 = st.tabs(["📈 Health Timeline", "📋 Reconciled State History", "🔍 Explainable Audit Trail"])

with tab1:
    st.subheader("Subsystem Health State Over Time")
    plot_path = "data/outputs/subsystem_health_timeline.png"
    
    # Generate plot using method or fallback to displaying output
    try:
        visualizer = StateVisualizer()
        if hasattr(visualizer, 'plot_timeline'):
            visualizer.plot_timeline(state_history, plot_path)
        elif hasattr(StateVisualizer, 'generate_plot'):
            StateVisualizer.generate_plot(state_history, plot_path)
    except Exception:
        pass

    if os.path.exists(plot_path):
        st.image(plot_path, use_column_width=True)

with tab2:
    st.subheader("Reconciled State JSON View")
    formatted_state = {
        sub: [
            {
                "timestamp": entry["timestamp"].isoformat() if hasattr(entry["timestamp"], "isoformat") else str(entry.get("timestamp", "")),
                "state": entry.get("state", "Unknown"),
                "controlling_source": entry.get("controlling_source", entry.get("source", "N/A")),
                "winning_event_id": entry.get("winning_event_id", entry.get("event_id", "N/A"))
            }
            for entry in history
        ]
        for sub, history in state_history.items()
    }
    st.json(formatted_state)

with tab3:
    st.subheader("Decision Trace Log")
    audit_data = [
        {
            "Subsystem": getattr(log, "subsystem", "N/A"),
            "Window Start": str(getattr(log, "window_start", "")),
            "Window End": str(getattr(log, "window_end", "")),
            "Winning Event": getattr(log, "winning_event_id", "N/A"),
            "Winning Source": getattr(log, "winning_source", "N/A"),
            "Rule Applied": getattr(log, "rule_applied", "N/A"),
            "Reasoning": getattr(log, "reasoning", "N/A")
        }
        for log in audit_logs
    ]
    st.dataframe(pd.DataFrame(audit_data), use_container_width=True)
       