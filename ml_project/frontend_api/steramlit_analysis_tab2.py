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
import pandas as pd
import plotly.express as px
from datetime import datetime
import plotly.graph_objects as go
from datetime import datetime, timedelta
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url
from ml_project.backend_api.fastapi_analysis_helper import*
from ml_project.frontend_api.streamlit_analysis_helper import*
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.frontend_api.streamlit_cache_data import fetch_generate_month_wise_open_close_pivot_report
from ml_project.frontend_api.streamlit_analysis_helper import (
generate_month_wise_open_clode_pivot_report,
generate_complaint_report,
generate_date_report,
generate_shift_duty_report,

)


config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]

from ml_project.configs.config import DatasetNotFoundError, get_dataset_path

try:
    dataset_path = get_dataset_path("data/raw_path")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")


# Fix Unicode encoding for Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except AttributeError:
        pass  # Python version doesn't support reconfigure

logger = get_logger(__name__)


# ========================================
# MAIN TAB2 FUNCTION
# ========================================

def streamlit_analysis_tab2(tab2, dataset_path, logger):
    """
    Renders all content for Tab 2 including analysis and reports.
    
    Parameters:
    -----------
    tab2 : streamlit.tabs
        The Streamlit tab container where content will be rendered
    dataset_path : str
        Path to the dataset file
    logger : logging.Logger
        Logger instance for logging operations
    """
    try:
        with tab2:
            # ========================================
            # SECTION 1: MONTH WISE OPEN/CLOSE COMPLAINTS PIVOT
            # ========================================
            st.header("📊 Month Wise Open/Close Complaints Report")
            st.caption("Select year and month to view complaints report")

            # Initialize session state for selected year and month
            if "selected_year_tab2" not in st.session_state:
                st.session_state.selected_year_tab2 = datetime.today().year
            
            if "selected_month_tab2" not in st.session_state:
                st.session_state.selected_month_tab2 = datetime.today().month
            
            # Initialize flag to track if report should be generated
            if "generate_report_tab2" not in st.session_state:
                st.session_state.generate_report_tab2 = False

            # Create columns for Year and Month selection
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                # Year selector
                current_year = datetime.today().year
                selected_year = st.selectbox(
                    "Select Year",
                    options=list(range(current_year - 5, current_year + 1)),
                    index=list(range(current_year - 5, current_year + 1)).index(
                        st.session_state.selected_year_tab2
                    ),
                    key="year_selector_tab2",
                    help="Choose the year"
                )
            
            with col2:
                # Month selector
                months = {
                    1: "January", 2: "February", 3: "March", 4: "April",
                    5: "May", 6: "June", 7: "July", 8: "August",
                    9: "September", 10: "October", 11: "November", 12: "December"
                }
                selected_month_num = st.selectbox(
                    "Select Month",
                    options=list(months.keys()),
                    format_func=lambda x: months[x],
                    index=st.session_state.selected_month_tab2 - 1,
                    key="month_selector_tab2",
                    help="Choose the month"
                )
            
            with col3:
                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button(
                    "📊 Generate Report",
                    type="primary",
                    use_container_width=True,
                    key="generate_report_button_tab2"
                ):
                    # Update session state when button is clicked
                    st.session_state.selected_year_tab2 = selected_year
                    st.session_state.selected_month_tab2 = selected_month_num
                    st.session_state.generate_report_tab2 = True

            # Convert to string format 'YYYY-MM'
            month_str = f"{st.session_state.selected_year_tab2}-{st.session_state.selected_month_tab2:02d}"
            
            # Display selected month
            st.info(
                f"📅 Selected Period: **{months[st.session_state.selected_month_tab2]} "
                f"{st.session_state.selected_year_tab2}** (Format: {month_str})"
            )

            # Only generate report if button was clicked
            if st.session_state.generate_report_tab2:
                with st.spinner("Loading data..."):
                    df, error, status_code = fetch_generate_month_wise_open_close_pivot_report(month_str)
                
                if error is None and df is not None:
                    st.success("✅ Report generated successfully!")
                    st.dataframe(df, use_container_width=True, height=400)
                    logger.info(f"Tab 2: Month wise report generated successfully | month={month_str}")
                    
                    # Store last generated time
                    st.session_state.last_report_time_tab2 = pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                    
                    # Reset flag after successful generation
                    st.session_state.generate_report_tab2 = False
                    
                else:
                    if status_code:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                        logger.error(f"Tab 2: API request failed | status_code={status_code}")
                    else:
                        st.error(f"❌ Error: {error}")
                        logger.error(f"Tab 2: Error - {error}")
                    
                    # Reset flag after error
                    st.session_state.generate_report_tab2 = False

            # Show last loaded timestamp
            if "last_report_time_tab2" in st.session_state:
                st.caption(f"Last loaded: {st.session_state.last_report_time_tab2}")
            else:
                st.caption("Last loaded: Not generated yet")
                
                
            

            st.divider()

            # Initialize session state
            if 'report_generated' not in st.session_state:
                st.session_state.report_generated = False
            if 'selected_month' not in st.session_state:
                st.session_state.selected_month = None
            if 'dataset_path' not in st.session_state:
                st.session_state.dataset_path = None

            # Load and cache the Excel data ONCE
            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def load_excel_data(file_path):
                """Load and cache Excel data"""
                df = pd.read_excel(file_path)
                df['DATE'] = pd.to_datetime(df['DATE'])
                return df

            # Filter monthly data (cached)
            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_month_data(df, selected_month):
                """Filter data for selected month"""
                return df[df['DATE'].dt.to_period('M') == selected_month]

            # Reports now take month_df directly (no file read)
            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def generate_complaint_report(month_df):
                return month_df['COMPLAINT TYPE'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def generate_date_report(month_df):
                return month_df['DATE'].value_counts().sort_index()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def generate_shift_duty_report(month_df):
                return month_df['SHIFT DUTY'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def generate_monthly_qrc_data(month_df):
                return month_df['QUERY/REQUEST/COMPLAINT'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_section_data(month_df):
                return month_df['SECTION'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_subdivision_data(month_df):
                return month_df['SUB-DIVISION'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_circle_data(month_df):
                return month_df['CIRCLE'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_consumer_number_data(month_df):
                return month_df['CONSUMER NUMBER'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_mobile_number_data(month_df):
                return month_df['MOBILE NUMB'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_dept_data(month_df):
                return month_df['DEPT'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_status_data(month_df):
                return month_df['CLOSED/OPEN'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_pscc_data(month_df):
                return month_df['PSCC/FG/TO'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_minute_data(month_df):
                return month_df['MINUTE'].value_counts()

            @st.cache_data(ttl=600, max_entries=20, show_spinner=True, persist=True)
            def get_monthly_remarks_analysis(month_df):
                """Analyze REMARKS column for patterns"""
                # Create a copy to avoid modifying cached data
                temp_df = month_df.copy()
                
                # Ensure REMARKS column exists and is string type
                if 'REMARKS' not in temp_df.columns:
                    return {
                        'Appreciation Tweets': 0,
                        'Awaited Consumer': 0,
                        '5-digit Numbers': 0,
                        'Total Remarks': 0
                    }
                
                # Convert to string and handle NaN
                temp_df['REMARKS'] = temp_df['REMARKS'].fillna('').astype(str)
                
                appreciation_count = temp_df['REMARKS'].str.contains("Appreciation Tweet", case=False, na=False).sum()
                awaited_consumer_count = temp_df['REMARKS'].str.contains("Awaited consumer", case=False, na=False).sum()
                number_count = temp_df['REMARKS'].str.contains(r"\b\d{5}\b", na=False).sum()

                return {
                    'Appreciation Tweets': int(appreciation_count),
                    'Awaited Consumer': int(awaited_consumer_count),
                    '5-digit Numbers': int(number_count),
                    'Total Remarks': len(temp_df)
                }


            # Main App
            st.header("📊 Month Wise Complaint Analysis Dashboard")

            # Define your dataset path here

            if dataset_path is not None:
                # Save to session state safely
                if "dataset_path" not in st.session_state or st.session_state.dataset_path != dataset_path:
                    st.session_state.dataset_path = dataset_path
                    st.session_state.report_generated = False
                
                try:
                    df = load_excel_data(dataset_path)
                    
                    # Month and year selectors with unique keys
                    col_month, col_year = st.columns(2)
                    with col_month:
                        month = st.selectbox(
                            "Select Month", 
                            list(range(1, 13)), 
                            format_func=lambda x: pd.to_datetime(str(x), format="%m").strftime("%B"),
                            key='tab2_month_selector'
                        )
                    with col_year:
                        year = st.selectbox(
                            "Select Year", 
                            list(range(2020, 2031)),
                            key='tab2_year_selector'
                        )

                    # Format selected month-year as Period
                    selected_month = pd.Period(f"{year}-{month:02d}", freq='M')
                    
                    # Store in session state
                    if st.session_state.selected_month != str(selected_month):
                        st.session_state.selected_month = str(selected_month)
                        st.session_state.report_generated = False

                    # Generate Report Button
                    generate_button = st.button("🔍 Generate Report", type="primary", use_container_width=True, key='tab2_generate_btn')

                    # Generate report when button clicked or if already generated
                    if generate_button or st.session_state.report_generated:
                        if generate_button:
                            st.session_state.report_generated = True
                        
                        try:
                            with st.spinner("Generating comprehensive reports..."):
                                # Generate all reports using cached functions
                                month_df = get_month_data(df, selected_month)

                                complaint_report        = generate_complaint_report(month_df)
                                date_report             = generate_date_report(month_df)
                                shift_report            = generate_shift_duty_report(month_df)
                                qrc_report              = generate_monthly_qrc_data(month_df)
                                section_report          = get_monthly_section_data(month_df)
                                subdivision_report      = get_monthly_subdivision_data(month_df)
                                circle_report           = get_monthly_circle_data(month_df)
                                consumer_number_report  = get_monthly_consumer_number_data(month_df)
                                mobile_number_report    = get_monthly_mobile_number_data(month_df)
                                dept_report             = get_monthly_dept_data(month_df)
                                status_report           = get_monthly_status_data(month_df)
                                pscc_report             = get_monthly_pscc_data(month_df)
                                minute_report           = get_monthly_minute_data(month_df)
                                remarks_report          = get_monthly_remarks_analysis(month_df)

                                if len(month_df) == 0:
                                    st.warning(f"⚠️ No data found for {selected_month.strftime('%B %Y')}")
                                else:
                                    # Summary Metrics Section
                                    st.subheader("📈 Summary Metrics")
                                    metric_col1, metric_col2, metric_col3, metric_col4, metric_col5, metric_col6 = st.columns(6)
                                    
                                    with metric_col1:
                                        st.metric("Total Records", len(month_df))
                                    with metric_col2:
                                        st.metric("Complaint Types", month_df['COMPLAINT TYPE'].nunique())
                                    with metric_col3:
                                        st.metric("Unique Dates", month_df['DATE'].nunique())
                                    with metric_col4:
                                        st.metric("Shift Types", month_df['SHIFT DUTY'].nunique())
                                    with metric_col5:
                                        closed_count = status_report.get('CLOSED', 0) if len(status_report) > 0 else 0
                                        total_count = status_report.sum() if len(status_report) > 0 else 1
                                        closure_rate = (closed_count / total_count * 100) if total_count > 0 else 0
                                        st.metric("Closure Rate", f"{closure_rate:.1f}%")
                                    with metric_col6:
                                        if len(month_df) > 0 and 'MINUTE' in month_df.columns:
                                            frt_value = month_df['MINUTE'].sum() / len(month_df)
                                            st.metric("FRT Report", round(frt_value, 2))
                                        else:
                                            st.metric("FRT Report", "N/A")

                                    st.divider()
                                    
                                    # Create tabs for better organization
                                    tab1, tab2, tab3, tab4 = st.tabs(["📊 Main Reports", "🔍 Detailed Analysis", "📈 Visualizations", "🎯 Remarks Analysis"])
                                    
                                    # Tab 1: Main Reports
                                    with tab1:
                                        col1, col2, col3 = st.columns(3)
                                        
                                        with col1:
                                            st.subheader("🔹 Complaint Type")
                                            complaint_df = complaint_report.reset_index()
                                            complaint_df.columns = ['Complaint Type', 'Count']
                                            st.dataframe(complaint_df, use_container_width=True, height=300)
                                            
                                            # Quick viz
                                            fig = px.pie(complaint_df, values='Count', names='Complaint Type', hole=0.3)
                                            st.plotly_chart(fig, use_container_width=True, key='complaint_pie_tab1')
                                        
                                        with col2:
                                            st.subheader("📅 Date Distribution")
                                            date_df = date_report.reset_index()
                                            date_df.columns = ['Date', 'Count']
                                            st.dataframe(date_df.head(10), use_container_width=True, height=300)
                                            
                                            # Quick viz
                                            fig = px.bar(date_df.head(10), x='Date', y='Count', color='Count')
                                            st.plotly_chart(fig, use_container_width=True, key='date_bar_tab1')
                                        
                                        with col3:
                                            st.subheader("⏰ Shift Duty")
                                            shift_df = shift_report.reset_index()
                                            shift_df.columns = ['Shift Duty', 'Count']
                                            st.dataframe(shift_df, use_container_width=True, height=300)
                                            
                                            # Quick viz
                                            fig = px.bar(shift_df, x='Shift Duty', y='Count', color='Count', color_continuous_scale='Greens')
                                            st.plotly_chart(fig, use_container_width=True, key='shift_bar_tab1')
                                        
                                        st.divider()
                                        
                                        # QRC and Status
                                        col4, col5 = st.columns(2)
                                        
                                        with col4:
                                            st.subheader("📝 Query/Request/Complaint")
                                            qrc_df = qrc_report.reset_index()
                                            qrc_df.columns = ['QRC Type', 'Count']
                                            st.dataframe(qrc_df, use_container_width=True, height=300)
                                            
                                            fig = px.pie(qrc_df, values='Count', names='QRC Type', hole=0.4)
                                            st.plotly_chart(fig, use_container_width=True, key='qrc_pie_tab1')
                                        
                                        with col5:
                                            st.subheader("🔄 Status (Closed/Open)")
                                            status_df = status_report.reset_index()
                                            status_df.columns = ['Status', 'Count']
                                            st.dataframe(status_df, use_container_width=True, height=300)
                                            
                                            fig = px.pie(status_df, values='Count', names='Status', 
                                                        color='Status',
                                                        color_discrete_map={'CLOSED': '#00CC96', 'OPEN': '#EF553B'})
                                            st.plotly_chart(fig, use_container_width=True, key='status_pie_tab1')
                                    
                                    # Tab 2: Detailed Analysis
                                    with tab2:
                                        detail_col1, detail_col2 = st.columns(2)
                                        
                                        with detail_col1:
                                            st.subheader("🏢 Section Analysis")
                                            section_df = section_report.reset_index()
                                            section_df.columns = ['Section', 'Count']
                                            st.dataframe(section_df, use_container_width=True, height=250)
                                            
                                            st.subheader("🏘️ Sub-Division Analysis")
                                            subdivision_df = subdivision_report.reset_index()
                                            subdivision_df.columns = ['Sub-Division', 'Count']
                                            st.dataframe(subdivision_df, use_container_width=True, height=250)
                                            
                                            st.subheader("🔵 Circle Analysis")
                                            circle_df = circle_report.reset_index()
                                            circle_df.columns = ['Circle', 'Count']
                                            st.dataframe(circle_df, use_container_width=True, height=250)
                                        
                                        with detail_col2:
                                            st.subheader("🏛️ Department Analysis")
                                            dept_df = dept_report.reset_index()
                                            dept_df.columns = ['Department', 'Count']
                                            st.dataframe(dept_df, use_container_width=True, height=250)
                                            
                                            st.subheader("📞 PSCC/FG/TO Analysis")
                                            pscc_df = pscc_report.reset_index()
                                            pscc_df.columns = ['PSCC Type', 'Count']
                                            st.dataframe(pscc_df, use_container_width=True, height=250)
                                            
                                            st.subheader("⏱️ Minute Analysis")
                                            minute_df = minute_report.reset_index()
                                            minute_df.columns = ['Minute', 'Count']
                                            st.dataframe(minute_df.head(20), use_container_width=True, height=250)
                                        
                                        st.divider()
                                        
                                        # Consumer and Mobile Numbers
                                        consumer_col1, consumer_col2 = st.columns(2)
                                        
                                        with consumer_col1:
                                            st.subheader("👤 Top Consumer Numbers")
                                            consumer_df = consumer_number_report.reset_index()
                                            consumer_df.columns = ['Consumer Number', 'Count']
                                            st.dataframe(consumer_df.head(20), use_container_width=True, height=300)
                                        
                                        with consumer_col2:
                                            st.subheader("📱 Top Mobile Numbers")
                                            mobile_df = mobile_number_report.reset_index()
                                            mobile_df.columns = ['Mobile Number', 'Count']
                                            st.dataframe(mobile_df.head(20), use_container_width=True, height=300)
                                    
                                    # Tab 3: Interactive Visualizations
                                    with tab3:
                                        st.subheader("📊 Interactive Visualizations")
                                        
                                        viz_option = st.selectbox(
                                            "Select Analysis Type:",
                                            ["Complaint Type Analysis", "Date Trends", "Shift Distribution", 
                                            "QRC Analysis", "Status Overview", "Department Breakdown",
                                            "Section & Circle", "Comparative Analysis"],
                                            key='viz_selector_tab3'
                                        )
                                        
                                        if viz_option == "Complaint Type Analysis":
                                            chart_type = st.radio("Chart Type:", ["Bar Chart", "Pie Chart", "Treemap"], 
                                                                horizontal=True, key='complaint_chart_tab3')
                                            
                                            if chart_type == "Bar Chart":
                                                fig = px.bar(complaint_df, x='Complaint Type', y='Count',
                                                        title="Complaint Type Distribution", color='Count',
                                                        color_continuous_scale='Blues')
                                                st.plotly_chart(fig, use_container_width=True)
                                            elif chart_type == "Pie Chart":
                                                fig = px.pie(complaint_df, values='Count', names='Complaint Type',
                                                        title="Complaint Type Distribution", hole=0.3)
                                                st.plotly_chart(fig, use_container_width=True)
                                            else:
                                                fig = px.treemap(complaint_df, path=['Complaint Type'], values='Count',
                                                            title="Complaint Type Hierarchy")
                                                st.plotly_chart(fig, use_container_width=True)
                                        
                                        elif viz_option == "Date Trends":
                                            fig = px.line(date_df, x='Date', y='Count',
                                                        title="Daily Complaint Trends", markers=True)
                                            st.plotly_chart(fig, use_container_width=True)
                                            
                                            fig2 = px.bar(date_df.head(15), x='Date', y='Count',
                                                        title="Top 15 Days by Count", color='Count')
                                            st.plotly_chart(fig2, use_container_width=True)
                                        
                                        elif viz_option == "Shift Distribution":
                                            chart_type = st.radio("Chart Type:", ["Bar Chart", "Donut Chart"], 
                                                                horizontal=True, key='shift_chart_tab3')
                                            
                                            if chart_type == "Bar Chart":
                                                fig = px.bar(shift_df, x='Shift Duty', y='Count',
                                                        title="Shift Duty Distribution", color='Count',
                                                        color_continuous_scale='Greens')
                                            else:
                                                fig = px.pie(shift_df, values='Count', names='Shift Duty',
                                                        title="Shift Duty Distribution", hole=0.4)
                                            st.plotly_chart(fig, use_container_width=True)
                                        
                                        elif viz_option == "QRC Analysis":
                                            fig = px.funnel(qrc_df, x='Count', y='QRC Type',
                                                        title="QRC Distribution")
                                            st.plotly_chart(fig, use_container_width=True)
                                        
                                        elif viz_option == "Status Overview":
                                            fig = px.pie(status_df, values='Count', names='Status',
                                                    title="Status Distribution",
                                                    color='Status',
                                                    color_discrete_map={'CLOSED': '#00CC96', 'OPEN': '#EF553B'})
                                            st.plotly_chart(fig, use_container_width=True)
                                        
                                        elif viz_option == "Department Breakdown":
                                            fig = px.bar(dept_df, x='Department', y='Count',
                                                    title="Department-wise Analysis", color='Count')
                                            st.plotly_chart(fig, use_container_width=True)
                                        
                                        elif viz_option == "Section & Circle":
                                            viz_col1, viz_col2 = st.columns(2)
                                            
                                            with viz_col1:
                                                fig = px.bar(section_df.head(10), x='Section', y='Count',
                                                        title="Top 10 Sections", color='Count')
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with viz_col2:
                                                fig = px.pie(circle_df, values='Count', names='Circle',
                                                        title="Circle Distribution", hole=0.3)
                                                st.plotly_chart(fig, use_container_width=True)
                                        
                                        else:  # Comparative Analysis
                                            comp_col1, comp_col2, comp_col3 = st.columns(3)
                                            
                                            with comp_col1:
                                                fig = px.pie(complaint_df, values='Count', names='Complaint Type',
                                                        title="Complaint Types")
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with comp_col2:
                                                fig = px.pie(shift_df, values='Count', names='Shift Duty',
                                                        title="Shift Distribution", hole=0.3)
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with comp_col3:
                                                fig = px.pie(status_df, values='Count', names='Status',
                                                        title="Status Overview",
                                                        color='Status',
                                                        color_discrete_map={'CLOSED': '#00CC96', 'OPEN': '#EF553B'})
                                                st.plotly_chart(fig, use_container_width=True)
                                    
                                    # Tab 4: Remarks Analysis
                                    with tab4:
                                        st.subheader("💬 Remarks Analysis")
                                        
                                        # Display metrics
                                        remark_col1, remark_col2, remark_col3, remark_col4 = st.columns(4)
                                        
                                        with remark_col1:
                                            st.metric("Total Remarks", remarks_report['Total Remarks'])
                                        with remark_col2:
                                            st.metric("Appreciation Tweets", remarks_report['Appreciation Tweets'])
                                        with remark_col3:
                                            st.metric("Awaited Consumer", remarks_report['Awaited Consumer'])
                                        with remark_col4:
                                            st.metric("5-digit Numbers", remarks_report['5-digit Numbers'])
                                        
                                        # Create visualization
                                        remarks_viz_data = pd.DataFrame({
                                            'Category': ['Appreciation Tweets', 'Awaited Consumer', '5-digit Numbers'],
                                            'Count': [
                                                remarks_report['Appreciation Tweets'],
                                                remarks_report['Awaited Consumer'],
                                                remarks_report['5-digit Numbers']
                                            ]
                                        })
                                        
                                        # Only show visualizations if there's data
                                        if remarks_viz_data['Count'].sum() > 0:
                                            viz_col1, viz_col2 = st.columns(2)
                                            
                                            with viz_col1:
                                                fig = px.bar(remarks_viz_data, x='Category', y='Count',
                                                        title="Remarks Category Distribution",
                                                        color='Count', color_continuous_scale='Viridis')
                                                st.plotly_chart(fig, use_container_width=True)
                                            
                                            with viz_col2:
                                                fig = px.pie(remarks_viz_data, values='Count', names='Category',
                                                        title="Remarks Category Breakdown", hole=0.4)
                                                st.plotly_chart(fig, use_container_width=True)
                                        else:
                                            st.info("No remarks patterns found in the selected month.")
                                        
                                        # Show sample remarks
                                        st.divider()
                                        st.subheader("📝 Sample Remarks")
                                        if 'REMARKS' in month_df.columns:
                                            sample_remarks = month_df[['DATE', 'REMARKS']].head(10)
                                            st.dataframe(sample_remarks, use_container_width=True)
                                        else:
                                            st.info("REMARKS column not found in dataset")
                                    
                                    st.divider()
                                    
                                    # Filter and Explore Section
                                    st.header("🔍 Filter and Explore Data")
                                    
                                    filter_col1, filter_col2, filter_col3 = st.columns(3)
                                    
                                    with filter_col1:
                                        selected_complaint = st.multiselect(
                                            "Filter by Complaint Type:",
                                            options=sorted(month_df['COMPLAINT TYPE'].unique()),
                                            key='complaint_filter_tab2'
                                        )
                                    
                                    with filter_col2:
                                        selected_shift = st.multiselect(
                                            "Filter by Shift Duty:",
                                            options=sorted(month_df['SHIFT DUTY'].unique()),
                                            key='shift_filter_tab2'
                                        )
                                    
                                    with filter_col3:
                                        selected_status = st.multiselect(
                                            "Filter by Status:",
                                            options=sorted(month_df['CLOSED/OPEN'].unique()),
                                            key='status_filter_tab2'
                                        )
                                    
                                    # Apply filters
                                    filtered_df = month_df.copy()
                                    if selected_complaint:
                                        filtered_df = filtered_df[filtered_df['COMPLAINT TYPE'].isin(selected_complaint)]
                                    if selected_shift:
                                        filtered_df = filtered_df[filtered_df['SHIFT DUTY'].isin(selected_shift)]
                                    if selected_status:
                                        filtered_df = filtered_df[filtered_df['CLOSED/OPEN'].isin(selected_status)]
                                    
                                    st.subheader(f"Filtered Data ({len(filtered_df)} records)")
                                    st.dataframe(filtered_df, use_container_width=True, height=400)
                                    
                                    # Download filtered data
                                    csv = filtered_df.to_csv(index=False).encode('utf-8')
                                    st.download_button(
                                        label="📥 Download Filtered Data as CSV",
                                        data=csv,
                                        file_name=f'filtered_data_{selected_month}.csv',
                                        mime='text/csv',
                                        key='download_filtered_tab2'
                                    )
                                
                                st.success("✅ Report generated successfully!")
                                
                        except Exception as e:
                            st.error(f"❌ Error processing data: {str(e)}")
                            st.info("Please ensure your Excel file has all required columns")
                            st.session_state.report_generated = False
                    else:
                        st.info("👆 Select a month and year, then click 'Generate Report' to view the analysis")
                
                except Exception as e:
                    st.error(f"❌ Error loading file: {str(e)}")
                    st.info("Please check if the file path is correct and the file exists")
                    
            else:
                st.info("👆 Please set the dataset_path variable in the code")
                st.markdown("""
                ### Expected File Format:
                Your Excel file should contain the following columns:
                - **COMPLAINT TYPE**: Type of complaint
                - **DATE**: Date of complaint
                - **SHIFT DUTY**: Shift during which complaint occurred
                - **QUERY/REQUEST/COMPLAINT**: QRC classification
                - **SECTION, SUB-DIVISION, CIRCLE**: Location details
                - **DEPT**: Department information
                - **CLOSED/OPEN**: Status of complaint
                - **PSCC/FG/TO**: PSCC type
                - **MINUTE**: Minute values
                - **REMARKS**: Remarks text
                - **CONSUMER NUMBER**: Consumer numbers
                - **MOBILE NUMB**: Mobile numbers
                """)
            


    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Unhandled error in Streamlit dashboard Tab 2 | error={error_msg}")
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)
