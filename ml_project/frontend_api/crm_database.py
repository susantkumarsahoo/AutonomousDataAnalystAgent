import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, Date, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel, validator, Field
from datetime import datetime, date
from typing import Optional
import pandas as pd

# SQLAlchemy setup
Base = declarative_base()
engine = create_engine('sqlite:///crm_database.db', echo=False)
Session = sessionmaker(bind=engine)

# SQLAlchemy Model
class ComplaintDB(Base):
    __tablename__ = 'complaints'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(Date)
    shift_duty = Column(String(100))
    query_request_complaint = Column(String(200))
    complaint_details = Column(Text)
    complaint_number = Column(String(14), unique=True, nullable=False)
    section = Column(String(100))
    sub_division = Column(String(100))
    division = Column(String(100))
    circle = Column(String(100))
    complaint_type = Column(String(100))
    consumer_number = Column(String(12), nullable=False)
    mobile_numb = Column(String(10), nullable=False)
    dept = Column(String(100))
    closed_open = Column(String(20))
    remarks = Column(Text)
    tweet_link = Column(String(500))
    complainant_name = Column(String(200))
    complaint_received_time = Column(DateTime)
    response_time = Column(DateTime)
    second_response_time = Column(DateTime)
    final_response_time = Column(DateTime)
    final_response_date = Column(Date)
    pscc_fg_to = Column(String(100))
    arrears = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)

# Create tables
Base.metadata.create_all(engine)

# Pydantic Validation Model
class ComplaintValidator(BaseModel):
    date: Optional[date] = None
    shift_duty: Optional[str] = Field(None, max_length=100)
    query_request_complaint: Optional[str] = Field(None, max_length=200)
    complaint_details: Optional[str] = None
    complaint_number: str = Field(..., min_length=14, max_length=14)
    section: Optional[str] = Field(None, max_length=100)
    sub_division: Optional[str] = Field(None, max_length=100)
    division: Optional[str] = Field(None, max_length=100)
    circle: Optional[str] = Field(None, max_length=100)
    complaint_type: Optional[str] = Field(None, max_length=100)
    consumer_number: str = Field(..., min_length=12, max_length=12)
    mobile_numb: str = Field(..., min_length=10, max_length=10)
    dept: Optional[str] = Field(None, max_length=100)
    closed_open: str = "OPEN"
    remarks: Optional[str] = None
    tweet_link: Optional[str] = Field(None, max_length=500)
    complainant_name: Optional[str] = Field(None, max_length=200)
    complaint_received_time: Optional[datetime] = None
    response_time: Optional[datetime] = None
    second_response_time: Optional[datetime] = None
    final_response_time: Optional[datetime] = None
    final_response_date: Optional[date] = None
    pscc_fg_to: Optional[str] = Field(None, max_length=100)
    arrears: Optional[str] = Field(None, max_length=100)
    
    @validator('complaint_number')
    def validate_complaint_number(cls, v):
        if not v.isdigit():
            raise ValueError('Complaint number must contain only digits')
        if len(v) != 14:
            raise ValueError('Complaint number must be exactly 14 digits')
        return v
    
    @validator('consumer_number')
    def validate_consumer_number(cls, v):
        if not v.isdigit():
            raise ValueError('Consumer number must contain only digits')
        if len(v) != 12:
            raise ValueError('Consumer number must be exactly 12 digits')
        return v
    
    @validator('mobile_numb')
    def validate_mobile_number(cls, v):
        if not v.isdigit():
            raise ValueError('Mobile number must contain only digits')
        if len(v) != 10:
            raise ValueError('Mobile number must be exactly 10 digits')
        return v
    
    class Config:
        arbitrary_types_allowed = True

# Database operations
def save_complaint(data: ComplaintValidator):
    """Save complaint to database using SQLAlchemy"""
    session = Session()
    try:
        complaint = ComplaintDB(
            date=data.date,
            shift_duty=data.shift_duty,
            query_request_complaint=data.query_request_complaint,
            complaint_details=data.complaint_details,
            complaint_number=data.complaint_number,
            section=data.section,
            sub_division=data.sub_division,
            division=data.division,
            circle=data.circle,
            complaint_type=data.complaint_type,
            consumer_number=data.consumer_number,
            mobile_numb=data.mobile_numb,
            dept=data.dept,
            closed_open=data.closed_open,
            remarks=data.remarks,
            tweet_link=data.tweet_link,
            complainant_name=data.complainant_name,
            complaint_received_time=data.complaint_received_time,
            response_time=data.response_time,
            second_response_time=data.second_response_time,
            final_response_time=data.final_response_time,
            final_response_date=data.final_response_date,
            pscc_fg_to=data.pscc_fg_to,
            arrears=data.arrears
        )
        session.add(complaint)
        session.commit()
        return True, "Complaint saved successfully!"
    except Exception as e:
        session.rollback()
        return False, f"Error: {str(e)}"
    finally:
        session.close()

def get_all_complaints():
    """Retrieve all complaints"""
    session = Session()
    try:
        complaints = session.query(ComplaintDB).order_by(ComplaintDB.created_at.desc()).all()
        data = []
        for c in complaints:
            data.append({
                'ID': c.id,
                'Date': c.date,
                'Shift': c.shift_duty,
                'Query': c.query_request_complaint,
                'Details': c.complaint_details,
                'Complaint#': c.complaint_number,
                'Section': c.section,
                'Sub-Div': c.sub_division,
                'Division': c.division,
                'Circle': c.circle,
                'Type': c.complaint_type,
                'Consumer#': c.consumer_number,
                'Mobile': c.mobile_numb,
                'Dept': c.dept,
                'Status': c.closed_open,
                'Remarks': c.remarks,
                'Link': c.tweet_link,
                'Name': c.complainant_name,
                'Received': c.complaint_received_time,
                'Response1': c.response_time,
                'Response2': c.second_response_time,
                'Final Resp': c.final_response_time,
                'Final Date': c.final_response_date,
                'PSCC': c.pscc_fg_to,
                'Arrears': c.arrears,
                'Created': c.created_at
            })
        return pd.DataFrame(data)
    finally:
        session.close()

def delete_complaint(complaint_id):
    """Delete complaint by ID"""
    session = Session()
    try:
        complaint = session.query(ComplaintDB).filter_by(id=complaint_id).first()
        if complaint:
            session.delete(complaint)
            session.commit()
            return True, "Deleted successfully!"
        return False, "Complaint not found"
    except Exception as e:
        session.rollback()
        return False, f"Error: {str(e)}"
    finally:
        session.close()

def parse_datetime(date_str):
    """Parse datetime string"""
    if not date_str or date_str.strip() == "":
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
        except:
            return None

# Streamlit App
st.set_page_config(page_title="CRM System", page_icon="📊", layout="wide")

# Custom CSS for compact layout
st.markdown("""
<style>
    .stTextInput>div>div>input, .stTextArea>div>div>textarea, 
    .stSelectbox>div>div>select, .stDateInput>div>div>input {
        padding: 0.25rem 0.5rem !important;
        font-size: 0.85rem !important;
        height: 2rem !important;
    }
    .stTextArea>div>div>textarea {
        height: 4rem !important;
    }
    .stButton>button {
        padding: 0.25rem 1rem !important;
        font-size: 0.85rem !important;
    }
    div[data-testid="stForm"] {
        padding: 0.5rem !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0.5rem !important;
    }
    h2 {
        font-size: 1.3rem !important;
        margin-bottom: 0.5rem !important;
    }
    h3 {
        font-size: 1.1rem !important;
        margin: 0.3rem 0 !important;
    }
    .element-container {
        margin-bottom: 0.3rem !important;
    }
    div[data-testid="column"] {
        padding: 0.3rem !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("📊 CRM System")
st.markdown("---")

tab1, tab2 = st.tabs(["📝 New Entry", "📊 View Data"])

with tab1:
    st.subheader("New Complaint")
    
    with st.form("complaint_form", clear_on_submit=True):
        # Row 1 - Basic Info
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            date_input = st.date_input("Date", label_visibility="visible")
        with c2:
            shift_duty = st.text_input("Shift Duty")
        with c3:
            query_request = st.text_input("Query/Request")
        with c4:
            complaint_type = st.text_input("Complaint Type")
        with c5:
            status = st.selectbox("Status", ["OPEN", "CLOSED"])
        
        # Row 2 - Numbers (Critical Fields)
        c6, c7, c8 = st.columns(3)
        with c6:
            complaint_num = st.text_input("Complaint Number* (14 digits)", max_chars=14)
        with c7:
            consumer_num = st.text_input("Consumer Number* (12 digits)", max_chars=12)
        with c8:
            mobile_num = st.text_input("Mobile Number* (10 digits)", max_chars=10)
        
        # Row 3 - Location
        c9, c10, c11, c12, c13 = st.columns(5)
        with c9:
            section = st.text_input("Section")
        with c10:
            sub_division = st.text_input("Sub-Division")
        with c11:
            division = st.text_input("Division")
        with c12:
            circle = st.text_input("Circle")
        with c13:
            dept = st.text_input("Department")
        
        # Row 4 - Personal Info
        c14, c15, c16, c17 = st.columns(4)
        with c14:
            complainant_name = st.text_input("Complainant Name")
        with c15:
            pscc_fg_to = st.text_input("PSCC/FG/TO")
        with c16:
            arrears = st.text_input("Arrears")
        with c17:
            tweet_link = st.text_input("Tweet/Link")
        
        # Row 5 - Details
        c18, c19 = st.columns(2)
        with c18:
            complaint_details = st.text_area("Complaint Details", height=80)
        with c19:
            remarks = st.text_area("Remarks", height=80)
        
        # Row 6 - Timestamps
        c20, c21, c22, c23 = st.columns(4)
        with c20:
            complaint_received = st.text_input("Received (YYYY-MM-DD HH:MM:SS)")
        with c21:
            response_time_input = st.text_input("Response 1 (YYYY-MM-DD HH:MM:SS)")
        with c22:
            second_response = st.text_input("Response 2 (YYYY-MM-DD HH:MM:SS)")
        with c23:
            final_response_input = st.text_input("Final Response (YYYY-MM-DD HH:MM:SS)")
        
        # Row 7 - Final Date
        final_date = st.date_input("Final Response Date")
        
        submitted = st.form_submit_button("💾 Save", use_container_width=True, type="primary")
        
        if submitted:
            try:
                # Prepare data for Pydantic validation
                complaint_data = ComplaintValidator(
                    date=date_input,
                    shift_duty=shift_duty if shift_duty else None,
                    query_request_complaint=query_request if query_request else None,
                    complaint_details=complaint_details if complaint_details else None,
                    complaint_number=complaint_num,
                    section=section if section else None,
                    sub_division=sub_division if sub_division else None,
                    division=division if division else None,
                    circle=circle if circle else None,
                    complaint_type=complaint_type if complaint_type else None,
                    consumer_number=consumer_num,
                    mobile_numb=mobile_num,
                    dept=dept if dept else None,
                    closed_open=status,
                    remarks=remarks if remarks else None,
                    tweet_link=tweet_link if tweet_link else None,
                    complainant_name=complainant_name if complainant_name else None,
                    complaint_received_time=parse_datetime(complaint_received),
                    response_time=parse_datetime(response_time_input),
                    second_response_time=parse_datetime(second_response),
                    final_response_time=parse_datetime(final_response_input),
                    final_response_date=final_date,
                    pscc_fg_to=pscc_fg_to if pscc_fg_to else None,
                    arrears=arrears if arrears else None
                )
                
                # Save to database
                success, message = save_complaint(complaint_data)
                if success:
                    st.success(f"✅ {message}")
                    st.balloons()
                else:
                    st.error(f"❌ {message}")
                    
            except Exception as e:
                st.error(f"❌ Validation Error: {str(e)}")

with tab2:
    st.subheader("All Complaints")
    
    # Controls
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_a:
        if st.button("🔄 Refresh"):
            st.rerun()
    
    # Get data
    df = get_all_complaints()
    
    if not df.empty:
        # Stats
        with col_b:
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("Total", len(df))
            with m2:
                st.metric("Open", len(df[df['Status'] == 'OPEN']))
            with m3:
                st.metric("Closed", len(df[df['Status'] == 'CLOSED']))
        
        # Filters
        col_d, col_e = st.columns([2, 1])
        with col_d:
            search = st.text_input("🔍 Search", placeholder="Complaint#, Consumer#, Name...")
        with col_e:
            filter_status = st.selectbox("Filter Status", ["All", "OPEN", "CLOSED"])
        
        # Apply filters
        filtered_df = df.copy()
        if search:
            filtered_df = filtered_df[
                (filtered_df['Complaint#'].astype(str).str.contains(search, na=False)) |
                (filtered_df['Consumer#'].astype(str).str.contains(search, na=False)) |
                (filtered_df['Name'].astype(str).str.contains(search, case=False, na=False))
            ]
        
        if filter_status != "All":
            filtered_df = filtered_df[filtered_df['Status'] == filter_status]
        
        # Display
        st.dataframe(filtered_df, use_container_width=True, height=400)
        
        # Delete
        st.markdown("---")
        del_col1, del_col2 = st.columns([3, 1])
        with del_col1:
            delete_id = st.number_input("Delete ID", min_value=1, step=1)
        with del_col2:
            if st.button("🗑️ Delete", type="secondary"):
                success, msg = delete_complaint(delete_id)
                if success:
                    st.success(f"✅ {msg}")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
    else:
        st.info("📭 No data. Add complaints to get started!")

st.markdown("---")
st.markdown("<p style='text-align: center; color: #666; font-size: 0.8rem;'>CRM System | Pydantic + SQLAlchemy + Streamlit</p>", unsafe_allow_html=True)

# streamlit run ml_project/frontend_api/crm_database.py