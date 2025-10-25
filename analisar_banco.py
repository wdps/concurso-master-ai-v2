import sqlite3
import pandas as pd

def analisar_questoes():
    conn = sqlite3.connect('concurso.db')
    
    print("🔍 ANALISANDO BANCO DE DADOS...")
    print("=" * 50)
    
    # Ver estrutura
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(questões)")
    colunas = cursor.fetchall()
    print("📋 ESTRUTURA DA TABELA:")
    for coluna in colunas:
        print(f"  {coluna[1]} ({coluna[2]})")
    
    # Contagem total
    cursor.execute("SELECT COUNT(*) as total FROM questões")
    total = cursor.fetchone()[0]
    print(f"\n📊 TOTAL DE QUESTÕES: {total}")
    
    # Matérias disponíveis
    print("\n🎯 MATÉRIAS DISPONÍVEIS:")
    cursor.execute("SELECT disciplina, COUNT(*) as qtd FROM questões GROUP BY disciplina ORDER BY qtd DESC")
    for materia, qtd in cursor.fetchall():
        print(f"  {materia}: {qtd} questões")
    
    # Amostra de questões
    print(f"\n📚 AMOSTRA DE 2 QUESTÕES:")
    cursor.execute("SELECT disciplina, enunciado, gabarito FROM questões LIMIT 2")
    for i, (materia, enunciado, gabarito) in enumerate(cursor.fetchall(), 1):
        print(f"\n--- Questão {i} ({materia}) ---")
        print(f"Enunciado: {enunciado[:150]}...")
        print(f"Gabarito: {gabarito}")
    
    conn.close()
    print("\n" + "=" * 50)
    print("✅ ANÁLISE CONCLUÍDA")

analisar_questoes()
