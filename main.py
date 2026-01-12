import os
import io
import sys
import time
import requests
import pandas as pd
import numpy as np
from io import BytesIO
from pathlib import Path
from typing import Optional
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
from ml_project.utils.helper import read_yaml
from ml_project.frontend_api.streamlit_cache_data import fetch_close_power_outage_duration
from ml_project.frontend_api.streamlit_analysis_helper import close_power_outage_duration


config = read_yaml("ml_project/config/ml_project_config.yaml")
dataset_path = config["data"]["raw_path"]



# streamlit run main.py


from datetime import datetime
import pandas as pd  
import streamlit as st  


st.subheader("Power Outage Duration Analysis")

# Date picker
selected_date = st.date_input(
    "Select Date",
    value=datetime.today(),
    help="Choose a date to analyze power outage durations"
)

# Add a button to trigger the analysis
if st.button("🔍 Restoration Duration Analysis Reports"):
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