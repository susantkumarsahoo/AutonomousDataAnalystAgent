import pandas as pd
import plotly.express as px
import numpy as np
import streamlit as st
import datetime
import plotly.graph_objects as go
from datetime import datetime, timedelta
import re


def get_remarks_df(df):
    """
    Process DataFrame to extract and flag specific patterns from REMARKS column.
    
    Parameters:
    -----------
    df : pd.DataFrame
        Input DataFrame containing complaint/tweet data
        
    Returns:
    --------
    pd.DataFrame
        Filtered DataFrame with extracted features and flags
    """
    df = df.copy()
    
    # ========================================================================
    # DUPLICATE CASE: Extract 3-5 digit numbers, excluding certain patterns
    # ========================================================================
    duplicate_case = []
    
    for remarks in df['REMARKS']:
        if pd.isna(remarks):
            duplicate_case.append('NA')
            continue
        
        remarks_str = str(remarks)
        
        # Check if remarks contain excluded number patterns
        # 12-digit consumer number pattern
        if re.search(r'\b\d{12}\b', remarks_str):
            duplicate_case.append('NA')
            continue
        
        # 14-digit complaint number pattern
        if re.search(r'\b\d{14}\b', remarks_str):
            duplicate_case.append('NA')
            continue
        
        # 10-digit mobile number pattern
        if re.search(r'\b\d{10}\b', remarks_str):
            duplicate_case.append('NA')
            continue
        
        # Extract 3-5 digit numbers only if no exclusion criteria met
        matches = re.findall(r'\b\d{3,5}\b', remarks_str)
        
        if matches:
            duplicate_case.append(', '.join(matches))
        else:
            duplicate_case.append('NA')
    
    # Create the Duplicate Case column
    df['Duplicate Case'] = duplicate_case
    
    # ========================================================================
    # APPRECIATION TWEET: Extract and normalize mentions
    # ========================================================================
    df['Appreciation Tweet'] = (
        df['REMARKS']
        .astype(str)
        .str.findall(r'(?i)\bappreciation\s*tweet\b')
        .apply(lambda x: 'Appreciation Tweet' if x else 'NA')
    )
    
    # ========================================================================
    # AWAITED CONSUMER ID: Flag mentions of awaited consumer/details/response
    # ========================================================================
    df['Awaited Consumer Id'] = (
        df['REMARKS']
        .astype(str)
        .str.contains(
            r"(?i)\b(awaited\s*consumer|details?|exacts?|response?s?|id|asked|ask|ca\.?no|doesn['`]t)\b",
            regex=True,
            na=False
        )
        .map({True: 'Yes', False: 'No'})
        .fillna('NA')
    )

    
    # ========================================================================
    # X USER ID: Extract Twitter/X username from URL
    # ========================================================================
    df['X User Id'] = (
        df['TWEET/LINK']
        .astype(str)
        .str.extract(r'(?:twitter\.com|x\.com)/([^/]+)/', expand=False)
    )
    
    df['X User Id'] = (
        df['X User Id']
        .apply(lambda x: '@' + x if pd.notna(x) and x != 'nan' and x else 'NA')
    )
    
    # ========================================================================
    # STREETLIGHT AND NOT TPWODL: Flag streetlight issues outside TPWODL
    # jurisdiction or containing location/jurisdiction keywords
    # ========================================================================
    df['Streetlight And Not TPWODL'] = (
        (
            df['REMARKS']
            .astype(str)
            .str.contains(r'(?i)\bstreetlight(s)?\b', regex=True, na=False) &
            ~df['REMARKS']
            .astype(str)
            .str.contains(r'(?i)\bTPWODL\b', regex=True, na=False)
        )
        |
        df['REMARKS']
        .astype(str)
        .str.contains(
            r'(?i)\b(not\s+related|dist|jurisdiction|jurisdictions|districts?|'
            r'not\s+under|not\s+coming|under|bhubaneswar|khordha|balasore|city|'
            r'angul|dhenkanal|boudh|koraput|nayagarh|ganjam|mayurbhanj|'
            r'nabarangpur|kandhamal|cuttack)\b',
            regex=True,
            na=False
        )
    )
    
    df['Streetlight And Not TPWODL'] = (
        df['Streetlight And Not TPWODL']
        .map({True: 'Yes', False: 'No'})
        .fillna('No')
    )
    
    # ========================================================================
    # CALL INITIATED CONSUMERS: Flag mentions of callback done
    # ========================================================================
    df['Call Initiated Consumers'] = (
        df['REMARKS']
        .astype(str)
        .str.contains(
            r'(?i)\b(call\s*back\s*done|callback\s*done|callcack\s*done)\b',
            regex=True,
            na=False
        )
        .map({True: 'Yes', False: 'No'})
        .fillna('NA')
    )
    
    # ========================================================================
    # ELEPHANT MOVEMENT: Flag mentions of elephant-related issues
    # ========================================================================
    df['Elephant Movement'] = (
        df['REMARKS']
        .astype(str)
        .str.contains(
            r'(?i)\b(elephant\s*movement|elephan\s*movement|movementum|elephant)\b',
            regex=True,
            na=False
        )
        .map({True: 'Yes', False: 'No'})
        .fillna('NA')
    )
    
    # ========================================================================
    # MAILED SENT: Flag mentions of email/mail communication
    # ========================================================================
    df['Mailed Sent'] = (
        df['REMARKS']
        .astype(str)
        .str.contains(
            r'(?i)\b(mailed|mail|mails|email|emailing)\b',
            regex=True,
            na=False
        )
        .map({True: 'Yes', False: 'No'})
        .fillna('NA')
    )

    # ========================================================================
    # WEATHER EVENT: Flag mentions of weather-related incidents
    # ========================================================================
    df['Weather Event'] = (
        df['REMARKS']
        .astype(str)
        .str.contains(
            r'(?i)\b(kalabaisakhi|kalbaisakhi|kalab|heavy rain|rain|lightning|'
            r'thunder storm|thunderstorm|thunder|storm|heavy wind|wind|rainy|tree fallen|'
            r'Thunderstorm/Lightning/Rain)\b',
            regex=True,
            na=False
        )
        .map({True: 'Yes', False: 'No'})
        .fillna('NA')
    )
    
    # ========================================================================
    # SELECT AND RETURN SPECIFIC COLUMNS
    # ========================================================================
    remarks_filter_df = df[[
        'SL.NO',
        'DATE',
        'DIVISION',
        'CIRCLE',
        'COMPLAINT TYPE',
        'REMARKS',
        'TWEET/LINK',
        'COMPLAINANT NAME',
        'Duplicate Case',
        'Appreciation Tweet',
        'Awaited Consumer Id',
        'X User Id',
        'Streetlight And Not TPWODL',
        'Call Initiated Consumers',
        'Elephant Movement',
        'Mailed Sent',
        'Weather Event'
    ]]
    
    return remarks_filter_df


def get_remarks_counts(remarks_df):
    """
    Generate a summary count DataFrame from remarks_df.
    
    Parameters:
    -----------
    remarks_df : pandas.DataFrame
        DataFrame containing remarks with various categorization columns
    
    Returns:
    --------
    pandas.DataFrame
        Summary DataFrame with categories and their counts
    """
    import pandas as pd
    
    counts_data = {
        'Category': [
            'Duplicate Cases',
            'Awaited Consumer Id',
            'Appreciation Tweets',
            'X User IDs Available',
            'X User IDs Not Available (DM)',
            'Not Related to TPWODL',
            'Calls Initiated to Consumers',
            'Elephant Movement Cases',
            'Emails Sent',
            'Weather Event'
        ],
        'Count': [
            (remarks_df["Duplicate Case"] != "NA").sum(),
            (remarks_df["Awaited Consumer Id"] != "No").sum(),
            (remarks_df["Appreciation Tweet"] != "NA").sum(),
            (remarks_df["X User Id"] != "NA").sum(),
            (remarks_df["X User Id"] == "NA").sum(),
            (remarks_df["Streetlight And Not TPWODL"] != "No").sum(),
            (remarks_df["Call Initiated Consumers"] != "No").sum(),
            (remarks_df["Elephant Movement"] != "No").sum(),
            (remarks_df["Mailed Sent"] != "No").sum(),
            (remarks_df["Weather Event"] != "No").sum()
        ]
    }
    
    # Create summary DataFrame
    summary_df = pd.DataFrame(counts_data)
    
    # Add total records row
    total_row = pd.DataFrame({
        'Category': ['Total Data Length Records'],
        'Count': [len(remarks_df)]
    })
    
    summary_df = pd.concat([summary_df, total_row], ignore_index=True)
    
    return summary_df