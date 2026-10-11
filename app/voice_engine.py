import os
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from deepgram import DeepgramClient, LiveTranscriptionEvents
import groq

router = APIRouter()

DEEPGRAM_API_KEY = os.getenv("DEEPGRAM_API_KEY", "your_deepgram_key_here")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "your_groq_key_here")

@router.websocket("/ws/voice")
async def voice_websocket(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket Connection Established with Client")

    try:
        dg_client = DeepgramClient(DEEPGRAM_API_KEY)
        options = {"punctuate": True, "language": "multi"}
        
        # Deepgram live connection start karne (Proper Indentation)
        dg_connection = dg_client.listen.asynclive.v("1")
        
        async def on_message(self, result, **kwargs):
            sentence = result.channel.alternatives[0].transcript
            if len(sentence) > 0:
                print(f"Transcribed: {sentence}")
                await websocket.send_json({"event": "transcription", "text": sentence})

        dg_connection.on(LiveTranscriptionEvents.Transcript, on_message)
        await dg_connection.start(options)

        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            await dg_connection.send(payload)
            
            # Simple Echo / Voice Response Engine Logic
            await websocket.send_json({
                "event": "transcription",
                "text": "Doc Voice AI Listening..."
            })

    except WebSocketDisconnect:
        print("WebSocket Disconnected")
    except Exception as e:
        print(f"Voice Engine Error: {e}")