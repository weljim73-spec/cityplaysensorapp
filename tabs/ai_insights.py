"""AI Insights tab for Mia Training Tracker."""

import streamlit as st

from shared import get_central_time, analyze_training_data


def render():
    """Render the AI Insights tab content."""
    st.header("🤖 AI Insights")

    if st.session_state.df is None or len(st.session_state.df) == 0:
        st.warning("📊 No data loaded. Please upload your Excel file in the sidebar.")
        return

    st.markdown("""
    Click the button below to generate a comprehensive training insights report analyzing:
    - Executive summary of current performance
    - 30-day trend analysis
    - Performance metrics and trends
    - Coach performance analysis
    - Agility and speed development
    - Technical skills assessment
    - Personalized action plan
    - Next milestone targets
    """)

    st.markdown("---")

    # Initialize session state for insights
    if 'ai_insights_generated' not in st.session_state:
        st.session_state.ai_insights_generated = False
        st.session_state.ai_insights_report = ""

    # Button to generate insights
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔍 Generate Comprehensive AI Insights", type="primary", use_container_width=True):
            with st.spinner("🤖 Analyzing training data and generating insights..."):
                df = st.session_state.df.copy()
                st.session_state.ai_insights_report = analyze_training_data(df)
                st.session_state.ai_insights_generated = True

    # Display the report if generated
    if st.session_state.ai_insights_generated and st.session_state.ai_insights_report:
        st.markdown("---")

        # Add a download button for the report
        st.download_button(
            label="📥 Download Report as Text File",
            data=st.session_state.ai_insights_report,
            file_name=f"mia_training_insights_{get_central_time().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain"
        )

        # Display the report with word wrap
        st.text_area(
            label="AI Insights Report",
            value=st.session_state.ai_insights_report,
            height=600,
            label_visibility="collapsed"
        )

        # Add option to clear/regenerate
        if st.button("🔄 Clear Report"):
            st.session_state.ai_insights_generated = False
            st.session_state.ai_insights_report = ""
            st.rerun()
