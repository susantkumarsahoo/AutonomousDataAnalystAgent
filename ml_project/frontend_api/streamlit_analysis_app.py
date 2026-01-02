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
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
logger = get_logger(__name__)


try:
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

        # Page Title
        st.title(dashboard_type)

        # ==================================================
        # ANALYSIS DASHBOARD
        # ==================================================
        if dashboard_type == "Analysis Dashboard":
            
            df = None
            if uploaded_file:
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_excel(dataset_path)
            
            if df is None:
                st.warning("⚠️ No data available. Please upload a file or check the default dataset path.")
                return

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
                # display_complaint_information()
                st.warning("🚧 This Project is under development.")

                # fastapi_api_request_url("/healthcheck")
                response = fastapi_api_request_url("/healthcheck", timeout=30)
                api_data = response.json()
                st.write("API Status:", api_data.get("status"))
               
                st.divider()
                # flask_api_request_url("/healthcheck")
                response = flask_api_request_url("/healthcheck", timeout=30)
                api_data = response.json()
                st.write("API Status:", api_data.get("status"))

                st.divider()
                # Complaint overview dashboard
                logger.info("Complaint overview dashboard rendered.")
                logger.info("Tab 1: Completed successfully.")

            # ----------------------------------------------
            # TAB 2: DATA TABLE
            # ----------------------------------------------
            with tab2:
                #display_missing_values_report()
                # under development
                st.warning("🚧 This Project is under development.")


            # ----------------------------------------------
            # TAB 3: SUMMARY
            # ----------------------------------------------
            with tab3:
                st.subheader("Summary")
                # under development
                st.warning("🚧 This Project is under development.")


            # ----------------------------------------------
            # TAB 4: DATASET INFORMATION
            # ----------------------------------------------
            with tab4:
                st.subheader("Dataset Information")
                # under development
                st.warning("🚧 This Project is under development.")

            # ----------------------------------------------
            # TAB 5: VISUALIZATIONS
            # ----------------------------------------------
            with tab5:
                st.subheader("Data Visualizations")
                # under development
                st.warning("🚧 This Project is under development.")


            # ----------------------------------------------
            # WEB APP: UNDER DEVELOPMENT
            # ----------------------------------------------

        else:
            st.info(f"🚧 {dashboard_type} is under development. Coming soon!")
            
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
except Exception as e:
    logger.error(str(CustomException(e, sys)))           



 