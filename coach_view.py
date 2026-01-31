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

from shared import (
    GSHEETS_AVAILABLE,
    get_central_time,
    load_data_from_google_sheets,
    calculate_personal_records,
    generate_executive_summary,
    generate_30day_change_summary,
    analyze_training_data,
)

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
        color: #1f1f1f;
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

# Calculate personal records
personal_records, pr_dates, pr_foot = calculate_personal_records(df)
st.session_state.personal_records = personal_records
st.session_state.pr_dates = pr_dates
st.session_state.pr_foot = pr_foot

# Show last sync time with refresh button
col1, col2 = st.columns([4, 1])
with col1:
    st.markdown(f'<div class="refresh-info">📊 Showing {len(df)} training sessions | Last refreshed: {get_central_time().strftime("%Y-%m-%d %H:%M:%S %Z")}</div>', unsafe_allow_html=True)
with col2:
    if st.button("🔄 Refresh", type="primary", use_container_width=True):
        st.rerun()

# Create tabs - 8 tabs total
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

# Tab 1: Dashboard
with tab1:
    st.header("📊 Training Dashboard")
    st.markdown("*High-level overview of Mia's training performance*")

    # Key Performance Indicators (Averages with Best)
    st.subheader("⭐ Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)

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
        if 'left_kicking_power_mph' in df.columns:
            left_power = pd.to_numeric(df['left_kicking_power_mph'], errors='coerce').dropna()
            if len(left_power) > 0:
                avg_left = left_power.mean()
                best_left = left_power.max()
                st.metric("Left Foot Power (mph)", f"{avg_left:.1f}",
                         delta=f"Best: {best_left:.1f}", delta_color="normal")
                st.caption("⚽ Left kick strength")
            else:
                st.metric("Left Foot Power (mph)", "N/A",
                         delta="No data", delta_color="off")
                st.caption("⚽ Left kick strength")

    with col4:
        if 'right_kicking_power_mph' in df.columns:
            right_power = pd.to_numeric(df['right_kicking_power_mph'], errors='coerce').dropna()
            if len(right_power) > 0:
                avg_right = right_power.mean()
                best_right = right_power.max()
                st.metric("Right Foot Power (mph)", f"{avg_right:.1f}",
                         delta=f"Best: {best_right:.1f}", delta_color="normal")
                st.caption("⚽ Right kick strength")
            else:
                st.metric("Right Foot Power (mph)", "N/A",
                         delta="No data", delta_color="off")
                st.caption("⚽ Right kick strength")

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
        file_name=f"mia_training_insights_{get_central_time().strftime('%Y%m%d_%H%M')}.txt",
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
        cutoff_date = get_central_time() - pd.Timedelta(days=30)
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
        cutoff_date = get_central_time() - pd.Timedelta(days=30)
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
        cutoff_date = get_central_time() - pd.Timedelta(days=30)
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

# Tab 7: Match Play
with tab7:
    st.header("⚽ Match Play Analysis")

    # Filter to only Match training types
    if 'training_type' in df.columns:
        match_df = df[df['training_type'].str.contains('Match', na=False, case=False)]

        if len(match_df) == 0:
            st.info("⚽ No match data found. Match data is recorded when training type contains 'Match' (Match-Grass, Match-Turf, Match-Hard).")
        else:
            df_match = match_df.copy()

            st.info("**What is Match Play?**\n\nMatch play tracks performance during actual game situations, including position played, goals, assists, work rate, and ball possessions.")

            # Coach filter
            if 'coach' in df_match.columns:
                coaches = df_match['coach'].dropna().unique().tolist()
                coaches_display = ["No Coach" if str(c).lower() == "solo" else c for c in coaches]
                coaches_display_map = dict(zip(coaches_display, coaches))

                selected_coach_display = st.selectbox(
                    "Filter by Coach",
                    ["All Coaches"] + coaches_display,
                    key="match_coach_filter"
                )

                if selected_coach_display != "All Coaches":
                    selected_coach = coaches_display_map[selected_coach_display]
                    df_match = df_match[df_match['coach'] == selected_coach]

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
            total_sessions = len(df_match)
            if match_time_filter == "Last 30 Days" and 'date' in df_match.columns:
                df_match['date'] = pd.to_datetime(df_match['date'], errors='coerce')
                cutoff_date = get_central_time() - pd.Timedelta(days=30)
                df_match = df_match[df_match['date'] >= cutoff_date]

                if len(df_match) > 0 and df_match['date'].notna().any():
                    date_min = df_match['date'].min().strftime('%b %d, %Y')
                    date_max = df_match['date'].max().strftime('%b %d, %Y')
                    with col2:
                        st.markdown(f"**📅 {date_min} - {date_max}** ({len(df_match)} of {total_sessions} sessions)")
                else:
                    with col2:
                        st.markdown(f"**📊 {len(df_match)} of {total_sessions} sessions**")
            else:
                if 'date' in df_match.columns:
                    df_match['date'] = pd.to_datetime(df_match['date'], errors='coerce')
                    if df_match['date'].notna().any():
                        date_min = df_match['date'].min().strftime('%b %d, %Y')
                        date_max = df_match['date'].max().strftime('%b %d, %Y')
                        with col2:
                            st.markdown(f"**📅 {date_min} - {date_max}** ({total_sessions} sessions)")
                    else:
                        with col2:
                            st.markdown(f"**📊 {total_sessions} sessions**")
                else:
                    with col2:
                        st.markdown(f"**📊 {total_sessions} sessions**")

            # Specific session selector
            # Create session labels with date and session name
            df_temp = df_match.copy()

            # Sort by date if available (date is already converted earlier in load function)
            if 'date' in df_temp.columns:
                df_temp = df_temp.sort_values('date', ascending=False, na_position='last')

            session_options = []
            session_indices = []

            if 'session_name' in df_temp.columns:
                for idx, row in df_temp.iterrows():
                    if pd.notna(row['session_name']) and str(row['session_name']).strip() != '':
                        if 'date' in df_temp.columns and pd.notna(row['date']):
                            date_str = row['date'].strftime('%b %d, %Y')
                            session_label = f"{date_str} - {row['session_name']}"
                        else:
                            session_label = str(row['session_name'])

                        session_options.append(session_label)
                        session_indices.append(idx)

            if len(session_options) > 0:
                selected_session = st.selectbox(
                    "Select a Specific Match",
                    ["All Matches"] + session_options,
                    key="coach_match_session_filter"
                )

                if selected_session != "All Matches":
                    selected_idx = session_indices[session_options.index(selected_session)]
                    df_match = df_match[df_match.index == selected_idx]

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
                    if col_name in df_match.columns:
                        if col_name == 'position':
                            values = df_match[col_name].dropna()
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
                            values = pd.to_numeric(df_match[col_name], errors='coerce').dropna()
                            if len(values) > 0:
                                avg_val = values.mean()
                                st.metric(label, f"{avg_val:.2f}")
                                st.caption(description)
                        else:
                            values = pd.to_numeric(df_match[col_name], errors='coerce').dropna()
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
                    if col_name in df_match.columns:
                        values = pd.to_numeric(df_match[col_name], errors='coerce').dropna()
                        if len(values) > 0:
                            avg_val = values.mean()
                            best_val = values.max()
                            st.metric(f"{label} (avg)", f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                            st.caption(description)

            # Match Surface Breakdown
            if 'surface' in df_match.columns:
                st.subheader("🌱 Surface Breakdown")
                surface_counts = df_match['surface'].value_counts()
                cols = st.columns(len(surface_counts))
                for idx, (surface, count) in enumerate(surface_counts.items()):
                    with cols[idx]:
                        percentage = (count / len(df_match)) * 100
                        st.metric(f"{surface}", f"{count}", delta=f"{percentage:.0f}%")
    else:
        st.info("⚽ No training type data available. Upload data with match training types to see match analysis.")

# Tab 8: Personal Records
with tab8:
    st.header("🏆 Personal Records")

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

# Footer
st.markdown("---")
st.markdown("*This is a read-only coach view. Data automatically syncs from Google Sheets when page is loaded.*")
st.markdown("*Refresh the page to see the latest training data.*")
