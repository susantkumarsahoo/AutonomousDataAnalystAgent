import pandas as pd
import plotly.express as px
import numpy as np
import streamlit as st
import datetime


def time_series_complaints_status_stacked(data):
    """
    Reads complaint data from Excel or DataFrame and returns a DataFrame in pivot format.
    Shows Closed vs Open complaints per month, grouped by year.
    Returns a format similar to the provided table with months as columns.
    Filters out appreciation tweets from the data.
    
    Parameters:
    -----------
    data : str or pd.DataFrame
        Either a file path to Excel file or a pandas DataFrame
    """
    # Handle both DataFrame and file path
    if isinstance(data, str):
        df = pd.read_excel(data)
    elif isinstance(data, pd.DataFrame):
        df = data.copy()
    else:
        raise ValueError("Input must be either a file path (str) or pandas DataFrame")
    
    # Filter out appreciation tweets
    # Create a boolean mask to identify appreciation tweets
    df['Appreciation Tweet'] = (
        df['REMARKS']
        .astype(str)
        .str.findall(r'(?i)\bappreciation\s*tweet\b')
        .apply(lambda x: 'Appreciation Tweet' if len(x) > 0 else 'NA')
    )
    
    # Keep only rows where it's NOT an appreciation tweet
    df = df[df['Appreciation Tweet'] == 'NA']
    
    # Load and preprocess
    df['DATE'] = pd.to_datetime(df['DATE'])
    df['YEAR'] = df['DATE'].dt.year
    df['MONTH'] = df['DATE'].dt.month
    df['MONTH_NAME'] = df['DATE'].dt.strftime('%B')
    
    # Group by YEAR, MONTH, MONTH_NAME
    summary = (
        df.groupby(['YEAR', 'MONTH', 'MONTH_NAME'])
          .size()
          .reset_index(name='COUNT')
    )
    
    # Sort by YEAR and MONTH
    summary = summary.sort_values(['YEAR', 'MONTH']).reset_index(drop=True)
    
    # Pivot to create the wide format with months as columns
    pivot_df = summary.pivot_table(
        index='YEAR',
        columns='MONTH_NAME',
        values='COUNT',
        fill_value=0
    )
    
    # Define correct month order
    month_order = ['April', 'May', 'June', 'July', 'August', 'September', 
                   'October', 'November', 'December', 'January', 'February', 'March']
    
    # Reorder columns to match fiscal year (April to March)
    available_months = [m for m in month_order if m in pivot_df.columns]
    pivot_df = pivot_df[available_months].round(0).astype(int)
    
    # Add Total column
    pivot_df['Total'] = pivot_df[available_months].sum(axis=1)
    
    # Reset index to make YEAR a column
    pivot_df = pivot_df.reset_index()
    
    return pivot_df


def get_qrc_value_counts(df):
    """
    Get value counts for QUERY/REQUEST/COMPLAINT column
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing complaint data
    """
    count_df = df['QUERY/REQUEST/COMPLAINT'].value_counts()
    count_df = pd.DataFrame(count_df).reset_index()
    count_df.columns = ['QUERY/REQUEST/COMPLAINT', 'count']
    return count_df


def get_complaint_type_value_counts_type(df):
    """
    Get top 5 complaint types by count
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame containing complaint data
    """
    df = df.copy()
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()
    count_df = df['COMPLAINT TYPE'].value_counts().head(5)
    count_df = pd.DataFrame(count_df).reset_index()
    count_df.columns = ['COMPLAINT TYPE', 'count']
    return count_df


def agging_all_open_pivot_table(data):
    """
    Reads an Excel file or DataFrame, creates a pivot table of complaint type vs age bucket,
    adds grand totals (row + column), and returns the result as a DataFrame.
    
    Parameters:
    -----------
    data : str or pd.DataFrame
        Either a file path to Excel file or a pandas DataFrame
    
    Returns:
    --------
    pd.DataFrame
        DataFrame representation of the pivot table with totals.
    """
    # Handle both DataFrame and file path
    if isinstance(data, str):
        old_df = pd.read_excel(data)
    elif isinstance(data, pd.DataFrame):
        old_df = data.copy()
    else:
        raise ValueError("Input must be either a file path (str) or pandas DataFrame")
    
    # Filter for open complaints
    df = old_df[old_df['CLOSED/OPEN'].str.lower().str.strip() == 'open']
    
    # Ensure DATE column is datetime
    df['DATE'] = pd.to_datetime(df['DATE'])

    # Clean data before pivoting
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()

    # Calculate age in days
    today = pd.Timestamp.today()
    df['Age_Days'] = (today - df['DATE']).dt.days

    # Define age buckets
    bins = [0, 15, 30, 60, 90, 180, float('inf')]
    labels = ['<15Days', '16-30Days', '31-60Days', '61-90Days', '91-180Days', '>180Days']
    df['Age_Bucket'] = pd.cut(df['Age_Days'], bins=bins, labels=labels, right=True, include_lowest=True)    
    
    # Pivot table with complaint type + age bucket
    pivot_data = pd.pivot_table(
        df,
        values='CLOSED/OPEN',           # column to count
        index='COMPLAINT TYPE',          # rows
        columns='Age_Bucket',            # columns
        aggfunc='count',
        fill_value=0
    )
    
    # Reorder columns to match the age bucket order
    pivot_data = pivot_data[labels]
    
    # Add Grand Total column (row-wise sum)
    pivot_data['Grand_Total'] = pivot_data.sum(axis=1)
    
    # Add Grand Total row (column-wise sum)
    pivot_data.loc['Grand_Total'] = pivot_data.sum(axis=0)
    
    # Ensure integers
    pivot_data = pivot_data.astype(int)
    
    # Reset index to make 'COMPLAINT TYPE' a regular column
    pivot_data = pivot_data.reset_index()
    
    return pivot_data

# streamlit_analysis_tab4_helper.py
