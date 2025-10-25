from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'corrigido_2024'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24
app.config['TEMPLATES_AUTO_RELOAD'] = True

DATABASE = 'concurso.db'

def debug_log(message):
    timestamp = datetime.now().strftime('%H:%M:%S')
    print(f'🔍 [{timestamp}] {message}')

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    try:
        debug_log('Iniciando banco de dados...')
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                enunciado TEXT NOT NULL,
                materia TEXT NOT NULL,
                alternativas TEXT NOT NULL,
                resposta_correta TEXT NOT NULL,
                explicacao TEXT,
                dica TEXT,
                formula TEXT
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM questoes')
        count = cursor.fetchone()[0]
        
        if count == 0:
            debug_log('Criando questões de exemplo...')
            criar_questoes_exemplo()
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        debug_log(f'Erro no banco: {e}')
        return False

def criar_questoes_exemplo():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        exemplos = [
            {
                'enunciado': 'Qual é a capital do Brasil?',
                'materia': 'Geografia',
                'alternativas': {'A': 'Rio de Janeiro', 'B': 'Brasília', 'C': 'São Paulo', 'D': 'Salvador'},
                'resposta': 'B',
                'explicacao': 'Brasília foi escolhida como capital federal em 1960.',
                'dica': '💡 Pense na cidade planejada para ser a capital',
                'formula': ''
            },
            {
                'enunciado': '2 + 2 é igual a:',
                'materia': 'Matemática', 
                'alternativas': {'A': '3', 'B': '4', 'C': '5', 'D': '6'},
                'resposta': 'B',
                'explicacao': 'Operação básica de adição: 2 + 2 = 4.',
                'dica': '💡 É uma operação fundamental da matemática',
                'formula': '📐 a + b = c'
            },
            {
                'enunciado': 'Qual artigo define os direitos fundamentais na Constituição?',
                'materia': 'Direito Constitucional',
                'alternativas': {'A': 'Artigo 1º', 'B': 'Artigo 5º', 'C': 'Artigo 10º', 'D': 'Artigo 15º'},
                'resposta': 'B', 
                'explicacao': 'O Artigo 5º da Constituição trata dos direitos e garantias fundamentais.',
                'dica': '💡 Pense no artigo que trata de direitos individuais',
                'formula': ''
            }
        ]
        
        for ex in exemplos:
            cursor.execute('''
                INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao, dica, formula)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                ex['enunciado'],
                ex['materia'],
                json.dumps(ex['alternativas']),
                ex['resposta'],
                ex['explicacao'],
                ex['dica'],
                ex['formula']
            ))
        
        conn.commit()
        conn.close()
        debug_log(f'✅ {len(exemplos)} questões de exemplo criadas')
        return True
        
    except Exception as e:
        debug_log(f'Erro ao criar exemplos: {e}')
        return False

# ========== ROTAS PRINCIPAIS ==========

@app.route('/')
def index():
    debug_log('📄 GET /')
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    debug_log('🎯 GET /simulado')
    try:
        if not init_database():
            return render_template('error.html', mensagem='Erro ao carregar banco')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT materia, COUNT(*) as total FROM questoes GROUP BY materia ORDER BY materia')
        materias_db = cursor.fetchall()
        conn.close()
        
        materias = [{'nome': row['materia'], 'total': row['total']} for row in materias_db]
        return render_template('simulado.html', materias=materias)
        
    except Exception as e:
        debug_log(f'Erro em /simulado: {e}')
        return render_template('error.html', mensagem='Erro ao carregar')

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    debug_log('🚀 POST /api/simulado/iniciar')
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Dados não fornecidos'}), 400
        
        quantidade = int(data.get('quantidade', 10))
        materias_selecionadas = data.get('materias', [])
        configs = data.get('configs', {})
        
        debug_log(f'Config: {quantidade} questões, {len(materias_selecionadas)} matérias')
        
        if not materias_selecionadas:
            return jsonify({'success': False, 'error': 'Selecione pelo menos uma matéria'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?'] * len(materias_selecionadas))
        query = f'SELECT id FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
        
        cursor.execute(query, materias_selecionadas + [quantidade])
        questao_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        debug_log(f'Questões encontradas: {len(questao_ids)}')
        
        if not questao_ids:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 404
        
        session.clear()
        session['simulado_ativo'] = True
        session['questoes_ids'] = questao_ids
        session['respostas'] = {}
        session['configs'] = configs
        
        return jsonify({
            'success': True,
            'total_questoes': len(questao_ids),
            'redirect_url': url_for('questao', numero=1)
        })
        
    except Exception as e:
        debug_log(f'Erro ao iniciar simulado: {e}')
        return jsonify({'success': False, 'error': f'Erro interno: {str(e)}'}), 500

@app.route('/questao/<int:numero>')
def questao(numero):
    debug_log(f'📖 GET /questao/{numero}')
    
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    questao_ids = session.get('questoes_ids', [])
    if numero < 1 or numero > len(questao_ids):
        return render_template('error.html', mensagem='Questão não encontrada')
    
    try:
        questao_id = questao_ids[numero-1]
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
        questao_db = cursor.fetchone()
        conn.close()
        
        if not questao_db:
            return render_template('error.html', mensagem='Questão não encontrada')
        
        alternativas = json.loads(questao_db['alternativas'])
        resposta_usuario = session.get('respostas', {}).get(str(numero))
        configs = session.get('configs', {})
        
        questao_data = {
            'enunciado': questao_db['enunciado'],
            'materia': questao_db['materia'],
            'alternativas': alternativas,
            'resposta_correta': questao_db['resposta_correta'],
            'explicacao': questao_db['explicacao'],
            'dica': questao_db['dica'] if configs.get('dicasAutomaticas', True) else '',
            'formula': questao_db['formula'] if configs.get('formulasMatematicas', True) else ''
        }
        
        return render_template('questao.html',
                             numero=numero,
                             total_questoes=len(questao_ids),
                             questao=questao_data,
                             resposta_usuario=resposta_usuario,
                             configs=configs,
                             questao_respondida=resposta_usuario is not None)
        
    except Exception as e:
        debug_log(f'Erro na questão: {e}')
        return render_template('error.html', mensagem='Erro ao carregar questão')

@app.route('/api/questao/responder', methods=['POST'])
def responder_questao():
    debug_log('📝 POST /api/questao/responder')
    
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'success': False, 'error': 'Simulado não iniciado'}), 400
        
        data = request.get_json()
        questao_numero = data.get('questao_numero')
        resposta = data.get('resposta')
        
        if 'respostas' not in session:
            session['respostas'] = {}
        
        session['respostas'][str(questao_numero)] = resposta
        session.modified = True
        
        return jsonify({'success': True})
        
    except Exception as e:
        debug_log(f'Erro ao salvar resposta: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/resultado')
def resultado():
    debug_log('📊 GET /resultado')
    
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    try:
        questao_ids = session.get('questoes_ids', [])
        respostas = session.get('respostas', {})
        
        acertos = 0
        detalhes_questoes = []
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for i, questao_id in enumerate(questao_ids, 1):
            cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
            questao_db = cursor.fetchone()
            
            if questao_db:
                resposta_usuario = respostas.get(str(i))
                resposta_correta = questao_db['resposta_correta']
                acertou = resposta_usuario == resposta_correta
                
                if acertou:
                    acertos += 1
                
                alternativas = json.loads(questao_db['alternativas'])
                detalhes_questoes.append({
                    'numero': i,
                    'enunciado': questao_db['enunciado'],
                    'materia': questao_db['materia'],
                    'resposta_usuario': resposta_usuario,
                    'resposta_correta': resposta_correta,
                    'acertou': acertou,
                    'explicacao': questao_db['explicacao'],
                    'alternativas': alternativas
                })
        
        conn.close()
        
        total_questoes = len(questao_ids)
        porcentagem_acertos = (acertos / total_questoes) * 100 if total_questoes > 0 else 0
        
        session.clear()
        
        return render_template('resultado.html',
                             total_questoes=total_questoes,
                             acertos=acertos,
                             erros=total_questoes - acertos,
                             porcentagem=porcentagem_acertos,
                             tempo_minutos=5.0,
                             desempenho='Bom' if porcentagem_acertos >= 70 else 'Regular',
                             cor_desempenho='success' if porcentagem_acertos >= 70 else 'warning',
                             detalhes_questoes=detalhes_questoes)
        
    except Exception as e:
        debug_log(f'Erro no resultado: {e}')
        return render_template('error.html', mensagem='Erro ao calcular resultado')

@app.route('/redacao')
def redacao():
    debug_log('📝 GET /redacao')
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    debug_log('📈 GET /dashboard')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM questoes')
        total_questoes = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(DISTINCT materia) as total FROM questoes')
        total_materias = cursor.fetchone()['total']
        
        cursor.execute('SELECT materia, COUNT(*) as total FROM questoes GROUP BY materia ORDER BY total DESC LIMIT 5')
        top_materias = cursor.fetchall()
        
        conn.close()
        
        return render_template('dashboard.html',
                             total_questoes=total_questoes,
                             total_materias=total_materias,
                             total_simulados=0,
                             top_materias=top_materias,
                             historico=[])
        
    except Exception as e:
        debug_log(f'Erro no dashboard: {e}')
        return render_template('error.html', mensagem='Erro ao carregar dashboard')

@app.route('/debug')
def debug():
    debug_log('🔧 GET /debug')
    
    info = {
        'sessao': dict(session),
        'questoes_no_banco': 0,
        'materias_disponiveis': []
    }
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM questoes')
        info['questoes_no_banco'] = cursor.fetchone()['total']
        
        cursor.execute('SELECT DISTINCT materia FROM questoes')
        info['materias_disponiveis'] = [row['materia'] for row in cursor.fetchall()]
        
        conn.close()
    except Exception as e:
        info['erro_banco'] = str(e)
    
    return jsonify(info)

@app.route('/debug/reset')
def debug_reset():
    debug_log('🔄 GET /debug/reset')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM questoes')
        conn.commit()
        conn.close()
        
        session.clear()
        init_database()
        
        return jsonify({'success': True, 'message': 'Sistema resetado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug_log(f'🚀 Servidor iniciado na porta {port}')
    app.run(host='0.0.0.0', port=port, debug=False)
