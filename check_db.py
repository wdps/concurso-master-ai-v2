import sqlite3
import os

def forcar_criacao_tabelas():
    \"\"\"Força a criação de todas as tabelas necessárias\"\"\"
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    
    # Tabela temas_redacao
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
    
    # Verificar se tem dados, se não, inserir
    cursor.execute('SELECT COUNT(*) FROM temas_redacao')
    if cursor.fetchone()[0] == 0:
        temas = [
            {
                'tema': 'Os impactos da inteligência artificial no mercado de trabalho',
                'categoria': 'Tecnologia e Sociedade', 
                'palavras_chave': 'IA, automação, emprego, qualificação',
                'dicas': 'Aborde tanto os benefícios quanto os desafios. Discuta a necessidade de requalificação profissional.'
            }
        ]
        for tema in temas:
            cursor.execute('INSERT INTO temas_redacao (tema, categoria, palavras_chave, dicas) VALUES (?, ?, ?, ?)',
                          (tema['tema'], tema['categoria'], tema['palavras_chave'], tema['dicas']))
    
    conn.commit()
    conn.close()
    print('? Tabelas verificadas/criadas!')

# Executar
forcar_criacao_tabelas()
