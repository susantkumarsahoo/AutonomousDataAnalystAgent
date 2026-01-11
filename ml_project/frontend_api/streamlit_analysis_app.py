import os
import sys
import time
import io
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
from ml_project.frontend_api.streamlit_analysis_helper import generate_all_agging_complaint_report,style_grand_total_dataframe,close_power_outage_duration
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.frontend_api.streamlit_cache_data import (
    fetch_open_complaint_pivot,
    fetch_open_close_complaint_pivot,
    fetch_agging_open_pivot,
    fetch_agging_open_close_pivot,
    fetch_open_close_complaint_report,
    fetch_all_agging_complaint_report )

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







                        st.subheader("Power Outage Duration Analysis")
                        
                        # Date picker
                        selected_date = st.date_input(
                            "Select Date",
                            value=datetime.today(),
                            help="Choose a date to analyze power outage durations"
                        )
                        

                        if dataset_path is not None:
                            try:
                                # Show loading spinner
                                with st.spinner('Processing data...'):
                                    # Get pivot table - pass uploaded_file and selected_date
                                    pivot_df = close_power_outage_duration(dataset_path, selected_date)
                                
                                # Display success message
                                st.success(f"✅ Data processed successfully for {selected_date}")
                                
                                # Checkbox to show raw data
                                show_raw_data = st.checkbox("📋 Show Raw Data", value=False)
                                
                                if show_raw_data:
                                    st.subheader("Raw Dataset")
                                    raw_df = pd.read_excel(uploaded_file)
                                    st.dataframe(
                                        raw_df,
                                        use_container_width=True,
                                        height=300
                                    )
                                    st.divider()
                                
                                # Display the pivot table
                                st.subheader("Duration Analysis Table")
                                st.dataframe(
                                    pivot_df,
                                    use_container_width=True,
                                    height=400
                                )
                                
                                # Download button for Excel file
                                from io import BytesIO
                                
                                # Create Excel file in memory
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                                    pivot_df.to_excel(writer, sheet_name='Power Outage Duration')
                                excel_data = output.getvalue()
                                
                                st.download_button(
                                    label="📥 Download as Excel",
                                    data=excel_data,
                                    file_name=f"power_outage_duration_{selected_date}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                                
                                # Optional: Show summary statistics
                                with st.expander("📊 Summary Statistics"):
                                    total_complaints = pivot_df.loc[('Grand Total', '', ''), :].sum()
                                    st.metric("Total Complaints", int(total_complaints))
                                    
                            except Exception as e:
                                st.error(f"❌ Error processing file: {str(e)}")
                                st.info("Please ensure your Excel file has the required columns: DATE, COMPLAINT TYPE, COMPLAINT RECEIVED TIME, FINAL RESPONSE TIME, DIVISION, SUB-DIVISION, SHIFT DUTY, CLOSED/OPEN")
                        else:
                            st.info("👆 Please upload an Excel file to begin analysis")




                    
                        
                # ========================================
                # SECTION 7: ALL AGGING COMPLAINT REPORT
                # ========================================
                st.header("📊 All Agging Complaint Report")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                # Add a button to trigger data loading
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
