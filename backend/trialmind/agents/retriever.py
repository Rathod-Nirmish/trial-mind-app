from trialmind.db import hybrid_search
from trialmind.ingestion.embed import embed_query
from trialmind.graph.state import AgentState, TraceEvent


async def run_retriever(state: AgentState) -> AgentState:
    query = state.refined_query or state.question
    emb = await embed_query(query)
    hits = await hybrid_search(query, emb, k=8)
    return state.model_copy(update={
        "chunks": hits,
        "trace": state.trace + [TraceEvent(
            agent="retriever",
            summary=f"retrieved {len(hits)} chunks for query: {query[:60]}",
            payload={"k": 8, "query": query, "top_score": hits[0].score if hits else 0.0},
        )],
    })
