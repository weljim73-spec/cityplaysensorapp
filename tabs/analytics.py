"""Training Analytics tab for Mia Training Tracker."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


def render():
    """Render the Training Analytics tab content."""
    st.header("📊 Training Analytics")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
        return

    df = st.session_state.df.copy()

    # Ensure date column is datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date')

    # Coach filter
    if 'coach' in df.columns:
        coaches = df['coach'].dropna().unique().tolist()
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
        return

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
