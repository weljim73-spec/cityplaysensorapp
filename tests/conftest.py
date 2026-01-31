"""Pytest fixtures for Mia Training Tracker tests."""

import pytest
import pandas as pd
from datetime import datetime


@pytest.fixture
def sample_training_df():
    """Create a sample training DataFrame for testing."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2024-01-01', '2024-01-05', '2024-01-10']),
        'top_speed': [12.5, 13.0, 12.8],
        'sprint_distance': [150, 180, 165],
        'ball_touches': [200, 250, 220],
        'kicking_power': [35.0, 38.0, 36.5],
        'total_distance': [1.5, 1.8, 1.6],
        'intense_turns': [8, 10, 9],
        'left_touches': [80, 100, 90],
        'right_touches': [120, 150, 130],
        'left_kicking_power_mph': [30.0, 33.0, 32.0],
        'right_kicking_power_mph': [35.0, 38.0, 36.5],
    })


@pytest.fixture
def sample_training_df_with_nulls():
    """Create a sample DataFrame with some null values."""
    return pd.DataFrame({
        'date': pd.to_datetime(['2024-01-01', '2024-01-05', None]),
        'top_speed': [12.5, None, 12.8],
        'sprint_distance': [150, 180, None],
        'ball_touches': [None, 250, 220],
        'intense_turns': [8, 10, 9],
        'left_touches': [80, 0, 90],
        'right_touches': [120, 0, 130],
    })


@pytest.fixture
def empty_df():
    """Create an empty DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def sample_ocr_text_basic():
    """Sample OCR text with basic metrics."""
    return """
    Training Session Summary
    Duration: 45 min
    Total Distance: 1.5 mi
    Top Speed: 13.2 mph
    Sprints: 12
    Ball Touches: 250
    """


@pytest.fixture
def sample_ocr_text_full():
    """Sample OCR text with all metrics."""
    return """
    Training Session - Agility Focus
    Duration: 60 min
    Intensity: Intense
    Training Type: Speed

    Movement Metrics:
    Total Distance: 2.1 mi
    Sprint Distance: 200 yd
    Top Speed: 14.5 mph
    Sprints: 15
    Accl/Decl: 45

    Agility:
    Left Turns: 85
    Right Turns: 90
    Back Turns: 45
    Intense Turns: 12
    Turn Entry Speed: 8.5 mph
    Turn Exit Speed: 9.2 mph

    Ball Work:
    Ball Touches: 300
    Left Foot: 120 (40%)
    Right Foot: 180 (60%)
    Kicking Power: 42.0 mph
    """


@pytest.fixture
def sample_ocr_text_with_kicking_power():
    """Sample OCR text with left/right kicking power."""
    return """
    Kicking Power Analysis
    Left Foot: 32.5 mph
    Right Foot: 38.0 mph
    Kicking Power: 38.0 mph
    """
