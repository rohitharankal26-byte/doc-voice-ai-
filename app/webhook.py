from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import AppointmentDB
from app.schemas import AppointmentCreate, AppointmentResponse
from app.services import send_whatsapp_message

router = APIRouter(prefix="/api", tags=["Appointments"])

@router.post("/appointments", response_model=AppointmentResponse)
def create_appointment(data: AppointmentCreate, db: Session = Depends(get_db)):
    # Create DB entry
    new_appt = AppointmentDB(
        patient_name=data.patient_name,
        phone_number=data.phone_number,
        appointment_time=data.appointment_time,
        doctor_name=data.doctor_name,
        call_id=data.call_id
    )
    db.add(new_appt)
    db.commit()
    db.refresh(new_appt)

    # Send Instant WhatsApp Confirmation
    whatsapp_msg = (
        f" Namaskar {data.patient_name} ji!\n\n"
        f" Tumchi appointment successfully book jhali ahe.\n"
        f" Doctor: {data.doctor_name}\n"
        f" Date & Time: {data.appointment_time}\n\n"
        f" Dhanyavad!"
    )
    send_whatsapp_message(data.phone_number, whatsapp_msg)

    return new_appt

@router.get("/appointments")
def get_all_appointments(db: Session = Depends(get_db)):
    return db.query(AppointmentDB).order_by(AppointmentDB.id.desc()).all()

@router.post("/whatsapp-webhook")
def whatsapp_incoming_reply(From: str = Form(...), Body: str = Form(...), db: Session = Depends(get_db)):
    """ Handles replies from patients (CANCEL/RESCHEDULE) """
    clean_phone = From.replace("whatsapp:", "").strip()
    user_msg = Body.strip().upper()

    appt = db.query(AppointmentDB).filter(
        AppointmentDB.phone_number.contains(clean_phone),
        AppointmentDB.status == "scheduled"
    ).first()

    if not appt:
        return {"status": "No active appointment found"}

    if "CANCEL" in user_msg:
        appt.status = "cancelled"
        db.commit()
        reply = " Tumchi appointment cancel karnyat ali ahe."
        send_whatsapp_message(clean_phone, reply)
    elif "RESCHEDULE" in user_msg:
        appt.status = "rescheduled"
        db.commit()
        reply = " Reschedule request milali ahe. Amchi team tumhala lagesch call karel."
        send_whatsapp_message(clean_phone, reply)

    return {"status": "success"}