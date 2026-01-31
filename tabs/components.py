"""
Reusable UI components for Mia Training Tracker tabs.

This module contains common UI patterns used across multiple tabs to reduce
code duplication and improve maintainability.
"""

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from typing import Optional, Tuple, List


def coach_filter(df: pd.DataFrame, key: str) -> pd.DataFrame:
    """
    Render a coach filter selectbox and return filtered DataFrame.

    Args:
        df: DataFrame with a 'coach' column
        key: Unique key for the Streamlit selectbox widget

    Returns:
        Filtered DataFrame based on selected coach, or original if 'All Coaches'
    """
    if 'coach' not in df.columns:
        return df

    coaches = df['coach'].dropna().unique().tolist()
    # Display "No Coach" instead of "Solo"
    coaches_display = ["No Coach" if str(c).lower() == "solo" else c for c in coaches]
    coaches_display_map = dict(zip(coaches_display, coaches))

    selected_coach_display = st.selectbox(
        "Filter by Coach",
        ["All Coaches"] + coaches_display,
        key=key
    )

    if selected_coach_display != "All Coaches":
        selected_coach = coaches_display_map[selected_coach_display]
        return df[df['coach'] == selected_coach].copy()

    return df.copy()


def time_filter(
    df: pd.DataFrame,
    key: str,
    options: List[str] = None
) -> Tuple[pd.DataFrame, str]:
    """
    Render a time period filter and return filtered DataFrame.

    Args:
        df: DataFrame with a 'date' column
        key: Unique key for the Streamlit radio widget
        options: List of time filter options (default: ["All Time", "Last 30 Days"])

    Returns:
        Tuple of (filtered DataFrame, selected time period string)
    """
    if options is None:
        options = ["All Time", "Last 30 Days"]

    if 'date' not in df.columns:
        return df, options[0]

    selected = st.radio(
        "Time Period",
        options,
        horizontal=True,
        key=key
    )

    if selected == "Last 30 Days":
        df = df.copy()
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        latest_date = df['date'].max()
        thirty_days_ago = latest_date - pd.Timedelta(days=30)
        filtered_df = df[df['date'] > thirty_days_ago].copy()
        return filtered_df, selected

    return df.copy(), selected


def create_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    xlabel: str,
    ylabel: str,
    figsize: Tuple[int, int] = (10, 6),
    marker: str = 'o',
    color: str = None,
    show_target_line: Optional[Tuple[float, str, str]] = None,
) -> plt.Figure:
    """
    Create a standardized line chart.

    Args:
        df: DataFrame containing the data
        x_col: Column name for x-axis
        y_col: Column name for y-axis
        title: Chart title
        xlabel: X-axis label
        ylabel: Y-axis label
        figsize: Figure size as (width, height)
        marker: Marker style for data points
        color: Line/marker color
        show_target_line: Optional tuple of (y_value, color, label) for horizontal target line

    Returns:
        matplotlib Figure object
    """
    fig, ax = plt.subplots(figsize=figsize)

    plot_kwargs = {
        'marker': marker,
        'linewidth': 2,
        'markersize': 8,
    }
    if color:
        plot_kwargs['color'] = color

    ax.plot(df[x_col], pd.to_numeric(df[y_col], errors='coerce'), **plot_kwargs)

    if show_target_line:
        y_val, line_color, label = show_target_line
        ax.axhline(y=y_val, color=line_color, linestyle='--', label=label)
        ax.legend()

    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    return fig


def display_metric_with_best(
    label: str,
    avg_value: float,
    best_value: float,
    format_str: str = "{:.1f}",
    caption: str = None,
) -> None:
    """
    Display a metric with its average and best value.

    Args:
        label: Metric label
        avg_value: Average value to display as main metric
        best_value: Best value to display as delta
        format_str: Format string for values
        caption: Optional caption text below the metric
    """
    st.metric(
        f"{label} (avg)",
        format_str.format(avg_value),
        delta=f"Best: {format_str.format(best_value)}",
        delta_color="normal"
    )
    if caption:
        st.caption(caption)


def display_time_range_info(df: pd.DataFrame, time_filter_value: str) -> None:
    """
    Display date range information for filtered data.

    Args:
        df: Filtered DataFrame with 'date' column
        time_filter_value: Selected time filter option
    """
    if 'date' not in df.columns or len(df) == 0:
        return

    df_copy = df.copy()
    df_copy['date'] = pd.to_datetime(df_copy['date'], errors='coerce')
    df_copy = df_copy.dropna(subset=['date'])

    if len(df_copy) == 0:
        return

    date_min = df_copy['date'].min()
    date_max = df_copy['date'].max()

    if time_filter_value == "Last 30 Days":
        st.caption(
            f"Showing data from {date_min.strftime('%b %d, %Y')} to "
            f"{date_max.strftime('%b %d, %Y')} ({len(df_copy)} sessions)"
        )
    else:
        st.caption(
            f"All time: {date_min.strftime('%b %d, %Y')} to "
            f"{date_max.strftime('%b %d, %Y')} ({len(df_copy)} sessions)"
        )
