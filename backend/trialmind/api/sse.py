import json
import logging
import time
from typing import AsyncIterator

from trialmind.agents.analyzer import run_analyzer
from trialmind.agents.citation_checker import run_citation_checker
from trialmind.agents.retriever import run_retriever
from trialmind.db_explorations import create_from_run
from trialmind.db_runs import AgentStep, Citation, create_run
from trialmind.graph.state import AgentState, TraceEvent
from trialmind.tracing import flush as tracing_flush
from trialmind.tracing import span, trace

log = logging.getLogger(__name__)

MAX_ITERATIONS = 2

_AGENT_TO_STEP_NAME = {
    "retriever": "retriever",
    "analyzer": "analyzer",
    "citation_checker": "citation-checker",
    "citation-checker": "citation-checker",
}


def _sse(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data)}


def _trace_payload(ev: TraceEvent) -> dict:
    return {
        "agent": ev.agent,
        "at": ev.at.isoformat(),
        "summary": ev.summary,
        "payload": ev.payload,
    }


def _derive_steps(trace: list[TraceEvent], checker_ok: bool, iterations: int) -> list[AgentStep]:
    """Collapse the flat trace into one AgentStep per agent (frontend shape).

    Time_s = seconds between the first and last event for that agent.
    Retriever gets 'retry' status if there was more than one iteration.
    Checker inherits ok / fail from the final check result.
    """
    by_agent: dict[str, list[TraceEvent]] = {}
    for ev in trace:
        name = _AGENT_TO_STEP_NAME.get(ev.agent, ev.agent)
        by_agent.setdefault(name, []).append(ev)

    steps: list[AgentStep] = []
    for name in ("retriever", "analyzer", "citation-checker"):
        evs = by_agent.get(name)
        if not evs:
            continue
        time_s = round((evs[-1].at - evs[0].at).total_seconds(), 2)
        summary = evs[-1].summary
        if name == "citation-checker":
            status = "ok" if checker_ok else ("retry" if iterations > 0 else "fail")
        elif name == "retriever" and iterations > 0:
            status = "retry"
        else:
            status = "ok"
        steps.append(AgentStep(name=name, status=status, time_s=max(time_s, 0.01), summary=summary))
    return steps


def _derive_status(checker_ok: bool, iterations: int, has_chunks: bool) -> str:
    if not has_chunks:
        return "failed"
    if not checker_ok:
        return "failed"
    return "refined" if iterations > 0 else "verified"


def _cite_pass(state: AgentState) -> str:
    total = len(state.chunks)
    if state.check_result is None:
        return f"0/{total}"
    passed = max(total - len(state.check_result.issues), 0)
    return f"{passed}/{total}"


async def stream_answer(question: str) -> AsyncIterator[dict]:
    """Run retriever → analyzer → checker, yielding each new trace event live.
    After the graph terminates, persist an agent_run + implicit exploration and
    emit `run` and `exploration` events before `final` so the UI can link out.
    """
    started = time.perf_counter()
    state = AgentState(question=question)

    async with trace("chat", input={"question": question}) as root:
        while True:
            async with span("retriever", input={"question": state.question,
                                                "refined_query": state.refined_query}) as s:
                state = await run_retriever(state)
                try:
                    s.update(output={"chunk_count": len(state.chunks),
                                     "trials": sorted({c.trial_id for c in state.chunks})})
                except Exception:
                    log.debug("langfuse span update failed", exc_info=True)
            yield _sse("trace", _trace_payload(state.trace[-1]))

            async with span("analyzer", input={"chunks": len(state.chunks)}) as s:
                state = await run_analyzer(state)
                try:
                    s.update(output={"draft_len": len(state.draft_answer or ""),
                                     "sentence_count": len(state.sentences)})
                except Exception:
                    log.debug("langfuse span update failed", exc_info=True)
            yield _sse("trace", _trace_payload(state.trace[-1]))

            async with span("citation-checker",
                            input={"sentence_count": len(state.sentences)}) as s:
                state = await run_citation_checker(state)
                try:
                    s.update(output={
                        "ok": bool(state.check_result and state.check_result.ok),
                        "issues": state.check_result.issues if state.check_result else [],
                    })
                except Exception:
                    log.debug("langfuse span update failed", exc_info=True)
            yield _sse("trace", _trace_payload(state.trace[-1]))

            checker_ok = bool(state.check_result and state.check_result.ok)
            if checker_ok or state.iteration >= MAX_ITERATIONS:
                break

        latency_ms = int((time.perf_counter() - started) * 1000)
        citations = [
            Citation(chunk_id=c.chunk_id, trial_id=c.trial_id, section=c.section,
                     text=c.text, score=c.score)
            for c in state.chunks
        ]
        trials = sorted({c.trial_id for c in state.chunks})
        steps = _derive_steps(state.trace, checker_ok, state.iteration)
        status = _derive_status(checker_ok, state.iteration, has_chunks=bool(state.chunks))
        cite_pass = _cite_pass(state)

        run_id_str: str | None = None
        exp_id_str: str | None = None
        try:
            run = await create_run(
                source="chat",
                question=question,
                status=status,  # type: ignore[arg-type]
                iterations=state.iteration,
                cite_pass=cite_pass,
                chunk_count=len(state.chunks),
                latency_ms=latency_ms,
                trials=trials,
                steps=steps,
                answer=state.draft_answer,
                citations=citations,
            )
            run_id_str = str(run.id)
            yield _sse("run", {"agent_run_id": run_id_str, "short_id": run.short_id})

            exp = await create_from_run(
                question=question,
                answer=state.draft_answer,
                citations=citations,
                agent_run_id=run.id,
                verified=(status != "failed"),
            )
            exp_id_str = str(exp.id)
            yield _sse("exploration", {"exploration_id": exp_id_str, "short_id": exp.short_id})
        except Exception:
            # Persistence failure must NOT block the answer — chat should still work
            # if the DB is having a bad day. Log and continue to final.
            log.exception("failed to persist chat run/exploration")

        # Attach trace-level metadata + output so runs are filterable in Langfuse.
        try:
            root.update_trace(
                output={"answer": state.draft_answer, "check_ok": checker_ok},
                metadata={
                    "agent_run_id": run_id_str,
                    "exploration_id": exp_id_str,
                    "status": status,
                    "iterations": state.iteration,
                    "cite_pass": cite_pass,
                    "chunk_count": len(state.chunks),
                    "trials": trials,
                    "latency_ms": latency_ms,
                },
            )
        except Exception:
            log.debug("langfuse update_trace failed", exc_info=True)

        yield _sse("final", {
            "answer": state.draft_answer,
            "citations": [c.model_dump() for c in citations],
            "check_ok": bool(checker_ok),
            "issues": state.check_result.issues if state.check_result else [],
            "agent_run_id": run_id_str,
            "exploration_id": exp_id_str,
        })

    # Flush outside the trace context so pending events reach Langfuse promptly
    # even under low request volume. Cheap when tracing is disabled.
    await tracing_flush()
