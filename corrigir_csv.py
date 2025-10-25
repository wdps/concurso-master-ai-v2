import pandas as pd
import sqlite3

print("🔧 CORRIGINDO CSV E CRIANDO BANCO...")

# Ler CSV linha por linha para debug
with open('questoes.csv', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"📄 Total de linhas no CSV: {len(lines)}")
print("🔍 Primeiras 2 linhas:")
for i in range(min(2, len(lines))):
    print(f"Linha {i+1}: {lines[i][:150]}")

# Tentar ler como CSV
try:
    df = pd.read_csv('questoes.csv', encoding='utf-8', sep=',', engine='python')
    print("✅ CSV lido com separador ,")
except:
    try:
        df = pd.read_csv('questoes.csv', encoding='utf-8', sep=';', engine='python') 
        print("✅ CSV lido com separador ;")
    except:
        try:
            df = pd.read_csv('questoes.csv', encoding='latin-1', sep=',', engine='python')
            print("✅ CSV lido com encoding latin-1")
        except Exception as e:
            print(f"❌ Erro: {e}")
            exit()

print(f"📊 Linhas: {len(df)}, Colunas: {len(df.columns)}")
print("📋 Colunas:", list(df.columns))

# Criar banco
conn = sqlite3.connect('concurso.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS questões (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        disciplina TEXT, enunciado TEXT,
        alt_a TEXT, alt_b TEXT, alt_c TEXT, alt_d TEXT,
        gabarito TEXT
    )
''')

# Inserir baseado na estrutura encontrada
inseridas = 0
colunas = df.columns

for index, row in df.iterrows():
    try:
        # Mapeamento flexível baseado nas colunas disponíveis
        values = []
        for col in ['disciplina', 'enunciado', 'alt_a', 'alt_b', 'alt_c', 'alt_d', 'gabarito']:
            if col in df.columns:
                values.append(str(row[col]))
            else:
                # Fallback para colunas numéricas
                col_index = list(df.columns).index(col) if col in df.columns else min(len(df.columns)-1, ['disciplina', 'enunciado', 'alt_a', 'alt_b', 'alt_c', 'alt_d', 'gabarito'].index(col))
                values.append(str(row[col_index]) if col_index < len(row) else "N/A")
        
        cursor.execute(
            "INSERT INTO questões (disciplina, enunciado, alt_a, alt_b, alt_c, alt_d, gabarito) VALUES (?, ?, ?, ?, ?, ?, ?)",
            tuple(values)
        )
        inseridas += 1
        
        if inseridas % 50 == 0:
            print(f"📥 {inseridas} questões processadas...")
            
    except Exception as e:
        continue

conn.commit()

cursor.execute("SELECT COUNT(*) FROM questões")
total = cursor.fetchone()[0]

cursor.execute("SELECT DISTINCT disciplina FROM questões")
materias = [row[0] for row in cursor.fetchall()]

print(f"🎉 BANCO CRIADO COM {total} QUESTÕES!")
print(f"📚 MATÉRIAS: {materias}")

conn.close()
