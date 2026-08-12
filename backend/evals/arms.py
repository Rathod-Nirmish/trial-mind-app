from __future__ import annotations
from trialmind.agents.analyzer import run_analyzer
from trialmind.agents.citation_checker import run_citation_checker
from trialmind.agents.retriever import run_retriever
from trialmind.db import SearchHit
from trialmind.graph.state import AgentState, Sentence

MAX_ITERATIONS = 2

# Returns (draft_answer, sentences, citation_id_map, chunks).
ArmResult = tuple[str, list[Sentence], dict[str, str], list[SearchHit]]


async def answer_without_checker(question: str) -> ArmResult:
    state = AgentState(question=question)
    state = await run_retriever(state)
    state = await run_analyzer(state)
    return state.draft_answer, state.sentences, state.citation_id_map, state.chunks


async def answer_with_checker(question: str) -> ArmResult:
    state = AgentState(question=question)
    while True:
        state = await run_retriever(state)
        state = await run_analyzer(state)
        state = await run_citation_checker(state)
        ok = state.check_result and state.check_result.ok
        if ok or state.iteration >= MAX_ITERATIONS:
            break
    return state.draft_answer, state.sentences, state.citation_id_map, state.chunks
