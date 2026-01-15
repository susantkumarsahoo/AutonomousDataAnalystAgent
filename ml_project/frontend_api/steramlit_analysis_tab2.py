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
import plotly.graph_objects as go
from datetime import datetime, timedelta
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url
from ml_project.backend_api.fastapi_analysis_helper import*
from ml_project.frontend_api.streamlit_analysis_helper import*
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.frontend_api.streamlit_cache_data import fetch_generate_month_wise_open_close_pivot_report
from ml_project.frontend_api.streamlit_analysis_helper import generate_month_wise_open_clode_pivot_report 


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
                    index=list(range(current_year - 5, current_year + 1)).index(st.session_state.selected_year_tab2),
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
                if st.button("📊 Generate Report", type="primary", use_container_width=True, key="generate_report_button_tab2"):
                    # Update session state when button is clicked
                    st.session_state.selected_year_tab2 = selected_year
                    st.session_state.selected_month_tab2 = selected_month_num
                    st.session_state.generate_report_tab2 = True

            # Convert to string format 'YYYY-MM'
            month_str = f"{st.session_state.selected_year_tab2}-{st.session_state.selected_month_tab2:02d}"
            
            # Display selected month
            st.info(f"📅 Selected Period: **{months[st.session_state.selected_month_tab2]} {st.session_state.selected_year_tab2}** (Format: {month_str})")

            # Only generate report if button was clicked
            if st.session_state.generate_report_tab2:
                with st.spinner("Loading data..."):
                    df, error, status_code = fetch_generate_month_wise_open_close_pivot_report(month_str)
                
                if error is None and df is not None:
                    st.success("✅ Report generated successfully!")
                    st.dataframe(df, use_container_width=True, height=400)
                    logger.info(f"Tab 2: Month wise report generated successfully | month={month_str}")
                    
                    # Store last generated time
                    if "last_report_time_tab2" not in st.session_state:
                        st.session_state.last_report_time_tab2 = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    else:
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
                st.caption(f"Last loaded: Not generated yet")
            
            st.divider()












            

    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error("Unhandled error in Streamlit dashboard Tab 2 | error=%s", error_msg)
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)


