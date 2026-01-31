"""Upload & Extract tab for Mia Training Tracker."""

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz

# Import optional dependencies
try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

from shared import (
    GSHEETS_AVAILABLE,
    save_data_to_google_sheets,
    load_data_from_google_sheets,
)


def parse_ocr_text(text):
    """
    Parse OCR text to extract training metrics.
    This is imported from the main app or defined here for the module.
    """
    import re
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

    return extracted


def render(calculate_personal_records_func):
    """
    Render the Upload & Extract tab content.

    Args:
        calculate_personal_records_func: Function to recalculate personal records after data changes
    """
    st.header("Upload CityPlay Screenshots")

    uploaded_files = st.file_uploader(
        "Upload one or more screenshots",
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        key='screenshot_upload'
    )

    if uploaded_files:
        st.write(f"📸 {len(uploaded_files)} image(s) uploaded")

        # Show thumbnails
        cols = st.columns(min(4, len(uploaded_files)))
        for idx, file in enumerate(uploaded_files):
            with cols[idx % 4]:
                if OCR_AVAILABLE:
                    image = Image.open(file)
                    st.image(image, caption=f"Image {idx+1}", use_container_width=True)

        if st.button("🔍 Extract Data from All Images", disabled=not OCR_AVAILABLE):
            if not OCR_AVAILABLE:
                st.error("❌ OCR is not available. Please enter data manually below.")
            else:
                with st.spinner("Processing images with OCR..."):
                    all_extracted = {}

                    for file in uploaded_files:
                        try:
                            image = Image.open(file)
                            text = pytesseract.image_to_string(image)
                            extracted = parse_ocr_text(text)

                            for key, value in extracted.items():
                                if value and str(value).strip():
                                    all_extracted[key] = value
                        except Exception as e:
                            st.error(f"Error processing {file.name}: {e}")

                    st.success(f"✅ Extracted {len(all_extracted)} fields!")
                    st.session_state['extracted_data'] = all_extracted

        if not OCR_AVAILABLE and uploaded_files:
            st.info("💡 OCR unavailable. Please manually enter data from your screenshots below.")

    # Data entry form
    st.subheader("Session Data Entry")

    # Initialize extracted_data in session state if not present
    if 'extracted_data' not in st.session_state:
        st.session_state['extracted_data'] = {}

    # Initialize form counter for reset functionality
    if 'form_counter' not in st.session_state:
        st.session_state['form_counter'] = 0

    # Initialize confirmation state
    if 'pending_submission' not in st.session_state:
        st.session_state['pending_submission'] = None

    extracted_data = st.session_state.get('extracted_data', {})

    # Training type selection (outside form to control field visibility)
    training_types = ["Speed and Agility", "Ball Work", "Match-Grass", "Match-Turf", "Match-Hard"]
    selected_training_type = st.selectbox(
        "Select Training Type",
        training_types,
        key=f"training_type_selector_{st.session_state['form_counter']}"
    )

    with st.form(f"session_form_{st.session_state['form_counter']}"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Session Info**")
            central_tz = pytz.timezone('America/Chicago')
            central_now = datetime.now(central_tz)
            date = st.date_input("Date", value=central_now)

            # Session Name - dropdown with existing values + custom entry
            existing_sessions = []
            if st.session_state.df is not None and 'session_name' in st.session_state.df.columns:
                existing_sessions = st.session_state.df['session_name'].dropna().unique().tolist()
            session_options = ["-- Enter New --"] + sorted(existing_sessions)
            session_choice = st.selectbox("Session Name", session_options, key="session_name_select")
            if session_choice == "-- Enter New --":
                session_name = st.text_input("↳ Enter New Session Name", value=extracted_data.get('session_name', ''), key="session_name_input")
            else:
                session_name = session_choice

            # Coach - dropdown with existing values + custom entry
            existing_coaches = []
            if st.session_state.df is not None and 'coach' in st.session_state.df.columns:
                existing_coaches = st.session_state.df['coach'].dropna().unique().tolist()
            coach_options = ["-- Enter New --"] + sorted(existing_coaches)
            coach_choice = st.selectbox("Coach", coach_options, key="coach_select")
            if coach_choice == "-- Enter New --":
                coach = st.text_input("↳ Enter New Coach Name", value=extracted_data.get('coach', ''), key="coach_input")
            else:
                coach = coach_choice

            # Location - dropdown with existing values + custom entry
            existing_locations = []
            if st.session_state.df is not None and 'location' in st.session_state.df.columns:
                existing_locations = st.session_state.df['location'].dropna().unique().tolist()
            location_options = ["-- Enter New --"] + sorted(existing_locations)
            location_choice = st.selectbox("Location", location_options, key="location_select")
            if location_choice == "-- Enter New --":
                location = st.text_input("↳ Enter New Location", value=extracted_data.get('location', ''), key="location_input")
            else:
                location = location_choice

            surface = st.selectbox("Surface", ["Grass", "Turf", "Hard"])
            with_ball = "Yes" if (selected_training_type == "Ball Work" or "Match" in selected_training_type) else "No"

            duration = st.number_input("Duration (min)", value=int(extracted_data.get('duration', 0)) if extracted_data.get('duration') else 0)

            intensity_options = ["Minimal", "Extremely Easy", "Very Easy", "Easy", "Moderate",
                               "Somewhat Hard", "Hard", "Very Hard", "Extremely Hard", "Maximal"]
            intensity = st.selectbox("Intensity", intensity_options)

            st.write("**Movement Metrics (All Types)**")
            total_distance = st.number_input("Total Distance (mi)", value=float(extracted_data.get('total_distance', 0)) if extracted_data.get('total_distance') else 0.0, format="%.2f")
            sprint_distance = st.number_input("Sprint Distance (yd)", value=float(extracted_data.get('sprint_distance', 0)) if extracted_data.get('sprint_distance') else 0.0, format="%.1f")
            top_speed = st.number_input("Top Speed (mph)", value=float(extracted_data.get('top_speed', 0)) if extracted_data.get('top_speed') else 0.0, format="%.2f")
            num_sprints = st.number_input("Number of Sprints", value=int(extracted_data.get('num_sprints', 0)) if extracted_data.get('num_sprints') else 0)
            accelerations = st.number_input("Accl/Decl", value=int(extracted_data.get('accelerations', 0)) if extracted_data.get('accelerations') else 0)

            st.write("**Agility (All Types)**")
            left_turns = st.number_input("Left Turns", value=int(extracted_data.get('left_turns', 0)) if extracted_data.get('left_turns') else 0)
            right_turns = st.number_input("Right Turns", value=int(extracted_data.get('right_turns', 0)) if extracted_data.get('right_turns') else 0)
            back_turns = st.number_input("Back Turns", value=int(extracted_data.get('back_turns', 0)) if extracted_data.get('back_turns') else 0)
            intense_turns = st.number_input("Intense Turns", value=int(extracted_data.get('intense_turns', 0)) if extracted_data.get('intense_turns') else 0)
            avg_turn_entry = st.number_input("Avg Turn Entry Speed (mph)", value=float(extracted_data.get('avg_turn_entry', 0)) if extracted_data.get('avg_turn_entry') else 0.0, format="%.1f")
            avg_turn_exit = st.number_input("Avg Turn Exit Speed (mph)", value=float(extracted_data.get('avg_turn_exit', 0)) if extracted_data.get('avg_turn_exit') else 0.0, format="%.1f")

        with col2:
            # Ball Work fields - shown for Ball Work and Match types
            if selected_training_type in ["Ball Work", "Match-Grass", "Match-Turf", "Match-Hard"]:
                st.write("**Ball Work**")
                left_touches = st.number_input("Left Foot Touches", value=int(extracted_data.get('left_touches', 0)) if extracted_data.get('left_touches') else 0)
                right_touches = st.number_input("Right Foot Touches", value=int(extracted_data.get('right_touches', 0)) if extracted_data.get('right_touches') else 0)
                left_releases = st.number_input("Left Releases", value=int(extracted_data.get('left_releases', 0)) if extracted_data.get('left_releases') else 0)
                right_releases = st.number_input("Right Releases", value=int(extracted_data.get('right_releases', 0)) if extracted_data.get('right_releases') else 0)
                left_kicking_power = st.number_input("Left Kicking Power (mph)", value=float(extracted_data.get('left_kicking_power_mph', 0)) if extracted_data.get('left_kicking_power_mph') else 0.0, format="%.2f")
                right_kicking_power = st.number_input("Right Kicking Power (mph)", value=float(extracted_data.get('right_kicking_power_mph', 0)) if extracted_data.get('right_kicking_power_mph') else 0.0, format="%.2f")
            else:
                left_touches = 0
                right_touches = 0
                left_releases = 0
                right_releases = 0
                left_kicking_power = 0
                right_kicking_power = 0

            # Match-specific fields - shown only for Match types
            if selected_training_type in ["Match-Grass", "Match-Turf", "Match-Hard"]:
                st.write("**Match Stats**")
                position = st.text_input("Position", value=extracted_data.get('position', ''))
                goals = st.number_input("Goals", value=int(extracted_data.get('goals', 0)) if extracted_data.get('goals') else 0)
                assists = st.number_input("Assists", value=int(extracted_data.get('assists', 0)) if extracted_data.get('assists') else 0)
                ball_possessions = st.number_input("Ball Possessions", value=int(extracted_data.get('ball_possessions', 0)) if extracted_data.get('ball_possessions') else 0)
            else:
                position = ''
                goals = 0
                assists = 0
                ball_possessions = 0

        col_submit1, col_submit2 = st.columns([1, 1])
        with col_submit1:
            submitted = st.form_submit_button("💾 Add to Data File", use_container_width=True)
        with col_submit2:
            reset = st.form_submit_button("🔄 Reset Form", use_container_width=True)

        if reset:
            st.session_state['extracted_data'] = {}
            st.session_state['form_counter'] += 1
            st.session_state['pending_submission'] = None
            st.rerun()

        if submitted:
            # Calculate derived fields
            total_turns = left_turns + right_turns + back_turns
            ball_touches = left_touches + right_touches
            left_foot_pct = (left_touches / ball_touches * 100) if ball_touches > 0 else 0
            right_foot_pct = 100 - left_foot_pct if ball_touches > 0 else 0
            kicking_power = max(left_kicking_power, right_kicking_power)
            work_rate = round(((total_distance * 1760) / duration), 2) if duration > 0 else 0

            central_tz = pytz.timezone('America/Chicago')
            date_with_time = central_tz.localize(datetime.combine(date, datetime.min.time()))

            new_row = {
                'date': date_with_time,
                'session_name': session_name,
                'coach': coach,
                'location': location,
                'surface': surface,
                'with_ball': with_ball,
                'training_type': selected_training_type,
                'duration': duration,
                'intensity': intensity,
                'total_distance': total_distance,
                'sprint_distance': sprint_distance,
                'accelerations': accelerations,
                'top_speed': top_speed,
                'num_sprints': num_sprints,
                'left_turns': left_turns,
                'back_turns': back_turns,
                'right_turns': right_turns,
                'intense_turns': intense_turns,
                'total_turns': total_turns,
                'avg_turn_entry': avg_turn_entry,
                'avg_turn_exit': avg_turn_exit,
                'ball_touches': ball_touches,
                'left_touches': left_touches,
                'right_touches': right_touches,
                'left_foot_pct': left_foot_pct,
                'right_foot_pct': right_foot_pct,
                'left_releases': left_releases,
                'right_releases': right_releases,
                'kicking_power': kicking_power,
                'left_kicking_power_mph': left_kicking_power,
                'right_kicking_power_mph': right_kicking_power,
                'position': position,
                'goals': goals,
                'assists': assists,
                'work_rate': work_rate,
                'ball_possessions': ball_possessions,
            }

            st.session_state['pending_submission'] = new_row

    # Show confirmation dialog if there's a pending submission
    if st.session_state.get('pending_submission') is not None:
        st.warning("⚠️ **Confirm you want to update the data file**")

        col_confirm1, col_confirm2, col_confirm3 = st.columns([1, 1, 2])

        with col_confirm1:
            if st.button("✅ Yes", type="primary", use_container_width=True):
                new_row = st.session_state['pending_submission']

                if st.session_state.df is None:
                    st.session_state.df = pd.DataFrame([new_row])
                else:
                    st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)

                # Ensure data types are preserved after concat
                numeric_columns = [
                    'duration', 'ball_touches', 'total_distance', 'sprint_distance',
                    'accelerations', 'kicking_power', 'top_speed', 'num_sprints',
                    'left_touches', 'right_touches', 'left_foot_pct', 'right_foot_pct',
                    'left_releases', 'right_releases',
                    'left_kicking_power_mph', 'right_kicking_power_mph',
                    'left_turns', 'back_turns', 'right_turns', 'intense_turns',
                    'avg_turn_entry', 'avg_turn_exit', 'total_turns', 'work_rate',
                    'goals', 'assists', 'ball_possessions'
                ]

                for col in numeric_columns:
                    if col in st.session_state.df.columns:
                        st.session_state.df[col] = pd.to_numeric(st.session_state.df[col], errors='coerce')

                if 'date' in st.session_state.df.columns:
                    st.session_state.df['date'] = pd.to_datetime(st.session_state.df['date'], errors='coerce')

                calculate_personal_records_func()

                # Auto-save to Google Sheets if configured
                if GSHEETS_AVAILABLE and "google_sheets_url" in st.secrets:
                    with st.spinner("Saving to Google Sheets..."):
                        success, error = save_data_to_google_sheets(st.session_state.df)
                        if error:
                            st.warning(f"⚠️ Session added locally but cloud save failed: {error}")
                            st.info("💡 Use 'Save to Cloud' button in sidebar to sync manually")
                        else:
                            df_reloaded, reload_error = load_data_from_google_sheets()
                            if not reload_error and df_reloaded is not None:
                                st.session_state.df = df_reloaded
                                calculate_personal_records_func()
                            st.success("✅ Session added and saved to cloud!")
                else:
                    st.success("✅ Session added successfully!")

                st.session_state['extracted_data'] = {}
                st.session_state['form_counter'] += 1
                st.session_state['pending_submission'] = None

                if 'ai_insights_generated' in st.session_state:
                    st.session_state.ai_insights_generated = False
                if 'ai_insights_report' in st.session_state:
                    st.session_state.ai_insights_report = ""

                st.rerun()

        with col_confirm2:
            if st.button("❌ No", use_container_width=True):
                st.session_state['pending_submission'] = None
                st.rerun()
