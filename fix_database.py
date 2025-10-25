import sqlite3
import os

def corrigir_estrutura_banco():
    print("🔧 CORRIGINDO ESTRUTURA DO BANCO DE DADOS...")
    
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    
    # 1. Verificar estrutura atual
    print("📊 ESTRUTURA ATUAL:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  Tabela: {table[0]}")
        cursor.execute(f"PRAGMA table_info({table[0]})")
        columns = cursor.fetchall()
        for col in columns:
            print(f"    - {col[1]} ({col[2]})")
    
    # 2. Recriar a tabela questões com estrutura correta
    print("\\n🔄 RECRIANDO TABELA QUESTOES...")
    
    # Backup dos dados existentes (se houver)
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questoes_old'")
    if not cursor.fetchone():
        cursor.execute("ALTER TABLE questoes RENAME TO questoes_old")
    
    # Criar nova tabela com estrutura correta
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            enunciado TEXT NOT NULL,
            materia TEXT NOT NULL,
            alternativas TEXT NOT NULL,
            resposta_correta TEXT NOT NULL,
            explicacao TEXT,
            dificuldade TEXT DEFAULT 'Media',
            tempo_estimado INTEGER DEFAULT 60,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Migrar dados se existir tabela old
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='questoes_old'")
    if cursor.fetchone():
        print("📦 MIGRANDO DADOS EXISTENTES...")
        try:
            cursor.execute('''
                INSERT INTO questoes (id, enunciado, materia, alternativas, resposta_correta, explicacao)
                SELECT id, enunciado, 
                       CASE 
                           WHEN materia IS NULL THEN 'Geral' 
                           ELSE materia 
                       END as materia,
                       alternativas, resposta_correta, explicacao
                FROM questoes_old
            ''')
            print(f"✅ {cursor.rowcount} questões migradas")
        except Exception as e:
            print(f"⚠️  Erro na migração: {e}")
            print("📝 Inserindo questões de exemplo...")
            inserir_questoes_exemplo(cursor)
    else:
        print("📝 INSERINDO QUESTÕES DE EXEMPLO...")
        inserir_questoes_exemplo(cursor)
    
    conn.commit()
    
    # 3. Verificar se a correção funcionou
    print("\\n✅ VERIFICANDO CORREÇÃO:")
    cursor.execute("PRAGMA table_info(questoes)")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"  Colunas na tabela questões: {columns}")
    
    cursor.execute("SELECT COUNT(*) FROM questoes")
    count = cursor.fetchone()[0]
    print(f"  Total de questões: {count}")
    
    cursor.execute("SELECT DISTINCT materia FROM questoes")
    materias = [row[0] for row in cursor.fetchall()]
    print(f"  Matérias disponíveis: {materias}")
    
    conn.close()
    print("🎉 ESTRUTURA DO BANCO CORRIGIDA COM SUCESSO!")
    return True

def inserir_questoes_exemplo(cursor):
    questões = [
        {
            'enunciado': 'Qual e a capital do Brasil?',
            'materia': 'Geografia',
            'alternativas': '{"A": "Rio de Janeiro", "B": "Brasilia", "C": "Sao Paulo", "D": "Salvador"}',
            'resposta_correta': 'B',
            'explicacao': '✅ CORRETO: Brasilia e a capital federal do Brasil desde 1960.'
        },
        {
            'enunciado': 'Quem escreveu "Dom Casmurro"?',
            'materia': 'Literatura', 
            'alternativas': '{"A": "Machado de Assis", "B": "Jose de Alencar", "C": "Lima Barreto", "D": "Graciliano Ramos"}',
            'resposta_correta': 'A',
            'explicacao': '✅ CORRETO: Machado de Assis publicou "Dom Casmurro" em 1899.'
        },
        {
            'enunciado': 'Qual oceano banha o litoral brasileiro?',
            'materia': 'Geografia',
            'alternativas': '{"A": "Oceano Pacifico", "B": "Oceano Indico", "C": "Oceano Atlantico", "D": "Oceano Artico"}',
            'resposta_correta': 'C',
            'explicacao': '✅ CORRETO: O Brasil possui litoral banhado pelo Oceano Atlantico.'
        }
    ]
    
    for questao in questões:
        cursor.execute('''
            INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            questao['enunciado'],
            questao['materia'],
            questao['alternativas'],
            questao['resposta_correta'],
            questao['explicacao']
        ))
    
    print(f"✅ {len(questões)} questões de exemplo inseridas")

if __name__ == '__main__':
    corrigir_estrutura_banco()
