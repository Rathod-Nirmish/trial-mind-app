"""Background runner for /corpus/ingest/nct.

Wraps ingestion.cli.ingest_nct with per-stage event writes to ingest_jobs.
Designed for FastAPI BackgroundTasks; one runner call handles the whole batch.
"""
from __future__ import annotations

import logging
import traceback
from datetime import datetime, timezone
from uuid import UUID

from trialmind.db_jobs import JobEvent, append_event, mark_finished
from trialmind.ingestion.cli import ingest_nct
from trialmind.ingestion.fetch import TrialNotFound

log = logging.getLogger(__name__)


def _now() -> datetime:
    return datetime.now(timezone.utc)


async def _emit(job_id: UUID, agent: str, summary: str, **payload) -> None:
    await append_event(
        job_id,
        JobEvent(at=_now(), agent=agent, summary=summary, payload=payload),
    )


async def run_ingest_job(job_id: UUID, nct_ids: list[str]) -> None:
    """Iterate NCTs, emitting progress. Never raises — records failure on the job."""
    ok, skipped, failed = 0, 0, 0
    try:
        await _emit(job_id, "runner", f"Starting ingest of {len(nct_ids)} trial(s)",
                    nct_ids=nct_ids)
        for nct in nct_ids:
            try:
                await _emit(job_id, "fetcher", f"Fetching {nct} from ClinicalTrials.gov")
                result = await ingest_nct(nct)
                if result.unchanged:
                    skipped += 1
                    await _emit(
                        job_id, "runner",
                        f"{nct}: unchanged (v{result.version}) — skipped embedding",
                        nct_id=nct, version=result.version, chunks=0, skipped=True,
                    )
                else:
                    ok += 1
                    action = "updated" if result.updated else "new"
                    await _emit(
                        job_id, "runner",
                        f"{nct}: {action} · {result.chunks} chunks indexed (v{result.version})",
                        nct_id=nct, version=result.version, chunks=result.chunks,
                        action=action,
                    )
            except TrialNotFound:
                failed += 1
                await _emit(job_id, "fetcher", f"{nct}: not found on ClinicalTrials.gov",
                            nct_id=nct, error="not_found")
            except Exception as exc:
                failed += 1
                log.exception("ingest failed for %s", nct)
                await _emit(
                    job_id, "runner",
                    f"{nct}: FAILED ({type(exc).__name__}: {exc})",
                    nct_id=nct, error=str(exc),
                )

        status = "succeeded" if failed == 0 else "failed"
        await _emit(job_id, "runner",
                    f"Done · {ok} indexed · {skipped} unchanged · {failed} failed")
        await mark_finished(
            job_id,
            status=status,
            error=None if failed == 0 else f"{failed} of {len(nct_ids)} trial(s) failed",
        )
    except Exception as exc:
        log.exception("runner crashed")
        await _emit(job_id, "runner", f"Runner crashed: {type(exc).__name__}: {exc}",
                    traceback=traceback.format_exc())
        await mark_finished(job_id, status="failed", error=str(exc))
