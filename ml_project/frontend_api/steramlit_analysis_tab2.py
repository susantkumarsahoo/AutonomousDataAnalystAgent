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
from ml_project.frontend_api.streamlit_cache_data import fetch_generate_month_wise_open_close_pivot_report
from ml_project.frontend_api.streamlit_analysis_helper import (
generate_month_wise_open_clode_pivot_report,
generate_complaint_report,
generate_date_report,
generate_shift_duty_report







)


config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]

from ml_project.configs.config import DatasetNotFoundError, get_dataset_path

try:
    dataset_path = get_dataset_path("data/raw_path")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")


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
            
            with col2:
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

        # Initialize session state
        if 'report_generated' not in st.session_state:
            st.session_state.report_generated = False
        if 'selected_month' not in st.session_state:
            st.session_state.selected_month = None
        if 'dataset_path' not in st.session_state:
            st.session_state.dataset_path = None

        # Cached data loading function
        @st.cache_data
        def load_excel_data(file_path):
            """Load and cache Excel data"""
            df = pd.read_excel(file_path)
            df['DATE'] = pd.to_datetime(df['DATE'])
            return df

        # Cached report generation functions
        @st.cache_data
        def generate_complaint_report(file_path, selected_month):
            """Generate complaint type report with caching"""
            df = pd.read_excel(file_path)
            df['DATE'] = pd.to_datetime(df['DATE'])
            month_data = df[df['DATE'].dt.to_period('M') == selected_month]
            return month_data['COMPLAINT TYPE'].value_counts()

        @st.cache_data
        def generate_date_report(file_path, selected_month):
            """Generate date report with caching"""
            df = pd.read_excel(file_path)
            df['DATE'] = pd.to_datetime(df['DATE'])
            month_data = df[df['DATE'].dt.to_period('M') == selected_month]
            return month_data['DATE'].value_counts().sort_index()

        @st.cache_data
        def generate_shift_duty_report(file_path, selected_month):
            """Generate shift duty report with caching"""
            df = pd.read_excel(file_path)
            df['DATE'] = pd.to_datetime(df['DATE'])
            month_data = df[df['DATE'].dt.to_period('M') == selected_month]
            return month_data['SHIFT DUTY'].value_counts()

        # Main App
        st.title("📊 Complaint Analysis Dashboard")

        if dataset_path is not None:
            # Save to session state safely
            if "dataset_path" not in st.session_state or st.session_state.dataset_path != dataset_path:
                st.session_state.dataset_path = dataset_path
                st.session_state.report_generated = False
            
            # Month and year selectors
            col_month, col_year = st.columns(2)
            with col_month:
                month = st.selectbox(
                    "Select Month", 
                    list(range(1, 13)), 
                    format_func=lambda x: pd.to_datetime(str(x), format="%m").strftime("%B"),
                    key='month_selector'
                )
            with col_year:
                year = st.selectbox(
                    "Select Year", 
                    list(range(2020, 2031)),
                    key='year_selector'
                )

            # Format selected month-year as "MM-YYYY"
            selected_month = f"{month:02d}-{year}"
            
            # Store in session state
            if st.session_state.selected_month != selected_month:
                st.session_state.selected_month = selected_month
                st.session_state.report_generated = False

            # Generate Report Button
            generate_button = st.button("🔍 Generate Report", type="primary", use_container_width=True)

            # Generate report when button clicked or if already generated
            if generate_button or st.session_state.report_generated:
                if generate_button:
                    st.session_state.report_generated = True
                
                try:
                    with st.spinner("Generating reports..."):
                        # Generate reports using cached functions
                        complaint_report = generate_complaint_report(dataset_path, selected_month)
                        date_report = generate_date_report(dataset_path, selected_month)
                        shift_report = generate_shift_duty_report(dataset_path, selected_month)
                        
                        # Load full dataframe using cached function
                        df = load_excel_data(dataset_path)
                        month_fd = df[df['DATE'].dt.to_period('M') == selected_month]
                        
                        # Create three columns for reports
                        col1, col2, col3 = st.columns(3)
                        
                        with col1:
                            st.subheader("🔹 Complaint Type Report")
                            st.dataframe(
                                complaint_report.reset_index().rename(
                                    columns={'COMPLAINT TYPE': 'Complaint Type', 'count': 'Count'}
                                ), 
                                use_container_width=True, 
                                height=300
                            )
                        
                        with col2:
                            st.subheader("📅 Date Report")
                            st.dataframe(
                                date_report.reset_index().rename(
                                    columns={'DATE': 'Date', 'count': 'Count'}
                                ), 
                                use_container_width=True, 
                                height=300
                            )
                        
                        with col3:
                            st.subheader("⏰ Shift Duty Report")
                            st.dataframe(
                                shift_report.reset_index().rename(
                                    columns={'SHIFT DUTY': 'Shift Duty', 'count': 'Count'}
                                ), 
                                use_container_width=True, 
                                height=300
                            )
                        
                        st.markdown("---")
                        
                        # Interactive Visualizations
                        st.header("📈 Interactive Visualizations")
                        
                        # Visualization selection
                        viz_option = st.selectbox(
                            "Select Visualization Type:",
                            ["Complaint Type Distribution", "Date Distribution", "Shift Duty Distribution", 
                            "Compare All", "Time Series Analysis"],
                            key='viz_selector'
                        )
                        
                        if viz_option == "Complaint Type Distribution":
                            chart_type = st.radio(
                                "Chart Type:", 
                                ["Bar Chart", "Pie Chart", "Treemap"], 
                                horizontal=True,
                                key='complaint_chart_type'
                            )
                            
                            if chart_type == "Bar Chart":
                                fig = px.bar(
                                    complaint_report.reset_index(), 
                                    x='COMPLAINT TYPE', y='count',
                                    labels={'COMPLAINT TYPE': 'Complaint Type', 'count': 'Count'},
                                    title="Complaint Type Distribution",
                                    color='count',
                                    color_continuous_scale='Blues'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            elif chart_type == "Pie Chart":
                                fig = px.pie(
                                    complaint_report.reset_index(), 
                                    values='count', names='COMPLAINT TYPE',
                                    title="Complaint Type Distribution"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            
                            else:
                                fig = px.treemap(
                                    complaint_report.reset_index(), 
                                    path=['COMPLAINT TYPE'], values='count',
                                    title="Complaint Type Distribution"
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        
                        elif viz_option == "Date Distribution":
                            fig = px.bar(
                                date_report.reset_index().head(20), 
                                x='DATE', y='count',
                                labels={'DATE': 'Date', 'count': 'Count'},
                                title="Top 20 Dates by Complaint Count",
                                color='count',
                                color_continuous_scale='Reds'
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        
                        elif viz_option == "Shift Duty Distribution":
                            chart_type = st.radio(
                                "Chart Type:", 
                                ["Bar Chart", "Donut Chart"], 
                                horizontal=True,
                                key='shift_chart_type'
                            )
                            
                            if chart_type == "Bar Chart":
                                fig = px.bar(
                                    shift_report.reset_index(), 
                                    x='SHIFT DUTY', y='count',
                                    labels={'SHIFT DUTY': 'Shift Duty', 'count': 'Count'},
                                    title="Shift Duty Distribution",
                                    color='count',
                                    color_continuous_scale='Greens'
                                )
                                st.plotly_chart(fig, use_container_width=True)
                            else:
                                fig = px.pie(
                                    shift_report.reset_index(), 
                                    values='count', names='SHIFT DUTY',
                                    title="Shift Duty Distribution",
                                    hole=0.4
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        
                        elif viz_option == "Compare All":
                            col_a, col_b, col_c = st.columns(3)
                            
                            with col_a:
                                fig1 = px.pie(
                                    complaint_report.reset_index(), 
                                    values='count', names='COMPLAINT TYPE',
                                    title="Complaint Types"
                                )
                                st.plotly_chart(fig1, use_container_width=True)
                            
                            with col_b:
                                fig2 = px.bar(
                                    date_report.reset_index().head(10), 
                                    x='DATE', y='count',
                                    title="Top 10 Dates"
                                )
                                st.plotly_chart(fig2, use_container_width=True)
                            
                            with col_c:
                                fig3 = px.pie(
                                    shift_report.reset_index(), 
                                    values='count', names='SHIFT DUTY',
                                    title="Shift Duties", hole=0.3
                                )
                                st.plotly_chart(fig3, use_container_width=True)
                        
                        else:  # Time Series Analysis
                            if 'DATE' in df.columns:
                                daily_counts = df.groupby('DATE').size().reset_index(name='Count')
                                
                                fig = px.line(
                                    daily_counts, x='DATE', y='Count',
                                    title="Complaints Over Time",
                                    markers=True
                                )
                                st.plotly_chart(fig, use_container_width=True)
                        
                        # Filter and Explore Section
                        st.markdown("---")
                        st.header("🔍 Filter and Explore Data")
                        
                        filter_col1, filter_col2 = st.columns(2)
                        
                        with filter_col1:
                            if 'COMPLAINT TYPE' in month_fd.columns:
                                selected_complaint = st.multiselect(
                                    "Filter by Complaint Type:",
                                    options=sorted(df['COMPLAINT TYPE'].unique()),
                                    default=None,
                                    key='complaint_filter'
                                )
                        
                        with filter_col2:
                            if 'SHIFT DUTY' in month_fd.columns:
                                selected_shift = st.multiselect(
                                    "Filter by Shift Duty:",
                                    options=sorted(month_fd['SHIFT DUTY'].unique()),
                                    default=None,
                                    key='shift_filter'
                                )
                        
                        # Apply filters
                        filtered_df = month_fd.copy()
                        if selected_complaint:
                            filtered_df = filtered_df[filtered_df['COMPLAINT TYPE'].isin(selected_complaint)]
                        if selected_shift:
                            filtered_df = filtered_df[filtered_df['SHIFT DUTY'].isin(selected_shift)]
                        
                        st.subheader(f"Filtered Data ({len(filtered_df)} records)")
                        st.dataframe(filtered_df, use_container_width=True, height=400)
                        
                        # Summary Statistics
                        st.markdown("---")
                        st.header("📊 Summary Statistics")
                        
                        stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
                        
                        with stat_col1:
                            st.metric("Total Complaints", len(month_fd))
                        
                        with stat_col2:
                            st.metric("Unique Complaint Types", month_fd['COMPLAINT TYPE'].nunique())
                        
                        with stat_col3:
                            st.metric("Date Range", len(month_fd['DATE'].unique()))
                        
                        with stat_col4:
                            st.metric("Shift Types", month_fd['SHIFT DUTY'].nunique())
                    
                    st.success("✅ Report generated successfully!")
                    
                except Exception as e:
                    st.error(f"Error processing file: {str(e)}")
                    st.info("Please ensure your Excel file has columns: 'COMPLAINT TYPE', 'DATE', and 'SHIFT DUTY'")
                    st.session_state.report_generated = False
            else:
                st.info("👆 Select a month and year, then click 'Generate Report' to view the analysis")
        else:
            st.info("👆 Please upload an Excel file to begin analysis")
            st.markdown("""
            ### Expected File Format:
            Your Excel file should contain the following columns:
            - **COMPLAINT TYPE**: Type of complaint
            - **DATE**: Date of complaint
            - **SHIFT DUTY**: Shift during which complaint occurred
            """)
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Unhandled error in Streamlit dashboard Tab 2 | error={error_msg}")
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)