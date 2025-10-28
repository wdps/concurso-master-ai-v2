import sqlite3
import json
import os

def init_db():
    conn = sqlite3.connect('concursos.db')
    cursor = conn.cursor()
    
    # Criar tabela de questões
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            materia TEXT NOT NULL,
            questao TEXT NOT NULL,
            alternativas TEXT NOT NULL,
            resposta_correta TEXT NOT NULL,
            explicacao TEXT
        )
    ''')
    
    # Criar tabela de temas de redação
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS redacao_temas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tema TEXT NOT NULL,
            categoria TEXT NOT NULL
        )
    ''')
    
    # Verificar se já existem dados
    cursor.execute("SELECT COUNT(*) FROM questions")
    count_questoes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM redacao_temas")
    count_temas = cursor.fetchone()[0]
    
    # Inserir dados de exemplo se estiver vazio
    if count_questoes == 0:
        print("📝 Inserindo questões de exemplo...")
        
        # Questões de exemplo
        questions = [
            {
                'materia': 'Matemática',
                'questao': 'Qual o valor de 2 + 2?',
                'alternativas': json.dumps(['A) 3', 'B) 4', 'C) 5', 'D) 6']),
                'resposta_correta': 'B',
                'explicacao': '2 + 2 = 4, portanto a alternativa correta é B) 4'
            },
            {
                'materia': 'Português', 
                'questao': 'Assinale a alternativa correta quanto à acentuação:',
                'alternativas': json.dumps(['A) idéia', 'B) ideia', 'C) idèia', 'D) ideía']),
                'resposta_correta': 'B',
                'explicacao': 'De acordo com o Novo Acordo Ortográfico, "ideia" não leva acento.'
            },
            {
                'materia': 'História',
                'questao': 'Quem descobriu o Brasil?',
                'alternativas': json.dumps(['A) Cabral', 'B) Colombo', 'C) Vasco da Gama', 'D) Magalhães']),
                'resposta_correta': 'A', 
                'explicacao': 'Pedro Álvares Cabral descobriu o Brasil em 22 de abril de 1500.'
            }
        ]
        
        for q in questions:
            cursor.execute(
                "INSERT INTO questions (materia, questao, alternativas, resposta_correta, explicacao) VALUES (?, ?, ?, ?, ?)",
                (q['materia'], q['questao'], q['alternativas'], q['resposta_correta'], q['explicacao'])
            )
    
    if count_temas == 0:
        print("📝 Inserindo temas de redação de exemplo...")
        
        temas = [
            ('O impacto das redes sociais na sociedade contemporânea', 'Tecnologia'),
            ('Desafios da educação no século XXI', 'Educação'),
            ('A importância da preservação ambiental', 'Meio Ambiente'),
            ('Os efeitos da globalização na cultura local', 'Cultura'),
            ('A violência urbana e suas consequências', 'Sociologia')
        ]
        
        for tema in temas:
            cursor.execute(
                "INSERT INTO redacao_temas (tema, categoria) VALUES (?, ?)",
                tema
            )
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado com sucesso!")

if __name__ == '__main__':
    init_db()
