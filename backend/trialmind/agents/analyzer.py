import json
from trialmind.llm_client import complete
from trialmind.graph.state import AgentState, Sentence, TraceEvent


SYSTEM = (
    "You are a clinical research analyst. Answer strictly from the provided chunks.\n\n"
    "You MUST emit your answer as a JSON object with a single key `sentences`, "
    "an array of {text, cids} pairs. Each sentence contains ONE factual claim, "
    "and the cids attached to that sentence must be exactly the chunks that "
    "jointly support that specific claim.\n\n"
    "Rules:\n"
    "1. One factual claim per sentence. If you have two facts, use two sentences.\n"
    "2. Do NOT bundle a long list of items into one sentence with one citation. "
    "If a chunk covers 6 items and another chunk covers 7 items, that's TWO "
    "sentences, each citing one chunk.\n"
    "3. Inside each sentence's `text`, include the citation markers inline "
    "like `[c1]` or `[c1][c3]` so the rendered answer shows citations to the reader.\n"
    "4. If chunks are insufficient to answer, emit one sentence with the "
    "explanation and empty cids: `{\"text\": \"The provided chunks are insufficient to answer.\", \"cids\": []}`.\n"
    "5. Do not invent facts. Every claim must be traceable to a cited chunk.\n\n"
    "Bad example (do NOT do this):\n"
    '  {"sentences": [{"text": "The trial investigated A, B, C, D, E, F, G, H, I, J [c1][c2][c3]", "cids": ["c1", "c2", "c3"]}]}\n\n'
    "Good example:\n"
    '  {"sentences": [\n'
    '    {"text": "The trial investigated A, B, C, D, and E [c1].", "cids": ["c1"]},\n'
    '    {"text": "It also investigated F, G, H, I, and J [c2].", "cids": ["c2"]}\n'
    '  ]}'
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


def _parse_sentences(raw: str) -> list[Sentence]:
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if not isinstance(parsed, dict):
            return []
        items = parsed.get("sentences", [])
        if not isinstance(items, list):
            return []
        out: list[Sentence] = []
        for item in items:
            if not isinstance(item, dict):
                continue
            text = str(item.get("text", "")).strip()
            cids_raw = item.get("cids", []) or []
            cids = [str(c) for c in cids_raw if isinstance(c, (str, int))]
            if text:
                out.append(Sentence(text=text, cids=cids))
        return out
    except json.JSONDecodeError:
        return []


async def run_analyzer(state: AgentState) -> AgentState:
    formatted, id_map = _format_chunks(state.chunks)
    prompt = (
        f"Question: {state.question}\n\n"
        f"Chunks:\n{formatted}\n\n"
        'Respond ONLY as JSON matching {"sentences": [{"text": string, "cids": string[]}]}. '
        "Use the short chunk IDs shown in brackets above (e.g. c1, c2)."
    )
    raw = await complete(prompt, model="gemini-flash-lite-latest", system=SYSTEM,
                         json_schema={"type": "object"})
    sentences = _parse_sentences(raw)
    # Fallback: if parsing failed, put the raw text in a single uncited sentence.
    if not sentences:
        sentences = [Sentence(text=raw.strip(), cids=[])]

    answer = " ".join(s.text for s in sentences)
    total_cids = sum(len(s.cids) for s in sentences)
    return state.model_copy(update={
        "draft_answer": answer,
        "sentences": sentences,
        "citation_id_map": id_map,
        "trace": state.trace + [TraceEvent(
            agent="analyzer",
            summary=f"drafted {len(sentences)} sentence(s), {total_cids} citation(s), {len(answer)} chars",
            payload={"sentence_count": len(sentences), "citation_count": total_cids},
        )],
    })
