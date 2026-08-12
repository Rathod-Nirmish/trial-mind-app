from __future__ import annotations
import asyncio
import hashlib
import json
from typing import Any

import httpx
from pydantic import BaseModel

BASE = "https://clinicaltrials.gov/api/v2/studies"


class TrialNotFound(Exception):
    pass


class TrialDoc(BaseModel):
    nct_id: str
    title: str
    phase: str | None = None          # 'I' | 'II' | 'III' | 'IV' | None
    status: str | None = None         # 'Recruiting' | 'Completed' | ...
    condition: str | None = None
    sections: dict[str, str]
    content_hash: str                 # sha256 over the raw payload; drives dedup
    raw: dict[str, Any] = {}          # original NCT payload, stored on trials.raw


def _extract_phase(proto: dict) -> str | None:
    phases = proto.get("designModule", {}).get("phases") or []
    # NCT returns like ["PHASE1", "PHASE2"] — take the highest as canonical.
    order = {"PHASE1": "I", "PHASE2": "II", "PHASE3": "III", "PHASE4": "IV"}
    ranked = [order[p] for p in phases if p in order]
    if not ranked:
        return None
    return sorted(ranked, key=["I", "II", "III", "IV"].index)[-1]


def _extract_status(proto: dict) -> str | None:
    raw = proto.get("statusModule", {}).get("overallStatus")
    if not raw:
        return None
    # NCT statuses are UPPER_SNAKE; Title-Case what the frontend expects.
    mapping = {
        "COMPLETED": "Completed",
        "RECRUITING": "Recruiting",
        "TERMINATED": "Terminated",
        "WITHDRAWN": "Withdrawn",
        "ACTIVE_NOT_RECRUITING": "Active",
        "ACTIVE": "Active",
    }
    return mapping.get(raw, raw.title().replace("_", " "))


def _extract_condition(proto: dict) -> str | None:
    conds = proto.get("conditionsModule", {}).get("conditions") or []
    return conds[0] if conds else None


def _extract_sections(proto: dict, payload: dict) -> dict[str, str]:
    sections: dict[str, str] = {}

    desc = proto.get("descriptionModule", {})
    if summary := desc.get("briefSummary"):
        sections["summary"] = summary
    if detailed := desc.get("detailedDescription"):
        sections["description"] = detailed

    elig = proto.get("eligibilityModule", {}).get("eligibilityCriteria")
    if elig:
        sections["eligibility"] = elig

    outcomes = proto.get("outcomesModule", {})
    primary = outcomes.get("primaryOutcomes") or []
    if primary:
        sections["outcomes"] = "\n\n".join(
            f"{o.get('measure', '')}: {o.get('description', '')}" for o in primary
        )

    ae = payload.get("resultsSection", {}).get("adverseEventsModule", {})
    ae_groups = ae.get("eventGroups") or []
    if ae_groups:
        sections["adverse_events"] = "\n\n".join(
            g.get("description", "") or g.get("title", "") for g in ae_groups
        )

    return sections


def _hash_payload(payload: dict) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


async def fetch_trial(nct_id: str) -> TrialDoc:
    url = f"{BASE}/{nct_id}?format=json"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url)
    if r.status_code == 404:
        raise TrialNotFound(nct_id)
    r.raise_for_status()
    payload = r.json()
    proto = payload.get("protocolSection", {})
    id_mod = proto.get("identificationModule", {})
    title = id_mod.get("briefTitle") or id_mod.get("officialTitle") or nct_id
    return TrialDoc(
        nct_id=nct_id,
        title=title,
        phase=_extract_phase(proto),
        status=_extract_status(proto),
        condition=_extract_condition(proto),
        sections=_extract_sections(proto, payload),
        content_hash=_hash_payload(payload),
        raw=payload,
    )


async def fetch_trials(nct_ids: list[str]) -> list[TrialDoc]:
    return await asyncio.gather(*(fetch_trial(x) for x in nct_ids))
