import asyncio, sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import psycopg
from trialmind.config import get_settings
from trialmind.db import hybrid_search, _vec_literal
from trialmind.ingestion.embed import embed_query

Q = "What were the eligibility criteria for the BNT162b2 vaccine trial?"


async def probe():
    emb = await embed_query(Q)
    vec_lit = _vec_literal(emb)

    c = psycopg.connect(get_settings().database_url)
    cur = c.cursor()

    # Raw vector search
    cur.execute(
        "SELECT trial_id, section, LEFT(text,60), (embedding <=> %s::vector) AS dist "
        "FROM chunks ORDER BY embedding <=> %s::vector LIMIT 5",
        (vec_lit, vec_lit),
    )
    print("--- pure vector top 5 ---")
    for r in cur.fetchall():
        print(" ", r)

    # Full-text alone
    cur.execute(
        "SELECT COUNT(*) FROM chunks WHERE tsv @@ plainto_tsquery('english', %s)", (Q,)
    )
    print("full-text hits for question:", cur.fetchone())

    c.close()

    hits = await hybrid_search(Q, emb, k=8)
    print(f"hybrid_search returned {len(hits)} hits")


asyncio.run(probe())
