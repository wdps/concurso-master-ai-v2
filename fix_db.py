# -*- coding: utf-8 -*-
import sqlite3
import json

def corrigir_banco():
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    
    # Criar tabela temas_redacao se não existir
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temas_redacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema TEXT NOT NULL,
            categoria TEXT NOT NULL,
            palavras_chave TEXT,
            dicas TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inserir alguns temas de exemplo
    temas = [
        ('Os impactos da inteligência artificial no mercado de trabalho', 'Tecnologia', 'IA, automação, emprego', 'Aborde benefícios e desafios'),
        ('Desafios da educação pública no Brasil', 'Educação', 'educação, desigualdade', 'Foque em soluções inovadoras'),
        ('Sustentabilidade e desenvolvimento econômico', 'Meio Ambiente', 'sustentabilidade, economia', 'Apresente exemplos concretos')
    ]
    
    for tema in temas:
        cursor.execute('INSERT OR IGNORE INTO temas_redacao (tema, categoria, palavras_chave, dicas) VALUES (?, ?, ?, ?)', tema)
    
    conn.commit()
    
    # Verificar
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    print('Tabelas:', tables)
    
    cursor.execute('SELECT COUNT(*) FROM temas_redacao')
    count = cursor.fetchone()[0]
    print(f'Temas de redação: {count}')
    
    conn.close()
    return True

if __name__ == '__main__':
    corrigir_banco()
    print('✅ Banco corrigido com sucesso!')
