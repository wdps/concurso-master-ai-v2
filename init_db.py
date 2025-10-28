import sqlite3
import json
import os
import csv
from io import StringIO

def init_db():
    print("🚀 INICIALIZANDO BANCO DE DADOS DO CONCURSOIA...")
    
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
    
    print(f"📊 Questões no banco: {count_questoes}")
    print(f"📝 Temas no banco: {count_temas}")
    
    # Inserir QUESTÕES se estiver vazio
    if count_questoes == 0:
        print("📥 Inserindo questões no banco...")
        
        # Questões completas do ConcursoIA
        questions_data = [
            # MATEMÁTICA
            {
                'materia': 'Matemática',
                'questao': 'Qual o valor de 2 + 2?',
                'alternativas': json.dumps(['A) 3', 'B) 4', 'C) 5', 'D) 6']),
                'resposta_correta': 'B',
                'explicacao': '2 + 2 = 4, portanto a alternativa correta é B) 4'
            },
            {
                'materia': 'Matemática',
                'questao': 'Qual a raiz quadrada de 16?',
                'alternativas': json.dumps(['A) 2', 'B) 3', 'C) 4', 'D) 5']),
                'resposta_correta': 'C', 
                'explicacao': 'A raiz quadrada de 16 é 4, pois 4 × 4 = 16'
            },
            {
                'materia': 'Matemática',
                'questao': 'Quanto é 15% de 200?',
                'alternativas': json.dumps(['A) 15', 'B) 20', 'C) 25', 'D) 30']),
                'resposta_correta': 'D',
                'explicacao': '15% de 200 = 0.15 × 200 = 30'
            },
            
            # PORTUGUÊS
            {
                'materia': 'Português',
                'questao': 'Assinale a alternativa correta quanto à acentuação:',
                'alternativas': json.dumps(['A) idéia', 'B) ideia', 'C) idèia', 'D) ideía']),
                'resposta_correta': 'B',
                'explicacao': 'De acordo com o Novo Acordo Ortográfico, "ideia" não leva acento.'
            },
            {
                'materia': 'Português', 
                'questao': 'Qual é o sujeito da frase: "Os alunos estudaram para a prova."?',
                'alternativas': json.dumps(['A) Os alunos', 'B) estudaram', 'C) para a prova', 'D) prova']),
                'resposta_correta': 'A',
                'explicacao': '"Os alunos" é o sujeito da oração, praticante da ação de estudar.'
            },
            
            # HISTÓRIA
            {
                'materia': 'História',
                'questao': 'Quem descobriu o Brasil?',
                'alternativas': json.dumps(['A) Cabral', 'B) Colombo', 'C) Vasco da Gama', 'D) Magalhães']),
                'resposta_correta': 'A',
                'explicacao': 'Pedro Álvares Cabral descobriu o Brasil em 22 de abril de 1500.'
            },
            {
                'materia': 'História',
                'questao': 'Em que ano ocorreu a Proclamação da República no Brasil?',
                'alternativas': json.dumps(['A) 1822', 'B) 1889', 'C) 1891', 'D) 1900']),
                'resposta_correta': 'B', 
                'explicacao': 'A Proclamação da República ocorreu em 15 de novembro de 1889.'
            },
            
            # GEOGRAFIA
            {
                'materia': 'Geografia',
                'questao': 'Qual é a capital do Brasil?',
                'alternativas': json.dumps(['A) Rio de Janeiro', 'B) São Paulo', 'C) Brasília', 'D) Salvador']),
                'resposta_correta': 'C',
                'explicacao': 'Brasília é a capital federal do Brasil desde 1960.'
            },
            
            # DIREITO CONSTITUCIONAL
            {
                'materia': 'Direito Constitucional',
                'questao': 'Quantos artigos tem a Constituição Federal de 1988?',
                'alternativas': json.dumps(['A) 200', 'B) 250', 'C) 300', 'D) 245']),
                'resposta_correta': 'B',
                'explicacao': 'A Constituição Federal de 1988 possui 250 artigos.'
            }
        ]
        
        for q in questions_data:
            cursor.execute(
                "INSERT INTO questions (materia, questao, alternativas, resposta_correta, explicacao) VALUES (?, ?, ?, ?, ?)",
                (q['materia'], q['questao'], q['alternativas'], q['resposta_correta'], q['explicacao'])
            )
        
        print(f"✅ {len(questions_data)} questões inseridas")
    
    # Inserir TEMAS DE REDAÇÃO se estiver vazio
    if count_temas == 0:
        print("📥 Inserindo temas de redação...")
        
        temas_data = [
            ('O impacto das redes sociais na sociedade contemporânea', 'Tecnologia'),
            ('Desafios da educação no século XXI', 'Educação'),
            ('A importância da preservação ambiental', 'Meio Ambiente'),
            ('Os efeitos da globalização na cultura local', 'Cultura'),
            ('A violência urbana e suas consequências', 'Sociologia'),
            ('O papel do Estado no combate às desigualdades sociais', 'Sociologia'),
            ('Os desafios da mobilidade urbana nas grandes cidades', 'Urbanismo'),
            ('A influência da inteligência artificial no mercado de trabalho', 'Tecnologia'),
            ('A importância do esporte na formação do cidadão', 'Educação'),
            ('Os limites da liberdade de expressão na internet', 'Direito')
        ]
        
        for tema in temas_data:
            cursor.execute(
                "INSERT INTO redacao_temas (tema, categoria) VALUES (?, ?)",
                tema
            )
        
        print(f"✅ {len(temas_data)} temas de redação inseridos")
    
    conn.commit()
    
    # Verificar dados finais
    cursor.execute("SELECT COUNT(*) FROM questions")
    final_questoes = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM redacao_temas") 
    final_temas = cursor.fetchone()[0]
    
    cursor.execute("SELECT DISTINCT materia FROM questions")
    materias = [row[0] for row in cursor.fetchall()]
    
    conn.close()
    
    print("=" * 50)
    print("🎯 BANCO DE DADOS INICIALIZADO COM SUCESSO!")
    print(f"📚 Total de questões: {final_questoes}")
    print(f"📝 Total de temas: {final_temas}")
    print(f"📖 Matérias: {', '.join(materias)}")
    print("=" * 50)

if __name__ == '__main__':
    init_db()
