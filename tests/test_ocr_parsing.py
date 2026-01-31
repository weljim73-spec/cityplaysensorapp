"""Tests for OCR text parsing functionality."""

import pytest
import sys
import os
import re

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def parse_ocr_text(text):
    """
    Parse OCR text to extract metrics.

    This is a copy of the function from streamlit_app.py for testing purposes,
    since importing from streamlit_app.py requires streamlit which adds complexity.
    """
    extracted = {}

    patterns = {
        'duration': r'(\d+)\s*min',
        'training_type': r'(technical|speed|agility|conditioning)',
        'intensity': r'(moderate|light|intense|hard)',
        'total_distance': r'(?:total\s+)?distance[:\s]*(\d+\.?\d*)\s*mi',
        'sprint_distance': r'sprint\s+distance[:\s]*(\d+\.?\d*)\s*(?:yd|yards)',
        'top_speed': r'top\s+speed[:\s]*(\d+\.?\d*)\s*mph',
        'num_sprints': r'sprints?\s*[:\s#]*(\d+)',
        'accelerations': r'(?:accl?|accel(?:eration)?s?)\s*[:\s/]+\s*(?:decl?)?\s*(\d+)',
        'ball_touches': r'(?:ball\s+)?touches\s*[:\s#]*(\d+)',
        'kicking_power': r'(?:kicking\s+)?power\s*[:\s]*(\d+\.?\d*)\s*mph',
        'left_turns': r'left\s+turns?\s*[:\s]*(\d+)',
        'right_turns': r'right\s+turns?\s*[:\s]*(\d+)',
        'back_turns': r'back\s+turns?\s*[:\s]*(\d+)',
        'intense_turns': r'intense\s+turns?\s*[:\s#]*(\d+)',
        'avg_turn_entry': r'(?:average\s+)?turn\s+entry\s+speed\s*[:\s]*(\d+\.?\d*)\s*mph',
        'avg_turn_exit': r'(?:average\s+)?turn\s+exit\s+speed\s*[:\s]*(\d+\.?\d*)\s*mph',
    }

    text_lower = text.lower()

    for key, pattern in patterns.items():
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            extracted[key] = match.group(1)

    # Special handling for left/right kicking power
    lines = text_lower.split('\n')
    for i, line in enumerate(lines):
        if 'kicking power' in line and i > 0:
            context = '\n'.join(lines[max(0, i-3):min(len(lines), i+4)])
            power_matches = re.findall(r'(\d+\.?\d*)\s*mph', context)
            if len(power_matches) >= 2:
                extracted['left_kicking_power_mph'] = power_matches[0]
                extracted['right_kicking_power_mph'] = power_matches[1]
                break

    # Touch percentages and counts
    touch_pattern = re.search(
        r'(\d+)\s*\((\d+)%\)[^\d]*touch[^\d]*(\d+)\s*\((\d+)%\)',
        text_lower, re.IGNORECASE
    )
    if touch_pattern:
        extracted['left_touches'] = touch_pattern.group(1)
        extracted['left_pct'] = touch_pattern.group(2)
        extracted['right_touches'] = touch_pattern.group(3)
        extracted['right_pct'] = touch_pattern.group(4)

    # Aggressive turn detection fallbacks
    if 'left_turns' not in extracted:
        for pattern in [r'(\d+)\s*[^\w\d]*left\s+turns?', r'left\s+turns?\s*[^\w\d]*(\d+)']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted['left_turns'] = match.group(1)
                break

    if 'right_turns' not in extracted:
        for pattern in [r'(\d+)\s*[^\w\d]*right\s+turns?', r'right\s+turns?\s*[^\w\d]*(\d+)']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted['right_turns'] = match.group(1)
                break

    if 'back_turns' not in extracted:
        for pattern in [r'(\d+)\s*[^\w\d]*back\s+turns?', r'back\s+turns?\s*[^\w\d]*(\d+)']:
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                extracted['back_turns'] = match.group(1)
                break

    return extracted


class TestParseOcrTextBasic:
    """Tests for basic OCR parsing functionality."""

    def test_parse_duration(self):
        """Test parsing duration from OCR text."""
        text = "Duration: 45 min"
        result = parse_ocr_text(text)
        assert result.get('duration') == '45'

    def test_parse_duration_no_space(self):
        """Test parsing duration without space."""
        text = "Duration: 45min"
        result = parse_ocr_text(text)
        assert result.get('duration') == '45'

    def test_parse_top_speed(self):
        """Test parsing top speed from OCR text."""
        text = "Top Speed: 13.2 mph"
        result = parse_ocr_text(text)
        assert result.get('top_speed') == '13.2'

    def test_parse_top_speed_integer(self):
        """Test parsing integer top speed."""
        text = "Top Speed: 14 mph"
        result = parse_ocr_text(text)
        assert result.get('top_speed') == '14'

    def test_parse_total_distance(self):
        """Test parsing total distance."""
        text = "Total Distance: 1.5 mi"
        result = parse_ocr_text(text)
        assert result.get('total_distance') == '1.5'

    def test_parse_distance_without_total(self):
        """Test parsing distance without 'total' prefix."""
        text = "Distance: 2.0 mi"
        result = parse_ocr_text(text)
        assert result.get('total_distance') == '2.0'

    def test_parse_sprint_distance(self):
        """Test parsing sprint distance."""
        text = "Sprint Distance: 150 yd"
        result = parse_ocr_text(text)
        assert result.get('sprint_distance') == '150'

    def test_parse_sprint_distance_yards(self):
        """Test parsing sprint distance with 'yards'."""
        text = "Sprint Distance: 200 yards"
        result = parse_ocr_text(text)
        assert result.get('sprint_distance') == '200'

    def test_parse_ball_touches(self):
        """Test parsing ball touches."""
        text = "Ball Touches: 250"
        result = parse_ocr_text(text)
        assert result.get('ball_touches') == '250'

    def test_parse_touches_without_ball(self):
        """Test parsing touches without 'ball' prefix."""
        text = "Touches: 300"
        result = parse_ocr_text(text)
        assert result.get('ball_touches') == '300'

    def test_parse_sprints(self):
        """Test parsing number of sprints."""
        text = "Sprints: 15"
        result = parse_ocr_text(text)
        assert result.get('num_sprints') == '15'

    def test_parse_accelerations(self):
        """Test parsing accelerations."""
        text = "Accl/Decl: 45"
        result = parse_ocr_text(text)
        assert result.get('accelerations') == '45'


class TestParseOcrTextAgility:
    """Tests for agility metrics parsing."""

    def test_parse_left_turns(self):
        """Test parsing left turns."""
        text = "Left Turns: 85"
        result = parse_ocr_text(text)
        assert result.get('left_turns') == '85'

    def test_parse_right_turns(self):
        """Test parsing right turns."""
        text = "Right Turns: 90"
        result = parse_ocr_text(text)
        assert result.get('right_turns') == '90'

    def test_parse_back_turns(self):
        """Test parsing back turns."""
        text = "Back Turns: 45"
        result = parse_ocr_text(text)
        assert result.get('back_turns') == '45'

    def test_parse_intense_turns(self):
        """Test parsing intense turns."""
        text = "Intense Turns: 12"
        result = parse_ocr_text(text)
        assert result.get('intense_turns') == '12'

    def test_parse_turn_entry_speed(self):
        """Test parsing turn entry speed."""
        text = "Turn Entry Speed: 8.5 mph"
        result = parse_ocr_text(text)
        assert result.get('avg_turn_entry') == '8.5'

    def test_parse_turn_exit_speed(self):
        """Test parsing turn exit speed."""
        text = "Turn Exit Speed: 9.2 mph"
        result = parse_ocr_text(text)
        assert result.get('avg_turn_exit') == '9.2'


class TestParseOcrTextTrainingType:
    """Tests for training type and intensity parsing."""

    def test_parse_training_type_speed(self):
        """Test parsing speed training type."""
        text = "Training Type: Speed"
        result = parse_ocr_text(text)
        assert result.get('training_type') == 'speed'

    def test_parse_training_type_agility(self):
        """Test parsing agility training type."""
        text = "Training Type: Agility"
        result = parse_ocr_text(text)
        assert result.get('training_type') == 'agility'

    def test_parse_intensity_intense(self):
        """Test parsing intense intensity."""
        text = "Intensity: Intense"
        result = parse_ocr_text(text)
        assert result.get('intensity') == 'intense'

    def test_parse_intensity_moderate(self):
        """Test parsing moderate intensity."""
        text = "Intensity: Moderate"
        result = parse_ocr_text(text)
        assert result.get('intensity') == 'moderate'


class TestParseOcrTextKickingPower:
    """Tests for kicking power parsing."""

    def test_parse_kicking_power(self):
        """Test parsing general kicking power."""
        text = "Kicking Power: 38.0 mph"
        result = parse_ocr_text(text)
        assert result.get('kicking_power') == '38.0'

    def test_parse_left_right_kicking_power(self, sample_ocr_text_with_kicking_power):
        """Test parsing left and right kicking power."""
        result = parse_ocr_text(sample_ocr_text_with_kicking_power)
        assert result.get('left_kicking_power_mph') == '32.5'
        assert result.get('right_kicking_power_mph') == '38.0'


class TestParseOcrTextComplex:
    """Tests for complex OCR text parsing."""

    def test_parse_full_session(self, sample_ocr_text_full):
        """Test parsing a complete session summary."""
        result = parse_ocr_text(sample_ocr_text_full)

        assert result.get('duration') == '60'
        assert result.get('intensity') == 'intense'
        assert result.get('training_type') == 'speed'
        assert result.get('total_distance') == '2.1'
        assert result.get('sprint_distance') == '200'
        assert result.get('top_speed') == '14.5'
        assert result.get('num_sprints') == '15'
        assert result.get('accelerations') == '45'
        assert result.get('left_turns') == '85'
        assert result.get('right_turns') == '90'
        assert result.get('back_turns') == '45'
        assert result.get('intense_turns') == '12'
        assert result.get('ball_touches') == '300'

    def test_parse_basic_session(self, sample_ocr_text_basic):
        """Test parsing a basic session summary."""
        result = parse_ocr_text(sample_ocr_text_basic)

        assert result.get('duration') == '45'
        assert result.get('total_distance') == '1.5'
        assert result.get('top_speed') == '13.2'
        assert result.get('num_sprints') == '12'
        assert result.get('ball_touches') == '250'

    def test_parse_empty_text(self):
        """Test parsing empty text returns empty dict."""
        result = parse_ocr_text("")
        assert result == {}

    def test_parse_irrelevant_text(self):
        """Test parsing irrelevant text returns empty dict."""
        text = "This is just some random text with no metrics."
        result = parse_ocr_text(text)
        assert result == {}

    def test_case_insensitivity(self):
        """Test that parsing is case insensitive."""
        text = "TOP SPEED: 15.0 MPH\nBALL TOUCHES: 200"
        result = parse_ocr_text(text)
        assert result.get('top_speed') == '15.0'
        assert result.get('ball_touches') == '200'
