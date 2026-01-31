"""Agility Analysis tab for Mia Training Tracker."""

import streamlit as st
import pandas as pd

from shared import get_central_time


def render():
    """Render the Agility Analysis tab content."""
    st.header("🔄 Agility Analysis")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
        return

    df = st.session_state.df.copy()

    st.info("**What is Agility?**\n\nAgility is the ability to respond to game actions fast through quick turns or changes in pace.")

    # Coach filter
    if 'coach' in df.columns:
        coaches = df['coach'].dropna().unique().tolist()
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
