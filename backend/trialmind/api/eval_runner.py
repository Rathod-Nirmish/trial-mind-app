"""Background runner for POST /runs/evals.

Runs the golden Q&A benchmark, optionally across both arms
(with_checker / without_checker), writes per-question rows to eval_results,
and stamps an aggregate onto eval_runs on completion.

Reuses the existing evals/arms.py + evals/judge.py so the CLI (`evals/run.py`)
and this API path share the same scoring logic.
"""
from __future__ import annotations

import logging
import time
import traceback
from pathlib import Path
from typing import Any
from uuid import UUID

import yaml

from evals.arms import answer_with_checker, answer_without_checker
from evals.judge import is_supported
from trialmind.db_evals import (
    EvalArm, compute_arm_metrics, finish_run, insert_result,
)

log = logging.getLogger(__name__)

QA_PATH = Path(__file__).resolve().parents[2] / "evals" / "golden_qa.yaml"

_ARMS = {
    "with": ("with_checker", answer_with_checker),
    "without": ("without_checker", answer_without_checker),
}


async def _judge_citations(sentences, id_map, chunks) -> tuple[int, int, list[dict[str, Any]]]:
    """Return (total_citations, unsupported_count, records) for one answer."""
    by_uuid = {c.chunk_id: c for c in chunks}
    records: list[dict[str, Any]] = []
    for sentence in sentences:
        for cid in sentence.cids:
            real_id = id_map.get(cid)
            chunk = by_uuid.get(real_id) if real_id else None
            if chunk is None:
                records.append({
                    "cid": cid, "sentence": sentence.text,
                    "supported": False,
                    "reason": "fabricated citation (cid not in id_map or chunks)",
                    "chunk_id": real_id, "trial_id": None,
                })
                continue
            supported, reason = await is_supported(sentence.text, chunk.text)
            records.append({
                "cid": cid, "sentence": sentence.text,
                "supported": bool(supported), "reason": reason,
                "chunk_id": chunk.chunk_id, "trial_id": chunk.trial_id,
            })
    unsupported = sum(1 for r in records if not r["supported"])
    return len(records), unsupported, records


async def _run_one_arm(question: str, arm_fn) -> dict[str, Any]:
    t0 = time.perf_counter()
    answer, sentences, id_map, chunks = await arm_fn(question)
    total, unsupported, records = await _judge_citations(sentences, id_map, chunks)
    latency_ms = int((time.perf_counter() - t0) * 1000)
    return {
        "answer": answer,
        "citations": records,
        "total_citations": total,
        "unsupported_citations": unsupported,
        "chunk_count": len(chunks),
        "latency_ms": latency_ms,
        "passed": unsupported == 0,
    }


def _load_questions() -> list[dict[str, str]]:
    return yaml.safe_load(QA_PATH.read_text(encoding="utf-8"))


async def run_eval_job(run_id: UUID, arm: EvalArm) -> None:
    """Iterate questions × requested arm(s), persist per-question results,
    compute aggregate, mark finished. Never raises — records failure on the run.
    """
    arms_to_run = ["with", "without"] if arm == "both" else [arm]
    per_arm_records: dict[str, list[dict[str, Any]]] = {a: [] for a in arms_to_run}

    try:
        questions = _load_questions()
        log.info("eval %s: %d questions × %d arm(s)",
                 run_id, len(questions), len(arms_to_run))

        for q in questions:
            for a in arms_to_run:
                arm_key, arm_fn = _ARMS[a]
                try:
                    result = await _run_one_arm(q["question"], arm_fn)
                except Exception as exc:
                    log.exception("eval question %s arm %s failed", q["id"], a)
                    result = {
                        "answer": None, "citations": [], "total_citations": 0,
                        "unsupported_citations": 0, "chunk_count": 0,
                        "latency_ms": 0, "passed": False,
                        "_error": f"{type(exc).__name__}: {exc}",
                    }
                await insert_result(
                    run_id=run_id,
                    question_id=q["id"],
                    arm=arm_key,
                    passed=result["passed"],
                    latency_ms=result["latency_ms"],
                    answer=result["answer"],
                    citations=result["citations"],
                )
                per_arm_records[a].append(result)

        aggregate = _build_aggregate(per_arm_records)
        await finish_run(run_id, status="succeeded", aggregate=aggregate)
        log.info("eval %s: done", run_id)
    except Exception as exc:
        log.exception("eval runner crashed")
        await finish_run(
            run_id,
            status="failed",
            aggregate={"error": str(exc), "traceback": traceback.format_exc()},
        )


def _build_aggregate(per_arm: dict[str, list[dict[str, Any]]]) -> dict[str, Any]:
    """Compose the aggregate dict stored on eval_runs.aggregate.

    Shape matches what the /runs/evals/aggregate endpoint reads back.
    """
    arms = {a: compute_arm_metrics(recs) for a, recs in per_arm.items()}

    # Delta = relative reduction in halluc rate from without → with, in percent.
    delta_pct = 0.0
    with_metrics = arms.get("with")
    without_metrics = arms.get("without")
    if with_metrics and without_metrics and without_metrics["halluc_pct"] > 0:
        delta_pct = round(
            (1 - with_metrics["halluc_pct"] / without_metrics["halluc_pct"]) * 100, 1
        )
    elif with_metrics and without_metrics and without_metrics["halluc_pct"] == 0:
        delta_pct = 0.0  # can't improve on perfect

    return {
        "arms": arms,
        "delta_pct": delta_pct,
    }
