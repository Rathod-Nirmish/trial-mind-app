from __future__ import annotations
import argparse
import asyncio
import sys
from dataclasses import dataclass

from trialmind.db import ChunkRow, upsert_chunks
from trialmind.db_trials import upsert_trial
from trialmind.ingestion.chunk import chunk_text
from trialmind.ingestion.embed import embed_texts
from trialmind.ingestion.fetch import fetch_trial
from trialmind.ingestion.pdf import parse_pdf


@dataclass
class IngestResult:
    nct_id: str
    chunks: int
    inserted: bool
    updated: bool
    unchanged: bool           # True if content_hash matched → skipped embedding
    version: int


async def ingest_nct(nct_id: str) -> IngestResult:
    """Fetch, dedup by content-hash, chunk+embed if new/changed, upsert everything.
    Idempotent: repeat calls for an unchanged trial return unchanged=True and skip
    the expensive embedding step.
    """
    doc = await fetch_trial(nct_id)
    result = await upsert_trial(
        nct_id=doc.nct_id,
        title=doc.title,
        phase=doc.phase,
        status=doc.status,
        condition=doc.condition,
        source="nct",
        content_hash=doc.content_hash,
        raw=doc.raw,
    )
    if result.unchanged:
        return IngestResult(
            nct_id=doc.nct_id, chunks=0,
            inserted=False, updated=False, unchanged=True, version=result.version,
        )

    rows: list[ChunkRow] = []
    for section, text in doc.sections.items():
        chunks = chunk_text(text)
        if not chunks:
            continue
        embeddings = await embed_texts(chunks)
        for c, e in zip(chunks, embeddings):
            rows.append(
                ChunkRow(trial_id=doc.nct_id, section=section, text=c, embedding=e)
            )
    await upsert_chunks(rows)
    return IngestResult(
        nct_id=doc.nct_id, chunks=len(rows),
        inserted=result.inserted, updated=result.updated, unchanged=False, version=result.version,
    )


async def ingest_pdf(path: str, trial_id: str) -> int:
    text = parse_pdf(path)
    chunks = chunk_text(text)
    if not chunks:
        return 0
    embeddings = await embed_texts(chunks)
    rows = [
        ChunkRow(trial_id=trial_id, section="pdf", text=c, embedding=e)
        for c, e in zip(chunks, embeddings)
    ]
    await upsert_chunks(rows)
    return len(rows)


async def _ingest_one(nct: str) -> int:
    try:
        r = await ingest_nct(nct)
        tag = "unchanged" if r.unchanged else ("updated" if r.updated else "new")
        print(f"  {nct}: {r.chunks} chunks ({tag}, v{r.version})", flush=True)
        return r.chunks
    except Exception as e:
        print(f"  {nct}: FAILED ({type(e).__name__}: {e})", flush=True)
        return 0


async def main_async(args: argparse.Namespace) -> None:
    total = 0
    if args.nct:
        results = await asyncio.gather(*(_ingest_one(x) for x in args.nct))
        total += sum(results)
    if args.pdf:
        n = await ingest_pdf(args.pdf, args.trial_id)
        print(f"PDF {args.pdf} as {args.trial_id}: {n} chunks")
        total += n
    print(f"Total: {total} chunks")


def main() -> None:
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    p = argparse.ArgumentParser()
    p.add_argument("--nct", nargs="*", default=[])
    p.add_argument("--pdf")
    p.add_argument("--trial-id")
    args = p.parse_args()
    if args.pdf and not args.trial_id:
        p.error("--pdf requires --trial-id")
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
