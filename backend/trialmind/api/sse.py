import json
from typing import AsyncIterator

from trialmind.agents.analyzer import run_analyzer
from trialmind.agents.citation_checker import run_citation_checker
from trialmind.agents.retriever import run_retriever
from trialmind.graph.state import AgentState

MAX_ITERATIONS = 2


def _sse(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data)}


def _trace_payload(ev) -> dict:
    return {
        "agent": ev.agent,
        "at": ev.at.isoformat(),
        "summary": ev.summary,
        "payload": ev.payload,
    }


async def stream_answer(question: str) -> AsyncIterator[dict]:
    """Run retriever → analyzer → checker, yielding each new trace event live.

    Mirrors the LangGraph supervisor's retry behavior (checker fails →
    retriever re-runs with refined_query, up to MAX_ITERATIONS) but yields
    events as they happen instead of after the whole graph terminates.
    """
    state = AgentState(question=question)

    while True:
        state = await run_retriever(state)
        yield _sse("trace", _trace_payload(state.trace[-1]))

        state = await run_analyzer(state)
        yield _sse("trace", _trace_payload(state.trace[-1]))

        state = await run_citation_checker(state)
        yield _sse("trace", _trace_payload(state.trace[-1]))

        checker_ok = state.check_result and state.check_result.ok
        if checker_ok or state.iteration >= MAX_ITERATIONS:
            break

    citations = [
        {"chunk_id": c.chunk_id, "trial_id": c.trial_id, "section": c.section,
         "text": c.text, "score": c.score}
        for c in state.chunks
    ]
    yield _sse("final", {
        "answer": state.draft_answer,
        "citations": citations,
        "check_ok": bool(checker_ok),
        "issues": state.check_result.issues if state.check_result else [],
    })
