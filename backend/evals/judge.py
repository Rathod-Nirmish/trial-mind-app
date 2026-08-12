import json
from trialmind.llm_client import complete

# Groq's Llama 3.3 70B: different vendor and architecture from the analyzer's
# Gemini, so no shared-bias risk. Free tier is 6000 RPD / 30 RPM — comfortably
# fits a 100-call eval.
JUDGE_MODEL = "llama-3.3-70b-versatile"

JUDGE_SYSTEM = (
    "You are a strict scientific verifier. Given a claim extracted from an "
    "answer and a source passage, decide whether the passage clearly supports "
    "the claim. Reply ONLY as JSON: {\"supported\": bool, \"reason\": string}. "
    "supported=true only if a reader could verify the claim from the passage "
    "alone. Partial or tangential support counts as false."
)


async def is_supported(claim: str, passage: str) -> tuple[bool, str]:
    prompt = f"Claim: {claim}\n\nPassage:\n{passage}"
    raw = await complete(
        prompt,
        model=JUDGE_MODEL,
        system=JUDGE_SYSTEM,
        json_schema={"type": "object"},
    )
    try:
        parsed = json.loads(raw)
        # Some models wrap the object in a list — unwrap.
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        if not isinstance(parsed, dict):
            return False, f"judge returned non-object: {type(parsed).__name__}"
        return bool(parsed.get("supported")), str(parsed.get("reason", ""))
    except json.JSONDecodeError:
        return False, "unparseable judge response"
