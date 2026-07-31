from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from zoneinfo import ZoneInfo
from config.database import Base 

# Helper function to automatically fetch exact IST time
def get_ist_time():
    return datetime.now(ZoneInfo("Asia/Kolkata"))

class AIUsageLog(Base):
    __tablename__ = "ai_usage_logs"

    id = Column(Integer, primary_key=True, index=True)
    
    # 1. Client & User Identification
    client_name = Column(String, index=True) # e.g., 'SSS', 'SGS', 'Demo'
    user_email = Column(String, index=True)  # Email of the Student/Faculty/HM/Admin/Parent
    
    # 2. Module & Feature Tracking
    module_name = Column(String, index=True) # e.g., 'Student Dashboard', 'Faculty Dashboard'
    feature_name = Column(String)            # e.g., 'Quiz Generator', 'Language Translator'
    
    # 3. Token Tracking
    prompt_tokens = Column(Integer, default=0)
    completion_tokens = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    
    # 4. Accurate Time Tracking in IST
    timestamp_ist = Column(DateTime, default=get_ist_time)