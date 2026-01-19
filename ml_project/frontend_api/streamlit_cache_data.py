import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import os
import sys
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url
from ml_project.utils.helper import read_yaml
from ml_project.frontend_api.streamlit_analysis_helper import close_power_outage_duration
from ml_project.configs.config import DatasetNotFoundError, get_dataset_path


config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]

API_URL = "http://localhost:8000"
FASTAPI_URL = "http://localhost:8000"
FLASK_URL = "http://localhost:5000"

try:
    dataset_path = get_dataset_path("data/raw_path")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")

logger = get_logger(__name__)

# CACHED API FUNCTIONS
# =====================================================

try:
    @st.cache_data(ttl=600,show_spinner=True)
    def fetch_open_complaint_pivot():
        """Fetch open complaint pivot data from API - cached"""
        try:
            response = fastapi_api_request_url("/open_complaint_pivot")
            if response is not None and response.status_code == 200:
                response_data = response.json()
                if response_data:
                    return pd.DataFrame(response_data), None, response.status_code
                else:
                    return None, "No data available", response.status_code
            else:
                status = response.status_code if response else None
                return None, f"API error: {status}", status
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Error fetching open complaint pivot: {error_msg}")
            return None, error_msg, None


    @st.cache_data(ttl=600,show_spinner=True)
    def fetch_open_close_complaint_pivot():
        """Fetch open/close complaint pivot data from API - cached"""
        try:
            response = fastapi_api_request_url("/open_close_complaint_pivot")
            if response is not None and response.status_code == 200:
                response_data = response.json()
                if response_data:
                    return pd.DataFrame(response_data), None, response.status_code
                else:
                    return None, "No data available", response.status_code
            else:
                status = response.status_code if response else None
                return None, f"API error: {status}", status
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Error fetching open/close complaint pivot: {error_msg}")
            return None, error_msg, None


    @st.cache_data(ttl=600,show_spinner=True)
    def fetch_agging_open_pivot():
        """Fetch agging open pivot data from API - cached"""
        try:
            response = fastapi_api_request_url("/agging_open_pivot_dict")
            if response is not None and response.status_code == 200:
                response_data = response.json()
                if response_data:
                    return pd.DataFrame(response_data), None, response.status_code
                else:
                    return None, "No data available", response.status_code
            else:
                status = response.status_code if response else None
                return None, f"API error: {status}", status
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Error fetching agging open pivot: {error_msg}")
            return None, error_msg, None


    @st.cache_data(ttl=600,show_spinner=True)
    def fetch_agging_open_close_pivot():
        """Fetch agging open/close pivot data from API - cached"""
        try:
            response = fastapi_api_request_url("/agging_open_close_pivot_dict")
            if response is not None and response.status_code == 200:
                response_data = response.json()
                if response_data:
                    return pd.DataFrame(response_data), None, response.status_code
                else:
                    return None, "No data available", response.status_code
            else:
                status = response.status_code if response else None
                return None, f"API error: {status}", status
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Error fetching agging open/close pivot: {error_msg}")
            return None, error_msg, None
        

    @st.cache_data(ttl=600,show_spinner=True)
    def fetch_open_close_complaint_report():
        """Fetch open/close complaint report data from API - cached"""
        try:
            response = fastapi_api_request_url("/open_close_complaint_report")
            if response is not None and response.status_code == 200:
                response_data = response.json()
                if response_data:
                    return pd.DataFrame(response_data), None, response.status_code
                else:
                    return None, "No data available", response.status_code
            else:
                status = response.status_code if response else None
                return None, f"API error: {status}", status
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Error fetching open/close complaint report: {error_msg}")
            return None, error_msg, None
        

    @st.cache_data(ttl=600,show_spinner=True)
    def fetch_all_agging_complaint_report():
        """Fetch all agging complaint report data from API - cached"""
        try:
            response = fastapi_api_request_url("/all_agging_complaint_report")
            if response is not None and response.status_code == 200:
                response_data = response.json()
                if response_data:
                    return pd.DataFrame(response_data), None, response.status_code
                else:
                    return None, "No data available", response.status_code
            else:
                status = response.status_code if response else None
                return None, f"API error: {status}", status
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Error fetching all agging complaint report: {error_msg}")
            return None, error_msg, None
    
    @st.cache_data(ttl=600,show_spinner=True)
    def fetch_close_power_outage_duration(dataset_path, selected_date):
        """Fetch open/close complaint report data - cached"""
        try:
            result = close_power_outage_duration(dataset_path, selected_date)
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error fetching open/close complaint report: {error_msg}")
            return None
        
    @st.cache_data(ttl=600,show_spinner=True)
    def fetch_generate_month_wise_open_close_pivot_report(selected_month: str):
        """Fetch month wise open/close pivot report data from API - cached"""
        try:
            # Pass selected_month as query parameter
            response = fastapi_api_request_url(f"/month_wise_open_close_pivot_report?selected_month={selected_month}")
            if response is not None and response.status_code == 200:
                response_data = response.json()
                if response_data:
                    return pd.DataFrame(response_data), None, response.status_code
                else:
                    return None, "No data available", response.status_code
            else:
                status = response.status_code if response else None
                return None, f"API error: {status}", status
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Error fetching month wise open/close pivot report: {error_msg}")
            return None, error_msg, None
        
except Exception as e:
    error_msg = str(CustomException(e, sys))
    logger.error(f"Unhandled error in Streamlit dashboard Tab1 | error={error_msg}")
    st.error("❌ An unexpected error occurred while loading the dashboard.")
    with st.expander("Show error details"):
     st.code(error_msg)