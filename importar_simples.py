import sqlite3
import pandas as pd

print("🚀 IMPORTANDO QUESTÕES DO CSV...")

# Conectar e criar tabela
conn = sqlite3.connect("concurso.db")
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS questões (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disciplina TEXT,
        enunciado TEXT,
        alt_a TEXT,
        alt_b TEXT,
        alt_c TEXT,
        alt_d TEXT,
        gabarito TEXT
    )
''')

print("✅ Tabela criada")

# Ler CSV
df = pd.read_csv("questoes.csv")
print(f"📄 CSV: {len(df)} questões")

# Inserir questões
for index, row in df.iterrows():
    cursor.execute(
        "INSERT INTO questões (disciplina, enunciado, alt_a, alt_b, alt_c, alt_d, gabarito) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (row['disciplina'], row['enunciado'], row['alt_a'], row['alt_b'], row['alt_c'], row['alt_d'], row['gabarito'])
    )

conn.commit()

# Ver resultado
cursor.execute("SELECT COUNT(*) FROM questões")
total = cursor.fetchone()[0]

cursor.execute("SELECT DISTINCT disciplina FROM questões")
materias = [row[0] for row in cursor.fetchall()]

print(f"🎉 {total} questões importadas!")
print("📚 Matérias:", materias)

conn.close()
