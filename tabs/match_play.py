"""Match Play Analysis tab for Mia Training Tracker."""

import streamlit as st
import pandas as pd

from shared import get_central_time


def render():
    """Render the Match Play Analysis tab content."""
    st.header("⚽ Match Play Analysis")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
        return

    df = st.session_state.df.copy()

    # Filter to only Match training types
    if 'training_type' not in df.columns:
        st.info("⚽ No training type data available. Upload data with match training types to see match analysis.")
        return

    match_df = df[df['training_type'].str.contains('Match', na=False, case=False)]

    if len(match_df) == 0:
        st.info("⚽ No match data found. Match data is recorded when training type contains 'Match' (Match-Grass, Match-Turf, Match-Hard).")
        return

    df = match_df

    st.info("**What is Match Play?**\n\nMatch play tracks performance during actual game situations, including position played, goals, assists, work rate, and ball possessions.")

    # Coach filter
    if 'coach' in df.columns:
        coaches = df['coach'].dropna().unique().tolist()
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
                    values = pd.to_numeric(df[col_name], errors='coerce').dropna()
                    if len(values) > 0:
                        avg_val = values.mean()
                        st.metric(label, f"{avg_val:.2f}")
                        st.caption(description)
                else:
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
