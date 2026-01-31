"""
Shared module for Mia Training Tracker
Contains data loading, column mapping, personal records, and analytics functions
used by both streamlit_app.py and coach_view.py
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import pytz

# Google Sheets Integration
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSHEETS_AVAILABLE = True
except ImportError:
    GSHEETS_AVAILABLE = False

# Column mapping for Excel/Google Sheets data
COLUMN_MAPPING = {
    # Session Info
    'date': 'date',
    'session_name': 'session_name',
    'coach': 'coach',
    'location': 'location',
    'surface': 'surface',
    'with_ball': 'with_ball',
    'training_type': 'training_type',
    'duration_min': 'duration',
    'intensity': 'intensity',
    # Movement Metrics
    'total_distance_mi': 'total_distance',
    'sprint_distance_yd': 'sprint_distance',
    'accl_decl': 'accelerations',
    'top_speed_mph': 'top_speed',
    'sprints': 'num_sprints',
    # Agility
    'left_turns': 'left_turns',
    'back_turns': 'back_turns',
    'right_turns': 'right_turns',
    'intense_turns': 'intense_turns',
    'total_turns': 'total_turns',
    'avg_turn_entry_speed_mph': 'avg_turn_entry',
    'avg_turn_exit_speed_mph': 'avg_turn_exit',
    # Ball Work
    'ball_touches': 'ball_touches',
    'left_touches': 'left_touches',
    'right_touches': 'right_touches',
    'left_foot_pct': 'left_foot_pct',
    'left_pct': 'left_foot_pct',
    'right_foot_pct': 'right_foot_pct',
    'right_pct': 'right_foot_pct',
    'left_releases': 'left_releases',
    'right_releases': 'right_releases',
    'kicking_power': 'kicking_power',
    'left_kicking_power_mph': 'left_kicking_power_mph',
    'right_kicking_power_mph': 'right_kicking_power_mph',
    # Match Stats
    'position': 'position',
    'goals': 'goals',
    'assists': 'assists',
    'work_rate': 'work_rate',
    'ball_possessions': 'ball_possessions',
}

# Google Sheets column mapping (subset used during load)
GSHEETS_COLUMN_MAPPING = {
    'top_speed_mph': 'top_speed',
    'sprint_distance_yd': 'sprint_distance',
    'total_distance_mi': 'total_distance',
    'duration_min': 'duration',
    'kicking_power_mph': 'kicking_power',
    'avg_turn_entry_speed_mph': 'avg_turn_entry',
    'avg_turn_exit_speed_mph': 'avg_turn_exit',
    'sprints': 'num_sprints',
    'accl_decl': 'accelerations',
    'left_pct': 'left_foot_pct',
    'right_pct': 'right_foot_pct',
}

NUMERIC_COLUMNS = [
    'duration', 'ball_touches', 'total_distance', 'sprint_distance',
    'accelerations', 'kicking_power', 'top_speed', 'num_sprints',
    'left_touches', 'right_touches', 'left_foot_pct', 'right_foot_pct',
    'left_releases', 'right_releases',
    'left_kicking_power_mph', 'right_kicking_power_mph',
    'left_turns', 'back_turns', 'right_turns', 'intense_turns',
    'avg_turn_entry', 'avg_turn_exit', 'total_turns', 'work_rate',
    'goals', 'assists', 'ball_possessions'
]


def get_central_time():
    """Get current time in U.S. Central Time"""
    central_tz = pytz.timezone('America/Chicago')
    return datetime.now(central_tz)


def connect_to_google_sheets(readonly=False):
    """Connect to Google Sheets using service account credentials from Streamlit secrets.

    Args:
        readonly: If True, use read-only scopes (for coach view).
    """
    try:
        if not GSHEETS_AVAILABLE:
            return None, "Google Sheets libraries not installed"

        if "gcp_service_account" not in st.secrets:
            return None, "Google Sheets credentials not configured. See setup guide."

        if readonly:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets.readonly",
                "https://www.googleapis.com/auth/drive.readonly"
            ]
        else:
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


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_gsheets_data(sheet_url: str, readonly: bool = False):
    """Internal cached function to fetch data from Google Sheets.

    Cached for 5 minutes (300 seconds) to reduce API calls.
    Use clear_gsheets_cache() to invalidate after saving data.
    """
    client, error = connect_to_google_sheets(readonly=readonly)
    if error:
        raise RuntimeError(error)

    spreadsheet = client.open_by_url(sheet_url)
    worksheet = spreadsheet.sheet1
    data = worksheet.get_all_values()

    if len(data) < 2:
        raise ValueError("No data found in Google Sheet")

    return data


def clear_gsheets_cache():
    """Clear the Google Sheets data cache. Call after saving data."""
    _fetch_gsheets_data.clear()


def load_data_from_google_sheets(readonly=False):
    """Load training data from Google Sheets.

    Args:
        readonly: If True, connect with read-only scopes.

    Data is cached for 5 minutes to reduce API calls.
    Use clear_gsheets_cache() to force refresh after saving.
    """
    try:
        if "google_sheets_url" not in st.secrets:
            return None, "Google Sheets URL not configured"

        sheet_url = st.secrets["google_sheets_url"]

        # Use cached fetch function
        data = _fetch_gsheets_data(sheet_url, readonly)

        headers = data[0]
        rows = data[1:]

        df = pd.DataFrame(rows, columns=headers)

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

        # Apply column mapping
        df.rename(columns=GSHEETS_COLUMN_MAPPING, inplace=True)

        # Convert date column to datetime and localize to Central Time
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            central_tz = pytz.timezone('America/Chicago')
            df['date'] = df['date'].apply(
                lambda x: central_tz.localize(x) if pd.notna(x) and x.tzinfo is None else x
            )

        # Convert numeric columns
        for col in NUMERIC_COLUMNS:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df, None

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return None, f"Error loading from Google Sheets: {str(e)}\n\nDetails: {error_details}"


def save_data_to_google_sheets(df):
    """Save training data to Google Sheets (full rewrite)."""
    try:
        client, error = connect_to_google_sheets()
        if error:
            return False, error

        sheet_url = st.secrets["google_sheets_url"]
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.sheet1

        worksheet.clear()

        df_save = df.copy()

        # Rename internal columns back to Google Sheets names
        if 'left_foot_pct' in df_save.columns:
            df_save.rename(columns={'left_foot_pct': 'left_pct'}, inplace=True)
        if 'right_foot_pct' in df_save.columns:
            df_save.rename(columns={'right_foot_pct': 'right_pct'}, inplace=True)

        # Format date column
        if 'date' in df_save.columns:
            df_save['date'] = pd.to_datetime(df_save['date'], errors='coerce')
            df_save['date'] = df_save['date'].dt.strftime('%Y-%m-%d %H:%M:%S')
            df_save['date'] = df_save['date'].fillna('')

        data = [df_save.columns.tolist()] + df_save.astype(str).values.tolist()
        worksheet.update('A1', data)

        # Clear cache so next load gets fresh data
        clear_gsheets_cache()

        return True, None

    except Exception as e:
        return False, f"Error saving to Google Sheets: {str(e)}"


def append_row_to_google_sheets(row_data):
    """Append a single row to Google Sheets."""
    try:
        client, error = connect_to_google_sheets()
        if error:
            return False, error

        sheet_url = st.secrets["google_sheets_url"]
        spreadsheet = client.open_by_url(sheet_url)
        worksheet = spreadsheet.sheet1

        worksheet.append_row(row_data)

        # Clear cache so next load gets fresh data
        clear_gsheets_cache()

        return True, None

    except Exception as e:
        return False, f"Error appending to Google Sheets: {str(e)}"


def calculate_personal_records(df):
    """Calculate all personal records from loaded data.

    Returns:
        tuple: (personal_records dict, pr_dates dict, pr_foot dict)
    """
    if df is None or len(df) == 0:
        return {}, {}, {}

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
    pr_foot = {}

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

    # L/R Touch Ratio - find ratio closest to 0.5 (vectorized)
    if 'left_touches' in df.columns and 'right_touches' in df.columns:
        left = pd.to_numeric(df['left_touches'], errors='coerce')
        right = pd.to_numeric(df['right_touches'], errors='coerce')
        valid_mask = (left > 0) & (right > 0) & pd.notna(left) & pd.notna(right)

        if valid_mask.any():
            ratios = left[valid_mask] / right[valid_mask]
            # Find ratio closest to 0.5 (perfect balance)
            distances = (ratios - 0.5).abs()
            best_idx = distances.idxmin()
            best_ratio = ratios.loc[best_idx]

            best_date = None
            if 'date' in df.columns and pd.notna(df.loc[best_idx, 'date']):
                best_date = pd.to_datetime(df.loc[best_idx, 'date'])

            personal_records['left_right_ratio'] = best_ratio
            pr_dates['left_right_ratio'] = best_date
        else:
            personal_records['left_right_ratio'] = 0.0
            pr_dates['left_right_ratio'] = None

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

    return personal_records, pr_dates, pr_foot


def generate_executive_summary(df):
    """Generate a narrative executive summary of current status."""
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
    """Generate a narrative summary analyzing trends over the past 30 days."""
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

    # SPEED & POWER TRENDS
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

    # TURN SPEED DYNAMICS
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

    # TRAINING VOLUME
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
    """Analyze training data and generate comprehensive insights report."""
    insights = "🤖 COMPREHENSIVE TRAINING INSIGHTS REPORT\n"
    insights += "=" * 80 + "\n"
    insights += f"Generated: {get_central_time().strftime('%Y-%m-%d %H:%M %Z')}\n"
    insights += f"Total Sessions Analyzed: {len(df)}\n"

    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        date_range = (df['date'].max() - df['date'].min()).days
        insights += f"Date Range: {df['date'].min().strftime('%b %d, %Y')} to {df['date'].max().strftime('%b %d, %Y')} ({date_range} days)\n"

    insights += "\n"

    # Executive summary and 30-day summary
    insights += generate_executive_summary(df)
    insights += "\n"
    insights += generate_30day_change_summary(df)
    insights += "\n"

    # 1. Training Volume Analysis
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

    # 2. Performance Trends
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

    # 3. Two-Footed Development
    insights += "\n⚽ TWO-FOOTED DEVELOPMENT\n" + "-" * 80 + "\n"
    if 'left_foot_pct' in df.columns:
        left_avg = pd.to_numeric(df['left_foot_pct'], errors='coerce').mean()
        if pd.notna(left_avg):
            right_avg = 100 - left_avg
            insights += f"  • Left Foot Usage: {left_avg:.1f}%\n"
            insights += f"  • Right Foot Usage: {right_avg:.1f}%\n"

            if left_avg < 30:
                insights += "  ⚠️ RECOMMENDATION: Increase left foot training to improve balance\n"
            else:
                insights += "  ✅ Good two-footed development - keep it up!\n"

    # 4. Coach Analysis
    insights += "\n👨‍🏫 COACH PERFORMANCE ANALYSIS\n" + "-" * 80 + "\n"
    if 'coach' in df.columns:
        for coach in df['coach'].dropna().unique():
            coach_df = df[df['coach'] == coach]
            coach_display = "No Coach" if str(coach).lower() == "solo" else coach
            insights += f"  {coach_display} ({len(coach_df)} sessions):\n"

            if 'top_speed' in df.columns:
                avg_speed = pd.to_numeric(coach_df['top_speed'], errors='coerce').mean()
                insights += f"    - Avg Top Speed: {avg_speed:.2f} mph\n"

            if 'ball_touches' in df.columns:
                avg_touches = pd.to_numeric(coach_df['ball_touches'], errors='coerce').mean()
                if not pd.isna(avg_touches):
                    insights += f"    - Avg Ball Touches: {avg_touches:.0f}\n"

    # 5. Agility Analysis
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

    # 6. Speed & Power Analysis
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

    # 7. Technical Skill
    insights += "\n⚽ TECHNICAL DEVELOPMENT\n" + "-" * 80 + "\n"

    if 'ball_touches' in df.columns:
        touches = pd.to_numeric(df['ball_touches'], errors='coerce')
        ball_sessions = touches.notna().sum()
        insights += f"  Ball Work Frequency: {ball_sessions}/{len(df)} sessions ({ball_sessions/len(df)*100:.0f}%)\n"
        if ball_sessions > 0:
            insights += f"  Avg Touches: {touches.mean():.0f} | Max: {touches.max():.0f}\n"

    if 'left_touches' in df.columns and 'right_touches' in df.columns:
        # Vectorized ratio calculation
        left = pd.to_numeric(df['left_touches'], errors='coerce')
        right = pd.to_numeric(df['right_touches'], errors='coerce')
        valid_mask = (left > 0) & (right > 0) & pd.notna(left) & pd.notna(right)

        if valid_mask.any():
            ratios = left[valid_mask] / right[valid_mask]
            avg_ratio = ratios.mean()
            # Best ratio is closest to 0.5 (perfect balance)
            distances = (ratios - 0.5).abs()
            best_ratio = ratios.loc[distances.idxmin()]

            insights += f"\n  Left/Right Touch Ratio:\n"
            insights += f"    Average: {avg_ratio:.2f} | Best: {best_ratio:.2f} | Goal: 0.50\n"

            if avg_ratio >= 0.5:
                insights += f"    ✅ GOAL MET: Excellent left foot development!\n"
            elif avg_ratio >= 0.4:
                insights += f"    📈 CLOSE: Almost at goal - keep working left foot!\n"
            else:
                insights += f"    ⚠️ FOCUS: Need more left foot touches (currently {avg_ratio:.0%} of right)\n"

    # 8. Workload & Recovery
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

    # 9. Metric Relationships & Correlations
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

    # 10. Training Environment Analysis
    insights += "\n🌍 TRAINING ENVIRONMENT ANALYSIS\n" + "-" * 80 + "\n"

    if 'location' in df.columns:
        location_dist = df['location'].value_counts()
        insights += f"  Training Locations:\n"
        for location, count in location_dist.items():
            insights += f"    • {location}: {count} sessions ({count/len(df)*100:.1f}%)\n"

        if 'top_speed' in df.columns and len(location_dist) > 1:
            insights += f"\n  Performance by Location:\n"
            for location in location_dist.index:
                loc_df = df[df['location'] == location]
                avg_speed = pd.to_numeric(loc_df['top_speed'], errors='coerce').mean()
                if pd.notna(avg_speed):
                    insights += f"    {location}: Avg Top Speed {avg_speed:.1f} mph\n"

    if 'surface' in df.columns:
        surface_dist = df['surface'].value_counts()
        insights += f"\n  Surface Distribution:\n"
        for surface, count in surface_dist.items():
            insights += f"    • {surface}: {count} sessions ({count/len(df)*100:.1f}%)\n"

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

    if 'with_ball' in df.columns:
        ball_dist = df['with_ball'].value_counts()
        insights += f"\n  Ball Work Distribution:\n"
        for status, count in ball_dist.items():
            insights += f"    • {status} Ball: {count} sessions ({count/len(df)*100:.1f}%)\n"

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

    if 'training_type' in df.columns:
        training_dist = df['training_type'].value_counts()
        insights += f"\n  Training Types:\n"
        top_trainings = training_dist.head(5)
        for training, count in top_trainings.items():
            insights += f"    • {training}: {count} sessions\n"

        if len(training_dist) > 5:
            insights += f"    • ({len(training_dist) - 5} other training types)\n"

    # 11. Actionable Recommendations
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

    # 12. Next Milestones
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
