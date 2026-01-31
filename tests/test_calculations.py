"""Tests for calculation functions in shared.py."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared import calculate_personal_records


class TestCalculatePersonalRecords:
    """Tests for calculate_personal_records function."""

    def test_empty_dataframe(self, empty_df):
        """Test with empty DataFrame returns empty dicts."""
        pr, dates, foot = calculate_personal_records(empty_df)
        assert pr == {}
        assert dates == {}
        assert foot == {}

    def test_none_dataframe(self):
        """Test with None returns empty dicts."""
        pr, dates, foot = calculate_personal_records(None)
        assert pr == {}
        assert dates == {}
        assert foot == {}

    def test_top_speed_record(self, sample_training_df):
        """Test top speed personal record is calculated correctly."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        assert pr['top_speed'] == 13.0  # Max of [12.5, 13.0, 12.8]

    def test_sprint_distance_record(self, sample_training_df):
        """Test sprint distance personal record."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        assert pr['sprint_distance'] == 180  # Max of [150, 180, 165]

    def test_ball_touches_record(self, sample_training_df):
        """Test ball touches personal record."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        assert pr['ball_touches'] == 250  # Max of [200, 250, 220]

    def test_kicking_power_record(self, sample_training_df):
        """Test kicking power personal record."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        assert pr['kicking_power'] == 38.0  # Max of [35.0, 38.0, 36.5]

    def test_kicking_power_foot(self, sample_training_df):
        """Test kicking power foot determination."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        # Right foot has higher power (38.0 vs 33.0 on PR date)
        assert foot['kicking_power'] == 'R'

    def test_intense_turns_record(self, sample_training_df):
        """Test intense turns personal record."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        assert pr['intense_turns'] == 10  # Max of [8, 10, 9]

    def test_total_distance_record(self, sample_training_df):
        """Test total distance personal record."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        assert pr['total_distance'] == 1.8  # Max of [1.5, 1.8, 1.6]

    def test_pr_dates_recorded(self, sample_training_df):
        """Test that PR dates are recorded correctly."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        # Top speed PR was on 2024-01-05 (index 1, where value is 13.0)
        assert dates['top_speed'] == pd.Timestamp('2024-01-05')

    def test_left_right_ratio(self, sample_training_df):
        """Test left/right touch ratio calculation."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        # Best ratio closest to 0.5:
        # Row 0: 80/120 = 0.667
        # Row 1: 100/150 = 0.667
        # Row 2: 90/130 = 0.692
        # All are > 0.5, so closest to 0.5 is 0.667
        assert 'left_right_ratio' in pr
        assert abs(pr['left_right_ratio'] - 0.667) < 0.01

    def test_left_right_ratio_average(self, sample_training_df):
        """Test left/right ratio average calculation."""
        pr, dates, foot = calculate_personal_records(sample_training_df)
        # (0.667 + 0.667 + 0.692) / 3 = 0.675
        assert 'left_right_ratio_avg' in pr
        assert abs(pr['left_right_ratio_avg'] - 0.675) < 0.01

    def test_handles_null_values(self, sample_training_df_with_nulls):
        """Test that null values are handled correctly."""
        pr, dates, foot = calculate_personal_records(sample_training_df_with_nulls)
        # Should still calculate valid records
        assert 'top_speed' in pr
        assert pr['top_speed'] == 12.8  # Max of [12.5, NaN, 12.8]

    def test_zero_touches_excluded_from_ratio(self, sample_training_df_with_nulls):
        """Test that sessions with zero touches are excluded from ratio."""
        pr, dates, foot = calculate_personal_records(sample_training_df_with_nulls)
        # Row 1 has left=0, right=0, should be excluded
        # Only rows 0 and 2 should be considered
        assert 'left_right_ratio' in pr

    def test_missing_columns_handled(self):
        """Test that missing columns don't cause errors."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01']),
            'top_speed': [12.5],
            # Missing most other columns
        })
        pr, dates, foot = calculate_personal_records(df)
        assert pr['top_speed'] == 12.5
        # Other records should not be in the dict
        assert 'ball_touches' not in pr

    def test_left_foot_kicking_power(self):
        """Test when left foot has higher kicking power."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01']),
            'kicking_power': [40.0],
            'left_kicking_power_mph': [40.0],
            'right_kicking_power_mph': [35.0],
        })
        pr, dates, foot = calculate_personal_records(df)
        assert foot['kicking_power'] == 'L'

    def test_equal_kicking_power_defaults_to_left(self):
        """Test when both feet have equal power, defaults to left."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01']),
            'kicking_power': [38.0],
            'left_kicking_power_mph': [38.0],
            'right_kicking_power_mph': [38.0],
        })
        pr, dates, foot = calculate_personal_records(df)
        assert foot['kicking_power'] == 'L'


class TestCalculatePersonalRecordsEdgeCases:
    """Edge case tests for calculate_personal_records."""

    def test_single_row_dataframe(self):
        """Test with single row DataFrame."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01']),
            'top_speed': [12.5],
            'ball_touches': [200],
        })
        pr, dates, foot = calculate_personal_records(df)
        assert pr['top_speed'] == 12.5
        assert pr['ball_touches'] == 200

    def test_all_null_column(self):
        """Test with a column that's all nulls."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'top_speed': [None, None],
            'ball_touches': [200, 250],
        })
        pr, dates, foot = calculate_personal_records(df)
        # top_speed should not be in PR since all values are null
        assert 'top_speed' not in pr
        assert pr['ball_touches'] == 250

    def test_negative_values_handled(self):
        """Test that negative values are handled (edge case)."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01', '2024-01-02']),
            'top_speed': [-5.0, 12.5],  # Negative would be data error
        })
        pr, dates, foot = calculate_personal_records(df)
        # Should still find max
        assert pr['top_speed'] == 12.5

    def test_string_numeric_conversion(self):
        """Test that string numbers are converted correctly."""
        df = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01']),
            'top_speed': ['12.5'],  # String instead of float
            'ball_touches': ['200'],
        })
        pr, dates, foot = calculate_personal_records(df)
        assert pr['top_speed'] == 12.5
        assert pr['ball_touches'] == 200

    def test_no_date_column(self):
        """Test with no date column."""
        df = pd.DataFrame({
            'top_speed': [12.5, 13.0],
            'ball_touches': [200, 250],
        })
        pr, dates, foot = calculate_personal_records(df)
        assert pr['top_speed'] == 13.0
        assert dates['top_speed'] is None
