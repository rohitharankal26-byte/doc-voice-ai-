from pydantic import BaseModel
from typing import Optional

class AppointmentCreate(BaseModel):
    patient_name: str
    phone_number: str
    appointment_time: str
    doctor_name: Optional[str] = "Dr. Sharma"
    call_id: Optional[str] = None

class AppointmentResponse(AppointmentCreate):
    id: int
    status: str
    reminder_sent: int

    class Config:
        from_attributes = True