from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'concurso_master_premium_2024_final'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600 * 24

DATABASE = 'concurso.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
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
                dica TEXT,
                formula TEXT
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM questoes')
        count = cursor.fetchone()[0]
        
        if count == 0:
            load_questions()
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f'Erro no banco: {e}')
        return False

def load_questions():
    if not os.path.exists('questoes.csv'):
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            
            for row in csv_reader:
                try:
                    enunciado = row.get('enunciado', '').strip()
                    materia = row.get('disciplina', 'Geral').strip()
                    
                    if not enunciado:
                        continue
                    
                    alternativas = {
                        'A': row.get('alt_a', 'Alternativa A').strip(),
                        'B': row.get('alt_b', 'Alternativa B').strip(),
                        'C': row.get('alt_c', 'Alternativa C').strip(),
                        'D': row.get('alt_d', 'Alternativa D').strip()
                    }
                    
                    resposta_correta = row.get('gabarito', 'A').strip().upper()
                    
                    # Sistema de dicas premium
                    dica = generate_hint(materia)
                    formula = generate_formula(materia)
                    
                    explicacao = f"Resposta correta: {resposta_correta}"
                    
                    cursor.execute('''
                        INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao, dica, formula)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (enunciado, materia, json.dumps(alternativas), resposta_correta, explicacao, dica, formula))
                    
                except Exception:
                    continue
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f'Erro ao carregar CSV: {e}')
        return False

def generate_hint(materia):
    hints = {
        'Matematica': '💡 Dica: Reveja os conceitos basicos e formulas relacionadas',
        'Portugues': '💡 Dica: Atencao a concordancia e regras gramaticais', 
        'Raciocinio': '💡 Dica: Identifique padroes e use eliminacao',
        'Direito': '💡 Dica: Lembre-se dos principios fundamentais'
    }
    
    for key, hint in hints.items():
        if key.lower() in materia.lower():
            return hint
    
    return '💡 Dica: Leia atentamente o enunciado'

def generate_formula(materia):
    formulas = {
        'Matematica': '📐 Formula: A = πr² (Area do circulo)',
        'Raciocinio': '🎯 Formula: P(A) = n(A)/n(S) (Probabilidade)'
    }
    
    for key, formula in formulas.items():
        if key.lower() in materia.lower():
            return formula
    
    return ''

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    try:
        init_database()
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT materia FROM questoes')
        materias = [row['materia'] for row in cursor.fetchall()]
        conn.close()
        
        return render_template('simulado.html', materias=[{'nome': m, 'total': 10} for m in materias])
        
    except Exception as e:
        return render_template('error.html', mensagem='Erro ao carregar')

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    try:
        data = request.get_json()
        quantidade = int(data.get('quantidade', 10))
        materias = data.get('materias', [])
        configs = data.get('configs', {})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if not materias:
            cursor.execute('SELECT id FROM questoes ORDER BY RANDOM() LIMIT ?', (quantidade,))
        else:
            placeholders = ','.join(['?'] * len(materias))
            query = f'SELECT id FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
            cursor.execute(query, materias + [quantidade])
        
        questao_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        session.clear()
        session['simulado_ativo'] = True
        session['questoes_ids'] = questao_ids
        session['respostas'] = {}
        session['configs'] = configs
        
        return jsonify({
            'success': True,
            'redirect_url': url_for('questao', numero=1)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/questao/<int:numero>')
def questao(numero):
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    questao_ids = session.get('questoes_ids', [])
    if numero < 1 or numero > len(questao_ids):
        return render_template('error.html', mensagem='Questao nao encontrada')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_ids[numero-1],))
        questao_db = cursor.fetchone()
        conn.close()
        
        if not questao_db:
            return render_template('error.html', mensagem='Questao nao encontrada')
        
        alternativas = json.loads(questao_db['alternativas'])
        resposta_usuario = session.get('respostas', {}).get(str(numero))
        configs = session.get('configs', {})
        
        questao_data = {
            'enunciado': questao_db['enunciado'],
            'materia': questao_db['materia'],
            'alternativas': alternativas,
            'resposta_correta': questao_db['resposta_correta'],
            'explicacao': questao_db['explicacao'],
            'dica': questao_db['dica'] if configs.get('dicasAutomaticas') else '',
            'formula': questao_db['formula'] if configs.get('formulasMatematicas') else ''
        }
        
        return render_template('questao_premium.html',
                             numero=numero,
                             total_questoes=len(questao_ids),
                             questao=questao_data,
                             resposta_usuario=resposta_usuario,
                             configs=configs,
                             questao_respondida=resposta_usuario is not None)
        
    except Exception as e:
        return render_template('error.html', mensagem='Erro ao carregar questao')

@app.route('/api/questao/responder', methods=['POST'])
def responder_questao():
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'success': False}), 400
        
        data = request.get_json()
        questao_numero = data.get('questao_numero')
        resposta = data.get('resposta')
        
        if 'respostas' not in session:
            session['respostas'] = {}
        
        session['respostas'][str(questao_numero)] = resposta
        session.modified = True
        
        return jsonify({'success': True})
        
    except Exception:
        return jsonify({'success': False}), 500

@app.route('/resultado')
def resultado():
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    try:
        questao_ids = session.get('questoes_ids', [])
        respostas = session.get('respostas', {})
        
        acertos = 0
        for i, questao_id in enumerate(questao_ids, 1):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT resposta_correta FROM questoes WHERE id = ?', (questao_id,))
            questao = cursor.fetchone()
            conn.close()
            
            if questao and respostas.get(str(i)) == questao['resposta_correta']:
                acertos += 1
        
        total = len(questao_ids)
        porcentagem = (acertos / total) * 100
        
        session.clear()
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head><title>Resultado</title></head>
        <body style="font-family: Arial; padding: 20px; text-align: center;">
            <h1>🎉 Resultado do Simulado</h1>
            <h2>{porcentagem:.1f}% de acertos</h2>
            <p>Você acertou {acertos} de {total} questões</p>
            <a href="/simulado" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Novo Simulado</a>
        </body>
        </html>
        '''
        
    except Exception as e:
        return render_template('error.html', mensagem='Erro ao calcular resultado')

@app.route('/redacao')
def redacao():
    return render_template('redacao_premium.html')

@app.route('/dashboard')
def dashboard():
    return '<h1>Dashboard - Em desenvolvimento</h1><a href="/">Voltar</a>'

@app.route('/materiais')
def materiais():
    return '<h1>Materiais - Em desenvolvimento</h1><a href="/">Voltar</a>'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"🚀 CONCURSOMASTER AI PREMIUM - Porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
