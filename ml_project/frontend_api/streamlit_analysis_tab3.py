import os
import sys
import time
import io
from io import BytesIO
import requests
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from datetime import datetime, timedelta
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url
from ml_project.backend_api.fastapi_analysis_helper import*
from ml_project.frontend_api.streamlit_analysis_helper import*
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.frontend_api.streamlit_cache_data import (
load_excel_data, get_financial_year_data,generate_complaint_report_fy,
generate_date_report_fy,generate_shift_duty_report_fy,generate_qrc_data_fy,
get_complaint_number_data_fy,get_section_data_fy, get_subdivision_data_fy,
get_division_data_fy, get_circle_data_fy, get_consumer_number_data_fy,
get_mobile_number_data_fy, get_dept_data_fy, get_status_data_fy,
get_complainant_name_data_fy, get_pscc_data_fy, get_minute_data_fy,

)



config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]

from ml_project.configs.config import DatasetNotFoundError, get_dataset_path

try:
    dataset_path = get_dataset_path("data/raw_path")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")
    
API_URL = "http://localhost:8000"
FASTAPI_URL = "http://localhost:8000"
FLASK_URL = "http://localhost:5000"

# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python version doesn't support reconfigure

logger = get_logger(__name__)


# ================================================================
# STREAMLIT APP FOR TAB 3
# ================================================================

def streamlit_analysis_tab3(tab3, dataset_path, logger):
    """
    Renders all content for Tab 3 including analysis and reports.
    
    Parameters:
    -----------
    tab3 : streamlit.tabs
        The Streamlit tab container where content will be rendered
    dataset_path : str
        Path to the dataset file
    logger : logging.Logger
        Logger instance for logging operations
    """
    try:
        with tab3:
            # ========================================
            # Initialize Session State
            # ========================================
            if 'filtered_df_tab3' not in st.session_state:
                st.session_state.filtered_df_tab3 = None
            if 'start_date_tab3' not in st.session_state:
                st.session_state.start_date_tab3 = None
            if 'end_date_tab3' not in st.session_state:
                st.session_state.end_date_tab3 = None
            
            # ========================================
            # SECTION 1: DATE RANGE ANALYSIS
            # ========================================
            st.header("📊 Custom Date Range Analysis")
            st.caption("Filter and analyze data by custom date range")
            df = load_excel_data(dataset_path)
            
            # Create a form for date selection
            with st.form("date_filter_form"):
                st.subheader("📅 Select Date Range")
                
                # Date Range Selection
                col_date1, col_date2 = st.columns(2)
                
                with col_date1:
                    start_date = st.date_input(
                        "Start Date",
                        value=pd.Timestamp('2024-04-01'),
                        help="Select the start date for analysis"
                    )
                
                with col_date2:
                    end_date = st.date_input(
                        "End Date",
                        value=pd.Timestamp('2025-03-31'),
                        help="Select the end date for analysis"
                    )
                
                # Submit button
                st.markdown("---")
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn2:
                    submit_button = st.form_submit_button(
                        "🔍 Generate Report",
                        use_container_width=True,
                        type="primary"
                    )
            
            # Process data when button is clicked
            if submit_button:
                # Validate date range
                if start_date > end_date:
                    st.error("❌ Start date must be before or equal to end date!")
                else:
                    with st.spinner("🔄 Filtering data and generating reports..."):
                        # Filter data based on date range
                        @st.cache_data(ttl=600, show_spinner=False)
                        def get_date_range_data(df, start, end):
                            """Filter data for selected date range"""
                            start_ts = pd.Timestamp(start)
                            end_ts = pd.Timestamp(end)
                            return df[(df['DATE'] >= start_ts) & (df['DATE'] <= end_ts)]
                        
                        # Get filtered data and store in session state
                        st.session_state.filtered_df_tab3 = get_date_range_data(df, start_date, end_date)
                        st.session_state.start_date_tab3 = start_date
                        st.session_state.end_date_tab3 = end_date
            
            # Display results if data exists in session state
            if st.session_state.filtered_df_tab3 is not None:
                filtered_df = st.session_state.filtered_df_tab3
                start_date = st.session_state.start_date_tab3
                end_date = st.session_state.end_date_tab3
                
                # Display summary metrics
                st.markdown("---")
                st.subheader(f"📈 Summary ({start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')})")
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric("Total Records", f"{len(filtered_df):,}")
                
                with metric_col2:
                    total_days = (end_date - start_date).days + 1
                    st.metric("Total Days", f"{total_days}")
                
                with metric_col3:
                    avg_per_day = len(filtered_df) / total_days if total_days > 0 else 0
                    st.metric("Avg Records/Day", f"{avg_per_day:.1f}")
                
                with metric_col4:
                    if len(filtered_df) > 0:
                        open_count = filtered_df['CLOSED/OPEN'].value_counts().get('OPEN', 0)
                        st.metric("Open Cases", f"{open_count:,}")
                    else:
                        st.metric("Open Cases", "0")
                
                if len(filtered_df) == 0:
                    st.warning("⚠️ No data found for the selected date range.")
                else:
                    st.markdown("---")
                    st.subheader("📋 Detailed Reports")
                    
                    # ========================================
                    # ROW 1: Complaint Type & Date Analysis
                    # ========================================
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🎯 Complaint Type Distribution")
                        complaint_data = generate_complaint_report_fy(filtered_df)
                        st.dataframe(
                            complaint_data,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        st.markdown("#### 📅 Date-wise Distribution")
                        date_data = generate_date_report_fy(filtered_df)
                        st.dataframe(
                            date_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    # ========================================
                    # ROW 2: Shift Duty & QRC Type
                    # ========================================
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### ⏰ Shift Duty Analysis")
                        shift_data = generate_shift_duty_report_fy(filtered_df)
                        st.dataframe(
                            shift_data,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        st.markdown("#### 📝 Query/Request/Complaint Type")
                        qrc_data = generate_qrc_data_fy(filtered_df)
                        st.dataframe(
                            qrc_data,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    # ========================================
                    # ROW 3: Section & Sub-Division
                    # ========================================
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🏢 Section-wise Distribution")
                        section_data = get_section_data_fy(filtered_df)
                        st.dataframe(
                            section_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    with col2:
                        st.markdown("#### 🏘️ Sub-Division Distribution")
                        subdivision_data = get_subdivision_data_fy(filtered_df)
                        st.dataframe(
                            subdivision_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    # ========================================
                    # ROW 4: Division & Circle
                    # ========================================
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🏛️ Division-wise Distribution")
                        division_data = get_division_data_fy(filtered_df)
                        st.dataframe(
                            division_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    with col2:
                        st.markdown("#### ⭕ Circle-wise Distribution")
                        circle_data = get_circle_data_fy(filtered_df)
                        st.dataframe(
                            circle_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    # ========================================
                    # ROW 5: Consumer Number & Mobile Number
                    # ========================================
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🔢 Consumer Number Frequency")
                        consumer_data = get_consumer_number_data_fy(filtered_df)
                        st.dataframe(
                            consumer_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    with col2:
                        st.markdown("#### 📱 Mobile Number Frequency")
                        mobile_data = get_mobile_number_data_fy(filtered_df)
                        st.dataframe(
                            mobile_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    # ========================================
                    # ROW 6: Department & Status
                    # ========================================
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🏢 Department Distribution")
                        dept_data = get_dept_data_fy(filtered_df)
                        st.dataframe(
                            dept_data,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        st.markdown("#### ✅ Status Distribution (Open/Closed)")
                        status_data = get_status_data_fy(filtered_df)
                        st.dataframe(
                            status_data,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    # ========================================
                    # ROW 7: Complaint Number & Complainant Name
                    # ========================================
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 🎫 Complaint Number Frequency")
                        complaint_num_data = get_complaint_number_data_fy(filtered_df)
                        st.dataframe(
                            complaint_num_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    with col2:
                        st.markdown("#### 👤 Complainant Name Frequency")
                        complainant_data = get_complainant_name_data_fy(filtered_df)
                        st.dataframe(
                            complainant_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    # ========================================
                    # ROW 8: PSCC/FG/TO & Minute
                    # ========================================
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### 📊 PSCC/FG/TO Distribution")
                        pscc_data = get_pscc_data_fy(filtered_df)
                        st.dataframe(
                            pscc_data,
                            use_container_width=True,
                            hide_index=True
                        )
                    
                    with col2:
                        st.markdown("#### ⏱️ Minute Distribution")
                        minute_data = get_minute_data_fy(filtered_df)
                        st.dataframe(
                            minute_data,
                            use_container_width=True,
                            hide_index=True,
                            height=400
                        )
                    
                    # ========================================
                    # DOWNLOAD SECTION
                    # ========================================
                    st.markdown("---")
                    st.subheader("💾 Download Filtered Data")
                    
                    # Create download button for filtered data
                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label=f"📥 Download Data ({len(filtered_df)} records)",
                        data=csv,
                        file_name=f"filtered_data_{start_date}_{end_date}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
            else:
                # Show instruction when no data in session state
                st.info("👆 Please select date range above and click '🔍 Generate Report' to view the analysis.")

    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Unhandled error in Streamlit dashboard Tab 3 | error={error_msg}")
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)