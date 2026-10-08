import os
from twilio.rest import Client
from datetime import datetime, timedelta
from app.database import SessionLocal
from app.models import AppointmentDB

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")
DOCTOR_PHONE = os.getenv("DOCTOR_PHONE", "")

def send_whatsapp_message(to_number: str, message_body: str):
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("Twilio credentials missing. Skipping WhatsApp message.")
        return False
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        if not to_number.startswith("whatsapp:"):
            to_number = f"whatsapp:{to_number}"
        
        client.messages.create(
            from_=TWILIO_WHATSAPP_NUMBER,
            body=message_body,
            to=to_number
        )
        return True
    except Exception as e:
        print(f"Error sending WhatsApp message: {e}")
        return False

def check_and_send_reminders():
    """ Runs every 10 mins: Checks appointments in next 1 hour and sends reminder """
    db = SessionLocal()
    try:
        now = datetime.now()
        one_hour_later = now + timedelta(hours=1)
        
        appointments = db.query(AppointmentDB).filter(
            AppointmentDB.status == "scheduled",
            AppointmentDB.reminder_sent == 0
        ).all()

        for appt in appointments:
            try:
                appt_time = datetime.strptime(appt.appointment_time, "%Y-%m-%d %H:%M")
                if now <= appt_time <= one_hour_later:
                    msg = (
                        f" Namaskar {appt.patient_name} ji,\n\n"
                        f" Tumchi appointment {appt.doctor_name} sobat "
                        f"aaj {appt.appointment_time.split(' ')[1]} vajta ahe.\n\n"
                        f" Krpaya velevar pahuncha. Cancel/Reschedule sathi uttar dya."
                    )
                    send_whatsapp_message(appt.phone_number, msg)
                    appt.reminder_sent = 1
                    db.commit()
            except Exception as ex:
                print(f"Error parsing date for appt id {appt.id}: {ex}")
    finally:
        db.close()

def send_doctor_daily_summary():
    """ Runs daily at 8:00 AM: Sends today's appointments list to Doctor """
    if not DOCTOR_PHONE:
        return
    db = SessionLocal()
    try:
        today_str = datetime.now().strftime("%Y-%m-%d")
        appointments = db.query(AppointmentDB).filter(
            AppointmentDB.appointment_time.like(f"{today_str}%"),
            AppointmentDB.status == "scheduled"
        ).all()

        if not appointments:
            summary_msg = f" Suprabhat Doctor! Aaj ({today_str}) ek pan appointment scheduled nahiye."
        else:
            summary_msg = f" Suprabhat Doctor! Aaj ({today_str}) chya appointments:\n\n"
            for idx, appt in enumerate(appointments, 1):
                time_part = appt.appointment_time.split(" ")[1] if " " in appt.appointment_time else appt.appointment_time
                summary_msg += f"{idx}. {appt.patient_name} - {time_part} ({appt.phone_number})\n"

        send_whatsapp_message(DOCTOR_PHONE, summary_msg)
    finally:
        db.close()