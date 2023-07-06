import sqlite3

conn = sqlite3.connect('instance/db.sqlite3')

c = conn.cursor()

c.execute("""CREATE TABLE upload (
            id text,
            filename text,
            data blob
            )""")

conn.commit()
conn.close()