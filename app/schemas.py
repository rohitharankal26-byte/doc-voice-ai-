from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AppointmentCreate(BaseModel):
    patient_name: str
    phone_number: str
    appointment_time: str
    doctor_name: Optional[str] = "Dr. Sharma"

class AppointmentResponse(AppointmentCreate):
    id: int
    call_id: Optional[str] = None
    status: str
    reminder_sent: int
    created_at: datetime

    class Config:
        from_attributes = True