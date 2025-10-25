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
            'tema': 'Os impactos da intelig�ncia artificial no mercado de trabalho',
            'categoria': 'Tecnologia e Sociedade',
            'palavras_chave': 'IA, automa��o, emprego, qualifica��o',
            'dicas': 'Aborde tanto os benef�cios quanto os desafios. Discuta a necessidade de requalifica��o profissional.'
        },
        {
            'tema': 'Desafios da educa��o p�blica no Brasil p�s-pandemia',
            'categoria': 'Educa��o',
            'palavras_chave': 'educa��o p�blica, desigualdade, tecnologia, evas�o escolar',
            'dicas': 'Foque nas desigualdades educacionais agravadas pela pandemia e proponha solu��es inovadoras.'
        },
        {
            'tema': 'Sustentabilidade e desenvolvimento econ�mico: � poss�vel conciliar?',
            'categoria': 'Meio Ambiente',
            'palavras_chave': 'sustentabilidade, desenvolvimento, meio ambiente, economia verde',
            'dicas': 'Apresente exemplos concretos de desenvolvimento sustent�vel e analise pol�ticas p�blicas eficazes.'
        },
        {
            'tema': 'A crise habitacional nas grandes cidades brasileiras',
            'categoria': 'Urbanismo',
            'palavras_chave': 'habita��o, mobilidade urbana, desigualdade, pol�ticas p�blicas',
            'dicas': 'Discuta causas estruturais e proponha solu��es integradas para moradia digna.'
        },
        {
            'tema': 'Os desafios do sistema de sa�de p�blica no Brasil',
            'categoria': 'Sa�de',
            'palavras_chave': 'SUS, sa�de p�blica, acesso, qualidade, financiamento',
            'dicas': 'Aborde desde a preven��o at� o tratamento, com foco na universalidade e equidade.'
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
    print(f'Temas de reda��o inseridos: {count}')
    
    conn.close()
    return True

if __name__ == '__main__':
    criar_tabelas()
    print('? Banco de dados inicializado com sucesso!')
