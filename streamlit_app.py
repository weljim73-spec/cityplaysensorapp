"""
Mia Training Tracker - Streamlit Web App
Soccer training analytics and tracking application
Accessible from any browser including mobile devices
"""

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import pytesseract
from PIL import Image
import io
import re

# Page configuration
st.set_page_config(
    page_title="Mia Training Tracker",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for mobile responsiveness
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'df' not in st.session_state:
    st.session_state.df = None
if 'personal_records' not in st.session_state:
    st.session_state.personal_records = {}
if 'pr_dates' not in st.session_state:
    st.session_state.pr_dates = {}
if 'uploaded_images' not in st.session_state:
    st.session_state.uploaded_images = []

# Column mapping for Excel data
COLUMN_MAPPING = {
    'top_speed_mph': 'top_speed',
    'sprint_distance_yd': 'sprint_distance',
    'total_distance_mi': 'total_distance',
    'ball_touches': 'ball_touches',
    'duration_min': 'duration',
    'kicking_power_mph': 'kicking_power',
    'left_kicking_power_mph': 'left_kicking_power_mph',
    'right_kicking_power_mph': 'right_kicking_power_mph',
    'left_foot_pct': 'left_pct',
    'right_foot_pct': 'right_pct',
    'intense_turns': 'intense_turns',
    'left_touches': 'left_touches',
    'right_touches': 'right_touches',
    'left_turns': 'left_turns',
    'right_turns': 'right_turns',
    'back_turns': 'back_turns',
    'avg_turn_entry_speed_mph': 'avg_turn_entry',
    'avg_turn_exit_speed_mph': 'avg_turn_exit',
    'sprints': 'num_sprints',
    'accl_decl': 'accelerations',
    'training_type': 'training_type',
}

def load_excel_file(uploaded_file):
    """Load and process Excel file"""
    try:
        df = pd.read_excel(uploaded_file)

        # Normalize column names
        df.columns = df.columns.str.strip().str.lower()

        # Apply column mapping
        df.rename(columns=COLUMN_MAPPING, inplace=True)

        # Calculate right_pct if missing
        if 'left_pct' in df.columns and 'right_pct' not in df.columns:
            df['right_pct'] = 100 - pd.to_numeric(df['left_pct'], errors='coerce')

        st.session_state.df = df
        calculate_personal_records()

        return True, f"✅ Loaded {len(df)} sessions successfully!"
    except Exception as e:
        return False, f"❌ Error loading file: {str(e)}"

def calculate_personal_records():
    """Calculate all personal records from loaded data"""
    if st.session_state.df is None or len(st.session_state.df) == 0:
        return

    df = st.session_state.df

    pr_columns = {
        'top_speed': 'Top Speed',
        'sprint_distance': 'Sprint Distance',
        'ball_touches': 'Ball Touches',
        'kicking_power': 'Kicking Power',
        'total_distance': 'Total Distance',
        'intense_turns': 'Intense Turns'
    }

    personal_records = {}
    pr_dates = {}

    for col, name in pr_columns.items():
        if col in df.columns:
            numeric_col = pd.to_numeric(df[col], errors='coerce')
            max_val = numeric_col.max()
            if pd.notna(max_val):
                personal_records[col] = max_val
                max_idx = numeric_col.idxmax()
                if 'date' in df.columns and pd.notna(df.loc[max_idx, 'date']):
                    pr_dates[col] = pd.to_datetime(df.loc[max_idx, 'date'])
                else:
                    pr_dates[col] = None

    # L/R Touch Ratio
    if 'left_touches' in df.columns and 'right_touches' in df.columns:
        best_ratio = None
        best_distance = float('inf')
        best_date = None

        for idx, row in df.iterrows():
            left = pd.to_numeric(row.get('left_touches'), errors='coerce')
            right = pd.to_numeric(row.get('right_touches'), errors='coerce')

            if pd.notna(left) and pd.notna(right) and left > 0 and right > 0:
                ratio = left / right

                if ratio >= 0.5:
                    distance = abs(ratio - 0.5)
                else:
                    distance = 0.5 - ratio

                if distance < best_distance:
                    best_distance = distance
                    best_ratio = ratio
                    if 'date' in row and pd.notna(row['date']):
                        best_date = pd.to_datetime(row['date'])

        personal_records['left_right_ratio'] = best_ratio if best_ratio else 0.0
        pr_dates['left_right_ratio'] = best_date

    # L/R Ratio Average
    if 'left_touches' in df.columns and 'right_touches' in df.columns:
        left = pd.to_numeric(df['left_touches'], errors='coerce')
        right = pd.to_numeric(df['right_touches'], errors='coerce')
        valid_mask = (left > 0) & (right > 0)

        if valid_mask.any():
            ratios = left[valid_mask] / right[valid_mask]
            personal_records['left_right_ratio_avg'] = ratios.mean()
        else:
            personal_records['left_right_ratio_avg'] = 0.0

        pr_dates['left_right_ratio_avg'] = None

    st.session_state.personal_records = personal_records
    st.session_state.pr_dates = pr_dates

def parse_ocr_text(text):
    """Parse OCR text to extract metrics - enhanced version from v4.2"""
    extracted = {}

    # Common patterns - more flexible to handle OCR variations
    patterns = {
        # Session info
        'duration': r'(\d+)\s*min',
        'training_type': r'(technical|speed|agility|conditioning)',
        'intensity': r'(moderate|light|intense|hard)',

        # Movement metrics
        'total_distance': r'(?:total\s+)?distance[:\s]*(\d+\.?\d*)\s*mi',
        'sprint_distance': r'sprint\s+distance[:\s]*(\d+\.?\d*)\s*(?:yd|yards)',
        'top_speed': r'top\s+speed[:\s]*(\d+\.?\d*)\s*mph',
        'num_sprints': r'sprints?\s*[:\s#]*(\d+)',
        'accelerations': r'(?:accl?|accel(?:eration)?s?)\s*[:\s/]+\s*(?:decl?)?\s*(\d+)',

        # Ball work
        'ball_touches': r'(?:ball\s+)?touches\s*[:\s#]*(\d+)',

        # Kicking power
        'kicking_power': r'(?:kicking\s+)?power\s*[:\s]*(\d+\.?\d*)\s*mph',

        # Agility
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
    touch_pattern = re.search(r'(\d+)\s*\((\d+)%\)[^\d]*touch[^\d]*(\d+)\s*\((\d+)%\)', text_lower, re.IGNORECASE)
    if touch_pattern:
        extracted['left_touches'] = touch_pattern.group(1)
        extracted['left_pct'] = touch_pattern.group(2)
        extracted['right_touches'] = touch_pattern.group(3)
        extracted['right_pct'] = touch_pattern.group(4)

    # Aggressive turn detection
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

    # Ultimate fallback for back turns - process of elimination
    if 'back_turns' not in extracted and 'left_turns' in extracted and 'right_turns' in extracted:
        agility_match = re.search(r'agility', text_lower, re.IGNORECASE)
        if agility_match:
            agility_section = text_lower[agility_match.end():agility_match.end()+500]
            numbers = re.findall(r'\b(\d{2,3})\b', agility_section)
            if len(numbers) >= 3:
                for num in numbers:
                    if num != extracted.get('left_turns') and num != extracted.get('right_turns'):
                        num_val = int(num)
                        if 20 <= num_val <= 150:
                            extracted['back_turns'] = num
                            break

    return extracted

# Main App Header
st.markdown('<div class="main-header">⚽ Mia Training Tracker</div>', unsafe_allow_html=True)

# Sidebar for Excel file upload
with st.sidebar:
    st.header("📁 Data Management")

    uploaded_excel = st.file_uploader("Upload Training Data Excel", type=['xlsx'], key='excel_upload')

    if uploaded_excel is not None:
        if st.button("Load Excel File"):
            success, message = load_excel_file(uploaded_excel)
            if success:
                st.success(message)
            else:
                st.error(message)

    if st.session_state.df is not None:
        st.success(f"✅ {len(st.session_state.df)} sessions loaded")

        # Download current data
        if st.button("📥 Download Excel"):
            buffer = io.BytesIO()
            st.session_state.df.to_excel(buffer, index=False)
            buffer.seek(0)
            st.download_button(
                label="Download Training Data",
                data=buffer,
                file_name=f"Mia_Training_Data_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

# Main tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📸 Upload & Extract",
    "📊 Analytics",
    "🔄 Agility",
    "⚽ Ball Work",
    "🏆 Personal Records",
    "🤖 AI Insights"
])

# Tab 1: Upload & Extract
with tab1:
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
                image = Image.open(file)
                st.image(image, caption=f"Image {idx+1}", use_container_width=True)

        if st.button("🔍 Extract Data from All Images"):
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

    # Data entry form
    st.subheader("Session Data Entry")

    extracted_data = st.session_state.get('extracted_data', {})

    with st.form("session_form"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**Session Info**")
            date = st.date_input("Date", value=datetime.now())
            duration = st.number_input("Duration (min)", value=int(extracted_data.get('duration', 0)) if extracted_data.get('duration') else 0)
            training_type = st.text_input("Training Type", value=extracted_data.get('training_type', ''))
            intensity = st.text_input("Intensity", value=extracted_data.get('intensity', ''))

            st.write("**Movement Metrics**")
            total_distance = st.number_input("Total Distance (mi)", value=float(extracted_data.get('total_distance', 0)) if extracted_data.get('total_distance') else 0.0, format="%.2f")
            sprint_distance = st.number_input("Sprint Distance (yd)", value=float(extracted_data.get('sprint_distance', 0)) if extracted_data.get('sprint_distance') else 0.0, format="%.1f")
            top_speed = st.number_input("Top Speed (mph)", value=float(extracted_data.get('top_speed', 0)) if extracted_data.get('top_speed') else 0.0, format="%.2f")
            num_sprints = st.number_input("Number of Sprints", value=int(extracted_data.get('num_sprints', 0)) if extracted_data.get('num_sprints') else 0)
            accelerations = st.number_input("Accelerations", value=int(extracted_data.get('accelerations', 0)) if extracted_data.get('accelerations') else 0)

        with col2:
            st.write("**Ball Work**")
            ball_touches = st.number_input("Ball Touches", value=int(extracted_data.get('ball_touches', 0)) if extracted_data.get('ball_touches') else 0)
            left_touches = st.number_input("Left Foot Touches", value=int(extracted_data.get('left_touches', 0)) if extracted_data.get('left_touches') else 0)
            right_touches = st.number_input("Right Foot Touches", value=int(extracted_data.get('right_touches', 0)) if extracted_data.get('right_touches') else 0)
            left_kicking_power = st.number_input("Left Kicking Power (mph)", value=float(extracted_data.get('left_kicking_power_mph', 0)) if extracted_data.get('left_kicking_power_mph') else 0.0, format="%.2f")
            right_kicking_power = st.number_input("Right Kicking Power (mph)", value=float(extracted_data.get('right_kicking_power_mph', 0)) if extracted_data.get('right_kicking_power_mph') else 0.0, format="%.2f")

            st.write("**Agility**")
            left_turns = st.number_input("Left Turns", value=int(extracted_data.get('left_turns', 0)) if extracted_data.get('left_turns') else 0)
            right_turns = st.number_input("Right Turns", value=int(extracted_data.get('right_turns', 0)) if extracted_data.get('right_turns') else 0)
            back_turns = st.number_input("Back Turns", value=int(extracted_data.get('back_turns', 0)) if extracted_data.get('back_turns') else 0)
            intense_turns = st.number_input("Intense Turns", value=int(extracted_data.get('intense_turns', 0)) if extracted_data.get('intense_turns') else 0)
            avg_turn_entry = st.number_input("Avg Turn Entry Speed (mph)", value=float(extracted_data.get('avg_turn_entry', 0)) if extracted_data.get('avg_turn_entry') else 0.0, format="%.1f")
            avg_turn_exit = st.number_input("Avg Turn Exit Speed (mph)", value=float(extracted_data.get('avg_turn_exit', 0)) if extracted_data.get('avg_turn_exit') else 0.0, format="%.1f")

        submitted = st.form_submit_button("💾 Add to Excel")

        if submitted:
            # Create new row
            new_row = {
                'date': date,
                'duration': duration,
                'training_type': training_type,
                'intensity': intensity,
                'total_distance': total_distance,
                'sprint_distance': sprint_distance,
                'top_speed': top_speed,
                'num_sprints': num_sprints,
                'accelerations': accelerations,
                'ball_touches': ball_touches,
                'left_touches': left_touches,
                'right_touches': right_touches,
                'left_kicking_power_mph': left_kicking_power,
                'right_kicking_power_mph': right_kicking_power,
                'left_turns': left_turns,
                'right_turns': right_turns,
                'back_turns': back_turns,
                'intense_turns': intense_turns,
                'avg_turn_entry': avg_turn_entry,
                'avg_turn_exit': avg_turn_exit,
            }

            # Calculate percentages
            if left_touches > 0 or right_touches > 0:
                total_touches = left_touches + right_touches
                new_row['left_pct'] = (left_touches / total_touches * 100) if total_touches > 0 else 0
                new_row['right_pct'] = (right_touches / total_touches * 100) if total_touches > 0 else 0

            # Add to dataframe
            if st.session_state.df is None:
                st.session_state.df = pd.DataFrame([new_row])
            else:
                st.session_state.df = pd.concat([st.session_state.df, pd.DataFrame([new_row])], ignore_index=True)

            calculate_personal_records()
            st.success("✅ Session added successfully!")
            st.session_state['extracted_data'] = {}  # Clear extracted data
            st.rerun()

# Continue with other tabs in next part...
# This is the continuation to append to streamlit_app.py after line "# Continue with other tabs in next part..."

# Tab 2: Analytics
with tab2:
    st.header("📊 Training Analytics")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        df = st.session_state.df.copy()

        # Ensure date column is datetime
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            df = df.sort_values('date')

        # Chart selection
        chart_option = st.selectbox(
            "Select Chart",
            ["Top Speed Progress", "Ball Touches Progress", "Sprint Distance Progress",
             "Kicking Power Progress", "Agility Performance", "Turn Speed Analysis"]
        )

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
        st.pyplot(fig)

# Tab 3: Agility
with tab3:
    st.header("🔄 Agility Analysis")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        df = st.session_state.df.copy()

        st.info("**What is Agility?**\n\nAgility is the ability to respond to game actions fast through quick turns or changes in pace.")

        # Calculate agility statistics
        agility_metrics = [
            ('intense_turns', 'Intense Turns', '⚡ MOST IMPORTANT - Direction changes at 9+ mph'),
            ('avg_turn_exit', 'Turn Exit Speed (mph)', '🎯 Speed coming out of turns - Higher exit than entry = explosive power'),
            ('avg_turn_entry', 'Turn Entry Speed (mph)', '💨 Speed going into turns - Higher = attacking at speed'),
            ('right_turns', 'Right Turns', '➡️ Cuts to right (30-150°)'),
            ('left_turns', 'Left Turns', '⬅️ Cuts to left (30-150°)'),
            ('back_turns', 'Back Turns', '↩️ Direction reversals (150°+)'),
        ]

        cols = st.columns(3)
        for idx, (col_name, label, description) in enumerate(agility_metrics):
            with cols[idx % 3]:
                if col_name in df.columns:
                    values = pd.to_numeric(df[col_name], errors='coerce').dropna()
                    if len(values) > 0:
                        avg_val = values.mean()
                        best_val = values.max()

                        st.metric(label, f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                        st.caption(description)

# Tab 4: Ball Work
with tab4:
    st.header("⚽ Ball Work Analysis")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        df = st.session_state.df.copy()

        st.info("**What is Ball Work?**\n\nBall work measures technical skill development through foot touches, two-footed ability, and kicking power.")

        ball_metrics = [
            ('ball_touches', 'Total Ball Touches', '📊 Overall volume per session'),
            ('left_touches', 'Left Foot Touches', '⬅️ Weak foot development'),
            ('right_touches', 'Right Foot Touches', '➡️ Dominant foot'),
            ('left_kicking_power_mph', 'Left Foot Power (mph)', '💪 Weak foot striking'),
            ('right_kicking_power_mph', 'Right Foot Power (mph)', '💪 Dominant striking'),
        ]

        cols = st.columns(3)
        for idx, (col_name, label, description) in enumerate(ball_metrics):
            with cols[idx % 3]:
                if col_name in df.columns:
                    values = pd.to_numeric(df[col_name], errors='coerce').dropna()
                    if len(values) > 0:
                        avg_val = values.mean()
                        best_val = values.max()

                        st.metric(label, f"{avg_val:.1f}", delta=f"Best: {best_val:.1f}")
                        st.caption(description)

        # L/R Ratio
        if 'left_touches' in df.columns and 'right_touches' in df.columns:
            left = pd.to_numeric(df['left_touches'], errors='coerce')
            right = pd.to_numeric(df['right_touches'], errors='coerce')
            valid_mask = (left > 0) & (right > 0)

            if valid_mask.any():
                ratios = left[valid_mask] / right[valid_mask]
                avg_ratio = ratios.mean()
                best_ratio = ratios.max()

                st.metric("L/R Touch Ratio", f"{avg_ratio:.2f}", delta=f"Best: {best_ratio:.2f}")
                st.caption("⚖️ Target: ≥ 0.5 for balance")

# Tab 5: Personal Records
with tab5:
    st.header("🏆 Personal Records")

    if not st.session_state.personal_records:
        st.warning("📊 No personal records calculated. Please upload your Excel file in the sidebar.")
    else:
        records = [
            ("Top Speed", 'top_speed', "mph", "🚀"),
            ("Sprint Distance", 'sprint_distance', "yards", "🏃"),
            ("Ball Touches", 'ball_touches', "touches", "⚽"),
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

                st.metric(f"{emoji} {name}", f"{display_value} {unit}")

                if pr_date:
                    st.caption(f"📅 {pr_date.strftime('%b %d, %Y')}")

# Tab 6: AI Insights (basic version - can be enhanced)
with tab6:
    st.header("🤖 AI Insights")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
    else:
        df = st.session_state.df.copy()

        st.subheader("Training Summary")
        st.write(f"**Total Sessions:** {len(df)}")

        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            date_range = (df['date'].max() - df['date'].min()).days
            st.write(f"**Date Range:** {df['date'].min().strftime('%b %d, %Y')} to {df['date'].max().strftime('%b %d, %Y')} ({date_range} days)")

        st.subheader("Key Performance Indicators")

        # Agility Status
        if 'intense_turns' in df.columns:
            intense_vals = pd.to_numeric(df['intense_turns'], errors='coerce').dropna()
            if len(intense_vals) > 0:
                avg_intense = intense_vals.mean()
                st.write(f"**Intense Turns Average:** {avg_intense:.1f} per session")
                if avg_intense >= 10:
                    st.success("✅ Elite-level agility!")
                elif avg_intense >= 7:
                    st.info("💪 Strong agility development")
                elif avg_intense >= 5:
                    st.warning("⚠️ Solid foundation - push for 10+")
                else:
                    st.error("🎯 Focus area: Build to 10+ intense turns per session")

        # Speed Status
        if 'top_speed' in df.columns:
            speed_vals = pd.to_numeric(df['top_speed'], errors='coerce').dropna()
            if len(speed_vals) > 0:
                avg_speed = speed_vals.mean()
                max_speed = speed_vals.max()
                st.write(f"**Top Speed:** {max_speed:.1f} mph (avg: {avg_speed:.1f} mph)")

        # L/R Balance
        if 'left_touches' in df.columns and 'right_touches' in df.columns:
            left = pd.to_numeric(df['left_touches'], errors='coerce')
            right = pd.to_numeric(df['right_touches'], errors='coerce')
            valid_mask = (left > 0) & (right > 0)

            if valid_mask.any():
                ratios = left[valid_mask] / right[valid_mask]
                avg_ratio = ratios.mean()
                st.write(f"**L/R Touch Ratio:** {avg_ratio:.2f}")
                if avg_ratio >= 0.5:
                    st.success("✅ Excellent two-footed balance!")
                else:
                    gap = 0.5 - avg_ratio
                    st.warning(f"⚠️ Left foot needs {gap:.2f} more to reach 0.5 target")

if __name__ == "__main__":
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Mia Training Tracker v1.0**")
    st.sidebar.markdown("Built with Streamlit")
