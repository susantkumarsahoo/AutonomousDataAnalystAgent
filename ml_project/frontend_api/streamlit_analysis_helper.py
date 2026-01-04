import time
from ml_project.utils.helper import read_yaml
import pandas as pd
import numpy as np



config = read_yaml("ml_project/config/ml_project_config.yaml")
dataset_path = config["data"]["raw_path"]

# Add this function before your tab1 code (at the top of your file or before the tab section)
def stream_data():
    """Generator function to stream complaint data with animation"""
    messages = [
        "🔍 Connecting to API...\n",
        "📊 Fetching complaint data...\n",
        "🔄 Processing records...\n",
        "✅ Data retrieved successfully!\n"
    ]
    
    for message in messages:
        for char in message:
            yield char
            time.sleep(0.02)  # Adjust speed of streaming
        time.sleep(0.3)  # Pause between messages

import time

def stream_pivot_data(dataset_path: str):
    """
    Stream the process of generating pivot table with progress updates.
    
    Parameters
    ----------
    dataset_path : str
        Path to the Excel file containing complaint data.
        
    Yields
    ------
    str
        Progress messages during data processing.
    """
    yield "🔍 Loading complaint dataset...\n"
    time.sleep(0.3)
    
    # Load dataset
    df = pd.read_excel(dataset_path)
    yield f"✅ Loaded {len(df)} total complaints\n"
    time.sleep(0.3)
    
    # Filter only open complaints
    df_open = df[df['CLOSED/OPEN'].str.lower().str.strip() == 'open']
    yield f"📊 Found {len(df_open)} open complaints\n"
    time.sleep(0.3)
    
    yield "🔄 Creating pivot table...\n"
    time.sleep(0.3)
    
    # Create pivot table
    pivot = pd.pivot_table(
        df_open,
        values='CLOSED/OPEN',
        index='COMPLAINT TYPE',
        columns='DEPT',
        aggfunc='count',
        fill_value=0
    )
    
    yield f"✅ Pivot table created with {len(pivot)} complaint types\n"
    time.sleep(0.3)
    
    # Add Grand Total column and row
    pivot['Grand_Total'] = pivot.sum(axis=1)
    pivot.loc['Grand_Total'] = pivot.sum(axis=0)
    pivot = pivot.astype(int)
    pivot = pivot.reset_index()
    
    yield "✨ Grand totals calculated\n"
    time.sleep(0.2)
    yield "🎉 Data ready!\n"


def stream_piv_data(dataset_path: str):
    """Minimal streaming for pivot data generation."""
    messages = [
        "🔍 Loading data...\n",
        "📊 Filtering open complaints...\n", 
        "🔄 Building pivot table...\n",
        "✅ Complete!\n"
    ]
    
    for msg in messages:
        yield msg
        time.sleep(0.4)


