import pandas as pd
import numpy as np
import os 
import sys



def open_complaint_pivot(dataset_path: str) -> pd.DataFrame:
    """
    Generate a pivot table of open complaints by department and complaint type,
    including grand totals for rows and columns.

    Parameters
    ----------
    dataset_path : str
        Path to the Excel file containing complaint data.

    Returns
    -------
    pd.DataFrame
        Pivot table with counts of open complaints, plus grand totals.
    """
    # Load dataset
    df = pd.read_excel(dataset_path)

    # Filter only open complaints (handle case-insensitive and NaN values)
    df_open = df[df['CLOSED/OPEN'].str.lower().str.strip() == 'open']
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()
    
    # Create pivot table
    pivot = pd.pivot_table(
        df_open,
        values='CLOSED/OPEN',
        index='COMPLAINT TYPE',
        columns='DEPT',
        aggfunc='count',
        fill_value=0
    )

    # Add Grand Total column (row-wise sum)
    pivot['Grand_Total'] = pivot.sum(axis=1)

    # Add Grand Total row (column-wise sum)
    pivot.loc['Grand_Total'] = pivot.sum(axis=0)

    # **FIX: Convert all numpy types to native Python types**
    pivot = pivot.astype(int)  # Convert to Python int
    
    # Reset index to make 'COMPLAINT TYPE' a regular column
    pivot = pivot.reset_index()

    return pivot


import pandas as pd

def open_close_complaint_pivot(dataset_path: str) -> pd.DataFrame:
    """
    Reads an Excel dataset and returns a pivot table of complaints
    grouped by COMPLAINT TYPE, Department, and Open/Closed status,
    with grand totals added.
    
    Parameters
    ----------
    dataset_path : str
        Path to the Excel file containing complaint data.
    
    Returns
    -------
    pd.DataFrame
        Pivot table with flattened columns and grand totals.
    """
    # Load dataset
    df = pd.read_excel(dataset_path)
    
    # **FIX: Clean data before pivoting**
    # Remove any whitespace and handle case sensitivity
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()
    df['DEPT'] = df['DEPT'].astype(str).str.strip().str.title()
    df['CLOSED/OPEN'] = df['CLOSED/OPEN'].astype(str).str.strip().str.title()  # Capitalize properly

    # Build pivot table
    pivot_data = pd.pivot_table(
        df,
        index='COMPLAINT TYPE',
        columns=['DEPT', 'CLOSED/OPEN'],
        aggfunc='size',
        fill_value=0
    )

    # **FIX: Flatten multi-level columns before adding totals**
    # This creates column names like "DEPT_STATUS" instead of tuples
    pivot_data.columns = ['_'.join(map(str, col)).strip('_') for col in pivot_data.columns]

    # Add Grand Total column (row-wise sum)
    pivot_data['Grand_Total'] = pivot_data.sum(axis=1)

    # Add Grand Total row (column-wise sum)
    pivot_data.loc['Grand_Total'] = pivot_data.sum(numeric_only=True, axis=0)

    # Ensure integer values (convert from float to int)
    pivot_data = pivot_data.astype(int)

    # Reset index to make 'COMPLAINT TYPE' a regular column
    pivot_data = pivot_data.reset_index()
    dict_pivot_data= pivot_data.to_dict()

    return dict_pivot_data


def agging_open_pivot_dict(dataset_path: str) -> dict:
    """
    Reads an Excel file, creates a pivot table of complaint type vs age bucket,
    adds grand totals (row + column), and returns the result as a dictionary.
    
    Parameters
    ----------
    dataset_path : str
        Path to the Excel dataset.
    
    Returns
    -------
    dict
        Dictionary representation of the pivot table with totals.
    """
    # Load dataset
    old_df = pd.read_excel(dataset_path)
    
    # Filter for open complaints (FIXED: was referencing 'df' instead of 'old_df')
    df = old_df[old_df['CLOSED/OPEN'].str.lower().str.strip() == 'open']
    
    # Ensure DATE column is datetime
    df['DATE'] = pd.to_datetime(df['DATE'])

    # **FIX: Clean data before pivoting**
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()

    # Calculate age in days
    today = pd.Timestamp.today()
    df['Age_Days'] = (today - df['DATE']).dt.days

    # Define age buckets (FIXED: bin ranges to match labels correctly)
    bins = [0, 15, 30, 60, 90, 180, float('inf')]
    labels = ['<15Days', '16-30Days', '31-60Days', '61-90Days', '91-180Days', '>180Days']
    df['Age_Bucket'] = pd.cut(df['Age_Days'], bins=bins, labels=labels, right=True, include_lowest=True)    
    
    # Pivot table with complaint type + age bucket
    pivot_data = pd.pivot_table(
        df,
        values='CLOSED/OPEN',           # column to count
        index='COMPLAINT TYPE',          # rows (no list needed for single column)
        columns='Age_Bucket',            # columns (no list needed for single column)
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
    
    # Convert to dictionary (orient='records' for better format)
    dict_pivot_data = pivot_data.to_dict(orient='records')
    
    return dict_pivot_data


def agging_open_close_pivot_dict(dataset_path: str) -> dict:
    """
    Reads an Excel file, creates a pivot table of complaint type vs age bucket,
    adds grand totals (row + column), and returns the result as a dictionary.
    
    Parameters
    ----------
    dataset_path : str
        Path to the Excel dataset.
    
    Returns
    -------
    dict
        Dictionary representation of the pivot table with totals.
    """
    # Load dataset
    old_df = pd.read_excel(dataset_path)
    df = old_df.copy()

    # Ensure DATE column is datetime
    df['DATE'] = pd.to_datetime(df['DATE'])

    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()

    # Calculate age in days
    today = pd.Timestamp.today()
    df['Age_Days'] = (today - df['DATE']).dt.days

    # Define age buckets (fixed bin ranges)
    bins = [0, 15, 30, 60, 90, 180, float('inf')]
    labels = ['<15Days', '16-30Days', '31-60Days', '61-90Days', '91-180Days', '>180Days']
    df['Age_Bucket'] = pd.cut(df['Age_Days'], bins=bins, labels=labels, right=True, include_lowest=True)    
    
    # Pivot table with complaint type + age bucket
    pivot_data = pd.pivot_table(
        df,
        values='CLOSED/OPEN',           # column to count
        index='COMPLAINT TYPE',          # rows (no list needed for single column)
        columns='Age_Bucket',            # columns (no list needed for single column)
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
    
    # Convert to dictionary (orient='records' for better format)
    dict_pivot_data = pivot_data.to_dict(orient='records')
    
    return dict_pivot_data



def generate_all_agging_complaint_report(dataset_path: str) -> dict:
    """
    Load complaint dataset, clean data, calculate age buckets,
    build pivot table, and return as dictionary report.
    """

    # Load dataset
    df = pd.read_excel(dataset_path)

    # Ensure DATE column is datetime
    df['DATE'] = pd.to_datetime(df['DATE'])

    # Clean string columns
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()
    df['DEPT'] = df['DEPT'].astype(str).str.strip().str.title()
    df['CLOSED/OPEN'] = df['CLOSED/OPEN'].astype(str).str.strip().str.title()

    # Calculate age in days
    today = pd.Timestamp.today()
    df['Age_Days'] = (today - df['DATE']).dt.days

    # Define age buckets
    bins = [0, 15, 30, 60, 90, 180, float('inf')]
    labels = ['<15Days', '16-30Days', '31-60Days', '61-90Days', '91-180Days', '>180Days']
    df['Age_Bucket'] = pd.cut(df['Age_Days'], bins=bins, labels=labels, right=True, include_lowest=True)

    # Pivot table with complaint type + age bucket + dept + open/close
    pivot_data_df = pd.pivot_table(
        df,
        values='SL.NO',
        index=['COMPLAINT TYPE'],              # rows
        columns=['Age_Bucket','DEPT','CLOSED/OPEN'],  # include CLOSED/OPEN in columns
        aggfunc='count',
        fill_value=0
    )

    # Add Grand Total column (row-wise sum)
    pivot_data_df['Grand_Total'] = pivot_data_df.sum(axis=1)

    # Add Grand Total row (column-wise sum)
    pivot_data_df.loc['Grand_Total'] = pivot_data_df.sum(axis=0)

    # Convert to dictionary
    all_aging_dict = pivot_data_df.to_dict(orient='records')

    return all_aging_dict



def open_close_complaint_report(dataset_path: str) -> dict:
    """
    Reads an Excel file, creates a pivot table of complaint type vs department & status,
    adds grand totals (row + column), and returns the result as a dictionary.

    Parameters
    ----------
    dataset_path : str
        Path to the Excel dataset.

    Returns
    -------
    dict
        Dictionary representation of the pivot table with totals.
    """
    # Load dataset
    df = pd.read_excel(dataset_path)
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip().str.title()


    # Create pivot table
    pivot_data = pd.pivot_table(
        df,
        index='COMPLAINT TYPE',
        columns=['DEPT', 'CLOSED/OPEN'],
        aggfunc='size',
        fill_value=0
    )

    # Add Grand Total column (row-wise sum)
    pivot_data['Grand_Total'] = pivot_data.sum(axis=1)

    # Add Grand Total row (column-wise sum)
    pivot_data.loc['Grand_Total'] = pivot_data.sum(axis=0)

    # Ensure integers
    pivot_data = pivot_data.astype(int)

    # **FIX: Flatten the MultiIndex columns to strings**
    if isinstance(pivot_data.columns, pd.MultiIndex):
        pivot_data.columns = [
            '_'.join(map(str, col)).strip('_') if isinstance(col, tuple) else str(col)
            for col in pivot_data.columns
        ]

    # Reset index to make 'COMPLAINT TYPE' a column
    pivot_data = pivot_data.reset_index()

    # Convert to dictionary
    dict_pivot_data = pivot_data.to_dict(orient='records')

    return dict_pivot_data