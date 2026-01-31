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

# Import tab modules
from tabs import (
    dashboard,
    upload,
    ai_insights,
    analytics,
    speed,
    agility,
    ball_work,
    match_play,
    personal_records,
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
    dashboard.render()

# Tab 2: Upload & Extract
with tab2:
    upload.render(calculate_personal_records)

# Tab 3: AI Insights
with tab3:
    ai_insights.render()

# Tab 4: Analytics
with tab4:
    analytics.render()

# Tab 5: Speed
with tab5:
    speed.render()

# Tab 6: Agility
with tab6:
    agility.render()

# Tab 7: Ball Work
with tab7:
    ball_work.render()

# Tab 8: Match Play
with tab8:
    match_play.render()

# Tab 9: Personal Records
with tab9:
    personal_records.render()


if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Mia Training Tracker v1.0**")
    st.sidebar.markdown("Built with Streamlit")
