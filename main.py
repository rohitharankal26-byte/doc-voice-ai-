import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import Base, engine
import app.models  # Models import karna garjeche ahe!
from app.webhook import router as api_router
from app.services import check_and_send_reminders, send_doctor_daily_summary

# Create DB Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Doc Voice AI Backend", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Scheduler setup for automated reminders and daily summary
scheduler = BackgroundScheduler()
# Check for 1-hour reminders every 10 minutes
scheduler.add_job(check_and_send_reminders, 'interval', minutes=10)
# Send doctor daily summary every day at 8:00 AM
scheduler.add_job(send_doctor_daily_summary, 'cron', hour=8, minute=0)
scheduler.start()

@app.get("/")
def home():
    return {"status": "Doc Voice AI Backend Running Smoothly!"}