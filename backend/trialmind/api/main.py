import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from trialmind import errors
from trialmind.api.corpus import router as corpus_router
from trialmind.api.explorations import router as explorations_router
from trialmind.api.runs import router as runs_router
from trialmind.api.sse import stream_answer
from trialmind.api.usage import router as usage_router
from trialmind.api.workbench import router as workbench_router
from trialmind.budget import assert_within_budget

DISCLAIMER = "TrialMind is a portfolio demo, not a medical decision-support tool."

app = FastAPI(title="TrialMind")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
errors.register(app)
app.include_router(corpus_router)
app.include_router(explorations_router)
app.include_router(runs_router)
app.include_router(usage_router)
app.include_router(workbench_router)


class ChatBody(BaseModel):
    question: str


@app.get("/")
def root():
    return {"name": "TrialMind", "disclaimer": DISCLAIMER}


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.post("/chat")
async def chat(body: ChatBody):
    await assert_within_budget()
    return EventSourceResponse(stream_answer(body.question))
