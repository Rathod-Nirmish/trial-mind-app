import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from trialmind.api.sse import stream_answer

DISCLAIMER = "TrialMind is a portfolio demo, not a medical decision-support tool."

app = FastAPI(title="TrialMind")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatBody(BaseModel):
    question: str


@app.get("/")
def root():
    return {"name": "TrialMind", "disclaimer": DISCLAIMER}


@app.post("/chat")
async def chat(body: ChatBody):
    return EventSourceResponse(stream_answer(body.question))
