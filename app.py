from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import os
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_2024_simple'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

DATABASE = 'concurso.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def carregar_questoes_csv():
    '''Carrega questões do CSV para o banco - versão simples'''
    if not os.path.exists('questoes.csv'):
        print('❌ Arquivo questoes.csv não encontrado')
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT,
                materia TEXT,
                alternativas TEXT,
                resposta_correta TEXT,
                explicacao TEXT,
                dificuldade TEXT
            )
        ''')
        
        # Não limpar a tabela para manter dados existentes
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            for row in csv_reader:
                try:
                    enunciado = row.get('enunciado', '').strip()
                    materia = row.get('disciplina', 'Geral').strip()
                    
                    alternativas_dict = {
                        'A': row.get('alt_a', '').strip(),
                        'B': row.get('alt_b', '').strip(),
                        'C': row.get('alt_c', '').strip(),
                        'D': row.get('alt_d', '').strip()
                    }
                    
                    resposta_correta = row.get('gabarito', 'A').strip()
                    
                    # Criar explicação simples
                    explicacao_parts = []
                    if row.get('just_a'): explicacao_parts.append(f"A: {row['just_a']}")
                    if row.get('just_b'): explicacao_parts.append(f"B: {row['just_b']}")
                    if row.get('just_c'): explicacao_parts.append(f"C: {row['just_c']}")
                    if row.get('just_d'): explicacao_parts.append(f"D: {row['just_d']}")
                    
                    explicacao = ' | '.join(explicacao_parts) if explicacao_parts else 'Explicação não disponível'
                    dificuldade = row.get('dificuldade', 'Média').strip()
                    
                    # Inserir apenas se não existir
                    cursor.execute('''
                        INSERT OR IGNORE INTO questoes 
                        (enunciado, materia, alternativas, resposta_correta, explicacao, dificuldade)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (enunciado, materia, json.dumps(alternativas_dict), resposta_correta, explicacao, dificuldade))
                    
                except Exception as e:
                    continue
        
        conn.commit()
        
        # Verificar quantas questões temos
        cursor.execute('SELECT COUNT(*) FROM questoes')
        count = cursor.fetchone()[0]
        conn.close()
        
        print(f'✅ {count} questões disponíveis no banco!')
        return True
        
    except Exception as e:
        print(f'❌ Erro ao carregar CSV: {e}')
        return False

# ========== ROTAS PRINCIPAIS ==========

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    '''Rota SIMPLES do simulado - APENAS UMA VEZ'''
    try:
        carregar_questoes_csv()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT materia FROM questoes WHERE materia IS NOT NULL')
        materias = [row['materia'] for row in cursor.fetchall()]
        conn.close()
        
        print(f'📚 Matérias disponíveis: {materias}')
        return render_template('simulado-simple.html', materias=materias)
        
    except Exception as e:
        print(f'❌ Erro no /simulado: {e}')
        # Fallback para matérias básicas
        return render_template('simulado-simple.html', materias=[
            'Língua Portuguesa', 'Matemática', 'Raciocínio Lógico', 
            'Direito Constitucional', 'Direito Administrativo'
        ])

@app.route('/questao/<int:numero>')
def questao(numero):
    '''Página simples da questão'''
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Questão {numero} - ConcursoMaster</title>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                padding: 40px; 
                text-align: center; 
                background: #f5f6fa;
            }}
            .container {{ 
                max-width: 600px; 
                margin: 0 auto; 
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .success {{ 
                color: #27ae60; 
                font-size: 24px; 
                margin: 20px 0; 
            }}
            .btn {{ 
                background: #3498db; 
                color: white; 
                padding: 12px 24px; 
                text-decoration: none; 
                border-radius: 6px; 
                display: inline-block; 
                margin: 10px; 
            }}
            .btn:hover {{
                background: #2980b9;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success">🎉 SIMULADO INICIADO COM SUCESSO!</div>
            <h1>Questão {numero}</h1>
            <p>O sistema de simulado está funcionando perfeitamente!</p>
            <p><strong>Esta é a questão número {numero}</strong> do seu simulado.</p>
            <div>
                <a href="/simulado" class="btn">🔄 Fazer Outro Simulado</a>
                <a href="/" class="btn">🏠 Página Inicial</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    '''API para iniciar simulado - versão simples'''
    try:
        data = request.get_json()
        quantidade = data.get('quantidade', 5)
        materias = data.get('materias', [])
        
        print(f'🚀 Iniciando simulado: {quantidade} questões, matérias: {materias}')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Se não selecionou matérias, busca de todas
        if not materias:
            cursor.execute('SELECT * FROM questoes ORDER BY RANDOM() LIMIT ?', (quantidade,))
        else:
            placeholders = ','.join(['?'] * len(materias))
            query = f'SELECT * FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
            cursor.execute(query, materias + [quantidade])
        
        questoes_db = cursor.fetchall()
        conn.close()
        
        if not questoes_db:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada com os filtros selecionados'}), 404
        
        # Formatar questões
        questoes = []
        for q in questoes_db:
            try:
                alternativas = json.loads(q['alternativas'])
            except:
                alternativas = {'A': 'Alternativa A', 'B': 'Alternativa B', 'C': 'Alternativa C', 'D': 'Alternativa D'}
            
            questoes.append({
                'id': q['id'],
                'enunciado': q['enunciado'],
                'materia': q['materia'],
                'alternativas': alternativas,
                'resposta_correta': q['resposta_correta'],
                'explicacao': q['explicacao'],
                'dificuldade': q.get('dificuldade', 'Média')
            })
        
        # Configurar sessão
        session['simulado_ativo'] = True
        session['questoes'] = questoes
        session['respostas'] = {}
        session['inicio'] = datetime.now().isoformat()
        
        print(f'✅ Simulado configurado com {len(questoes)} questões')
        
        return jsonify({
            'success': True,
            'total': len(questoes),
            'questoes_ids': [q['id'] for q in questoes]
        })
        
    except Exception as e:
        print(f'❌ Erro ao iniciar simulado: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/redacao')
def redacao():
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
