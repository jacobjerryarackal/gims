import sqlite3
import os

path = os.path.abspath('.chromadb/chroma.sqlite3')
print('path', path)
print('exists', os.path.exists(path))
if not os.path.exists(path):
    raise SystemExit(1)

con = sqlite3.connect(path)
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cur.fetchall()
print('tables', tables)
for t in [t[0] for t in tables]:
    try:
        cur.execute(f'SELECT count(*) FROM {t}')
        cnt = cur.fetchone()[0]
        print(t, cnt)
    except Exception as e:
        print('skip', t, type(e).__name__, e)

# Try to see collection metadata if available
for t in ['collections', 'documents', 'metadatas', 'embeddings', 'ids', 'chunks']:
    if any(tab[0] == t for tab in tables):
        try:
            cur.execute(f'SELECT * FROM {t} LIMIT 5')
            rows = cur.fetchall()
            print('sample', t, rows)
        except Exception as e:
            print('sample error', t, type(e).__name__, e)
con.close()
