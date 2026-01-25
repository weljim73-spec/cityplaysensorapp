"""
Mia Training Tracker - Coach View (Read-Only)
Automatically syncs with Google Sheets and displays all analytics
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

# Initialize session state
if 'personal_records' not in st.session_state:
    st.session_state.personal_records = {}
if 'pr_dates' not in st.session_state:
    st.session_state.pr_dates = {}
if 'ai_insights_generated' not in st.session_state:
    st.session_state.ai_insights_generated = False
    st.session_state.ai_insights_report = ""

# Google Sheets functions
def connect_to_google_sheets():
    """Connect to Google Sheets using service account credentials from Streamlit secrets"""
    try:
        if not GSHEETS_AVAILABLE:
            return None, "Google Sheets libraries not installed"

        if "gcp_service_account" not in st.secrets:
            return None, "Google Sheets credentials not configured"

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]

        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scopes
        )

        client = gspread.authorize(credentials)
        return client, None

    except Exception as e:
        return None, f"Error connecting to Google Sheets: {str(e)}"

def load_data_from_google_sheets():
    """Load training data from Google Sheets"""
    try:
        if "google_sheets_url" not in st.secrets:
            return None, "Google Sheets URL not configured"

        client, error = connect_to_google_sheets()
        if error:
            return None, error

        sheet_url = st.secrets["google_sheets_url"]
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.sheet1

        data = worksheet.get_all_values()

        if len(data) < 2:
            return None, "No data found in Google Sheet"

        headers = data[0]
        rows = data[1:]

        df = pd.DataFrame(rows, columns=headers)

        # Normalize column names
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

def calculate_personal_records(df):
    """Calculate all personal records from loaded data"""
    if df is None or len(df) == 0:
        return {}, {}

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

    return personal_records, pr_dates

# Copy all AI Insights generation functions from main app
def generate_executive_summary(df):
    """Generate executive summary - exact copy from main app"""
    summary = "📋 EXECUTIVE SUMMARY\n" + "-" * 80 + "\n"

    sessions = len(df)

    date_info = ""
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        days_span = (df['date'].max() - df['date'].min()).days
        date_info = f" over {days_span} days"

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

    summary += f"Based on analysis of {sessions} training sessions{date_info}, "

    if agility_status:
        summary += f"Mia demonstrates {agility_status}. "
        if intense_trend:
            summary += f"Her intense turns show {intense_trend}, currently averaging {intense_current:.1f} per session with a best of {intense_best:.0f}. "

    if speed_status:
        summary += f"In terms of speed development, she is {speed_status}, with recent sessions averaging {speed_current:.1f} mph against a personal best of {speed_best:.1f} mph. "

    if acceleration_status:
        summary += f"{acceleration_status}. "

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
    """Generate 30-day summary - exact copy from main app"""
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
    before_30_days = df[df['date'] <= thirty_days_ago].copy()

    if len(last_30_days) == 0:
        summary += f"No sessions recorded in the past 30 days from {latest_date.strftime('%b %d, %Y')}.\n\n"
        return summary

    sessions_count = len(last_30_days)
    date_range_start = last_30_days['date'].min()
    date_range_end = last_30_days['date'].max()
    actual_days = (date_range_end - date_range_start).days + 1

    summary += f"Over the past 30 days ({date_range_start.strftime('%b %d')} - {date_range_end.strftime('%b %d, %Y')}), "
    summary += f"Mia completed {sessions_count} training session{'s' if sessions_count != 1 else ''} "
    summary += f"spanning {actual_days} day{'s' if actual_days != 1 else ''}. "

    # AGILITY TRENDS
    agility_narrative = ""
    if 'intense_turns' in df.columns:
        recent_intense = pd.to_numeric(last_30_days['intense_turns'], errors='coerce').dropna()
        if len(recent_intense) > 0:
            recent_avg = recent_intense.mean()
            recent_max = recent_intense.max()
            recent_trend = ""

            if len(recent_intense) > 2:
                first_half_avg = recent_intense.iloc[:len(recent_intense)//2].mean()
                second_half_avg = recent_intense.iloc[len(recent_intense)//2:].mean()

                if second_half_avg > first_half_avg * 1.15:
                    recent_trend = "surging upward"
                elif second_half_avg > first_half_avg * 1.05:
                    recent_trend = "trending positively"
                elif second_half_avg < first_half_avg * 0.85:
                    recent_trend = "declining"
                else:
                    recent_trend = "holding steady"

            comparison = ""
            if len(before_30_days) > 0 and 'intense_turns' in before_30_days.columns:
                baseline_intense = pd.to_numeric(before_30_days['intense_turns'], errors='coerce').dropna()
                if len(baseline_intense) > 0:
                    baseline_avg = baseline_intense.mean()
                    pct_change = ((recent_avg - baseline_avg) / baseline_avg * 100) if baseline_avg > 0 else 0

                    if pct_change > 20:
                        comparison = f", representing a {pct_change:.0f}% improvement from her earlier baseline"
                    elif pct_change > 5:
                        comparison = f", showing {pct_change:.0f}% growth from previous performance"
                    elif pct_change < -10:
                        comparison = f", down {abs(pct_change):.0f}% from her earlier average"

            agility_narrative = f"Her agility development shows intense turns averaging {recent_avg:.1f} per session with a peak of {recent_max:.0f}, {recent_trend}{comparison}. "

    speed_narrative = ""
    if 'top_speed' in df.columns:
        recent_speed = pd.to_numeric(last_30_days['top_speed'], errors='coerce').dropna()
        if len(recent_speed) > 0:
            recent_avg_speed = recent_speed.mean()
            recent_max_speed = recent_speed.max()

            speed_consistency = ""
            if recent_speed.std() < 0.5:
                speed_consistency = "with excellent consistency"
            elif recent_speed.std() < 1.0:
                speed_consistency = "showing reliable performance"
            else:
                speed_consistency = "with some variability"

            speed_narrative = f"Speed metrics reveal an average top speed of {recent_avg_speed:.1f} mph (best: {recent_max_speed:.1f} mph) {speed_consistency}. "

    turn_narrative = ""
    if 'avg_turn_entry' in df.columns and 'avg_turn_exit' in df.columns:
        recent_entry = pd.to_numeric(last_30_days['avg_turn_entry'], errors='coerce').dropna()
        recent_exit = pd.to_numeric(last_30_days['avg_turn_exit'], errors='coerce').dropna()

        if len(recent_entry) > 0 and len(recent_exit) > 0:
            avg_entry = recent_entry.mean()
            avg_exit = recent_exit.mean()
            speed_diff = avg_exit - avg_entry

            if speed_diff > 0.5:
                turn_narrative = f"Turn dynamics are exceptional, with exit speeds averaging {speed_diff:.1f} mph faster than entry speeds, demonstrating explosive acceleration out of cuts. "
            elif speed_diff > 0:
                turn_narrative = f"Turn performance shows positive exit acceleration ({speed_diff:+.1f} mph), indicating developing explosive power. "
            else:
                turn_narrative = f"Turn exit speeds are currently {abs(speed_diff):.1f} mph slower than entry speeds on average, presenting a clear opportunity for plyometric and explosive training focus. "

    volume_narrative = ""
    if 'duration' in df.columns:
        recent_duration = pd.to_numeric(last_30_days['duration'], errors='coerce').dropna()
        if len(recent_duration) > 0:
            total_mins = recent_duration.sum()
            avg_session = recent_duration.mean()
            volume_narrative = f"Training volume totaled {total_mins:.0f} minutes ({total_mins/60:.1f} hours) with sessions averaging {avg_session:.0f} minutes each. "

    summary += agility_narrative
    summary += speed_narrative
    summary += turn_narrative
    summary += volume_narrative

    summary += "These trends provide a comprehensive view of recent development patterns and identify specific areas where focused training can accelerate progress toward elite performance.\n\n"

    return summary

def analyze_training_data(df):
    """Generate comprehensive insights - exact copy from main app (importing all analyze functions)"""
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

    # Two-Footed Development
    insights += "\n⚽ TWO-FOOTED DEVELOPMENT\n" + "-" * 80 + "\n"
    if 'left_pct' in df.columns and 'right_pct' in df.columns:
        left_avg = pd.to_numeric(df['left_pct'], errors='coerce').mean()
        right_avg = pd.to_numeric(df['right_pct'], errors='coerce').mean()
        insights += f"  • Left Foot Usage: {left_avg:.1f}%\n"
        insights += f"  • Right Foot Usage: {right_avg:.1f}%\n"

        if left_avg < 30:
            insights += "  ⚠️ RECOMMENDATION: Increase left foot training to improve balance\n"
        else:
            insights += "  ✅ Good two-footed development - keep it up!\n"

    # Coach Analysis
    insights += "\n👨‍🏫 COACH PERFORMANCE ANALYSIS\n" + "-" * 80 + "\n"
    if 'coach' in df.columns:
        for coach in df['coach'].dropna().unique():
            coach_df = df[df['coach'] == coach]
            # Display "No Coach" instead of "Solo"
            coach_display = "No Coach" if str(coach).lower() == "solo" else coach
            insights += f"  {coach_display} ({len(coach_df)} sessions):\n"

            if 'top_speed' in df.columns:
                avg_speed = pd.to_numeric(coach_df['top_speed'], errors='coerce').mean()
                insights += f"    - Avg Top Speed: {avg_speed:.2f} mph\n"

            if 'ball_touches' in df.columns:
                avg_touches = pd.to_numeric(coach_df['ball_touches'], errors='coerce').mean()
                if not pd.isna(avg_touches):
                    insights += f"    - Avg Ball Touches: {avg_touches:.0f}\n"

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
            insights += f"       → Plyometric training, first-step drills\n"

    # Turn directional balance
    if all(col in df.columns for col in ['left_turns', 'right_turns', 'back_turns']):
        left_avg = pd.to_numeric(df['left_turns'], errors='coerce').mean()
        right_avg = pd.to_numeric(df['right_turns'], errors='coerce').mean()
        back_avg = pd.to_numeric(df['back_turns'], errors='coerce').mean()

        insights += f"\n  ↔️ DIRECTIONAL AGILITY:\n"
        insights += f"    Left Turns: {left_avg:.1f} | Right Turns: {right_avg:.1f} | Back Turns: {back_avg:.1f}\n"

        if left_avg > 0 and right_avg > 0:
            ratio = left_avg / right_avg
            if 0.7 <= ratio <= 1.3:
                insights += f"    ✅ Balanced left/right development\n"

    # Speed & Power Analysis
    insights += "\n🚀 SPEED & POWER DEVELOPMENT\n" + "-" * 80 + "\n"

    if 'top_speed' in df.columns:
        speed = pd.to_numeric(df['top_speed'], errors='coerce')
        insights += f"  Top Speed: Current Max {speed.max():.1f} mph | Avg {speed.mean():.1f} mph\n"

        if len(speed) > 3:
            recent_trend = speed.tail(3).mean() - speed.head(3).mean()
            if recent_trend > 0.5:
                insights += f"  ✅ Improving: +{recent_trend:.1f} mph in recent sessions\n"
            elif recent_trend < -0.5:
                insights += f"  ⚠️ Declining: {recent_trend:.1f} mph - may need recovery\n"

    if 'kicking_power' in df.columns:
        kick = pd.to_numeric(df['kicking_power'], errors='coerce')
        insights += f"\n  Kicking Power: Max {kick.max():.1f} mph | Avg {kick.mean():.1f} mph\n"

        if 'left_kicking_power_mph' in df.columns and 'right_kicking_power_mph' in df.columns:
            left_kick = pd.to_numeric(df['left_kicking_power_mph'], errors='coerce').mean()
            right_kick = pd.to_numeric(df['right_kicking_power_mph'], errors='coerce').mean()
            if pd.notna(left_kick) and pd.notna(right_kick):
                insights += f"  Left Foot: {left_kick:.1f} mph | Right Foot: {right_kick:.1f} mph\n"
                diff = abs(left_kick - right_kick)
                if diff < 3:
                    insights += f"  ✅ Balanced kicking power between feet\n"
                else:
                    weaker_foot = "left" if left_kick < right_kick else "right"
                    insights += f"  ⚠️ {weaker_foot.capitalize()} foot needs power development\n"

    if 'sprint_distance' in df.columns and 'num_sprints' in df.columns:
        sprint_dist = pd.to_numeric(df['sprint_distance'], errors='coerce')
        num_sprints = pd.to_numeric(df['num_sprints'], errors='coerce')
        insights += f"\n  Sprint Volume: Avg {sprint_dist.mean():.0f} yards over {num_sprints.mean():.1f} sprints\n"

    # Technical Development
    insights += "\n⚽ TECHNICAL DEVELOPMENT\n" + "-" * 80 + "\n"

    if 'ball_touches' in df.columns:
        touches = pd.to_numeric(df['ball_touches'], errors='coerce')
        ball_sessions = touches.notna().sum()
        insights += f"  Ball Work Frequency: {ball_sessions}/{len(df)} sessions ({ball_sessions/len(df)*100:.0f}%)\n"
        if ball_sessions > 0:
            insights += f"  Avg Touches: {touches.mean():.0f} | Max: {touches.max():.0f}\n"

    if 'left_touches' in df.columns and 'right_touches' in df.columns:
        left_touch = pd.to_numeric(df['left_touches'], errors='coerce')
        right_touch = pd.to_numeric(df['right_touches'], errors='coerce')

        ratios = []
        for idx, row in df.iterrows():
            l = pd.to_numeric(row.get('left_touches'), errors='coerce')
            r = pd.to_numeric(row.get('right_touches'), errors='coerce')
            if pd.notna(l) and pd.notna(r) and l > 0 and r > 0:
                ratios.append(l / r)

        if ratios:
            avg_ratio = sum(ratios) / len(ratios)
            best_ratio = min(ratios, key=lambda x: abs(x - 0.5))
            insights += f"\n  Left/Right Touch Ratio:\n"
            insights += f"    Average: {avg_ratio:.2f} | Best: {best_ratio:.2f} | Goal: 0.50\n"

            if avg_ratio >= 0.5:
                insights += f"    ✅ GOAL MET: Excellent left foot development!\n"
            elif avg_ratio >= 0.4:
                insights += f"    📈 CLOSE: Almost at goal - keep working left foot!\n"
            else:
                insights += f"    ⚠️ FOCUS: Need more left foot touches (currently {avg_ratio:.0%} of right)\n"

    # Training Load Management
    insights += "\n📊 TRAINING LOAD MANAGEMENT\n" + "-" * 80 + "\n"

    if 'duration' in df.columns:
        duration = pd.to_numeric(df['duration'], errors='coerce')
        total_mins = duration.sum()
        insights += f"  Total Volume: {total_mins:.0f} minutes ({total_mins/60:.1f} hours)\n"
        insights += f"  Avg Session: {duration.mean():.1f} minutes\n"

    if 'date' in df.columns:
        date_range = (df['date'].max() - df['date'].min()).days
        sessions_per_week = len(df) / (date_range / 7) if date_range > 0 else 0
        insights += f"  Training Frequency: {sessions_per_week:.1f} sessions/week\n"

        if sessions_per_week < 3:
            insights += f"  ⚠️ Consider increasing to 3-4 sessions/week for optimal development\n"

    if 'intensity' in df.columns:
        intensity_dist = df['intensity'].value_counts(normalize=True)
        insights += f"\n  Intensity Distribution:\n"
        for intensity, pct in intensity_dist.items():
            if pd.notna(intensity):
                insights += f"    {intensity}: {pct*100:.0f}%\n"

    # Performance Relationships
    insights += "\n🔗 PERFORMANCE RELATIONSHIPS\n" + "-" * 80 + "\n"

    if 'intense_turns' in df.columns and 'top_speed' in df.columns:
        intense_vals = pd.to_numeric(df['intense_turns'], errors='coerce')
        speed_vals = pd.to_numeric(df['top_speed'], errors='coerce')
        valid_mask = intense_vals.notna() & speed_vals.notna()

        if valid_mask.sum() > 3:
            correlation = intense_vals[valid_mask].corr(speed_vals[valid_mask])
            insights += f"  Agility-Speed Correlation: {correlation:.2f}\n"

    if 'ball_touches' in df.columns and 'total_distance' in df.columns:
        touches_vals = pd.to_numeric(df['ball_touches'], errors='coerce')
        dist_vals = pd.to_numeric(df['total_distance'], errors='coerce')

        if touches_vals.notna().any() and dist_vals.notna().any():
            insights += f"\n  Ball Work Intensity:\n"
            high_touch_sessions = df[touches_vals > touches_vals.median()]
            if len(high_touch_sessions) > 0 and 'total_distance' in high_touch_sessions.columns:
                avg_dist_high_touch = pd.to_numeric(high_touch_sessions['total_distance'], errors='coerce').mean()
                insights += f"    High-touch sessions avg distance: {avg_dist_high_touch:.2f} miles\n"

    # Training Environment Analysis
    insights += "\n🌍 TRAINING ENVIRONMENT ANALYSIS\n" + "-" * 80 + "\n"

    # Location analysis
    if 'location' in df.columns:
        location_dist = df['location'].value_counts()
        insights += f"  Training Locations:\n"
        for location, count in location_dist.items():
            insights += f"    • {location}: {count} sessions ({count/len(df)*100:.1f}%)\n"

        # Performance by location
        if 'top_speed' in df.columns and len(location_dist) > 1:
            insights += f"\n  Performance by Location:\n"
            for location in location_dist.index:
                loc_df = df[df['location'] == location]
                avg_speed = pd.to_numeric(loc_df['top_speed'], errors='coerce').mean()
                if pd.notna(avg_speed):
                    insights += f"    {location}: Avg Top Speed {avg_speed:.1f} mph\n"

    # Surface analysis
    if 'surface' in df.columns:
        surface_dist = df['surface'].value_counts()
        insights += f"\n  Surface Distribution:\n"
        for surface, count in surface_dist.items():
            insights += f"    • {surface}: {count} sessions ({count/len(df)*100:.1f}%)\n"

        # Performance by surface
        if len(surface_dist) > 1:
            insights += f"\n  Surface Performance Comparison:\n"
            for surface in surface_dist.index:
                surf_df = df[df['surface'] == surface]

                if 'top_speed' in df.columns:
                    avg_speed = pd.to_numeric(surf_df['top_speed'], errors='coerce').mean()
                    if pd.notna(avg_speed):
                        insights += f"    {surface}:\n"
                        insights += f"      - Top Speed: {avg_speed:.1f} mph\n"

                if 'intense_turns' in df.columns:
                    avg_turns = pd.to_numeric(surf_df['intense_turns'], errors='coerce').mean()
                    if pd.notna(avg_turns):
                        insights += f"      - Intense Turns: {avg_turns:.1f}\n"

            # Find best surface
            if 'top_speed' in df.columns:
                best_surface = None
                best_speed = 0
                for surface in surface_dist.index:
                    surf_df = df[df['surface'] == surface]
                    avg_speed = pd.to_numeric(surf_df['top_speed'], errors='coerce').mean()
                    if pd.notna(avg_speed) and avg_speed > best_speed:
                        best_speed = avg_speed
                        best_surface = surface
                if best_surface:
                    insights += f"\n    ✅ Best surface for speed: {best_surface} ({best_speed:.1f} mph avg)\n"

    # With Ball vs Without Ball analysis
    if 'with_ball' in df.columns:
        ball_dist = df['with_ball'].value_counts()
        insights += f"\n  Ball Work Distribution:\n"
        for status, count in ball_dist.items():
            insights += f"    • {status} Ball: {count} sessions ({count/len(df)*100:.1f}%)\n"

        # Compare ball vs non-ball sessions
        if len(ball_dist) > 1:
            ball_sessions = df[df['with_ball'].str.lower() == 'yes']
            no_ball_sessions = df[df['with_ball'].str.lower() == 'no']

            insights += f"\n  Ball vs Non-Ball Performance:\n"

            if 'top_speed' in df.columns:
                ball_speed = pd.to_numeric(ball_sessions['top_speed'], errors='coerce').mean()
                no_ball_speed = pd.to_numeric(no_ball_sessions['top_speed'], errors='coerce').mean()
                if pd.notna(ball_speed) and pd.notna(no_ball_speed):
                    insights += f"    Top Speed: With Ball {ball_speed:.1f} mph | Without Ball {no_ball_speed:.1f} mph\n"
                    diff = no_ball_speed - ball_speed
                    if diff > 1:
                        insights += f"    💡 {diff:.1f} mph faster without ball - expected for pure speed work\n"

            if 'intense_turns' in df.columns:
                ball_turns = pd.to_numeric(ball_sessions['intense_turns'], errors='coerce').mean()
                no_ball_turns = pd.to_numeric(no_ball_sessions['intense_turns'], errors='coerce').mean()
                if pd.notna(ball_turns) and pd.notna(no_ball_turns):
                    insights += f"    Intense Turns: With Ball {ball_turns:.1f} | Without Ball {no_ball_turns:.1f}\n"

            if 'duration' in df.columns:
                ball_duration = pd.to_numeric(ball_sessions['duration'], errors='coerce').mean()
                no_ball_duration = pd.to_numeric(no_ball_sessions['duration'], errors='coerce').mean()
                if pd.notna(ball_duration) and pd.notna(no_ball_duration):
                    insights += f"    Avg Duration: With Ball {ball_duration:.0f} min | Without Ball {no_ball_duration:.0f} min\n"

    # Session type analysis
    if 'session_name' in df.columns:
        session_dist = df['session_name'].value_counts()
        insights += f"\n  Session Types:\n"
        top_sessions = session_dist.head(5)
        for session, count in top_sessions.items():
            insights += f"    • {session}: {count} sessions\n"

        if len(session_dist) > 5:
            insights += f"    • ({len(session_dist) - 5} other session types)\n"

    # Actionable Recommendations
    insights += "\n💡 PERSONALIZED ACTION PLAN\n" + "-" * 80 + "\n"

    recommendations = []

    if 'intense_turns' in df.columns:
        intense_avg = pd.to_numeric(df['intense_turns'], errors='coerce').mean()
        if intense_avg < 5:
            recommendations.append("🎯 PRIORITY: Increase intense turns to 10+/session\n   → High-speed cutting drills, small-sided games")

    if 'avg_turn_entry' in df.columns and 'avg_turn_exit' in df.columns:
        entry_avg = pd.to_numeric(df['avg_turn_entry'], errors='coerce').mean()
        exit_avg = pd.to_numeric(df['avg_turn_exit'], errors='coerce').mean()
        if exit_avg <= entry_avg:
            recommendations.append("⚡ Improve explosive power out of cuts\n   → Plyometrics, resistance training, first-step drills")

    if 'left_touches' in df.columns and 'right_touches' in df.columns:
        left_avg = pd.to_numeric(df['left_touches'], errors='coerce').mean()
        right_avg = pd.to_numeric(df['right_touches'], errors='coerce').mean()
        if left_avg > 0 and right_avg > 0:
            ratio = left_avg / right_avg
            if ratio < 0.4:
                recommendations.append("👣 Increase left foot training for better balance\n   → Dedicated left-foot drills, force left-only touches")

    if 'top_speed' in df.columns:
        speed = pd.to_numeric(df['top_speed'], errors='coerce')
        if len(speed) > 3:
            recent = speed.tail(3).mean()
            if recent < speed.max() * 0.9:
                recommendations.append("🚀 Focus on maintaining top speed\n   → Sprint intervals, resistance training, proper recovery")

    if recommendations:
        for i, rec in enumerate(recommendations, 1):
            insights += f"  {i}. {rec}\n\n"
    else:
        insights += "  ✅ All metrics show balanced, effective development!\n"
        insights += "     Continue current training approach.\n"

    # Next Milestones
    insights += "\n🎯 NEXT MILESTONE TARGETS\n" + "-" * 80 + "\n"

    if 'top_speed' in df.columns:
        current_speed = pd.to_numeric(df['top_speed'], errors='coerce').max()
        next_target = ((current_speed // 0.5) + 1) * 0.5
        insights += f"  • Top Speed: Current {current_speed:.1f} mph → Target {next_target:.1f} mph\n"

    if 'ball_touches' in df.columns:
        current_touches = pd.to_numeric(df['ball_touches'], errors='coerce').max()
        next_target = ((current_touches // 50) + 1) * 50
        insights += f"  • Ball Touches: Current {current_touches:.0f} → Target {next_target:.0f}\n"

    insights += "\n" + "=" * 80 + "\n"
    insights += "Keep pushing boundaries and tracking progress! 🌟⚽\n"

    return insights

# Open Graph meta tags for link previews
st.markdown("""
<meta property="og:title" content="Mia Training Tracker - Coach View" />
<meta property="og:description" content="Read-only soccer performance analytics dashboard for coaches" />
<meta property="og:image" content="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/preview.png" />
<meta property="og:type" content="website" />
<meta name="twitter:card" content="summary_large_image" />
<meta name="twitter:title" content="Mia Training Tracker - Coach View" />
<meta name="twitter:description" content="Read-only performance dashboard" />
<meta name="twitter:image" content="https://raw.githubusercontent.com/YOUR_USERNAME/YOUR_REPO/main/preview.png" />
""", unsafe_allow_html=True)

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

# Calculate personal records
personal_records, pr_dates = calculate_personal_records(df)
st.session_state.personal_records = personal_records
st.session_state.pr_dates = pr_dates

# Show last sync time with refresh button
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f'<div class="refresh-info">📊 Showing {len(df)} training sessions | Last refreshed: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</div>', unsafe_allow_html=True)
with col2:
    if st.button("🔄 Refresh", type="primary", use_container_width=True):
        st.rerun()

# Create tabs - 7 tabs total
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Dashboard",
    "🤖 AI Insights",
    "📈 Analytics",
    "⚡ Speed",
    "🔄 Agility",
    "⚽ Ball Work",
    "🏆 Personal Records"
])

# Tab 1: Dashboard
with tab1:
    st.header("📊 Training Dashboard")
    st.markdown("*High-level overview of Mia's training performance*")

    # Key Performance Indicators (Averages with Best)
    st.subheader("⭐ Key Performance Indicators")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if 'top_speed' in df.columns:
            values = pd.to_numeric(df['top_speed'], errors='coerce').dropna()
            if len(values) > 0:
                avg_speed = values.mean()
                best_speed = values.max()
                st.metric("Top Speed (mph) (avg)", f"{avg_speed:.1f}",
                         delta=f"Best: {best_speed:.1f}", delta_color="normal")
                st.caption("🚀 Maximum velocity")

    with col2:
        if 'intense_turns' in df.columns:
            values = pd.to_numeric(df['intense_turns'], errors='coerce').dropna()
            if len(values) > 0:
                avg_turns = values.mean()
                best_turns = values.max()
                st.metric("Intense Turns (avg)", f"{avg_turns:.1f}",
                         delta=f"Best: {best_turns:.1f}", delta_color="normal")
                st.caption("🔄 High-speed direction changes")

    with col3:
        if 'left_kicking_power_mph' in df.columns and 'right_kicking_power_mph' in df.columns:
            left_power = pd.to_numeric(df['left_kicking_power_mph'], errors='coerce').dropna()
            right_power = pd.to_numeric(df['right_kicking_power_mph'], errors='coerce').dropna()

            if len(left_power) > 0 or len(right_power) > 0:
                best_left = left_power.max() if len(left_power) > 0 else 0
                best_right = right_power.max() if len(right_power) > 0 else 0

                if best_left >= best_right:
                    top_power = best_left
                    foot = "L"
                    best_foot = "L"
                else:
                    top_power = best_right
                    foot = "R"
                    best_foot = "R"

                st.metric("Top Foot Power (mph)", f"{top_power:.1f} {foot}",
                         delta=f"Best: {top_power:.1f} {best_foot}", delta_color="normal")
                st.caption("⚽ Strongest kick recorded")

    with col4:
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
                st.caption("🦶 Two-footed balance")
            else:
                st.metric("L/R Touch Ratio (avg)", "N/A",
                         delta="No data", delta_color="off")
                st.caption("🦶 Two-footed balance")

    st.markdown("---")

    # Training Summary
    st.subheader("📋 Training Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Sessions", len(df))
        st.caption("📅 All-time sessions")

    with col2:
        if 'date' in df.columns:
            df_copy = df.copy()
            df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
            date_range = f"{df_copy['date'].min().strftime('%b %d, %Y')} - {df_copy['date'].max().strftime('%b %d, %Y')}"
            days_span = (df_copy['date'].max() - df_copy['date'].min()).days
            st.metric("Training Period", f"{days_span} days")
            st.caption(f"📆 {date_range}")

    with col3:
        if 'duration' in df.columns:
            total_time = pd.to_numeric(df['duration'], errors='coerce').sum()
            st.metric("Total Time", f"{total_time:.0f} min")
            st.caption(f"⏱️ {total_time/60:.1f} hours")

    with col4:
        if 'ball_touches' in df.columns:
            ball_sessions = len(df[df['ball_touches'] > 0])
            non_ball = len(df) - ball_sessions
            st.metric("Ball Sessions", f"{ball_sessions}")
            st.caption(f"⚽ {ball_sessions}/{len(df)} sessions ({ball_sessions/len(df)*100:.0f}%)")

    st.markdown("---")

    # Recent Performance Trends (Last 5 Sessions)
    st.subheader("📈 Recent Performance Trends (Last 5 Sessions)")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**🚀 Speed Progression**")
        if 'top_speed' in df.columns and 'date' in df.columns:
            recent_df = df.tail(5).copy()
            recent_df['date'] = pd.to_datetime(recent_df['date'], errors='coerce')
            recent_df = recent_df.dropna(subset=['date', 'top_speed'])

            if len(recent_df) > 0:
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(range(len(recent_df)), pd.to_numeric(recent_df['top_speed'], errors='coerce'),
                       marker='o', linewidth=2, markersize=8, color='#1E88E5')
                ax.set_xlabel('Session (Recent)', fontsize=10)
                ax.set_ylabel('Top Speed (mph)', fontsize=10)
                ax.set_title('Top Speed - Last 5 Sessions', fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.set_xticks(range(len(recent_df)))
                ax.set_xticklabels([f"S{i+1}" for i in range(len(recent_df))])
                plt.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

    with col2:
        st.markdown("**🔄 Agility Progression**")
        if 'intense_turns' in df.columns and 'date' in df.columns:
            recent_df = df.tail(5).copy()
            recent_df['date'] = pd.to_datetime(recent_df['date'], errors='coerce')
            recent_df = recent_df.dropna(subset=['date', 'intense_turns'])

            if len(recent_df) > 0:
                fig, ax = plt.subplots(figsize=(8, 4))
                ax.plot(range(len(recent_df)), pd.to_numeric(recent_df['intense_turns'], errors='coerce'),
                       marker='s', linewidth=2, markersize=8, color='#43A047')
                ax.set_xlabel('Session (Recent)', fontsize=10)
                ax.set_ylabel('Intense Turns', fontsize=10)
                ax.set_title('Intense Turns - Last 5 Sessions', fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.set_xticks(range(len(recent_df)))
                ax.set_xticklabels([f"S{i+1}" for i in range(len(recent_df))])
                plt.tight_layout()
                st.pyplot(fig, use_container_width=True)
                plt.close(fig)

    st.markdown("---")

    # Quick Insights
    st.subheader("💡 Quick Insights")
    col1, col2 = st.columns(2)

    with col1:
        if 'left_touches' in df.columns and 'right_touches' in df.columns:
            ball_df = df[(df['left_touches'] > 0) | (df['right_touches'] > 0)]
            if len(ball_df) > 0:
                left_total = pd.to_numeric(ball_df['left_touches'], errors='coerce').sum()
                right_total = pd.to_numeric(ball_df['right_touches'], errors='coerce').sum()
                total = left_total + right_total
                if total > 0:
                    left_pct = (left_total / total * 100)
                    right_pct = (right_total / total * 100)
                    ratio = left_total / right_total if right_total > 0 else 0

                    balance_status = "Good" if ratio >= 0.3 else "Needs Work"
                    st.info(f"**⚽ Two-Footed Balance**\n\nLeft: {left_pct:.0f}% | Right: {right_pct:.0f}%\n\n" +
                           f"L/R Ratio: {ratio:.2f} ({balance_status})")

    with col2:
        if 'intensity' in df.columns:
            intensity_counts = df['intensity'].value_counts()
            if len(intensity_counts) > 0:
                most_common = intensity_counts.index[0]
                count = intensity_counts.iloc[0]
                st.info(f"**🔥 Training Intensity**\n\nMost Common: {most_common}\n\n" +
                       f"Used in {count}/{len(df)} sessions ({count/len(df)*100:.0f}%)")

# Tab 2: AI Insights - Auto-generated
with tab2:
    st.header("🤖 AI Insights")
    st.markdown("*Automatically generated comprehensive training analysis*")

    # Auto-generate insights
    with st.spinner("🤖 Generating comprehensive AI insights..."):
        insights_report = analyze_training_data(df.copy())

    st.markdown("---")

    # Download button
    st.download_button(
        label="📥 Download Report as Text File",
        data=insights_report,
        file_name=f"mia_training_insights_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain"
    )

    # Display the report with word wrap
    st.text_area(
        label="AI Insights Report",
        value=insights_report,
        height=600,
        label_visibility="collapsed"
    )

# Tab 3: Analytics
with tab3:
    st.header("📊 Training Analytics")

    df_analytics = df.copy()

    # Coach filter
    if 'coach' in df_analytics.columns:
        coaches = df_analytics['coach'].dropna().unique().tolist()
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
            df_analytics = df_analytics[df_analytics['coach'] == selected_coach]

    # Ensure date column is datetime
    if 'date' in df_analytics.columns:
        df_analytics['date'] = pd.to_datetime(df_analytics['date'], errors='coerce')
        df_analytics = df_analytics.sort_values('date')

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
            if 'top_speed' in df_analytics.columns and 'date' in df_analytics.columns:
                speed_data = df_analytics[['date', 'top_speed']].dropna()
                ax.plot(speed_data['date'], speed_data['top_speed'], marker='o', linewidth=2, markersize=8)
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Top Speed (mph)', fontsize=12)
                ax.set_title('Top Speed Progress Over Time', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)

        elif chart_option == "Ball Touches Progress":
            if 'ball_touches' in df_analytics.columns and 'date' in df_analytics.columns:
                touches_data = df_analytics[df_analytics['ball_touches'] > 0][['date', 'ball_touches']].dropna()
                ax.plot(touches_data['date'], touches_data['ball_touches'], marker='s', linewidth=2, markersize=8, color='green')
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Ball Touches', fontsize=12)
                ax.set_title('Ball Touches Progress Over Time', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)

        elif chart_option == "Sprint Distance Progress":
            if 'sprint_distance' in df_analytics.columns and 'date' in df_analytics.columns:
                sprint_data = df_analytics[['date', 'sprint_distance']].dropna()
                ax.plot(sprint_data['date'], sprint_data['sprint_distance'], marker='^', linewidth=2, markersize=8, color='orange')
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Sprint Distance (yards)', fontsize=12)
                ax.set_title('Sprint Distance Progress Over Time', fontsize=14, fontweight='bold')
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)

        elif chart_option == "Kicking Power Progress":
            if 'left_kicking_power_mph' in df_analytics.columns or 'right_kicking_power_mph' in df_analytics.columns:
                left_vals = pd.to_numeric(df_analytics['left_kicking_power_mph'], errors='coerce') if 'left_kicking_power_mph' in df_analytics.columns else pd.Series([None]*len(df_analytics))
                right_vals = pd.to_numeric(df_analytics['right_kicking_power_mph'], errors='coerce') if 'right_kicking_power_mph' in df_analytics.columns else pd.Series([None]*len(df_analytics))

                mask = left_vals.notna() | right_vals.notna()
                df_filtered = df_analytics[mask].copy()

                if 'left_kicking_power_mph' in df_analytics.columns:
                    left_filtered = left_vals[mask]
                    ax.plot(df_filtered['date'], left_filtered, marker='s', linewidth=2, markersize=7, label='Left Foot', color='#3498db')

                if 'right_kicking_power_mph' in df_analytics.columns:
                    right_filtered = right_vals[mask]
                    ax.plot(df_filtered['date'], right_filtered, marker='^', linewidth=2, markersize=7, label='Right Foot', color='#e74c3c')

                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Kicking Power (mph)', fontsize=12)
                ax.set_title('Kicking Power Progress (Left vs Right)', fontsize=14, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)

        elif chart_option == "Agility Performance":
            if 'intense_turns' in df_analytics.columns and 'date' in df_analytics.columns:
                agility_data = df_analytics[['date', 'intense_turns']].dropna()
                ax.plot(agility_data['date'], agility_data['intense_turns'], marker='D', linewidth=2, markersize=8, color='purple')
                ax.axhline(y=10, color='r', linestyle='--', label='Elite Target (10+)')
                ax.set_xlabel('Date', fontsize=12)
                ax.set_ylabel('Intense Turns', fontsize=12)
                ax.set_title('Intense Turns Over Time', fontsize=14, fontweight='bold')
                ax.legend()
                ax.grid(True, alpha=0.3)
                plt.xticks(rotation=45)

        elif chart_option == "Turn Speed Analysis":
            if 'avg_turn_entry' in df_analytics.columns and 'avg_turn_exit' in df_analytics.columns:
                entry_data = pd.to_numeric(df_analytics['avg_turn_entry'], errors='coerce')
                exit_data = pd.to_numeric(df_analytics['avg_turn_exit'], errors='coerce')

                mask = entry_data.notna() | exit_data.notna()
                df_filtered = df_analytics[mask].copy()

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

# Tab 4: Speed
with tab4:
    st.header("⚡ Speed Analysis")

    st.info("**What is Speed?**\n\nSpeed measures explosive power, acceleration, and top-end velocity in training sessions.")

    df_speed = df.copy()

    # Coach filter
    if 'coach' in df_speed.columns:
        coaches = df_speed['coach'].dropna().unique().tolist()
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
            df_speed = df_speed[df_speed['coach'] == selected_coach]

    # Time filter with date range display
    col1, col2 = st.columns([1, 2])
    with col1:
        speed_time_filter = st.radio(
            "Time Period",
            ["All Time", "Last 30 Days"],
            horizontal=True,
            key="speed_time_filter"
        )

    # Filter data based on selection and show date range (update total_sessions after coach filter)
    total_sessions = len(df_speed)
    if speed_time_filter == "Last 30 Days" and 'date' in df_speed.columns:
        df_speed['date'] = pd.to_datetime(df_speed['date'], errors='coerce')
        cutoff_date = datetime.now() - pd.Timedelta(days=30)
        df_speed = df_speed[df_speed['date'] >= cutoff_date]

        if len(df_speed) > 0 and df_speed['date'].notna().any():
            date_min = df_speed['date'].min().strftime('%b %d, %Y')
            date_max = df_speed['date'].max().strftime('%b %d, %Y')
            with col2:
                st.markdown(f"**📅 {date_min} - {date_max}** ({len(df_speed)} of {total_sessions} sessions)")
        else:
            with col2:
                st.markdown(f"**📊 {len(df_speed)} of {total_sessions} sessions**")
    else:
        if 'date' in df_speed.columns:
            df_speed['date'] = pd.to_datetime(df_speed['date'], errors='coerce')
            if df_speed['date'].notna().any():
                date_min = df_speed['date'].min().strftime('%b %d, %Y')
                date_max = df_speed['date'].max().strftime('%b %d, %Y')
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
            if col_name in df_speed.columns:
                values = pd.to_numeric(df_speed[col_name], errors='coerce').dropna()
                if len(values) > 0:
                    avg_val = values.mean()
                    best_val = values.max()

                    st.metric(f"{label} (avg)", f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                    st.caption(description)

# Tab 5: Agility
with tab5:
    st.header("🔄 Agility Analysis")

    st.info("**What is Agility?**\n\nAgility is the ability to respond to game actions fast through quick turns or changes in pace.")

    df_agility = df.copy()

    # Coach filter
    if 'coach' in df_agility.columns:
        coaches = df_agility['coach'].dropna().unique().tolist()
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
            df_agility = df_agility[df_agility['coach'] == selected_coach]

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
    total_sessions = len(df_agility)
    if agility_time_filter == "Last 30 Days" and 'date' in df_agility.columns:
        df_agility['date'] = pd.to_datetime(df_agility['date'], errors='coerce')
        cutoff_date = datetime.now() - pd.Timedelta(days=30)
        df_agility = df_agility[df_agility['date'] >= cutoff_date]

        if len(df_agility) > 0 and df_agility['date'].notna().any():
            date_min = df_agility['date'].min().strftime('%b %d, %Y')
            date_max = df_agility['date'].max().strftime('%b %d, %Y')
            with col2:
                st.markdown(f"**📅 {date_min} - {date_max}** ({len(df_agility)} of {total_sessions} sessions)")
        else:
            with col2:
                st.markdown(f"**📊 {len(df_agility)} of {total_sessions} sessions**")
    else:
        if 'date' in df_agility.columns:
            df_agility['date'] = pd.to_datetime(df_agility['date'], errors='coerce')
            if df_agility['date'].notna().any():
                date_min = df_agility['date'].min().strftime('%b %d, %Y')
                date_max = df_agility['date'].max().strftime('%b %d, %Y')
                with col2:
                    st.markdown(f"**📅 {date_min} - {date_max}** ({total_sessions} sessions)")
            else:
                with col2:
                    st.markdown(f"**📊 {total_sessions} sessions**")
        else:
            with col2:
                st.markdown(f"**📊 {total_sessions} sessions**")

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
            if col_name in df_agility.columns:
                values = pd.to_numeric(df_agility[col_name], errors='coerce').dropna()
                if len(values) > 0:
                    avg_val = values.mean()
                    best_val = values.max()

                    st.metric(f"{label} (avg)", f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                    st.caption(description)

# Tab 6: Ball Work
with tab6:
    st.header("⚽ Ball Work Analysis")

    st.info("**What is Ball Work?**\n\nBall work measures technical skill development through foot touches, two-footed ability, and kicking power.")

    df_ball = df.copy()

    # Coach filter
    if 'coach' in df_ball.columns:
        coaches = df_ball['coach'].dropna().unique().tolist()
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
            df_ball = df_ball[df_ball['coach'] == selected_coach]

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
    total_sessions = len(df_ball)
    if ball_time_filter == "Last 30 Days" and 'date' in df_ball.columns:
        df_ball['date'] = pd.to_datetime(df_ball['date'], errors='coerce')
        cutoff_date = datetime.now() - pd.Timedelta(days=30)
        df_ball = df_ball[df_ball['date'] >= cutoff_date]

        if len(df_ball) > 0 and df_ball['date'].notna().any():
            date_min = df_ball['date'].min().strftime('%b %d, %Y')
            date_max = df_ball['date'].max().strftime('%b %d, %Y')
            with col2:
                st.markdown(f"**📅 {date_min} - {date_max}** ({len(df_ball)} of {total_sessions} sessions)")
        else:
            with col2:
                st.markdown(f"**📊 {len(df_ball)} of {total_sessions} sessions**")
    else:
        if 'date' in df_ball.columns:
            df_ball['date'] = pd.to_datetime(df_ball['date'], errors='coerce')
            if df_ball['date'].notna().any():
                date_min = df_ball['date'].min().strftime('%b %d, %Y')
                date_max = df_ball['date'].max().strftime('%b %d, %Y')
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
            if col_name in df_ball.columns:
                values = pd.to_numeric(df_ball[col_name], errors='coerce').dropna()
                if len(values) > 0:
                    avg_val = values.mean()
                    best_val = values.max()

                    st.metric(f"{label} (avg)", f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                    st.caption(description)

    # L/R Ratio
    if 'left_touches' in df_ball.columns and 'right_touches' in df_ball.columns:
        left = pd.to_numeric(df_ball['left_touches'], errors='coerce')
        right = pd.to_numeric(df_ball['right_touches'], errors='coerce')
        valid_mask = (left > 0) & (right > 0)

        if valid_mask.any():
            ratios = left[valid_mask] / right[valid_mask]
            avg_ratio = ratios.mean()
            best_ratio = ratios.max()

            st.metric("L/R Touch Ratio (avg)", f"{avg_ratio:.2f}", delta=f"Best: {best_ratio:.2f}")
            st.caption("⚖️ Target: ≥ 0.5 for balance")

# Tab 7: Personal Records
with tab7:
    st.header("🏆 Personal Records")

    records = [
        ("Top Speed", 'top_speed', "mph", "🚀"),
        ("Sprint Distance", 'sprint_distance', "yards", "🏃"),
        ("Ball Touches", 'ball_touches', "touches", "⚽"),
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

            st.metric(f"{emoji} {name}", f"{display_value} {unit}")

            if pr_date:
                st.caption(f"📅 {pr_date.strftime('%b %d, %Y')}")

# Footer
st.markdown("---")
st.markdown("*This is a read-only coach view. Data automatically syncs from Google Sheets when page is loaded.*")
st.markdown("*Refresh the page to see the latest training data.*")
