import os
import base64
import asyncio

import httpx
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from groq import AsyncGroq

router = APIRouter()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY")

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.3-70b-versatile"
)

TTS_MODEL = os.getenv(
    "DEEPGRAM_TTS_MODEL",
    "aura-2-thalia-en"
)

groq_client = (
    AsyncGroq(api_key=GROQ_API_KEY)
    if GROQ_API_KEY
    else None
)

SYSTEM_PROMPT = """
You are Doc Voice AI, a friendly and professional
doctor appointment booking assistant.

Your responsibilities:
- Help users book doctor appointments.
- Ask which doctor or specialty they want.
- Ask their preferred date and time.
- Collect only the information needed for booking.
- Speak naturally, politely, and conversationally.
- Keep answers short and easy to understand.
- Confirm booking details before claiming a booking is complete.
- Never claim an appointment is booked unless the booking
  system confirms it.
- Do not diagnose diseases or recommend medicines.
- If someone asks for medical advice, explain that you can
  help them arrange an appointment with a qualified doctor.

Do not invent doctor availability or appointment details.
"""


async def generate_ai_response(message, history):
    if not groq_client:
        raise RuntimeError("GROQ_API_KEY is missing.")

    history.append({
        "role": "user",
        "content": message
    })

    response = await groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            *history
        ],
        temperature=0.5,
        max_tokens=250
    )

    answer = response.choices[0].message.content

    if not answer:
        answer = "Sorry, could you please repeat that?"

    history.append({
        "role": "assistant",
        "content": answer
    })

    # Keep recent conversation context.
    del history[:-12]

    return answer


async def generate_speech(text):
    if not DEEPGRAM_API_KEY:
        raise RuntimeError("DEEPGRAM_API_KEY is missing.")

    url = "https://api.deepgram.com/v1/speak"

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}",
        "Content-Type": "application/json"
    }

    params = {
        "model": TTS_MODEL,
        "encoding": "mp3"
    }

    payload = {
        "text": text
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            url,
            headers=headers,
            params=params,
            json=payload
        )

        response.raise_for_status()

        return response.content


@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()

    history = []

    try:
        await websocket.send_json({
            "event": "connected",
            "message": "Doc Voice AI is ready."
        })

        while True:
            data = await websocket.receive_json()

            event = data.get("event")

            # Frontend must send recognized text in this format.
            if event != "user_text":
                await websocket.send_json({
                    "event": "error",
                    "message": (
                        "Expected event='user_text' with a text field."
                    )
                })
                continue

            user_text = data.get("text", "").strip()

            if not user_text:
                continue

            await websocket.send_json({
                "event": "processing",
                "message": "Preparing your response..."
            })

            try:
                answer = await generate_ai_response(
                    user_text,
                    history
                )

                audio_bytes = await generate_speech(answer)

                audio_base64 = base64.b64encode(
                    audio_bytes
                ).decode("utf-8")

                await websocket.send_json({
                    "event": "assistant_response",
                    "text": answer,
                    "audio": audio_base64,
                    "audio_format": "mp3"
                })

            except httpx.HTTPStatusError as error:
                print(
                    "API error:",
                    error.response.status_code,
                    error.response.text[:500]
                )

                await websocket.send_json({
                    "event": "error",
                    "message": (
                        "The voice service returned an API error. "
                        "Please check the server logs and API keys."
                    )
                })

            except Exception as error:
                print("Voice Engine Error:", repr(error))

                await websocket.send_json({
                    "event": "error",
                    "message": (
                        "Sorry, I could not prepare a voice response."
                    )
                })

    except WebSocketDisconnect:
        print("Voice client disconnected.")

    except Exception as error:
        print("WebSocket Error:", repr(error))

        try:
            await websocket.close()
        except Exception:
            pass