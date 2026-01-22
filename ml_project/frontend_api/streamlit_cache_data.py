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
    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def fetch_open_complaint_pivot():
        """Fetch open complaint pivot data from API - cached"""
        try:
            response = fastapi_api_request_url("/open_complaint_pivot")
            if response is not None and response.status_code == 200:
                response_data = response.json()
                if response_data:
                    # Convert to DataFrame
                    df = pd.DataFrame(response_data)
                    
                    return df, None, response.status_code
                else:
                    return None, "No data available", response.status_code
            else:
                status = response.status_code if response else None
                return None, f"API error: {status}", status
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Error fetching open complaint pivot: {error_msg}")
            return None, error_msg, None

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
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


    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
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


    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
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
        

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
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
        

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
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
    
    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def fetch_close_power_outage_duration(dataset_path, selected_date):
        """Fetch open/close complaint report data - cached"""
        try:
            result = close_power_outage_duration(dataset_path, selected_date)
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error fetching open/close complaint report: {error_msg}")
            return None
        
    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
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
        

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def fetch_generate_quarter_wise_agging_pivot_report(
        start_year: str,
        start_quarter: str,
        end_year: str,
        end_quarter: str
    ):    
        """Fetch quarter wise agging pivot report data from API - cached"""
        try:
            # Remove dataset_path from query parameters - it's handled by the API
            response = fastapi_api_request_url(
                f"/quarter_wise_open_close_report?start_year={start_year}&start_quarter={start_quarter}&end_year={end_year}&end_quarter={end_quarter}"
            )
            
            if response is not None and response.status_code == 200:
                response_data = response.json()
                if response_data:
                    # Convert the dictionary back to DataFrame
                    df = pd.DataFrame.from_dict(response_data)
                    return df, None, response.status_code
                else:
                    return None, "No data available", response.status_code
            else:
                status = response.status_code if response else None
                return None, f"API error: {status}", status
                
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error(f"Error fetching quarter wise agging pivot report: {error_msg}")
            return None, error_msg, None



    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def fetch_generate_finance_year_wise_open_close_pivot_report(start_year: str, start_date: str, end_year: str, end_date: str):
            """Fetch year wise open/close pivot report data from API - cached"""
            try:
                # Pass parameters as query parameters
                response = fastapi_api_request_url(f"/year_wise_open_close_pivot_report?start_year={start_year}&start_date={start_date}&end_year={end_year}&end_date={end_date}")
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
                logger.error(f"Error fetching year wise open/close pivot report: {error_msg}")
                return None, error_msg, None



    # Load Excel data (no change needed)
    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def load_excel_data(file_path):
        """Load and cache Excel data"""
        df = pd.read_excel(file_path)
        df['DATE'] = pd.to_datetime(df['DATE'])
        return df

    # Filter financial year data (NEW - replaces get_month_data)
    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_financial_year_data(df, selected_fy):
        """Filter data for selected financial year"""
        # Extract start and end year from FY string (e.g., "2023-24")
        start_year = int(selected_fy.split('-')[0])
        end_year = int(selected_fy.split('-')[1])
        
        # Financial year runs from April to March
        fy_start = pd.Timestamp(f'{start_year}-04-01')
        fy_end = pd.Timestamp(f'{end_year + 2000}-03-31')
        
        return df[(df['DATE'] >= fy_start) & (df['DATE'] <= fy_end)]

    # Enhanced report functions for Financial Year
    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def generate_complaint_report_fy(fy_df):
        result = fy_df['COMPLAINT TYPE'].value_counts().reset_index()
        result.columns = ['Complaint Type', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def generate_date_report_fy(fy_df):
        result = fy_df['DATE'].value_counts().sort_index().reset_index()
        result.columns = ['Date', 'Count']
        result['Day of Week'] = pd.to_datetime(result['Date']).dt.day_name()
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def generate_shift_duty_report_fy(fy_df):
        result = fy_df['SHIFT DUTY'].value_counts().reset_index()
        result.columns = ['Shift Duty', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def generate_qrc_data_fy(fy_df):
        result = fy_df['QUERY/REQUEST/COMPLAINT'].value_counts().reset_index()
        result.columns = ['QRC Type', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_complaint_number_data_fy(fy_df):
        result = fy_df['COMPLAINT NUMBER'].value_counts().reset_index()
        result.columns = ['Complaint Number', 'Count']
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_section_data_fy(fy_df):
        result = fy_df['SECTION'].value_counts().reset_index()
        result.columns = ['Section', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_subdivision_data_fy(fy_df):
        result = fy_df['SUB-DIVISION'].value_counts().reset_index()
        result.columns = ['Sub-Division', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_division_data_fy(fy_df):
        result = fy_df['DIVISION'].value_counts().reset_index()
        result.columns = ['Division', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_circle_data_fy(fy_df):
        result = fy_df['CIRCLE'].value_counts().reset_index()
        result.columns = ['Circle', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_consumer_number_data_fy(fy_df):
        result = fy_df['CONSUMER NUMBER'].value_counts().reset_index()
        result.columns = ['Consumer Number', 'Count']
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_mobile_number_data_fy(fy_df):
        result = fy_df['MOBILE NUMB'].value_counts().reset_index()
        result.columns = ['Mobile Number', 'Count']
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_dept_data_fy(fy_df):
        result = fy_df['DEPT'].value_counts().reset_index()
        result.columns = ['Department', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_status_data_fy(fy_df):
        result = fy_df['CLOSED/OPEN'].value_counts().reset_index()
        result.columns = ['Status', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_complainant_name_data_fy(fy_df):
        result = fy_df['COMPLAINANT NAME'].value_counts().reset_index()
        result.columns = ['Complainant Name', 'Count']
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_pscc_data_fy(fy_df):
        result = fy_df['PSCC/FG/TO'].value_counts().reset_index()
        result.columns = ['PSCC Type', 'Count']
        result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
        return result

    @st.cache_data(ttl=600, show_spinner="Fetching Data... Please wait ⏳")
    def get_minute_data_fy(fy_df):
        result = fy_df['MINUTE'].value_counts().reset_index()
        result.columns = ['Minute', 'Count']
        return result






except Exception as e:
    error_msg = str(CustomException(e, sys))
    logger.error(f"Unhandled error in Streamlit dashboard Tab1 | error={error_msg}")
    st.error("❌ An unexpected error occurred while loading the dashboard.")
    with st.expander("Show error details"):
     st.code(error_msg)

