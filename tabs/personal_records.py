"""Personal Records tab for Mia Training Tracker."""

import streamlit as st


def render():
    """Render the Personal Records tab content."""
    st.header("🏆 Personal Records")

    if not st.session_state.personal_records:
        st.warning("📊 No personal records calculated. Please upload your Excel file in the sidebar.")
        return

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
