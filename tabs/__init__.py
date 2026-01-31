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

from . import dashboard
from . import upload
from . import ai_insights
from . import analytics
from . import speed
from . import agility
from . import ball_work
from . import match_play
from . import personal_records

__all__ = [
    # Components
    'coach_filter',
    'time_filter',
    'create_line_chart',
    'display_metric_with_best',
    # Tab modules
    'dashboard',
    'upload',
    'ai_insights',
    'analytics',
    'speed',
    'agility',
    'ball_work',
    'match_play',
    'personal_records',
]
