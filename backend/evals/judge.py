import json
from trialmind.llm_client import complete

# Note: spec said 2.5-pro, but free-tier quota for that model is 0 on this key.
# 2.5-flash is a different tier than the analyzer's flash-lite, so shared-bias
# risk remains low. Upgrade to 2.5-pro later if paid billing is enabled.
JUDGE_MODEL = "gemini-2.5-flash"

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
        return bool(parsed.get("supported")), str(parsed.get("reason", ""))
    except json.JSONDecodeError:
        return False, "unparseable judge response"
