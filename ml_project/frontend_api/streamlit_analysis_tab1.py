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
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from ml_project.backend_api.api_url import fastapi_api_request_url, flask_api_request_url
from ml_project.backend_api.fastapi_analysis_helper import open_complaint_pivot
from ml_project.frontend_api.streamlit_analysis_helper import generate_all_agging_complaint_report,style_grand_total_dataframe
from ml_project.utils.helper import read_yaml
from ml_project.logger.custom_logger import get_logger
from ml_project.exceptions.exception import CustomException
from ml_project.frontend_api.streamlit_cache_data import (
    fetch_open_complaint_pivot,
    fetch_open_close_complaint_pivot,
    fetch_agging_open_pivot,
    fetch_agging_open_close_pivot,
    fetch_open_close_complaint_report,
    fetch_all_agging_complaint_report,
    fetch_close_power_outage_duration )

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



# Pie Chart , donut chart, mosaic plot, marimekko chart,sunburst chart,sankey diagram,parallel sets,network diagram,polar area chart,Heatmap 
# multi-line chart, Area Chart by Category, stacked area chart, scatter plot with hue,dot plot by category, Choropleth Map, Dot Density Map
# Funnel Chart, Mixed Subplots
# 3d pie chart,3D 3D Bar Chart, 3D Column Chart,3d treemap,3d line plot,3D Scatter Plot,3D Histogram,3d bubble chart,3D Grouped Bar Chart,3d choropleth map
#JSON Schema Tree,Tree View

logger = get_logger(__name__)


def streamlit_analysis_tab1(tab1, dataset_path, logger):
    """
    Renders all content for Tab 1 including complaint reports and power outage analysis.
    
    Parameters:
    -----------
    tab1 : streamlit.tabs
        The Streamlit tab container where content will be rendered
    dataset_path : str
        Path to the dataset file
    logger : logging.Logger
        Logger instance for logging operations
    """
    try:    

        with tab1:
            # ========================================
            # SECTION 1: OPEN COMPLAINTS PIVOT
            # ========================================
            
            # Add button to fetch data
            if st.button("📥 Load Open Complaints Data", key="load_complaints_btn", type="primary"):
                with st.spinner("Loading data..."):
                    df_pivot, error, status_code = fetch_open_complaint_pivot()

                if error is None and df_pivot is not None:
                    st.subheader("📊 Open Complaints Dashboard")
                    st.caption("Grand Total row is highlighted in red for easy identification")

                    # Display the styled dataframe
                    styled_df = style_grand_total_dataframe(df_pivot)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}") 

                    st.markdown("## 📊 Open Complaints Pie Chart")

                    # Prepare data for visualization
                    # Convert dict/DataFrame to proper format
                    if isinstance(df_pivot, dict):
                        df = pd.DataFrame(df_pivot)
                    else:
                        df = df_pivot.copy()
                    
                    # Set COMPLAINT TYPE as index if it exists as a column
                    if 'COMPLAINT TYPE' in df.columns:
                        df = df.set_index('COMPLAINT TYPE')
                    
                    # Remove Grand_Total column and Grand Total row for cleaner visualization
                    if 'Grand_Total' in df.columns:
                        df_viz = df.drop(columns=['Grand_Total'])
                    else:
                        df_viz = df.copy()
                    
                    df_viz = df_viz[df_viz.index != 'Grand_Total'].copy() if 'Grand_Total' in df_viz.index else df_viz.copy()
                    
                    # Get total complaints per category (sum across columns)
                    if len(df_viz.columns) > 0:
                        totals = df_viz.sum(axis=1)
                        totals = totals[totals > 0]  # Remove zero values
                        
                        if len(totals) > 0:
                            # Create 3D Pie Chart with Plotly
                            fig = go.Figure(data=[go.Pie(
                                labels=totals.index.astype(str),  # Ensure labels are strings
                                values=totals.values,
                                hole=0.3,  # Donut chart style
                                pull=[0.05] * len(totals),  # Slightly separate slices
                                marker=dict(
                                    colors=px.colors.qualitative.Plotly,  # Mixed vibrant colors
                                    line=dict(color='white', width=2)
                                ),
                                textinfo='label+percent',
                                textposition='auto',
                                hovertemplate='<b>%{label}</b><br>' +
                                            'Complaints: %{value}<br>' +
                                            'Percentage: %{percent}<br>' +
                                            '<extra></extra>'
                            )])
                            
                            # Update layout for better appearance with bigger size
                            fig.update_layout(
                                title={
                                    'text': '🎯 Complaints Distribution by Category',
                                    'x': 0.5,
                                    'xanchor': 'center',
                                    'font': {'size': 20, 'color': '#1f77b4'}
                                },
                                showlegend=True,
                                legend=dict(
                                    orientation="v",
                                    yanchor="middle",
                                    y=0.5,
                                    xanchor="left",
                                    x=1.05,
                                    font=dict(size=11)
                                ),
                                height=600,  # Bigger chart height
                                margin=dict(l=20, r=150, t=80, b=20),
                                paper_bgcolor='rgba(0,0,0,0)',
                                plot_bgcolor='rgba(0,0,0,0)'
                            )
                            
                            # Add 3D effect using scene configuration
                            fig.update_traces(
                                rotation=90,
                                pull=[0.1 if i == totals.values.argmax() else 0.02 
                                    for i in range(len(totals))]  # Pull out largest slice
                            )
                            
                            st.plotly_chart(fig, use_container_width=True)


                            st.markdown("## 🍩 Open Complaints Donut Chart")

                            # Prepare data for donut visualization
                            if isinstance(df_pivot, dict):
                                df_donut = pd.DataFrame(df_pivot)
                            else:
                                df_donut = df_pivot.copy()

                            # Set COMPLAINT TYPE as index if it exists as a column
                            if 'COMPLAINT TYPE' in df_donut.columns:
                                df_donut = df_donut.set_index('COMPLAINT TYPE')

                            # Remove Grand_Total column and Grand Total row for cleaner visualization
                            if 'Grand_Total' in df_donut.columns:
                                df_donut_viz = df_donut.drop(columns=['Grand_Total'])
                            else:
                                df_donut_viz = df_donut.copy()

                            df_donut_viz = df_donut_viz[df_donut_viz.index != 'Grand_Total'].copy() if 'Grand_Total' in df_donut_viz.index else df_donut_viz.copy()

                            # Get total complaints per category (sum across columns)
                            if len(df_donut_viz.columns) > 0:
                                totals_donut = df_donut_viz.sum(axis=1)
                                totals_donut = totals_donut[totals_donut > 0]  # Remove zero values
                                
                                if len(totals_donut) > 0:
                                    # Create Donut Chart with Plotly
                                    fig_donut = go.Figure(data=[go.Pie(
                                        labels=totals_donut.index.astype(str),
                                        values=totals_donut.values,
                                        hole=0.5,  # Larger hole for donut effect
                                        pull=[0.08] * len(totals_donut),
                                        marker=dict(
                                            colors=px.colors.qualitative.Bold,  # Different color palette
                                            line=dict(color='white', width=3)
                                        ),
                                        textinfo='label+value',
                                        textposition='outside',
                                        hovertemplate='<b>%{label}</b><br>' +
                                                    'Total: %{value}<br>' +
                                                    'Share: %{percent}<br>' +
                                                    '<extra></extra>'
                                    )])
                                    
                                    # Update layout
                                    fig_donut.update_layout(
                                        title={
                                            'text': '🎯 Complaints by Category - Donut View',
                                            'x': 0.5,
                                            'xanchor': 'center',
                                            'font': {'size': 20, 'color': '#2ca02c'}
                                        },
                                        showlegend=True,
                                        legend=dict(
                                            orientation="h",
                                            yanchor="bottom",
                                            y=-0.2,
                                            xanchor="center",
                                            x=0.5,
                                            font=dict(size=11)
                                        ),
                                        height=600,
                                        margin=dict(l=20, r=20, t=80, b=100),
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        annotations=[dict(
                                            text=f'Total<br>{int(totals_donut.sum())}',
                                            x=0.5, y=0.5,
                                            font_size=24,
                                            showarrow=False,
                                            font_color='#333333'
                                        )]
                                    )
                                    
                                    # Highlight the largest slice
                                    fig_donut.update_traces(
                                        pull=[0.15 if i == totals_donut.values.argmax() else 0.05 
                                            for i in range(len(totals_donut))]
                                    )
                                    
                                    st.plotly_chart(fig_donut, use_container_width=True)
                                    
                                else:
                                    st.warning("No complaint data available for donut chart")
                            else:
                                st.warning("No columns found in the data for donut chart")


                            st.markdown("## 📊 Open Complaints Marimekko Chart")

                            # Prepare data for Marimekko visualization
                            if isinstance(df_pivot, dict):
                                df_marimekko = pd.DataFrame(df_pivot)
                            else:
                                df_marimekko = df_pivot.copy()

                            # Set COMPLAINT TYPE as index if it exists as a column
                            if 'COMPLAINT TYPE' in df_marimekko.columns:
                                df_marimekko = df_marimekko.set_index('COMPLAINT TYPE')

                            # Remove Grand_Total column and Grand Total row for cleaner visualization
                            if 'Grand_Total' in df_marimekko.columns:
                                df_marimekko_viz = df_marimekko.drop(columns=['Grand_Total'])
                            else:
                                df_marimekko_viz = df_marimekko.copy()

                            df_marimekko_viz = df_marimekko_viz[df_marimekko_viz.index != 'Grand_Total'].copy() if 'Grand_Total' in df_marimekko_viz.index else df_marimekko_viz.copy()

                            # Get data for Marimekko chart
                            if len(df_marimekko_viz.columns) > 0 and len(df_marimekko_viz) > 0:
                                # Calculate totals and proportions
                                category_totals = df_marimekko_viz.sum(axis=1)
                                category_totals = category_totals[category_totals > 0]
                                
                                if len(category_totals) > 0:
                                    # Prepare data for Marimekko chart using shapes
                                    fig_marimekko = go.Figure()
                                    
                                    # Calculate cumulative widths for positioning
                                    total_complaints = category_totals.sum()
                                    cumulative_x = 0
                                    colors = px.colors.qualitative.Vivid
                                    
                                    # Store all rectangles and annotations
                                    shapes = []
                                    annotations = []
                                    legend_traces = []
                                    
                                    for idx, (category, total) in enumerate(category_totals.items()):
                                        # Width proportional to total complaints in category
                                        width = (total / total_complaints) * 100
                                        
                                        # Get subcategory breakdown if available
                                        if len(df_marimekko_viz.columns) > 1:
                                            subcategories = df_marimekko_viz.loc[category]
                                            subcategories = subcategories[subcategories > 0]
                                            
                                            cumulative_y = 0
                                            for sub_idx, (subcategory, value) in enumerate(subcategories.items()):
                                                height = (value / total) * 100
                                                
                                                # Calculate opacity for subcategories
                                                opacity = 0.6 + (sub_idx * 0.15)
                                                if opacity > 1:
                                                    opacity = 0.6 + ((sub_idx % 3) * 0.15)
                                                
                                                # Add rectangle shape
                                                shapes.append(dict(
                                                    type="rect",
                                                    x0=cumulative_x,
                                                    x1=cumulative_x + width,
                                                    y0=cumulative_y,
                                                    y1=cumulative_y + height,
                                                    fillcolor=colors[idx % len(colors)],
                                                    opacity=opacity,
                                                    line=dict(color='white', width=2)
                                                ))
                                                
                                                # Add annotation for label (only if rectangle is large enough)
                                                if height > 5 and width > 5:
                                                    annotations.append(dict(
                                                        x=cumulative_x + width/2,
                                                        y=cumulative_y + height/2,
                                                        text=f'{subcategory}<br>{int(value)}',
                                                        showarrow=False,
                                                        font=dict(size=9, color='white'),
                                                        align='center'
                                                    ))
                                                
                                                # Add invisible scatter trace for legend
                                                legend_traces.append(go.Scatter(
                                                    x=[cumulative_x + width/2],
                                                    y=[cumulative_y + height/2],
                                                    mode='markers',
                                                    marker=dict(size=10, color=colors[idx % len(colors)], opacity=opacity),
                                                    name=f'{category} - {subcategory}',
                                                    hovertemplate=f'<b>{category} - {subcategory}</b><br>' +
                                                                f'Count: {int(value)}<br>' +
                                                                f'Category %: {height:.1f}%<br>' +
                                                                f'Total %: {(value/total_complaints)*100:.1f}%<br>' +
                                                                '<extra></extra>',
                                                    showlegend=True
                                                ))
                                                
                                                cumulative_y += height
                                        else:
                                            # Single category without subcategories
                                            shapes.append(dict(
                                                type="rect",
                                                x0=cumulative_x,
                                                x1=cumulative_x + width,
                                                y0=0,
                                                y1=100,
                                                fillcolor=colors[idx % len(colors)],
                                                opacity=0.7,
                                                line=dict(color='white', width=2)
                                            ))
                                            
                                            annotations.append(dict(
                                                x=cumulative_x + width/2,
                                                y=50,
                                                text=f'{category}<br>{int(total)}',
                                                showarrow=False,
                                                font=dict(size=10, color='white', weight='bold'),
                                                align='center'
                                            ))
                                            
                                            legend_traces.append(go.Scatter(
                                                x=[cumulative_x + width/2],
                                                y=[50],
                                                mode='markers',
                                                marker=dict(size=10, color=colors[idx % len(colors)]),
                                                name=category,
                                                hovertemplate=f'<b>{category}</b><br>' +
                                                            f'Count: {int(total)}<br>' +
                                                            f'Percentage: {width:.1f}%<br>' +
                                                            '<extra></extra>',
                                                showlegend=True
                                            ))
                                        
                                        cumulative_x += width
                                    
                                    # Add all traces
                                    for trace in legend_traces:
                                        fig_marimekko.add_trace(trace)
                                    
                                    # Update layout with shapes and annotations
                                    fig_marimekko.update_layout(
                                        title={
                                            'text': '📐 Complaints Distribution - Marimekko View',
                                            'x': 0.5,
                                            'xanchor': 'center',
                                            'font': {'size': 20, 'color': '#d62728'}
                                        },
                                        shapes=shapes,
                                        annotations=annotations,
                                        xaxis=dict(
                                            title='Proportion of Total Complaints (%)',
                                            showgrid=True,
                                            gridcolor='lightgray',
                                            range=[0, 100],
                                            zeroline=False
                                        ),
                                        yaxis=dict(
                                            title='Category Distribution (%)',
                                            showgrid=True,
                                            gridcolor='lightgray',
                                            range=[0, 100],
                                            zeroline=False
                                        ),
                                        height=600,
                                        margin=dict(l=60, r=200, t=80, b=60),
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(250,250,250,0.5)',
                                        showlegend=True,
                                        legend=dict(
                                            orientation="v",
                                            yanchor="top",
                                            y=1,
                                            xanchor="left",
                                            x=1.02,
                                            font=dict(size=9),
                                            bgcolor='rgba(255,255,255,0.8)'
                                        ),
                                        hovermode='closest'
                                    )
                                    
                                    st.plotly_chart(fig_marimekko, use_container_width=True)
                                    
                                    # Add explanation
                                    st.caption("💡 Width represents proportion of total complaints, height shows internal distribution within each category")
                                    
                                else:
                                    st.warning("No complaint data available for Marimekko chart")
                            else:
                                st.warning("No columns found in the data for Marimekko chart")



                            st.markdown("## 📈 Open Complaints Area Chart by Category")

                            # Prepare data for Area Chart visualization
                            if isinstance(df_pivot, dict):
                                df_area = pd.DataFrame(df_pivot)
                            else:
                                df_area = df_pivot.copy()

                            # Set COMPLAINT TYPE as index if it exists as a column
                            if 'COMPLAINT TYPE' in df_area.columns:
                                df_area = df_area.set_index('COMPLAINT TYPE')

                            # Remove Grand_Total column and Grand Total row for cleaner visualization
                            if 'Grand_Total' in df_area.columns:
                                df_area_viz = df_area.drop(columns=['Grand_Total'])
                            else:
                                df_area_viz = df_area.copy()

                            df_area_viz = df_area_viz[df_area_viz.index != 'Grand_Total'].copy() if 'Grand_Total' in df_area_viz.index else df_area_viz.copy()

                            # Get data for Area chart
                            if len(df_area_viz.columns) > 0 and len(df_area_viz) > 0:
                                # Transpose data so categories become columns
                                df_area_transposed = df_area_viz.T
                                
                                if len(df_area_transposed) > 0:
                                    # Create Area Chart with Plotly
                                    fig_area = go.Figure()
                                    
                                    colors = px.colors.qualitative.Pastel
                                    
                                    # Add area trace for each complaint category
                                    for idx, category in enumerate(df_area_transposed.columns):
                                        fig_area.add_trace(go.Scatter(
                                            x=df_area_transposed.index,
                                            y=df_area_transposed[category],
                                            mode='lines',
                                            name=str(category),
                                            fill='tonexty' if idx > 0 else 'tozeroy',
                                            line=dict(
                                                width=2,
                                                color=colors[idx % len(colors)]
                                            ),
                                            fillcolor=colors[idx % len(colors)],
                                            hovertemplate='<b>%{fullData.name}</b><br>' +
                                                        'Period: %{x}<br>' +
                                                        'Complaints: %{y}<br>' +
                                                        '<extra></extra>',
                                            stackgroup='one'
                                        ))
                                    
                                    # Update layout
                                    fig_area.update_layout(
                                        title={
                                            'text': '📊 Complaints Trend - Stacked Area View',
                                            'x': 0.5,
                                            'xanchor': 'center',
                                            'font': {'size': 20, 'color': '#9467bd'}
                                        },
                                        xaxis=dict(
                                            title='Time Period / Category',
                                            showgrid=True,
                                            gridcolor='lightgray',
                                            tickangle=-45
                                        ),
                                        yaxis=dict(
                                            title='Number of Complaints',
                                            showgrid=True,
                                            gridcolor='lightgray'
                                        ),
                                        height=600,
                                        margin=dict(l=60, r=20, t=80, b=100),
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(250,250,250,0.5)',
                                        showlegend=True,
                                        legend=dict(
                                            orientation="v",
                                            yanchor="top",
                                            y=1,
                                            xanchor="left",
                                            x=1.02,
                                            font=dict(size=11),
                                            bgcolor='rgba(255,255,255,0.8)',
                                            bordercolor='gray',
                                            borderwidth=1
                                        ),
                                        hovermode='x unified'
                                    )
                                    
                                    st.plotly_chart(fig_area, use_container_width=True)
                                    
                                    # Add summary statistics
                                    st.markdown("### 📊 Area Chart Insights")
                                    insight_cols = st.columns(3)
                                    with insight_cols[0]:
                                        total_periods = len(df_area_transposed)
                                        st.metric("Total Periods", str(total_periods))
                                    with insight_cols[1]:
                                        total_categories = len(df_area_transposed.columns)
                                        st.metric("Categories Tracked", str(total_categories))
                                    with insight_cols[2]:
                                        max_period = df_area_transposed.sum(axis=1).idxmax()
                                        max_value = int(df_area_transposed.sum(axis=1).max())
                                        st.metric("Peak Period", str(max_period), f"{max_value} complaints")
                                    
                                else:
                                    st.warning("No complaint data available for area chart")
                            else:
                                st.warning("No columns found in the data for area chart")                        



                            st.markdown("## 🔻 Open Complaints Funnel Chart")

                            # Prepare data for Funnel Chart visualization
                            if isinstance(df_pivot, dict):
                                df_funnel = pd.DataFrame(df_pivot)
                            else:
                                df_funnel = df_pivot.copy()

                            # Set COMPLAINT TYPE as index if it exists as a column
                            if 'COMPLAINT TYPE' in df_funnel.columns:
                                df_funnel = df_funnel.set_index('COMPLAINT TYPE')

                            # Remove Grand_Total column and Grand Total row for cleaner visualization
                            if 'Grand_Total' in df_funnel.columns:
                                df_funnel_viz = df_funnel.drop(columns=['Grand_Total'])
                            else:
                                df_funnel_viz = df_funnel.copy()

                            df_funnel_viz = df_funnel_viz[df_funnel_viz.index != 'Grand_Total'].copy() if 'Grand_Total' in df_funnel_viz.index else df_funnel_viz.copy()

                            # Get data for Funnel chart
                            if len(df_funnel_viz.columns) > 0 and len(df_funnel_viz) > 0:
                                # Calculate totals and sort in descending order
                                funnel_totals = df_funnel_viz.sum(axis=1)
                                funnel_totals = funnel_totals[funnel_totals > 0].sort_values(ascending=False)
                                
                                if len(funnel_totals) > 0:
                                    # Create Funnel Chart with Plotly
                                    fig_funnel = go.Figure()
                                    
                                    colors = px.colors.sequential.RdBu
                                    
                                    fig_funnel.add_trace(go.Funnel(
                                        name='Complaints',
                                        y=funnel_totals.index.astype(str),
                                        x=funnel_totals.values,
                                        textposition="inside",
                                        textinfo="value+percent initial",
                                        opacity=0.85,
                                        marker=dict(
                                            color=colors,
                                            line=dict(
                                                color='white',
                                                width=2
                                            )
                                        ),
                                        connector=dict(
                                            line=dict(
                                                color="royalblue",
                                                dash="dot",
                                                width=3
                                            )
                                        ),
                                        hovertemplate='<b>%{label}</b><br>' +
                                                    'Complaints: %{value}<br>' +
                                                    'Percentage: %{percentInitial}<br>' +
                                                    '<extra></extra>'
                                    ))
                                    
                                    # Update layout
                                    fig_funnel.update_layout(
                                        title={
                                            'text': '🎯 Complaints Volume Funnel',
                                            'x': 0.5,
                                            'xanchor': 'center',
                                            'font': {'size': 20, 'color': '#ff7f0e'}
                                        },
                                        funnelmode="stack",
                                        height=600,
                                        margin=dict(l=20, r=20, t=80, b=60),
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        showlegend=False,
                                        xaxis=dict(
                                            title='Number of Complaints',
                                            showgrid=True,
                                            gridcolor='lightgray'
                                        )
                                    )
                                    
                                    st.plotly_chart(fig_funnel, use_container_width=True)
                                    
                                    # Add funnel metrics
                                    st.markdown("### 📉 Funnel Analysis")
                                    funnel_cols = st.columns(4)
                                    with funnel_cols[0]:
                                        st.metric("Top Stage", str(funnel_totals.index[0]), 
                                                f"{int(funnel_totals.iloc[0])} complaints")
                                    with funnel_cols[1]:
                                        if len(funnel_totals) > 1:
                                            conversion_rate = (funnel_totals.iloc[-1] / funnel_totals.iloc[0]) * 100
                                            st.metric("Conversion Rate", f"{conversion_rate:.1f}%")
                                        else:
                                            st.metric("Conversion Rate", "N/A")
                                    with funnel_cols[2]:
                                        if len(funnel_totals) > 1:
                                            drop_off = funnel_totals.iloc[0] - funnel_totals.iloc[-1]
                                            st.metric("Total Drop-off", f"{int(drop_off)}")
                                        else:
                                            st.metric("Total Drop-off", "N/A")
                                    with funnel_cols[3]:
                                        st.metric("Funnel Stages", str(len(funnel_totals)))
                                    
                                    st.caption("💡 Funnel shows complaint categories sorted by volume from highest to lowest")
                                    
                                else:
                                    st.warning("No complaint data available for funnel chart")
                            else:
                                st.warning("No columns found in the data for funnel chart")



                            st.markdown("## 🔄 Open Complaints Sankey Diagram")

                            # Prepare data for Sankey Diagram visualization
                            if isinstance(df_pivot, dict):
                                df_sankey = pd.DataFrame(df_pivot)
                            else:
                                df_sankey = df_pivot.copy()

                            # Set COMPLAINT TYPE as index if it exists as a column
                            if 'COMPLAINT TYPE' in df_sankey.columns:
                                df_sankey = df_sankey.set_index('COMPLAINT TYPE')

                            # Remove Grand_Total column and Grand Total row for cleaner visualization
                            if 'Grand_Total' in df_sankey.columns:
                                df_sankey_viz = df_sankey.drop(columns=['Grand_Total'])
                            else:
                                df_sankey_viz = df_sankey.copy()

                            df_sankey_viz = df_sankey_viz[df_sankey_viz.index != 'Grand_Total'].copy() if 'Grand_Total' in df_sankey_viz.index else df_sankey_viz.copy()

                            # Get data for Sankey diagram
                            if len(df_sankey_viz.columns) > 0 and len(df_sankey_viz) > 0:
                                # Prepare data for Sankey
                                sources = []
                                targets = []
                                values = []
                                labels = []
                                
                                # Create label list (complaint types + subcategories)
                                complaint_types = df_sankey_viz.index.tolist()
                                subcategories = df_sankey_viz.columns.tolist()
                                labels = complaint_types + subcategories
                                
                                # Create source-target-value relationships
                                for i, complaint_type in enumerate(complaint_types):
                                    for j, subcategory in enumerate(subcategories):
                                        value = df_sankey_viz.loc[complaint_type, subcategory]
                                        if value > 0:  # Only include non-zero flows
                                            sources.append(i)  # Index of complaint type
                                            targets.append(len(complaint_types) + j)  # Index of subcategory
                                            values.append(value)
                                
                                if len(sources) > 0:
                                    # Create color palette
                                    colors_palette = px.colors.qualitative.Set2
                                    node_colors = [colors_palette[i % len(colors_palette)] for i in range(len(labels))]
                                    
                                    # Create link colors with transparency
                                    link_colors = []
                                    for source_idx in sources:
                                        base_color = colors_palette[source_idx % len(colors_palette)]
                                        # Convert to rgba with transparency
                                        if base_color.startswith('#'):
                                            r = int(base_color[1:3], 16)
                                            g = int(base_color[3:5], 16)
                                            b = int(base_color[5:7], 16)
                                            link_colors.append(f'rgba({r},{g},{b},0.4)')
                                        else:
                                            link_colors.append(base_color)
                                    
                                    # Create Sankey Diagram
                                    fig_sankey = go.Figure(data=[go.Sankey(
                                        node=dict(
                                            pad=15,
                                            thickness=20,
                                            line=dict(color='white', width=2),
                                            label=labels,
                                            color=node_colors,
                                            hovertemplate='<b>%{label}</b><br>Total: %{value}<extra></extra>'
                                        ),
                                        link=dict(
                                            source=sources,
                                            target=targets,
                                            value=values,
                                            color=link_colors,
                                            hovertemplate='<b>%{source.label}</b> → <b>%{target.label}</b><br>' +
                                                        'Flow: %{value}<br>' +
                                                        '<extra></extra>'
                                        )
                                    )])
                                    
                                    # Update layout
                                    fig_sankey.update_layout(
                                        title={
                                            'text': '🌊 Complaints Flow - Sankey Diagram',
                                            'x': 0.5,
                                            'xanchor': 'center',
                                            'font': {'size': 20, 'color': '#17becf'}
                                        },
                                        height=600,
                                        margin=dict(l=20, r=20, t=80, b=60),
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        font=dict(size=11, color='#333333')
                                    )
                                    
                                    st.plotly_chart(fig_sankey, use_container_width=True)
                                    
                                    # Add Sankey metrics
                                    st.markdown("### 🔀 Flow Analysis")
                                    sankey_cols = st.columns(4)
                                    with sankey_cols[0]:
                                        total_flow = sum(values)
                                        st.metric("Total Flow", f"{int(total_flow):,}")
                                    with sankey_cols[1]:
                                        st.metric("Source Nodes", str(len(complaint_types)))
                                    with sankey_cols[2]:
                                        st.metric("Target Nodes", str(len(subcategories)))
                                    with sankey_cols[3]:
                                        st.metric("Active Connections", str(len(sources)))
                                    
                                    st.caption("💡 Sankey diagram shows the flow of complaints from categories (left) to subcategories (right)")
                                    
                                else:
                                    st.warning("No complaint flow data available for Sankey diagram")
                            else:
                                st.warning("No columns found in the data for Sankey diagram")





                            st.markdown("## 🔥 Open Complaints Heatmap")

                            # Prepare data for Heatmap visualization
                            if isinstance(df_pivot, dict):
                                df_heatmap = pd.DataFrame(df_pivot)
                            else:
                                df_heatmap = df_pivot.copy()

                            # Set COMPLAINT TYPE as index if it exists as a column
                            if 'COMPLAINT TYPE' in df_heatmap.columns:
                                df_heatmap = df_heatmap.set_index('COMPLAINT TYPE')

                            # Remove Grand_Total column and Grand Total row for cleaner visualization
                            if 'Grand_Total' in df_heatmap.columns:
                                df_heatmap_viz = df_heatmap.drop(columns=['Grand_Total'])
                            else:
                                df_heatmap_viz = df_heatmap.copy()

                            df_heatmap_viz = df_heatmap_viz[df_heatmap_viz.index != 'Grand_Total'].copy() if 'Grand_Total' in df_heatmap_viz.index else df_heatmap_viz.copy()

                            # Get data for Heatmap
                            if len(df_heatmap_viz.columns) > 0 and len(df_heatmap_viz) > 0:
                                # Create Heatmap with Plotly
                                fig_heatmap = go.Figure(data=go.Heatmap(
                                    z=df_heatmap_viz.values,
                                    x=df_heatmap_viz.columns.astype(str),
                                    y=df_heatmap_viz.index.astype(str),
                                    colorscale='YlOrRd',  # Yellow-Orange-Red color scale
                                    text=df_heatmap_viz.values,
                                    texttemplate='%{text}',
                                    textfont=dict(size=10, color='white'),
                                    hoverongaps=False,
                                    hovertemplate='<b>Category:</b> %{y}<br>' +
                                                '<b>Subcategory:</b> %{x}<br>' +
                                                '<b>Complaints:</b> %{z}<br>' +
                                                '<extra></extra>',
                                    colorbar=dict(
                                        title='Complaints',
                                        titleside='right',
                                        tickmode='linear',
                                        tick0=0,
                                        dtick=df_heatmap_viz.values.max() / 10 if df_heatmap_viz.values.max() > 0 else 1,
                                        thickness=15,
                                        len=0.7
                                    )
                                ))
                                
                                # Update layout
                                fig_heatmap.update_layout(
                                    title={
                                        'text': '🌡️ Complaints Intensity Heatmap',
                                        'x': 0.5,
                                        'xanchor': 'center',
                                        'font': {'size': 20, 'color': '#e74c3c'}
                                    },
                                    xaxis=dict(
                                        title='Subcategories',
                                        side='bottom',
                                        tickangle=-45,
                                        showgrid=False
                                    ),
                                    yaxis=dict(
                                        title='Complaint Types',
                                        showgrid=False,
                                        autorange='reversed'  # Top to bottom ordering
                                    ),
                                    height=600,
                                    margin=dict(l=150, r=100, t=80, b=120),
                                    paper_bgcolor='rgba(0,0,0,0)',
                                    plot_bgcolor='rgba(255,255,255,1)'
                                )
                                
                                st.plotly_chart(fig_heatmap, use_container_width=True)
                                
                                # Add Heatmap statistics
                                st.markdown("### 🔥 Heatmap Insights")
                                heatmap_cols = st.columns(4)
                                with heatmap_cols[0]:
                                    max_value = int(df_heatmap_viz.values.max())
                                    st.metric("Highest Intensity", f"{max_value:,}")
                                with heatmap_cols[1]:
                                    min_value = int(df_heatmap_viz.values.min())
                                    st.metric("Lowest Intensity", f"{min_value:,}")
                                with heatmap_cols[2]:
                                    avg_value = int(df_heatmap_viz.values.mean())
                                    st.metric("Average Complaints", f"{avg_value:,}")
                                with heatmap_cols[3]:
                                    # Find hotspot (cell with max value)
                                    max_idx = df_heatmap_viz.values.argmax()
                                    max_row = max_idx // len(df_heatmap_viz.columns)
                                    max_col = max_idx % len(df_heatmap_viz.columns)
                                    hotspot = f"{df_heatmap_viz.index[max_row]}"
                                    st.metric("Hotspot Category", hotspot[:20] + "..." if len(hotspot) > 20 else hotspot)
                                
                                st.caption("💡 Darker colors indicate higher complaint volumes. Hover over cells for detailed information.")
                                
                            else:
                                st.warning("No complaint data available for heatmap")



                            st.markdown("## 📊 Open Complaints Count Bar Chart")

                            # Prepare data for Count Bar Chart visualization
                            if isinstance(df_pivot, dict):
                                df_bar = pd.DataFrame(df_pivot)
                            else:
                                df_bar = df_pivot.copy()

                            # Set COMPLAINT TYPE as index if it exists as a column
                            if 'COMPLAINT TYPE' in df_bar.columns:
                                df_bar = df_bar.set_index('COMPLAINT TYPE')

                            # Remove Grand_Total column and Grand Total row for cleaner visualization
                            if 'Grand_Total' in df_bar.columns:
                                df_bar_viz = df_bar.drop(columns=['Grand_Total'])
                            else:
                                df_bar_viz = df_bar.copy()

                            df_bar_viz = df_bar_viz[df_bar_viz.index != 'Grand_Total'].copy() if 'Grand_Total' in df_bar_viz.index else df_bar_viz.copy()

                            # Get data for Count Bar Chart
                            if len(df_bar_viz.columns) > 0 and len(df_bar_viz) > 0:
                                # Calculate totals per category
                                bar_totals = df_bar_viz.sum(axis=1)
                                bar_totals = bar_totals[bar_totals > 0].sort_values(ascending=True)  # Sort ascending for horizontal bars
                                
                                if len(bar_totals) > 0:
                                    # Create color gradient based on values
                                    colors_gradient = px.colors.sequential.Viridis
                                    normalized_values = (bar_totals - bar_totals.min()) / (bar_totals.max() - bar_totals.min()) if bar_totals.max() > bar_totals.min() else [0.5] * len(bar_totals)
                                    bar_colors = [colors_gradient[int(val * (len(colors_gradient) - 1))] for val in normalized_values]
                                    
                                    # Create horizontal bar chart
                                    fig_bar = go.Figure()
                                    
                                    fig_bar.add_trace(go.Bar(
                                        x=bar_totals.values,
                                        y=bar_totals.index.astype(str),
                                        orientation='h',
                                        marker=dict(
                                            color=bar_colors,
                                            line=dict(color='white', width=1.5),
                                            opacity=0.9
                                        ),
                                        text=bar_totals.values,
                                        texttemplate='%{text:,}',
                                        textposition='outside',
                                        textfont=dict(size=11, color='#333333'),
                                        hovertemplate='<b>%{y}</b><br>' +
                                                    'Total Complaints: %{x:,}<br>' +
                                                    '<extra></extra>'
                                    ))
                                    
                                    # Update layout
                                    fig_bar.update_layout(
                                        title={
                                            'text': '📊 Complaint Count by Category',
                                            'x': 0.5,
                                            'xanchor': 'center',
                                            'font': {'size': 20, 'color': '#3498db'}
                                        },
                                        xaxis=dict(
                                            title='Number of Complaints',
                                            showgrid=True,
                                            gridcolor='lightgray',
                                            zeroline=True,
                                            zerolinecolor='gray',
                                            zerolinewidth=2
                                        ),
                                        yaxis=dict(
                                            title='Complaint Categories',
                                            showgrid=False,
                                            tickfont=dict(size=10)
                                        ),
                                        height=600,
                                        margin=dict(l=200, r=80, t=80, b=60),
                                        paper_bgcolor='rgba(0,0,0,0)',
                                        plot_bgcolor='rgba(250,250,250,0.5)',
                                        showlegend=False
                                    )
                                    
                                    st.plotly_chart(fig_bar, use_container_width=True)
                                    
                                    # Add bar chart statistics
                                    st.markdown("### 📊 Bar Chart Statistics")
                                    bar_cols = st.columns(4)
                                    with bar_cols[0]:
                                        total_complaints = int(bar_totals.sum())
                                        st.metric("Total Complaints", f"{total_complaints:,}")
                                    with bar_cols[1]:
                                        top_category = str(bar_totals.iloc[-1] if len(bar_totals) > 0 else "N/A")
                                        top_count = int(bar_totals.iloc[-1]) if len(bar_totals) > 0 else 0
                                        st.metric("Top Category", top_category[:15] + "..." if len(top_category) > 15 else top_category, 
                                                f"{top_count:,}")
                                    with bar_cols[2]:
                                        if len(bar_totals) > 0:
                                            median_value = int(bar_totals.median())
                                            st.metric("Median Count", f"{median_value:,}")
                                        else:
                                            st.metric("Median Count", "N/A")
                                    with bar_cols[3]:
                                        st.metric("Categories", str(len(bar_totals)))
                                    
                                    st.caption("💡 Horizontal bars show complaint counts sorted from lowest to highest")
                                    
                                else:
                                    st.warning("No complaint data available for count bar chart")
                            else:
                                st.warning("No columns found in the data for count bar chart")




                            
                            st.markdown("### 📈 Quick Stats")

                            # Create 5 columns instead of 3
                            metric_cols = st.columns(5)

                            with metric_cols[0]:
                                st.metric("Total Complaints", f"{int(totals.sum()):,}")

                            with metric_cols[1]:
                                st.metric("Categories", str(len(totals)))

                            with metric_cols[2]:
                                max_category = str(totals.idxmax())
                                max_value = int(totals.max())
                                st.metric("Top Category", max_category, f"{max_value} cases")

                            with metric_cols[3]:
                                min_category = str(totals.idxmin())
                                min_value = int(totals.min())
                                st.metric("Lowest Category", min_category, f"{min_value} cases")

                            with metric_cols[4]:
                                # Calculate the median value
                                median_value = totals.median()
                                # Find the category whose value is closest to the median
                                median_category = (totals - median_value).abs().idxmin()
                                median_display_value = int(totals[median_category])
                                st.metric("Median Category", median_category, f"{median_display_value} cases")


                        else:
                            st.warning("No complaint data available to visualize")
                    else:
                        st.warning("No columns found in the data")
                    
                    logger.info("Tab 1: Complaint overview displayed successfully")
                    
                else:
                    if status_code:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                        st.info("The API service may be experiencing issues. Please try again in a few moments.")
                        logger.error(f"Tab 1: API request failed with status code {status_code}")
                    else:
                        st.error(f"❌ Error: {error}")
                        st.info("The API service may be temporarily unavailable. Please try again in a few moments.")
                        logger.error(f"Tab 1: Error - {error}")
            else:
                st.info("👆 Click the button above to load the open complaints data")
                st.caption(f"Ready to load at: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            st.divider()











            # ========================================
            # SECTION 2: OPEN/CLOSE COMPLAINTS PIVOT
            # ========================================
            st.subheader("📊 Open/Close Complaints Reports")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load Open/Close Complaints Data", key="load_open_close_complaints_btn", type="primary"):
                with st.spinner("Loading data..."):
                    df_pivot_02, error_02, status_code_02 = fetch_open_close_complaint_pivot()

                if error_02 is None and df_pivot_02 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_02)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Open Close Complaints Pivot Table displayed successfully")
                    
                    st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code_02:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_02}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_02}")
                    else:
                        st.error(f"❌ Error: {error_02}")
                        logger.error(f"Tab 1: Error - {error_02}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the open/close complaints data")
            
            st.divider()
            
            # ========================================
            # SECTION 3: AGGING OPEN COMPLAINTS PIVOT
            # ========================================
            st.header("📊 Agging Open Complaints Reports")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load Agging Open Complaints Data", key="load_agging_open_complaints_btn",type="primary"):
                with st.spinner("Loading data..."):
                    df_pivot_03, error_03, status_code_03 = fetch_agging_open_pivot()

                if error_03 is None and df_pivot_03 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_03)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Agging Open Complaints Pivot Table displayed successfully")
                    
                    st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code_03:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_03}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_03}")
                    else:
                        st.error(f"❌ Error: {error_03}")
                        logger.error(f"Tab 1: Error - {error_03}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the agging open complaints data")
            
            st.divider()
            
            # ========================================
            # SECTION 4: AGGING OPEN/CLOSE COMPLAINTS PIVOT
            # ========================================
            st.header("📊 Agging Day Difference All Complaints Reports")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load Agging Day Difference Data", key="load_agging_day_diff_complaints_btn",type="primary"):
                with st.spinner("Loading data..."):
                    df_pivot_04, error_04, status_code_04 = fetch_agging_open_close_pivot()

                if error_04 is None and df_pivot_04 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_04)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Agging Open/Close Complaints Pivot Table displayed successfully")
                    
                    st.caption(f"Last cached: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code_04:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_04}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_04}")
                    else:
                        st.error(f"❌ Error: {error_04}")
                        logger.error(f"Tab 1: Error - {error_04}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the agging day difference data")
            
            st.divider()

            # ========================================
            # SECTION 5: OPEN/CLOSE COMPLAINT REPORT
            # ========================================
            st.header("📊 All Complaint Report")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load All Complaint Report Data", key="load_all_complaint_report_btn",type="primary"):
                with st.spinner("Loading data..."):
                    df_pivot_05, error_05, status_code_05 = fetch_open_close_complaint_report()

                if error_05 is None and df_pivot_05 is not None:
                    styled_df = style_grand_total_dataframe(df_pivot_05)
                    st.dataframe(styled_df, use_container_width=True, height=400)
                    logger.info("Tab 1: Open Close Complaint Report displayed successfully")

                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                else:
                    if status_code_05:
                        st.error(f"❌ Failed to fetch data. Status code: {status_code_05}")
                        logger.error(f"Tab 1: API request failed with status code {status_code_05}")
                    else:
                        st.error(f"❌ Error: {error_05}")
                        logger.error(f"Tab 1: Error - {error_05}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the all complaint report data")
            
            st.divider()

            # ========================================
            # SECTION 6: ALL AGGING COMPLAINT REPORT
            # ======================================== 
            st.header("📊 All Department Complaint Type Report")
            st.caption("View complaints categorized by type, department, and status (Open/Closed)")

            # Add button to fetch data
            if st.button("📥 Load All Department Complaint Type Data", key="load_all_dept_complaint_btn",type="primary"):
                # Validate dataset path exists
                if not dataset_path:
                    st.error("❌ Dataset path is not provided.")
                    st.info("ℹ️ Please configure the dataset path in the settings.")

                elif not os.path.exists(dataset_path):
                    st.error(f"❌ Dataset not found at: `{dataset_path}`")
                    st.info("ℹ️ Please verify the file path and try again.")

                else:
                    # Show loading spinner while processing
                    with st.spinner("📊 Loading data..."):
                        @st.cache_data
                        def load_complaint_data(path):
                            return generate_all_agging_complaint_report(path)
                        
                        complaint_data = load_complaint_data(dataset_path)

                    # Check if data is None or empty (handle both list and DataFrame)
                    if complaint_data is None:
                        st.warning("⚠️ No data available to display.")
                        st.info("ℹ️ The dataset may be empty or contain no valid records.")
                    else:
                        complaint_df = complaint_data

                        # Display dataframe
                        st.dataframe(
                            complaint_df,
                            use_container_width=True,
                            height=400
                        )

                        logger.info("Tab 1: All Agging Complaint Report displayed successfully")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                st.info("👆 Click the button above to load the all department complaint type data")
            st.divider()

            # ========================================
            # SECTION 7: POWER OUTAGE DURATION
            # ======================================== 

            st.header("X-Dashboard Shift wise Power Outage Duration Hour Analysis")

            # Initialize session state for selected date if it doesn't exist
            if "selected_outage_date" not in st.session_state:
                st.session_state.selected_outage_date = datetime.today()

            # Initialize a flag to track if analysis should run
            if "run_analysis" not in st.session_state:
                st.session_state.run_analysis = False

            # Date picker with a unique key to prevent auto-triggering
            selected_date = st.date_input(
                "Select Date",
                value=st.session_state.selected_outage_date,
                key="date_picker_outage",  # Add unique key
                help="Choose a date to analyze power outage durations"
            )

            # Add a button to trigger the analysis
            if st.button("🔍 Restoration Duration Hour Analysis Reports", key="analyze_button",type="primary"):
                # Update session state only when button is clicked
                st.session_state.selected_outage_date = selected_date
                st.session_state.run_analysis = True

            # Only process if the button was clicked
            if st.session_state.run_analysis:
                if dataset_path is not None:
                    try:
                        # Show loading spinner
                        with st.spinner("Processing data..."):
                            pivot_df = fetch_close_power_outage_duration(
                                dataset_path,
                                st.session_state.selected_outage_date  # Use stored date from session state
                            )

                            # Display the pivot table
                            st.subheader("Restoration Duration Analysis Reports")
                            st.dataframe(
                                pivot_df,
                                use_container_width=True,
                                height=400,
                                hide_index=False
                            )

                        st.success("✅ Data processing successfully!")
                        
                        # Reset the flag after successful processing
                        st.session_state.run_analysis = False

                    except ValueError as ve:
                        # Handle time format errors specifically
                        if "time data" in str(ve).lower() or "format" in str(ve).lower():
                            st.error("❌ Error: Time format is incorrect in the dataset. Please check the date/time columns format.")
                            st.info("💡 Expected format: YYYY-MM-DD HH:MM:SS or similar standard datetime format")
                        else:
                            st.error(f"❌ Data error: {str(ve)}")
                        st.session_state.run_analysis = False

                    except pd.errors.ParserError as pe:
                        st.error("❌ Error: Unable to parse the data file. Please check if the file format is correct.")
                        st.info(f"Details: {str(pe)}")
                        st.session_state.run_analysis = False

                    except FileNotFoundError:
                        st.error("❌ Error: Dataset file not found. Please check the file path.")
                        st.session_state.run_analysis = False

                    except KeyError as ke:
                        st.error(f"❌ Error: Required column not found in dataset: {str(ke)}")
                        st.info("Please ensure all necessary columns exist in your dataset.")
                        st.session_state.run_analysis = False

                    except Exception as e:
                        st.error(f"❌ Error processing file: {str(e)}")
                        st.info("💡 If this is a time format issue, please verify your datetime columns are in standard format (YYYY-MM-DD HH:MM:SS)")
                        st.session_state.run_analysis = False

                else:
                    st.warning("⚠️ Dataset path is not configured. Please check your configuration.")
                    st.session_state.run_analysis = False

            # Show last loaded timestamp only if analysis was run
            if "last_analysis_time" not in st.session_state:
                st.session_state.last_analysis_time = None

            if st.session_state.last_analysis_time:
                st.caption(f"Last loaded: {st.session_state.last_analysis_time}")
                
            else:
                st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
                st.info("👆 Click the button above to load the X-Dashboard Shift wise Power Outage Duration Hour Analysis")


            # ========================================
            # ALL SECTIONS IN 5-COLUMN LAYOUT
            # ========================================

            st.divider()

            st.header("Loding All Complaint Reports View")

            # Create 5 columns
            col1, col2, col3, col4, col5 = st.columns(5)

            # ========================================
            # COLUMN 1: All Agging Complaint Report
            # ========================================
            with col1:
                st.subheader("📊Report 01")
                # Add a button to trigger data loading
                if st.button("📥 Load Open Complaints Data OverView", type="primary"):
                    with st.spinner("Loading data..."):
                        df_pivot, error, status_code = fetch_open_complaint_pivot()

                    if error is None and df_pivot is not None:
                        st.subheader("📊 Open Complaints Reports")
                        st.caption("Grand Total row is highlighted in red for easy identification")
                        
                        styled_df = style_grand_total_dataframe(df_pivot)
                        st.dataframe(styled_df, use_container_width=True, height=400)
                        logger.info("Tab 1: Complaint overview displayed successfully")
                        
                    else:
                        if status_code:
                            st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                            st.info("The API service may be experiencing issues. Please try again in a few moments.")
                            logger.error(f"Tab 1: API request failed with status code {status_code}")
                        else:
                            st.error(f"❌ Error: {error}")
                            st.info("The API service may be temporarily unavailable. Please try again in a few moments.")
                            logger.error(f"Tab 1: Error - {error}")
                else:
                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    
            # ========================================
            # COLUMN 2: Data All View
            # ========================================
            with col2:
                st.subheader("📊Report 02")

                if st.button("🔄 Load Data All Open Close Complaint Report", key="load_data_all_view", type="primary"):
                    with st.spinner("Loading data..."):
                        df_07, error_07, status_code_07 = fetch_open_close_complaint_pivot()

                    if error_07 is None and df_07 is not None:                    
                        st.dataframe(df_07, use_container_width=True, height=400)
                        logger.info("Tab 1: Data All View displayed successfully")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        if status_code_07:
                            st.error(f"❌ Failed to fetch data. Status code: {status_code_07}")
                            logger.error(f"Tab 1: API request failed with status code {status_code_07}")
                        else:
                            st.error(f"❌ Error: {error_07}")
                            logger.error(f"Tab 1: Error - {error_07}")
                else:
                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # ========================================
            # COLUMN 3: Generate All Agging Complaints Report
            # ========================================
            with col3:
                st.subheader("📊Report 03")

                # Validate dataset path exists
                if not dataset_path:
                    st.error("❌ Dataset path is not provided.")
                    st.info("ℹ️ Please configure the dataset path in the settings.")

                elif not os.path.exists(dataset_path):
                    st.error(f"❌ Dataset not found at: `{dataset_path}`")
                    st.info("ℹ️ Please verify the file path and try again.")

                else:
                    # Add button to trigger data loading
                    if st.button("📊 All Department Complaint Type Report View", type="primary"):
                        # Show loading spinner while processing
                        with st.spinner("📊 Loading data..."):
                            @st.cache_data
                            def load_complaint_data(path):
                                return generate_all_agging_complaint_report(path)
                            
                            complaint_data = load_complaint_data(dataset_path)

                        # Check if data is None or empty (handle both list and DataFrame)
                        if complaint_data is None:
                            st.warning("⚠️ No data available to display.")
                            st.info("ℹ️ The dataset may be empty or contain no valid records.")
                        else:
                            complaint_df = complaint_data

                            # Display dataframe
                            st.dataframe(
                                complaint_df,
                                use_container_width=True,
                                height=400
                            )

                            logger.info("Tab 1: All Agging Complaint Report displayed successfully")

                    else:
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    
                            
            # ========================================
            # COLUMN 4: Agging Open Report
            # ========================================
            with col4:
                st.subheader("📊Report 04")

                if st.button("🔄 Load Generate Agging Open View Report", key="generate_agging_open_report", type="primary"):
                    with st.spinner("Generating report..."):
                        df_10, error_10, status_code_10 = fetch_agging_open_pivot()

                    if error_10 is None and df_10 is not None:                    
                        st.dataframe(df_10, use_container_width=True, height=400)
                        logger.info("Tab 1: Agging Open Report displayed successfully")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        if status_code_10:
                            st.error(f"❌ Failed to fetch data. Status code: {status_code_10}")
                            logger.error(f"Tab 1: API request failed with status code {status_code_10}")
                        else:
                            st.error(f"❌ Error: {error_10}")
                            logger.error(f"Tab 1: Error - {error_10}")
                else:
                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

            # ========================================
            # COLUMN 5: Open Complaints Reports
            # ========================================
            with col5:
                st.subheader("📊Report 05")
                
                if st.button("🔄 Load Generate Open Complaints Report", key="load_open_complaints", type="primary"):
                    with st.spinner("Loading data..."):
                        df_pivot, error, status_code = fetch_open_complaint_pivot()

                    if error is None and df_pivot is not None:
                        styled_df = style_grand_total_dataframe(df_pivot)
                        st.dataframe(styled_df, use_container_width=True, height=400)
                        logger.info("Tab 1: Complaint overview displayed successfully")
                        st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        if status_code:
                            st.error(f"❌ Failed to fetch data. Status code: {status_code}")
                            st.info("The API service may be experiencing issues. Please try again in a few moments.")
                            logger.error(f"Tab 1: API request failed with status code {status_code}")
                        else:
                            st.error(f"❌ Error: {error}")
                            st.info("The API service may be temporarily unavailable. Please try again in a few moments.")
                            logger.error(f"Tab 1: Error - {error}")
                else:
                    st.caption(f"Last loaded: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Divider
        st.divider()

        if st.button("🔄 Data Refresh All", key="refresh_all_btn", type="primary", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
            
        logger.info("Streamlit dashboard Tab 1 loaded successfully")
        
    except Exception as e:
        error_msg = str(CustomException(e, sys))
        logger.error(f"Unhandled error in Streamlit dashboard Tab1 | error={error_msg}")
        st.error("❌ An unexpected error occurred while loading the dashboard.")
        with st.expander("Show error details"):
            st.code(error_msg)
            
    