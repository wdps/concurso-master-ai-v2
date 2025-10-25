import sqlite3

print("🔍 VERIFICANDO BANCO DE DADOS...")

try:
    conn = sqlite3.connect('concurso.db')
    c = conn.cursor()
    
    # Contar questões
    c.execute('SELECT COUNT(*) FROM questões')
    qtd = c.fetchone()[0]
    print(f'🎯 Questões no banco local: {qtd}')
    
    # Listar tabelas
    c.execute('SELECT name FROM sqlite_master WHERE type=\"table\"')
    tables = [row[0] for row in c.fetchall()]
    print(f'📊 Tabelas: {tables}')
    
    # Ver matérias
    if 'questões' in tables:
        c.execute('SELECT DISTINCT disciplina FROM questões')
        materias = [row[0] for row in c.fetchall()]
        print(f'📚 Matérias: {len(materias)}')
        for materia in materias[:5]:  # Mostrar primeiras 5
            print(f'   - {materia}')
    
    conn.close()
    print('✅ Verificação concluída!')
    
except Exception as e:
    print(f'❌ Erro: {e}')
