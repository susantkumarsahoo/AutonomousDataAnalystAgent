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
logger = get_logger(__name__)

# CACHED API FUNCTIONS
# =====================================================

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
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


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
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


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
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


@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
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