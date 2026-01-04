import sys
import os
import streamlit as st
import requests
import pandas as pd
from datetime import datetime
from pathlib import Path
from ml_project.frontend_api.streamlit_analysis_app import analysis_dashboard
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url, check_api_status
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException

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


try:
    # -----------------------------------------------------------------------------
    # Page Configuration
    # -----------------------------------------------------------------------------
    st.set_page_config(
        page_title="Twitter Analytics Dashboard",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # -----------------------------------------------------------------------------
    # SIDEBAR
    # -----------------------------------------------------------------------------
    with st.sidebar:
        st.header("🧭 Navigation")

        dashboard_type = st.radio(
            "Select Dashboard",
            [
                "📈 Analysis Dashboard",
                "📊 Mathematics & Statistical Analysis",
                "🔮 Twitter Flow Prediction",
                "🕒 Time Series Analysis",
                "📝 Sentiment Analysis",
                "🗂️ CRM Database",
                "🤖 AI Chatbot"
            ],
            label_visibility="collapsed",
        )

        st.divider()

        st.header("📁 Data Source")

        uploaded_file = st.file_uploader(
            "Upload your data",
            type=["csv", "xlsx", "json"]
        )

        # Define save directory
        SAVE_DIR = "data/raw"

        # Create directory if it doesn't exist
        os.makedirs(SAVE_DIR, exist_ok=True)

        if uploaded_file is not None:
            try:
                # Remove all previous files in the directory
                for file in os.listdir(SAVE_DIR):
                    file_path_to_remove = os.path.join(SAVE_DIR, file)
                    try:
                        if os.path.isfile(file_path_to_remove):
                            os.remove(file_path_to_remove)
                            logger.info("Removed previous file | path=%s", file_path_to_remove)
                    except Exception as e:
                        logger.error("Error removing file | path=%s | error=%s", file_path_to_remove, str(e))
                
                # Full path where new file will be saved
                file_path = os.path.join(SAVE_DIR, uploaded_file.name)

                # Save new file
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())

                logger.info("New file saved | path=%s", file_path)
                st.success(f"✅ '{uploaded_file.name}' uploaded and saved to `{SAVE_DIR}/`")
            
            except Exception as e:
                st.error(f"❌ Error uploading file: {str(e)}")
                logger.error("File upload error | error=%s", str(e))
 



        st.divider()
    
        st.header("🔌 API Status")
        
        try:
            is_connected, api_data = check_api_status()
        except Exception as e:
            is_connected = False
            api_data = {"message": str(e), "dataset_path": "Not available"}
            logger.error("API status check error | error=%s", str(e))
        
        # Set dataset_path from API response or default
        dataset_path = api_data.get("dataset_path", "Not available")
        
        if is_connected:
            st.success("✅ API Connected")
            if api_data.get("dataset_available"):
                st.info("📂 Dataset available")
            else:
                st.warning("⚠️ Dataset not found")
        else:
            st.error("❌ API Disconnected")
            with st.expander("Show error details"):
                st.code(api_data.get("message", "Unknown error"))
    
        if st.button("🔄 Refresh API Status", use_container_width=True):
            logger.info("API status refresh triggered")
            st.rerun()

        # API Service Status
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.subheader("Fst1 Terminal API")
            try:
                response = fastapi_api_request_url("/healthcheck", timeout=30)
                if response and response.json().get("status") == "healthy":
                    st.badge("✅ Healthy", color="green")
                    logger.info("FastAPI healthcheck successful")
                else:
                    st.badge("❌ Unhealthy", color="red")
                    logger.error("FastAPI healthcheck failed")
            except Exception as e:
                st.badge("❌ Error", color="red")
                logger.error("FastAPI healthcheck error | error=%s", str(e))
        
        with col2:
            st.subheader("Flk2 Terminal API")
            try:
                response = flask_api_request_url("/healthcheck", timeout=30)
                if response and response.json().get("status") == "healthy":
                    st.badge("✅ Healthy", color="green")
                    logger.info("Flask API healthcheck successful")
                else:
                    st.badge("❌ Unhealthy", color="red")
                    logger.error("Flask API healthcheck failed")
            except Exception as e:
                st.badge("❌ Error", color="red")
                logger.error("Flask API healthcheck error | error=%s", str(e))

        with col3:
            st.subheader("Stm3 Terminal API")
            try:
                st.badge("✅ Healthy", color="green")
                logger.info("Streamlit healthcheck successful")
            except Exception as e:
                st.badge("❌ Error", color="red")
                logger.error("Streamlit healthcheck error | error=%s", str(e))


        st.divider()
    
        with st.expander("ℹ️ Dashboard Info"):
            st.info(
                f"""
                **Version:** 2.0  
                **Last Updated:** {datetime.now().strftime("%Y-%m-%d %H:%M")}  
                **Status:** {"Connected" if is_connected else "Disconnected"}  
                **Dataset:** {dataset_path}
                """
            )

    # -----------------------------------------------------------------------------
    # MAIN CONTENT
    # -----------------------------------------------------------------------------
    if not is_connected:
        st.title("⚠️ API Connection Required")
        st.error("Cannot connect to FastAPI backend. Please ensure the server is running.")
        st.info("""
        **Troubleshooting Steps:**
        1. Ensure FastAPI server is running on http://localhost:8000
        2. Check if the port 8000 is not blocked
        3. Verify API endpoint: /healthcheck
        4. Check if the backend server is started
        """)
        logger.warning("Streamlit blocked due to API unavailability")
    
    else:
        try:
            # Strip emoji from dashboard_type for logging to avoid encoding issues
            dashboard_type_clean = dashboard_type.encode('ascii', 'ignore').decode('ascii').strip()
            logger.info("Rendering dashboard | type=%s", dashboard_type_clean)
            
            # Render the selected dashboard
            analysis_dashboard(dashboard_type, dataset_path, uploaded_file)
            
            logger.info("Streamlit dashboard rendered successfully")
    
        except Exception as e:
            error_msg = str(CustomException(e, sys))
            logger.error("Unhandled error in Streamlit dashboard | error=%s", error_msg)
            st.error("❌ An unexpected error occurred while loading the dashboard.")
            with st.expander("Show error details"):
                st.code(error_msg)
    
except Exception as e:
    error_msg = str(CustomException(e, sys))
    logger.error("Critical application error | error=%s", error_msg)
    st.error("❌ Critical application error occurred.")
    st.code(error_msg)

# python app_runner.py