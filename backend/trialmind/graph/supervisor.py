from langgraph.graph import StateGraph, END
from trialmind.graph.state import AgentState
from trialmind.agents.retriever import run_retriever
from trialmind.agents.analyzer import run_analyzer
from trialmind.agents.citation_checker import run_citation_checker

MAX_ITERATIONS = 2


async def _retriever_node(state: AgentState) -> AgentState:
    return await run_retriever(state)


async def _analyzer_node(state: AgentState) -> AgentState:
    return await run_analyzer(state)


async def _checker_node(state: AgentState) -> AgentState:
    return await run_citation_checker(state)


def _route_after_checker(state: AgentState) -> str:
    if state.check_result and state.check_result.ok:
        return END
    if state.iteration >= MAX_ITERATIONS:
        return END
    return "retriever"


def build_graph():
    g = StateGraph(AgentState)
    g.add_node("retriever", _retriever_node)
    g.add_node("analyzer", _analyzer_node)
    g.add_node("checker", _checker_node)
    g.set_entry_point("retriever")
    g.add_edge("retriever", "analyzer")
    g.add_edge("analyzer", "checker")
    g.add_conditional_edges("checker", _route_after_checker,
                            {"retriever": "retriever", END: END})
    return g.compile().with_config({"recursion_limit": 10})


_app = None


def _get_app():
    global _app
    if _app is None:
        _app = build_graph()
    return _app


async def run(question: str) -> AgentState:
    initial = AgentState(question=question)
    result = await _get_app().ainvoke(initial)
    return AgentState.model_validate(result) if isinstance(result, dict) else result
