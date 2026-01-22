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
from ml_project.frontend_api.streamlit_cache_data import (
load_excel_data, get_financial_year_data,generate_complaint_report_fy,
generate_date_report_fy,generate_shift_duty_report_fy,generate_qrc_data_fy,
get_complaint_number_data_fy,get_section_data_fy, get_subdivision_data_fy,
get_division_data_fy, get_circle_data_fy, get_consumer_number_data_fy,
get_mobile_number_data_fy, get_dept_data_fy, get_status_data_fy,
get_complainant_name_data_fy, get_pscc_data_fy, get_minute_data_fy,

)



config = read_yaml("ml_project/configs/ml_project_config.yaml")
dataset = config["data"]["raw_path"]

from ml_project.configs.config import DatasetNotFoundError, get_dataset_path

try:
    dataset_path = get_dataset_path("data/raw_path")
    print(f"Dataset found at: {dataset_path}")
except DatasetNotFoundError as e:
    print(f"Error: {e}")
    
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


# ================================================================
# STREAMLIT APP FOR TAB 3
# ================================================================

def streamlit_analysis_tab3(tab3, dataset_path, logger):
    """
    Renders all content for Tab 3 including analysis and reports.
    
    Parameters:
    -----------
    tab3 : streamlit.tabs
        The Streamlit tab container where content will be rendered
    dataset_path : str
        Path to the dataset file
    logger : logging.Logger
        Logger instance for logging operations
    """
    try:
        with tab3:
            # ========================================
            # Initialize Session State
            # ========================================
            if 'filtered_df_tab3' not in st.session_state:
                st.session_state.filtered_df_tab3 = None
            if 'start_date_tab3' not in st.session_state:
                st.session_state.start_date_tab3 = None
            if 'end_date_tab3' not in st.session_state:
                st.session_state.end_date_tab3 = None
            
            # ========================================
            # SECTION 1: DATE RANGE ANALYSIS
            # ========================================
            st.header("📊 Custom Date Range Analysis")
            st.caption("Filter and analyze data by custom date range")
            df = load_excel_data(dataset_path)
            
            # Create a form for date selection
            with st.form("date_filter_form"):
                st.subheader("📅 Select Date Range")
                
                # Date Range Selection
                col_date1, col_date2 = st.columns(2)
                
                with col_date1:
                    start_date = st.date_input(
                        "Start Date",
                        value=pd.Timestamp('2024-04-01'),
                        help="Select the start date for analysis"
                    )
                
                with col_date2:
                    end_date = st.date_input(
                        "End Date",
                        value=pd.Timestamp('2025-03-31'),
                        help="Select the end date for analysis"
                    )
                
                # Submit button
                st.markdown("---")
                col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 1])
                with col_btn2:
                    submit_button = st.form_submit_button(
                        "🔍 Generate Report",
                        use_container_width=True,
                        type="primary"
                    )
            
            # Process data when button is clicked
            if submit_button:
                # Validate date range
                if start_date > end_date:
                    st.error("❌ Start date must be before or equal to end date!")
                else:
                    with st.spinner("🔄 Filtering data and generating reports..."):
                        # Filter data based on date range
                        @st.cache_data(ttl=600, show_spinner=False)
                        def get_date_range_data(df, start, end):
                            """Filter data for selected date range"""
                            start_ts = pd.Timestamp(start)
                            end_ts = pd.Timestamp(end)
                            return df[(df['DATE'] >= start_ts) & (df['DATE'] <= end_ts)]
                        
                        # Get filtered data and store in session state
                        st.session_state.filtered_df_tab3 = get_date_range_data(df, start_date, end_date)
                        st.session_state.start_date_tab3 = start_date
                        st.session_state.end_date_tab3 = end_date
            
            # Display results if data exists in session state
            if st.session_state.filtered_df_tab3 is not None:
                filtered_df = st.session_state.filtered_df_tab3
                start_date = st.session_state.start_date_tab3
                end_date = st.session_state.end_date_tab3
                
                # Display summary metrics
                st.markdown("---")
                st.subheader(f"📈 Summary ({start_date.strftime('%d-%b-%Y')} to {end_date.strftime('%d-%b-%Y')})")
                
                metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
                
                with metric_col1:
                    st.metric("Total Records", f"{len(filtered_df):,}")
                
                with metric_col2:
                    total_days = (end_date - start_date).days + 1
                    st.metric("Total Days", f"{total_days}")
                
                with metric_col3:
                    avg_per_day = len(filtered_df) / total_days if total_days > 0 else 0
                    st.metric("Avg Records/Day", f"{avg_per_day:.1f}")
                
                with metric_col4:
                    if len(filtered_df) > 0:
                        open_count = filtered_df['CLOSED/OPEN'].value_counts().get('OPEN', 0)
                        st.metric("Open Cases", f"{open_count:,}")
                    else:
                        st.metric("Open Cases", "0")
                
                if len(filtered_df) == 0:
                    st.warning("⚠️ No data found for the selected date range.")
                else:
                    # ========================================
                    # VISUALIZATION TOGGLE
                    # ========================================
                    st.markdown("---")
                    view_option = st.radio(
                        "Select View:",
                        ["📊 Visualizations", "📋 Data Tables", "📊📋 Both"],
                        horizontal=True,
                        help="Choose how you want to view the analysis"
                    )
                    
                    st.markdown("---")
                    
                    # ========================================
                    # ROW 1: Complaint Type & Date Analysis
                    # ========================================
                    st.subheader("🎯 Complaint Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Complaint Type Distribution")
                        complaint_data = generate_complaint_report_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Interactive Pie Chart
                            fig_complaint = px.pie(
                                complaint_data,
                                values='Count',
                                names='Complaint Type',
                                title='Complaint Type Breakdown',
                                color_discrete_sequence=px.colors.qualitative.Set3,
                                hover_data=['Percentage']
                            )
                            fig_complaint.update_traces(textposition='inside', textinfo='percent+label')
                            st.plotly_chart(fig_complaint, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(complaint_data, use_container_width=True, hide_index=True)
                    
                    with col2:
                        st.markdown("#### Date-wise Distribution")
                        date_data = generate_date_report_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Interactive Line Chart with Area
                            fig_date = px.area(
                                date_data,
                                x='Date',
                                y='Count',
                                title='Daily Complaint Trend',
                                color_discrete_sequence=['#636EFA']
                            )
                            fig_date.update_traces(mode='lines+markers')
                            st.plotly_chart(fig_date, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(date_data, use_container_width=True, hide_index=True, height=300)
                    
                    # ========================================
                    # ROW 2: Shift Duty & QRC Type
                    # ========================================
                    st.markdown("---")
                    st.subheader("⏰ Shift & Query Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Shift Duty Analysis")
                        shift_data = generate_shift_duty_report_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Bar Chart
                            fig_shift = px.bar(
                                shift_data,
                                x='Shift Duty',
                                y='Count',
                                title='Complaints by Shift Duty',
                                color='Count',
                                color_continuous_scale='Blues',
                                text='Count'
                            )
                            fig_shift.update_traces(texttemplate='%{text}', textposition='outside')
                            st.plotly_chart(fig_shift, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(shift_data, use_container_width=True, hide_index=True)
                    
                    with col2:
                        st.markdown("#### Query/Request/Complaint Type")
                        qrc_data = generate_qrc_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Donut Chart
                            fig_qrc = px.pie(
                                qrc_data,
                                values='Count',
                                names='QRC Type',
                                title='QRC Type Distribution',
                                hole=0.4,
                                color_discrete_sequence=px.colors.qualitative.Pastel
                            )
                            st.plotly_chart(fig_qrc, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(qrc_data, use_container_width=True, hide_index=True)
                    
                    # ========================================
                    # ROW 3: Section & Sub-Division
                    # ========================================
                    st.markdown("---")
                    st.subheader("🏢 Geographic Distribution")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Section-wise Distribution")
                        section_data = get_section_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Horizontal Bar Chart
                            fig_section = px.bar(
                                section_data.head(15),
                                y='Section',
                                x='Count',
                                title='Top 15 Sections',
                                orientation='h',
                                color='Percentage',
                                color_continuous_scale='Viridis',
                                text='Count'
                            )
                            fig_section.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_section, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(section_data, use_container_width=True, hide_index=True, height=400)
                    
                    with col2:
                        st.markdown("#### Sub-Division Distribution")
                        subdivision_data = get_subdivision_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Horizontal Bar Chart
                            fig_subdivision = px.bar(
                                subdivision_data.head(15),
                                y='Sub-Division',
                                x='Count',
                                title='Top 15 Sub-Divisions',
                                orientation='h',
                                color='Count',
                                color_continuous_scale='Oranges',
                                text='Count'
                            )
                            fig_subdivision.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_subdivision, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(subdivision_data, use_container_width=True, hide_index=True, height=400)
                    
                    # ========================================
                    # ROW 4: Division & Circle
                    # ========================================
                    st.markdown("---")
                    st.subheader("🏛️ Administrative Units")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Division-wise Distribution")
                        division_data = get_division_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Treemap
                            fig_division = px.treemap(
                                division_data,
                                path=['Division'],
                                values='Count',
                                title='Division Distribution (Treemap)',
                                color='Count',
                                color_continuous_scale='RdYlGn_r'
                            )
                            st.plotly_chart(fig_division, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(division_data, use_container_width=True, hide_index=True, height=300)
                    
                    with col2:
                        st.markdown("#### Circle-wise Distribution")
                        circle_data = get_circle_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Sunburst Chart
                            fig_circle = px.sunburst(
                                circle_data,
                                path=['Circle'],
                                values='Count',
                                title='Circle Distribution (Sunburst)',
                                color='Count',
                                color_continuous_scale='thermal'
                            )
                            st.plotly_chart(fig_circle, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(circle_data, use_container_width=True, hide_index=True, height=300)
                    
                    # ========================================
                    # ROW 5: Consumer Number & Mobile Number
                    # ========================================
                    st.markdown("---")
                    st.subheader("📞 Contact Information Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Consumer Number Frequency")
                        consumer_data = get_consumer_number_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Top 20 Bar Chart
                            fig_consumer = px.bar(
                                consumer_data.head(20),
                                x='Consumer Number',
                                y='Count',
                                title='Top 20 Consumer Numbers',
                                color='Count',
                                color_continuous_scale='Reds'
                            )
                            fig_consumer.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_consumer, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(consumer_data, use_container_width=True, hide_index=True, height=400)
                    
                    with col2:
                        st.markdown("#### Mobile Number Frequency")
                        mobile_data = get_mobile_number_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Top 20 Bar Chart
                            fig_mobile = px.bar(
                                mobile_data.head(20),
                                x='Mobile Number',
                                y='Count',
                                title='Top 20 Mobile Numbers',
                                color='Count',
                                color_continuous_scale='Greens'
                            )
                            fig_mobile.update_layout(xaxis_tickangle=-45)
                            st.plotly_chart(fig_mobile, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(mobile_data, use_container_width=True, hide_index=True, height=400)
                    
                    # ========================================
                    # ROW 6: Department & Status
                    # ========================================
                    st.markdown("---")
                    st.subheader("🏢 Department & Status Overview")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Department Distribution")
                        dept_data = get_dept_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Pie Chart
                            fig_dept = px.pie(
                                dept_data,
                                values='Count',
                                names='Department',
                                title='Department-wise Breakdown',
                                color_discrete_sequence=px.colors.qualitative.Bold
                            )
                            st.plotly_chart(fig_dept, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(dept_data, use_container_width=True, hide_index=True)
                    
                    with col2:
                        st.markdown("#### Status Distribution (Open/Closed)")
                        status_data = get_status_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Gauge-like Bar Chart
                            fig_status = px.bar(
                                status_data,
                                x='Status',
                                y='Count',
                                title='Open vs Closed Status',
                                color='Status',
                                color_discrete_map={'OPEN': '#FF6B6B', 'CLOSED': '#4ECDC4'},
                                text='Count'
                            )
                            fig_status.update_traces(texttemplate='%{text}<br>(%{y})', textposition='outside')
                            st.plotly_chart(fig_status, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(status_data, use_container_width=True, hide_index=True)
                    
                    # ========================================
                    # ROW 7: Complaint Number & Complainant Name
                    # ========================================
                    st.markdown("---")
                    st.subheader("🎫 Complaint & Complainant Details")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### Complaint Number Frequency")
                        complaint_num_data = get_complaint_number_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Scatter Plot
                            complaint_num_data_plot = complaint_num_data.head(30).reset_index()
                            fig_complaint_num = px.scatter(
                                complaint_num_data_plot,
                                x='index',
                                y='Count',
                                size='Count',
                                title='Top 30 Complaint Numbers (Bubble Chart)',
                                color='Count',
                                color_continuous_scale='Rainbow',
                                hover_data=['Complaint Number']
                            )
                            fig_complaint_num.update_layout(xaxis_title='Rank')
                            st.plotly_chart(fig_complaint_num, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(complaint_num_data, use_container_width=True, hide_index=True, height=400)
                    
                    with col2:
                        st.markdown("#### Complainant Name Frequency")
                        complainant_data = get_complainant_name_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Horizontal Bar for Top 15
                            fig_complainant = px.bar(
                                complainant_data.head(15),
                                y='Complainant Name',
                                x='Count',
                                title='Top 15 Complainants',
                                orientation='h',
                                color='Count',
                                color_continuous_scale='Purples'
                            )
                            fig_complainant.update_layout(yaxis={'categoryorder':'total ascending'})
                            st.plotly_chart(fig_complainant, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(complainant_data, use_container_width=True, hide_index=True, height=400)
                    
                    # ========================================
                    # ROW 8: PSCC/FG/TO & Minute
                    # ========================================
                    st.markdown("---")
                    st.subheader("📊 PSCC & Time Analysis")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("#### PSCC/FG/TO Distribution")
                        pscc_data = get_pscc_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Funnel Chart
                            fig_pscc = px.funnel(
                                pscc_data,
                                x='Count',
                                y='PSCC Type',
                                title='PSCC Type Funnel',
                                color='PSCC Type',
                                color_discrete_sequence=px.colors.qualitative.Safe
                            )
                            st.plotly_chart(fig_pscc, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(pscc_data, use_container_width=True, hide_index=True)
                    
                    with col2:
                        st.markdown("#### Minute Distribution")
                        minute_data = get_minute_data_fy(filtered_df)
                        
                        if view_option in ["📊 Visualizations", "📊📋 Both"]:
                            # Histogram
                            fig_minute = px.histogram(
                                minute_data.head(20),
                                x='Minute',
                                y='Count',
                                title='Top 20 Minute Values',
                                color='Count',
                                nbins=20
                            )
                            fig_minute.update_traces(marker_colorscale='Teal')
                            fig_minute.update_layout(bargap=0.1)
                            st.plotly_chart(fig_minute, use_container_width=True)
                        
                        if view_option in ["📋 Data Tables", "📊📋 Both"]:
                            st.dataframe(minute_data, use_container_width=True, hide_index=True, height=400)
                    
                    # ========================================
                    # ADVANCED ANALYTICS SECTION
                    # ========================================
                    st.markdown("---")
                    st.subheader("🔬 Advanced Analytics")
                    
                    # Create tabs for advanced analytics
                    adv_tab1, adv_tab2, adv_tab3 = st.tabs(["📈 Trends", "🔥 Heatmap", "📊 Correlation"])
                    
                    with adv_tab1:
                        st.markdown("#### Daily Trend with Moving Average")
                        date_data_full = generate_date_report_fy(filtered_df)
                        date_data_full = date_data_full.sort_values('Date')
                        date_data_full['7-Day MA'] = date_data_full['Count'].rolling(window=7, min_periods=1).mean()
                        
                        fig_trend = go.Figure()
                        fig_trend.add_trace(go.Scatter(
                            x=date_data_full['Date'],
                            y=date_data_full['Count'],
                            mode='lines+markers',
                            name='Daily Count',
                            line=dict(color='lightblue', width=2)
                        ))
                        fig_trend.add_trace(go.Scatter(
                            x=date_data_full['Date'],
                            y=date_data_full['7-Day MA'],
                            mode='lines',
                            name='7-Day Moving Average',
                            line=dict(color='red', width=3, dash='dash')
                        ))
                        fig_trend.update_layout(
                            title='Daily Complaints with 7-Day Moving Average',
                            xaxis_title='Date',
                            yaxis_title='Count',
                            hovermode='x unified'
                        )
                        st.plotly_chart(fig_trend, use_container_width=True)
                    
                    with adv_tab2:
                        st.markdown("#### Heatmap: Day of Week vs Complaint Type")
                        
                        # Create day of week column
                        heatmap_df = filtered_df.copy()
                        heatmap_df['Day of Week'] = pd.to_datetime(heatmap_df['DATE']).dt.day_name()
                        
                        # Create pivot table
                        heatmap_data = heatmap_df.groupby(['Day of Week', 'COMPLAINT TYPE']).size().reset_index(name='Count')
                        heatmap_pivot = heatmap_data.pivot(index='Day of Week', columns='COMPLAINT TYPE', values='Count').fillna(0)
                        
                        # Reorder days
                        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                        heatmap_pivot = heatmap_pivot.reindex([d for d in day_order if d in heatmap_pivot.index])
                        
                        fig_heatmap = px.imshow(
                            heatmap_pivot,
                            labels=dict(x="Complaint Type", y="Day of Week", color="Count"),
                            title='Heatmap: Complaints by Day and Type',
                            color_continuous_scale='YlOrRd',
                            aspect='auto'
                        )
                        fig_heatmap.update_xaxes(tickangle=-45)
                        st.plotly_chart(fig_heatmap, use_container_width=True)
                    
                    with adv_tab3:
                        st.markdown("#### Multi-Dimensional Analysis")
                        
                        # Sunburst: Circle -> Division -> Section (top 10 of each)
                        multi_df = filtered_df[['CIRCLE', 'DIVISION', 'SECTION']].copy()
                        multi_df = multi_df.groupby(['CIRCLE', 'DIVISION', 'SECTION']).size().reset_index(name='Count')
                        multi_df = multi_df.sort_values('Count', ascending=False).head(50)
                        
                        fig_multi = px.sunburst(
                            multi_df,
                            path=['CIRCLE', 'DIVISION', 'SECTION'],
                            values='Count',
                            title='Hierarchical View: Circle → Division → Section (Top 50)',
                            color='Count',
                            color_continuous_scale='RdBu_r'
                        )
                        st.plotly_chart(fig_multi, use_container_width=True)
                    
                    # ========================================
                    # DOWNLOAD SECTION
                    # ========================================
                    st.markdown("---")
                    st.subheader("💾 Download Options")
                    
                    download_col1, download_col2 = st.columns(2)
                    
                    with download_col1:
                        # Download filtered data
                        csv = filtered_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"📥 Download Filtered Data ({len(filtered_df)} records)",
                            data=csv,
                            file_name=f"filtered_data_{start_date}_{end_date}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                    
                    with download_col2:
                        # Download summary report
                        summary_data = {
                            'Metric': ['Total Records', 'Total Days', 'Avg Records/Day', 'Open Cases', 'Closed Cases'],
                            'Value': [
                                len(filtered_df),
                                total_days,
                                round(avg_per_day, 2),
                                open_count if len(filtered_df) > 0 else 0,
                                len(filtered_df) - (open_count if len(filtered_df) > 0 else 0)
                            ]
                        }
                        summary_csv = pd.DataFrame(summary_data).to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📊 Download Summary Report",
                            data=summary_csv,
                            file_name=f"summary_report_{start_date}_{end_date}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
            else:
                # Show instruction when no data in session state
                st.info("👆 Please select date range above and click '🔍 Generate Report' to view the analysis.")

    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Unhandled error in Streamlit dashboard Tab 3 | error={error_msg}")
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)