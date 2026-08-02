from __future__ import annotations
import asyncio
import json
import sys
from datetime import date
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import yaml
from trialmind.agents.citation_checker import (
    _sentence_around_citation,
    extract_citations,
)
from evals.arms import answer_with_checker, answer_without_checker
from evals.judge import is_supported

ARMS = {
    "with_checker": answer_with_checker,
    "without_checker": answer_without_checker,
}

REPO_ROOT = Path(__file__).resolve().parents[2]
QA_PATH = Path(__file__).resolve().parent / "golden_qa.yaml"
OUT_DIR = REPO_ROOT / "docs" / "eval"


async def _judge_answer(answer: str, id_map: dict[str, str], chunks: list) -> list[dict]:
    """For each citation in `answer`, ask the judge whether the cited chunk supports the claim."""
    by_uuid = {c.chunk_id: c for c in chunks}
    records: list[dict] = []
    for cid in extract_citations(answer):
        real_id = id_map.get(cid)
        chunk = by_uuid.get(real_id) if real_id else None
        if chunk is None:
            records.append({
                "cid": cid,
                "supported": False,
                "reason": "fabricated citation (cid not in id_map or chunks)",
                "chunk_id": real_id,
                "trial_id": None,
            })
            continue
        claim = _sentence_around_citation(answer, cid)
        supported, reason = await is_supported(claim, chunk.text)
        records.append({
            "cid": cid,
            "supported": supported,
            "reason": reason,
            "chunk_id": chunk.chunk_id,
            "trial_id": chunk.trial_id,
        })
    return records


async def _run_one(q_id: str, question: str, arm_name: str, arm_fn) -> dict:
    print(f"  [{arm_name}] {q_id} …", flush=True)
    answer, id_map, chunks = await arm_fn(question)
    citation_records = await _judge_answer(answer, id_map, chunks)
    unsupported = sum(1 for r in citation_records if not r["supported"])
    total = len(citation_records)
    return {
        "q_id": q_id,
        "arm": arm_name,
        "question": question,
        "answer": answer,
        "citations": citation_records,
        "total_citations": total,
        "unsupported_citations": unsupported,
    }


def _aggregate(results: list[dict], arm: str) -> dict:
    arm_results = [r for r in results if r["arm"] == arm]
    total_citations = sum(r["total_citations"] for r in arm_results)
    unsupported = sum(r["unsupported_citations"] for r in arm_results)
    answers_with_bad = sum(1 for r in arm_results if r["unsupported_citations"] > 0)
    rate = (unsupported / total_citations) if total_citations else 0.0
    return {
        "arm": arm,
        "total_answers": len(arm_results),
        "total_citations": total_citations,
        "unsupported_citations": unsupported,
        "hallucinated_citation_rate": rate,
        "unsupported_answers": answers_with_bad,
    }


def _write_reports(results: list[dict], summaries: dict[str, dict]) -> tuple[Path, Path]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()

    json_path = OUT_DIR / f"{today}-results.json"
    json_path.write_text(json.dumps({"summaries": summaries, "results": results}, indent=2))

    with_ = summaries["with_checker"]
    without = summaries["without_checker"]
    reduction = 0.0
    if without["hallucinated_citation_rate"] > 0:
        reduction = 1 - (with_["hallucinated_citation_rate"] / without["hallucinated_citation_rate"])

    md = [
        f"# TrialMind Golden Q&A Eval — {today}",
        "",
        "## Headline",
        "",
        f"- **Without checker:** {without['hallucinated_citation_rate']:.1%} hallucinated-citation rate "
        f"({without['unsupported_citations']}/{without['total_citations']} citations)",
        f"- **With checker:** {with_['hallucinated_citation_rate']:.1%} hallucinated-citation rate "
        f"({with_['unsupported_citations']}/{with_['total_citations']} citations)",
        f"- **Relative reduction:** {reduction:.0%}",
        "",
        "## Per-arm summary",
        "",
        "| Arm | Answers | Citations | Unsupported | Rate | Answers with ≥1 unsupported |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for arm in ("without_checker", "with_checker"):
        s = summaries[arm]
        md.append(
            f"| {arm} | {s['total_answers']} | {s['total_citations']} | "
            f"{s['unsupported_citations']} | {s['hallucinated_citation_rate']:.1%} | "
            f"{s['unsupported_answers']} |"
        )
    md += ["", "## Per-question breakdown", ""]
    md.append("| Question | Arm | Citations | Unsupported |")
    md.append("|---|---|---:|---:|")
    for r in results:
        md.append(
            f"| {r['q_id']} | {r['arm']} | {r['total_citations']} | {r['unsupported_citations']} |"
        )
    md.append("")

    md_path = OUT_DIR / f"{today}-results.md"
    md_path.write_text("\n".join(md), encoding="utf-8")
    return json_path, md_path


async def main() -> None:
    questions = yaml.safe_load(QA_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(questions)} questions from {QA_PATH.name}", flush=True)

    results: list[dict] = []
    try:
        for q in questions:
            for arm_name, arm_fn in ARMS.items():
                r = await _run_one(q["id"], q["question"], arm_name, arm_fn)
                results.append(r)
    except Exception as e:  # noqa: BLE001 — always write partial results
        import traceback
        print(f"\n*** ABORTED: {type(e).__name__}: {str(e)[:200]}")
        traceback.print_exc()
        print(f"*** {len(results)} arm-runs completed before abort; writing partial report")

    if not results:
        raise RuntimeError("no results collected; nothing to write")

    summaries = {arm: _aggregate(results, arm) for arm in ARMS}
    json_path, md_path = _write_reports(results, summaries)

    print("")
    print(f"JSON: {json_path}")
    print(f"MD:   {md_path}")
    print("")
    with_ = summaries["with_checker"]
    without = summaries["without_checker"]
    print(f"without_checker: {without['hallucinated_citation_rate']:.1%} "
          f"({without['unsupported_citations']}/{without['total_citations']})")
    print(f"with_checker:    {with_['hallucinated_citation_rate']:.1%} "
          f"({with_['unsupported_citations']}/{with_['total_citations']})")


if __name__ == "__main__":
    asyncio.run(main())
