"""
Mia Training Tracker - Streamlit Web App
Soccer training analytics and tracking application
Accessible from any browser including mobile devices
"""

import streamlit as st

# Page configuration - MUST be first Streamlit command
st.set_page_config(
    page_title="Mia Training Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
)

import pandas as pd
import numpy as np
from datetime import datetime
import pytz
from PIL import Image
import io
from io import BytesIO
import re
import os

# Import matplotlib with proper backend for Streamlit
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

from shared import (
    GSHEETS_AVAILABLE,
    COLUMN_MAPPING,
    NUMERIC_COLUMNS,
    get_central_time,
    connect_to_google_sheets,
    load_data_from_google_sheets,
    save_data_to_google_sheets,
    append_row_to_google_sheets,
    clear_gsheets_cache,
    calculate_personal_records as _calculate_personal_records,
    generate_executive_summary,
    generate_30day_change_summary,
    analyze_training_data,
)

# Try to import pytesseract and configure for Streamlit Cloud
try:
    import pytesseract

    # Configure Tesseract path for different environments
    # Streamlit Cloud uses /usr/bin/tesseract
    if os.path.exists('/usr/bin/tesseract'):
        pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    elif os.path.exists('/opt/homebrew/bin/tesseract'):
        pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

    # Test if tesseract is working
    try:
        pytesseract.get_tesseract_version()
        OCR_AVAILABLE = True
        OCR_ERROR = None
    except Exception as e:
        OCR_AVAILABLE = False
        OCR_ERROR = "Tesseract not found"
except ImportError:
    OCR_AVAILABLE = False
    OCR_ERROR = "pytesseract module not installed"

# Custom CSS for mobile responsiveness and hide sidebar
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #f8f9fa;
    }
    /* AGGRESSIVE styling for sidebar collapse button - all possible selectors */
    /* When collapsed */
    [data-testid="collapsedControl"] {
        background-color: #ff4444 !important;
        border: 3px solid #cc0000 !important;
        box-shadow: 0 0 10px rgba(255, 68, 68, 0.8) !important;
    }
    [data-testid="collapsedControl"]:hover {
        background-color: #cc0000 !important;
    }
    [data-testid="collapsedControl"] svg {
        color: white !important;
        fill: white !important;
    }
    /* Target sidebar header with multiple selectors */
    section[data-testid="stSidebar"] > div:first-child button,
    [data-testid="stSidebar"] button[kind="header"],
    [data-testid="stSidebar"] button[data-testid="baseButton-header"],
    [data-testid="stSidebar"] [class*="viewerBadge"] button {
        background: #ff4444 !important;
        background-color: #ff4444 !important;
        border: 3px solid #cc0000 !important;
        box-shadow: 0 0 10px rgba(255, 68, 68, 0.8) !important;
        min-width: 40px !important;
        min-height: 40px !important;
    }
    section[data-testid="stSidebar"] > div:first-child button:hover,
    [data-testid="stSidebar"] button[kind="header"]:hover {
        background: #cc0000 !important;
        background-color: #cc0000 !important;
    }
    /* Force white icons everywhere in sidebar header */
    section[data-testid="stSidebar"] > div:first-child svg,
    section[data-testid="stSidebar"] > div:first-child svg path,
    [data-testid="stSidebar"] button svg,
    [data-testid="stSidebar"] button svg path {
        color: white !important;
        fill: white !important;
        stroke: white !important;
    }
    /* Nuclear option - style ALL buttons at top of sidebar */
    [data-testid="stSidebar"] div[data-testid="stToolbar"] button {
        background-color: #ff4444 !important;
        border: 3px solid #cc0000 !important;
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
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []
if 'initial_load_done' not in st.session_state:
    st.session_state.initial_load_done = False


def load_excel_file(uploaded_file):
    """Load and process Excel file"""
    try:
        df = pd.read_excel(uploaded_file)

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        # Apply column mapping
        df.rename(columns=COLUMN_MAPPING, inplace=True)

        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        st.session_state.df = df
        calculate_personal_records()

        return True, f"✅ Loaded {len(df)} sessions successfully!"
    except Exception as e:
        return False, f"❌ Error loading file: {str(e)}"

def calculate_personal_records():
    """Calculate all personal records from loaded data"""
    if st.session_state.df is None or len(st.session_state.df) == 0:
        return

    df = st.session_state.df

    pr_columns = {
        'top_speed': 'Top Speed',
        'sprint_distance': 'Sprint Distance',
        'ball_touches': 'Ball Touches',
        'kicking_power': 'Kicking Power',
        'total_distance': 'Total Distance',
        'intense_turns': 'Intense Turns'
    }

    personal_records = {}
    pr_dates = {}
    pr_foot = {}  # Track which foot for kicking power

    for col, name in pr_columns.items():
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            max_val = numeric_col.max()
            if pd.notna(max_val):
                personal_records[col] = max_val
                max_idx = numeric_col.idxmax()
                if 'date' in df.columns and pd.notna(df.loc[max_idx, 'date']):
                    pr_dates[col] = pd.to_datetime(df.loc[max_idx, 'date'])
                else:
                    pr_dates[col] = None

                # For kicking_power, determine which foot
                if col == 'kicking_power':
                    left_power = pd.to_numeric(df.loc[max_idx, 'left_kicking_power_mph'], errors='coerce') if 'left_kicking_power_mph' in df.columns else 0
                    right_power = pd.to_numeric(df.loc[max_idx, 'right_kicking_power_mph'], errors='coerce') if 'right_kicking_power_mph' in df.columns else 0
                    if pd.notna(left_power) and pd.notna(right_power):
                        pr_foot['kicking_power'] = 'L' if left_power >= right_power else 'R'
                    elif pd.notna(left_power):
                        pr_foot['kicking_power'] = 'L'
                    elif pd.notna(right_power):
                        pr_foot['kicking_power'] = 'R'
                    else:
                        pr_foot['kicking_power'] = ''

    # L/R Touch Ratio
    if 'left_touches' in df.columns and 'right_touches' in df.columns:
        best_ratio = None
        best_distance = float('inf')
        best_date = None

        for idx, row in df.iterrows():
            left = pd.to_numeric(row.get('left_touches'), errors='coerce')
            right = pd.to_numeric(row.get('right_touches'), errors='coerce')

            if pd.notna(left) and pd.notna(right) and left > 0 and right > 0:
                ratio = left / right

                if ratio >= 0.5:
                    distance = abs(ratio - 0.5)
                else:
                    distance = 0.5 - ratio

                if distance < best_distance:
                    best_distance = distance
                    best_ratio = ratio
                    if 'date' in row and pd.notna(row['date']):
                        best_date = pd.to_datetime(row['date'])

        personal_records['left_right_ratio'] = best_ratio if best_ratio else 0.0
        pr_dates['left_right_ratio'] = best_date

    # L/R Ratio Average
    if 'left_touches' in df.columns and 'right_touches' in df.columns:
        left = pd.to_numeric(df['left_touches'], errors='coerce')
        right = pd.to_numeric(df['right_touches'], errors='coerce')
        valid_mask = (left > 0) & (right > 0)

        if valid_mask.any():
            ratios = left[valid_mask] / right[valid_mask]
            personal_records['left_right_ratio_avg'] = ratios.mean()
        else:
            personal_records['left_right_ratio_avg'] = 0.0

        pr_dates['left_right_ratio_avg'] = None

    st.session_state.personal_records = personal_records
    st.session_state.pr_dates = pr_dates
    st.session_state.pr_foot = pr_foot

def parse_ocr_text(text):
    """Parse OCR text to extract metrics - enhanced version from v4.2"""
    extracted = {}

    # Common patterns - more flexible to handle OCR variations
    patterns = {
        # Session info
        'duration': r'(\d+)\s*min',
        'training_type': r'(technical|speed|agility|conditioning)',
        'intensity': r'(moderate|light|intense|hard)',

        # Movement metrics
        'total_distance': r'(?:total\s+)?distance[:\s]*(\d+\.?\d*)\s*mi',
        'sprint_distance': r'sprint\s+distance[:\s]*(\d+\.?\d*)\s*(?:yd|yards)',
        'top_speed': r'top\s+speed[:\s]*(\d+\.?\d*)\s*mph',
        'num_sprints': r'sprints?\s*[:\s#]*(\d+)',
        'accelerations': r'(?:accl?|accel(?:eration)?s?)\s*[:\s/]+\s*(?:decl?)?\s*(\d+)',

        # Ball work
        'ball_touches': r'(?:ball\s+)?touches\s*[:\s#]*(\d+)',

        # Kicking power
        'kicking_power': r'(?:kicking\s+)?power\s*[:\s]*(\d+\.?\d*)\s*mph',

        # Agility
        'left_turns': r'left\s+turns?\s*[:\s]*(\d+)',
        'right_turns': r'right\s+turns?\s*[:\s]*(\d+)',
        'back_turns': r'back\s+turns?\s*[:\s]*(\d+)',
        'intense_turns': r'intense\s+turns?\s*[:\s#]*(\d+)',
        'avg_turn_entry': r'(?:average\s+)?turn\s+entry\s+speed\s*[:\s]*(\d+\.?\d*)\s*mph',
        'avg_turn_exit': r'(?:average\s+)?turn\s+exit\s+speed\s*[:\s]*(\d+\.?\d*)\s*mph',
    }

    text_lower = text.lower()

    for key, pattern in patterns.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            extracted[key] = match.group(1)

    # Special handling for left/right kicking power
    lines = text_lower.split('\n')
    for i, line in enumerate(lines):
        if 'kicking power' in line and i > 0:
            context = '\n'.join(lines[max(0, i-3):min(len(lines), i+4)])
            power_matches = re.findall(r'(\d+\.?\d*)\s*mph', context)
            if len(power_matches) >= 2:
                extracted['left_kicking_power_mph'] = power_matches[0]
                extracted['right_kicking_power_mph'] = power_matches[1]
                break

    # Touch percentages and counts
    touch_pattern = re.search(r'(\d+)\s*\((\d+)%\)[^\d]*touch[^\d]*(\d+)\s*\((\d+)%\)', text_lower, re.IGNORECASE)
    if touch_pattern:
        extracted['left_touches'] = touch_pattern.group(1)
        extracted['left_pct'] = touch_pattern.group(2)
        extracted['right_touches'] = touch_pattern.group(3)
        extracted['right_pct'] = touch_pattern.group(4)

    # Aggressive turn detection
    if 'left_turns' not in extracted:
        for pattern in [r'(\d+)\s*[^\w\d]*left\s+turns?', r'left\s+turns?\s*[^\w\d]*(\d+)']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted['left_turns'] = match.group(1)
                break

    if 'right_turns' not in extracted:
        for pattern in [r'(\d+)\s*[^\w\d]*right\s+turns?', r'right\s+turns?\s*[^\w\d]*(\d+)']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted['right_turns'] = match.group(1)
                break

    if 'back_turns' not in extracted:
        for pattern in [r'(\d+)\s*[^\w\d]*back\s+turns?', r'back\s+turns?\s*[^\w\d]*(\d+)']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted['back_turns'] = match.group(1)
                break

    # Ultimate fallback for back turns - process of elimination
    if 'back_turns' not in extracted and 'left_turns' in extracted and 'right_turns' in extracted:
        agility_match = re.search(r'agility', text_lower, re.IGNORECASE)
        if agility_match:
            agility_section = text_lower[agility_match.end():agility_match.end()+500]
            numbers = re.findall(r'\b(\d{2,3})\b', agility_section)
            if len(numbers) >= 3:
                for num in numbers:
                    if num != extracted.get('left_turns') and num != extracted.get('right_turns'):
                        num_val = int(num)
                        if 20 <= num_val <= 150:
                            extracted['back_turns'] = num
                            break

    return extracted


# Open Graph meta tags for link previews
st.markdown("""
<meta property="og:title" content="Mia Training Tracker" />
<meta property="og:description" content="Soccer Performance Analytics - Track speed, agility, ball work, and comprehensive training metrics" />
<meta property="og:image" content="https://raw.githubusercontent.com/weljim73-spec/cityplaysensorapp/main/preview.png" />
<meta property="og:type" content="website" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Mia Training Tracker" />
<meta name="twitter:description" content="Soccer Performance Analytics" />
<meta name="twitter:image" content="https://raw.githubusercontent.com/weljim73-spec/cityplaysensorapp/main/preview.png" />
""", unsafe_allow_html=True)

# Main App Header
st.markdown('<div class="main-header">⚽ Mia Training Tracker</div>', unsafe_allow_html=True)

# Display OCR warning if not available
if not OCR_AVAILABLE:
    st.warning(f"⚠️ OCR not available: {OCR_ERROR}. Manual data entry only.")

# ============================================================================
# SIDEBAR - Data Management (Google Sheets Only)
# ============================================================================
with st.sidebar:
    st.header("☁️ Google Sheets")

    # Check if Google Sheets is configured
    if GSHEETS_AVAILABLE and "google_sheets_url" in st.secrets:

        # Load from Google Sheets
        if st.button("🔄 Load Data from Google Sheets", type="primary", use_container_width=True):
            with st.spinner("Loading data from Google Sheets..."):
                df, error = load_data_from_google_sheets()
                if error:
                    st.error(f"❌ **Failed to load data**")
                    st.error(f"Error: {error}")
                    st.info("💡 **Troubleshooting:**\n"
                           "1. Check Google Sheet URL in secrets\n"
                           "2. Verify service account has access\n"
                           "3. Ensure column headers match exactly")
                else:
                    st.session_state.df = df
                    st.session_state.auto_loaded = True
                    calculate_personal_records()
                    st.success(f"✅ Loaded {len(df)} sessions from Google Sheets!")
                    st.rerun()

        st.markdown("---")

        # Save to Google Sheets
        if st.session_state.df is not None and len(st.session_state.df) > 0:
            if st.button("💾 Save Data to Google Sheets", use_container_width=True):
                with st.spinner("Saving to Google Sheets..."):
                    success, error = save_data_to_google_sheets(st.session_state.df)
                    if error:
                        st.error(f"❌ **Failed to save**")
                        st.error(f"Error: {error}")
                    else:
                        st.success("✅ Data saved to Google Sheets!")

        st.markdown("---")

        # Data Status
        st.subheader("📊 Current Data")
        if st.session_state.df is not None and len(st.session_state.df) > 0:
            st.success(f"**{len(st.session_state.df)}** sessions loaded")
            if 'date' in st.session_state.df.columns:
                latest = st.session_state.df['date'].max()
                if pd.notna(latest):
                    st.caption(f"Latest: {latest.strftime('%b %d, %Y')}")
        else:
            st.warning("⚠️ No data loaded")
            st.info("Click '🔄 Load Data from Google Sheets' above to get started")

    else:
        # Google Sheets not configured
        st.error("❌ **Google Sheets Not Configured**")
        st.info("**To configure Google Sheets:**\n\n"
               "1. Go to Streamlit Cloud app settings\n"
               "2. Click 'Secrets' in sidebar\n"
               "3. Add your Google Sheets URL and service account credentials\n\n"
               "See GOOGLE_SHEETS_SETUP_GUIDE.md for detailed instructions.")

        if st.button("📖 View Setup Guide", use_container_width=True):
            st.info("Setup guide is in your repository:\n"
                   "`GOOGLE_SHEETS_SETUP_GUIDE.md`")

# Auto-load data from Google Sheets on app start
if GSHEETS_AVAILABLE and "google_sheets_url" in st.secrets:
    if 'auto_loaded' not in st.session_state:
        st.session_state.auto_loaded = False

    if not st.session_state.auto_loaded:
        with st.spinner("🔄 Auto-loading data from Google Sheets..."):
            df, error = load_data_from_google_sheets()
            if not error and df is not None:
                st.session_state.df = df
                st.session_state.auto_loaded = True
                calculate_personal_records()
                # Force a rerun to display the loaded data
                st.rerun()

# Refresh Data button (visible in main area)
if GSHEETS_AVAILABLE and "google_sheets_url" in st.secrets:
    col_refresh1, col_refresh2, col_refresh3 = st.columns([1, 1, 1])
    with col_refresh2:
        if st.button("🔄 Refresh Data", type="primary", use_container_width=True):
            with st.spinner("Refreshing data from Google Sheets..."):
                df, error = load_data_from_google_sheets()
                if error:
                    st.error(f"❌ Failed to refresh: {error}")
                else:
                    st.session_state.df = df
                    calculate_personal_records()

                    # Clear cached AI insights so user regenerates with refreshed data
                    if 'ai_insights_generated' in st.session_state:
                        st.session_state.ai_insights_generated = False
                    if 'ai_insights_report' in st.session_state:
                        st.session_state.ai_insights_report = ""

                    st.success("✅ Data refreshed!")
                    st.rerun()

st.markdown("---")

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs([
    "📊 Dashboard",
    "📸 Upload & Extract",
    "🤖 AI Insights",
    "📈 Analytics",
    "⚡ Speed",
    "🔄 Agility",
    "⚽ Ball Work",
    "⚽ Match Play",
    "🏆 Personal Records"
])

# Tab 1: Dashboard
with tab1:
    st.header("📊 Training Dashboard")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar or sync from Google Sheets.")
    else:
        df = st.session_state.df.copy()

        # Key Metrics Row 1
        st.subheader("🎯 Key Performance Indicators")
        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            if 'top_speed' in df.columns:
                values = pd.to_numeric(df['top_speed'], errors='coerce').dropna()
                if len(values) > 0:
                    avg_speed = values.mean()
                    best_speed = values.max()
                    st.metric("Top Speed (mph) (avg)", f"{avg_speed:.1f}",
                             delta=f"Best: {best_speed:.1f}", delta_color="normal")

        with col2:
            if 'intense_turns' in df.columns:
                values = pd.to_numeric(df['intense_turns'], errors='coerce').dropna()
                if len(values) > 0:
                    avg_turns = values.mean()
                    best_turns = values.max()
                    st.metric("Intense Turns (avg)", f"{avg_turns:.1f}",
                             delta=f"Best: {best_turns:.1f}", delta_color="normal")

        with col3:
            if 'left_kicking_power_mph' in df.columns:
                left_power = pd.to_numeric(df['left_kicking_power_mph'], errors='coerce').dropna()
                if len(left_power) > 0:
                    avg_left = left_power.mean()
                    best_left = left_power.max()
                    st.metric("Left Foot Power (mph)", f"{avg_left:.1f}",
                             delta=f"Best: {best_left:.1f}", delta_color="normal")
                else:
                    st.metric("Left Foot Power (mph)", "N/A",
                             delta="No data", delta_color="off")

        with col4:
            if 'right_kicking_power_mph' in df.columns:
                right_power = pd.to_numeric(df['right_kicking_power_mph'], errors='coerce').dropna()
                if len(right_power) > 0:
                    avg_right = right_power.mean()
                    best_right = right_power.max()
                    st.metric("Right Foot Power (mph)", f"{avg_right:.1f}",
                             delta=f"Best: {best_right:.1f}", delta_color="normal")
                else:
                    st.metric("Right Foot Power (mph)", "N/A",
                             delta="No data", delta_color="off")

        with col5:
            if 'left_touches' in df.columns and 'right_touches' in df.columns:
                left = pd.to_numeric(df['left_touches'], errors='coerce')
                right = pd.to_numeric(df['right_touches'], errors='coerce')
                valid_mask = (left > 0) & (right > 0)

                if valid_mask.any():
                    ratios = left[valid_mask] / right[valid_mask]
                    avg_ratio = ratios.mean()
                    best_ratio = ratios.max()

                    st.metric("L/R Touch Ratio (avg)", f"{avg_ratio:.2f}",
                             delta=f"Best: {best_ratio:.2f}", delta_color="normal")
                else:
                    st.metric("L/R Touch Ratio (avg)", "N/A",
                             delta="No data", delta_color="off")

        st.markdown("---")

        # Training Summary Row
        st.subheader("📅 Training Summary")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Sessions", len(df))

        with col2:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                date_range = (df['date'].max() - df['date'].min()).days
                st.metric("Training Period (days)", date_range)

        with col3:
            if 'duration' in df.columns:
                total_mins = pd.to_numeric(df['duration'], errors='coerce').sum()
                st.metric("Total Training Time", f"{total_mins/60:.1f} hrs")

        with col4:
            if 'with_ball' in df.columns:
                ball_sessions = (df['with_ball'].str.lower() == 'yes').sum()
                st.metric("Ball Work Sessions", f"{ball_sessions}/{len(df)}")

        st.markdown("---")

        # Recent Performance Trends
        st.subheader("📈 Recent Trends (Last 5 Sessions)")

        if len(df) >= 5:
            recent_df = df.tail(5)

            col1, col2 = st.columns(2)

            with col1:
                # Speed trend
                if 'top_speed' in recent_df.columns and 'date' in recent_df.columns:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    speed_data = recent_df[['date', 'top_speed']].dropna()
                    if len(speed_data) > 0:
                        ax.plot(speed_data['date'], speed_data['top_speed'],
                               marker='o', linewidth=2, markersize=8, color='#1E88E5')
                        ax.set_xlabel('Date', fontsize=10)
                        ax.set_ylabel('Top Speed (mph)', fontsize=10)
                        ax.set_title('Top Speed Trend', fontsize=12, fontweight='bold')
                        ax.grid(True, alpha=0.3)
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        st.pyplot(fig, use_container_width=True)
                        plt.close(fig)

            with col2:
                # Agility trend
                if 'intense_turns' in recent_df.columns and 'date' in recent_df.columns:
                    fig, ax = plt.subplots(figsize=(8, 4))
                    agility_data = recent_df[['date', 'intense_turns']].dropna()
                    if len(agility_data) > 0:
                        ax.plot(agility_data['date'], agility_data['intense_turns'],
                               marker='s', linewidth=2, markersize=8, color='#E53935')
                        ax.set_xlabel('Date', fontsize=10)
                        ax.set_ylabel('Intense Turns', fontsize=10)
                        ax.set_title('Agility Trend', fontsize=12, fontweight='bold')
                        ax.grid(True, alpha=0.3)
                        plt.xticks(rotation=45)
                        plt.tight_layout()
                        st.pyplot(fig, use_container_width=True)
                        plt.close(fig)
        else:
            st.info("Need at least 5 sessions to show trend charts")

        st.markdown("---")

        # Quick Insights
        st.subheader("💡 Quick Insights")
        col1, col2 = st.columns(2)

        with col1:
            # Two-footed balance
            if 'left_touches' in df.columns and 'right_touches' in df.columns:
                left_total = pd.to_numeric(df['left_touches'], errors='coerce').sum()
                right_total = pd.to_numeric(df['right_touches'], errors='coerce').sum()
                if right_total > 0:
                    ratio = left_total / right_total
                    st.info(f"**⚖️ Two-Footed Balance**\n\nLeft/Right Ratio: {ratio:.2f}\n\n" +
                           ("✅ Excellent balance!" if ratio >= 0.5 else
                            "📈 Good progress - keep working left foot!" if ratio >= 0.4 else
                            "⚠️ Focus on left foot development"))

        with col2:
            # Training intensity
            if 'intensity' in df.columns:
                intensity_counts = df['intensity'].value_counts()
                if len(intensity_counts) > 0:
                    most_common = intensity_counts.index[0]
                    count = intensity_counts.iloc[0]
                    st.info(f"**🔥 Training Intensity**\n\nMost Common: {most_common}\n\n" +
                           f"Used in {count}/{len(df)} sessions ({count/len(df)*100:.0f}%)")

# Tab 2: Upload & Extract
with tab2:
    st.header("Upload CityPlay Screenshots")

    uploaded_files = st.file_uploader(
        "Upload one or more screenshots",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        key='screenshot_upload'
    )

    if uploaded_files:
        st.write(f"📸 {len(uploaded_files)} image(s) uploaded")

        # Show thumbnails
        cols = st.columns(min(4, len(uploaded_files)))
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 4]:
                image = Image.open(file)
                st.image(image, caption=f"Image {idx+1}", use_container_width=True)

        if st.button("🔍 Extract Data from All Images", disabled=not OCR_AVAILABLE):
            if not OCR_AVAILABLE:
                st.error("❌ OCR is not available. Please enter data manually below.")
            else:
                with st.spinner("Processing images with OCR..."):
                    all_extracted = {}

                    for file in uploaded_files:
                        try:
                            image = Image.open(file)
                            text = pytesseract.image_to_string(image)
                            extracted = parse_ocr_text(text)

                            for key, value in extracted.items():
                                if value and str(value).strip():
                                    all_extracted[key] = value
                        except Exception as e:
                            st.error(f"Error processing {file.name}: {e}")

                    st.success(f"✅ Extracted {len(all_extracted)} fields!")
                    st.session_state['extracted_data'] = all_extracted

        if not OCR_AVAILABLE and uploaded_files:
            st.info("💡 OCR unavailable. Please manually enter data from your screenshots below.")

    # Data entry form
    st.subheader("Session Data Entry")

    # Initialize extracted_data in session state if not present
    if 'extracted_data' not in st.session_state:
        st.session_state['extracted_data'] = {}

    # Initialize form counter for reset functionality
    if 'form_counter' not in st.session_state:
        st.session_state['form_counter'] = 0

    # Initialize confirmation state
    if 'pending_submission' not in st.session_state:
        st.session_state['pending_submission'] = None

    extracted_data = st.session_state.get('extracted_data', {})

    # Training type selection (outside form to control field visibility)
    training_types = ["Speed and Agility", "Ball Work", "Match-Grass", "Match-Turf", "Match-Hard"]
    selected_training_type = st.selectbox(
        "Select Training Type",
        training_types,
        key=f"training_type_selector_{st.session_state['form_counter']}"
    )

    with st.form(f"session_form_{st.session_state['form_counter']}"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Session Info**")
            # Use U.S. Central Time for date
            central_tz = pytz.timezone('America/Chicago')
            central_now = datetime.now(central_tz)
            date = st.date_input("Date", value=central_now)

            # Session Name - dropdown with existing values + custom entry
            existing_sessions = []
            if st.session_state.df is not None and 'session_name' in st.session_state.df.columns:
                existing_sessions = st.session_state.df['session_name'].dropna().unique().tolist()
            session_options = ["-- Enter New --"] + sorted(existing_sessions)
            session_choice = st.selectbox("Session Name", session_options, key="session_name_select")
            if session_choice == "-- Enter New --":
                session_name = st.text_input("↳ Enter New Session Name", value=extracted_data.get('session_name', ''), key="session_name_input")
            else:
                session_name = session_choice

            # Coach - dropdown with existing values + custom entry
            existing_coaches = []
            if st.session_state.df is not None and 'coach' in st.session_state.df.columns:
                existing_coaches = st.session_state.df['coach'].dropna().unique().tolist()
            coach_options = ["-- Enter New --"] + sorted(existing_coaches)
            coach_choice = st.selectbox("Coach", coach_options, key="coach_select")
            if coach_choice == "-- Enter New --":
                coach = st.text_input("↳ Enter New Coach Name", value=extracted_data.get('coach', ''), key="coach_input")
            else:
                coach = coach_choice

            # Location - dropdown with existing values + custom entry
            existing_locations = []
            if st.session_state.df is not None and 'location' in st.session_state.df.columns:
                existing_locations = st.session_state.df['location'].dropna().unique().tolist()
            location_options = ["-- Enter New --"] + sorted(existing_locations)
            location_choice = st.selectbox("Location", location_options, key="location_select")
            if location_choice == "-- Enter New --":
                location = st.text_input("↳ Enter New Location", value=extracted_data.get('location', ''), key="location_input")
            else:
                location = location_choice

            # Surface - fixed dropdown
            surface = st.selectbox("Surface", ["Grass", "Turf", "Hard"])

            # Auto-set With Ball based on training type
            # "Yes" for Ball Work and any Match types (Match-Grass, Match-Turf, Match-Hard)
            with_ball = "Yes" if (selected_training_type == "Ball Work" or "Match" in selected_training_type) else "No"

            duration = st.number_input("Duration (min)", value=int(extracted_data.get('duration', 0)) if extracted_data.get('duration') else 0)

            # Intensity - fixed dropdown with 10 levels
            intensity_options = ["Minimal", "Extremely Easy", "Very Easy", "Easy", "Moderate",
                               "Somewhat Hard", "Hard", "Very Hard", "Extremely Hard", "Maximal"]
            intensity = st.selectbox("Intensity", intensity_options)

            st.write("**Movement Metrics (All Types)**")
            total_distance = st.number_input("Total Distance (mi)", value=float(extracted_data.get('total_distance', 0)) if extracted_data.get('total_distance') else 0.0, format="%.2f")
            sprint_distance = st.number_input("Sprint Distance (yd)", value=float(extracted_data.get('sprint_distance', 0)) if extracted_data.get('sprint_distance') else 0.0, format="%.1f")
            top_speed = st.number_input("Top Speed (mph)", value=float(extracted_data.get('top_speed', 0)) if extracted_data.get('top_speed') else 0.0, format="%.2f")
            num_sprints = st.number_input("Number of Sprints", value=int(extracted_data.get('num_sprints', 0)) if extracted_data.get('num_sprints') else 0)
            accelerations = st.number_input("Accl/Decl", value=int(extracted_data.get('accelerations', 0)) if extracted_data.get('accelerations') else 0)

            st.write("**Agility (All Types)**")
            left_turns = st.number_input("Left Turns", value=int(extracted_data.get('left_turns', 0)) if extracted_data.get('left_turns') else 0)
            right_turns = st.number_input("Right Turns", value=int(extracted_data.get('right_turns', 0)) if extracted_data.get('right_turns') else 0)
            back_turns = st.number_input("Back Turns", value=int(extracted_data.get('back_turns', 0)) if extracted_data.get('back_turns') else 0)
            intense_turns = st.number_input("Intense Turns", value=int(extracted_data.get('intense_turns', 0)) if extracted_data.get('intense_turns') else 0)
            # Total Turns - calculated field (removed from user input)
            avg_turn_entry = st.number_input("Avg Turn Entry Speed (mph)", value=float(extracted_data.get('avg_turn_entry', 0)) if extracted_data.get('avg_turn_entry') else 0.0, format="%.1f")
            avg_turn_exit = st.number_input("Avg Turn Exit Speed (mph)", value=float(extracted_data.get('avg_turn_exit', 0)) if extracted_data.get('avg_turn_exit') else 0.0, format="%.1f")

        with col2:
            # Ball Work fields - shown for Ball Work and Match types
            if selected_training_type in ["Ball Work", "Match-Grass", "Match-Turf", "Match-Hard"]:
                st.write("**Ball Work**")
                # Ball Touches - calculated field (removed from user input)
                left_touches = st.number_input("Left Foot Touches", value=int(extracted_data.get('left_touches', 0)) if extracted_data.get('left_touches') else 0)
                right_touches = st.number_input("Right Foot Touches", value=int(extracted_data.get('right_touches', 0)) if extracted_data.get('right_touches') else 0)
                # Left Foot % - calculated field (removed from user input)
                left_releases = st.number_input("Left Releases", value=int(extracted_data.get('left_releases', 0)) if extracted_data.get('left_releases') else 0)
                right_releases = st.number_input("Right Releases", value=int(extracted_data.get('right_releases', 0)) if extracted_data.get('right_releases') else 0)
                # Kicking Power - calculated field (removed from user input)
                left_kicking_power = st.number_input("Left Kicking Power (mph)", value=float(extracted_data.get('left_kicking_power_mph', 0)) if extracted_data.get('left_kicking_power_mph') else 0.0, format="%.2f")
                right_kicking_power = st.number_input("Right Kicking Power (mph)", value=float(extracted_data.get('right_kicking_power_mph', 0)) if extracted_data.get('right_kicking_power_mph') else 0.0, format="%.2f")
            else:
                # Set defaults for Speed and Agility
                left_touches = 0
                right_touches = 0
                left_releases = 0
                right_releases = 0
                left_kicking_power = 0
                right_kicking_power = 0

            # Match-specific fields - shown only for Match types
            if selected_training_type in ["Match-Grass", "Match-Turf", "Match-Hard"]:
                st.write("**Match Stats**")
                position = st.text_input("Position", value=extracted_data.get('position', ''))
                goals = st.number_input("Goals", value=int(extracted_data.get('goals', 0)) if extracted_data.get('goals') else 0)
                assists = st.number_input("Assists", value=int(extracted_data.get('assists', 0)) if extracted_data.get('assists') else 0)
                # Work Rate - calculated field (removed from user input)
                ball_possessions = st.number_input("Ball Possessions", value=int(extracted_data.get('ball_possessions', 0)) if extracted_data.get('ball_possessions') else 0)
            else:
                # Set defaults for non-match types
                position = ''
                goals = 0
                assists = 0
                ball_possessions = 0

        col_submit1, col_submit2 = st.columns([1, 1])
        with col_submit1:
            submitted = st.form_submit_button("💾 Add to Data File", use_container_width=True)
        with col_submit2:
            reset = st.form_submit_button("🔄 Reset Form", use_container_width=True)

        if reset:
            # Clear extracted data and increment form counter to reset form
            st.session_state['extracted_data'] = {}
            st.session_state['form_counter'] += 1
            st.session_state['pending_submission'] = None
            st.rerun()

        if submitted:
            # Calculate derived fields
            # Total Turns = Left Turns + Right Turns + Back Turns
            total_turns = left_turns + right_turns + back_turns

            # Ball Touches = Left Foot Touches + Right Foot Touches
            ball_touches = left_touches + right_touches

            # Left Foot % = Left Foot Touches / Ball Touches (if Ball Touches > 0)
            left_foot_pct = (left_touches / ball_touches * 100) if ball_touches > 0 else 0

            # Right Foot % = 100 - Left Foot %
            right_foot_pct = 100 - left_foot_pct if ball_touches > 0 else 0

            # Kicking Power = Max of Left Kicking Power or Right Kicking Power
            kicking_power = max(left_kicking_power, right_kicking_power)

            # Work Rate = (Total Distance in miles × 1760 yards/mile) / Duration in minutes
            # Result is in yards per minute, rounded to 2 decimal places
            work_rate = round(((total_distance * 1760) / duration), 2) if duration > 0 else 0

            # Store submission data for confirmation
            # Convert date to timezone-aware datetime in Central Time
            central_tz = pytz.timezone('America/Chicago')
            date_with_time = central_tz.localize(datetime.combine(date, datetime.min.time()))

            new_row = {
                'date': date_with_time,
                'session_name': session_name,
                'coach': coach,
                'location': location,
                'surface': surface,
                'with_ball': with_ball,
                'training_type': selected_training_type,
                'duration': duration,
                'intensity': intensity,
                'total_distance': total_distance,
                'sprint_distance': sprint_distance,
                'accelerations': accelerations,
                'top_speed': top_speed,
                'num_sprints': num_sprints,
                'left_turns': left_turns,
                'back_turns': back_turns,
                'right_turns': right_turns,
                'intense_turns': intense_turns,
                'total_turns': total_turns,
                'avg_turn_entry': avg_turn_entry,
                'avg_turn_exit': avg_turn_exit,
                'ball_touches': ball_touches,
                'left_touches': left_touches,
                'right_touches': right_touches,
                'left_foot_pct': left_foot_pct,
                'right_foot_pct': right_foot_pct,
                'left_releases': left_releases,
                'right_releases': right_releases,
                'kicking_power': kicking_power,
                'left_kicking_power_mph': left_kicking_power,
                'right_kicking_power_mph': right_kicking_power,
                'position': position,
                'goals': goals,
                'assists': assists,
                'work_rate': work_rate,
                'ball_possessions': ball_possessions,
            }

            # Store the row for confirmation
            st.session_state['pending_submission'] = new_row

    # Show confirmation dialog if there's a pending submission
    if st.session_state.get('pending_submission') is not None:
        st.warning("⚠️ **Confirm you want to update the data file**")

        col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 1, 2])

        with col_confirm1:
            if st.button("✅ Yes", type="primary", use_container_width=True):
                new_row = st.session_state['pending_submission']

                # Add to dataframe
                if st.session_state.df is None:
                    st.session_state.df = pd.DataFrame([new_row])
                else:
                    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)

                # Ensure data types are preserved after concat
                numeric_columns = [
                    'duration', 'ball_touches', 'total_distance', 'sprint_distance',
                    'accelerations', 'kicking_power', 'top_speed', 'num_sprints',
                    'left_touches', 'right_touches', 'left_foot_pct', 'right_foot_pct',
                    'left_releases', 'right_releases',
                    'left_kicking_power_mph', 'right_kicking_power_mph',
                    'left_turns', 'back_turns', 'right_turns', 'intense_turns',
                    'avg_turn_entry', 'avg_turn_exit', 'total_turns', 'work_rate',
                    'goals', 'assists', 'ball_possessions'
                ]

                for col in numeric_columns:
                    if col in st.session_state.df.columns:
                        st.session_state.df[col] = pd.to_numeric(st.session_state.df[col], errors='coerce')

                # Ensure date column is datetime
                if 'date' in st.session_state.df.columns:
                    st.session_state.df['date'] = pd.to_datetime(st.session_state.df['date'], errors='coerce')

                calculate_personal_records()

                # Auto-save to Google Sheets if configured
                if GSHEETS_AVAILABLE and "google_sheets_url" in st.secrets:
                    with st.spinner("Saving to Google Sheets..."):
                        success, error = save_data_to_google_sheets(st.session_state.df)
                        if error:
                            st.warning(f"⚠️ Session added locally but cloud save failed: {error}")
                            st.info("💡 Use 'Save to Cloud' button in sidebar to sync manually")
                        else:
                            # Reload from Google Sheets to ensure data types are correct
                            df_reloaded, reload_error = load_data_from_google_sheets()
                            if not reload_error and df_reloaded is not None:
                                st.session_state.df = df_reloaded
                                calculate_personal_records()
                            st.success("✅ Session added and saved to cloud!")
                else:
                    st.success("✅ Session added successfully!")

                st.session_state['extracted_data'] = {}  # Clear extracted data
                st.session_state['form_counter'] += 1  # Increment to reset form
                st.session_state['pending_submission'] = None  # Clear pending submission

                # Clear cached AI insights so user regenerates with new data
                if 'ai_insights_generated' in st.session_state:
                    st.session_state.ai_insights_generated = False
                if 'ai_insights_report' in st.session_state:
                    st.session_state.ai_insights_report = ""

                st.rerun()

        with col_confirm2:
            if st.button("❌ No", use_container_width=True):
                st.session_state['pending_submission'] = None
                st.rerun()

# Tab 4: Analytics
with tab4:
    st.header("📊 Training Analytics")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        df = st.session_state.df.copy()

        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.sort_values('date')

        # Coach filter
        if 'coach' in df.columns:
            coaches = df['coach'].dropna().unique().tolist()
            # Replace "Solo" with "No Coach" in the display
            coaches_display = ["No Coach" if str(c).lower() == "solo" else c for c in coaches]
            coaches_display_map = dict(zip(coaches_display, coaches))

            selected_coach_display = st.selectbox(
                "Filter by Coach",
                ["All Coaches"] + coaches_display,
                key="analytics_coach_filter"
            )

            if selected_coach_display != "All Coaches":
                selected_coach = coaches_display_map[selected_coach_display]
                df = df[df['coach'] == selected_coach]

        # Chart selection
        chart_option = st.selectbox(
            "Select Chart",
            ["-- Select a Chart --", "Top Speed Progress", "Ball Touches Progress", "Sprint Distance Progress",
             "Kicking Power Progress", "Agility Performance", "Turn Speed Analysis"]
        )

        if chart_option == "-- Select a Chart --":
            st.info("📊 **Select a Chart from the List Above**")
        else:
            fig, ax = plt.subplots(figsize=(10, 6))

            if chart_option == "Top Speed Progress":
                if 'top_speed' in df.columns and 'date' in df.columns:
                    speed_data = df[['date', 'top_speed']].dropna()
                    ax.plot(speed_data['date'], speed_data['top_speed'], marker='o', linewidth=2, markersize=8)
                    ax.set_xlabel('Date', fontsize=12)
                    ax.set_ylabel('Top Speed (mph)', fontsize=12)
                    ax.set_title('Top Speed Progress Over Time', fontsize=14, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)

            elif chart_option == "Ball Touches Progress":
                if 'ball_touches' in df.columns and 'date' in df.columns:
                    touches_data = df[df['ball_touches'] > 0][['date', 'ball_touches']].dropna()
                    ax.plot(touches_data['date'], touches_data['ball_touches'], marker='s', linewidth=2, markersize=8, color='green')
                    ax.set_xlabel('Date', fontsize=12)
                    ax.set_ylabel('Ball Touches', fontsize=12)
                    ax.set_title('Ball Touches Progress Over Time', fontsize=14, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)

            elif chart_option == "Sprint Distance Progress":
                if 'sprint_distance' in df.columns and 'date' in df.columns:
                    sprint_data = df[['date', 'sprint_distance']].dropna()
                    ax.plot(sprint_data['date'], sprint_data['sprint_distance'], marker='^', linewidth=2, markersize=8, color='orange')
                    ax.set_xlabel('Date', fontsize=12)
                    ax.set_ylabel('Sprint Distance (yards)', fontsize=12)
                    ax.set_title('Sprint Distance Progress Over Time', fontsize=14, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)

            elif chart_option == "Kicking Power Progress":
                if 'left_kicking_power_mph' in df.columns or 'right_kicking_power_mph' in df.columns:
                    left_vals = pd.to_numeric(df['left_kicking_power_mph'], errors='coerce') if 'left_kicking_power_mph' in df.columns else pd.Series([None]*len(df))
                    right_vals = pd.to_numeric(df['right_kicking_power_mph'], errors='coerce') if 'right_kicking_power_mph' in df.columns else pd.Series([None]*len(df))

                    mask = left_vals.notna() | right_vals.notna()
                    df_filtered = df[mask].copy()

                    if 'left_kicking_power_mph' in df.columns:
                        left_filtered = left_vals[mask]
                        ax.plot(df_filtered['date'], left_filtered, marker='s', linewidth=2, markersize=7, label='Left Foot', color='#3498db')

                    if 'right_kicking_power_mph' in df.columns:
                        right_filtered = right_vals[mask]
                        ax.plot(df_filtered['date'], right_filtered, marker='^', linewidth=2, markersize=7, label='Right Foot', color='#e74c3c')

                    ax.set_xlabel('Date', fontsize=12)
                    ax.set_ylabel('Kicking Power (mph)', fontsize=12)
                    ax.set_title('Kicking Power Progress (Left vs Right)', fontsize=14, fontweight='bold')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)

            elif chart_option == "Agility Performance":
                if 'intense_turns' in df.columns and 'date' in df.columns:
                    agility_data = df[['date', 'intense_turns']].dropna()
                    ax.plot(agility_data['date'], agility_data['intense_turns'], marker='D', linewidth=2, markersize=8, color='purple')
                    ax.axhline(y=10, color='r', linestyle='--', label='Elite Target (10+)')
                    ax.set_xlabel('Date', fontsize=12)
                    ax.set_ylabel('Intense Turns', fontsize=12)
                    ax.set_title('Intense Turns Over Time', fontsize=14, fontweight='bold')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)

            elif chart_option == "Turn Speed Analysis":
                if 'avg_turn_entry' in df.columns and 'avg_turn_exit' in df.columns:
                    entry_data = pd.to_numeric(df['avg_turn_entry'], errors='coerce')
                    exit_data = pd.to_numeric(df['avg_turn_exit'], errors='coerce')

                    mask = entry_data.notna() | exit_data.notna()
                    df_filtered = df[mask].copy()

                    ax.plot(df_filtered['date'], entry_data[mask], marker='o', linewidth=2, markersize=7, label='Entry Speed', color='#3498db')
                    ax.plot(df_filtered['date'], exit_data[mask], marker='s', linewidth=2, markersize=7, label='Exit Speed', color='#e74c3c')
                    ax.set_xlabel('Date', fontsize=12)
                    ax.set_ylabel('Speed (mph)', fontsize=12)
                    ax.set_title('Turn Entry vs Exit Speed', fontsize=14, fontweight='bold')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)

            plt.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

# Tab 5: Speed
with tab5:
    st.header("⚡ Speed Analysis")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        df = st.session_state.df.copy()

        st.info("**What is Speed?**\n\nSpeed measures explosive power, acceleration, and top-end velocity in training sessions.")

        # Coach filter
        if 'coach' in df.columns:
            coaches = df['coach'].dropna().unique().tolist()
            # Replace "Solo" with "No Coach" in the display
            coaches_display = ["No Coach" if str(c).lower() == "solo" else c for c in coaches]
            coaches_display_map = dict(zip(coaches_display, coaches))

            selected_coach_display = st.selectbox(
                "Filter by Coach",
                ["All Coaches"] + coaches_display,
                key="speed_coach_filter"
            )

            if selected_coach_display != "All Coaches":
                selected_coach = coaches_display_map[selected_coach_display]
                df = df[df['coach'] == selected_coach]

        # Time filter with date range display
        col1, col2 = st.columns([1, 2])
        with col1:
            speed_time_filter = st.radio(
                "Time Period",
                ["All Time", "Last 30 Days"],
                horizontal=True,
                key="speed_time_filter"
            )

        # Filter data based on selection and show date range
        total_sessions = len(df)
        if speed_time_filter == "Last 30 Days" and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            cutoff_date = get_central_time() - pd.Timedelta(days=30)
            df = df[df['date'] >= cutoff_date]

            if len(df) > 0 and df['date'].notna().any():
                date_min = df['date'].min().strftime('%b %d, %Y')
                date_max = df['date'].max().strftime('%b %d, %Y')
                with col2:
                    st.markdown(f"**📅 {date_min} - {date_max}** ({len(df)} of {total_sessions} sessions)")
            else:
                with col2:
                    st.markdown(f"**📊 {len(df)} of {total_sessions} sessions**")
        else:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                if df['date'].notna().any():
                    date_min = df['date'].min().strftime('%b %d, %Y')
                    date_max = df['date'].max().strftime('%b %d, %Y')
                    with col2:
                        st.markdown(f"**📅 {date_min} - {date_max}** ({total_sessions} sessions)")
                else:
                    with col2:
                        st.markdown(f"**📊 {total_sessions} sessions**")
            else:
                with col2:
                    st.markdown(f"**📊 {total_sessions} sessions**")

        # Calculate speed statistics
        speed_metrics = [
            ('top_speed', 'Top Speed (mph)', '🚀 Maximum velocity achieved'),
            ('num_sprints', 'Sprints', '💨 Number of sprint efforts'),
            ('sprint_distance', 'Sprint Distance (yards)', '🏃 Total distance at sprint speed'),
            ('accelerations', 'Accl/Decl', '⚡ Explosive movements and changes of pace'),
        ]

        cols = st.columns(3)
        for idx, (col_name, label, description) in enumerate(speed_metrics):
            with cols[idx % 3]:
                if col_name in df.columns:
                    values = pd.to_numeric(df[col_name], errors='coerce').dropna()
                    if len(values) > 0:
                        avg_val = values.mean()
                        best_val = values.max()

                        st.metric(f"{label} (avg)", f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                        st.caption(description)

# Tab 6: Agility
with tab6:
    st.header("🔄 Agility Analysis")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        df = st.session_state.df.copy()

        st.info("**What is Agility?**\n\nAgility is the ability to respond to game actions fast through quick turns or changes in pace.")

        # Coach filter
        if 'coach' in df.columns:
            coaches = df['coach'].dropna().unique().tolist()
            # Replace "Solo" with "No Coach" in the display
            coaches_display = ["No Coach" if str(c).lower() == "solo" else c for c in coaches]
            coaches_display_map = dict(zip(coaches_display, coaches))

            selected_coach_display = st.selectbox(
                "Filter by Coach",
                ["All Coaches"] + coaches_display,
                key="agility_coach_filter"
            )

            if selected_coach_display != "All Coaches":
                selected_coach = coaches_display_map[selected_coach_display]
                df = df[df['coach'] == selected_coach]

        # Time filter with date range display
        col1, col2 = st.columns([1, 2])
        with col1:
            agility_time_filter = st.radio(
                "Time Period",
                ["All Time", "Last 30 Days"],
                horizontal=True,
                key="agility_time_filter"
            )

        # Filter data based on selection and show date range
        total_sessions = len(df)
        if agility_time_filter == "Last 30 Days" and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            cutoff_date = get_central_time() - pd.Timedelta(days=30)
            df = df[df['date'] >= cutoff_date]

            if len(df) > 0 and df['date'].notna().any():
                date_min = df['date'].min().strftime('%b %d, %Y')
                date_max = df['date'].max().strftime('%b %d, %Y')
                with col2:
                    st.markdown(f"**📅 {date_min} - {date_max}** ({len(df)} of {total_sessions} sessions)")
            else:
                with col2:
                    st.markdown(f"**📊 {len(df)} of {total_sessions} sessions**")
        else:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                if df['date'].notna().any():
                    date_min = df['date'].min().strftime('%b %d, %Y')
                    date_max = df['date'].max().strftime('%b %d, %Y')
                    with col2:
                        st.markdown(f"**📅 {date_min} - {date_max}** ({total_sessions} sessions)")
                else:
                    with col2:
                        st.markdown(f"**📊 {total_sessions} sessions**")
            else:
                with col2:
                    st.markdown(f"**📊 {total_sessions} sessions**")

        # Calculate agility statistics
        agility_metrics = [
            ('intense_turns', 'Intense Turns', '⚡ MOST IMPORTANT - Direction changes at 9+ mph'),
            ('avg_turn_exit', 'Turn Exit Speed (mph)', '🎯 Speed coming out of turns - Higher exit than entry = explosive power'),
            ('avg_turn_entry', 'Turn Entry Speed (mph)', '💨 Speed going into turns - Higher = attacking at speed'),
            ('right_turns', 'Right Turns', '➡️ Cuts to right (30-150°)'),
            ('left_turns', 'Left Turns', '⬅️ Cuts to left (30-150°)'),
            ('back_turns', 'Back Turns', '↩️ Direction reversals (150°+)'),
        ]

        cols = st.columns(3)
        for idx, (col_name, label, description) in enumerate(agility_metrics):
            with cols[idx % 3]:
                if col_name in df.columns:
                    values = pd.to_numeric(df[col_name], errors='coerce').dropna()
                    if len(values) > 0:
                        avg_val = values.mean()
                        best_val = values.max()

                        st.metric(f"{label} (avg)", f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                        st.caption(description)

# Tab 7: Ball Work
with tab7:
    st.header("⚽ Ball Work Analysis")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        df = st.session_state.df.copy()

        st.info("**What is Ball Work?**\n\nBall work measures technical skill development through foot touches, two-footed ability, and kicking power.")

        # Coach filter
        if 'coach' in df.columns:
            coaches = df['coach'].dropna().unique().tolist()
            # Replace "Solo" with "No Coach" in the display
            coaches_display = ["No Coach" if str(c).lower() == "solo" else c for c in coaches]
            coaches_display_map = dict(zip(coaches_display, coaches))

            selected_coach_display = st.selectbox(
                "Filter by Coach",
                ["All Coaches"] + coaches_display,
                key="ball_coach_filter"
            )

            if selected_coach_display != "All Coaches":
                selected_coach = coaches_display_map[selected_coach_display]
                df = df[df['coach'] == selected_coach]

        # Time filter with date range display
        col1, col2 = st.columns([1, 2])
        with col1:
            ball_time_filter = st.radio(
                "Time Period",
                ["All Time", "Last 30 Days"],
                horizontal=True,
                key="ball_time_filter"
            )

        # Filter data based on selection and show date range
        total_sessions = len(df)
        if ball_time_filter == "Last 30 Days" and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            cutoff_date = get_central_time() - pd.Timedelta(days=30)
            df = df[df['date'] >= cutoff_date]

            if len(df) > 0 and df['date'].notna().any():
                date_min = df['date'].min().strftime('%b %d, %Y')
                date_max = df['date'].max().strftime('%b %d, %Y')
                with col2:
                    st.markdown(f"**📅 {date_min} - {date_max}** ({len(df)} of {total_sessions} sessions)")
            else:
                with col2:
                    st.markdown(f"**📊 {len(df)} of {total_sessions} sessions**")
        else:
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'], errors='coerce')
                if df['date'].notna().any():
                    date_min = df['date'].min().strftime('%b %d, %Y')
                    date_max = df['date'].max().strftime('%b %d, %Y')
                    with col2:
                        st.markdown(f"**📅 {date_min} - {date_max}** ({total_sessions} sessions)")
                else:
                    with col2:
                        st.markdown(f"**📊 {total_sessions} sessions**")
            else:
                with col2:
                    st.markdown(f"**📊 {total_sessions} sessions**")

        ball_metrics = [
            ('ball_touches', 'Total Ball Touches', '📊 Overall volume per session'),
            ('left_touches', 'Left Foot Touches', '⬅️ Weak foot development'),
            ('right_touches', 'Right Foot Touches', '➡️ Dominant foot'),
            ('left_releases', 'Left Foot Releases', '🎯 Weak foot passes/shots'),
            ('right_releases', 'Right Foot Releases', '🎯 Dominant passes/shots'),
            ('left_kicking_power_mph', 'Left Foot Power (mph)', '💪 Weak foot striking'),
            ('right_kicking_power_mph', 'Right Foot Power (mph)', '💪 Dominant striking'),
        ]

        cols = st.columns(3)
        for idx, (col_name, label, description) in enumerate(ball_metrics):
            with cols[idx % 3]:
                if col_name in df.columns:
                    values = pd.to_numeric(df[col_name], errors='coerce').dropna()
                    if len(values) > 0:
                        avg_val = values.mean()
                        best_val = values.max()

                        st.metric(f"{label} (avg)", f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                        st.caption(description)

        # L/R Ratio
        if 'left_touches' in df.columns and 'right_touches' in df.columns:
            left = pd.to_numeric(df['left_touches'], errors='coerce')
            right = pd.to_numeric(df['right_touches'], errors='coerce')
            valid_mask = (left > 0) & (right > 0)

            if valid_mask.any():
                ratios = left[valid_mask] / right[valid_mask]
                avg_ratio = ratios.mean()
                best_ratio = ratios.max()

                st.metric("L/R Touch Ratio (avg)", f"{avg_ratio:.2f}", delta=f"Best: {best_ratio:.2f}")
                st.caption("⚖️ Target: ≥ 0.5 for balance")

# Tab 8: Match Play
with tab8:
    st.header("⚽ Match Play Analysis")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        df = st.session_state.df.copy()

        # Filter to only Match training types
        if 'training_type' in df.columns:
            match_df = df[df['training_type'].str.contains('Match', na=False, case=False)]

            if len(match_df) == 0:
                st.info("⚽ No match data found. Match data is recorded when training type contains 'Match' (Match-Grass, Match-Turf, Match-Hard).")
            else:
                df = match_df

                st.info("**What is Match Play?**\n\nMatch play tracks performance during actual game situations, including position played, goals, assists, work rate, and ball possessions.")

                # Coach filter
                if 'coach' in df.columns:
                    coaches = df['coach'].dropna().unique().tolist()
                    # Replace "Solo" with "No Coach" in the display
                    coaches_display = ["No Coach" if str(c).lower() == "solo" else c for c in coaches]
                    coaches_display_map = dict(zip(coaches_display, coaches))

                    selected_coach_display = st.selectbox(
                        "Filter by Coach",
                        ["All Coaches"] + coaches_display,
                        key="match_coach_filter"
                    )

                    if selected_coach_display != "All Coaches":
                        selected_coach = coaches_display_map[selected_coach_display]
                        df = df[df['coach'] == selected_coach]

                # Time filter with date range display
                col1, col2 = st.columns([1, 2])
                with col1:
                    match_time_filter = st.radio(
                        "Time Period",
                        ["All Time", "Last 30 Days"],
                        horizontal=True,
                        key="match_time_filter"
                    )

                # Filter data based on selection and show date range
                total_sessions = len(df)
                if match_time_filter == "Last 30 Days" and 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    cutoff_date = get_central_time() - pd.Timedelta(days=30)
                    df = df[df['date'] >= cutoff_date]

                    if len(df) > 0 and df['date'].notna().any():
                        date_min = df['date'].min().strftime('%b %d, %Y')
                        date_max = df['date'].max().strftime('%b %d, %Y')
                        with col2:
                            st.markdown(f"**📅 {date_min} - {date_max}** ({len(df)} of {total_sessions} sessions)")
                    else:
                        with col2:
                            st.markdown(f"**📊 {len(df)} of {total_sessions} sessions**")
                else:
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'], errors='coerce')
                        if df['date'].notna().any():
                            date_min = df['date'].min().strftime('%b %d, %Y')
                            date_max = df['date'].max().strftime('%b %d, %Y')
                            with col2:
                                st.markdown(f"**📅 {date_min} - {date_max}** ({total_sessions} sessions)")
                        else:
                            with col2:
                                st.markdown(f"**📊 {total_sessions} sessions**")
                    else:
                        with col2:
                            st.markdown(f"**📊 {total_sessions} sessions**")

                # Specific session selector
                if 'date' in df.columns and 'session_name' in df.columns:
                    # Create session labels with date and session name
                    df_temp = df.copy()
                    df_temp['date'] = pd.to_datetime(df_temp['date'], errors='coerce')
                    df_temp = df_temp.sort_values('date', ascending=False)

                    session_options = []
                    session_indices = []
                    for idx, row in df_temp.iterrows():
                        if pd.notna(row['date']) and pd.notna(row['session_name']):
                            date_str = row['date'].strftime('%b %d, %Y')
                            session_label = f"{date_str} - {row['session_name']}"
                            session_options.append(session_label)
                            session_indices.append(idx)

                    if len(session_options) > 0:
                        selected_session = st.selectbox(
                            "Select a Specific Match",
                            ["All Matches"] + session_options,
                            key="match_session_filter"
                        )

                        if selected_session != "All Matches":
                            # Find the selected session index
                            selected_idx = session_indices[session_options.index(selected_session)]
                            df = df[df.index == selected_idx]

                # Match-Specific KPIs
                st.subheader("🎯 Match Performance Indicators")

                match_metrics = [
                    ('position', 'Position', '📍 Most played position'),
                    ('goals', 'Goals', '⚽ Goals scored'),
                    ('assists', 'Assists', '🎯 Assists made'),
                    ('work_rate', 'Work Rate (yd/min)', '💪 Effort level'),
                    ('ball_possessions', 'Ball Possessions', '🏃 Time on ball'),
                ]

                cols = st.columns(5)
                for idx, (col_name, label, description) in enumerate(match_metrics):
                    with cols[idx]:
                        if col_name in df.columns:
                            if col_name == 'position':
                                # For position, show most common (filter out empty strings)
                                values = df[col_name].dropna()
                                values = values[values.str.strip() != ''] if len(values) > 0 else values
                                if len(values) > 0:
                                    most_common = values.mode()
                                    if len(most_common) > 0:
                                        st.metric(label, str(most_common[0]))
                                        st.caption(description)
                                    else:
                                        st.metric(label, "N/A")
                                        st.caption(description)
                                else:
                                    st.metric(label, "N/A")
                                    st.caption(description)
                            elif col_name == 'work_rate':
                                # For work rate, show average (numeric field)
                                values = pd.to_numeric(df[col_name], errors='coerce').dropna()
                                if len(values) > 0:
                                    avg_val = values.mean()
                                    st.metric(label, f"{avg_val:.2f}")
                                    st.caption(description)
                            else:
                                # For numeric fields, show total and average
                                values = pd.to_numeric(df[col_name], errors='coerce').dropna()
                                if len(values) > 0:
                                    total_val = values.sum()
                                    avg_val = values.mean()
                                    st.metric(label, f"{total_val:.0f}", delta=f"Avg: {avg_val:.1f}")
                                    st.caption(description)

                # Additional Performance Metrics
                st.subheader("📊 Overall Match Performance")

                performance_metrics = [
                    ('top_speed', 'Top Speed (mph)', '🚀 Maximum velocity'),
                    ('intense_turns', 'Intense Turns', '🔄 High-speed changes'),
                    ('ball_touches', 'Ball Touches', '⚽ Total touches'),
                    ('sprints', 'Sprints', '💨 Sprint count'),
                    ('sprint_distance', 'Sprint Distance (yd)', '🏃 Sprint yardage'),
                    ('total_distance', 'Total Distance (mi)', '📏 Ground covered'),
                    ('left_kicking_power_mph', 'Left Foot Power (mph)', '💪 Left foot striking'),
                    ('right_kicking_power_mph', 'Right Foot Power (mph)', '💪 Right foot striking'),
                    ('duration', 'Duration (min)', '⏱️ Match time'),
                ]

                cols = st.columns(3)
                for idx, (col_name, label, description) in enumerate(performance_metrics):
                    with cols[idx % 3]:
                        if col_name in df.columns:
                            values = pd.to_numeric(df[col_name], errors='coerce').dropna()
                            if len(values) > 0:
                                avg_val = values.mean()
                                best_val = values.max()
                                st.metric(f"{label} (avg)", f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                                st.caption(description)

                # Match Surface Breakdown
                if 'surface' in df.columns:
                    st.subheader("🌱 Surface Breakdown")
                    surface_counts = df['surface'].value_counts()
                    cols = st.columns(len(surface_counts))
                    for idx, (surface, count) in enumerate(surface_counts.items()):
                        with cols[idx]:
                            percentage = (count / len(df)) * 100
                            st.metric(f"{surface}", f"{count}", delta=f"{percentage:.0f}%")
        else:
            st.info("⚽ No training type data available. Upload data with match training types to see match analysis.")

# Tab 9: Personal Records
with tab9:
    st.header("🏆 Personal Records")

    if not st.session_state.personal_records:
        st.warning("📊 No personal records calculated. Please upload your Excel file in the sidebar.")
    else:
        records = [
            ("Top Speed", 'top_speed', "mph", "🚀"),
            ("Sprint Distance", 'sprint_distance', "yards", "🏃"),
            ("Ball Touches", 'ball_touches', "touches", "⚽"),
            ("Kicking Power", 'kicking_power', "mph", "💪"),
            ("Total Distance", 'total_distance', "miles", "📏"),
            ("Intense Turns", 'intense_turns', "turns", "🔄"),
            ("L/R Touch Ratio", 'left_right_ratio', "(best, goal: ≥0.5)", "🎯"),
            ("L/R Ratio Average", 'left_right_ratio_avg', "(all time avg)", "📊"),
        ]

        cols = st.columns(3)
        for idx, (name, key, unit, emoji) in enumerate(records):
            with cols[idx % 3]:
                value = st.session_state.personal_records.get(key, 0)
                pr_date = st.session_state.pr_dates.get(key)

                if 'ratio' in key.lower():
                    display_value = f"{value:.2f}" if value > 0 else "N/A"
                else:
                    display_value = f"{value:.1f}" if value > 0 else "N/A"

                # Add foot indicator for kicking power
                if key == 'kicking_power' and hasattr(st.session_state, 'pr_foot'):
                    foot_indicator = st.session_state.pr_foot.get('kicking_power', '')
                    if foot_indicator:
                        display_value = f"{display_value} ({foot_indicator})"

                st.metric(f"{emoji} {name}", f"{display_value} {unit}")

                if pr_date:
                    st.caption(f"📅 {pr_date.strftime('%b %d, %Y')}")

# Tab 3: AI Insights - Comprehensive Analysis
with tab3:
    st.header("🤖 AI Insights")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        st.markdown("""
        Click the button below to generate a comprehensive training insights report analyzing:
        - Executive summary of current performance
        - 30-day trend analysis
        - Performance metrics and trends
        - Coach performance analysis
        - Agility and speed development
        - Technical skills assessment
        - Personalized action plan
        - Next milestone targets
        """)

        st.markdown("---")

        # Initialize session state for insights
        if 'ai_insights_generated' not in st.session_state:
            st.session_state.ai_insights_generated = False
            st.session_state.ai_insights_report = ""

        # Button to generate insights
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("🔍 Generate Comprehensive AI Insights", type="primary", use_container_width=True):
                with st.spinner("🤖 Analyzing training data and generating insights..."):
                    df = st.session_state.df.copy()
                    st.session_state.ai_insights_report = analyze_training_data(df)
                    st.session_state.ai_insights_generated = True

        # Display the report if generated
        if st.session_state.ai_insights_generated and st.session_state.ai_insights_report:
            st.markdown("---")

            # Add a download button for the report
            st.download_button(
                label="📥 Download Report as Text File",
                data=st.session_state.ai_insights_report,
                file_name=f"mia_training_insights_{get_central_time().strftime('%Y%m%d_%H%M')}.txt",
                mime="text/plain"
            )

            # Display the report with word wrap
            st.text_area(
                label="AI Insights Report",
                value=st.session_state.ai_insights_report,
                height=600,
                label_visibility="collapsed"
            )

            # Add option to clear/regenerate
            if st.button("🔄 Clear Report"):
                st.session_state.ai_insights_generated = False
                st.session_state.ai_insights_report = ""
                st.rerun()

if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Mia Training Tracker v1.0**")
    st.sidebar.markdown("Built with Streamlit")
