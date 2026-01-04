import pandas as pd
import numpy as np



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
    df['COMPLAINT TYPE'] = df['COMPLAINT TYPE'].astype(str).str.strip()
    df['DEPT'] = df['DEPT'].astype(str).str.strip()
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

    return pivot_data
