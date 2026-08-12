import asyncio, sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import psycopg
from trialmind.config import get_settings
from trialmind.ingestion.fetch import fetch_trial


def show_db():
    c = psycopg.connect(get_settings().database_url)
    cur = c.cursor()
    cur.execute("SELECT text FROM chunks WHERE trial_id='NCT04368728' AND text LIKE '%naive%' OR text LIKE '%na%ve%' LIMIT 2")
    for (t,) in cur.fetchall():
        # find 'na' followed by anything then 've' to catch both cases
        i = t.lower().find("na")
        if i >= 0:
            frag = t[i:i+15]
            print("DB fragment repr:", repr(frag))
            print("DB fragment bytes:", frag.encode("utf-8"))
    c.close()


async def show_fetch():
    doc = await fetch_trial("NCT04368728")
    txt = doc.sections.get("summary", "")
    i = txt.lower().find("na")
    if i >= 0:
        frag = txt[i:i+15]
        print("HTTP fragment repr:", repr(frag))
        print("HTTP fragment bytes:", frag.encode("utf-8"))
    # look for micro sign or >= too
    for needle in ["µ", "≥", "é"]:
        if needle in txt:
            j = txt.find(needle)
            print(f"HTTP has {needle!r} at pos {j}: {txt[max(0,j-10):j+10]!r}")


show_db()
asyncio.run(show_fetch())
