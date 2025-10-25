import sqlite3
import pandas as pd
import os

def criar_banco_completo():
    print("🚀 CRIANDO BANCO DE DADOS COMPLETO...")
    
    # Conectar ao banco
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    
    # Criar tabela se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questões (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina TEXT NOT NULL,
            enunciado TEXT NOT NULL,
            alt_a TEXT NOT NULL,
            alt_b TEXT NOT NULL,
            alt_c TEXT NOT NULL,
            alt_d TEXT NOT NULL,
            gabarito TEXT NOT NULL
        )
    ''')
    
    print("✅ TABELA CRIADA")
    
    # Verificar se já existem questões
    cursor.execute("SELECT COUNT(*) FROM questões")
    qtd_existente = cursor.fetchone()[0]
    
    if qtd_existente > 0:
        print(f"📊 Banco já tem {qtd_existente} questões")
        conn.close()
        return qtd_existente
    
    # Importar do CSV
    try:
        print("📄 LENDO ARQUIVO CSV...")
        df = pd.read_csv('questoes.csv')
        print(f"📊 CSV carregado: {len(df)} questões")
        
        # Inserir questões
        for index, row in df.iterrows():
            cursor.execute('''
                INSERT INTO questões (disciplina, enunciado, alt_a, alt_b, alt_c, alt_d, gabarito)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                str(row['disciplina']),
                str(row['enunciado']),
                str(row['alt_a']),
                str(row['alt_b']),
                str(row['alt_c']),
                str(row['alt_d']),
                str(row['gabarito'])
            ))
        
        conn.commit()
        
        # Verificar total
        cursor.execute("SELECT COUNT(*) FROM questões")
        total = cursor.fetchone()[0]
        
        # Ver matérias
        cursor.execute("SELECT DISTINCT disciplina, COUNT(*) FROM questões GROUP BY disciplina")
        materias = cursor.fetchall()
        
        print(f"🎉 IMPORTADAS {total} QUESTÕES!")
        print("📚 MATÉRIAS IMPORTADAS:")
        for materia, qtd in materias:
            print(f"   {materia}: {qtd} questões")
            
        conn.close()
        return total
        
    except Exception as e:
        print(f"❌ ERRO NA IMPORTACAO: {e}")
        conn.close()
        return 0

# Executar
if __name__ == "__main__":
    criar_banco_completo()
