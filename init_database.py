# -*- coding: utf-8 -*-
import sqlite3
import os

def init_database():
    \"\"\"Inicializa o banco de dados com todas as tabelas necessárias\"\"\"
    conn = sqlite3.connect('concurso.db')
    cursor = conn.cursor()
    
    # Lista de tabelas para criar
    tables = {
        'questoes': '''
            CREATE TABLE IF NOT EXISTS questões (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT NOT NULL,
                materia TEXT NOT NULL,
                alternativas TEXT NOT NULL,
                resposta_correta TEXT NOT NULL,
                explicacao TEXT,
                dificuldade TEXT DEFAULT 'Média',
                tempo_estimado INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''',
        'historico_simulados': '''
            CREATE TABLE IF NOT EXISTS historico_simulados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                relatorio TEXT NOT NULL,
                data_fim TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tipo_simulado TEXT DEFAULT 'Personalizado',
                quantidade_questoes INTEGER,
                materias_selecionadas TEXT
            )
        ''',
        'temas_redacao': '''
            CREATE TABLE IF NOT EXISTS temas_redacao (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tema TEXT NOT NULL,
                categoria TEXT NOT NULL,
                palavras_chave TEXT,
                dicas TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        '''
    }
    
    # Criar cada tabela
    for table_name, create_sql in tables.items():
        try:
            cursor.execute(create_sql)
            print(f'✅ Tabela {table_name} criada/verificada')
        except Exception as e:
            print(f'❌ Erro na tabela {table_name}: {e}')
    
    # Inserir dados iniciais em temas_redacao se estiver vazia
    cursor.execute('SELECT COUNT(*) FROM temas_redacao')
    if cursor.fetchone()[0] == 0:
        temas = [
            ('Inteligência artificial e o futuro do trabalho', 'Tecnologia', 'IA, emprego, tecnologia', 'Analise impactos positivos e negativos'),
            ('Educação pública no século XXI', 'Educação', 'educação, tecnologia, acesso', 'Discuta inclusão digital'),
            ('Desenvolvimento sustentável', 'Meio Ambiente', 'sustentabilidade, economia', 'Aborde soluções práticas')
        ]
        for tema in temas:
            cursor.execute('INSERT INTO temas_redacao (tema, categoria, palavras_chave, dicas) VALUES (?, ?, ?, ?)', tema)
        print('✅ Temas de redação inseridos')
    
    conn.commit()
    conn.close()
    print('🎉 Banco de dados inicializado com sucesso!')

if __name__ == '__main__':
    init_database()
