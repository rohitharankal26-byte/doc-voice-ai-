import os
os.environ["DISABLE_SQLALCHEMY_CEXT"] = "1"
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler

from app.database import Base, engine
import app.models
from app.webhook import router as api_router
from app.voice_engine import router as voice_router
from app.services import check_and_send_reminders, send_doctor_daily_summary

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
app.include_router(voice_router)

scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_reminders, 'interval', minutes=10)
scheduler.add_job(send_doctor_daily_summary, 'cron', hour=8, minute=0)
scheduler.start()

@app.get("/")
def home():
    return {"status": "Doc Voice AI Backend & Voice Engine Running Smoothly!"}