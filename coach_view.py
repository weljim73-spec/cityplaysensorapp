"""
Mia Training Tracker - Coach View (Read-Only)
Automatically syncs with Google Sheets and displays all analytics
For sharing with coaches
"""

import streamlit as st

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Mia Training Tracker - Coach View",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import pandas as pd

from shared import (
    get_central_time,
    load_data_from_google_sheets,
    calculate_personal_records,
)

# Import tab modules
from tabs import (
    dashboard,
    ai_insights,
    analytics,
    speed,
    agility,
    ball_work,
    match_play,
    personal_records,
)

# Custom CSS for coach view
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .read-only-badge {
        background-color: #f0f2f6;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin-bottom: 2rem;
        font-size: 0.9rem;
        color: #666;
    }
    .refresh-info {
        background-color: #e8f4f8;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        text-align: center;
        margin-bottom: 1rem;
        font-size: 0.85rem;
        color: #1f1f1f;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'personal_records' not in st.session_state:
    st.session_state.personal_records = {}
if 'pr_dates' not in st.session_state:
    st.session_state.pr_dates = {}
if 'ai_insights_generated' not in st.session_state:
    st.session_state.ai_insights_generated = False
    st.session_state.ai_insights_report = ""

# Open Graph meta tags for link previews
st.markdown("""
<meta property="og:title" content="Mia Training Tracker - Coach View" />
<meta property="og:description" content="Read-only soccer performance analytics dashboard for coaches" />
<meta property="og:image" content="https://raw.githubusercontent.com/weljim73-spec/cityplaysensorapp/main/preview.png" />
<meta property="og:type" content="website" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Mia Training Tracker - Coach View" />
<meta name="twitter:description" content="Read-only performance dashboard" />
<meta name="twitter:image" content="https://raw.githubusercontent.com/weljim73-spec/cityplaysensorapp/main/preview.png" />
""", unsafe_allow_html=True)

# Main App
st.markdown('<div class="main-header">⚽ Mia Training Tracker - Coach View</div>', unsafe_allow_html=True)
st.markdown('<div class="read-only-badge">📖 Read-Only View for Coaches | Auto-Syncs with Latest Data</div>', unsafe_allow_html=True)

# Auto-load data from Google Sheets (read-only)
with st.spinner("🔄 Loading latest training data from cloud..."):
    df, error = load_data_from_google_sheets(readonly=True)

if error:
    st.error(f"❌ Error loading data: {error}")
    st.info("Please contact the administrator to configure Google Sheets access.")
    st.stop()

if df is None or len(df) == 0:
    st.warning("No training data available yet.")
    st.stop()

# Store df in session state for tab modules
st.session_state.df = df

# Calculate personal records and store in session state
pr_records, pr_dates, pr_foot = calculate_personal_records(df)
st.session_state.personal_records = pr_records
st.session_state.pr_dates = pr_dates
st.session_state.pr_foot = pr_foot

# Show last sync time with refresh button
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f'<div class="refresh-info">📊 Showing {len(df)} training sessions | Last refreshed: {get_central_time().strftime("%Y-%m-%d %H:%M:%S %Z")}</div>', unsafe_allow_html=True)
with col2:
    if st.button("🔄 Refresh", type="primary", use_container_width=True):
        st.rerun()

# Create tabs - 8 tabs (no Upload tab for read-only view)
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Dashboard",
    "🤖 AI Insights",
    "📈 Analytics",
    "⚡ Speed",
    "🔄 Agility",
    "⚽ Ball Work",
    "⚽ Match Play",
    "🏆 Personal Records"
])

# Render tabs using shared modules
with tab1:
    dashboard.render()

with tab2:
    ai_insights.render()

with tab3:
    analytics.render()

with tab4:
    speed.render()

with tab5:
    agility.render()

with tab6:
    ball_work.render()

with tab7:
    match_play.render()

with tab8:
    personal_records.render()
