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
fetch_generate_month_wise_open_close_pivot_report,
fetch_generate_quarter_wise_agging_pivot_report,
fetch_generate_finance_year_wise_open_close_pivot_report,

)
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


# Pie Chart , donut chart, mosaic plot, marimekko chart,sunburst chart,sankey diagram,parallel sets,network diagram,polar area chart,Heatmap 
# multi-line chart, Area Chart by Category, stacked area chart, scatter plot with hue,dot plot by category, Choropleth Map, Dot Density Map
# Funnel Chart, Mixed Subplots
# 3d pie chart,3D 3D Bar Chart, 3D Column Chart,3d treemap,3d line plot,3D Scatter Plot,3D Histogram,3d bubble chart,3D Grouped Bar Chart,3d choropleth map
# JSON Schema Tree,Tree View


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

            with col2:               
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

            
            with col3:
                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button(
                    "📊 Generate Report",
                    type="primary",
                    width="stretch",
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
                    
                    # Prepare data for visualizations
                    df_viz = df[df.index != 'Grand Total'].copy()
                    
                    # Extract department names and statuses from column names
                    dept_status_cols = [col for col in df.columns if col != 'Grand Total']
                    
                    # Calculate summary statistics
                    total_complaints = df['Grand Total_'].sum()/2
                   
                    # Separate open and closed
                    open_cols = [col for col in df.columns if 'Open' in col]
                    closed_cols = [col for col in df.columns if 'Closed' in col]
                    
                    total_open = df_viz[open_cols].sum().sum() if open_cols else 0
                    total_closed = df_viz[closed_cols].sum().sum() if closed_cols else 0
                    
                    # Display KPI Metrics
                    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
                    with col_m1:
                        st.metric("📊 Total Complaints", f"{int(total_complaints):,}")
                    with col_m2:
                        st.metric("🟢 Closed", f"{int(total_closed):,}")
                    with col_m3:
                        st.metric("🔴 Open", f"{int(total_open):,}")
                    with col_m4:
                        closure_rate = (total_closed / total_complaints * 100) if total_complaints > 0 else 0
                        st.metric("✅ Closure Rate", f"{closure_rate:.1f}%")
                    
                    st.divider()
                    
                    # ========================================
                    # VISUALIZATIONS SECTION
                    # ========================================
                    st.header("📈 Visual Analytics Dashboard")
                    
                    # Create tabs for different visualization categories
                    viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
                        "🎯 Status Overview", 
                        "🏢 Department Insights", 
                        "📋 Complaint Analysis",
                        "🔥 Advanced Views"
                    ])
                    
                    with viz_tab1:
                        st.subheader("Status Distribution Overview")
                        
                        col_pie1, col_pie2 = st.columns(2)
                        
                        # 1. PIE CHART - Open vs Closed
                        with col_pie1:
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=['Closed', 'Open'],
                                values=[total_closed, total_open],
                                marker=dict(colors=['#00CC96', '#EF553B']),
                                textinfo='label+percent+value',
                                textfont_size=15,
                                pull=[0.05, 0.1]  # Explode the slices slightly
                            )])
                            fig_pie.update_layout(
                                title=dict(text="<b>Complaint Status Distribution</b><br><sub>Pie Chart</sub>", 
                                        font=dict(size=18), x=0.5, xanchor='center'),
                                height=450,
                                showlegend=True,
                                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
                            )
                            st.plotly_chart(fig_pie, width="stretch")
                        
                        # 2. DONUT CHART - Department-wise Distribution
                        with col_pie2:
                            dept_totals = {}
                            for col in df.columns:
                                if col != 'Grand Total' and '_' in col:
                                    dept = col.split('_')[0]
                                    if dept not in dept_totals:
                                        dept_totals[dept] = 0
                                    dept_totals[dept] += df_viz[col].sum()
                            
                            if dept_totals:
                                fig_donut = go.Figure(data=[go.Pie(
                                    labels=list(dept_totals.keys()),
                                    values=list(dept_totals.values()),
                                    hole=0.5,  # Creates donut effect
                                    textinfo='label+percent',
                                    textfont_size=13,
                                    marker=dict(line=dict(color='white', width=2))
                                )])
                                fig_donut.update_layout(
                                    title=dict(text="<b>Department Distribution</b><br><sub>Donut Chart</sub>", 
                                            font=dict(size=18), x=0.5, xanchor='center'),
                                    height=450,
                                    showlegend=True,
                                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
                                    annotations=[dict(text=f'<b>{int(total_complaints)}</b><br>Total', 
                                                    x=0.5, y=0.5, font_size=20, showarrow=False)]
                                )
                                st.plotly_chart(fig_donut, width="stretch")
                        
                        # 3. BAR CHART - Stacked by Complaint Type
                        st.subheader("Complaints by Type - Stacked View")
                        
                        complaint_types = df_viz.index.tolist()
                        open_data = []
                        closed_data = []
                        
                        for idx in complaint_types:
                            open_sum = df_viz.loc[idx, open_cols].sum() if open_cols else 0
                            closed_sum = df_viz.loc[idx, closed_cols].sum() if closed_cols else 0
                            open_data.append(open_sum)
                            closed_data.append(closed_sum)
                        
                        fig_bar_stacked = go.Figure()
                        fig_bar_stacked.add_trace(go.Bar(
                            name='Closed',
                            x=complaint_types,
                            y=closed_data,
                            marker_color='#00CC96',
                            text=closed_data,
                            textposition='inside',
                            textfont=dict(color='white', size=12, family='Arial Black'),
                            hovertemplate='<b>%{x}</b><br>Closed: %{y}<extra></extra>'
                        ))
                        fig_bar_stacked.add_trace(go.Bar(
                            name='Open',
                            x=complaint_types,
                            y=open_data,
                            marker_color='#EF553B',
                            text=open_data,
                            textposition='inside',
                            textfont=dict(color='white', size=12, family='Arial Black'),
                            hovertemplate='<b>%{x}</b><br>Open: %{y}<extra></extra>'
                        ))
                        
                        fig_bar_stacked.update_layout(
                            title=dict(text="<b>Complaint Status by Type</b><br><sub>Stacked Bar Chart</sub>", 
                                    font=dict(size=20), x=0.5, xanchor='center'),
                            barmode='stack',
                            xaxis_title="Complaint Type",
                            yaxis_title="Number of Complaints",
                            height=550,
                            hovermode='x unified',
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                            xaxis=dict(tickangle=-45)
                        )
                        st.plotly_chart(fig_bar_stacked, width="stretch")
                    
                    with viz_tab2:
                        st.subheader("Department Performance Analysis")
                        
                        # Create department comparison
                        dept_open_closed = {}
                        for col in df.columns:
                            if col != 'Grand Total' and '_' in col:
                                dept, status = col.rsplit('_', 1)
                                if dept not in dept_open_closed:
                                    dept_open_closed[dept] = {'Open': 0, 'Closed': 0}
                                if 'Open' in status:
                                    dept_open_closed[dept]['Open'] += df_viz[col].sum()
                                elif 'Closed' in status:
                                    dept_open_closed[dept]['Closed'] += df_viz[col].sum()
                        
                        if dept_open_closed:
                            depts = list(dept_open_closed.keys())
                            open_vals = [dept_open_closed[d]['Open'] for d in depts]
                            closed_vals = [dept_open_closed[d]['Closed'] for d in depts]
                            
                            # 4. GROUPED BAR CHART - Department Comparison
                            fig_dept_grouped = go.Figure()
                            fig_dept_grouped.add_trace(go.Bar(
                                name='Open',
                                x=depts,
                                y=open_vals,
                                marker=dict(color='#EF553B', line=dict(color='darkred', width=1.5)),
                                text=open_vals,
                                textposition='outside',
                                textfont=dict(size=13, family='Arial Black'),
                                hovertemplate='<b>%{x}</b><br>Open: %{y}<extra></extra>'
                            ))
                            fig_dept_grouped.add_trace(go.Bar(
                                name='Closed',
                                x=depts,
                                y=closed_vals,
                                marker=dict(color='#00CC96', line=dict(color='darkgreen', width=1.5)),
                                text=closed_vals,
                                textposition='outside',
                                textfont=dict(size=13, family='Arial Black'),
                                hovertemplate='<b>%{x}</b><br>Closed: %{y}<extra></extra>'
                            ))
                            
                            fig_dept_grouped.update_layout(
                                title=dict(text="<b>Department Performance: Open vs Closed</b><br><sub>Grouped Bar Chart</sub>", 
                                        font=dict(size=20), x=0.5, xanchor='center'),
                                xaxis_title="Department",
                                yaxis_title="Number of Complaints",
                                barmode='group',
                                height=550,
                                hovermode='x unified',
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            st.plotly_chart(fig_dept_grouped, width="stretch")
                            
                            # 5. HEATMAP - Complaint Type vs Department
                            st.subheader("Complaint Distribution Matrix")
                            
                            dept_complaint_matrix = []
                            for ct in complaint_types:
                                row_data = []
                                for dept in depts:
                                    dept_cols = [col for col in df.columns if col.startswith(dept + '_')]
                                    total = df_viz.loc[ct, dept_cols].sum() if dept_cols else 0
                                    row_data.append(total)
                                dept_complaint_matrix.append(row_data)
                            
                            fig_heatmap = go.Figure(data=go.Heatmap(
                                z=dept_complaint_matrix,
                                x=depts,
                                y=complaint_types,
                                colorscale='YlOrRd',
                                text=dept_complaint_matrix,
                                texttemplate='<b>%{text}</b>',
                                textfont={"size": 12, "family": "Arial Black"},
                                colorbar=dict(title="<b>Count</b>", titleside='right'),
                                hovertemplate='<b>Type:</b> %{y}<br><b>Dept:</b> %{x}<br><b>Count:</b> %{z}<extra></extra>'
                            ))
                            
                            fig_heatmap.update_layout(
                                title=dict(text="<b>Complaint Type vs Department</b><br><sub>Heatmap</sub>", 
                                        font=dict(size=20), x=0.5, xanchor='center'),
                                xaxis_title="<b>Department</b>",
                                yaxis_title="<b>Complaint Type</b>",
                                height=600,
                                xaxis=dict(side='bottom'),
                                yaxis=dict(tickmode='linear')
                            )
                            st.plotly_chart(fig_heatmap, width="stretch")
                            
                            # Department Efficiency Score
                            st.subheader("Department Efficiency Metrics")
                            
                            dept_efficiency = []
                            for dept in depts:
                                total = open_vals[depts.index(dept)] + closed_vals[depts.index(dept)]
                                closed = closed_vals[depts.index(dept)]
                                efficiency = (closed / total * 100) if total > 0 else 0
                                dept_efficiency.append(efficiency)
                            
                            fig_efficiency = go.Figure()
                            fig_efficiency.add_trace(go.Bar(
                                x=depts,
                                y=dept_efficiency,
                                marker=dict(
                                    color=dept_efficiency,
                                    colorscale='RdYlGn',
                                    showscale=True,
                                    colorbar=dict(title="<b>Rate %</b>"),
                                    line=dict(color='black', width=1.5)
                                ),
                                text=[f"{eff:.1f}%" for eff in dept_efficiency],
                                textposition='outside',
                                textfont=dict(size=14, family='Arial Black'),
                                hovertemplate='<b>%{x}</b><br>Efficiency: %{y:.1f}%<extra></extra>'
                            ))
                            
                            fig_efficiency.update_layout(
                                title=dict(text="<b>Department Closure Rate</b><br><sub>Efficiency Bar Chart</sub>", 
                                        font=dict(size=20), x=0.5, xanchor='center'),
                                xaxis_title="<b>Department</b>",
                                yaxis_title="<b>Closure Rate (%)</b>",
                                yaxis=dict(range=[0, 105]),
                                height=500,
                                hovermode='x'
                            )
                            st.plotly_chart(fig_efficiency, width="stretch")
                    
                    with viz_tab3:
                        st.subheader("Complaint Type Deep Dive")
                        
                        # 6. TREEMAP - Hierarchical View
                        st.subheader("Hierarchical Distribution")
                        
                        treemap_data = []
                        for ct in complaint_types:
                            for col in df.columns:
                                if col != 'Grand Total' and '_' in col:
                                    parts = col.rsplit('_', 1)
                                    if len(parts) == 2:
                                        dept, status = parts
                                        value = df_viz.loc[ct, col]
                                        if value > 0:
                                            treemap_data.append({
                                                'Complaint Type': ct,
                                                'Department': dept,
                                                'Status': status,
                                                'Count': value,
                                                'Label': f"{ct}<br>{dept}<br>{status}"
                                            })
                        
                        if treemap_data:
                            df_treemap = pd.DataFrame(treemap_data)
                            
                            fig_treemap = px.treemap(
                                df_treemap,
                                path=['Complaint Type', 'Department', 'Status'],
                                values='Count',
                                color='Count',
                                color_continuous_scale='Viridis',
                                title="<b>Complaint Distribution Treemap</b><br><sub>Complaint Type → Department → Status</sub>"
                            )
                            fig_treemap.update_layout(
                                height=650,
                                title=dict(font=dict(size=20), x=0.5, xanchor='center')
                            )
                            fig_treemap.update_traces(
                                textinfo="label+value+percent parent",
                                textfont=dict(size=12, family='Arial')
                            )
                            st.plotly_chart(fig_treemap, width="stretch")
                        
                        # Top Complaint Types
                        st.subheader("Top Complaint Types")
                        
                        complaint_totals = df_viz.sum(axis=1).sort_values(ascending=False)
                        top_n = min(10, len(complaint_totals))
                        
                        fig_top = go.Figure()
                        fig_top.add_trace(go.Bar(
                            x=complaint_totals.head(top_n).values,
                            y=complaint_totals.head(top_n).index,
                            orientation='h',
                            marker=dict(
                                color=complaint_totals.head(top_n).values,
                                colorscale='Plasma',
                                showscale=True,
                                colorbar=dict(title="<b>Count</b>"),
                                line=dict(color='black', width=1)
                            ),
                            text=complaint_totals.head(top_n).values,
                            textposition='outside',
                            textfont=dict(size=13, family='Arial Black'),
                            hovertemplate='<b>%{y}</b><br>Total: %{x}<extra></extra>'
                        ))
                        
                        fig_top.update_layout(
                            title=dict(text=f"<b>Top {top_n} Complaint Types</b><br><sub>Horizontal Bar Chart</sub>", 
                                    font=dict(size=20), x=0.5, xanchor='center'),
                            xaxis_title="<b>Total Complaints</b>",
                            yaxis_title="<b>Complaint Type</b>",
                            height=550,
                            yaxis=dict(autorange="reversed")
                        )
                        st.plotly_chart(fig_top, width="stretch")
                    
                    with viz_tab4:
                        st.subheader("Advanced Analytical Views")
                        
                        # 7. MOSAIC PLOT (Simulated using stacked bars with percentages)
                        st.subheader("Complaint Type Composition")
                        
                        # Prepare data for mosaic-style visualization
                        mosaic_data = []
                        for ct in complaint_types:
                            ct_total = df_viz.loc[ct].sum()
                            if ct_total > 0:
                                for col in df.columns:
                                    if col != 'Grand Total' and '_' in col:
                                        parts = col.rsplit('_', 1)
                                        if len(parts) == 2:
                                            dept, status = parts
                                            value = df_viz.loc[ct, col]
                                            pct = (value / ct_total) * 100
                                            mosaic_data.append({
                                                'Complaint Type': ct,
                                                'Department_Status': f"{dept} - {status}",
                                                'Count': value,
                                                'Percentage': pct
                                            })
                        
                        if mosaic_data:
                            df_mosaic = pd.DataFrame(mosaic_data)
                            
                            # Create mosaic-style stacked bar chart
                            fig_mosaic = go.Figure()
                            
                            dept_status_unique = df_mosaic['Department_Status'].unique()
                            colors = px.colors.qualitative.Set3[:len(dept_status_unique)]
                            
                            for idx, ds in enumerate(dept_status_unique):
                                subset = df_mosaic[df_mosaic['Department_Status'] == ds]
                                fig_mosaic.add_trace(go.Bar(
                                    name=ds,
                                    x=subset['Complaint Type'],
                                    y=subset['Percentage'],
                                    text=subset['Count'],
                                    textposition='inside',
                                    textfont=dict(size=10, color='white'),
                                    marker_color=colors[idx % len(colors)],
                                    hovertemplate='<b>%{x}</b><br>' + ds + '<br>Count: %{text}<br>Percentage: %{y:.1f}%<extra></extra>'
                                ))
                            
                            fig_mosaic.update_layout(
                                title=dict(text="<b>Complaint Type Composition</b><br><sub>Mosaic Plot (100% Stacked)</sub>", 
                                        font=dict(size=20), x=0.5, xanchor='center'),
                                barmode='stack',
                                xaxis_title="<b>Complaint Type</b>",
                                yaxis_title="<b>Percentage (%)</b>",
                                height=600,
                                hovermode='x unified',
                                legend=dict(
                                    orientation="v",
                                    yanchor="middle",
                                    y=0.5,
                                    xanchor="left",
                                    x=1.02,
                                    title="<b>Dept - Status</b>"
                                ),
                                xaxis=dict(tickangle=-45),
                                yaxis=dict(range=[0, 100])
                            )
                            st.plotly_chart(fig_mosaic, width="stretch")
                        
                        # Sunburst Chart
                        st.subheader("Interactive Sunburst Visualization")
                        
                        sunburst_data = []
                        for ct in complaint_types:
                            for col in df.columns:
                                if col != 'Grand Total' and '_' in col:
                                    parts = col.rsplit('_', 1)
                                    if len(parts) == 2:
                                        dept, status = parts
                                        value = df_viz.loc[ct, col]
                                        if value > 0:
                                            sunburst_data.append({
                                                'Complaint Type': ct,
                                                'Department': dept,
                                                'Status': status,
                                                'Count': value
                                            })
                        
                        if sunburst_data:
                            df_sunburst = pd.DataFrame(sunburst_data)
                            
                            fig_sunburst = px.sunburst(
                                df_sunburst,
                                path=['Complaint Type', 'Department', 'Status'],
                                values='Count',
                                color='Count',
                                color_continuous_scale='Rainbow',
                                title="<b>Hierarchical Sunburst Chart</b><br><sub>Click segments to drill down</sub>"
                            )
                            fig_sunburst.update_layout(
                                height=650,
                                title=dict(font=dict(size=20), x=0.5, xanchor='center')
                            )
                            fig_sunburst.update_traces(
                                textinfo="label+value+percent parent",
                                textfont=dict(size=11)
                            )
                            st.plotly_chart(fig_sunburst, width="stretch")
                        
                        # Bubble Chart - Department Performance
                        st.subheader("Department Performance Bubble Chart")
                        
                        if dept_open_closed:
                            bubble_data = []
                            for dept in depts:
                                total = dept_open_closed[dept]['Open'] + dept_open_closed[dept]['Closed']
                                closed = dept_open_closed[dept]['Closed']
                                efficiency = (closed / total * 100) if total > 0 else 0
                                bubble_data.append({
                                    'Department': dept,
                                    'Total': total,
                                    'Closed': closed,
                                    'Open': dept_open_closed[dept]['Open'],
                                    'Efficiency': efficiency
                                })
                            
                            df_bubble = pd.DataFrame(bubble_data)
                            
                            fig_bubble = px.scatter(
                                df_bubble,
                                x='Total',
                                y='Efficiency',
                                size='Total',
                                color='Efficiency',
                                hover_name='Department',
                                text='Department',
                                color_continuous_scale='RdYlGn',
                                size_max=60,
                                title="<b>Department Performance Analysis</b><br><sub>Bubble size = Total Complaints</sub>"
                            )
                            fig_bubble.update_traces(
                                textposition='top center',
                                textfont=dict(size=12, family='Arial Black')
                            )
                            fig_bubble.update_layout(
                                height=550,
                                title=dict(font=dict(size=20), x=0.5, xanchor='center'),
                                xaxis_title="<b>Total Complaints</b>",
                                yaxis_title="<b>Closure Rate (%)</b>",
                                yaxis=dict(range=[0, 105])
                            )
                            st.plotly_chart(fig_bubble, width="stretch")
                    
                    st.divider()
                    
                    # ========================================
                    # DATA TABLE SECTION
                    # ========================================
                    st.header("📋 Detailed Data Table")
                    
                    # Add download button
                    col_download1, col_download2, col_download3 = st.columns([1, 1, 1])
                    with col_download2:
                        csv = df.to_csv(index=True).encode('utf-8')
                        st.download_button(
                            label="📥 Download Report as CSV",
                            data=csv,
                            file_name=f"monthly_report_{month_str}.csv",
                            mime="text/csv",
                            width="stretch",
                            type="primary"
                        )
                    
                    # Display dataframe
                    st.dataframe(df, width="stretch", height=400)
                    
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
            # ========================================
            # SECTION 1: YEAR AND QUARTER SELECTION
            # ========================================
            st.header("📊 Year and Quarter Analysis Report")
            st.caption("Select start year/quarter and end year/quarter to view analysis")

            # Initialize session state for selected years and quarters
            if "start_year_tab2" not in st.session_state:
                st.session_state.start_year_tab2 = datetime.today().year

            if "end_year_tab2" not in st.session_state:
                st.session_state.end_year_tab2 = datetime.today().year

            if "start_quarter_tab2" not in st.session_state:
                st.session_state.start_quarter_tab2 = 1

            if "end_quarter_tab2" not in st.session_state:
                st.session_state.end_quarter_tab2 = 4

            # Initialize flag to track if report should be generated
            if "generate_report_tab2" not in st.session_state:
                st.session_state.generate_report_tab2 = False

            # Quarter mapping
            quarters = {
                1: "Q1 (Jan-Mar)",
                2: "Q2 (Apr-Jun)",
                3: "Q3 (Jul-Sep)",
                4: "Q4 (Oct-Dec)"
            }

            # Create columns for Start and End selection
            st.subheader("Start Period")
            col1, col2 = st.columns([1, 1])
                        
            with col1:
                # Start Year selector
                current_year = datetime.today().year
                start_year = st.selectbox(
                    "Start Year",
                    options=list(range(current_year - 10, current_year + 1)),
                    index=list(range(current_year - 10, current_year + 1)).index(
                        st.session_state.start_year_tab2
                    ),
                    key="start_year_selector",
                    help="Choose the starting year"
                )

            with col2:
                # Start Quarter selector
                start_quarter = st.selectbox(
                    "Start Quarter",
                    options=list(quarters.keys()),
                    format_func=lambda x: quarters[x],
                    index=st.session_state.start_quarter_tab2 - 1,
                    key="start_quarter_selector_tab2",
                    help="Choose the starting quarter"
                )

            st.subheader("End Period")
            col3, col4 = st.columns([1, 1])

            with col3:
                # End Year selector
                end_year = st.selectbox(
                    "End Year",
                    options=list(range(current_year - 10, current_year + 1)),
                    index=list(range(current_year - 10, current_year + 1)).index(
                        st.session_state.end_year_tab2
                    ),
                    key="end_year_selector",
                    help="Choose the ending year"
                )

            with col4:
                # End Quarter selector
                end_quarter = st.selectbox(
                    "End Quarter",
                    options=list(quarters.keys()),
                    format_func=lambda x: quarters[x],
                    index=st.session_state.end_quarter_tab2 - 1,
                    key="end_quarter_selector",
                    help="Choose the ending quarter"
                )

            # Generate Report Button
            col_button = st.columns([1, 1, 1])
            with col_button[1]:
                if st.button(
                    "📊 Generate Report",
                    type="primary",
                    width="stretch",
                    key="generate_report_button_t"
                ):
                    # Validate quarter range
                    start_period = start_year * 10 + start_quarter
                    end_period = end_year * 10 + end_quarter
                    
                    if start_period > end_period:
                        st.error("❌ Start period cannot be greater than end period!")
                    else:
                        # Update session state when button is clicked
                        st.session_state.start_year_tab2 = start_year
                        st.session_state.end_year_tab2 = end_year
                        st.session_state.start_quarter_tab2 = start_quarter
                        st.session_state.end_quarter_tab2 = end_quarter
                        st.session_state.generate_report_tab2 = True

            # Display selected range
            period_range = (
                f"{quarters[st.session_state.start_quarter_tab2]} {st.session_state.start_year_tab2} "
                f"to {quarters[st.session_state.end_quarter_tab2]} {st.session_state.end_year_tab2}"
            )

            # Calculate total quarters
            total_quarters = (
                (st.session_state.end_year_tab2 - st.session_state.start_year_tab2) * 4 + 
                (st.session_state.end_quarter_tab2 - st.session_state.start_quarter_tab2 + 1)
            )

            st.info(
                f"📅 Selected Period: **{period_range}** | "
                f"Duration: **{total_quarters} quarter(s)**"
            )

            # Only generate report if button was clicked
            if st.session_state.generate_report_tab2:
                with st.spinner("Loading data..."):
                    # Call your function with start/end year and quarter
                    df, error, status_code = fetch_generate_quarter_wise_agging_pivot_report(
                        str(st.session_state.start_year_tab2),
                        str(st.session_state.start_quarter_tab2),
                        str(st.session_state.end_year_tab2),
                        str(st.session_state.end_quarter_tab2)
                    )
                
                if error is None and df is not None:
                    st.success("✅ Report generated successfully!")
                                        
                    # ========================================
                    # VISUALIZATIONS SECTION
                    # ========================================
                    st.header("📈 Visual Analytics")
                    
                    # Prepare data for visualizations
                    # Remove 'Grand Total' row for cleaner visualizations
                    df_viz = df[df.index != 'Grand Total'].copy()
                    
                    # Extract department names and statuses from column names
                    dept_status_cols = [col for col in df.columns if col != 'Grand Total']
                    
                    # Create tabs for different visualizations
                    viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
                        "📊 Overview Dashboard", 
                        "🔄 Open vs Closed", 
                        "🏢 Department Analysis",
                        "📋 Complaint Types"
                    ])
                    
                    with viz_tab1:
                        st.subheader("Overview Dashboard")
                        
                        # Calculate summary statistics
                        total_complaints = df.loc['Grand Total', 'Grand Total'] if 'Grand Total' in df.columns else df.sum().sum()/4
                        
                        # Separate open and closed
                        open_cols = [col for col in df.columns if 'Open' in col]
                        closed_cols = [col for col in df.columns if 'Closed' in col]
                        
                        total_open = df_viz[open_cols].sum().sum() if open_cols else 0
                        total_closed = df_viz[closed_cols].sum().sum() if closed_cols else 0
                        
                        # KPI Cards
                        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
                        with kpi_col1:
                            st.metric("📊 Total Complaints", f"{int(total_complaints):,}")
                        with kpi_col2:
                            st.metric("🟢 Closed", f"{int(total_closed):,}", 
                                    delta=f"{(total_closed/total_complaints*100):.1f}%" if total_complaints > 0 else "0%")
                        with kpi_col3:
                            st.metric("🔴 Open", f"{int(total_open):,}", 
                                    delta=f"-{(total_open/total_complaints*100):.1f}%" if total_complaints > 0 else "0%",
                                    delta_color="inverse")
                            
                        with kpi_col4:
                            closure_rate = (total_closed/total_complaints*100) if total_complaints > 0 else 0
                            st.metric("✅ Closure Rate", f"{closure_rate:.1f}%",
                                    delta="Good" if closure_rate >= 95 else "Monitor",
                                    delta_color="normal" if closure_rate >= 95 else "inverse")
                                        
                                                   
                        # Pie Chart: Open vs Closed
                        col_pie1, col_pie2 = st.columns(2)
                        
                        with col_pie1:
                            fig_pie = go.Figure(data=[go.Pie(
                                labels=['Closed', 'Open'],
                                values=[total_closed, total_open],
                                hole=0.4,
                                marker=dict(colors=['#00CC96', '#EF553B']),
                                textinfo='label+percent+value',
                                textfont_size=14
                            )])
                            fig_pie.update_layout(
                                title=dict(text="Complaint Status Distribution", font=dict(size=18)),
                                height=400,
                                showlegend=True,
                                legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
                            )
                            st.plotly_chart(fig_pie, width="stretch")
                        
                        with col_pie2:
                            # Department-wise total complaints
                            dept_totals = {}
                            for col in df.columns:
                                if col != 'Grand Total' and '_' in col:
                                    dept = col.split('_')[0]
                                    if dept not in dept_totals:
                                        dept_totals[dept] = 0
                                    dept_totals[dept] += df_viz[col].sum()
                            
                            if dept_totals:
                                fig_dept_pie = go.Figure(data=[go.Pie(
                                    labels=list(dept_totals.keys()),
                                    values=list(dept_totals.values()),
                                    hole=0.4,
                                    textinfo='label+percent',
                                    textfont_size=12
                                )])
                                fig_dept_pie.update_layout(
                                    title=dict(text="Department-wise Distribution", font=dict(size=18)),
                                    height=400,
                                    showlegend=True,
                                    legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5)
                                )
                                st.plotly_chart(fig_dept_pie, width="stretch")
                    
                    with viz_tab2:
                        st.subheader("🔄 Open vs Closed Analysis")
                        
                        # Stacked bar chart by complaint type
                        complaint_types = df_viz.index.tolist()
                        
                        # Aggregate open and closed by complaint type
                        open_data = []
                        closed_data = []
                        
                        for idx in complaint_types:
                            open_sum = df_viz.loc[idx, open_cols].sum() if open_cols else 0
                            closed_sum = df_viz.loc[idx, closed_cols].sum() if closed_cols else 0
                            open_data.append(open_sum)
                            closed_data.append(closed_sum)
                        
                        fig_stacked = go.Figure()
                        fig_stacked.add_trace(go.Bar(
                            name='Closed',
                            x=complaint_types,
                            y=closed_data,
                            marker_color='#00CC96',
                            text=closed_data,
                            textposition='inside',
                            textfont=dict(color='white', size=11)
                        ))
                        fig_stacked.add_trace(go.Bar(
                            name='Open',
                            x=complaint_types,
                            y=open_data,
                            marker_color='#EF553B',
                            text=open_data,
                            textposition='inside',
                            textfont=dict(color='white', size=11)
                        ))
                        
                        fig_stacked.update_layout(
                            title=dict(text="Complaints Status by Type", font=dict(size=20)),
                            barmode='stack',
                            xaxis_title="Complaint Type",
                            yaxis_title="Number of Complaints",
                            height=500,
                            hovermode='x unified',
                            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                        )
                        st.plotly_chart(fig_stacked, width="stretch")
                        
                        # Closure rate by complaint type
                        closure_rates = []
                        for i, ct in enumerate(complaint_types):
                            total = closed_data[i] + open_data[i]
                            rate = (closed_data[i] / total * 100) if total > 0 else 0
                            closure_rates.append(rate)
                        
                        fig_closure = go.Figure()
                        fig_closure.add_trace(go.Bar(
                            x=complaint_types,
                            y=closure_rates,
                            marker=dict(
                                color=closure_rates,
                                colorscale='RdYlGn',
                                showscale=True,
                                colorbar=dict(title="Rate %")
                            ),
                            text=[f"{rate:.1f}%" for rate in closure_rates],
                            textposition='outside'
                        ))
                        
                        fig_closure.update_layout(
                            title=dict(text="Closure Rate by Complaint Type", font=dict(size=20)),
                            xaxis_title="Complaint Type",
                            yaxis_title="Closure Rate (%)",
                            yaxis=dict(range=[0, 105]),
                            height=500,
                            hovermode='x'
                        )
                        st.plotly_chart(fig_closure, width="stretch")
                    
                    with viz_tab3:
                        st.subheader("🏢 Department-wise Analysis")
                        
                        # Create department comparison
                        dept_open_closed = {}
                        for col in df.columns:
                            if col != 'Grand Total' and '_' in col:
                                dept, status = col.rsplit('_', 1)
                                if dept not in dept_open_closed:
                                    dept_open_closed[dept] = {'Open': 0, 'Closed': 0}
                                if 'Open' in status:
                                    dept_open_closed[dept]['Open'] += df_viz[col].sum()
                                elif 'Closed' in status:
                                    dept_open_closed[dept]['Closed'] += df_viz[col].sum()
                        
                        if dept_open_closed:
                            depts = list(dept_open_closed.keys())
                            open_vals = [dept_open_closed[d]['Open'] for d in depts]
                            closed_vals = [dept_open_closed[d]['Closed'] for d in depts]
                            
                            # Grouped bar chart
                            fig_dept_grouped = go.Figure()
                            fig_dept_grouped.add_trace(go.Bar(
                                name='Open',
                                x=depts,
                                y=open_vals,
                                marker_color='#EF553B',
                                text=open_vals,
                                textposition='outside'
                            ))
                            fig_dept_grouped.add_trace(go.Bar(
                                name='Closed',
                                x=depts,
                                y=closed_vals,
                                marker_color='#00CC96',
                                text=closed_vals,
                                textposition='outside'
                            ))
                            
                            fig_dept_grouped.update_layout(
                                title=dict(text="Department Performance: Open vs Closed", font=dict(size=20)),
                                xaxis_title="Department",
                                yaxis_title="Number of Complaints",
                                barmode='group',
                                height=500,
                                hovermode='x unified',
                                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                            )
                            st.plotly_chart(fig_dept_grouped, width="stretch")
                            
                            # Department efficiency heatmap
                            dept_complaint_matrix = []
                            for ct in complaint_types:
                                row_data = []
                                for dept in depts:
                                    dept_cols = [col for col in df.columns if col.startswith(dept + '_')]
                                    total = df_viz.loc[ct, dept_cols].sum() if dept_cols else 0
                                    row_data.append(total)
                                dept_complaint_matrix.append(row_data)
                            
                            fig_heatmap = go.Figure(data=go.Heatmap(
                                z=dept_complaint_matrix,
                                x=depts,
                                y=complaint_types,
                                colorscale='Blues',
                                text=dept_complaint_matrix,
                                texttemplate='%{text}',
                                textfont={"size": 11},
                                colorbar=dict(title="Count")
                            ))
                            
                            fig_heatmap.update_layout(
                                title=dict(text="Complaint Type vs Department Heatmap", font=dict(size=20)),
                                xaxis_title="Department",
                                yaxis_title="Complaint Type",
                                height=500
                            )
                            st.plotly_chart(fig_heatmap, width="stretch")
                    
                    with viz_tab4:
                        st.subheader("📋 Complaint Type Analysis")
                        
                        # Top complaint types
                        complaint_totals = df_viz.sum(axis=1).sort_values(ascending=False)
                        top_n = min(10, len(complaint_totals))
                        
                        fig_top = go.Figure()
                        fig_top.add_trace(go.Bar(
                            x=complaint_totals.head(top_n).values,
                            y=complaint_totals.head(top_n).index,
                            orientation='h',
                            marker=dict(
                                color=complaint_totals.head(top_n).values,
                                colorscale='Viridis',
                                showscale=True
                            ),
                            text=complaint_totals.head(top_n).values,
                            textposition='outside'
                        ))
                        
                        fig_top.update_layout(
                            title=dict(text=f"Top {top_n} Complaint Types", font=dict(size=20)),
                            xaxis_title="Total Complaints",
                            yaxis_title="Complaint Type",
                            height=500,
                            yaxis=dict(autorange="reversed")
                        )
                        st.plotly_chart(fig_top, width="stretch")
                        
                        # Sunburst chart for hierarchical view
                        sunburst_data = []
                        for ct in complaint_types:
                            for col in df.columns:
                                if col != 'Grand Total' and '_' in col:
                                    dept, status = col.rsplit('_', 1)
                                    value = df_viz.loc[ct, col]
                                    if value > 0:
                                        sunburst_data.append({
                                            'Complaint Type': ct,
                                            'Department': dept,
                                            'Status': status,
                                            'Count': value
                                        })
                        
                        if sunburst_data:
                            df_sunburst = pd.DataFrame(sunburst_data)
                            
                            fig_sunburst = px.sunburst(
                                df_sunburst,
                                path=['Complaint Type', 'Department', 'Status'],
                                values='Count',
                                color='Count',
                                color_continuous_scale='RdYlGn_r',
                                title="Hierarchical View: Complaint Type → Department → Status"
                            )
                            fig_sunburst.update_layout(height=600)
                            st.plotly_chart(fig_sunburst, width="stretch")
                    
                    st.divider()
                    
                    # ========================================
                    # DATA TABLE SECTION
                    # ========================================
                    st.header("📋 Detailed Data Table")
                    
                    # Add download button
                    col_download1, col_download2, col_download3 = st.columns([1, 1, 1])
                    with col_download2:
                        csv = df.to_csv(index=True).encode('utf-8')
                        st.download_button(
                            label="📥 Download CSV",
                            data=csv,
                            file_name=f"quarterly_report_{period_range.replace(' ', '_')}.csv",
                            mime="text/csv",
                            width="stretch"
                        )
                    
                    # Display dataframe
                    st.dataframe(df, width="stretch", height=400)
                    
                    logger.info(
                        f"Tab 2: Quarterly report generated | "
                        f"start={st.session_state.start_quarter_tab2}-{st.session_state.start_year_tab2} | "
                        f"end={st.session_state.end_quarter_tab2}-{st.session_state.end_year_tab2}"
                    )
                    
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
                # ========================================
                # SECTION 1: YEAR TO DATE RANGE SELECTION
                # ========================================
                st.header("📊 Finance Year Analysis Report")
                st.caption("Select start year/date and end year/date to view analysis")

                # Initialize session state for selected years and dates
                if "start_year_tab2" not in st.session_state:
                    st.session_state.start_year_tab2 = datetime.today().year

                if "end_year_tab2" not in st.session_state:
                    st.session_state.end_year_tab2 = datetime.today().year

                if "start_date_tab2" not in st.session_state:
                    st.session_state.start_date_tab2 = "04-01"

                if "end_date_tab2" not in st.session_state:
                    st.session_state.end_date_tab2 = "03-31"

                # Initialize flag to track if report should be generated
                if "generate_report_tab2" not in st.session_state:
                    st.session_state.generate_report_tab2 = False

                # Create columns for Year selection
                col1, col2, col3 = st.columns([1, 1, 1])
                            
                with col1:
                    # Start Year selector
                    current_year = datetime.today().year
                    start_year = st.selectbox(
                        "Start Year",
                        options=list(range(current_year - 10, current_year + 1)),
                        index=list(range(current_year - 10, current_year + 1)).index(
                            st.session_state.start_year_tab2
                        ),
                        key="start_year_selector_tab2",
                        help="Choose the starting year"
                    )
                    
                    start_date_obj = st.date_input(
                        "Start Date",
                        value=datetime(start_year, 4, 1),  # Default April 1st
                        key="start_date_selector_tab2",
                        help="Choose the starting date"
                    )
                    start_date = start_date_obj.strftime("%m-%d")

                with col2:
                    # End Year selector
                    end_year = st.selectbox(
                        "End Year",
                        options=list(range(current_year - 10, current_year + 1)),
                        index=list(range(current_year - 10, current_year + 1)).index(
                            st.session_state.end_year_tab2
                        ),
                        key="end_year_selector_tab2",
                        help="Choose the ending year"
                    )
                    
                    end_date_obj = st.date_input(
                        "End Date",
                        value=datetime(end_year, 3, 31),  # Default March 31st
                        key="end_date_selector_tab2",
                        help="Choose the ending date"
                    )
                    end_date = end_date_obj.strftime("%m-%d")

                with col3:
                    st.write("")  # Spacing
                    st.write("")  # Spacing
                    if st.button(
                        "📊 Generate Report",
                        type="primary",
                        width="stretch",
                        key="generate_report_button"
                    ):
                        # Validate date range
                        start_full_date = datetime.strptime(f"{start_year}-{start_date}", "%Y-%m-%d")
                        end_full_date = datetime.strptime(f"{end_year}-{end_date}", "%Y-%m-%d")
                        
                        if start_full_date > end_full_date:
                            st.error("❌ Start date cannot be greater than end date!")
                        else:
                            # Update session state when button is clicked
                            st.session_state.start_year_tab2 = start_year
                            st.session_state.end_year_tab2 = end_year
                            st.session_state.start_date_tab2 = start_date
                            st.session_state.end_date_tab2 = end_date
                            st.session_state.generate_report_tab2 = True

                # Display selected range
                date_range = f"{st.session_state.start_year_tab2}-{st.session_state.start_date_tab2} to {st.session_state.end_year_tab2}-{st.session_state.end_date_tab2}"
                st.info(f"📅 Selected Period: **{date_range}**")

                # Only generate report if button was clicked
                if st.session_state.generate_report_tab2:
                    with st.spinner("Loading data..."):
                        # Call your function with dataset_path, start_year, start_date, end_year, end_date
                        df, error, status_code = fetch_generate_finance_year_wise_open_close_pivot_report(
                            str(st.session_state.start_year_tab2),
                            st.session_state.start_date_tab2,
                            str(st.session_state.end_year_tab2),
                            st.session_state.end_date_tab2
                        )
                    
                    if error is None and df is not None:
                        st.success("✅ Report generated successfully!")
                        
                        # Prepare data for visualizations
                        df_viz = df[df.index != 'Grand Total'].copy()
                        
                        # Calculate summary statistics
                        total_complaints = df.loc[df.index == 'Grand Total', 'Grand Total'].values[0] if 'Grand Total' in df.columns else df.sum().sum() / 4

                        
                        # Separate open and closed
                        open_cols = [col for col in df.columns if 'Open' in col]
                        closed_cols = [col for col in df.columns if 'Closed' in col]
                        
                        total_open = df_viz[open_cols].sum().sum() if open_cols else 0
                        total_closed = df_viz[closed_cols].sum().sum() if closed_cols else 0
                        
                        years_covered = st.session_state.end_year_tab2 - st.session_state.start_year_tab2 + 1
                        
                        # Display KPI Metrics
                        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                        with col_m1:
                            st.metric("📊 Total Complaints", f"{int(total_complaints):,}")
                        with col_m2:
                            st.metric("🟢 Closed", f"{int(total_closed):,}")
                        with col_m3:
                            st.metric("🔴 Open", f"{int(total_open):,}")
                        with col_m4:
                            closure_rate = (total_closed / total_complaints * 100) if total_complaints > 0 else 0
                            st.metric("✅ Closure Rate", f"{closure_rate:.1f}%")
                        with col_m5:
                            st.metric("📅 Years Covered", years_covered)
                        
                        st.divider()
                        
                        # ========================================
                        # VISUALIZATIONS SECTION
                        # ========================================
                        st.header("📈 Financial Year Analytics Dashboard")
                        
                        # Create tabs for different visualization categories
                        viz_tab1, viz_tab2, viz_tab3, viz_tab4 = st.tabs([
                            "🎯 Status Overview", 
                            "🏢 Department Analysis", 
                            "📋 Complaint Breakdown",
                            "🔥 Advanced Insights"
                        ])
                        
                        with viz_tab1:
                            st.subheader("Financial Year Status Distribution")
                            
                            col_viz1, col_viz2 = st.columns(2)
                            
                            # 1. PIE CHART - Open vs Closed
                            with col_viz1:
                                fig_pie = go.Figure(data=[go.Pie(
                                    labels=['Closed', 'Open'],
                                    values=[total_closed, total_open],
                                    marker=dict(
                                        colors=['#00CC96', '#EF553B'],
                                        line=dict(color='white', width=3)
                                    ),
                                    textinfo='label+percent+value',
                                    textfont=dict(size=16, family='Arial Black'),
                                    pull=[0.08, 0.12],
                                    hole=0
                                )])
                                fig_pie.update_layout(
                                    title=dict(
                                        text="<b>Overall Complaint Status</b><br><sub>Pie Chart Distribution</sub>", 
                                        font=dict(size=19), 
                                        x=0.5, 
                                        xanchor='center'
                                    ),
                                    height=480,
                                    showlegend=True,
                                    legend=dict(
                                        orientation="h", 
                                        yanchor="bottom", 
                                        y=-0.2, 
                                        xanchor="center", 
                                        x=0.5,
                                        font=dict(size=13)
                                    )
                                )
                                st.plotly_chart(fig_pie, width="stretch")
                            
                            # 2. DONUT CHART - Department-wise Distribution
                            with col_viz2:
                                dept_totals = {}
                                for col in df.columns:
                                    if col != 'Grand Total' and '_' in col:
                                        dept = col.split('_')[0]
                                        if dept not in dept_totals:
                                            dept_totals[dept] = 0
                                        dept_totals[dept] += df_viz[col].sum()
                                
                                if dept_totals:
                                    fig_donut = go.Figure(data=[go.Pie(
                                        labels=list(dept_totals.keys()),
                                        values=list(dept_totals.values()),
                                        hole=0.55,
                                        textinfo='label+percent',
                                        textfont=dict(size=14, family='Arial'),
                                        marker=dict(
                                            line=dict(color='white', width=3),
                                            colors=px.colors.qualitative.Set2
                                        )
                                    )])
                                    fig_donut.update_layout(
                                        title=dict(
                                            text="<b>Department-wise Distribution</b><br><sub>Donut Chart</sub>", 
                                            font=dict(size=19), 
                                            x=0.5, 
                                            xanchor='center'
                                        ),
                                        height=480,
                                        showlegend=True,
                                        legend=dict(
                                            orientation="h", 
                                            yanchor="bottom", 
                                            y=-0.2, 
                                            xanchor="center", 
                                            x=0.5,
                                            font=dict(size=13)
                                        ),
                                        annotations=[dict(
                                            text=f'<b>{int(total_complaints):,}</b><br><span style="font-size:14px">Total<br>Complaints</span>', 
                                            x=0.5, 
                                            y=0.5, 
                                            font_size=22, 
                                            showarrow=False
                                        )]
                                    )
                                    st.plotly_chart(fig_donut, width="stretch")
                            
                            # 3. STACKED BAR CHART - Complaints by Type
                            st.subheader("Complaint Type Analysis")
                            
                            complaint_types = df_viz.index.tolist()
                            open_data = []
                            closed_data = []
                            
                            for idx in complaint_types:
                                open_sum = df_viz.loc[idx, open_cols].sum() if open_cols else 0
                                closed_sum = df_viz.loc[idx, closed_cols].sum() if closed_cols else 0
                                open_data.append(open_sum)
                                closed_data.append(closed_sum)
                            
                            fig_bar_stacked = go.Figure()
                            fig_bar_stacked.add_trace(go.Bar(
                                name='Closed',
                                x=complaint_types,
                                y=closed_data,
                                marker=dict(
                                    color='#00CC96',
                                    line=dict(color='darkgreen', width=1.5)
                                ),
                                text=closed_data,
                                textposition='inside',
                                textfont=dict(color='white', size=13, family='Arial Black'),
                                hovertemplate='<b>%{x}</b><br>Closed: %{y:,}<extra></extra>'
                            ))
                            fig_bar_stacked.add_trace(go.Bar(
                                name='Open',
                                x=complaint_types,
                                y=open_data,
                                marker=dict(
                                    color='#EF553B',
                                    line=dict(color='darkred', width=1.5)
                                ),
                                text=open_data,
                                textposition='inside',
                                textfont=dict(color='white', size=13, family='Arial Black'),
                                hovertemplate='<b>%{x}</b><br>Open: %{y:,}<extra></extra>'
                            ))
                            
                            fig_bar_stacked.update_layout(
                                title=dict(
                                    text="<b>Complaint Status by Type</b><br><sub>Stacked Bar Chart</sub>", 
                                    font=dict(size=21), 
                                    x=0.5, 
                                    xanchor='center'
                                ),
                                barmode='stack',
                                xaxis_title="<b>Complaint Type</b>",
                                yaxis_title="<b>Number of Complaints</b>",
                                height=580,
                                hovermode='x unified',
                                legend=dict(
                                    orientation="h", 
                                    yanchor="bottom", 
                                    y=1.02, 
                                    xanchor="right", 
                                    x=1,
                                    font=dict(size=14)
                                ),
                                xaxis=dict(tickangle=-45, tickfont=dict(size=11))
                            )
                            st.plotly_chart(fig_bar_stacked, width="stretch")
                            
                            # Closure Rate by Complaint Type
                            st.subheader("Closure Efficiency Analysis")
                            
                            closure_rates = []
                            for i in range(len(complaint_types)):
                                total = closed_data[i] + open_data[i]
                                rate = (closed_data[i] / total * 100) if total > 0 else 0
                                closure_rates.append(rate)
                            
                            fig_closure = go.Figure()
                            fig_closure.add_trace(go.Bar(
                                x=complaint_types,
                                y=closure_rates,
                                marker=dict(
                                    color=closure_rates,
                                    colorscale='RdYlGn',
                                    showscale=True,
                                    colorbar=dict(title="<b>Rate %</b>", titleside='right'),
                                    line=dict(color='black', width=1.5)
                                ),
                                text=[f"{rate:.1f}%" for rate in closure_rates],
                                textposition='outside',
                                textfont=dict(size=13, family='Arial Black'),
                                hovertemplate='<b>%{x}</b><br>Closure Rate: %{y:.1f}%<extra></extra>'
                            ))
                            
                            fig_closure.update_layout(
                                title=dict(
                                    text="<b>Closure Rate by Complaint Type</b><br><sub>Color-coded Bar Chart</sub>", 
                                    font=dict(size=21), 
                                    x=0.5, 
                                    xanchor='center'
                                ),
                                xaxis_title="<b>Complaint Type</b>",
                                yaxis_title="<b>Closure Rate (%)</b>",
                                yaxis=dict(range=[0, 108]),
                                height=550,
                                hovermode='x',
                                xaxis=dict(tickangle=-45, tickfont=dict(size=11))
                            )
                            st.plotly_chart(fig_closure, width="stretch")
                        
                        with viz_tab2:
                            st.subheader("Department Performance Metrics")
                            
                            # Create department comparison
                            dept_open_closed = {}
                            for col in df.columns:
                                if col != 'Grand Total' and '_' in col:
                                    dept, status = col.rsplit('_', 1)
                                    if dept not in dept_open_closed:
                                        dept_open_closed[dept] = {'Open': 0, 'Closed': 0}
                                    if 'Open' in status:
                                        dept_open_closed[dept]['Open'] += df_viz[col].sum()
                                    elif 'Closed' in status:
                                        dept_open_closed[dept]['Closed'] += df_viz[col].sum()
                            
                            if dept_open_closed:
                                depts = list(dept_open_closed.keys())
                                open_vals = [dept_open_closed[d]['Open'] for d in depts]
                                closed_vals = [dept_open_closed[d]['Closed'] for d in depts]
                                
                                # 4. GROUPED BAR CHART - Department Performance
                                st.subheader("Department Comparison")
                                
                                fig_dept_grouped = go.Figure()
                                fig_dept_grouped.add_trace(go.Bar(
                                    name='Open',
                                    x=depts,
                                    y=open_vals,
                                    marker=dict(
                                        color='#EF553B',
                                        line=dict(color='darkred', width=2)
                                    ),
                                    text=open_vals,
                                    textposition='outside',
                                    textfont=dict(size=14, family='Arial Black'),
                                    hovertemplate='<b>%{x}</b><br>Open: %{y:,}<extra></extra>'
                                ))
                                fig_dept_grouped.add_trace(go.Bar(
                                    name='Closed',
                                    x=depts,
                                    y=closed_vals,
                                    marker=dict(
                                        color='#00CC96',
                                        line=dict(color='darkgreen', width=2)
                                    ),
                                    text=closed_vals,
                                    textposition='outside',
                                    textfont=dict(size=14, family='Arial Black'),
                                    hovertemplate='<b>%{x}</b><br>Closed: %{y:,}<extra></extra>'
                                ))
                                
                                fig_dept_grouped.update_layout(
                                    title=dict(
                                        text="<b>Department Performance: Open vs Closed</b><br><sub>Grouped Bar Chart</sub>", 
                                        font=dict(size=21), 
                                        x=0.5, 
                                        xanchor='center'
                                    ),
                                    xaxis_title="<b>Department</b>",
                                    yaxis_title="<b>Number of Complaints</b>",
                                    barmode='group',
                                    height=580,
                                    hovermode='x unified',
                                    legend=dict(
                                        orientation="h", 
                                        yanchor="bottom", 
                                        y=1.02, 
                                        xanchor="right", 
                                        x=1,
                                        font=dict(size=14)
                                    )
                                )
                                st.plotly_chart(fig_dept_grouped, width="stretch")
                                
                                # 5. HEATMAP - Department vs Complaint Type
                                st.subheader("Complaint Distribution Matrix")
                                
                                dept_complaint_matrix = []
                                for ct in complaint_types:
                                    row_data = []
                                    for dept in depts:
                                        dept_cols = [col for col in df.columns if col.startswith(dept + '_')]
                                        total = df_viz.loc[ct, dept_cols].sum() if dept_cols else 0
                                        row_data.append(total)
                                    dept_complaint_matrix.append(row_data)
                                
                                fig_heatmap = go.Figure(data=go.Heatmap(
                                    z=dept_complaint_matrix,
                                    x=depts,
                                    y=complaint_types,
                                    colorscale='YlOrRd',
                                    text=dept_complaint_matrix,
                                    texttemplate='<b>%{text}</b>',
                                    textfont=dict(size=13, family='Arial Black'),
                                    colorbar=dict(
                                        title="<b>Complaint<br>Count</b>", 
                                        titleside='right',
                                        titlefont=dict(size=13)
                                    ),
                                    hovertemplate='<b>Type:</b> %{y}<br><b>Dept:</b> %{x}<br><b>Count:</b> %{z:,}<extra></extra>'
                                ))
                                
                                fig_heatmap.update_layout(
                                    title=dict(
                                        text="<b>Complaint Type vs Department Intensity</b><br><sub>Heatmap Visualization</sub>", 
                                        font=dict(size=21), 
                                        x=0.5, 
                                        xanchor='center'
                                    ),
                                    xaxis_title="<b>Department</b>",
                                    yaxis_title="<b>Complaint Type</b>",
                                    height=650,
                                    xaxis=dict(side='bottom', tickfont=dict(size=12)),
                                    yaxis=dict(tickmode='linear', tickfont=dict(size=11))
                                )
                                st.plotly_chart(fig_heatmap, width="stretch")
                                
                                # Department Efficiency Metrics
                                st.subheader("Department Efficiency Score")
                                
                                dept_efficiency = []
                                for dept in depts:
                                    total = open_vals[depts.index(dept)] + closed_vals[depts.index(dept)]
                                    closed = closed_vals[depts.index(dept)]
                                    efficiency = (closed / total * 100) if total > 0 else 0
                                    dept_efficiency.append(efficiency)
                                
                                fig_efficiency = go.Figure()
                                fig_efficiency.add_trace(go.Bar(
                                    x=depts,
                                    y=dept_efficiency,
                                    marker=dict(
                                        color=dept_efficiency,
                                        colorscale='RdYlGn',
                                        showscale=True,
                                        colorbar=dict(title="<b>Efficiency<br>%</b>", titleside='right'),
                                        line=dict(color='black', width=2)
                                    ),
                                    text=[f"{eff:.1f}%" for eff in dept_efficiency],
                                    textposition='outside',
                                    textfont=dict(size=15, family='Arial Black'),
                                    hovertemplate='<b>%{x}</b><br>Efficiency: %{y:.1f}%<extra></extra>'
                                ))
                                
                                # Add target line at 80%
                                fig_efficiency.add_hline(
                                    y=80, 
                                    line_dash="dash", 
                                    line_color="blue", 
                                    annotation_text="Target: 80%",
                                    annotation_position="right"
                                )
                                
                                fig_efficiency.update_layout(
                                    title=dict(
                                        text="<b>Department Closure Efficiency</b><br><sub>Performance Bar Chart</sub>", 
                                        font=dict(size=21), 
                                        x=0.5, 
                                        xanchor='center'
                                    ),
                                    xaxis_title="<b>Department</b>",
                                    yaxis_title="<b>Closure Rate (%)</b>",
                                    yaxis=dict(range=[0, 108]),
                                    height=550,
                                    hovermode='x'
                                )
                                st.plotly_chart(fig_efficiency, width="stretch")
                        
                        with viz_tab3:
                            st.subheader("Complaint Type Deep Analysis")
                            
                            # 6. TREEMAP - Hierarchical View
                            st.subheader("Hierarchical Distribution View")
                            
                            treemap_data = []
                            for ct in complaint_types:
                                for col in df.columns:
                                    if col != 'Grand Total' and '_' in col:
                                        parts = col.rsplit('_', 1)
                                        if len(parts) == 2:
                                            dept, status = parts
                                            value = df_viz.loc[ct, col]
                                            if value > 0:
                                                treemap_data.append({
                                                    'Complaint Type': ct,
                                                    'Department': dept,
                                                    'Status': status,
                                                    'Count': value
                                                })
                            
                            if treemap_data:
                                df_treemap = pd.DataFrame(treemap_data)
                                
                                # Create treemap
                                fig_treemap = px.treemap(
                                    df_treemap,
                                    path=['Complaint Type', 'Department', 'Status'],
                                    values='Count',
                                    color='Count',
                                    color_continuous_scale='Turbo',
                                    title="<b>Complaint Hierarchy Treemap</b><br><sub>Complaint Type → Department → Status</sub>"
                                )
                                fig_treemap.update_layout(
                                    height=680,
                                    title=dict(font=dict(size=21), x=0.5, xanchor='center')
                                )
                                fig_treemap.update_traces(
                                    textinfo="label+value+percent parent",
                                    textfont=dict(size=13, family='Arial'),
                                    marker=dict(line=dict(width=2, color='white'))
                                )
                                st.plotly_chart(fig_treemap, width="stretch")
                            
                            # Bubble Chart - Department Performance
                            st.subheader("Department Performance Bubble Analysis")
                            
                            if dept_open_closed:
                                bubble_data = []
                                for dept in depts:
                                    total = dept_open_closed[dept]['Open'] + dept_open_closed[dept]['Closed']
                                    closed = dept_open_closed[dept]['Closed']
                                    efficiency = (closed / total * 100) if total > 0 else 0
                                    bubble_data.append({
                                        'Department': dept,
                                        'Total': total,
                                        'Closed': closed,
                                        'Open': dept_open_closed[dept]['Open'],
                                        'Efficiency': efficiency
                                    })
                                
                                df_bubble = pd.DataFrame(bubble_data)
                                
                                fig_bubble = px.scatter(
                                    df_bubble,
                                    x='Total',
                                    y='Efficiency',
                                    size='Total',
                                    color='Efficiency',
                                    hover_name='Department',
                                    text='Department',
                                    color_continuous_scale='RdYlGn',
                                    size_max=70,
                                    title="<b>Department Performance Bubble Chart</b><br><sub>Bubble size = Total Complaints | Color = Efficiency</sub>"
                                )
                                fig_bubble.update_traces(
                                    textposition='top center',
                                    textfont=dict(size=13, family='Arial Black'),
                                    marker=dict(line=dict(width=2, color='DarkSlateGrey'))
                                )
                                fig_bubble.update_layout(
                                    height=600,
                                    title=dict(font=dict(size=21), x=0.5, xanchor='center'),
                                    xaxis_title="<b>Total Complaints</b>",
                                    yaxis_title="<b>Closure Rate (%)</b>",
                                    xaxis=dict(tickfont=dict(size=12)),
                                    yaxis=dict(
                                        range=[0, 108],
                                        tickfont=dict(size=12)
                                    )
                                )
                                st.plotly_chart(fig_bubble, width="stretch")
                            
                            # Waterfall Chart - Status Breakdown
                            st.subheader("Complaint Status Waterfall")
                            
                            waterfall_values = []
                            waterfall_labels = []
                            waterfall_measure = []
                            
                            # Start with total
                            waterfall_labels.append("Total Complaints")
                            waterfall_values.append(total_complaints)
                            waterfall_measure.append("absolute")
                            
                            # Add closed
                            waterfall_labels.append("Closed")
                            waterfall_values.append(-total_closed)
                            waterfall_measure.append("relative")
                            
                            # Add open
                            waterfall_labels.append("Open Remaining")
                            waterfall_values.append(total_open)
                            waterfall_measure.append("total")
                            
                            fig_waterfall = go.Figure(go.Waterfall(
                                name="Status Flow",
                                orientation="v",
                                measure=waterfall_measure,
                                x=waterfall_labels,
                                textposition="outside",
                                text=[f"{abs(v):,.0f}" for v in waterfall_values],
                                y=waterfall_values,
                                connector={"line": {"color": "rgb(63, 63, 63)"}},
                                decreasing={"marker": {"color": "#00CC96"}},
                                increasing={"marker": {"color": "#EF553B"}},
                                totals={"marker": {"color": "#636EFA"}}
                            ))
                            
                            fig_waterfall.update_layout(
                                title=dict(
                                    text="<b>Complaint Status Waterfall</b><br><sub>Flow from Total to Open</sub>",
                                    font=dict(size=21),
                                    x=0.5,
                                    xanchor='center'
                                ),
                                height=550,
                                showlegend=False,
                                xaxis_title="<b>Status Category</b>",
                                yaxis_title="<b>Number of Complaints</b>"
                            )
                            st.plotly_chart(fig_waterfall, width="stretch")

                            # Top Complaint Types
                            st.subheader("Top Complaint Rankings")
                            
                            complaint_totals = df_viz.sum(axis=1).sort_values(ascending=False)
                            top_n = min(12, len(complaint_totals))
                            
                            fig_top = go.Figure()
                            fig_top.add_trace(go.Bar(
                                x=complaint_totals.head(top_n).values,
                                y=complaint_totals.head(top_n).index,
                                orientation='h',
                                marker=dict(
                                    color=complaint_totals.head(top_n).values,
                                    colorscale='Viridis',
                                    showscale=True,
                                    colorbar=dict(title="<b>Total<br>Count</b>", titleside='right'),
                                    line=dict(color='black', width=1.5)
                                ),
                                text=complaint_totals.head(top_n).values,
                                textposition='outside',
                                textfont=dict(size=14, family='Arial Black'),
                                hovertemplate='<b>%{y}</b><br>Total: %{x:,}<extra></extra>'
                            ))
                            
                            fig_top.update_layout(
                                title=dict(
                                    text=f"<b>Top {top_n} Complaint Types</b><br><sub>Ranked Horizontal Bar Chart</sub>", 
                                    font=dict(size=21), 
                                    x=0.5, 
                                    xanchor='center'
                                ),
                                xaxis_title="<b>Total Complaints</b>",
                                yaxis_title="<b>Complaint Type</b>",
                                height=600,
                                yaxis=dict(autorange="reversed", tickfont=dict(size=11))
                            )
                            st.plotly_chart(fig_top, width="stretch")
                        
                        
                        with viz_tab4:
                            st.subheader("Advanced Analytics & Insights")
                            
                            # 7. MOSAIC PLOT - Composition Analysis
                            st.subheader("Complaint Composition Analysis")
                            
                            mosaic_data = []
                            for ct in complaint_types:
                                ct_total = df_viz.loc[ct].sum()
                                if ct_total > 0:
                                    for col in df.columns:
                                        if col != 'Grand Total' and '_' in col:
                                            parts = col.rsplit('_', 1)
                                            if len(parts) == 2:
                                                dept, status = parts
                                                value = df_viz.loc[ct, col]
                                                pct = (value / ct_total) * 100
                                                mosaic_data.append({
                                                    'Complaint Type': ct,
                                                    'Department_Status': f"{dept} - {status}",
                                                    'Count': value,
                                                    'Percentage': pct
                                                })
                            
                            if mosaic_data:
                                df_mosaic = pd.DataFrame(mosaic_data)
                                
                                fig_mosaic = go.Figure()
                                
                                dept_status_unique = df_mosaic['Department_Status'].unique()
                                colors = px.colors.qualitative.Bold[:len(dept_status_unique)]
                                
                                for idx, ds in enumerate(dept_status_unique):
                                    subset = df_mosaic[df_mosaic['Department_Status'] == ds]
                                    fig_mosaic.add_trace(go.Bar(
                                        name=ds,
                                        x=subset['Complaint Type'],
                                        y=subset['Percentage'],
                                        text=subset['Count'],
                                        textposition='inside',
                                        textfont=dict(size=11, color='white', family='Arial Black'),
                                        marker=dict(
                                            color=colors[idx % len(colors)],
                                            line=dict(color='white', width=1.5)
                                        ),
                                        hovertemplate='<b>%{x}</b><br>' + ds + '<br>Count: %{text:,}<br>Percentage: %{y:.1f}%<extra></extra>'
                                    ))
                                
                                fig_mosaic.update_layout(
                                    title=dict(
                                        text="<b>Complaint Type Composition</b><br><sub>Mosaic Plot (100% Stacked)</sub>", 
                                        font=dict(size=21), 
                                        x=0.5, 
                                        xanchor='center'
                                    ),
                                    barmode='stack',
                                    xaxis_title="<b>Complaint Type</b>",
                                    yaxis_title="<b>Percentage (%)</b>",
                                    height=650,
                                    hovermode='x unified',
                                    legend=dict(
                                        orientation="v",
                                        yanchor="middle",
                                        y=0.5,
                                        xanchor="left",
                                        x=1.02,
                                        title="<b>Department - Status</b>",
                                        font=dict(size=11)
                                    ),
                                    xaxis=dict(tickangle=-45, tickfont=dict(size=10)),
                                    yaxis=dict(range=[0, 100])
                                )
                                st.plotly_chart(fig_mosaic, width="stretch")
                            
                            # Sunburst Chart
                            st.subheader("Interactive Sunburst Hierarchy")
                            
                            # Prepare sunburst data (reuse treemap_data structure)
                            sunburst_data = []
                            for ct in complaint_types:
                                for col in df.columns:
                                    if col != 'Grand Total' and '_' in col:
                                        parts = col.rsplit('_', 1)
                                        if len(parts) == 2:
                                            dept, status = parts
                                            value = df_viz.loc[ct, col]
                                            if value > 0:
                                                sunburst_data.append({
                                                    'Complaint Type': ct,
                                                    'Department': dept,
                                                    'Status': status,
                                                    'Count': value
                                                })
                            
                            if sunburst_data:
                                df_sunburst = pd.DataFrame(sunburst_data)
                                
                                fig_sunburst = px.sunburst(
                                    df_sunburst,
                                    path=['Complaint Type', 'Department', 'Status'],
                                    values='Count',
                                    color='Count',
                                    color_continuous_scale='Viridis',
                                    hover_data={'Count': ':,'}
                                )
                                
                                fig_sunburst.update_traces(
                                    textinfo='label+percent parent',
                                    hovertemplate='<b>%{label}</b><br>Count: %{value:,}<br>Percentage: %{percentParent:.1f}%<extra></extra>'
                                )
                                
                                fig_sunburst.update_layout(
                                    title=dict(
                                        text="<b>Hierarchical Complaint Distribution</b><br><sub>Complaint Type → Department → Status</sub>",
                                        font=dict(size=21),
                                        x=0.5,
                                        xanchor='center'
                                    ),
                                    height=700,
                                    margin=dict(t=100, l=0, r=0, b=0)
                                )
                                
                                st.plotly_chart(fig_sunburst, width="stretch")
                                
                        st.divider()
                        
                        # ========================================
                        # DATA TABLE SECTION
                        # ========================================
                        st.header("📋 Detailed Data Table")
                        
                        # Add download and export options
                        col_export1, col_export2, col_export3 = st.columns([1, 1, 1])
                        
                        with col_export2:
                            csv = df.to_csv(index=True).encode('utf-8')
                            st.download_button(
                                label="📥 Download CSV Report",
                                data=csv,
                                file_name=f"finance_year_report_{date_range.replace(' ', '_').replace('/', '-')}.csv",
                                mime="text/csv",
                                width="stretch",
                                type="primary"
                            )
                        
                        # Display dataframe with enhanced styling
                        st.dataframe(
                            df,
                            width="stretch",
                            height=450
                        )
                        
                        logger.info(f"Tab 2: Finance year report generated | range={date_range}")
                        
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
                                
                                
                                




            # ===============================
            # SECTION 2: MONTH WISE OPEN/CLOSE COMPLAINTS PIVOT
            # ===============================

            st.divider()

            # Initialize session state
            if 'report_generated' not in st.session_state:
                st.session_state.report_generated = False
            if 'selected_month' not in st.session_state:
                st.session_state.selected_month = None
            if 'dataset_path' not in st.session_state:
                st.session_state.dataset_path = None

            # Load and cache the Excel data ONCE
            @st.cache_data(ttl=600)
            def load_excel_data(file_path):
                """Load and cache Excel data"""
                df = pd.read_excel(file_path)
                df['DATE'] = pd.to_datetime(df['DATE'])
                return df

            # Filter monthly data (cached)
            @st.cache_data(ttl=600)
            def get_month_data(df, selected_month):
                """Filter data for selected month"""
                return df[df['DATE'].dt.to_period('M') == selected_month]

            # Enhanced report functions
            @st.cache_data(ttl=600)
            def generate_complaint_report(month_df):
                result = month_df['COMPLAINT TYPE'].value_counts().reset_index()
                result.columns = ['Complaint Type', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def generate_date_report(month_df):
                result = month_df['DATE'].value_counts().sort_index().reset_index()
                result.columns = ['Date', 'Count']
                result['Day of Week'] = pd.to_datetime(result['Date']).dt.day_name()
                return result

            @st.cache_data(ttl=600)
            def generate_shift_duty_report(month_df):
                result = month_df['SHIFT DUTY'].value_counts().reset_index()
                result.columns = ['Shift Duty', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def generate_monthly_qrc_data(month_df):
                result = month_df['QUERY/REQUEST/COMPLAINT'].value_counts().reset_index()
                result.columns = ['QRC Type', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_section_data(month_df):
                result = month_df['SECTION'].value_counts().reset_index()
                result.columns = ['Section', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_subdivision_data(month_df):
                result = month_df['SUB-DIVISION'].value_counts().reset_index()
                result.columns = ['Sub-Division', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_circle_data(month_df):
                result = month_df['CIRCLE'].value_counts().reset_index()
                result.columns = ['Circle', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_consumer_number_data(month_df):
                result = month_df['CONSUMER NUMBER'].value_counts().reset_index()
                result.columns = ['Consumer Number', 'Count']
                return result

            @st.cache_data(ttl=600)
            def get_monthly_mobile_number_data(month_df):
                result = month_df['MOBILE NUMB'].value_counts().reset_index()
                result.columns = ['Mobile Number', 'Count']
                return result

            @st.cache_data(ttl=600)
            def get_monthly_dept_data(month_df):
                result = month_df['DEPT'].value_counts().reset_index()
                result.columns = ['Department', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_status_data(month_df):
                result = month_df['CLOSED/OPEN'].value_counts().reset_index()
                result.columns = ['Status', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_pscc_data(month_df):
                result = month_df['PSCC/FG/TO'].value_counts().reset_index()
                result.columns = ['PSCC Type', 'Count']
                result['Percentage'] = (result['Count'] / result['Count'].sum() * 100).round(2)
                return result

            @st.cache_data(ttl=600)
            def get_monthly_minute_data(month_df):
                result = month_df['MINUTE'].value_counts().reset_index()
                result.columns = ['Minute', 'Count']
                return result

            @st.cache_data(ttl=600)
            def get_monthly_remarks_analysis(month_df):
                """Analyze REMARKS column for patterns"""
                temp_df = month_df.copy()
                
                if 'REMARKS' not in temp_df.columns:
                    return {
                        'Appreciation Tweets': 0,
                        'Awaited Consumer': 0,
                        '5-digit Numbers': 0,
                        'Total Remarks': 0
                    }
                
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

            @st.cache_data(ttl=600)
            def get_performance_metrics(month_df):
                """Calculate advanced performance metrics"""
                metrics = {}
                
                # Average resolution time
                if 'MINUTE' in month_df.columns:
                    metrics['avg_resolution_time'] = month_df['MINUTE'].mean()
                    metrics['median_resolution_time'] = month_df['MINUTE'].median()
                    metrics['max_resolution_time'] = month_df['MINUTE'].max()
                    metrics['min_resolution_time'] = month_df['MINUTE'].min()
                
                # Daily averages
                metrics['avg_daily_complaints'] = len(month_df) / month_df['DATE'].nunique()
                
                # Peak hours analysis
                if 'SHIFT DUTY' in month_df.columns:
                    peak_shift = month_df['SHIFT DUTY'].value_counts().idxmax()
                    metrics['peak_shift'] = peak_shift
                
                return metrics

            @st.cache_data(ttl=600)
            def get_trend_analysis(month_df):
                """Analyze trends over the month"""
                daily_counts = month_df.groupby(month_df['DATE'].dt.date).size().reset_index()
                daily_counts.columns = ['Date', 'Count']
                
                # Calculate trend
                if len(daily_counts) > 1:
                    daily_counts['Trend'] = daily_counts['Count'].diff()
                    daily_counts['7-Day Moving Avg'] = daily_counts['Count'].rolling(window=7, min_periods=1).mean()
                
                return daily_counts


            # Main App
            st.markdown("## 📊 Month Wise Complaint Analysis Dashboard")
            st.markdown("### Comprehensive Analytics & Insights Platform")

            if dataset_path is not None:
                if "dataset_path" not in st.session_state or st.session_state.dataset_path != dataset_path:
                    st.session_state.dataset_path = dataset_path
                    st.session_state.report_generated = False
                
                try:
                    df = load_excel_data(dataset_path)
                    
                    # Enhanced month and year selectors
                    st.markdown("### 📅 Select Analysis Period")
                    col_month, col_year, col_space = st.columns([1, 1, 2])
                    with col_month:
                        month = st.selectbox(
                            "Month", 
                            list(range(1, 13)), 
                            format_func=lambda x: pd.to_datetime(str(x), format="%m").strftime("%B"),
                            key='tab2_month_selector'
                        )
                    with col_year:
                        year = st.selectbox(
                            "Year", 
                            list(range(2020, 2031)),
                            key='tab2_year_selector'
                        )

                    selected_month = pd.Period(f"{year}-{month:02d}", freq='M')
                    
                    if st.session_state.selected_month != str(selected_month):
                        st.session_state.selected_month = str(selected_month)
                        st.session_state.report_generated = False

                    st.markdown("---")
                    generate_button = st.button("🔍 Generate Comprehensive Report", type="primary", width="stretch", key='tab2_generate_btn')

                    if generate_button or st.session_state.report_generated:
                        if generate_button:
                            st.session_state.report_generated = True
                        
                        try:
                            with st.spinner("🔄 Generating comprehensive analytics..."):
                                month_df = get_month_data(df, selected_month)

                                if len(month_df) == 0:
                                    st.warning(f"⚠️ No data found for {selected_month.strftime('%B %Y')}")
                                else:
                                    # Generate all reports
                                    complaint_report = generate_complaint_report(month_df)
                                    date_report = generate_date_report(month_df)
                                    shift_report = generate_shift_duty_report(month_df)
                                    qrc_report = generate_monthly_qrc_data(month_df)
                                    section_report = get_monthly_section_data(month_df)
                                    subdivision_report = get_monthly_subdivision_data(month_df)
                                    circle_report = get_monthly_circle_data(month_df)
                                    consumer_number_report = get_monthly_consumer_number_data(month_df)
                                    mobile_number_report = get_monthly_mobile_number_data(month_df)
                                    dept_report = get_monthly_dept_data(month_df)
                                    status_report = get_monthly_status_data(month_df)
                                    pscc_report = get_monthly_pscc_data(month_df)
                                    minute_report = get_monthly_minute_data(month_df)
                                    remarks_report = get_monthly_remarks_analysis(month_df)
                                    performance_metrics = get_performance_metrics(month_df)
                                    trend_data = get_trend_analysis(month_df)

                                    # Enhanced Summary Metrics Section
                                    st.markdown("## 📊 Executive Summary")
                                    st.markdown(f"### Analysis for **{selected_month.strftime('%B %Y')}**")
                                    
                                    metric_cols = st.columns(6)
                                    
                                    with metric_cols[0]:
                                        st.metric("📋 Total Records", f"{len(month_df):,}", help="Total number of complaints/queries received")
                                    with metric_cols[1]:
                                        st.metric("📂 Complaint Types", month_df['COMPLAINT TYPE'].nunique(), help="Unique types of complaints")
                                    with metric_cols[2]:
                                        st.metric("📅 Active Days", month_df['DATE'].nunique(), help="Days with recorded complaints")
                                    with metric_cols[3]:
                                        closed_count = status_report[status_report['Status'] == 'CLOSED']['Count'].sum() if len(status_report) > 0 else 0
                                        total_count = status_report['Count'].sum() if len(status_report) > 0 else 1
                                        closure_rate = (closed_count / total_count * 100) if total_count > 0 else 0
                                        st.metric("✅ Closure Rate", f"{closure_rate:.1f}%", help="Percentage of closed cases")
                                    with metric_cols[4]:
                                        avg_daily = performance_metrics.get('avg_daily_complaints', 0)
                                        st.metric("📈 Daily Average", f"{avg_daily:.1f}", help="Average complaints per day")
                                    with metric_cols[5]:
                                        if 'avg_resolution_time' in performance_metrics:
                                            st.metric("⏱️ Avg Resolution", f"{performance_metrics['avg_resolution_time']:.0f} min", help="Average time to resolve")
                                        else:
                                            st.metric("⏱️ Avg Resolution", "N/A")

                                    st.markdown("---")
                                    
                                    # Create enhanced tabs
                                    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
                                        "📊 Overview & Analysis", 
                                        "🔍 Detailed Reports", 
                                        "📈 Data Visualizations", 
                                        "🎯 Remarks & Insights",
                                        "📉 Trends & Performance",
                                        "🔎 Advanced Filters"
                                    ])
                                    
                                    # Tab 1: Overview & Analysis
                                    with tab1:
                                        st.markdown("### 🎯 Key Metrics Overview")
                                        
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("#### 📋 Complaint Type Distribution")
                                            st.dataframe(
                                                complaint_report.style.background_gradient(subset=['Count'], cmap='Blues'),
                                                width="stretch", 
                                                height=400
                                            )
                                            
                                            fig = px.pie(
                                                complaint_report, 
                                                values='Count', 
                                                names='Complaint Type',
                                                title="Complaint Type Breakdown",
                                                hole=0.4,
                                                color_discrete_sequence=px.colors.qualitative.Set3
                                            )
                                            fig.update_traces(textposition='inside', textinfo='percent+label')
                                            fig.update_layout(height=500)
                                            st.plotly_chart(fig, width="stretch", key='complaint_pie_main')
                                        
                                        with col2:
                                            st.markdown("#### 🔄 Status Overview")
                                            st.dataframe(
                                                status_report.style.background_gradient(subset=['Count'], cmap='RdYlGn'),
                                                width="stretch",
                                                height=400
                                            )
                                            
                                            fig = px.pie(
                                                status_report, 
                                                values='Count', 
                                                names='Status',
                                                title="Case Status Distribution",
                                                color='Status',
                                                color_discrete_map={'CLOSED': '#00CC96', 'OPEN': '#EF553B'},
                                                hole=0.4
                                            )
                                            fig.update_traces(textposition='inside', textinfo='percent+label')
                                            fig.update_layout(height=500)
                                            st.plotly_chart(fig, width="stretch", key='status_pie_main')
                                        
                                        st.markdown("---")
                                        
                                        col3, col4 = st.columns(2)
                                        
                                        with col3:
                                            st.markdown("#### ⏰ Shift Distribution")
                                            st.dataframe(
                                                shift_report.style.background_gradient(subset=['Count'], cmap='Greens'),
                                                width="stretch",
                                                height=350
                                            )
                                            
                                            fig = px.bar(
                                                shift_report, 
                                                x='Shift Duty', 
                                                y='Count',
                                                title="Complaints by Shift",
                                                color='Count',
                                                color_continuous_scale='Viridis',
                                                text='Count'
                                            )
                                            fig.update_traces(texttemplate='%{text}', textposition='outside')
                                            fig.update_layout(height=450)
                                            st.plotly_chart(fig, width="stretch", key='shift_bar_main')
                                        
                                        with col4:
                                            st.markdown("#### 📝 QRC Analysis")
                                            st.dataframe(
                                                qrc_report.style.background_gradient(subset=['Count'], cmap='Purples'),
                                                width="stretch",
                                                height=350
                                            )
                                            
                                            fig = px.bar(
                                                qrc_report, 
                                                x='QRC Type', 
                                                y='Count',
                                                title="Query/Request/Complaint Distribution",
                                                color='Count',
                                                color_continuous_scale='Plasma',
                                                text='Count'
                                            )
                                            fig.update_traces(texttemplate='%{text}', textposition='outside')
                                            fig.update_layout(height=450)
                                            st.plotly_chart(fig, width="stretch", key='qrc_bar_main')

                                            st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                                    
                                    # Tab 2: Detailed Reports
                                    with tab2:
                                        st.markdown("### 📑 Comprehensive Data Reports")
                                        
                                        report_selector = st.selectbox(
                                            "Select Report Category:",
                                            ["Geographic Analysis", "Department & Section", "Contact Information", "Time Analysis"],
                                            key='report_selector_tab2'
                                        )
                                        
                                        if report_selector == "Geographic Analysis":
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.markdown("#### 🏘️ Sub-Division Analysis")
                                                st.dataframe(
                                                    subdivision_report.style.background_gradient(subset=['Count'], cmap='YlOrRd'),
                                                    width="stretch",
                                                    height=450
                                                )
                                                
                                                fig = px.treemap(
                                                    subdivision_report.head(15),
                                                    path=['Sub-Division'],
                                                    values='Count',
                                                    title="Top 15 Sub-Divisions (Treemap)",
                                                    color='Count',
                                                    color_continuous_scale='RdYlGn'
                                                )
                                                fig.update_layout(height=500)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            with col2:
                                                st.markdown("#### 🔵 Circle Analysis")
                                                st.dataframe(
                                                    circle_report.style.background_gradient(subset=['Count'], cmap='Blues'),
                                                    width="stretch",
                                                    height=450
                                                )
                                                
                                                fig = px.bar(
                                                    circle_report.head(15),
                                                    y='Circle',
                                                    x='Count',
                                                    orientation='h',
                                                    title="Top 15 Circles",
                                                    color='Count',
                                                    color_continuous_scale='Teal',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=500)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            st.markdown("#### 🏢 Section Analysis")
                                            st.dataframe(
                                                section_report.style.background_gradient(subset=['Count'], cmap='Oranges'),
                                                width="stretch",
                                                height=400
                                            )
                                        
                                        elif report_selector == "Department & Section":
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.markdown("#### 🏛️ Department Distribution")
                                                st.dataframe(
                                                    dept_report.style.background_gradient(subset=['Count'], cmap='Purples'),
                                                    width="stretch",
                                                    height=500
                                                )
                                                
                                                fig = px.sunburst(
                                                    dept_report.head(10),
                                                    path=['Department'],
                                                    values='Count',
                                                    title="Department Hierarchy"
                                                )
                                                fig.update_layout(height=600)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            with col2:
                                                st.markdown("#### 📞 PSCC/FG/TO Analysis")
                                                st.dataframe(
                                                    pscc_report.style.background_gradient(subset=['Count'], cmap='Greens'),
                                                    width="stretch",
                                                    height=500
                                                )
                                                
                                                fig = px.pie(
                                                    pscc_report,
                                                    values='Count',
                                                    names='PSCC Type',
                                                    title="PSCC Type Distribution",
                                                    hole=0.3
                                                )
                                                fig.update_layout(height=600)
                                                st.plotly_chart(fig, width="stretch")
                                        
                                        elif report_selector == "Contact Information":
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.markdown("#### 👤 Top Consumer Numbers")
                                                st.dataframe(
                                                    consumer_number_report.head(25).style.background_gradient(subset=['Count'], cmap='YlGnBu'),
                                                    width="stretch",
                                                    height=600
                                                )
                                            
                                            with col2:
                                                st.markdown("#### 📱 Top Mobile Numbers")
                                                st.dataframe(
                                                    mobile_number_report.head(25).style.background_gradient(subset=['Count'], cmap='YlOrBr'),
                                                    width="stretch",
                                                    height=600
                                                )
                                        
                                        else:  # Time Analysis
                                            st.markdown("#### ⏱️ Resolution Time Analysis")
                                            st.dataframe(
                                                minute_report.head(30).style.background_gradient(subset=['Count'], cmap='RdYlGn_r'),
                                                width="stretch",
                                                height=450
                                            )
                                            
                                            fig = px.histogram(
                                                month_df,
                                                x='MINUTE',
                                                nbins=50,
                                                title="Distribution of Resolution Times",
                                                labels={'MINUTE': 'Minutes', 'count': 'Frequency'},
                                                color_discrete_sequence=['#636EFA']
                                            )
                                            fig.update_layout(height=500)
                                            st.plotly_chart(fig, width="stretch")
                                    
                                    # Tab 3: Data Visualizations
                                    with tab3:
                                        st.markdown("### 📊 Interactive Data Visualizations")
                                        
                                        viz_category = st.radio(
                                            "Select Visualization Category:",
                                            ["Primary Metrics", "Geographic Insights", "Time-based Analysis", "Comparative Views"],
                                            horizontal=True,
                                            key='viz_category_tab3'
                                        )
                                        
                                        if viz_category == "Primary Metrics":
                                            st.markdown("#### 📋 Complaint Analysis")
                                            
                                            chart_type = st.radio(
                                                "Visualization Type:",
                                                ["Horizontal Bar", "Vertical Bar", "Donut Chart", "Treemap"],
                                                horizontal=True,
                                                key='primary_chart_type'
                                            )
                                            
                                            if chart_type == "Horizontal Bar":
                                                fig = px.bar(
                                                    complaint_report,
                                                    y='Complaint Type',
                                                    x='Count',
                                                    orientation='h',
                                                    title="Complaint Type Distribution (Horizontal)",
                                                    color='Count',
                                                    color_continuous_scale='Viridis',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=600)
                                            elif chart_type == "Vertical Bar":
                                                fig = px.bar(
                                                    complaint_report,
                                                    x='Complaint Type',
                                                    y='Count',
                                                    title="Complaint Type Distribution (Vertical)",
                                                    color='Count',
                                                    color_continuous_scale='Blues',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=600)
                                            elif chart_type == "Donut Chart":
                                                fig = px.pie(
                                                    complaint_report,
                                                    values='Count',
                                                    names='Complaint Type',
                                                    title="Complaint Type Distribution",
                                                    hole=0.5
                                                )
                                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                                fig.update_layout(height=600)
                                            else:
                                                fig = px.treemap(
                                                    complaint_report,
                                                    path=['Complaint Type'],
                                                    values='Count',
                                                    title="Complaint Type Hierarchy",
                                                    color='Count',
                                                    color_continuous_scale='RdYlGn'
                                                )
                                                fig.update_layout(height=600)
                                            
                                            st.plotly_chart(fig, width="stretch")
                                        
                                        elif viz_category == "Geographic Insights":
                                            geo_col1, geo_col2 = st.columns(2)
                                            
                                            with geo_col1:
                                                fig = px.bar(
                                                    subdivision_report.head(12),
                                                    y='Sub-Division',
                                                    x='Count',
                                                    orientation='h',
                                                    title="Top 12 Sub-Divisions",
                                                    color='Count',
                                                    color_continuous_scale='Reds',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=550)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            with geo_col2:
                                                fig = px.sunburst(
                                                    circle_report.head(12),
                                                    path=['Circle'],
                                                    values='Count',
                                                    title="Circle Distribution (Sunburst)"
                                                )
                                                fig.update_layout(height=550)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            fig = px.bar(
                                                section_report.head(15),
                                                x='Section',
                                                y='Count',
                                                title="Top 15 Sections by Count",
                                                color='Count',
                                                color_continuous_scale='Teal',
                                                text='Count'
                                            )
                                            fig.update_traces(texttemplate='%{text}', textposition='outside')
                                            fig.update_layout(height=500, xaxis_tickangle=-45)
                                            st.plotly_chart(fig, width="stretch")
                                        
                                        elif viz_category == "Time-based Analysis":
                                            st.markdown("#### 📅 Daily Trends")
                                            
                                            fig = px.line(
                                                date_report,
                                                x='Date',
                                                y='Count',
                                                title="Daily Complaint Trends",
                                                markers=True,
                                                color_discrete_sequence=['#FF6692']
                                            )
                                            fig.update_traces(line=dict(width=3), marker=dict(size=8))
                                            fig.update_layout(height=500)
                                            st.plotly_chart(fig, width="stretch")
                                            
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                day_of_week_counts = date_report.groupby('Day of Week')['Count'].sum().reset_index()
                                                day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                                                day_of_week_counts['Day of Week'] = pd.Categorical(day_of_week_counts['Day of Week'], categories=day_order, ordered=True)
                                                day_of_week_counts = day_of_week_counts.sort_values('Day of Week')
                                                
                                                fig = px.bar(
                                                    day_of_week_counts,
                                                    x='Day of Week',
                                                    y='Count',
                                                    title="Complaints by Day of Week",
                                                    color='Count',
                                                    color_continuous_scale='Blues'
                                                )
                                                fig.update_layout(height=450)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            with col2:
                                                fig = px.bar(
                                                    shift_report,
                                                    x='Shift Duty',
                                                    y='Count',
                                                    title="Shift-wise Distribution",
                                                    color='Count',
                                                    color_continuous_scale='Greens',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=450)
                                                st.plotly_chart(fig, width="stretch")
                                        
                                        else:  # Comparative Views
                                            st.markdown("#### 🔄 Multi-dimensional Comparison")
                                            
                                            comp_col1, comp_col2, comp_col3 = st.columns(3)
                                            
                                            with comp_col1:
                                                fig = px.pie(
                                                    complaint_report.head(8),
                                                    values='Count',
                                                    names='Complaint Type',
                                                    title="Top Complaints",
                                                    hole=0.4
                                                )
                                                fig.update_layout(height=400)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            with comp_col2:
                                                fig = px.pie(
                                                    status_report,
                                                    values='Count',
                                                    names='Status',
                                                    title="Status Split",
                                                    color='Status',
                                                    color_discrete_map={'CLOSED': '#00CC96', 'OPEN': '#EF553B'},
                                                    hole=0.4
                                                )
                                                fig.update_layout(height=400)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            with comp_col3:
                                                fig = px.pie(
                                                    qrc_report,
                                                    values='Count',
                                                    names='QRC Type',
                                                    title="QRC Distribution",
                                                    hole=0.4
                                                )
                                                fig.update_layout(height=400)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            # Stacked comparison
                                            st.markdown("#### 📊 Department vs Status Comparison")
                                            if len(dept_report) > 0 and len(status_report) > 0:
                                                dept_status = month_df.groupby(['DEPT', 'CLOSED/OPEN']).size().reset_index(name='Count')
                                                fig = px.bar(
                                                    dept_status.head(30),
                                                    x='DEPT',
                                                    y='Count',
                                                    color='CLOSED/OPEN',
                                                    title="Department-wise Status Distribution",
                                                    barmode='stack',
                                                    color_discrete_map={'CLOSED': '#00CC96', 'OPEN': '#EF553B'}
                                                )
                                                fig.update_layout(height=500, xaxis_tickangle=-45)
                                                st.plotly_chart(fig, width="stretch")
                                    
                                    # Tab 4: Remarks & Insights
                                    with tab4:
                                        st.markdown("### 💬 Remarks Analysis & Insights")
                                        
                                        remark_cols = st.columns(4)
                                        
                                        with remark_cols[0]:
                                            st.metric("📝 Total Remarks", f"{remarks_report['Total Remarks']:,}")
                                        with remark_cols[1]:
                                            st.metric("👍 Appreciation Tweets", remarks_report['Appreciation Tweets'])
                                        with remark_cols[2]:
                                            st.metric("⏳ Awaited Consumer", remarks_report['Awaited Consumer'])
                                        with remark_cols[3]:
                                            st.metric("🔢 5-digit Numbers", remarks_report['5-digit Numbers'])
                                        
                                        st.markdown("---")
                                        
                                        remarks_viz_data = pd.DataFrame({
                                            'Category': ['Appreciation Tweets', 'Awaited Consumer', '5-digit Numbers'],
                                            'Count': [
                                                remarks_report['Appreciation Tweets'],
                                                remarks_report['Awaited Consumer'],
                                                remarks_report['5-digit Numbers']
                                            ]
                                        })
                                        
                                        if remarks_viz_data['Count'].sum() > 0:
                                            viz_col1, viz_col2 = st.columns(2)
                                            
                                            with viz_col1:
                                                fig = px.bar(
                                                    remarks_viz_data,
                                                    x='Category',
                                                    y='Count',
                                                    title="Remarks Pattern Distribution",
                                                    color='Count',
                                                    color_continuous_scale='Viridis',
                                                    text='Count'
                                                )
                                                fig.update_traces(texttemplate='%{text}', textposition='outside')
                                                fig.update_layout(height=500)
                                                st.plotly_chart(fig, width="stretch")
                                            
                                            with viz_col2:
                                                fig = px.pie(
                                                    remarks_viz_data[remarks_viz_data['Count'] > 0],
                                                    values='Count',
                                                    names='Category',
                                                    title="Remarks Category Breakdown",
                                                    hole=0.5
                                                )
                                                fig.update_traces(textposition='inside', textinfo='percent+label')
                                                fig.update_layout(height=500)
                                                st.plotly_chart(fig, width="stretch")
                                        else:
                                            st.info("ℹ️ No specific remarks patterns found in the selected month.")
                                        
                                        st.markdown("---")
                                        st.markdown("#### 📋 Sample Remarks Data")
                                        if 'REMARKS' in month_df.columns:
                                            sample_remarks_df = month_df[['DATE', 'COMPLAINT TYPE', 'REMARKS']].head(20)
                                            st.dataframe(
                                                sample_remarks_df.style.set_properties(**{'text-align': 'left'}),
                                                width="stretch",
                                                height=450
                                            )
                                        else:
                                            st.info("ℹ️ REMARKS column not found in dataset")
                                    
                                    # Tab 5: Trends & Performance
                                    with tab5:
                                        st.markdown("### 📉 Trends & Performance Analytics")
                                        
                                        perf_col1, perf_col2, perf_col3, perf_col4 = st.columns(4)
                                        
                                        with perf_col1:
                                            st.metric("📊 Daily Avg", f"{performance_metrics.get('avg_daily_complaints', 0):.1f} cases")
                                        with perf_col2:
                                            if 'avg_resolution_time' in performance_metrics:
                                                st.metric("⏱️ Avg Time", f"{performance_metrics['avg_resolution_time']:.0f} min")
                                            else:
                                                st.metric("⏱️ Avg Time", "N/A")
                                        with perf_col3:
                                            if 'median_resolution_time' in performance_metrics:
                                                st.metric("📍 Median Time", f"{performance_metrics['median_resolution_time']:.0f} min")
                                            else:
                                                st.metric("📍 Median Time", "N/A")
                                        with perf_col4:
                                            if 'peak_shift' in performance_metrics:
                                                st.metric("🔥 Peak Shift", performance_metrics['peak_shift'])
                                            else:
                                                st.metric("🔥 Peak Shift", "N/A")
                                        
                                        st.markdown("---")
                                        
                                        st.markdown("#### 📈 Daily Trend Analysis")
                                        st.dataframe(
                                            trend_data.style.background_gradient(subset=['Count'], cmap='YlOrRd'),
                                            width="stretch",
                                            height=400
                                        )
                                        
                                        fig = px.line(
                                            trend_data,
                                            x='Date',
                                            y='Count',
                                            title="Daily Complaint Volume Trend",
                                            markers=True
                                        )
                                        if '7-Day Moving Avg' in trend_data.columns:
                                            fig.add_scatter(x=trend_data['Date'], y=trend_data['7-Day Moving Avg'], 
                                                        mode='lines', name='7-Day Moving Average',
                                                        line=dict(color='red', width=2, dash='dash'))
                                        fig.update_layout(height=550)
                                        st.plotly_chart(fig, width="stretch")
                                        
                                        col1, col2 = st.columns(2)
                                        
                                        with col1:
                                            st.markdown("#### 🎯 Performance Summary")
                                            perf_summary = pd.DataFrame({
                                                'Metric': ['Total Cases', 'Avg Daily', 'Peak Day Count', 'Lowest Day Count'],
                                                'Value': [
                                                    len(month_df),
                                                    f"{performance_metrics.get('avg_daily_complaints', 0):.1f}",
                                                    trend_data['Count'].max(),
                                                    trend_data['Count'].min()
                                                ]
                                            })
                                            st.dataframe(perf_summary, width="stretch", height=250)
                                        
                                        with col2:
                                            if 'avg_resolution_time' in performance_metrics:
                                                st.markdown("#### ⏱️ Resolution Time Stats")
                                                time_stats = pd.DataFrame({
                                                    'Statistic': ['Average', 'Median', 'Minimum', 'Maximum'],
                                                    'Minutes': [
                                                        f"{performance_metrics.get('avg_resolution_time', 0):.0f}",
                                                        f"{performance_metrics.get('median_resolution_time', 0):.0f}",
                                                        f"{performance_metrics.get('min_resolution_time', 0):.0f}",
                                                        f"{performance_metrics.get('max_resolution_time', 0):.0f}"
                                                    ]
                                                })
                                                st.dataframe(time_stats, width="stretch", height=250)
                                    
                                                                        # Tab 6: Advanced Filters
                                    # Tab 6: Advanced Filters
                                    with tab6:
                                        st.markdown("### 🔎 Advanced Data Filtering & Export")
                                        
                                        st.markdown("#### 🎛️ Filter Controls")
                                        filter_col1, filter_col2, filter_col3 = st.columns(3)
                                        
                                        with filter_col1:
                                            selected_complaint = st.multiselect(
                                                "🔹 Complaint Type",
                                                options=sorted(month_df['COMPLAINT TYPE'].dropna().unique()),
                                                key='complaint_filter_tab6'
                                            )
                                        
                                        with filter_col2:
                                            selected_shift = st.multiselect(
                                                "⏰ Shift Duty",
                                                options=sorted(month_df['SHIFT DUTY'].dropna().unique()),
                                                key='shift_filter_tab6'
                                            )
                                        
                                        with filter_col3:
                                            selected_status = st.multiselect(
                                                "🔄 Status",
                                                options=sorted(month_df['CLOSED/OPEN'].dropna().unique()),
                                                key='status_filter_tab6'
                                            )
                                        
                                        filter_col4, filter_col5, filter_col6 = st.columns(3)
                                        
                                        with filter_col4:
                                            selected_dept = st.multiselect(
                                                "🏛️ Department",
                                                options=sorted(month_df['DEPT'].dropna().unique()),
                                                key='dept_filter_tab6'
                                            )
                                        
                                        with filter_col5:
                                            selected_section = st.multiselect(
                                                "🏢 Section",
                                                options=sorted(month_df['SECTION'].dropna().unique()),
                                                key='section_filter_tab6'
                                            )
                                        
                                        with filter_col6:
                                            selected_circle = st.multiselect(
                                                "🔵 Circle",
                                                options=sorted(month_df['CIRCLE'].dropna().unique()),
                                                key='circle_filter_tab6'
                                            )
                                        
                                        # Apply filters
                                        filtered_df = month_df.copy()
                                        
                                        if selected_complaint:
                                            filtered_df = filtered_df[filtered_df['COMPLAINT TYPE'].isin(selected_complaint)]
                                        if selected_shift:
                                            filtered_df = filtered_df[filtered_df['SHIFT DUTY'].isin(selected_shift)]
                                        if selected_status:
                                            filtered_df = filtered_df[filtered_df['CLOSED/OPEN'].isin(selected_status)]
                                        if selected_dept:
                                            filtered_df = filtered_df[filtered_df['DEPT'].isin(selected_dept)]
                                        if selected_section:
                                            filtered_df = filtered_df[filtered_df['SECTION'].isin(selected_section)]
                                        if selected_circle:
                                            filtered_df = filtered_df[filtered_df['CIRCLE'].isin(selected_circle)]
                                        
                                        st.markdown("---")
                                        st.markdown(f"#### 📊 Filtered Results: **{len(filtered_df):,}** records")
                                        
                                        if len(filtered_df) > 0:
                                            # Show filtered summary
                                            summary_col1, summary_col2, summary_col3, summary_col4 = st.columns(4)
                                            
                                            with summary_col1:
                                                st.metric("Total Records", f"{len(filtered_df):,}")
                                            with summary_col2:
                                                closed_filtered = (filtered_df['CLOSED/OPEN'] == 'CLOSED').sum()
                                                closure_filtered = (closed_filtered / len(filtered_df) * 100) if len(filtered_df) > 0 else 0
                                                st.metric("Closure Rate", f"{closure_filtered:.1f}%")
                                            with summary_col3:
                                                st.metric("Complaint Types", filtered_df['COMPLAINT TYPE'].nunique())
                                            with summary_col4:
                                                if 'MINUTE' in filtered_df.columns:
                                                    avg_time_filtered = filtered_df['MINUTE'].mean()
                                                    st.metric("Avg Time", f"{avg_time_filtered:.0f} min")
                                                else:
                                                    st.metric("Avg Time", "N/A")
                                            
                                            st.markdown("---")
                                            st.dataframe(
                                                filtered_df.style.set_properties(**{'text-align': 'left'}),
                                                width="stretch",
                                                height=500
                                            )
                                            
                                            # Download options
                                            st.markdown("#### 📥 Export Options")
                                            download_col1, download_col2 = st.columns(2)
                                            
                                            with download_col1:
                                                csv = filtered_df.to_csv(index=False).encode('utf-8')
                                                st.download_button(
                                                    label="📄 Download as CSV",
                                                    data=csv,
                                                    file_name=f'filtered_data_{selected_month}.csv',
                                                    mime='text/csv',
                                                    width="stretch",
                                                    key='download_csv_tab6'
                                                )
                                            
                                            with download_col2:
                                                # Create Excel file in memory
                                                from io import BytesIO
                                                buffer = BytesIO()
                                                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                                                    filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
                                                buffer.seek(0)
                                                
                                                st.download_button(
                                                    label="📊 Download as Excel",
                                                    data=buffer,
                                                    file_name=f'filtered_data_{selected_month}.xlsx',
                                                    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                                    width="stretch",
                                                    key='download_excel_tab6'
                                                )
                                        else:
                                            st.warning("⚠️ No records match the selected filters. Please adjust your criteria.")

                                    st.markdown("---")
                                    st.success("✅ Report generated successfully!")
                                    
                        except Exception as e:
                            st.error(f"❌ Error processing data: {str(e)}")
                            st.info("💡 Please ensure your Excel file has all required columns")
                            st.session_state.report_generated = False
                    else:
                        st.info("👆 Select a month and year from the dropdowns above, then click 'Generate Comprehensive Report'")
                
                except Exception as e:
                    st.error(f"❌ Error loading file: {str(e)}")
                    st.info("💡 Please check if the file path is correct and the file exists")
            else:
                st.warning("⚠️ Please provide a valid dataset path to begin analysis")
                st.info("💡 Set the `dataset_path` variable to point to your Excel file")
                    

            st.divider()
            # Add your Streamlit code for Tab 2 here



    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Unhandled error in Streamlit dashboard Tab 2 | error={error_msg}")
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)
