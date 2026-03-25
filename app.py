import streamlit as st
import asyncio
import websockets
import json
import os
from dotenv import load_dotenv

load_dotenv()

AGENT_ID = os.getenv("AGENT_ID")
API_KEY = os.getenv("ELEVENLABS_API_KEY")

WS_URL = f"wss://api.elevenlabs.io/v1/convai/conversation?agent_id={AGENT_ID}"

if "messages" not in st.session_state:
    st.session_state.messages = []

async def chat_once(user_input):
    headers = {
        "xi-api-key": API_KEY
    }

    async with websockets.connect(
        WS_URL,
        additional_headers=headers
    ) as ws:

        init_payload = {
            "type": "conversation_initiation_client_data",
            "conversation_config_override": {
                "conversation": {
                    "text_only": True
                }
            }
        }

        await ws.send(json.dumps(init_payload))

        await ws.send(json.dumps({
            "type": "user_message",
            "text": user_input
        }))

        while True:
            msg = await ws.recv()
            data = json.loads(msg)

            if data["type"] == "agent_response":
                return data["agent_response_event"]["agent_response"]

            elif data["type"] == "ping":
                await ws.send(json.dumps({
                    "type": "pong",
                    "event_id": data["ping_event"]["event_id"]
                }))

st.title("ElevenLabs Chat Agent")

for role, msg in st.session_state.messages:
    with st.chat_message(role):
        st.write(msg)

user_input = st.chat_input("Type your message...")

if user_input:
    st.session_state.messages.append(("user", user_input))
    response = asyncio.run(chat_once(user_input))
    st.session_state.messages.append(("agent", response))
    st.rerun()