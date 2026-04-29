import sys
sys.stdout.reconfigure(encoding="utf-8", errors="ignore")
sys.stderr.reconfigure(encoding="utf-8", errors="ignore")
import html
import streamlit as st
import requests
import pandas as pd
from datetime import date
import plotly.express as px
import time
from backend.domain.models import ComplianceRecord
from backend.core.database import SessionLocal
import streamlit.components.v1 as components
import html
import datetime

# ⏱ Auto-refresh every 10 seconds
REFRESH_INTERVAL = 10

# Store last refresh time
if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = time.time()

# Check if refresh needed
if time.time() - st.session_state.last_refresh > REFRESH_INTERVAL:
    st.session_state.last_refresh = time.time()
    st.rerun()

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="Intern Progress Tracking",
    layout="wide"
)

st.title("📊 Intern Progress Tracking System")

# =========================================================
# ⚙️ EMAIL PROCESSING (ASYNC)
# =========================================================
st.header("⚙️ Email Processing")

if st.button("⚙️ Process Pending Emails"):
    try:
        res = requests.post(f"{BASE_URL}/email/process")

        if res.status_code == 200:
            st.info("🚀 Processing started in background...")
        else:
            st.error("Failed to start processing.")

    except Exception:
        st.error("Backend not reachable.")

# =========================================================
# 📡 STATUS POLLING
# =========================================================
st.subheader("📡 Processing Status")

status_placeholder = st.empty()

for _ in range(15):
    try:
        res = requests.get(f"{BASE_URL}/email/status")
        data = res.json()

        if data["is_running"]:
            status_placeholder.warning("⏳ Processing emails...")
        else:
            if data["last_status"] == "success" or "success" in data["last_status"]:
                status_placeholder.success("✅ Emails processed successfully")
                break
            elif "failed" in data["last_status"]:
                status_placeholder.error(data["last_status"])
                break
            else:
                status_placeholder.info("Idle")

    except Exception:
        status_placeholder.error("Status check failed")

    time.sleep(1)

st.divider()

# =========================================================
# FETCH HR UPDATES
# =========================================================
def fetch_updates():
    try:
        res = requests.get(f"{BASE_URL}/hr/updates")
        res.raise_for_status()
        return res.json()
    except Exception:
        st.error("Backend not responding at /hr/updates")
        st.stop()

updates = fetch_updates()

if not updates:
    st.info("No intern activity yet.")
    st.stop()

df = pd.DataFrame(updates)

df = df[df["intern_id"].apply(lambda x: isinstance(x, str) and "@" in x)]

if df.empty:
    st.warning("No valid intern email data.")
    st.stop()

# =========================================================
# NORMALIZE TIME
# =========================================================
if "created_at" in df.columns:
    df["event_time"] = pd.to_datetime(df["created_at"], utc=True)
elif "time" in df.columns:
    df["event_time"] = pd.to_datetime(df["time"], utc=True)
else:
    st.error("No time column found.")
    st.stop()

df["event_time"] = df["event_time"].dt.tz_convert("Asia/Kolkata")
df = df.sort_values("event_time")
df["intern_id"] = df["intern_id"].astype(str)

# =========================================================
# PROGRESS CLASSIFICATION
# =========================================================
def classify_summary(summary: str) -> str:
    s = summary.lower()
    if any(w in s for w in ["blocked", "stuck", "failed", "unresolved", "unable"]):
        return "Blocked"
    elif any(w in s for w in ["delay", "issue", "problem", "timeout"]):
        return "At Risk"
    else:
        return "Progress"

df["progress_state"] = df["summary"].apply(classify_summary)

# =========================================================
# KPI OVERVIEW
# =========================================================
st.subheader("📊 Intern Consistency Overview")

today = pd.Timestamp(date.today())
interns = sorted(df["intern_id"].unique())

cols = st.columns(min(3, len(interns)))

for i, intern in enumerate(interns):

    intern_df = df[df["intern_id"] == intern]

    active_days = intern_df["event_time"].dt.date.nunique()
    last_update = intern_df["event_time"].max().date()
    days_since_last = (today.date() - last_update).days

    with cols[i % len(cols)]:
        st.metric(
            label=intern,
            value=f"{active_days} active days",
            delta=f"{days_since_last} days since last update"
        )

st.divider()

# =========================================================
# 📊 MONTHLY REMINDER ANALYSIS
# =========================================================
st.subheader("📊 Monthly Reminder Analysis")

db = SessionLocal()
records = db.query(ComplianceRecord).all()
db.close()

if not records:
    st.success("No reminder alerts have been sent.")
else:

    alert_data = []

    for r in records:
        alert_data.append({
            "intern": r.intern_email,
            "date": pd.to_datetime(r.created_at).tz_localize(None)
        })

    alert_df = pd.DataFrame(alert_data)

    alert_df["month"] = alert_df["date"].dt.to_period("M").astype(str)
    alert_df["week"] = alert_df["date"].dt.day.apply(lambda d: f"Week{((d-1)//7)+1}")

    months = sorted(alert_df["month"].unique())

    selected_month = st.selectbox(
        "Select Month",
        months,
        key="monthly_table"
    )

    month_df = alert_df[alert_df["month"] == selected_month]

    pivot_df = (
        month_df
        .pivot_table(
            index="intern",
            columns="week",
            values="date",
            aggfunc="count",
            fill_value=0
        )
    )

    pivot_df["Total"] = pivot_df.sum(axis=1)

    st.dataframe(
    pivot_df.style
        .format(precision=0)

        # 🎯 Highlight high reminder counts (problem areas)
        .apply(lambda row: [
            "background-color: #1f2937; color: #9ca3af" if val == 0 else
            "background-color: #f59e0b; color: #111827" if val <= 2 else
            "background-color: #dc2626; color: white"
            for val in row
        ], axis=1)

        # 📊 Highlight total column strongly
        .apply(lambda col: [
            "background-color: #3b82f6; color: white; font-weight: bold"
            if col.name == "Total" else ""
            for _ in col
        ], axis=0)

        # ✨ Clean base styling
        .set_properties(**{
            "border": "1px solid #1f2937",
            "text-align": "center"
        }),

    use_container_width=True
)

st.divider()

# =========================================================
# 📅 CALENDAR VIEW
# =========================================================
st.subheader("📅 Reminder Calendar View")

if records:

    intern_list = sorted(alert_df["intern"].unique())

    selected_intern = st.selectbox(
        "Select Intern",
        intern_list,
        key="calendar_intern"
    )

    intern_alerts = alert_df[alert_df["intern"] == selected_intern].copy()

    intern_alerts.loc[:, "month"] = (
        intern_alerts["date"].dt.to_period("M").astype(str)
    )

    months = sorted(intern_alerts["month"].unique())

    selected_month = st.selectbox(
        "Select Month",
        months,
        key="calendar_month"
    )

    month_df = intern_alerts[intern_alerts["month"] == selected_month]

    reminder_days = set(month_df["date"].dt.day.tolist())

    cols = st.columns(7)

    for i in range(1, 32):
        col = cols[(i - 1) % 7]

        if i in reminder_days:
            col.markdown(
                f"""
                <div style="
                    background:#3b82f6;
                    padding:15px;
                    border-radius:10px;
                    text-align:center;
                    color:ffffff;
                    font-weight:bold;
                    box-shadow:0 0 10px rgba(215,0,64,0.4);
                ">
                    {i}
                </div>
                """,
                unsafe_allow_html=True
            )

        else:
            col.markdown(
                f"""
                <div style="
                background:#1f2937;
                padding:15px;
                border-radius:10px;
                text-align:center;
                color:#9ca3af;
            ">
                {i}
            </div>
            """,
            unsafe_allow_html=True
        )

st.divider()

# =========================================================
# 📈 MOMENTUM TREND
# =========================================================
st.subheader("📈 Momentum Trend")

MOMENTUM_MAP = {
    "Blocked": 0,
    "At Risk": 1,
    "Progress": 2
}

df["momentum_score"] = df["progress_state"].map(MOMENTUM_MAP)

selected_for_momentum = st.selectbox(
    "Select Intern for Momentum Analysis",
    interns,
    key="momentum"
)

momentum_df = df[df["intern_id"] == selected_for_momentum].copy()
momentum_df["update_index"] = range(len(momentum_df))

fig = px.line(
    momentum_df,
    x="update_index",
    y="momentum_score",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

# =========================================================
# 🧾 TIMELINE
# =========================================================
st.subheader("🧾 Intern Progress Timeline")

selected_intern = st.selectbox(
    "Select Intern",
    interns,
    key="timeline"
)

intern_df = df[df["intern_id"] == selected_intern].copy()
intern_df = intern_df.sort_values("event_time", ascending=False)

color_map = {
    "Blocked": "#ef4444",
    "At Risk": "#f59e0b",
    "Progress": "#10b981"
}

full_html = ""

for _, row in intern_df.iterrows():

    color = color_map.get(row["progress_state"], "#60a5fa")
    safe_summary = html.escape(str(row["summary"]))

    full_html += f"""
    <div style="
        margin-bottom:20px;
        padding:20px;
        border-radius:12px;
        background:#111827;
        border:1px solid #1f2937;
        font-family:sans-serif;
    ">
        <div style="font-size:16px; color:#9ca3af; margin-bottom:10px;">
            🗓 {row['event_time'].strftime('%d %b %Y %H:%M')}
        </div>

        <div style="
            font-size:14px;
            font-weight:bold;
            color:{color};
            margin-bottom:10px;
        ">
            {row['progress_state']}
        </div>

        <div style="
                    font-size:16px;
                    line-height:1.6;
                    font-family: 'Inter', sans-serif;
                    color:#e5e7eb;">
            {safe_summary}
        </div>
    </div>
    """

# ✅ Render properly using components (THIS FIXES EVERYTHING)
components.html(full_html, height=600, scrolling=True)

# =========================================================
# RAW DATA
# =========================================================
# =========================================================
# RAW DATA (CLEAN + EXPANDED)
# =========================================================
with st.expander("🔍 View Raw HR Data"):

    df_display = df.copy()

    # ❌ Remove unwanted columns
    cols_to_remove = ["time"]
    df_display = df_display.drop(columns=[c for c in cols_to_remove if c in df_display.columns])

    # ⏱ Format event_time → only till seconds
    if "event_time" in df_display.columns:
        df_display["event_time"] = df_display["event_time"].dt.strftime("%Y-%m-%d %H:%M:%S")

    # 📏 Expand full width + better UI
    st.dataframe(
        df_display,
        use_container_width=True,
        height=500
    )