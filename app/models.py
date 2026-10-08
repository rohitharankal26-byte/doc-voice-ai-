from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from app.database import Base

class AppointmentDB(Base):
    _tablename_ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_name = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    appointment_time = Column(String, nullable=False) # Format: YYYY-MM-DD HH:MM
    doctor_name = Column(String, default="Dr. Sharma")
    call_id = Column(String, nullable=True)
    status = Column(String, default="scheduled") # scheduled, completed, cancelled, rescheduled
    reminder_sent = Column(Integer, default=0) # 0 = No, 1 = Yes
    created_at = Column(DateTime, default=datetime.utcnow)