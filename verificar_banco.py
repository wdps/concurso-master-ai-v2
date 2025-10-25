# verificar_banco.py - Verificar questões no banco
import sqlite3
import csv
import os

def verificar_questoes():
    print("🔍 VERIFICANDO BANCO DE DADOS")
    print("=" * 50)
    
    # Conectar ao banco
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    
    # Verificar tabela
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questoes'")
    tabela_existe = cursor.fetchone()
    
    if not tabela_existe:
        print("❌ Tabela 'questoes' não existe!")
        return
    
    # Contar questões no banco
    cursor.execute("SELECT COUNT(*) FROM questoes")
    total_banco = cursor.fetchone()[0]
    print(f"📊 Total de questões no banco: {total_banco}")
    
    # Verificar questões por matéria
    print("\n📚 Questões por matéria:")
    cursor.execute("SELECT materia, COUNT(*) FROM questoes GROUP BY materia ORDER BY COUNT(*) DESC")
    for materia, count in cursor.fetchall():
        print(f"   - {materia}: {count} questões")
    
    # Verificar CSV
    print(f"\n📁 Verificando arquivo CSV...")
    if os.path.exists('questoes.csv'):
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            linhas_csv = list(csv_reader)
            print(f"📄 Total de linhas no CSV: {len(linhas_csv)}")
            
            # Verificar matérias únicas no CSV
            materias_csv = set()
            for row in linhas_csv:
                materia = row.get('disciplina', 'Geral')
                materias_csv.add(materia)
            
            print(f"📚 Matérias únicas no CSV: {len(materias_csv)}")
            
    else:
        print("❌ Arquivo questoes.csv não encontrado!")
    
    # Verificar algumas questões de exemplo
    print(f"\n🔍 Amostra de questões (primeiras 3):")
    cursor.execute("SELECT id, materia, enunciado FROM questoes LIMIT 3")
    for id, materia, enunciado in cursor.fetchall():
        print(f"   ID {id} - {materia}: {enunciado[:80]}...")
    
    conn.close()
    print("=" * 50)
    
    if total_banco < 100:
        print("⚠️  AVISO: Poucas questões no banco. Verifique o carregamento do CSV.")
    else:
        print("✅ Banco parece estar correto!")

if __name__ == "__main__":
    verificar_questoes()
