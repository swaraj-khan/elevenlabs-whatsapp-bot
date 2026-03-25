import os
import json
import websockets
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse

load_dotenv()

AGENT_ID = os.getenv("AGENT_ID")
ELEVEN_API_KEY = os.getenv("ELEVENLABS_API_KEY")

AUTHKEY_API_KEY = os.getenv("AUTHKEY_API_KEY")
AUTHKEY_BRAND_NUMBER = os.getenv("AUTHKEY_BRAND_NUMBER")

ELEVEN_WS_URL = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={AGENT_ID}"

app = FastAPI()


async def get_agent_response(user_text: str):
    async with websockets.connect(
        ELEVEN_WS_URL,
        additional_headers={"xi-api-key": ELEVEN_API_KEY}
    ) as ws:

        await ws.send(json.dumps({
            "type": "conversation_initiation_client_data",
            "conversation_config_override": {
                "conversation": {"text_only": True}
            }
        }))

        await ws.send(json.dumps({
            "type": "user_message",
            "text": user_text
        }))

        while True:
            data = json.loads(await ws.recv())

            if data["type"] == "agent_response":
                return data["agent_response_event"]["agent_response"]

            if data["type"] == "ping":
                await ws.send(json.dumps({
                    "type": "pong",
                    "event_id": data["ping_event"]["event_id"]
                }))


async def send_whatsapp_reply(to_number: str, message: str):
    async with httpx.AsyncClient(timeout=10) as client:
        await client.post(
            "https://console.authkey.io/restapi/convjson.php",
            json={
                "mobile": to_number, 
                "message_type": "text",
                "brand_number": AUTHKEY_BRAND_NUMBER,
                "message": message
            },
            headers={
                "Authorization": f"Basic {AUTHKEY_API_KEY}", 
                "Content-Type": "application/json"
            }
        )


@app.post("/chat")
async def chat(request: Request):
    try:
        body = await request.json()
    except:
        form = await request.form()
        body = dict(form)

    user_text = body.get("eventContent[message][text][body]")
    user_number = body.get("eventContent[message][from]")

    if not user_text or not user_number:
        return PlainTextResponse("OK")

    response = await get_agent_response(user_text)
    await send_whatsapp_reply(user_number, response)

    return PlainTextResponse("OK")