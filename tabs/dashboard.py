"""Dashboard tab for Mia Training Tracker."""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


def render():
    """Render the Dashboard tab content."""
    st.header("📊 Training Dashboard")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar or sync from Google Sheets.")
        return

    df = st.session_state.df.copy()

    # Key Metrics Row 1
    st.subheader("🎯 Key Performance Indicators")
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        if 'top_speed' in df.columns:
            values = pd.to_numeric(df['top_speed'], errors='coerce').dropna()
            if len(values) > 0:
                avg_speed = values.mean()
                best_speed = values.max()
                st.metric("Top Speed (mph) (avg)", f"{avg_speed:.1f}",
                         delta=f"Best: {best_speed:.1f}", delta_color="normal")

    with col2:
        if 'intense_turns' in df.columns:
            values = pd.to_numeric(df['intense_turns'], errors='coerce').dropna()
            if len(values) > 0:
                avg_turns = values.mean()
                best_turns = values.max()
                st.metric("Intense Turns (avg)", f"{avg_turns:.1f}",
                         delta=f"Best: {best_turns:.1f}", delta_color="normal")

    with col3:
        if 'left_kicking_power_mph' in df.columns:
            left_power = pd.to_numeric(df['left_kicking_power_mph'], errors='coerce').dropna()
            if len(left_power) > 0:
                avg_left = left_power.mean()
                best_left = left_power.max()
                st.metric("Left Foot Power (mph)", f"{avg_left:.1f}",
                         delta=f"Best: {best_left:.1f}", delta_color="normal")
            else:
                st.metric("Left Foot Power (mph)", "N/A",
                         delta="No data", delta_color="off")

    with col4:
        if 'right_kicking_power_mph' in df.columns:
            right_power = pd.to_numeric(df['right_kicking_power_mph'], errors='coerce').dropna()
            if len(right_power) > 0:
                avg_right = right_power.mean()
                best_right = right_power.max()
                st.metric("Right Foot Power (mph)", f"{avg_right:.1f}",
                         delta=f"Best: {best_right:.1f}", delta_color="normal")
            else:
                st.metric("Right Foot Power (mph)", "N/A",
                         delta="No data", delta_color="off")

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
            else:
                st.metric("L/R Touch Ratio (avg)", "N/A",
                         delta="No data", delta_color="off")

    st.markdown("---")

    # Training Summary Row
    st.subheader("📅 Training Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Sessions", len(df))

    with col2:
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            date_range = (df['date'].max() - df['date'].min()).days
            st.metric("Training Period (days)", date_range)

    with col3:
        if 'duration' in df.columns:
            total_mins = pd.to_numeric(df['duration'], errors='coerce').sum()
            st.metric("Total Training Time", f"{total_mins/60:.1f} hrs")

    with col4:
        if 'with_ball' in df.columns:
            ball_sessions = (df['with_ball'].str.lower() == 'yes').sum()
            st.metric("Ball Work Sessions", f"{ball_sessions}/{len(df)}")

    st.markdown("---")

    # Recent Performance Trends
    st.subheader("📈 Recent Trends (Last 5 Sessions)")

    if len(df) >= 5:
        recent_df = df.tail(5)

        col1, col2 = st.columns(2)

        with col1:
            # Speed trend
            if 'top_speed' in recent_df.columns and 'date' in recent_df.columns:
                fig, ax = plt.subplots(figsize=(8, 4))
                speed_data = recent_df[['date', 'top_speed']].dropna()
                if len(speed_data) > 0:
                    ax.plot(speed_data['date'], speed_data['top_speed'],
                           marker='o', linewidth=2, markersize=8, color='#1E88E5')
                    ax.set_xlabel('Date', fontsize=10)
                    ax.set_ylabel('Top Speed (mph)', fontsize=10)
                    ax.set_title('Top Speed Trend', fontsize=12, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)

        with col2:
            # Agility trend
            if 'intense_turns' in recent_df.columns and 'date' in recent_df.columns:
                fig, ax = plt.subplots(figsize=(8, 4))
                agility_data = recent_df[['date', 'intense_turns']].dropna()
                if len(agility_data) > 0:
                    ax.plot(agility_data['date'], agility_data['intense_turns'],
                           marker='s', linewidth=2, markersize=8, color='#E53935')
                    ax.set_xlabel('Date', fontsize=10)
                    ax.set_ylabel('Intense Turns', fontsize=10)
                    ax.set_title('Agility Trend', fontsize=12, fontweight='bold')
                    ax.grid(True, alpha=0.3)
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    st.pyplot(fig, use_container_width=True)
                    plt.close(fig)
    else:
        st.info("Need at least 5 sessions to show trend charts")

    st.markdown("---")

    # Quick Insights
    st.subheader("💡 Quick Insights")
    col1, col2 = st.columns(2)

    with col1:
        # Two-footed balance
        if 'left_touches' in df.columns and 'right_touches' in df.columns:
            left_total = pd.to_numeric(df['left_touches'], errors='coerce').sum()
            right_total = pd.to_numeric(df['right_touches'], errors='coerce').sum()
            if right_total > 0:
                ratio = left_total / right_total
                st.info(f"**⚖️ Two-Footed Balance**\n\nLeft/Right Ratio: {ratio:.2f}\n\n" +
                       ("✅ Excellent balance!" if ratio >= 0.5 else
                        "📈 Good progress - keep working left foot!" if ratio >= 0.4 else
                        "⚠️ Focus on left foot development"))

    with col2:
        # Training intensity
        if 'intensity' in df.columns:
            intensity_counts = df['intensity'].value_counts()
            if len(intensity_counts) > 0:
                most_common = intensity_counts.index[0]
                count = intensity_counts.iloc[0]
                st.info(f"**🔥 Training Intensity**\n\nMost Common: {most_common}\n\n" +
                       f"Used in {count}/{len(df)} sessions ({count/len(df)*100:.0f}%)")
