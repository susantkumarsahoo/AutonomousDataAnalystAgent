import os
import sys
import time
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

from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException

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
                # Add a header
                st.header("📈 Complaint Overview")
                
                # Add a warning message
                st.warning("🚧 This Project is under development.")
                
                # Add descriptive header
                st.markdown("""
                ### Open Complaints Overview
                This dashboard provides a real-time view of open complaints categorized by type and status. 
                The pivot table below summarizes active complaint cases across different categories.
                """)
                
                # Add a divider
                st.divider()
                
                response = fastapi_api_request_url("/open_complaint_pivot")

                if response is not None:
                    try:
                        response_data = response.json()
                        
                        if response_data:  # Check if data exists
                            df = pd.DataFrame(response_data)
                                                        
                            # **IMPROVEMENT: Style the Grand_Total row**
                            st.subheader("📊 Open Complaints Pivot Table")
                            st.caption("Grand Total row is highlighted in red for easy identification")
                            
                            styled_df = df.style.apply(
                                lambda x: ['background-color: #ff0000; font-weight: bold' if x.name == len(df)-1 else '' for _ in x],
                                axis=1
                            ) if 'Grand_Total' in df['COMPLAINT TYPE'].values else df
                            
                            st.dataframe(
                                styled_df,
                                use_container_width=True,
                                height=400
                            )
                                                       
                            logger.info("Tab 1: Complaint overview displayed successfully")
                        else:
                            st.warning("⚠️ No data available at the moment. Please try refreshing or check back later.")
                            logger.warning("Tab 1: Empty response data")
                            
                    except Exception as e:
                        st.error(f"❌ Failed to parse response: {e}")
                        st.info("Please contact support if this issue persists.")
                        logger.error(f"Tab 1: Error parsing response - {e}")
                else:
                    st.error("❌ No response from API")
                    st.info("The API service may be temporarily unavailable. Please try again in a few moments.")
                    logger.error("Tab 1: API returned None")
                
                # Add footer with last update time
                st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")


                st.divider()

                # Open Close Complaints Pivot Table
                st.subheader("📊 Open/Close Complaints Pivot Table")
                st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                response_01 = fastapi_api_request_url("/open_close_complaint_pivot")  # Make sure using FastAPI

                if response_01 is not None:
                    try:
                        response_data = response_01.json()
                        
                        if response_data:  # Check if data exists
                            df = pd.DataFrame(response_data)
                            
                            # Apply styling if Grand_Total row exists
                            if 'Grand_Total' in df['COMPLAINT TYPE'].values:
                                def highlight_grand_total(row):
                                    if row['COMPLAINT TYPE'] == 'Grand_Total':
                                        return ['background-color: #ff0000; color: white; font-weight: bold'] * len(row)
                                    else:
                                        return [''] * len(row)
                                
                                styled_df = df.style.apply(highlight_grand_total, axis=1)
                            else:
                                styled_df = df
                                                        
                            st.dataframe(
                                styled_df,
                                use_container_width=True,
                                height=400
                            )
                        
                            logger.info("Tab 1: Open Close Complaints Pivot Table displayed successfully")
                        else:
                            st.warning("⚠️ No data available at the moment. Please try refreshing or check back later.")
                            logger.warning("Tab 1: Empty response data")
                            
                        # Add footer with last update time
                        st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")


                        # Add a divider
                        st.divider()
                        # Add a header
                        st.header("📊 Agging Open Complaints Pivot Table")
                        st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                        @st.cache_data(ttl=300)  # Cache for 5 minutes
                        def fetch_agging_open_data():
                            return fastapi_api_request_url("/agging_open_pivot_dict")

                        with st.spinner("Loading data..."):
                            response_02 = fetch_agging_open_data()

                        if response_02 is not None:
                            response_data = response_02.json()
                            if response_data:
                                df = pd.DataFrame(response_data)
                                
                                # Store in session state
                                st.session_state['agging_open_df'] = df
                                
                                # Apply styling if Grand_Total row exists
                                if 'Grand_Total' in df['COMPLAINT TYPE'].values:
                                    def highlight_grand_total(row):
                                        if row['COMPLAINT TYPE'] == 'Grand_Total':
                                            return ['background-color: #ff0000; color: white; font-weight: bold'] * len(row)
                                        else:
                                            return [''] * len(row)
                                    
                                    styled_df = df.style.apply(highlight_grand_total, axis=1)
                                    st.dataframe(styled_df, use_container_width=True, height=400)
                                else:
                                    st.dataframe(df, use_container_width=True, height=400)
                                
                                logger.info("Tab 1: Agging Open Complaints Pivot Table displayed successfully")
                            else:
                                st.warning("⚠️ No data available at the moment. Please try refreshing or check back later.")
                                logger.warning("Tab 1: Empty response data")
                            
                            # Add footer with last update time
                            st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")


                        # Add a divider
                        st.divider()
                        # get("/agging_open_close_pivot_dict")
                        st.header("📊 Agging Open/Close Complaints Pivot Table")
                        st.caption("View complaints categorized by type, department, and status (Open/Closed)")

                        with st.spinner("Loading data..."):
                            response_03 = fastapi_api_request_url("/agging_open_close_pivot_dict")

                        if response_03 is not None:
                            response_data = response_03.json()
                            if response_data:
                                df = pd.DataFrame(response_data)
                                
                                # Store in session state
                                st.session_state['agging_open_close_df'] = df

                                # Apply styling if Grand_Total row exists
                                if 'Grand_Total' in df['COMPLAINT TYPE'].values:
                                    def highlight_grand_total(row):
                                        if row['COMPLAINT TYPE'] == 'Grand_Total':
                                            return ['background-color: #ff0000; color: white; font-weight: bold'] * len(row)
                                        else:
                                            return [''] * len(row)
                                    
                                    styled_df = df.style.apply(highlight_grand_total, axis=1)
                                    st.dataframe(styled_df, use_container_width=True, height=400)
                                else:
                                    st.dataframe(df, use_container_width=True, height=400)

                                logger.info("Tab 1: Agging Open/Close Complaints Pivot Table displayed successfully")
                            else:
                                st.warning("⚠️ No data available at the moment. Please try refreshing or check back later.")
                                logger.warning("Tab 1: Empty response data")
                            
                            # Add footer with last update time
                            st.caption(f"Last updated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

                        st.divider()
                           
                    except Exception as e:
                        st.error(f"❌ Failed to parse response: {e}")
                        st.info("Please contact support if this issue persists.")
                        logger.error(f"Tab 1: Error parsing response - {e}")
                        import traceback
                        st.code(traceback.format_exc())  # Show detailed error for debugging
                else:
                    st.error("❌ No response from API")
                    st.info("The API endpoint may not be registered. Check FastAPI router.")
                    logger.error("Tab 1: API returned None for open_close_complaint_pivot")

                st.divider()

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


# streamlit_analysis_app.py
 