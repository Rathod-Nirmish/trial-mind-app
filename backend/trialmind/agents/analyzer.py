import json
from trialmind.llm_client import complete
from trialmind.graph.state import AgentState, TraceEvent


SYSTEM = (
    "You are a clinical research analyst. Answer strictly from the provided chunks. "
    "Cite chunks inline using bracket notation. Each citation MUST be its own "
    "bracket — write [c1][c7], NEVER [c1, c7] or [c1,c7]. "
    "Do not invent facts. If chunks are insufficient, say so explicitly."
)


def _format_chunks(chunks) -> tuple[str, dict[str, str]]:
    if not chunks:
        return "(no chunks retrieved)", {}
    id_map: dict[str, str] = {}
    lines: list[str] = []
    for i, h in enumerate(chunks, 1):
        short = f"c{i}"
        id_map[short] = h.chunk_id
        lines.append(f"[{short}] (trial={h.trial_id}, section={h.section})\n{h.text}")
    return "\n\n".join(lines), id_map


async def run_analyzer(state: AgentState) -> AgentState:
    formatted, id_map = _format_chunks(state.chunks)
    prompt = (
        f"Question: {state.question}\n\n"
        f"Chunks:\n{formatted}\n\n"
        'Respond ONLY as JSON: {"answer": string, "cited_chunk_ids": string[]}. '
        "Use the short chunk IDs shown in brackets above (e.g. c1, c2)."
    )
    raw = await complete(prompt, model="gemini-flash-lite-latest", system=SYSTEM,
                         json_schema={"type": "object"})
    try:
        parsed = json.loads(raw)
        answer = parsed.get("answer", "").strip()
        cited = parsed.get("cited_chunk_ids", [])
    except json.JSONDecodeError:
        answer = raw.strip()
        cited = []
    return state.model_copy(update={
        "draft_answer": answer,
        "citation_id_map": id_map,
        "trace": state.trace + [TraceEvent(
            agent="analyzer",
            summary=f"drafted answer ({len(answer)} chars, {len(cited)} citations)",
            payload={"cited_chunk_ids": cited},
        )],
    })
