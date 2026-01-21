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
from ml_project.backend_api.fastapi_analysis_helper import open_complaint_pivot
from ml_project.frontend_api.streamlit_analysis_helper import generate_all_agging_complaint_report,style_grand_total_dataframe
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.frontend_api.streamlit_cache_data import (
    fetch_open_complaint_pivot,
    fetch_open_close_complaint_pivot,
    fetch_agging_open_pivot,
    fetch_agging_open_close_pivot,
    fetch_open_close_complaint_report,
    fetch_all_agging_complaint_report,
    fetch_close_power_outage_duration )

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



# Pie Chart , donut chart, mosaic plot, marimekko chart,sunburst chart,sankey diagram,parallel sets,network diagram,polar area chart,Heatmap 
# multi-line chart, Area Chart by Category, stacked area chart, scatter plot with hue,dot plot by category, Choropleth Map, Dot Density Map
# Funnel Chart, Mixed Subplots
# 3d pie chart,3D 3D Bar Chart, 3D Column Chart,3d treemap,3d line plot,3D Scatter Plot,3D Histogram,3d bubble chart,3D Grouped Bar Chart,3d choropleth map
#JSON Schema Tree,Tree View

logger = get_logger(__name__)


def streamlit_analysis_tab1(tab1, dataset_path, logger):
    """
    Renders all content for Tab 1 including complaint reports and power outage analysis.
    
    Parameters:
    -----------
    tab1 : streamlit.tabs
        The Streamlit tab container where content will be rendered
    dataset_path : str
        Path to the dataset file
    logger : logging.Logger
        Logger instance for logging operations
    """
    try:    
        with tab1:
            # ========================================
            # SECTION 1: OPEN COMPLAINTS PIVOT
            # ========================================
            
            # Add button to fetch data
            if st.button("📥 Load Open Complaints Data", key="load_complaints_btn",type="primary" ):
                with st.spinner("Loading data..."):
                    df_pivot, error, status_code = fetch_open_complaint_pivot()

                if error is None and df_pivot is not None:
                    st.subheader("📊 Open Complaints Reports")
                    st.caption("Grand Total row is highlighted in red for easy identification")
                    
                    styled_df = style_grand_total_dataframe(df_pivot)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Complaint overview displayed successfully")
                    
                    st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                        st.info("The API service may be experiencing issues. Please try again in a few moments.")
                        logger.error(f"Tab 1: API request failed with status code {status_code}")
                    else:
                        st.error(f"❌ Error: {error}")
                        st.info("The API service may be temporarily unavailable. Please try again in a few moments.")
                        logger.error(f"Tab 1: Error - {error}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the open complaints data")
            
            
            st.divider()

            # ========================================
            # SECTION 2: OPEN/CLOSE COMPLAINTS PIVOT
            # ========================================
            st.subheader("📊 Open/Close Complaints Reports")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load Open/Close Complaints Data", key="load_open_close_complaints_btn", type="primary"):
                with st.spinner("Loading data..."):
                    df_pivot_02, error_02, status_code_02 = fetch_open_close_complaint_pivot()

                if error_02 is None and df_pivot_02 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_02)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Open Close Complaints Pivot Table displayed successfully")
                    
                    st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code_02:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_02}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_02}")
                    else:
                        st.error(f"❌ Error: {error_02}")
                        logger.error(f"Tab 1: Error - {error_02}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the open/close complaints data")
            
            st.divider()
            
            # ========================================
            # SECTION 3: AGGING OPEN COMPLAINTS PIVOT
            # ========================================
            st.header("📊 Agging Open Complaints Reports")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load Agging Open Complaints Data", key="load_agging_open_complaints_btn",type="primary"):
                with st.spinner("Loading data..."):
                    df_pivot_03, error_03, status_code_03 = fetch_agging_open_pivot()

                if error_03 is None and df_pivot_03 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_03)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Agging Open Complaints Pivot Table displayed successfully")
                    
                    st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code_03:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_03}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_03}")
                    else:
                        st.error(f"❌ Error: {error_03}")
                        logger.error(f"Tab 1: Error - {error_03}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the agging open complaints data")
            
            st.divider()
            
            # ========================================
            # SECTION 4: AGGING OPEN/CLOSE COMPLAINTS PIVOT
            # ========================================
            st.header("📊 Agging Day Difference All Complaints Reports")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load Agging Day Difference Data", key="load_agging_day_diff_complaints_btn",type="primary"):
                with st.spinner("Loading data..."):
                    df_pivot_04, error_04, status_code_04 = fetch_agging_open_close_pivot()

                if error_04 is None and df_pivot_04 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_04)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Agging Open/Close Complaints Pivot Table displayed successfully")
                    
                    st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code_04:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_04}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_04}")
                    else:
                        st.error(f"❌ Error: {error_04}")
                        logger.error(f"Tab 1: Error - {error_04}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the agging day difference data")
            
            st.divider()

            # ========================================
            # SECTION 5: OPEN/CLOSE COMPLAINT REPORT
            # ========================================
            st.header("📊 All Complaint Report")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load All Complaint Report Data", key="load_all_complaint_report_btn",type="primary"):
                with st.spinner("Loading data..."):
                    df_pivot_05, error_05, status_code_05 = fetch_open_close_complaint_report()

                if error_05 is None and df_pivot_05 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_05)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Open Close Complaint Report displayed successfully")

                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code_05:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_05}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_05}")
                    else:
                        st.error(f"❌ Error: {error_05}")
                        logger.error(f"Tab 1: Error - {error_05}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the all complaint report data")
            
            st.divider()

            # ========================================
            # SECTION 6: ALL AGGING COMPLAINT REPORT
            # ======================================== 
            st.header("📊 All Department Complaint Type Report")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load All Department Complaint Type Data", key="load_all_dept_complaint_btn",type="primary"):
                # Validate dataset path exists
                if not dataset_path:
                    st.error("❌ Dataset path is not provided.")
                    st.info("ℹ️ Please configure the dataset path in the settings.")

                elif not os.path.exists(dataset_path):
                    st.error(f"❌ Dataset not found at: `{dataset_path}`")
                    st.info("ℹ️ Please verify the file path and try again.")

                else:
                    # Show loading spinner while processing
                    with st.spinner("📊 Loading data..."):
                        @st.cache_data
                        def load_complaint_data(path):
                            return generate_all_agging_complaint_report(path)
                        
                        complaint_data = load_complaint_data(dataset_path)

                    # Check if data is None or empty (handle both list and DataFrame)
                    if complaint_data is None:
                        st.warning("⚠️ No data available to display.")
                        st.info("ℹ️ The dataset may be empty or contain no valid records.")
                    else:
                        complaint_df = complaint_data

                        # Display dataframe
                        st.dataframe(
                            complaint_df,
                            use_container_width=True,
                            height=400
                        )

                        logger.info("Tab 1: All Agging Complaint Report displayed successfully")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the all department complaint type data")
            st.divider()

            # ========================================
            # SECTION 7: POWER OUTAGE DURATION
            # ======================================== 

            st.header("X-Dashboard Shift wise Power Outage Duration Hour Analysis")

            # Initialize session state for selected date if it doesn't exist
            if "selected_outage_date" not in st.session_state:
                st.session_state.selected_outage_date = datetime.today()

            # Initialize a flag to track if analysis should run
            if "run_analysis" not in st.session_state:
                st.session_state.run_analysis = False

            # Date picker with a unique key to prevent auto-triggering
            selected_date = st.date_input(
                "Select Date",
                value=st.session_state.selected_outage_date,
                key="date_picker_outage",  # Add unique key
                help="Choose a date to analyze power outage durations"
            )

            # Add a button to trigger the analysis
            if st.button("🔍 Restoration Duration Hour Analysis Reports", key="analyze_button",type="primary"):
                # Update session state only when button is clicked
                st.session_state.selected_outage_date = selected_date
                st.session_state.run_analysis = True

            # Only process if the button was clicked
            if st.session_state.run_analysis:
                if dataset_path is not None:
                    try:
                        # Show loading spinner
                        with st.spinner("Processing data..."):
                            pivot_df = fetch_close_power_outage_duration(
                                dataset_path,
                                st.session_state.selected_outage_date  # Use stored date from session state
                            )

                            # Display the pivot table
                            st.subheader("Restoration Duration Analysis Reports")
                            st.dataframe(
                                pivot_df,
                                use_container_width=True,
                                height=400,
                                hide_index=False
                            )

                        st.success("✅ Data processing successfully!")
                        
                        # Reset the flag after successful processing
                        st.session_state.run_analysis = False

                    except ValueError as ve:
                        # Handle time format errors specifically
                        if "time data" in str(ve).lower() or "format" in str(ve).lower():
                            st.error("❌ Error: Time format is incorrect in the dataset. Please check the date/time columns format.")
                            st.info("💡 Expected format: YYYY-MM-DD HH:MM:SS or similar standard datetime format")
                        else:
                            st.error(f"❌ Data error: {str(ve)}")
                        st.session_state.run_analysis = False

                    except pd.errors.ParserError as pe:
                        st.error("❌ Error: Unable to parse the data file. Please check if the file format is correct.")
                        st.info(f"Details: {str(pe)}")
                        st.session_state.run_analysis = False

                    except FileNotFoundError:
                        st.error("❌ Error: Dataset file not found. Please check the file path.")
                        st.session_state.run_analysis = False

                    except KeyError as ke:
                        st.error(f"❌ Error: Required column not found in dataset: {str(ke)}")
                        st.info("Please ensure all necessary columns exist in your dataset.")
                        st.session_state.run_analysis = False

                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
                        st.info("💡 If this is a time format issue, please verify your datetime columns are in standard format (YYYY-MM-DD HH:MM:SS)")
                        st.session_state.run_analysis = False

                else:
                    st.warning("⚠️ Dataset path is not configured. Please check your configuration.")
                    st.session_state.run_analysis = False

            # Show last loaded timestamp only if analysis was run
            if "last_analysis_time" not in st.session_state:
                st.session_state.last_analysis_time = None

            if st.session_state.last_analysis_time:
                st.caption(f"Last loaded: {st.session_state.last_analysis_time}")
                
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
                st.info("👆 Click the button above to load the X-Dashboard Shift wise Power Outage Duration Hour Analysis")


            # ========================================
            # ALL SECTIONS IN 5-COLUMN LAYOUT
            # ========================================

            st.divider()

            st.header("Loding All Complaint Reports View")

            # Create 5 columns
            col1, col2, col3, col4, col5 = st.columns(5)

            # ========================================
            # COLUMN 1: All Agging Complaint Report
            # ========================================
            with col1:
                st.subheader("📊Report 01")
                # Add a button to trigger data loading
                if st.button("📥 Load Open Complaints Data OverView", type="primary"):
                    with st.spinner("Loading data..."):
                        df_pivot, error, status_code = fetch_open_complaint_pivot()

                    if error is None and df_pivot is not None:
                        st.subheader("📊 Open Complaints Reports")
                        st.caption("Grand Total row is highlighted in red for easy identification")
                        
                        styled_df = style_grand_total_dataframe(df_pivot)
                        st.dataframe(styled_df, use_container_width=True, height=400)
                        logger.info("Tab 1: Complaint overview displayed successfully")
                        
                    else:
                        if status_code:
                            st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                            st.info("The API service may be experiencing issues. Please try again in a few moments.")
                            logger.error(f"Tab 1: API request failed with status code {status_code}")
                        else:
                            st.error(f"❌ Error: {error}")
                            st.info("The API service may be temporarily unavailable. Please try again in a few moments.")
                            logger.error(f"Tab 1: Error - {error}")
                else:
                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    
            # ========================================
            # COLUMN 2: Data All View
            # ========================================
            with col2:
                st.subheader("📊Report 02")

                if st.button("🔄 Load Data All Open Close Complaint Report", key="load_data_all_view", type="primary"):
                    with st.spinner("Loading data..."):
                        df_07, error_07, status_code_07 = fetch_open_close_complaint_pivot()

                    if error_07 is None and df_07 is not None:                    
                        st.dataframe(df_07, use_container_width=True, height=400)
                        logger.info("Tab 1: Data All View displayed successfully")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        if status_code_07:
                            st.error(f"❌ Failed to fetch data. Status code: {status_code_07}")
                            logger.error(f"Tab 1: API request failed with status code {status_code_07}")
                        else:
                            st.error(f"❌ Error: {error_07}")
                            logger.error(f"Tab 1: Error - {error_07}")
                else:
                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # ========================================
            # COLUMN 3: Generate All Agging Complaints Report
            # ========================================
            with col3:
                st.subheader("📊Report 03")

                # Validate dataset path exists
                if not dataset_path:
                    st.error("❌ Dataset path is not provided.")
                    st.info("ℹ️ Please configure the dataset path in the settings.")

                elif not os.path.exists(dataset_path):
                    st.error(f"❌ Dataset not found at: `{dataset_path}`")
                    st.info("ℹ️ Please verify the file path and try again.")

                else:
                    # Add button to trigger data loading
                    if st.button("📊 All Department Complaint Type Report View", type="primary"):
                        # Show loading spinner while processing
                        with st.spinner("📊 Loading data..."):
                            @st.cache_data
                            def load_complaint_data(path):
                                return generate_all_agging_complaint_report(path)
                            
                            complaint_data = load_complaint_data(dataset_path)

                        # Check if data is None or empty (handle both list and DataFrame)
                        if complaint_data is None:
                            st.warning("⚠️ No data available to display.")
                            st.info("ℹ️ The dataset may be empty or contain no valid records.")
                        else:
                            complaint_df = complaint_data

                            # Display dataframe
                            st.dataframe(
                                complaint_df,
                                use_container_width=True,
                                height=400
                            )

                            logger.info("Tab 1: All Agging Complaint Report displayed successfully")

                    else:
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                            
            # ========================================
            # COLUMN 4: Agging Open Report
            # ========================================
            with col4:
                st.subheader("📊Report 04")

                if st.button("🔄 Load Generate Agging Open View Report", key="generate_agging_open_report", type="primary"):
                    with st.spinner("Generating report..."):
                        df_10, error_10, status_code_10 = fetch_agging_open_pivot()

                    if error_10 is None and df_10 is not None:                    
                        st.dataframe(df_10, use_container_width=True, height=400)
                        logger.info("Tab 1: Agging Open Report displayed successfully")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        if status_code_10:
                            st.error(f"❌ Failed to fetch data. Status code: {status_code_10}")
                            logger.error(f"Tab 1: API request failed with status code {status_code_10}")
                        else:
                            st.error(f"❌ Error: {error_10}")
                            logger.error(f"Tab 1: Error - {error_10}")
                else:
                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # ========================================
            # COLUMN 5: Open Complaints Reports
            # ========================================
            with col5:
                st.subheader("📊Report 05")
                
                if st.button("🔄 Load Generate Open Complaints Report", key="load_open_complaints", type="primary"):
                    with st.spinner("Loading data..."):
                        df_pivot, error, status_code = fetch_open_complaint_pivot()

                    if error is None and df_pivot is not None:
                        styled_df = style_grand_total_dataframe(df_pivot)
                        st.dataframe(styled_df, use_container_width=True, height=400)
                        logger.info("Tab 1: Complaint overview displayed successfully")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        if status_code:
                            st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                            st.info("The API service may be experiencing issues. Please try again in a few moments.")
                            logger.error(f"Tab 1: API request failed with status code {status_code}")
                        else:
                            st.error(f"❌ Error: {error}")
                            st.info("The API service may be temporarily unavailable. Please try again in a few moments.")
                            logger.error(f"Tab 1: Error - {error}")
                else:
                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Divider
        st.divider()

        if st.button("🔄 Data Refresh All", key="refresh_all_btn", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        logger.info("Streamlit dashboard Tab 1 loaded successfully")
        
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Unhandled error in Streamlit dashboard Tab1 | error={error_msg}")
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)
            
    