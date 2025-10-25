import sqlite3
import json
import os

DATABASE = 'concurso.db'

def criar_tabelas():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Tabela de temas_redacao
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
    
    # Inserir temas de exemplo
    temas = [
        {
            'tema': 'Os impactos da inteligência artificial no mercado de trabalho',
            'categoria': 'Tecnologia e Sociedade',
            'palavras_chave': 'IA, automação, emprego, qualificação',
            'dicas': 'Aborde tanto os benefícios quanto os desafios. Discuta a necessidade de requalificação profissional.'
        },
        {
            'tema': 'Desafios da educação pública no Brasil pós-pandemia',
            'categoria': 'Educação',
            'palavras_chave': 'educação pública, desigualdade, tecnologia, evasão escolar',
            'dicas': 'Foque nas desigualdades educacionais agravadas pela pandemia e proponha soluções inovadoras.'
        },
        {
            'tema': 'Sustentabilidade e desenvolvimento econômico: é possível conciliar?',
            'categoria': 'Meio Ambiente',
            'palavras_chave': 'sustentabilidade, desenvolvimento, meio ambiente, economia verde',
            'dicas': 'Apresente exemplos concretos de desenvolvimento sustentável e analise políticas públicas eficazes.'
        },
        {
            'tema': 'A crise habitacional nas grandes cidades brasileiras',
            'categoria': 'Urbanismo',
            'palavras_chave': 'habitação, mobilidade urbana, desigualdade, políticas públicas',
            'dicas': 'Discuta causas estruturais e proponha soluções integradas para moradia digna.'
        },
        {
            'tema': 'Os desafios do sistema de saúde pública no Brasil',
            'categoria': 'Saúde',
            'palavras_chave': 'SUS, saúde pública, acesso, qualidade, financiamento',
            'dicas': 'Aborde desde a prevenção até o tratamento, com foco na universalidade e equidade.'
        }
    ]
    
    for tema in temas:
        cursor.execute('''
            INSERT OR IGNORE INTO temas_redacao 
            (tema, categoria, palavras_chave, dicas)
            VALUES (?, ?, ?, ?)
        ''', (
            tema['tema'],
            tema['categoria'],
            tema['palavras_chave'],
            tema['dicas']
        ))
    
    conn.commit()
    
    # Verificar tabelas criadas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print('Tabelas no banco:')
    for table in tables:
        print(f'- {table[0]}')
    
    # Contar temas inseridos
    cursor.execute('SELECT COUNT(*) FROM temas_redacao')
    count = cursor.fetchone()[0]
    print(f'Temas de redação inseridos: {count}')
    
    conn.close()
    return True

if __name__ == '__main__':
    criar_tabelas()
    print('? Banco de dados inicializado com sucesso!')
