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
from ml_project.frontend_api.streamlit_cache_data import fetch_generate_month_wise_open_close_pivot_report,fetch_generate_quarter_wise_agging_pivot_report,fetch_generate_year_wise_open_close_pivot_report
from ml_project.frontend_api.streamlit_analysis_helper import (
generate_month_wise_open_clode_pivot_report,
generate_complaint_report,
generate_date_report,
generate_shift_duty_report,

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


# ========================================
# MAIN TAB2 FUNCTION
# ========================================

def streamlit_analysis_tab2(tab2, dataset_path, logger):
    """
    Renders all content for Tab 2 including analysis and reports.
    
    Parameters:
    -----------
    tab2 : streamlit.tabs
        The Streamlit tab container where content will be rendered
    dataset_path : str
        Path to the dataset file
    logger : logging.Logger
        Logger instance for logging operations
    """
    try:
        with tab2:
            # ========================================
            # SECTION 1: MONTH WISE OPEN/CLOSE COMPLAINTS PIVOT
            # ========================================
            st.header("📊 Month Wise Open/Close Complaints Report")
            st.caption("Select year and month to view complaints report")

            # Initialize session state for selected year and month
            if "selected_year_tab2" not in st.session_state:
                st.session_state.selected_year_tab2 = datetime.today().year
            
            if "selected_month_tab2" not in st.session_state:
                st.session_state.selected_month_tab2 = datetime.today().month
            
            # Initialize flag to track if report should be generated
            if "generate_report_tab2" not in st.session_state:
                st.session_state.generate_report_tab2 = False

            # Create columns for Year and Month selection
            col1, col2, col3 = st.columns([1, 1, 1])
                        
            with col1:
                # Month selector
                months = {
                    1: "January", 2: "February", 3: "March", 4: "April",
                    5: "May", 6: "June", 7: "July", 8: "August",
                    9: "September", 10: "October", 11: "November", 12: "December"
                }
                selected_month_num = st.selectbox(
                    "Select Month",
                    options=list(months.keys()),
                    format_func=lambda x: months[x],
                    index=st.session_state.selected_month_tab2 - 1,
                    key="month_selector_tab2",
                    help="Choose the month"
                )

            with col2:
                # Year selector
                current_year = datetime.today().year
                selected_year = st.selectbox(
                    "Select Year",
                    options=list(range(current_year - 5, current_year + 1)),
                    index=list(range(current_year - 5, current_year + 1)).index(
                        st.session_state.selected_year_tab2
                    ),
                    key="year_selector_tab2",
                    help="Choose the year"
                )

            
            with col3:
                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button(
                    "📊 Generate Report",
                    type="primary",
                    use_container_width=True,
                    key="generate_report_button_tab2"
                ):
                    # Update session state when button is clicked
                    st.session_state.selected_year_tab2 = selected_year
                    st.session_state.selected_month_tab2 = selected_month_num
                    st.session_state.generate_report_tab2 = True

            # Convert to string format 'YYYY-MM'
            month_str = f"{st.session_state.selected_year_tab2}-{st.session_state.selected_month_tab2:02d}"
            
            # Display selected month
            st.info(
                f"📅 Selected Period: **{months[st.session_state.selected_month_tab2]} "
                f"{st.session_state.selected_year_tab2}** (Format: {month_str})"
            )

            # Only generate report if button was clicked
            if st.session_state.generate_report_tab2:
                with st.spinner("Loading data..."):
                    df, error, status_code = fetch_generate_month_wise_open_close_pivot_report(month_str)
                
                if error is None and df is not None:
                    st.success("✅ Report generated successfully!")
                    st.dataframe(df, use_container_width=True, height=400)
                    logger.info(f"Tab 2: Month wise report generated successfully | month={month_str}")
                    
                    # Store last generated time
                    st.session_state.last_report_time_tab2 = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Reset flag after successful generation
                    st.session_state.generate_report_tab2 = False
                    
                else:
                    if status_code:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                        logger.error(f"Tab 2: API request failed | status_code={status_code}")
                    else:
                        st.error(f"❌ Error: {error}")
                        logger.error(f"Tab 2: Error - {error}")
                    
                    # Reset flag after error
                    st.session_state.generate_report_tab2 = False

            # Show last loaded timestamp
            if "last_report_time_tab2" in st.session_state:
                st.caption(f"Last loaded: {st.session_state.last_report_time_tab2}")
            else:
                st.caption("Last loaded: Not generated yet")

            st.divider()
            # ========================================
            # SECTION 1: YEAR TO DATE RANGE SELECTION
            # ========================================
            st.header("📊 Year to Date Analysis Report")
            st.caption("Select start year and end year to view analysis")

            # Initialize session state for selected years
            if "start_year_tab2" not in st.session_state:
                st.session_state.start_year_tab2 = datetime.today().year
            
            if "end_year_tab2" not in st.session_state:
                st.session_state.end_year_tab2 = datetime.today().year
            
            # Initialize flag to track if report should be generated
            if "generate_report_tab2" not in st.session_state:
                st.session_state.generate_report_tab2 = False

            # Create columns for Year selection
            col1, col2, col3 = st.columns([1, 1, 1])
                        
            with col1:
                # Start Year selector
                current_year = datetime.today().year
                start_year = st.selectbox(
                    "Start Year",
                    options=list(range(current_year - 10, current_year + 1)),
                    index=list(range(current_year - 10, current_year + 1)).index(
                        st.session_state.start_year_tab2
                    ),
                    key="start_year_selector_tab2",
                    help="Choose the starting year"
                )

            with col2:
                # End Year selector
                end_year = st.selectbox(
                    "End Year",
                    options=list(range(current_year - 10, current_year + 1)),
                    index=list(range(current_year - 10, current_year + 1)).index(
                        st.session_state.end_year_tab2
                    ),
                    key="end_year_selector_tab2",
                    help="Choose the ending year"
                )

            with col3:
                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button(
                    "📊 Generate Report",
                    type="primary",
                    use_container_width=True,
                    key="generate_report_button"
                ):
                    # Validate year range
                    if start_year > end_year:
                        st.error("❌ Start year cannot be greater than end year!")
                    else:
                        # Update session state when button is clicked
                        st.session_state.start_year_tab2 = start_year
                        st.session_state.end_year_tab2 = end_year
                        st.session_state.generate_report_tab2 = True

            # Display selected range
            year_range = f"{st.session_state.start_year_tab2} to {st.session_state.end_year_tab2}"
            st.info(
                f"📅 Selected Period: **{year_range}** | "
                f"Duration: **{st.session_state.end_year_tab2 - st.session_state.start_year_tab2 + 1} year(s)**"
            )

            # Only generate report if button was clicked
            if st.session_state.generate_report_tab2:
                with st.spinner("Loading data..."):
                    # Call your function with start_year and end_year
                    df, error, status_code = fetch_generate_year_wise_open_close_pivot_report(
                        st.session_state.start_year_tab2,
                        st.session_state.end_year_tab2
                    )
                
                if error is None and df is not None:
                    st.success("✅ Report generated successfully!")
                    
                    # Display metrics if you want
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Total Records", len(df))
                    with col_m2:
                        st.metric("Years Covered", st.session_state.end_year_tab2 - st.session_state.start_year_tab2 + 1)
                    with col_m3:
                        st.metric("Columns", len(df.columns))
                    
                    # Display dataframe
                    st.dataframe(df, use_container_width=True, height=400)
                    logger.info(f"Tab 2: Year-to-date report generated | range={year_range}")
                    
                    # Store last generated time
                    st.session_state.last_report_time_tab2 = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Reset flag after successful generation
                    st.session_state.generate_report_tab2 = False
                    
                else:
                    if status_code:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                        logger.error(f"Tab 2: API request failed | status_code={status_code}")
                    else:
                        st.error(f"❌ Error: {error}")
                        logger.error(f"Tab 2: Error - {error}")
                    
                    # Reset flag after error
                    st.session_state.generate_report_tab2 = False

            # Show last loaded timestamp
            if "last_report_time_tab2" in st.session_state:
                st.caption(f"Last loaded: {st.session_state.last_report_time_tab2}")
            else:
                st.caption("Last loaded: Not generated yet")
                

            st.divider()
            # ========================================
            # SECTION 1: YEAR AND QUARTER SELECTION
            # ========================================
            st.header("📊 Year and Quarter Analysis Report")
            st.caption("Select start year/quarter and end year/quarter to view analysis")

            # Initialize session state for selected years and quarters
            if "start_year_tab2" not in st.session_state:
                st.session_state.start_year_tab2 = datetime.today().year
            
            if "end_year_tab2" not in st.session_state:
                st.session_state.end_year_tab2 = datetime.today().year
            
            if "start_quarter_tab2" not in st.session_state:
                st.session_state.start_quarter_tab2 = 1
            
            if "end_quarter_tab2" not in st.session_state:
                st.session_state.end_quarter_tab2 = 4
            
            # Initialize flag to track if report should be generated
            if "generate_report_tab2" not in st.session_state:
                st.session_state.generate_report_tab2 = False

            # Quarter mapping
            quarters = {
                1: "Q1 (Jan-Mar)",
                2: "Q2 (Apr-Jun)",
                3: "Q3 (Jul-Sep)",
                4: "Q4 (Oct-Dec)"
            }

            # Create columns for Start and End selection
            st.subheader("Start Period")
            col1, col2 = st.columns([1, 1])
                        
            with col1:
                # Start Year selector
                current_year = datetime.today().year
                start_year = st.selectbox(
                    "Start Year",
                    options=list(range(current_year - 10, current_year + 1)),
                    index=list(range(current_year - 10, current_year + 1)).index(
                        st.session_state.start_year_tab2
                    ),
                    key="start_year_selector",
                    help="Choose the starting year"
                )

            with col2:
                # Start Quarter selector
                start_quarter = st.selectbox(
                    "Start Quarter",
                    options=list(quarters.keys()),
                    format_func=lambda x: quarters[x],
                    index=st.session_state.start_quarter_tab2 - 1,
                    key="start_quarter_selector_tab2",
                    help="Choose the starting quarter"
                )

            st.subheader("End Period")
            col3, col4 = st.columns([1, 1])

            with col3:
                # End Year selector
                end_year = st.selectbox(
                    "End Year",
                    options=list(range(current_year - 10, current_year + 1)),
                    index=list(range(current_year - 10, current_year + 1)).index(
                        st.session_state.end_year_tab2
                    ),
                    key="end_year_selector",
                    help="Choose the ending year"
                )

            with col4:
                # End Quarter selector
                end_quarter = st.selectbox(
                    "End Quarter",
                    options=list(quarters.keys()),
                    format_func=lambda x: quarters[x],
                    index=st.session_state.end_quarter_tab2 - 1,
                    key="end_quarter_selector",
                    help="Choose the ending quarter"
                )

            # Generate Report Button
            col_button = st.columns([1, 1, 1])
            with col_button[1]:
                if st.button(
                    "📊 Generate Report",
                    type="primary",
                    use_container_width=True,
                    key="generate_report_button_t"
                ):
                    # Validate quarter range
                    start_period = start_year * 10 + start_quarter
                    end_period = end_year * 10 + end_quarter
                    
                    if start_period > end_period:
                        st.error("❌ Start period cannot be greater than end period!")
                    else:
                        # Update session state when button is clicked
                        st.session_state.start_year_tab2 = start_year
                        st.session_state.end_year_tab2 = end_year
                        st.session_state.start_quarter_tab2 = start_quarter
                        st.session_state.end_quarter_tab2 = end_quarter
                        st.session_state.generate_report_tab2 = True

            # Display selected range
            period_range = (
                f"{quarters[st.session_state.start_quarter_tab2]} {st.session_state.start_year_tab2} "
                f"to {quarters[st.session_state.end_quarter_tab2]} {st.session_state.end_year_tab2}"
            )
            
            # Calculate total quarters
            total_quarters = (
                (st.session_state.end_year_tab2 - st.session_state.start_year_tab2) * 4 + 
                (st.session_state.end_quarter_tab2 - st.session_state.start_quarter_tab2 + 1)
            )
            
            st.info(
                f"📅 Selected Period: **{period_range}** | "
                f"Duration: **{total_quarters} quarter(s)**"
            )

            # Only generate report if button was clicked
            if st.session_state.generate_report_tab2:
                with st.spinner("Loading data..."):
                    # Call your function with start/end year and quarter
                    df, error, status_code = fetch_generate_quarter_wise_agging_pivot_report(
                        st.session_state.start_year_tab2,
                        st.session_state.start_quarter_tab2,
                        st.session_state.end_year_tab2,
                        st.session_state.end_quarter_tab2
                    )
                
                if error is None and df is not None:
                    st.success("✅ Report generated successfully!")
                    
                    # Display metrics
                    col_m1, col_m2, col_m3 = st.columns(3)
                    with col_m1:
                        st.metric("Total Records", len(df))
                    with col_m2:
                        st.metric("Quarters Covered", total_quarters)
                    with col_m3:
                        st.metric("Columns", len(df.columns))
                    
                    # Display dataframe
                    st.dataframe(df, use_container_width=True, height=400)
                    logger.info(
                        f"Tab 2: Quarterly report generated | "
                        f"start={st.session_state.start_quarter_tab2}-{st.session_state.start_year_tab2} | "
                        f"end={st.session_state.end_quarter_tab2}-{st.session_state.end_year_tab2}"
                    )
                    
                    # Store last generated time
                    st.session_state.last_report_time_tab2 = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Reset flag after successful generation
                    st.session_state.generate_report_tab2 = False
                    
                else:
                    if status_code:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                        logger.error(f"Tab 2: API request failed | status_code={status_code}")
                    else:
                        st.error(f"❌ Error: {error}")
                        logger.error(f"Tab 2: Error - {error}")
                    
                    # Reset flag after error
                    st.session_state.generate_report_tab2 = False

            # Show last loaded timestamp
            if "last_report_time_tab2" in st.session_state:
                st.caption(f"Last loaded: {st.session_state.last_report_time_tab2}")
            else:
                st.caption("Last loaded: Not generated yet")





            # ===============================
            # SECTION 2: MONTH WISE OPEN/CLOSE COMPLAINTS PIVOT
            # ===============================

            st.divider()

            # Initialize session state
            if 'report_generated' not in st.session_state:
                st.session_state.report_generated = False
            if 'selected_month' not in st.session_state:
                st.session_state.selected_month = None
            if 'dataset_path' not in st.session_state:
                st.session_state.dataset_path = None

            # Load and cache the Excel data ONCE
            @st.cache_data(ttl=600, show_spinner=True)
            def load_excel_data(file_path):
                """Load and cache Excel data"""
                df = pd.read_excel(file_path)
                df['DATE'] = pd.to_datetime(df['DATE'])
                return df

            # Filter monthly data (cached)
            @st.cache_data(ttl=600)
            def get_month_data(df, selected_month):
                """Filter data for selected month"""
                return df[df['DATE'].dt.to_period('M') == selected_month]

            # Enhanced report functions
            @st.cache_data(ttl=600)
            def generate_complaint_report(month_df):
                result = month_df['COMPLAINT TYPE'].value_counts().reset_index()
                result.columns = ['Complaint Type', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def generate_date_report(month_df):
                result = month_df['DATE'].value_counts().sort_index().reset_index()
                result.columns = ['Date', 'Count']
                result['Day of Week'] = pd.to_datetime(result['Date']).dt.day_name()
                return result

            @st.cache_data(ttl=600)
            def generate_shift_duty_report(month_df):
                result = month_df['SHIFT DUTY'].value_counts().reset_index()
                result.columns = ['Shift Duty', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def generate_monthly_qrc_data(month_df):
                result = month_df['QUERY/REQUEST/COMPLAINT'].value_counts().reset_index()
                result.columns = ['QRC Type', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_section_data(month_df):
                result = month_df['SECTION'].value_counts().reset_index()
                result.columns = ['Section', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_subdivision_data(month_df):
                result = month_df['SUB-DIVISION'].value_counts().reset_index()
                result.columns = ['Sub-Division', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_circle_data(month_df):
                result = month_df['CIRCLE'].value_counts().reset_index()
                result.columns = ['Circle', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_consumer_number_data(month_df):
                result = month_df['CONSUMER NUMBER'].value_counts().reset_index()
                result.columns = ['Consumer Number', 'Count']
                return result

            @st.cache_data(ttl=600)
            def get_monthly_mobile_number_data(month_df):
                result = month_df['MOBILE NUMB'].value_counts().reset_index()
                result.columns = ['Mobile Number', 'Count']
                return result

            @st.cache_data(ttl=600)
            def get_monthly_dept_data(month_df):
                result = month_df['DEPT'].value_counts().reset_index()
                result.columns = ['Department', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_status_data(month_df):
                result = month_df['CLOSED/OPEN'].value_counts().reset_index()
                result.columns = ['Status', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_pscc_data(month_df):
                result = month_df['PSCC/FG/TO'].value_counts().reset_index()
                result.columns = ['PSCC Type', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_minute_data(month_df):
                result = month_df['MINUTE'].value_counts().reset_index()
                result.columns = ['Minute', 'Count']
                return result

            @st.cache_data(ttl=600)
            def get_monthly_remarks_analysis(month_df):
                """Analyze REMARKS column for patterns"""
                temp_df = month_df.copy()
                
                if 'REMARKS' not in temp_df.columns:
                    return {
                        'Appreciation Tweets': 0,
                        'Awaited Consumer': 0,
                        '5-digit Numbers': 0,
                        'Total Remarks': 0
                    }
                
                temp_df['REMARKS'] = temp_df['REMARKS'].fillna('').astype(str)
                
                appreciation_count = temp_df['REMARKS'].str.contains("Appreciation Tweet", case=False, na=False).sum()
                awaited_consumer_count = temp_df['REMARKS'].str.contains("Awaited consumer", case=False, na=False).sum()
                number_count = temp_df['REMARKS'].str.contains(r"\b\d{5}\b", na=False).sum()

                return {
                    'Appreciation Tweets': int(appreciation_count),
                    'Awaited Consumer': int(awaited_consumer_count),
                    '5-digit Numbers': int(number_count),
                    'Total Remarks': len(temp_df)
                }

            @st.cache_data(ttl=600)
            def get_performance_metrics(month_df):
                """Calculate advanced performance metrics"""
                metrics = {}
                
                # Average resolution time
                if 'MINUTE' in month_df.columns:
                    metrics['avg_resolution_time'] = month_df['MINUTE'].mean()
                    metrics['median_resolution_time'] = month_df['MINUTE'].median()
                    metrics['max_resolution_time'] = month_df['MINUTE'].max()
                    metrics['min_resolution_time'] = month_df['MINUTE'].min()
                
                # Daily averages
                metrics['avg_daily_complaints'] = len(month_df) / month_df['DATE'].nunique()
                
                # Peak hours analysis
                if 'SHIFT DUTY' in month_df.columns:
                    peak_shift = month_df['SHIFT DUTY'].value_counts().idxmax()
                    metrics['peak_shift'] = peak_shift
                
                return metrics

            @st.cache_data(ttl=600)
            def get_trend_analysis(month_df):
                """Analyze trends over the month"""
                daily_counts = month_df.groupby(month_df['DATE'].dt.date).size().reset_index()
                daily_counts.columns = ['Date', 'Count']
                
                # Calculate trend
                if len(daily_counts) > 1:
                    daily_counts['Trend'] = daily_counts['Count'].diff()
                    daily_counts['7-Day Moving Avg'] = daily_counts['Count'].rolling(window=7, min_periods=1).mean()
                
                return daily_counts


            # Main App
            st.markdown("# 📊 Month Wise Complaint Analysis Dashboard")
            st.markdown("### Comprehensive Analytics & Insights Platform")

            if dataset_path is not None:
                if "dataset_path" not in st.session_state or st.session_state.dataset_path != dataset_path:
                    st.session_state.dataset_path = dataset_path
                    st.session_state.report_generated = False
                
                try:
                    df = load_excel_data(dataset_path)
                    
                    # Enhanced month and year selectors
                    st.markdown("## 📅 Select Analysis Period")
                    col_month, col_year, col_space = st.columns([1, 1, 2])
                    with col_month:
                        month = st.selectbox(
                            "Month", 
                            list(range(1, 13)), 
                            format_func=lambda x: pd.to_datetime(str(x), format="%m").strftime("%B"),
                            key='tab2_month_selector'
                        )
                    with col_year:
                        year = st.selectbox(
                            "Year", 
                            list(range(2020, 2031)),
                            key='tab2_year_selector'
                        )

                    selected_month = pd.Period(f"{year}-{month:02d}", freq='M')
                    
                    if st.session_state.selected_month != str(selected_month):
                        st.session_state.selected_month = str(selected_month)
                        st.session_state.report_generated = False

                    st.markdown("---")
                    generate_button = st.button("🔍 Generate Comprehensive Report", type="primary", use_container_width=True, key='tab2_generate_btn')

                    if generate_button or st.session_state.report_generated:
                        if generate_button:
                            st.session_state.report_generated = True
                        
                        try:
                            with st.spinner("🔄 Generating comprehensive analytics..."):
                                month_df = get_month_data(df, selected_month)

                                if len(month_df) == 0:
                                    st.warning(f"⚠️ No data found for {selected_month.strftime('%B %Y')}")
                                else:
                                    # Generate all reports
                                    complaint_report = generate_complaint_report(month_df)
                                    date_report = generate_date_report(month_df)
                                    shift_report = generate_shift_duty_report(month_df)
                                    qrc_report = generate_monthly_qrc_data(month_df)
                                    section_report = get_monthly_section_data(month_df)
                                    subdivision_report = get_monthly_subdivision_data(month_df)
                                    circle_report = get_monthly_circle_data(month_df)
                                    consumer_number_report = get_monthly_consumer_number_data(month_df)
                                    mobile_number_report = get_monthly_mobile_number_data(month_df)
                                    dept_report = get_monthly_dept_data(month_df)
                                    status_report = get_monthly_status_data(month_df)
                                    pscc_report = get_monthly_pscc_data(month_df)
                                    minute_report = get_monthly_minute_data(month_df)
                                    remarks_report = get_monthly_remarks_analysis(month_df)
                                    performance_metrics = get_performance_metrics(month_df)
                                    trend_data = get_trend_analysis(month_df)

                                    # Enhanced Summary Metrics Section
                                    st.markdown("## 📊 Executive Summary")
                                    st.markdown(f"### Analysis for **{selected_month.strftime('%B %Y')}**")
                                    
                                    metric_cols = st.columns(6)
                                    
                                    with metric_cols[0]:
                                        st.metric("📋 Total Records", f"{len(month_df):,}", help="Total number of complaints/queries received")
                                    with metric_cols[1]:
                                        st.metric("📂 Complaint Types", month_df['COMPLAINT TYPE'].nunique(), help="Unique types of complaints")
                                    with metric_cols[2]:
                                        st.metric("📅 Active Days", month_df['DATE'].nunique(), help="Days with recorded complaints")
                                    with metric_cols[3]:
                                        closed_count = status_report[status_report['Status'] == 'CLOSED']['Count'].sum() if len(status_report) > 0 else 0
                                        total_count = status_report['Count'].sum() if len(status_report) > 0 else 1
                                        closure_rate = (closed_count / total_count * 100) if total_count > 0 else 0
                                        st.metric("✅ Closure Rate", f"{closure_rate:.1f}%", help="Percentage of closed cases")
                                    with metric_cols[4]:
                                        avg_daily = performance_metrics.get('avg_daily_complaints', 0)
                                        st.metric("📈 Daily Average", f"{avg_daily:.1f}", help="Average complaints per day")
                                    with metric_cols[5]:
                                        if 'avg_resolution_time' in performance_metrics:
                                            st.metric("⏱️ Avg Resolution", f"{performance_metrics['avg_resolution_time']:.0f} min", help="Average time to resolve")
                                        else:
                                            st.metric("⏱️ Avg Resolution", "N/A")

                                    st.markdown("---")
                                    
                                    # Create enhanced tabs
                                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                                        "📊 Overview & Analysis", 
                                        "🔍 Detailed Reports", 
                                        "📈 Data Visualizations", 
                                        "🎯 Remarks & Insights",
                                        "📉 Trends & Performance",
                                        "🔎 Advanced Filters"
                                    ])
                                    
                                    # Tab 1: Overview & Analysis
                                    with tab1:
                                        st.markdown("### 🎯 Key Metrics Overview")
                                        
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("#### 📋 Complaint Type Distribution")
                                            st.dataframe(
                                                complaint_report.style.background_gradient(subset=['Count'], cmap='Blues'),
                                                use_container_width=True, 
                                                height=400
                                            )
                                            
                                            fig = px.pie(
                                                complaint_report, 
                                                values='Count', 
                                                names='Complaint Type',
                                                title="Complaint Type Breakdown",
                                                hole=0.4,
                                                color_discrete_sequence=px.colors.qualitative.Set3
                                            )
                                            fig.update_traces(textposition='inside', textinfo='percent+label')
                                            fig.update_layout(height=500)
                                            st.plotly_chart(fig, use_container_width=True, key='complaint_pie_main')
                                        
                                        with col2:
                                            st.markdown("#### 🔄 Status Overview")
                                            st.dataframe(
                                                status_report.style.background_gradient(subset=['Count'], cmap='RdYlGn'),
                                                use_container_width=True,
                                                height=400
                                            )
                                            
                                            fig = px.pie(
                                                status_report, 
                                                values='Count', 
                                                names='Status',
                                                title="Case Status Distribution",
                                                color='Status',
                                                color_discrete_map={'CLOSED': '#00CC96', 'OPEN': '#EF553B'},
                                                hole=0.4
                                            )
                                            fig.update_traces(textposition='inside', textinfo='percent+label')
                                            fig.update_layout(height=500)
                                            st.plotly_chart(fig, use_container_width=True, key='status_pie_main')
                                        
                                        st.markdown("---")
                                        
                                        col3, col4 = st.columns(2)
                                        
                                        with col3:
                                            st.markdown("#### ⏰ Shift Distribution")
                                            st.dataframe(
                                                shift_report.style.background_gradient(subset=['Count'], cmap='Greens'),
                                                use_container_width=True,
                                                height=350
                                            )
                                            
                                            fig = px.bar(
                                                shift_report, 
                                                x='Shift Duty', 
                                                y='Count',
                                                title="Complaints by Shift",
                                                color='Count',
                                                color_continuous_scale='Viridis',
                                                text='Count'
                                            )
                                            fig.update_traces(texttemplate='%{text}', textposition='outside')
                                            fig.update_layout(height=450)
                                            st.plotly_chart(fig, use_container_width=True, key='shift_bar_main')
                                        
                                        with col4:
                                            st.markdown("#### 📝 QRC Analysis")
                                            st.dataframe(
                                                qrc_report.style.background_gradient(subset=['Count'], cmap='Purples'),
                                                use_container_width=True,
                                                height=350
                                            )
                                            
                                            fig = px.bar(
                                                qrc_report, 
                                                x='QRC Type', 
                                                y='Count',
                                                title="Query/Request/Complaint Distribution",
                                                color='Count',
                                                color_continuous_scale='Plasma',
                                                text='Count'
                                            )
                                            fig.update_traces(texttemplate='%{text}', textposition='outside')
                                            fig.update_layout(height=450)
                                            st.plotly_chart(fig, use_container_width=True, key='qrc_bar_main')

                                            st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                    
                                    # Tab 2: Detailed Reports
                                    with tab2:
                                        st.markdown("### 📑 Comprehensive Data Reports")
                                        
                                        report_selector = st.selectbox(
                                            "Select Report Category:",
                                            ["Geographic Analysis", "Department & Section", "Contact Information", "Time Analysis"],
                                            key='report_selector_tab2'
                                        )
                                        
                                        if report_selector == "Geographic Analysis":
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.markdown("#### 🏘️ Sub-Division Analysis")
                                                st.dataframe(
                                                    subdivision_report.style.background_gradient(subset=['Count'], cmap='YlOrRd'),
                                                    use_container_width=True,
                                                    height=450
                                                )
                                                
                                                fig = px.treemap(
                                                    subdivision_report.head(15),
                                                    path=['Sub-Division'],
                                                    values='Count',
                                                    title="Top 15 Sub-Divisions (Treemap)",
                                                    color='Count',
                                                    color_continuous_scale='RdYlGn'
                                                )
                                                fig.update_layout(height=500)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with col2:
                                                st.markdown("#### 🔵 Circle Analysis")
                                                st.dataframe(
                                                    circle_report.style.background_gradient(subset=['Count'], cmap='Blues'),
                                                    use_container_width=True,
                                                    height=450
                                                )
                                                
                                                fig = px.bar(
                                                    circle_report.head(15),
                                                    y='Circle',
                                                    x='Count',
                                                    orientation='h',
                                                    title="Top 15 Circles",
                                                    color='Count',
                                                    color_continuous_scale='Teal',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=500)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            st.markdown("#### 🏢 Section Analysis")
                                            st.dataframe(
                                                section_report.style.background_gradient(subset=['Count'], cmap='Oranges'),
                                                use_container_width=True,
                                                height=400
                                            )
                                        
                                        elif report_selector == "Department & Section":
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.markdown("#### 🏛️ Department Distribution")
                                                st.dataframe(
                                                    dept_report.style.background_gradient(subset=['Count'], cmap='Purples'),
                                                    use_container_width=True,
                                                    height=500
                                                )
                                                
                                                fig = px.sunburst(
                                                    dept_report.head(10),
                                                    path=['Department'],
                                                    values='Count',
                                                    title="Department Hierarchy"
                                                )
                                                fig.update_layout(height=600)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with col2:
                                                st.markdown("#### 📞 PSCC/FG/TO Analysis")
                                                st.dataframe(
                                                    pscc_report.style.background_gradient(subset=['Count'], cmap='Greens'),
                                                    use_container_width=True,
                                                    height=500
                                                )
                                                
                                                fig = px.pie(
                                                    pscc_report,
                                                    values='Count',
                                                    names='PSCC Type',
                                                    title="PSCC Type Distribution",
                                                    hole=0.3
                                                )
                                                fig.update_layout(height=600)
                                                st.plotly_chart(fig, use_container_width=True)
                                        
                                        elif report_selector == "Contact Information":
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.markdown("#### 👤 Top Consumer Numbers")
                                                st.dataframe(
                                                    consumer_number_report.head(25).style.background_gradient(subset=['Count'], cmap='YlGnBu'),
                                                    use_container_width=True,
                                                    height=600
                                                )
                                            
                                            with col2:
                                                st.markdown("#### 📱 Top Mobile Numbers")
                                                st.dataframe(
                                                    mobile_number_report.head(25).style.background_gradient(subset=['Count'], cmap='YlOrBr'),
                                                    use_container_width=True,
                                                    height=600
                                                )
                                        
                                        else:  # Time Analysis
                                            st.markdown("#### ⏱️ Resolution Time Analysis")
                                            st.dataframe(
                                                minute_report.head(30).style.background_gradient(subset=['Count'], cmap='RdYlGn_r'),
                                                use_container_width=True,
                                                height=450
                                            )
                                            
                                            fig = px.histogram(
                                                month_df,
                                                x='MINUTE',
                                                nbins=50,
                                                title="Distribution of Resolution Times",
                                                labels={'MINUTE': 'Minutes', 'count': 'Frequency'},
                                                color_discrete_sequence=['#636EFA']
                                            )
                                            fig.update_layout(height=500)
                                            st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Tab 3: Data Visualizations
                                    with tab3:
                                        st.markdown("### 📊 Interactive Data Visualizations")
                                        
                                        viz_category = st.radio(
                                            "Select Visualization Category:",
                                            ["Primary Metrics", "Geographic Insights", "Time-based Analysis", "Comparative Views"],
                                            horizontal=True,
                                            key='viz_category_tab3'
                                        )
                                        
                                        if viz_category == "Primary Metrics":
                                            st.markdown("#### 📋 Complaint Analysis")
                                            
                                            chart_type = st.radio(
                                                "Visualization Type:",
                                                ["Horizontal Bar", "Vertical Bar", "Donut Chart", "Treemap"],
                                                horizontal=True,
                                                key='primary_chart_type'
                                            )
                                            
                                            if chart_type == "Horizontal Bar":
                                                fig = px.bar(
                                                    complaint_report,
                                                    y='Complaint Type',
                                                    x='Count',
                                                    orientation='h',
                                                    title="Complaint Type Distribution (Horizontal)",
                                                    color='Count',
                                                    color_continuous_scale='Viridis',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=600)
                                            elif chart_type == "Vertical Bar":
                                                fig = px.bar(
                                                    complaint_report,
                                                    x='Complaint Type',
                                                    y='Count',
                                                    title="Complaint Type Distribution (Vertical)",
                                                    color='Count',
                                                    color_continuous_scale='Blues',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=600)
                                            elif chart_type == "Donut Chart":
                                                fig = px.pie(
                                                    complaint_report,
                                                    values='Count',
                                                    names='Complaint Type',
                                                    title="Complaint Type Distribution",
                                                    hole=0.5
                                                )
                                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                                fig.update_layout(height=600)
                                            else:
                                                fig = px.treemap(
                                                    complaint_report,
                                                    path=['Complaint Type'],
                                                    values='Count',
                                                    title="Complaint Type Hierarchy",
                                                    color='Count',
                                                    color_continuous_scale='RdYlGn'
                                                )
                                                fig.update_layout(height=600)
                                            
                                            st.plotly_chart(fig, use_container_width=True)
                                        
                                        elif viz_category == "Geographic Insights":
                                            geo_col1, geo_col2 = st.columns(2)
                                            
                                            with geo_col1:
                                                fig = px.bar(
                                                    subdivision_report.head(12),
                                                    y='Sub-Division',
                                                    x='Count',
                                                    orientation='h',
                                                    title="Top 12 Sub-Divisions",
                                                    color='Count',
                                                    color_continuous_scale='Reds',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=550)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with geo_col2:
                                                fig = px.sunburst(
                                                    circle_report.head(12),
                                                    path=['Circle'],
                                                    values='Count',
                                                    title="Circle Distribution (Sunburst)"
                                                )
                                                fig.update_layout(height=550)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            fig = px.bar(
                                                section_report.head(15),
                                                x='Section',
                                                y='Count',
                                                title="Top 15 Sections by Count",
                                                color='Count',
                                                color_continuous_scale='Teal',
                                                text='Count'
                                            )
                                            fig.update_traces(texttemplate='%{text}', textposition='outside')
                                            fig.update_layout(height=500, xaxis_tickangle=-45)
                                            st.plotly_chart(fig, use_container_width=True)
                                        
                                        elif viz_category == "Time-based Analysis":
                                            st.markdown("#### 📅 Daily Trends")
                                            
                                            fig = px.line(
                                                date_report,
                                                x='Date',
                                                y='Count',
                                                title="Daily Complaint Trends",
                                                markers=True,
                                                color_discrete_sequence=['#FF6692']
                                            )
                                            fig.update_traces(line=dict(width=3), marker=dict(size=8))
                                            fig.update_layout(height=500)
                                            st.plotly_chart(fig, use_container_width=True)
                                            
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                day_of_week_counts = date_report.groupby('Day of Week')['Count'].sum().reset_index()
                                                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                                                day_of_week_counts['Day of Week'] = pd.Categorical(day_of_week_counts['Day of Week'], categories=day_order, ordered=True)
                                                day_of_week_counts = day_of_week_counts.sort_values('Day of Week')
                                                
                                                fig = px.bar(
                                                    day_of_week_counts,
                                                    x='Day of Week',
                                                    y='Count',
                                                    title="Complaints by Day of Week",
                                                    color='Count',
                                                    color_continuous_scale='Blues'
                                                )
                                                fig.update_layout(height=450)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with col2:
                                                fig = px.bar(
                                                    shift_report,
                                                    x='Shift Duty',
                                                    y='Count',
                                                    title="Shift-wise Distribution",
                                                    color='Count',
                                                    color_continuous_scale='Greens',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=450)
                                                st.plotly_chart(fig, use_container_width=True)
                                        
                                        else:  # Comparative Views
                                            st.markdown("#### 🔄 Multi-dimensional Comparison")
                                            
                                            comp_col1, comp_col2, comp_col3 = st.columns(3)
                                            
                                            with comp_col1:
                                                fig = px.pie(
                                                    complaint_report.head(8),
                                                    values='Count',
                                                    names='Complaint Type',
                                                    title="Top Complaints",
                                                    hole=0.4
                                                )
                                                fig.update_layout(height=400)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with comp_col2:
                                                fig = px.pie(
                                                    status_report,
                                                    values='Count',
                                                    names='Status',
                                                    title="Status Split",
                                                    color='Status',
                                                    color_discrete_map={'CLOSED': '#00CC96', 'OPEN': '#EF553B'},
                                                    hole=0.4
                                                )
                                                fig.update_layout(height=400)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with comp_col3:
                                                fig = px.pie(
                                                    qrc_report,
                                                    values='Count',
                                                    names='QRC Type',
                                                    title="QRC Distribution",
                                                    hole=0.4
                                                )
                                                fig.update_layout(height=400)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            # Stacked comparison
                                            st.markdown("#### 📊 Department vs Status Comparison")
                                            if len(dept_report) > 0 and len(status_report) > 0:
                                                dept_status = month_df.groupby(['DEPT', 'CLOSED/OPEN']).size().reset_index(name='Count')
                                                fig = px.bar(
                                                    dept_status.head(30),
                                                    x='DEPT',
                                                    y='Count',
                                                    color='CLOSED/OPEN',
                                                    title="Department-wise Status Distribution",
                                                    barmode='stack',
                                                    color_discrete_map={'CLOSED': '#00CC96', 'OPEN': '#EF553B'}
                                                )
                                                fig.update_layout(height=500, xaxis_tickangle=-45)
                                                st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Tab 4: Remarks & Insights
                                    with tab4:
                                        st.markdown("### 💬 Remarks Analysis & Insights")
                                        
                                        remark_cols = st.columns(4)
                                        
                                        with remark_cols[0]:
                                            st.metric("📝 Total Remarks", f"{remarks_report['Total Remarks']:,}")
                                        with remark_cols[1]:
                                            st.metric("👍 Appreciation Tweets", remarks_report['Appreciation Tweets'])
                                        with remark_cols[2]:
                                            st.metric("⏳ Awaited Consumer", remarks_report['Awaited Consumer'])
                                        with remark_cols[3]:
                                            st.metric("🔢 5-digit Numbers", remarks_report['5-digit Numbers'])
                                        
                                        st.markdown("---")
                                        
                                        remarks_viz_data = pd.DataFrame({
                                            'Category': ['Appreciation Tweets', 'Awaited Consumer', '5-digit Numbers'],
                                            'Count': [
                                                remarks_report['Appreciation Tweets'],
                                                remarks_report['Awaited Consumer'],
                                                remarks_report['5-digit Numbers']
                                            ]
                                        })
                                        
                                        if remarks_viz_data['Count'].sum() > 0:
                                            viz_col1, viz_col2 = st.columns(2)
                                            
                                            with viz_col1:
                                                fig = px.bar(
                                                    remarks_viz_data,
                                                    x='Category',
                                                    y='Count',
                                                    title="Remarks Pattern Distribution",
                                                    color='Count',
                                                    color_continuous_scale='Viridis',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=500)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with viz_col2:
                                                fig = px.pie(
                                                    remarks_viz_data[remarks_viz_data['Count'] > 0],
                                                    values='Count',
                                                    names='Category',
                                                    title="Remarks Category Breakdown",
                                                    hole=0.5
                                                )
                                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                                fig.update_layout(height=500)
                                                st.plotly_chart(fig, use_container_width=True)
                                        else:
                                            st.info("ℹ️ No specific remarks patterns found in the selected month.")
                                        
                                        st.markdown("---")
                                        st.markdown("#### 📋 Sample Remarks Data")
                                        if 'REMARKS' in month_df.columns:
                                            sample_remarks_df = month_df[['DATE', 'COMPLAINT TYPE', 'REMARKS']].head(20)
                                            st.dataframe(
                                                sample_remarks_df.style.set_properties(**{'text-align': 'left'}),
                                                use_container_width=True,
                                                height=450
                                            )
                                        else:
                                            st.info("ℹ️ REMARKS column not found in dataset")
                                    
                                    # Tab 5: Trends & Performance
                                    with tab5:
                                        st.markdown("### 📉 Trends & Performance Analytics")
                                        
                                        perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
                                        
                                        with perf_col1:
                                            st.metric("📊 Daily Avg", f"{performance_metrics.get('avg_daily_complaints', 0):.1f} cases")
                                        with perf_col2:
                                            if 'avg_resolution_time' in performance_metrics:
                                                st.metric("⏱️ Avg Time", f"{performance_metrics['avg_resolution_time']:.0f} min")
                                            else:
                                                st.metric("⏱️ Avg Time", "N/A")
                                        with perf_col3:
                                            if 'median_resolution_time' in performance_metrics:
                                                st.metric("📍 Median Time", f"{performance_metrics['median_resolution_time']:.0f} min")
                                            else:
                                                st.metric("📍 Median Time", "N/A")
                                        with perf_col4:
                                            if 'peak_shift' in performance_metrics:
                                                st.metric("🔥 Peak Shift", performance_metrics['peak_shift'])
                                            else:
                                                st.metric("🔥 Peak Shift", "N/A")
                                        
                                        st.markdown("---")
                                        
                                        st.markdown("#### 📈 Daily Trend Analysis")
                                        st.dataframe(
                                            trend_data.style.background_gradient(subset=['Count'], cmap='YlOrRd'),
                                            use_container_width=True,
                                            height=400
                                        )
                                        
                                        fig = px.line(
                                            trend_data,
                                            x='Date',
                                            y='Count',
                                            title="Daily Complaint Volume Trend",
                                            markers=True
                                        )
                                        if '7-Day Moving Avg' in trend_data.columns:
                                            fig.add_scatter(x=trend_data['Date'], y=trend_data['7-Day Moving Avg'], 
                                                        mode='lines', name='7-Day Moving Average',
                                                        line=dict(color='red', width=2, dash='dash'))
                                        fig.update_layout(height=550)
                                        st.plotly_chart(fig, use_container_width=True)
                                        
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("#### 🎯 Performance Summary")
                                            perf_summary = pd.DataFrame({
                                                'Metric': ['Total Cases', 'Avg Daily', 'Peak Day Count', 'Lowest Day Count'],
                                                'Value': [
                                                    len(month_df),
                                                    f"{performance_metrics.get('avg_daily_complaints', 0):.1f}",
                                                    trend_data['Count'].max(),
                                                    trend_data['Count'].min()
                                                ]
                                            })
                                            st.dataframe(perf_summary, use_container_width=True, height=250)
                                        
                                        with col2:
                                            if 'avg_resolution_time' in performance_metrics:
                                                st.markdown("#### ⏱️ Resolution Time Stats")
                                                time_stats = pd.DataFrame({
                                                    'Statistic': ['Average', 'Median', 'Minimum', 'Maximum'],
                                                    'Minutes': [
                                                        f"{performance_metrics.get('avg_resolution_time', 0):.0f}",
                                                        f"{performance_metrics.get('median_resolution_time', 0):.0f}",
                                                        f"{performance_metrics.get('min_resolution_time', 0):.0f}",
                                                        f"{performance_metrics.get('max_resolution_time', 0):.0f}"
                                                    ]
                                                })
                                                st.dataframe(time_stats, use_container_width=True, height=250)
                                    
                                    # Tab 6: Advanced Filters
                                    with tab6:
                                        st.markdown("### 🔎 Advanced Data Filtering & Export")
                                        
                                        st.markdown("#### 🎛️ Filter Controls")
                                        filter_col1, filter_col2, filter_col3 = st.columns(3)
                                        
                                        with filter_col1:
                                            selected_complaint = st.multiselect(
                                                "🔹 Complaint Type",
                                                options=sorted(month_df['COMPLAINT TYPE'].unique()),
                                                key='complaint_filter_tab6'
                                            )
                                        
                                        with filter_col2:
                                            selected_shift = st.multiselect(
                                                "⏰ Shift Duty",
                                                options=sorted(month_df['SHIFT DUTY'].unique()),
                                                key='shift_filter_tab6'
                                            )
                                        
                                        with filter_col3:
                                            selected_status = st.multiselect(
                                                "🔄 Status",
                                                options=sorted(month_df['CLOSED/OPEN'].unique()),
                                                key='status_filter_tab6'
                                            )
                                        
                                        filter_col4, filter_col5, filter_col6 = st.columns(3)
                                        
                                        with filter_col4:
                                            selected_dept = st.multiselect(
                                                "🏛️ Department",
                                                options=sorted(month_df['DEPT'].unique()),
                                                key='dept_filter_tab6'
                                            )
                                        
                                        with filter_col5:
                                            selected_section = st.multiselect(
                                                "🏢 Section",
                                                options=sorted(month_df['SECTION'].unique()),
                                                key='section_filter_tab6'
                                            )
                                        
                                        with filter_col6:
                                            selected_circle = st.multiselect(
                                                "🔵 Circle",
                                                options=sorted(month_df['CIRCLE'].unique()),
                                                key='circle_filter_tab6'
                                            )
                                        
                                        # Apply filters
                                        filtered_df = month_df.copy()
                                        
                                        if selected_complaint:
                                            filtered_df = filtered_df[filtered_df['COMPLAINT TYPE'].isin(selected_complaint)]
                                        if selected_shift:
                                            filtered_df = filtered_df[filtered_df['SHIFT DUTY'].isin(selected_shift)]
                                        if selected_status:
                                            filtered_df = filtered_df[filtered_df['CLOSED/OPEN'].isin(selected_status)]
                                        if selected_dept:
                                            filtered_df = filtered_df[filtered_df['DEPT'].isin(selected_dept)]
                                        if selected_section:
                                            filtered_df = filtered_df[filtered_df['SECTION'].isin(selected_section)]
                                        if selected_circle:
                                            filtered_df = filtered_df[filtered_df['CIRCLE'].isin(selected_circle)]
                                        
                                        st.markdown("---")
                                        st.markdown(f"#### 📊 Filtered Results: **{len(filtered_df):,}** records")
                                        
                                        if len(filtered_df) > 0:
                                            # Show filtered summary
                                            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
                                            
                                            with summary_col1:
                                                st.metric("Total Records", f"{len(filtered_df):,}")
                                            with summary_col2:
                                                closed_filtered = (filtered_df['CLOSED/OPEN'] == 'CLOSED').sum()
                                                closure_filtered = (closed_filtered / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
                                                st.metric("Closure Rate", f"{closure_filtered:.1f}%")
                                            with summary_col3:
                                                st.metric("Complaint Types", filtered_df['COMPLAINT TYPE'].nunique())
                                            with summary_col4:
                                                if 'MINUTE' in filtered_df.columns:
                                                    avg_time_filtered = filtered_df['MINUTE'].mean()
                                                    st.metric("Avg Time", f"{avg_time_filtered:.0f} min")
                                                else:
                                                    st.metric("Avg Time", "N/A")
                                            
                                            st.markdown("---")
                                            st.dataframe(
                                                filtered_df.style.set_properties(**{'text-align': 'left'}),
                                                use_container_width=True,
                                                height=500
                                            )
                                            
                                            # Download options
                                            st.markdown("#### 📥 Export Options")
                                            download_col1, download_col2 = st.columns(2)
                                            
                                            with download_col1:
                                                csv = filtered_df.to_csv(index=False).encode('utf-8')
                                                st.download_button(
                                                    label="📄 Download as CSV",
                                                    data=csv,
                                                    file_name=f'filtered_data_{selected_month}.csv',
                                                    mime='text/csv',
                                                    use_container_width=True,
                                                    key='download_csv_tab6'
                                                )
                                            
                                            with download_col2:
                                                # Create Excel file in memory
                                                from io import BytesIO
                                                buffer = BytesIO()
                                                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                                    filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
                                                buffer.seek(0)
                                                
                                                st.download_button(
                                                    label="📊 Download as Excel",
                                                    data=buffer,
                                                    file_name=f'filtered_data_{selected_month}.xlsx',
                                                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                                    use_container_width=True,
                                                    key='download_excel_tab6'
                                                )
                                        else:
                                            st.warning("⚠️ No records match the selected filters. Please adjust your criteria.")
                                    
                                    st.markdown("---")
                                    st.success("✅ Report generated successfully!")
                                    
                        except Exception as e:
                            st.error(f"❌ Error processing data: {str(e)}")
                            st.info("💡 Please ensure your Excel file has all required columns")
                            st.session_state.report_generated = False
                    else:
                        st.info("👆 Select a month and year from the dropdowns above, then click 'Generate Comprehensive Report'")
                
                except Exception as e:
                    st.error(f"❌ Error loading file: {str(e)}")
                    st.info("💡 Please check if the file path is correct and the file exists")
            else:
                st.warning("⚠️ Please provide a valid dataset path to begin analysis")
                st.info("💡 Set the `dataset_path` variable to point to your Excel file")
                    

            st.header("📊 Year Wise Complaint Analysis Dashboard")
            st.divider()
            # Add your Streamlit code for Tab 2 here



    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Unhandled error in Streamlit dashboard Tab 2 | error={error_msg}")
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)
