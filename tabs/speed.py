"""Speed Analysis tab for Mia Training Tracker."""

import streamlit as st
import pandas as pd

from shared import get_central_time


def render():
    """Render the Speed Analysis tab content."""
    st.header("⚡ Speed Analysis")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
        return

    df = st.session_state.df.copy()

    st.info("**What is Speed?**\n\nSpeed measures explosive power, acceleration, and top-end velocity in training sessions.")

    # Coach filter
    if 'coach' in df.columns:
        coaches = df['coach'].dropna().unique().tolist()
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
