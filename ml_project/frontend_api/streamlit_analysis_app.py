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

config = read_yaml("ml_project/config/ml_project_config.yaml")
dataset_path = config["data"]["raw_path"]

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

def analysis_dashboard(
    dashboard_type: str,
    dataset_path: str,
    uploaded_file: Optional[object] = None,
) -> None:
    """
    Render the selected dashboard.

    Parameters:
        dashboard_type (str): Selected dashboard option
        dataset_path (str): Path to the default dataset
        uploaded_file (Optional[object]): Optional user-uploaded file
    """
    try:
        # Strip emojis from dashboard_type for logging
        dashboard_type_clean = dashboard_type.encode('ascii', 'ignore').decode('ascii').strip()
        logger.info("Rendering analysis dashboard | type=%s", dashboard_type_clean)
        
        # Page Title
        st.title(dashboard_type)

        # ==================================================
        # ANALYSIS DASHBOARD
        # ==================================================
        if "Analysis Dashboard" in dashboard_type:
           
            df = None
            try:
                if uploaded_file:
                    logger.info("Loading uploaded file")
                    df = pd.read_excel(uploaded_file)
                elif dataset_path and dataset_path != "Not available":
                    logger.info("Loading default dataset | path=%s", dataset_path)
                    df = pd.read_excel(dataset_path)
                else:
                    st.warning("⚠️ No data available. Please upload a file or check the default dataset path.")
                    logger.warning("No dataset available")
                    return
            except Exception as e:
                st.error(f"❌ Error loading data: {str(e)}")
                logger.error("Error loading dataset | error=%s", str(e))
                return
            
            if df is None or df.empty:
                st.warning("⚠️ No data available. Please upload a file or check the default dataset path.")
                logger.warning("DataFrame is empty or None")
                return

            logger.info("Dataset loaded successfully | shape=%s", df.shape)

            tab1, tab2, tab3, tab4, tab5 = st.tabs(
                [
                    "📈 Complaint Overview",
                    "📋 Data Table",
                    "📊 Summary",
                    "🔍 Dataset Information",
                    "📊 Visualizations",
                ]
            )

            # ----------------------------------------------
            # TAB 1: COMPLAINT OVERVIEW
            # ----------------------------------------------
            with tab1:
                st.success("🛠️ This project is under development.")

                # ========================================
                # SECTION 1: OPEN COMPLAINT PIVOT
                # ========================================
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

                st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()

                # ========================================
                # SECTION 2: OPEN/CLOSE COMPLAINTS PIVOT
                # ========================================
                st.subheader("📊 Open/Close Complaints Reports")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                with st.spinner("Loading data..."):
                    df_pivot_02, error_02, status_code_02 = fetch_open_close_complaint_pivot()

                if error_02 is None and df_pivot_02 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_02)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Open Close Complaints Pivot Table displayed successfully")
                else:
                    if status_code_02:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_02}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_02}")
                    else:
                        st.error(f"❌ Error: {error_02}")
                        logger.error(f"Tab 1: Error - {error_02}")

                st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()
                
                # ========================================
                # SECTION 3: AGGING OPEN COMPLAINTS PIVOT
                # ========================================
                st.header("📊 Agging Open Complaints Reports")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                with st.spinner("Loading data..."):
                    df_pivot_03, error_03, status_code_03 = fetch_agging_open_pivot()

                if error_03 is None and df_pivot_03 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_03)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Agging Open Complaints Pivot Table displayed successfully")
                else:
                    if status_code_03:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_03}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_03}")
                    else:
                        st.error(f"❌ Error: {error_03}")
                        logger.error(f"Tab 1: Error - {error_03}")

                st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()
                
                # ========================================
                # SECTION 4: AGGING OPEN/CLOSE COMPLAINTS PIVOT
                # ========================================
                st.header("📊 Agging Day Difference All Complaints Reports")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                with st.spinner("Loading data..."):
                    df_pivot_04, error_04, status_code_04 = fetch_agging_open_close_pivot()

                if error_04 is None and df_pivot_04 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_04)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Agging Open/Close Complaints Pivot Table displayed successfully")
                else:
                    if status_code_04:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_04}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_04}")
                    else:
                        st.error(f"❌ Error: {error_04}")
                        logger.error(f"Tab 1: Error - {error_04}")

                st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()

                # ========================================
                # SECTION 5: OPEN/CLOSE COMPLAINT REPORT
                # ========================================
                st.header("📊 All Complaint Report")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                with st.spinner("Loading data..."):
                    df_pivot_05, error_05, status_code_05 = fetch_open_close_complaint_report()

                if error_05 is None and df_pivot_05 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_05)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Open Close Complaint Report displayed successfully")

                    st.caption(
                        f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code_05:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_05}")
                        logger.error(
                            f"Tab 1: API request failed with status code {status_code_05}")
                    else:
                        st.error(f"❌ Error: {error_05}")
                        logger.error(f"Tab 1: Error - {error_05}")
                        st.caption(
                            f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.divider()

                # ========================================
                # SECTION 6: ALL AGGING COMPLAINT REPORT
                # ======================================== 
                st.header("📊 All Department Complaint Type Report")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

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

                        # Display success message with record count
                        st.success(f"✅ Successfully loaded {len(complaint_df):,} records.")

                        # Display dataframe
                        st.dataframe(
                            complaint_df,
                            use_container_width=True,
                            height=400
                        )

                        # Save DataFrame to BytesIO buffer
                        buffer = io.BytesIO()

                        # Create a copy and flatten MultiIndex columns if they exist
                        df_to_save = complaint_df.copy()

                        # Check if columns are MultiIndex and flatten them
                        if isinstance(df_to_save.columns, pd.MultiIndex):
                            # Flatten MultiIndex columns by joining levels with underscore
                            df_to_save.columns = [
                                '_'.join(map(str, col)).strip('_') for col in df_to_save.columns.values
                            ]

                        # Now save to Excel
                        df_to_save.to_excel(buffer, index=False, engine='openpyxl')
                        buffer.seek(0)

                        # Download button
                        st.download_button(
                            label="📥 Download Data as Excel",
                            data=buffer,
                            file_name="complaint_report.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                        logger.info("Tab 1: All Agging Complaint Report displayed successfully")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        st.divider()

                # ========================================
                # SECTION 7: POWER OUTAGE DURATION
                # ======================================== 

                st.header("X-Dashboard Shift wise Power Outage Duration Hour Analysis")

                # Date picker with key to prevent auto-rerun
                selected_date = st.date_input(
                    "Select Date",
                    value=datetime.today(),
                    help="Choose a date to analyze power outage durations",
                    key="outage_date_picker"
                )

                # Add a button to trigger the analysis
                if st.button("🔍 Restoration Duration Analysis Reports", key="analyze_button"):
                    if dataset_path is not None:
                        try:
                            # Show loading spinner
                            with st.spinner("Processing data..."):
                                pivot_df = fetch_close_power_outage_duration(
                                    dataset_path,
                                    selected_date
                                )

                                # Display the pivot table
                                st.subheader("Restoration Duration Analysis Reports")
                                st.dataframe(
                                    pivot_df,
                                    use_container_width=True,
                                    height=400
                                )
                                
                                st.info("Summary statistics not available")

                            st.success("✅ Data processing completed successfully!")

                        except ValueError as ve:
                            # Handle time format errors specifically
                            if "time data" in str(ve).lower() or "format" in str(ve).lower():
                                st.error("❌ Error: Time format is incorrect in the dataset. Please check the date/time columns format.")
                                st.info("💡 Expected format: YYYY-MM-DD HH:MM:SS or similar standard datetime format")
                            else:
                                st.error(f"❌ Data error: {str(ve)}")
                        
                        except pd.errors.ParserError as pe:
                            st.error("❌ Error: Unable to parse the data file. Please check if the file format is correct.")
                            st.info(f"Details: {str(pe)}")
                        
                        except FileNotFoundError:
                            st.error("❌ Error: Dataset file not found. Please check the file path.")
                        
                        except KeyError as ke:
                            st.error(f"❌ Error: Required column not found in dataset: {str(ke)}")
                            st.info("Please ensure all necessary columns exist in your dataset.")
                        
                        except Exception as e:
                            st.error(f"❌ Error processing file: {str(e)}")
                            st.info("💡 If this is a time format issue, please verify your datetime columns are in standard format (YYYY-MM-DD HH:MM:SS)")

                    else:
                        st.warning("⚠️ Dataset path is not configured. Please check your configuration.")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")




                # ========================================
                # ALL SECTIONS IN 5-COLUMN LAYOUT
                # ========================================

                st.divider()

                st.header("All Complaint Reports View")

                # Create 5 columns
                col1, col2, col3, col4, col5 = st.columns(5)

                # ========================================
                # COLUMN 1: SECTION 8 - All Agging Complaint Report
                # ========================================
                with col1:
                    st.subheader("📊Report 01")

                    if st.button("🔄 Load All Agging Complaint Report", key="load_all_agging_report"):
                        with st.spinner("Loading data..."):
                            df_pivot_06, error_06, status_code_06 = fetch_all_agging_complaint_report()

                        if error_06 is None and df_pivot_06 is not None:                    
                            styled_df = style_grand_total_dataframe(df_pivot_06)
                            st.dataframe(styled_df, use_container_width=True, height=400)
                            logger.info("Tab 1: All Agging Complaint Report displayed successfully")
                            st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            if status_code_06:
                                st.error(f"❌ Failed to fetch data. Status code: {status_code_06}")
                                logger.error(f"Tab 1: API request failed with status code {status_code_06}")
                            else:
                                st.error(f"❌ Error: {error_06}")
                                logger.error(f"Tab 1: Error - {error_06}")
                    else:
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # ========================================
                # COLUMN 2: SECTION 9 - Data All View
                # ========================================
                with col2:
                    st.subheader("📊 Report 02")

                    if st.button("🔄 Load Data All View Open Close Complaint Report", key="load_data_all_view"):
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
                # COLUMN 3: SECTION 10 - Generate All Agging Complaints Report
                # ========================================
                with col3:
                    st.subheader("📊 Report 03")

                    if st.button("🔄 Load Generate All Agging Complaint Report", key="generate_all_agging_report"):
                        with st.spinner("Generating report..."):
                            df_09, error_09, status_code_09 = generate_all_agging_complaint_report()

                        if error_09 is None and df_09 is not None:                    
                            st.dataframe(df_09, use_container_width=True, height=400)
                            logger.info("Tab 1: All Agging Complaint Report displayed successfully")
                            st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                        else:
                            if status_code_09:
                                st.error(f"❌ Failed to fetch data. Status code: {status_code_09}")
                                logger.error(f"Tab 1: API request failed with status code {status_code_09}")
                            else:
                                st.error(f"❌ Error: {error_09}")
                                logger.error(f"Tab 1: Error - {error_09}")
                    else:
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

                # ========================================
                # COLUMN 4: SECTION 11 - Agging Open Report
                # ========================================
                with col4:
                    st.subheader("📊 Report 04")

                    if st.button("🔄 Load Generate Agging Open Report", key="generate_agging_open_report"):
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
                # COLUMN 5: SECTION 12 - Open Complaints Reports
                # ========================================
                with col5:
                    st.subheader("📊 Report 05")
                    
                    if st.button("🔄 Load Open Complaints Report", key="load_open_complaints"):
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

                col1, col2 = st.columns([6, 1])

                with col1:
                    if st.button("🔄 Data All View"):
                        st.info("📊 Data All View")

                with col2:
                    if st.button("🔄 Refresh All", key="refresh_all_btn"):
                        st.cache_data.clear()
                        st.experimental_rerun()

            # ----------------------------------------------
            # TAB 2: DATA TABLE
            # ----------------------------------------------
            with tab2:
                st.subheader("Data Table")
                st.warning("🚧 This Project is under development.")

            # ----------------------------------------------
            # TAB 3: SUMMARY
            # ----------------------------------------------
            with tab3:
                st.subheader("Summary")
                st.warning("🚧 This Project is under development.")

            # ----------------------------------------------
            # TAB 4: DATASET INFORMATION
            # ----------------------------------------------
            with tab4:
                st.subheader("Dataset Information")
                st.warning("🚧 This Project is under development.")

            # ----------------------------------------------
            # TAB 5: VISUALIZATIONS
            # ----------------------------------------------
            with tab5:
                st.subheader("Data Visualizations")
                st.warning("🚧 This Project is under development.")

        # ==================================================
        # OTHER DASHBOARDS
        # ==================================================
        else:
            dashboard_type_clean = dashboard_type.encode('ascii', 'ignore').decode('ascii').strip()
            st.info(f"🚧 {dashboard_type} is under development. Coming soon!")
            logger.info("Dashboard under development | type=%s", dashboard_type_clean)

            # Placeholder content
            with st.expander("📋 Planned Features"):
                st.markdown(f"""
                ### {dashboard_type}

                This dashboard will include:
                - Advanced analytics features
                - Interactive visualizations
                - Real-time data processing
                - Machine learning models
                - Export capabilities

                **Status:** In Development  
                **Expected Release:** Q1 2025
                """)

        logger.info("Dashboard rendering completed successfully")

    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error("Dashboard rendering error | error=%s", error_msg)
        st.error("❌ An unexpected error occurred while rendering the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)
