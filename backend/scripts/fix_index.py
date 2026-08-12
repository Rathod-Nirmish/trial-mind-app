import psycopg
from trialmind.config import get_settings

c = psycopg.connect(get_settings().database_url)
c.execute("DROP INDEX IF EXISTS chunks_embedding_idx")
c.commit()
c.close()
print("dropped ivfflat index; queries will use sequential scan (fine for small corpora)")
