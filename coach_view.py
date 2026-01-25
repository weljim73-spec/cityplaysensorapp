"""
Mia Training Tracker - Coach View (Read-Only)
Automatically syncs with Google Sheets and displays AI insights
For sharing with coaches
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

# Google Sheets Integration
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False
    st.error("Google Sheets integration not available. Please check requirements.")

# Page configuration
st.set_page_config(
    page_title="Mia Training Tracker - Coach View",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    }
</style>
""", unsafe_allow_html=True)

# Google Sheets functions
def connect_to_google_sheets():
    """Connect to Google Sheets using service account credentials from Streamlit secrets"""
    try:
        if not GSHEETS_AVAILABLE:
            return None, "Google Sheets libraries not installed"

        # Get credentials from Streamlit secrets
        if "gcp_service_account" not in st.secrets:
            return None, "Google Sheets credentials not configured"

        # Define the required scopes
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        # Create credentials from the secrets
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )

        # Authorize and return the client
        client = gspread.authorize(credentials)
        return client, None

    except Exception as e:
        return None, f"Error connecting to Google Sheets: {str(e)}"

def load_data_from_google_sheets():
    """Load training data from Google Sheets"""
    try:
        # Check if Google Sheets is configured
        if "google_sheets_url" not in st.secrets:
            return None, "Google Sheets URL not configured"

        # Connect to Google Sheets
        client, error = connect_to_google_sheets()
        if error:
            return None, error

        # Open the spreadsheet by URL
        sheet_url = st.secrets["google_sheets_url"]
        spreadsheet = client.open_by_url(sheet_url)

        # Get the first worksheet
        worksheet = spreadsheet.sheet1

        # Get all values and convert to DataFrame
        data = worksheet.get_all_values()

        if len(data) < 2:
            return None, "No data found in Google Sheet"

        # First row is headers
        headers = data[0]
        rows = data[1:]

        # Create DataFrame
        df = pd.DataFrame(rows, columns=headers)

        # Normalize column names to lowercase with underscores for consistency
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        # Apply column mapping
        column_mapping = {
            'top_speed_mph': 'top_speed',
            'sprint_distance_yd': 'sprint_distance',
            'total_distance_mi': 'total_distance',
            'duration_min': 'duration',
            'kicking_power_mph': 'kicking_power',
            'left_foot_pct': 'left_pct',
            'avg_turn_entry_speed_mph': 'avg_turn_entry',
            'avg_turn_exit_speed_mph': 'avg_turn_exit',
            'sprints': 'num_sprints',
            'accl_decl': 'accelerations',
        }
        df.rename(columns=column_mapping, inplace=True)

        # Calculate right_pct if missing
        if 'left_pct' in df.columns and 'right_pct' not in df.columns:
            df['right_pct'] = 100 - pd.to_numeric(df['left_pct'], errors='coerce')

        # Convert date column to datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')

        # Convert numeric columns
        numeric_columns = [
            'duration', 'ball_touches', 'total_distance', 'sprint_distance',
            'accelerations', 'kicking_power', 'top_speed', 'num_sprints',
            'left_touches', 'right_touches', 'left_pct', 'right_pct',
            'left_releases', 'right_releases',
            'left_kicking_power_mph', 'right_kicking_power_mph',
            'left_turns', 'back_turns', 'right_turns', 'intense_turns',
            'avg_turn_entry', 'avg_turn_exit', 'total_turns'
        ]

        for col in numeric_columns:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df, None

    except Exception as e:
        return None, f"Error loading from Google Sheets: {str(e)}"

# AI Insights functions (same as main app)
def generate_executive_summary(df):
    """Generate a 500-word executive summary of Mia's current status"""
    summary = "📋 EXECUTIVE SUMMARY\n" + "-" * 80 + "\n"

    sessions = len(df)

    # Date range
    date_info = ""
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        days_span = (df['date'].max() - df['date'].min()).days
        date_info = f" over {days_span} days"

    # AGILITY ANALYSIS
    agility_status = ""
    intense_current = 0
    intense_best = 0
    intense_trend = ""
    if 'intense_turns' in df.columns:
        intense_vals = pd.to_numeric(df['intense_turns'], errors='coerce').dropna()
        if len(intense_vals) > 0:
            intense_current = intense_vals.tail(3).mean()
            intense_best = intense_vals.max()

            if len(intense_vals) > 3:
                early_avg = intense_vals.head(3).mean()
                recent_avg = intense_vals.tail(3).mean()
                if recent_avg > early_avg * 1.2:
                    intense_trend = "significant improvement"
                elif recent_avg > early_avg:
                    intense_trend = "steady growth"
                else:
                    intense_trend = "stable performance"

            if intense_current >= 10:
                agility_status = "elite-level agility with consistent high-speed direction changes"
            elif intense_current >= 7:
                agility_status = "strong agility development, approaching elite performance"
            elif intense_current >= 5:
                agility_status = "solid agility foundation with room to reach elite levels"
            else:
                agility_status = "early-stage agility development with significant growth opportunity"

    # SPEED & POWER ANALYSIS
    speed_status = ""
    speed_current = 0
    speed_best = 0
    if 'top_speed' in df.columns:
        speed_vals = pd.to_numeric(df['top_speed'], errors='coerce').dropna()
        if len(speed_vals) > 0:
            speed_current = speed_vals.tail(3).mean()
            speed_best = speed_vals.max()

            if speed_current >= speed_best * 0.95:
                speed_status = "performing at peak speed"
            elif speed_current >= speed_vals.mean() * 1.05:
                speed_status = "showing recent speed gains"
            else:
                speed_status = "maintaining speed development"

    # TURN SPEED DYNAMICS
    acceleration_status = ""
    if 'avg_turn_entry' in df.columns and 'avg_turn_exit' in df.columns:
        entry = pd.to_numeric(df['avg_turn_entry'], errors='coerce').dropna()
        exit_speed = pd.to_numeric(df['avg_turn_exit'], errors='coerce').dropna()

        if len(entry) > 0 and len(exit_speed) > 0:
            avg_entry = entry.mean()
            avg_exit = exit_speed.mean()
            speed_diff = avg_exit - avg_entry

            if speed_diff > 0.5:
                acceleration_status = "She shows explosive acceleration out of cuts, a critical game-speed skill"
            elif speed_diff > 0:
                acceleration_status = "She maintains speed through turns with slight acceleration"
            else:
                acceleration_status = "Her turn exit speed presents an opportunity for explosive power development"

    # BUILD COMPREHENSIVE NARRATIVE
    summary += f"Based on analysis of {sessions} training sessions{date_info}, "

    if agility_status:
        summary += f"Mia demonstrates {agility_status}. "
        if intense_trend:
            summary += f"Her intense turns show {intense_trend}, currently averaging {intense_current:.1f} per session with a best of {intense_best:.0f}. "

    if speed_status:
        summary += f"In terms of speed development, she is {speed_status}, with recent sessions averaging {speed_current:.1f} mph against a personal best of {speed_best:.1f} mph. "

    if acceleration_status:
        summary += f"{acceleration_status}. "

    # PRIMARY FOCUS AREAS
    summary += "\n\nPRIMARY FOCUS AREAS: "
    focus_items = []

    if intense_current < 10:
        focus_items.append(f"Increase intense turns from {intense_current:.1f} to 10+ per session through high-speed cutting drills and small-sided games")

    if acceleration_status and "opportunity" in acceleration_status:
        focus_items.append("Develop explosive acceleration out of turns with plyometrics and first-step quickness drills")

    if not focus_items:
        focus_items.append("Continue balanced development while maintaining current momentum across all metrics")

    for i, item in enumerate(focus_items[:2], 1):
        summary += f"\n  {i}. {item}"

    summary += "\n\n"
    return summary

def generate_30day_change_summary(df):
    """Generate 30-day trend analysis"""
    summary = "📅 30-DAY CHANGE SUMMARY\n" + "-" * 80 + "\n"

    if 'date' not in df.columns:
        summary += "Date information not available for 30-day analysis.\n\n"
        return summary

    df = df.copy()
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date'])
    df = df.sort_values('date')

    if len(df) == 0:
        summary += "No date data available for analysis.\n\n"
        return summary

    latest_date = df['date'].max()
    thirty_days_ago = latest_date - pd.Timedelta(days=30)
    last_30_days = df[df['date'] > thirty_days_ago].copy()

    if len(last_30_days) == 0:
        summary += f"No sessions recorded in the past 30 days.\n\n"
        return summary

    sessions_count = len(last_30_days)
    date_range_start = last_30_days['date'].min()
    date_range_end = last_30_days['date'].max()
    actual_days = (date_range_end - date_range_start).days + 1

    summary += f"Over the past 30 days ({date_range_start.strftime('%b %d')} - {date_range_end.strftime('%b %d, %Y')}), "
    summary += f"Mia completed {sessions_count} training session{'s' if sessions_count != 1 else ''} "
    summary += f"spanning {actual_days} day{'s' if actual_days != 1 else ''}. "

    # Add trend narratives (simplified for coach view)
    if 'intense_turns' in df.columns:
        recent_intense = pd.to_numeric(last_30_days['intense_turns'], errors='coerce').dropna()
        if len(recent_intense) > 0:
            recent_avg = recent_intense.mean()
            recent_max = recent_intense.max()
            summary += f"Intense turns averaging {recent_avg:.1f} per session with a peak of {recent_max:.0f}. "

    if 'top_speed' in df.columns:
        recent_speed = pd.to_numeric(last_30_days['top_speed'], errors='coerce').dropna()
        if len(recent_speed) > 0:
            recent_avg_speed = recent_speed.mean()
            recent_max_speed = recent_speed.max()
            summary += f"Top speed averaging {recent_avg_speed:.1f} mph (best: {recent_max_speed:.1f} mph). "

    summary += "\n\n"
    return summary

def analyze_training_data(df):
    """Generate comprehensive insights (full function from main app)"""
    insights = "🤖 COMPREHENSIVE TRAINING INSIGHTS REPORT\n"
    insights += "=" * 80 + "\n"
    insights += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
    insights += f"Total Sessions Analyzed: {len(df)}\n"

    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        date_range = (df['date'].max() - df['date'].min()).days
        insights += f"Date Range: {df['date'].min().strftime('%b %d, %Y')} to {df['date'].max().strftime('%b %d, %Y')} ({date_range} days)\n"

    insights += "\n"
    insights += generate_executive_summary(df)
    insights += "\n"
    insights += generate_30day_change_summary(df)
    insights += "\n"

    # Training Volume Analysis
    insights += "📊 TRAINING VOLUME ANALYSIS\n" + "-" * 80 + "\n"
    if 'duration' in df.columns:
        total_mins = pd.to_numeric(df['duration'], errors='coerce').sum()
        avg_session = pd.to_numeric(df['duration'], errors='coerce').mean()
        insights += f"  • Total Training Time: {total_mins:.0f} minutes ({total_mins/60:.1f} hours)\n"
        insights += f"  • Average Session Length: {avg_session:.1f} minutes\n"

    if 'training_type' in df.columns:
        type_dist = df['training_type'].value_counts()
        insights += f"\n  Training Distribution:\n"
        for ttype, count in type_dist.items():
            if pd.notna(ttype):
                insights += f"    - {ttype}: {count} sessions ({count/len(df)*100:.1f}%)\n"

    # Performance Trends
    insights += "\n📈 PERFORMANCE TRENDS\n" + "-" * 80 + "\n"

    metrics_to_analyze = [
        ('top_speed', 'Top Speed', 'mph'),
        ('ball_touches', 'Ball Touches', 'touches'),
        ('sprint_distance', 'Sprint Distance', 'yards')
    ]

    for metric, name, unit in metrics_to_analyze:
        if metric in df.columns:
            values = pd.to_numeric(df[metric], errors='coerce').dropna()
            if len(values) > 1:
                trend = "IMPROVING" if values.iloc[-1] > values.iloc[0] else "DECLINING"
                change = ((values.iloc[-1] - values.iloc[0]) / values.iloc[0] * 100)
                insights += f"  • {name}: {trend} ({change:+.1f}% from first to last session)\n"
                insights += f"    Current: {values.iloc[-1]:.1f} {unit} | Best: {values.max():.1f} {unit} | Avg: {values.mean():.1f} {unit}\n"

    # Agility Analysis
    insights += "\n🔄 AGILITY DEVELOPMENT ANALYSIS\n" + "-" * 80 + "\n"

    if 'intense_turns' in df.columns:
        intense = pd.to_numeric(df['intense_turns'], errors='coerce')
        avg_intense = intense.mean()
        max_intense = intense.max()
        insights += f"  ⚡ INTENSE TURNS (Game-Speed Agility at 9+ mph):\n"
        insights += f"    Average: {avg_intense:.1f} | Best: {max_intense:.0f}\n"

    if 'avg_turn_entry' in df.columns and 'avg_turn_exit' in df.columns:
        entry = pd.to_numeric(df['avg_turn_entry'], errors='coerce')
        exit_s = pd.to_numeric(df['avg_turn_exit'], errors='coerce')
        avg_entry = entry.mean()
        avg_exit = exit_s.mean()
        speed_diff = avg_exit - avg_entry

        insights += f"\n  💨 TURN SPEED DYNAMICS:\n"
        insights += f"    Entry Speed: {avg_entry:.1f} mph | Exit Speed: {avg_exit:.1f} mph\n"
        insights += f"    Speed Change: {speed_diff:+.1f} mph\n"

        if speed_diff > 0.5:
            insights += f"    ✅ EXPLOSIVE: Accelerating out of cuts - excellent power!\n"
        elif speed_diff < 0:
            insights += f"    ⚠️ FOCUS: Exit slower than entry - work on explosive acceleration\n"

    insights += "\n" + "=" * 80 + "\n"
    insights += "Data auto-synced from Google Sheets\n"

    return insights

# Main App
st.markdown('<div class="main-header">⚽ Mia Training Tracker - Coach View</div>', unsafe_allow_html=True)
st.markdown('<div class="read-only-badge">📖 Read-Only View for Coaches | Auto-Syncs with Latest Data</div>', unsafe_allow_html=True)

# Auto-load data from Google Sheets
with st.spinner("🔄 Loading latest training data from cloud..."):
    df, error = load_data_from_google_sheets()

if error:
    st.error(f"❌ Error loading data: {error}")
    st.info("Please contact the administrator to configure Google Sheets access.")
    st.stop()

if df is None or len(df) == 0:
    st.warning("No training data available yet.")
    st.stop()

# Show last sync time
st.markdown(f'<div class="refresh-info">📊 Showing {len(df)} training sessions | Last refreshed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | Refresh page to see latest data</div>', unsafe_allow_html=True)

# Create tabs for coach view
tab1, tab2, tab3 = st.tabs([
    "🤖 AI Insights",
    "📊 Key Metrics",
    "📈 Progress Charts"
])

# Tab 1: Auto-generated AI Insights
with tab1:
    st.header("🤖 Comprehensive Training Insights")
    st.markdown("*Automatically generated analysis based on latest training data*")

    with st.spinner("🤖 Generating AI insights..."):
        insights_report = analyze_training_data(df)

    # Display the report
    st.code(insights_report, language=None)

    # Download button
    st.download_button(
        label="📥 Download Full Report",
        data=insights_report,
        file_name=f"mia_training_insights_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

# Tab 2: Key Metrics Dashboard
with tab2:
    st.header("📊 Key Performance Indicators")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if 'top_speed' in df.columns:
            max_speed = pd.to_numeric(df['top_speed'], errors='coerce').max()
            st.metric("🏃 Top Speed", f"{max_speed:.1f} mph")

    with col2:
        if 'intense_turns' in df.columns:
            avg_intense = pd.to_numeric(df['intense_turns'], errors='coerce').mean()
            st.metric("⚡ Avg Intense Turns", f"{avg_intense:.1f}")

    with col3:
        if 'ball_touches' in df.columns:
            max_touches = pd.to_numeric(df['ball_touches'], errors='coerce').max()
            st.metric("⚽ Max Ball Touches", f"{max_touches:.0f}")

    with col4:
        st.metric("📅 Total Sessions", len(df))

    # Recent Sessions Table
    st.subheader("Recent Training Sessions")
    display_cols = ['date', 'training_type', 'coach', 'duration', 'top_speed', 'intense_turns', 'ball_touches']
    available_cols = [col for col in display_cols if col in df.columns]

    if available_cols:
        recent_df = df[available_cols].tail(10).sort_values('date', ascending=False)
        st.dataframe(recent_df, use_container_width=True, hide_index=True)

# Tab 3: Progress Charts
with tab3:
    st.header("📈 Progress Over Time")

    # Top Speed Trend
    if 'top_speed' in df.columns and 'date' in df.columns:
        st.subheader("Top Speed Progression")
        speed_df = df[['date', 'top_speed']].dropna()
        if len(speed_df) > 0:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(speed_df['date'], speed_df['top_speed'], marker='o', linewidth=2, markersize=6)
            ax.set_xlabel('Date')
            ax.set_ylabel('Top Speed (mph)')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

    # Intense Turns Trend
    if 'intense_turns' in df.columns and 'date' in df.columns:
        st.subheader("Intense Turns Progression")
        turns_df = df[['date', 'intense_turns']].dropna()
        if len(turns_df) > 0:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(turns_df['date'], turns_df['intense_turns'], marker='o', linewidth=2, markersize=6, color='green')
            ax.set_xlabel('Date')
            ax.set_ylabel('Intense Turns')
            ax.grid(True, alpha=0.3)
            plt.xticks(rotation=45)
            plt.tight_layout()
            st.pyplot(fig)

# Footer
st.markdown("---")
st.markdown("*This is a read-only view. For full access, use the main training tracker app.*")
st.markdown("*Page automatically refreshes data from Google Sheets when loaded.*")
