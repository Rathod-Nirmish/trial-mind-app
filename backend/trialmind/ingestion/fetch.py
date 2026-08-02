from __future__ import annotations
import asyncio
import httpx
from pydantic import BaseModel

BASE = "https://clinicaltrials.gov/api/v2/studies"


class TrialNotFound(Exception):
    pass


class TrialDoc(BaseModel):
    nct_id: str
    title: str
    sections: dict[str, str]


def _extract_sections(payload: dict) -> tuple[str, dict[str, str]]:
    proto = payload.get("protocolSection", {})
    id_mod = proto.get("identificationModule", {})
    title = id_mod.get("briefTitle") or id_mod.get("officialTitle") or ""

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

    return title, sections


async def fetch_trial(nct_id: str) -> TrialDoc:
    url = f"{BASE}/{nct_id}?format=json"
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.get(url)
    if r.status_code == 404:
        raise TrialNotFound(nct_id)
    r.raise_for_status()
    payload = r.json()
    title, sections = _extract_sections(payload)
    return TrialDoc(nct_id=nct_id, title=title, sections=sections)


async def fetch_trials(nct_ids: list[str]) -> list[TrialDoc]:
    return await asyncio.gather(*(fetch_trial(x) for x in nct_ids))
