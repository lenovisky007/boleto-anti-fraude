import sqlite3

conn = sqlite3.connect("app.db")
cur = conn.cursor()

cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
print("Tabelas:", cur.fetchall())

try:
    cur.execute("SELECT * FROM trusted_entities LIMIT 1")
    print("trusted_entities existe.")
except Exception as e:
    print("Erro ao acessar trusted_entities:", e)