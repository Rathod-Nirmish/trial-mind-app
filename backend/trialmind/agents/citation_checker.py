import json
import re
from trialmind.llm_client import complete
from trialmind.graph.state import AgentState, CheckResult, TraceEvent

# Matches a bracketed citation group like [c1], [c1, c7], or [c1,c2,c3].
_CITATION_GROUP_RE = re.compile(r"\[\s*(c\d+(?:\s*,\s*c\d+)*)\s*\]")
_CID_RE = re.compile(r"c\d+")


def extract_citations(text: str) -> list[str]:
    seen: list[str] = []
    for group_match in _CITATION_GROUP_RE.finditer(text):
        for cid in _CID_RE.findall(group_match.group(1)):
            if cid not in seen:
                seen.append(cid)
    return seen


ENTAIL_SYSTEM = (
    "You are a strict verifier. Given a claim and a source passage, "
    'reply JSON {"entails": bool, "reason": string}. entails=true only if '
    "the passage clearly supports the claim."
)

REFINE_SYSTEM = (
    "You are a query rewriter. Given the original question and a list of "
    "issues with the previous answer attempt, produce a single improved "
    "search query more likely to retrieve supporting passages. Reply with "
    "just the query — no preamble, no quotes."
)


def _sentence_around_citation(text: str, cid: str) -> str:
    idx = text.find(f"[{cid}]")
    if idx == -1:
        # cid may be inside a comma-grouped bracket like [c1, c7]
        for m in _CITATION_GROUP_RE.finditer(text):
            if cid in _CID_RE.findall(m.group(1)):
                idx = m.start()
                break
    if idx == -1:
        return text
    start = max(
        text.rfind(". ", 0, idx),
        text.rfind("! ", 0, idx),
        text.rfind("? ", 0, idx),
        -1,
    ) + 1
    end_candidates = [text.find(s, idx) for s in (". ", "! ", "? ")]
    end_candidates = [e for e in end_candidates if e != -1]
    end = min(end_candidates) + 1 if end_candidates else len(text)
    return text[start:end].strip()


async def _check_entailment(claim: str, chunk_text: str) -> tuple[bool, str]:
    prompt = f"Claim: {claim}\n\nPassage:\n{chunk_text}"
    raw = await complete(prompt, model="gemini-flash-lite-latest", system=ENTAIL_SYSTEM,
                         json_schema={"type": "object"})
    try:
        parsed = json.loads(raw)
        return bool(parsed.get("entails")), str(parsed.get("reason", ""))
    except json.JSONDecodeError:
        return False, "unparseable verifier response"


async def _refine_query(question: str, issues: list[str]) -> str:
    prompt = f"Question: {question}\n\nIssues:\n" + "\n".join(f"- {i}" for i in issues)
    out = await complete(prompt, model="gemini-flash-lite-latest", system=REFINE_SYSTEM)
    return out.strip() or question


async def run_citation_checker(state: AgentState) -> AgentState:
    id_map = state.citation_id_map
    known = {c.chunk_id: c for c in state.chunks}
    issues: list[str] = []

    # Fallback for cases where the analyzer produced no structured output.
    if not state.sentences:
        return state.model_copy(update={
            "check_result": CheckResult(ok=True, issues=[]),
            "iteration": state.iteration + 1,
            "trace": state.trace + [TraceEvent(
                agent="citation_checker",
                summary="skipped: no structured sentences",
                payload={},
            )],
        })

    for sentence in state.sentences:
        for cid in sentence.cids:
            real_id = id_map.get(cid)
            if real_id is None or real_id not in known:
                issues.append(f"cited unknown chunk id: {cid}")
                continue
            entails, reason = await _check_entailment(sentence.text, known[real_id].text)
            if not entails:
                issues.append(f"chunk {cid} does not entail claim: {reason}")

    result = CheckResult(ok=len(issues) == 0, issues=issues)
    update: dict = {
        "check_result": result,
        "iteration": state.iteration + 1,
        "trace": state.trace + [TraceEvent(
            agent="citation_checker",
            summary=f"ok={result.ok}, issues={len(issues)}, iter={state.iteration + 1}",
            payload={"issues": issues},
        )],
    }
    if not result.ok:
        update["refined_query"] = await _refine_query(state.question, issues)
    return state.model_copy(update=update)
