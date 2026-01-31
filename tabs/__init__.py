"""
Tabs package for Mia Training Tracker.

This package contains reusable UI components and tab-specific modules.
"""

from .components import (
    coach_filter,
    time_filter,
    create_line_chart,
    display_metric_with_best,
)

__all__ = [
    'coach_filter',
    'time_filter',
    'create_line_chart',
    'display_metric_with_best',
]
