from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import sqlite3
import json
import os
import csv
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'concurso_master_premium_2024_secret'
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
                enunciado TEXT NOT NULL,
                materia TEXT NOT NULL,
                alternativas TEXT NOT NULL,
                resposta_correta TEXT NOT NULL,
                explicacao TEXT,
                dica TEXT,
                formula TEXT,
                dificuldade TEXT DEFAULT 'Media',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resultados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_questoes INTEGER,
                acertos INTEGER,
                porcentagem REAL,
                tempo_gasto REAL,
                data_simulado TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                configs TEXT
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS redacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                titulo TEXT,
                texto TEXT,
                nota INTEGER,
                feedback TEXT,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM questoes')
        count = cursor.fetchone()[0]
        
        if count == 0:
            print('Carregando questões premium...')
            load_questions_premium()
        else:
            print(f'{count} questões premium no banco')
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f'Erro no banco: {e}')
        return False

def load_questions_premium():
    if not os.path.exists('questoes.csv'):
        print('Arquivo questoes.csv nao encontrado')
        return False
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        with open('questoes.csv', 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            questions_loaded = 0
            
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
                    dica = generate_hint(materia, enunciado)
                    formula = generate_formula(materia, enunciado)
                    
                    explicacao_parts = []
                    if row.get('just_a'): explicacao_parts.append(f"A: {row['just_a']}")
                    if row.get('just_b'): explicacao_parts.append(f"B: {row['just_b']}")
                    if row.get('just_c'): explicacao_parts.append(f"C: {row['just_c']}")
                    if row.get('just_d'): explicacao_parts.append(f"D: {row['just_d']}")
                    if row.get('dica_interpretacao'): explicacao_parts.append(f"Dica: {row['dica_interpretacao']}")
                    
                    explicacao = ' | '.join(explicacao_parts) if explicacao_parts else 'Explicacao detalhada nao disponivel'
                    
                    cursor.execute('''
                        INSERT INTO questoes (enunciado, materia, alternativas, resposta_correta, explicacao, dica, formula)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (enunciado, materia, json.dumps(alternativas), resposta_correta, explicacao, dica, formula))
                    
                    questions_loaded += 1
                    
                except Exception as e:
                    continue
        
        conn.commit()
        conn.close()
        print(f'{questions_loaded} questões premium carregadas')
        return True
        
    except Exception as e:
        print(f'Erro ao carregar CSV: {e}')
        return False

def generate_hint(materia, enunciado):
    hints = {
        'Matematica': [
            "Dica: Reveja os conceitos basicos da operacao",
            "Analise cuidadosamente cada alternativa",
            "Verifique se ha necessidade de usar formulas especificas"
        ],
        'Portugues': [
            "Atencao a concordancia verbal e nominal",
            "Analise o contexto da frase",
            "Lembre-se das regras gramaticais aplicaveis"
        ],
        'Raciocinio': [
            "Quebre o problema em partes menores",
            "Identifique padroes e sequencias",
            "Use o processo de eliminacao"
        ]
    }
    
    for key, hint_list in hints.items():
        if key.lower() in materia.lower():
            return random.choice(hint_list)
    
    return "Dica: Leia atentamente o enunciado e analise cada alternativa"

def generate_formula(materia, enunciado):
    formulas = {
        'Matematica': [
            "Area do circulo: A = πr²",
            "Teorema de Pitagoras: a² + b² = c²",
            "Regra de tres: a/b = c/d",
            "Juros simples: J = C × i × t"
        ],
        'Raciocinio': [
            "Probabilidade: P(A) = n(A)/n(S)",
            "Principio fundamental da contagem",
            "Permutacao: Pₙ = n!"
        ]
    }
    
    for key, formula_list in formulas.items():
        if key.lower() in materia.lower():
            return random.choice(formula_list)
    
    return ""

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    try:
        init_database()
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DISTINCT materia, COUNT(*) as total 
            FROM questoes 
            WHERE materia IS NOT NULL 
            GROUP BY materia 
            ORDER BY total DESC
        ''')
        materias_db = cursor.fetchall()
        conn.close()
        
        materias = [{'nome': row['materia'], 'total': row['total']} for row in materias_db]
        
        return render_template('simulado.html', materias=materias)
        
    except Exception as e:
        print(f'Erro no simulado: {e}')
        return render_template('error.html', mensagem='Erro ao carregar configuracoes')

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    try:
        data = request.get_json()
        quantidade = int(data.get('quantidade', 30))
        materias_selecionadas = data.get('materias', [])
        configs = data.get('configs', {})
        
        print(f'Iniciando simulado: {quantidade} questões')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if not materias_selecionadas:
            cursor.execute('SELECT id FROM questoes ORDER BY RANDOM() LIMIT ?', (quantidade,))
        else:
            placeholders = ','.join(['?'] * len(materias_selecionadas))
            query = f'SELECT id FROM questoes WHERE materia IN ({placeholders}) ORDER BY RANDOM() LIMIT ?'
            cursor.execute(query, materias_selecionadas + [quantidade])
        
        questao_ids = [row['id'] for row in cursor.fetchall()]
        conn.close()
        
        if not questao_ids:
            return jsonify({'success': False, 'error': 'Nenhuma questao encontrada'}), 404
        
        session.clear()
        session['simulado_ativo'] = True
        session['questoes_ids'] = questao_ids
        session['respostas'] = {}
        session['configs'] = configs
        session['inicio_simulado'] = datetime.now().isoformat()
        
        print(f'Simulado com {len(questao_ids)} questões iniciado!')
        
        return jsonify({
            'success': True,
            'total_questoes': len(questao_ids),
            'redirect_url': url_for('questao', numero=1)
        })
        
    except Exception as e:
        print(f'Erro ao iniciar simulado: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/questao/<int:numero>')
def questao(numero):
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    questao_ids = session.get('questoes_ids', [])
    total_questoes = len(questao_ids)
    configs = session.get('configs', {})
    
    if numero < 1 or numero > total_questoes:
        return render_template('error.html', mensagem='Questao nao encontrada')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_ids[numero-1],))
        questao_db = cursor.fetchone()
        
        if not questao_db:
            return render_template('error.html', mensagem='Questao nao encontrada')
        
        alternativas = json.loads(questao_db['alternativas'])
        resposta_usuario = session.get('respostas', {}).get(str(numero))
        
        questao_data = {
            'id': questao_db['id'],
            'enunciado': questao_db['enunciado'],
            'materia': questao_db['materia'],
            'alternativas': alternativas,
            'resposta_correta': questao_db['resposta_correta'],
            'explicacao': questao_db['explicacao'],
            'dica': questao_db['dica'],
            'formula': questao_db['formula'],
            'dificuldade': questao_db['dificuldade']
        }
        
        conn.close()
        
        return render_template('questao_premium.html',
                             numero=numero,
                             total_questoes=total_questoes,
                             questao=questao_data,
                             resposta_usuario=resposta_usuario,
                             configs=configs,
                             questao_respondida=resposta_usuario is not None)
        
    except Exception as e:
        print(f'Erro ao carregar questao: {e}')
        return render_template('error.html', mensagem='Erro ao carregar questao')

@app.route('/api/questao/responder', methods=['POST'])
def responder_questao():
    try:
        if not session.get('simulado_ativo'):
            return jsonify({'success': False, 'error': 'Simulado nao iniciado'}), 400
        
        data = request.get_json()
        questao_numero = data.get('questao_numero')
        resposta = data.get('resposta')
        
        if not questao_numero or not resposta:
            return jsonify({'success': False, 'error': 'Dados invalidos'}), 400
        
        if 'respostas' not in session:
            session['respostas'] = {}
        
        session['respostas'][str(questao_numero)] = resposta
        session.modified = True
        
        return jsonify({'success': True})
        
    except Exception as e:
        print(f'Erro ao registrar resposta: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/resultado')
def resultado():
    if not session.get('simulado_ativo'):
        return redirect(url_for('simulado'))
    
    try:
        questao_ids = session.get('questoes_ids', [])
        respostas = session.get('respostas', {})
        configs = session.get('configs', {})
        inicio_simulado = datetime.fromisoformat(session.get('inicio_simulado'))
        
        acertos = 0
        detalhes_questoes = []
        desempenho_por_materia = {}
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        for i, questao_id in enumerate(questao_ids, 1):
            cursor.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,))
            questao_db = cursor.fetchone()
            
            if questao_db:
                resposta_usuario = respostas.get(str(i))
                resposta_correta = questao_db['resposta_correta']
                acertou = resposta_usuario == resposta_correta
                materia = questao_db['materia']
                
                if acertou:
                    acertos += 1
                
                if materia not in desempenho_por_materia:
                    desempenho_por_materia[materia] = {'total': 0, 'acertos': 0}
                
                desempenho_por_materia[materia]['total'] += 1
                if acertou:
                    desempenho_por_materia[materia]['acertos'] += 1
                
                alternativas = json.loads(questao_db['alternativas'])
                
                detalhes_questoes.append({
                    'numero': i,
                    'enunciado': questao_db['enunciado'],
                    'materia': materia,
                    'resposta_usuario': resposta_usuario,
                    'resposta_correta': resposta_correta,
                    'acertou': acertou,
                    'explicacao': questao_db['explicacao'],
                    'alternativas': alternativas,
                    'dificuldade': questao_db['dificuldade']
                })
        
        total_questoes = len(questao_ids)
        porcentagem_acertos = (acertos / total_questoes) * 100 if total_questoes > 0 else 0
        tempo_total = (datetime.now() - inicio_simulado).total_seconds()
        
        if porcentagem_acertos >= 90:
            desempenho = 'Excelente 🎉'
            cor_desempenho = 'success'
        elif porcentagem_acertos >= 70:
            desempenho = 'Bom 👍'
            cor_desempenho = 'info'
        elif porcentagem_acertos >= 50:
            desempenho = 'Regular 💪'
            cor_desempenho = 'warning'
        else:
            desempenho = 'Precisa melhorar 📚'
            cor_desempenho = 'danger'
        
        cursor.execute('''
            INSERT INTO resultados (total_questoes, acertos, porcentagem, tempo_gasto, configs)
            VALUES (?, ?, ?, ?, ?)
        ''', (total_questoes, acertos, porcentagem_acertos, tempo_total, json.dumps(configs)))
        conn.commit()
        conn.close()
        
        session.pop('simulado_ativo', None)
        session.pop('questoes_ids', None)
        session.pop('respostas', None)
        session.pop('inicio_simulado', None)
        session.pop('configs', None)
        
        return render_template('resultado_premium.html',
                             total_questoes=total_questoes,
                             acertos=acertos,
                             erros=total_questoes - acertos,
                             porcentagem=porcentagem_acertos,
                             tempo_minutos=tempo_total / 60,
                             desempenho=desempenho,
                             cor_desempenho=cor_desempenho,
                             desempenho_por_materia=desempenho_por_materia,
                             detalhes_questoes=detalhes_questoes)
        
    except Exception as e:
        print(f'Erro ao calcular resultados: {e}')
        return render_template('error.html', mensagem='Erro ao processar resultados')

@app.route('/redacao')
def redacao():
    return render_template('redacao_premium.html')

@app.route('/api/redacao/corrigir', methods=['POST'])
def corrigir_redacao():
    try:
        data = request.get_json()
        titulo = data.get('titulo', '')
        texto = data.get('texto', '')
        
        if not texto.strip():
            return jsonify({'success': False, 'error': 'Texto da redacao nao pode estar vazio'})
        
        palavras = len(texto.split())
        paragrafos = texto.count('\n\n') + 1
        
        nota = max(100, min(1000, palavras * 2))
        feedback = generate_writing_feedback(texto, palavras, paragrafos)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO redacoes (titulo, texto, nota, feedback)
            VALUES (?, ?, ?, ?)
        ''', (titulo, texto, nota, feedback))
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'nota': nota,
            'feedback': feedback,
            'estatisticas': {
                'palavras': palavras,
                'paragrafos': paragrafos,
                'caracteres': len(texto)
            }
        })
        
    except Exception as e:
        print(f'Erro ao corrigir redacao: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

def generate_writing_feedback(texto, palavras, paragrafos):
    feedback_parts = []
    
    if paragrafos < 4:
        feedback_parts.append("Estrutura: Considere dividir seu texto em 4-5 paragrafos")
    else:
        feedback_parts.append("Estrutura: Boa organizacao em paragrafos!")
    
    if palavras < 200:
        feedback_parts.append("Tamanho: Seu texto esta muito curto")
    elif palavras > 800:
        feedback_parts.append("Tamanho: Seu texto esta muito longo")
    else:
        feedback_parts.append("Tamanho: Tamanho adequado")
    
    feedback_parts.extend([
        "Dica: Revise a concordancia verbal e nominal",
        "Dica: Use conectivos para melhorar a coesao",
        "Dica: Evite repeticoes de palavras"
    ])
    
    return "\n\n".join(feedback_parts)

@app.route('/dashboard')
def dashboard():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as total FROM questoes')
        total_questoes = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(DISTINCT materia) as total FROM questoes')
        total_materias = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total FROM resultados')
        total_simulados = cursor.fetchone()['total']
        
        cursor.execute('SELECT COUNT(*) as total, materia FROM questoes GROUP BY materia ORDER BY total DESC LIMIT 5')
        top_materias = cursor.fetchall()
        
        cursor.execute('SELECT * FROM resultados ORDER BY data_simulado DESC LIMIT 10')
        historico = cursor.fetchall()
        
        cursor.execute('SELECT AVG(porcentagem) as media_geral, MAX(porcentagem) as melhor_desempenho FROM resultados')
        stats = cursor.fetchone()
        
        conn.close()
        
        return render_template('dashboard_premium.html',
                             total_questoes=total_questoes,
                             total_materias=total_materias,
                             total_simulados=total_simulados,
                             top_materias=top_materias,
                             historico=historico,
                             stats=stats)
        
    except Exception as e:
        print(f'Erro no dashboard: {e}')
        return render_template('error.html', mensagem='Erro ao carregar dashboard')

@app.route('/materiais')
def materiais():
    return render_template('materiais.html')

@app.errorhandler(404)
def pagina_nao_encontrada(e):
    return render_template('error.html', mensagem='Pagina nao encontrada'), 404

@app.errorhandler(500)
def erro_interno(e):
    return render_template('error.html', mensagem='Erro interno do servidor'), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    print(f"Servidor ConcursoMaster AI Premium iniciado na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
