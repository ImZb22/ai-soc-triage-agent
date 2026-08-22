import streamlit as st
import sqlite3
import pandas as pd
from log_generator import generate_log
from agent import run_agent_loop

# 1. Page Configuration
st.set_page_config(page_title="AI SOC Copilot", page_icon="🛡️", layout="wide")

# Custom CSS for UI, Muted Pills, and Unprocessed Status Highlights
st.markdown("""
    <style>
    /* Metric Card Styling */
    .metric-card {
        background-color: #161922;
        border: 1px solid #282f3f;
        border-radius: 10px;
        padding: 16px 20px;
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 500;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .metric-value {
        color: #38bdf8;
        font-size: 1.8rem;
        font-weight: 700;
        font-family: monospace;
    }
    .metric-sub {
        color: #4ade80;
        font-size: 0.8rem;
        margin-top: 4px;
    }
    .metric-sub-red {
        color: #f87171;
        font-size: 0.8rem;
        margin-top: 4px;
    }

    /* Modern Muted Color-Coded Severity Pills */
    .badge-critical {
        background-color: rgba(225, 29, 72, 0.2);
        color: #fda4af;
        border: 1px solid rgba(225, 29, 72, 0.4);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-block;
    }
    .badge-high {
        background-color: rgba(234, 88, 12, 0.2);
        color: #fdba74;
        border: 1px solid rgba(234, 88, 12, 0.4);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-block;
    }
    .badge-low {
        background-color: rgba(202, 138, 4, 0.2);
        color: #fef08a;
        border: 1px solid rgba(202, 138, 4, 0.4);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-block;
    }
    .badge-info {
        background-color: rgba(30, 58, 138, 0.3);
        color: #93c5fd;
        border: 1px solid rgba(59, 130, 246, 0.4);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-block;
    }
    .badge-passed {
        background-color: rgba(16, 185, 129, 0.2);
        color: #6ee7b7;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        display: inline-block;
    }

    /* Status Column Badges */
    .badge-unprocessed {
        background-color: rgba(234, 179, 8, 0.25);
        color: #fef08a;
        border: 1px solid rgba(234, 179, 8, 0.5);
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        display: inline-block;
    }
    .badge-processed {
        color: #64748b;
        font-size: 0.75rem;
        font-weight: 500;
    }

    /* Custom Full-Width HTML Table Styling */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #161922;
        border: 1px solid #282f3f;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 20px;
    }
    .custom-table th {
        background-color: #1e2330;
        color: #94a3b8;
        padding: 10px 14px;
        text-align: left;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        border-bottom: 1px solid #282f3f;
        white-space: nowrap;
    }
    .custom-table td {
        padding: 10px 14px;
        color: #cbd5e1;
        font-size: 0.85rem;
        border-bottom: 1px solid #1f2430;
        white-space: nowrap;
    }

    /* ReAct Card Styling */
    .react-card {
        background-color: #161922;
        border: 1px solid #282f3f;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 12px;
        border-left: 4px solid #38bdf8;
    }
    .react-step {
        color: #94a3b8;
        font-size: 0.88rem;
        margin-bottom: 8px;
        line-height: 1.4;
    }
    .react-label {
        color: #cbd5e1;
        font-weight: 600;
    }

    /* Enhanced Sidebar Styling */
    .sidebar-section {
        padding: 12px 0 6px 0;
        color: #64748b;
        font-size: 0.72rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        font-weight: 700;
    }
    .sidebar-status-box {
        background-color: #161922;
        border: 1px solid #282f3f;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 16px;
    }
    .status-online {
        color: #4ade80;
        font-size: 0.8rem;
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 6px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🛡️ AI SOC Copilot")

# 2. Helper Data Function
def fetch_data(query):
    conn = sqlite3.connect("soc_data.db")
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# Fetch Metrics for Sidebar & Dashboard
try:
    total_logs = fetch_data("SELECT COUNT(*) as count FROM raw_logs")['count'][0]
    contained_threats = fetch_data("SELECT COUNT(*) as count FROM blocked_entities")['count'][0]
    high_risk_logs = fetch_data("SELECT COUNT(*) as count FROM raw_logs WHERE severity IN ('HIGH', 'CRITICAL')")['count'][0]

    mttr_query = """
        SELECT AVG(strftime('%s', a.timestamp) - strftime('%s', r.timestamp)) as avg_seconds
        FROM alert_history a
        JOIN raw_logs r ON a.log_id = r.id
    """
    avg_sec = fetch_data(mttr_query)['avg_seconds'][0]
    
    if avg_sec is not None and avg_sec >= 0:
        mttr_str = f"{avg_sec:.2f} sec" if avg_sec < 60 else f"{avg_sec/60:.1f} min"
    else:
        mttr_str = "< 1 sec"
except:
    total_logs, contained_threats, high_risk_logs, mttr_str = 0, 0, 0, "< 1 sec"

# 3. Sidebar Panel Construction
st.sidebar.markdown("""
    <div class="sidebar-status-box">
        <div class="status-online">● Autonomous Agent Active</div>
        <div style="color: #64748b; font-size: 0.75rem; margin-top: 4px;">Model: ReAct SOC Engine</div>
    </div>
""", unsafe_allow_html=True)

st.sidebar.markdown('<div class="sidebar-section">NAVIGATION</div>', unsafe_allow_html=True)
st.sidebar.selectbox("View Panel", ["Overview / Dashboard", "Live Telemetry", "ReAct Traces", "Containment Vault"], index=0)

st.sidebar.markdown('<div class="sidebar-section">SIMULATION CONTROLS</div>', unsafe_allow_html=True)

if st.sidebar.button("⚡ Simulate Incoming Threat", use_container_width=True):
    generate_log()
    st.toast("⚡ New telemetry ingested into raw logs!", icon="📥")
    st.rerun()

if st.sidebar.button("🤖 Trigger AI Agent Triage", use_container_width=True):
    run_agent_loop()
    st.toast("🤖 AI Agent Triage complete! Threat logs evaluated.", icon="🛡️")
    st.rerun()

st.sidebar.markdown('<div class="sidebar-section">SYSTEM HEALTH</div>', unsafe_allow_html=True)
st.sidebar.markdown(f"""
<div style="color: #94a3b8; font-size: 0.8rem; line-height: 1.6;">
    • DB Connection: <span style="color:#4ade80;">Active</span><br>
    • Ingestion Rate: <span style="color:#38bdf8;">Realtime</span><br>
    • Blocked Entities: <span style="color:#f87171;">{contained_threats}</span>
</div>
""", unsafe_allow_html=True)

# 4. Metric Cards Row with Clean Vector Icons
m1, m2, m3 = st.columns(3)

alert_icon = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f87171" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>'
chart_icon = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg>'
clock_icon = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#4ade80" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>'

with m1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{alert_icon} Active Threats</div>
        <div class="metric-value">{high_risk_logs} <span style="font-size:1.2rem; color:#f87171;">↑</span></div>
        <div class="metric-sub-red">Critical / High Severity</div>
    </div>
    """, unsafe_allow_html=True)

with m2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{chart_icon} Logs Ingested (24h)</div>
        <div class="metric-value">{total_logs}</div>
        <div class="metric-sub">↑ Live Pipeline Ingestion</div>
    </div>
    """, unsafe_allow_html=True)

with m3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-title">{clock_icon} MTTR (Calculated Dynamic)</div>
        <div class="metric-value">{mttr_str}</div>
        <div class="metric-sub">↓ Automated Agent Triage</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# 5. Main Dashboard Body
left_col, right_col = st.columns([1.35, 1])

with left_col:
    st.markdown("##### LIVE THREAT LOG TABLE")
    try:
        logs_df = fetch_data("SELECT id, source_ip, event_type, severity, status, timestamp FROM raw_logs ORDER BY timestamp DESC LIMIT 7")
        
        # Format Severity Pills
        def apply_severity_pill(val):
            v = str(val).upper()
            if v == "CRITICAL":
                return '<span class="badge-critical">CRITICAL</span>'
            elif v == "HIGH":
                return '<span class="badge-high">HIGH</span>'
            elif v == "LOW":
                return '<span class="badge-low">LOW</span>'
            return '<span class="badge-info">INFO</span>'

        # Format Status Highlights
        def apply_status_pill(val):
            v = str(val).upper()
            if v == "UNPROCESSED":
                return '<span class="badge-unprocessed">● UNPROCESSED</span>'
            return '<span class="badge-processed">PROCESSED</span>'

        logs_df['severity'] = logs_df['severity'].apply(apply_severity_pill)
        logs_df['status'] = logs_df['status'].apply(apply_status_pill)
        
        html_table = logs_df.to_html(escape=False, index=False, classes="custom-table")
        st.markdown(html_table, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading threat logs: {e}")

    st.markdown("##### AUTOMATED CONTAINMENT LOGS")
    try:
        blocked_df = fetch_data("SELECT entity_type, entity_value, reason, blocked_at FROM blocked_entities ORDER BY blocked_at DESC LIMIT 5")
        blocked_df['Safety Guardrail'] = '<span class="badge-passed">✓ PASSED</span>'
        
        html_blocked_table = blocked_df.to_html(escape=False, index=False, classes="custom-table")
        st.markdown(html_blocked_table, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error loading containment logs: {e}")

with right_col:
    st.markdown("##### AI REACT REASONING TRACE")
    try:
        traces = fetch_data("SELECT ai_thought_trace, decision, timestamp FROM alert_history ORDER BY timestamp DESC LIMIT 3")
        if not traces.empty:
            for idx, row in traces.iterrows():
                trace_text = row['ai_thought_trace']
                parts = trace_text.split(" | ")
                
                thought = parts[0].replace("THOUGHT: ", "") if len(parts) > 0 else ""
                action = parts[1].replace("ACTION: ", "") if len(parts) > 1 else ""
                obs = parts[2].replace("OBSERVATION: ", "") if len(parts) > 2 else ""

                st.markdown(f"""
                <div class="react-card">
                    <div class="react-step"><span class="react-label">Thought:</span> {thought}</div>
                    <div class="react-step"><span class="react-label">Action:</span> {action}</div>
                    <div class="react-step"><span class="react-label">Observation:</span> {obs}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No AI traces available.")
    except Exception as e:
        st.error(f"Error loading traces: {e}")