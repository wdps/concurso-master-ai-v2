from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import os
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'concurso_master_ai_2024_completo'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600

DATABASE = 'concurso.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def carregar_questoes_csv():
    '''Carrega questões do CSV para o banco'''
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
                    
                    explicacao_parts = []
                    if row.get('just_a'): explicacao_parts.append(f"A: {row['just_a']}")
                    if row.get('just_b'): explicacao_parts.append(f"B: {row['just_b']}")
                    if row.get('just_c'): explicacao_parts.append(f"C: {row['just_c']}")
                    if row.get('just_d'): explicacao_parts.append(f"D: {row['just_d']}")
                    
                    explicacao = ' | '.join(explicacao_parts) if explicacao_parts else 'Explicação não disponível'
                    dificuldade = row.get('dificuldade', 'Média').strip()
                    
                    cursor.execute('''
                        INSERT OR IGNORE INTO questoes 
                        (enunciado, materia, alternativas, resposta_correta, explicacao, dificuldade)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (enunciado, materia, json.dumps(alternativas_dict), resposta_correta, explicacao, dificuldade))
                    
                except Exception as e:
                    continue
        
        conn.commit()
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
        return render_template('simulado-simple.html', materias=['Língua Portuguesa', 'Matemática', 'Raciocínio Lógico'])

@app.route('/questao/<int:numero>')
def questao(numero):
    '''Página REAL da questão com todas as funcionalidades'''
    if 'simulado_ativo' not in session:
        return render_template('erro.html', mensagem='Simulado não iniciado. <a href=\"/simulado\">Iniciar simulado</a>')
    
    if numero < 1 or numero > len(session['questoes']):
        return render_template('erro.html', mensagem='Questão não encontrada.')
    
    questao_atual = session['questoes'][numero - 1]
    
    return render_template('questao.html',
                         numero=numero,
                         total_questoes=len(session['questoes']),
                         questao=questao_atual)

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    '''API para iniciar simulado - VERSÃO COMPLETA'''
    try:
        data = request.get_json()
        quantidade = data.get('quantidade', 5)
        materias = data.get('materias', [])
        
        print(f'🚀 Iniciando simulado: {quantidade} questões, matérias: {materias}')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if not materias:
            cursor.execute('SELECT * FROM questoes ORDER BY RANDOM() LIMIT ?', (quantidade,))
        else:
            placeholders = ','.join(['?'] * len(materias))
            query = f'SELECT * FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
            cursor.execute(query, materias + [quantidade])
        
        questoes_db = cursor.fetchall()
        conn.close()
        
        if not questoes_db:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 404
        
        # Formatar questões - CORRETO
        questoes = []
        for q in questoes_db:
            try:
                alternativas = json.loads(q['alternativas'])
            except:
                alternativas = {'A': 'Alternativa A', 'B': 'Alternativa B', 'C': 'Alternativa C', 'D': 'Alternativa D'}
            
            questao_formatada = {
                'id': q['id'],
                'enunciado': q['enunciado'],
                'materia': q['materia'],
                'alternativas': alternativas,
                'resposta_correta': q['resposta_correta'],
                'explicacao': q['explicacao'],
                'dificuldade': q['dificuldade'] if 'dificuldade' in q.keys() else 'Média'
            }
                
            questoes.append(questao_formatada)
        
        # Configurar sessão COMPLETA
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

@app.route('/api/simulado/responder', methods=['POST'])
def responder_questao():
    '''Salvar resposta da questão'''
    try:
        if 'simulado_ativo' not in session:
            return jsonify({'success': False, 'error': 'Simulado não iniciado'}), 400
        
        data = request.get_json()
        questao_numero = data.get('questao_numero')
        resposta = data.get('resposta')
        
        session['respostas'][str(questao_numero)] = resposta
        session.modified = True
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f'❌ Erro ao salvar resposta: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/resposta/<int:numero>')
def obter_resposta(numero):
    '''Obter resposta salva da questão'''
    try:
        if 'simulado_ativo' not in session:
            return jsonify({'resposta': None})
        
        resposta = session['respostas'].get(str(numero))
        return jsonify({'resposta': resposta})
        
    except Exception as e:
        print(f'❌ Erro ao obter resposta: {e}')
        return jsonify({'resposta': None})

@app.route('/simulado/resultado')
def resultado_simulado():
    '''Página de resultado COMPLETA'''
    if 'simulado_ativo' not in session:
        return render_template('erro.html', mensagem='Nenhum simulado em andamento.')
    
    # Calcular resultados
    respostas = session.get('respostas', {})
    questoes = session['questoes']
    
    corretas = 0
    revisao = []
    
    for i, questao in enumerate(questoes, 1):
        resposta_usuario = respostas.get(str(i))
        resposta_correta = questao['resposta_correta']
        correta = resposta_usuario == resposta_correta
        
        if correta:
            corretas += 1
        
        revisao.append({
            'numero': i,
            'enunciado': questao['enunciado'],
            'materia': questao['materia'],
            'resposta_usuario': resposta_usuario or 'Não respondida',
            'resposta_correta': resposta_correta,
            'correta': correta,
            'explicacao': questao['explicacao']
        })
    
    total_questoes = len(questoes)
    porcentagem = (corretas / total_questoes) * 100 if total_questoes > 0 else 0
    erradas = total_questoes - corretas
    
    # Calcular tempo
    inicio = datetime.fromisoformat(session['inicio'])
    fim = datetime.now()
    tempo_segundos = (fim - inicio).total_seconds()
    tempo_minutos = tempo_segundos / 60
    
    # Feedback
    if porcentagem >= 80:
        feedback = '🎉 Excelente! Seu desempenho foi ótimo!'
    elif porcentagem >= 60:
        feedback = '👍 Bom trabalho! Continue estudando!'
    elif porcentagem >= 40:
        feedback = '💪 Está no caminho certo! Revise os conteúdos.'
    else:
        feedback = '📚 Hora de reforçar os estudos!'
    
    # Limpar sessão do simulado
    session.pop('simulado_ativo', None)
    session.pop('questoes', None)
    session.pop('respostas', None)
    session.pop('inicio', None)
    
    return render_template('resultado.html',
                         total_questoes=total_questoes,
                         corretas=corretas,
                         erradas=erradas,
                         porcentagem=porcentagem,
                         tempo_minutos=tempo_minutos,
                         feedback=feedback,
                         revisao=revisao)

@app.route('/redacao')
def redacao():
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Template de erro simples
@app.route('/erro')
def erro():
    mensagem = request.args.get('mensagem', 'Ocorreu um erro.')
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Erro - ConcursoMaster</title>
        <style>
            body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; background: #f5f6fa; }}
            .container {{ max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
            .erro {{ color: #e74c3c; font-size: 24px; margin: 20px 0; }}
            .btn {{ background: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block; margin: 10px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="erro">❌ {mensagem}</div>
            <a href="/" class="btn">🏠 Página Inicial</a>
        </div>
    </body>
    </html>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
