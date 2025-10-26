from flask import Flask, render_template, request, jsonify, session
import sqlite3
import json
import random
import time
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'concurso_master_secret_key_v4'
app.config['SESSION_TYPE'] = 'filesystem'

def get_db_connection():
    conn = sqlite3.connect('concurso.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    
    # Tabela de questões
    conn.execute('''
        CREATE TABLE IF NOT EXISTS questoes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            disciplina TEXT NOT NULL,
            materia TEXT NOT NULL,
            enunciado TEXT NOT NULL,
            alternativas TEXT NOT NULL,
            resposta_correta TEXT NOT NULL,
            dificuldade TEXT CHECK(dificuldade IN ('Fácil', 'Médio', 'Difícil')) DEFAULT 'Médio',
            justificativa TEXT,
            dica TEXT,
            formula TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de histórico de simulados
    conn.execute('''
        CREATE TABLE IF NOT EXISTS historico_simulados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            simulado_id TEXT NOT NULL UNIQUE,
            config TEXT NOT NULL,
            respostas TEXT NOT NULL,
            relatorio TEXT NOT NULL,
            data_inicio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_fim TIMESTAMP,
            tempo_total_minutos REAL DEFAULT 0
        )
    ''')
    
    # Tabela de temas de redação
    conn.execute('''
        CREATE TABLE IF NOT EXISTS temas_redacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT NOT NULL,
            descricao TEXT NOT NULL,
            tipo TEXT NOT NULL,
            dificuldade TEXT CHECK(dificuldade IN ('Fácil', 'Médio', 'Difícil')) DEFAULT 'Médio',
            palavras_chave TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Verificar se existem questões
    cursor = conn.execute('SELECT COUNT(*) as count FROM questoes')
    count = cursor.fetchone()['count']
    
    if count == 0:
        print("Inserindo questões de exemplo...")
        
        questões_exemplo = [
            {
                'disciplina': 'Matemática',
                'materia': 'Álgebra',
                'enunciado': 'Qual é o valor de x na equação 2x + 5 = 15?',
                'alternativas': {'A': '5', 'B': '10', 'C': '7', 'D': '8'},
                'resposta_correta': 'A',
                'dificuldade': 'Fácil',
                'justificativa': 'Para resolver a equação 2x + 5 = 15, subtraímos 5 de ambos os lados: 2x = 10. Depois dividimos por 2: x = 5.',
                'dica': 'Lembre-se de isolar a variável x realizando as operações inversas.',
                'formula': '2x + 5 = 15 → 2x = 15 - 5 → 2x = 10 → x = 10/2 → x = 5'
            },
            {
                'disciplina': 'Português', 
                'materia': 'Gramática',
                'enunciado': 'Assinale a alternativa em que todas as palavras são acentuadas pela mesma regra:',
                'alternativas': {
                    'A': 'café, você, índio',
                    'B': 'saúde, herói, dói', 
                    'C': 'árvore, lâmpada, pêssego',
                    'D': 'cidade, útil, fábrica'
                },
                'resposta_correta': 'B',
                'dificuldade': 'Médio',
                'justificativa': 'Todas as palavras da alternativa B são oxítonas terminadas em ditongo aberto, recebendo acento gráfico.',
                'dica': 'Lembre-se das regras de acentuação para oxítonas, paroxítonas e proparoxítonas.',
                'formula': 'Oxítonas: terminadas em a/as, e/es, o/os, em/ens → acento'
            }
        ]
        
        for questao in questões_exemplo:
            conn.execute('''
                INSERT INTO questoes (disciplina, materia, enunciado, alternativas, resposta_correta, dificuldade, justificativa, dica, formula)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                questao['disciplina'],
                questao['materia'],
                questao['enunciado'],
                json.dumps(questao['alternativas']),
                questao['resposta_correta'],
                questao['dificuldade'],
                questao['justificativa'],
                questao['dica'],
                questao['formula']
            ))
    
    # Verificar temas de redação
    cursor = conn.execute('SELECT COUNT(*) as count FROM temas_redacao')
    count = cursor.fetchone()['count']
    
    if count == 0:
        print("Inserindo temas de redação...")
        
        temas_exemplo = [
            {
                'titulo': 'Os desafios da educação digital no Brasil',
                'descricao': 'Redija uma dissertação sobre os principais desafios para implementação da educação digital no Brasil.',
                'tipo': 'Dissertação',
                'dificuldade': 'Médio',
                'palavras_chave': 'educação digital, tecnologia, desigualdade'
            }
        ]
        
        for tema in temas_exemplo:
            conn.execute('''
                INSERT INTO temas_redacao (titulo, descricao, tipo, dificuldade, palavras_chave)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                tema['titulo'],
                tema['descricao'],
                tema['tipo'],
                tema['dificuldade'],
                tema['palavras_chave']
            ))
    
    conn.commit()
    conn.close()
    print("Banco de dados inicializado com sucesso!")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/simulado')
def simulado():
    return render_template('simulado.html')

@app.route('/redacao')
def redacao():
    return render_template('redacao.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/materias')
def api_materias():
    try:
        conn = get_db_connection()
        
        materias_data = conn.execute('''
            SELECT materia, disciplina, COUNT(*) as total
            FROM questoes 
            GROUP BY materia, disciplina
            ORDER BY disciplina, materia
        ''').fetchall()
        
        materias = []
        estatisticas = {}
        
        for row in materias_data:
            materia = row['materia']
            materias.append(materia)
            estatisticas[materia] = {
                'total': row['total'],
                'disciplina': row['disciplina']
            }
        
        return jsonify({
            'success': True,
            'materias': materias,
            'estatisticas': estatisticas
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/iniciar', methods=['POST'])
def iniciar_simulado():
    try:
        data = request.get_json()
        materias = data.get('materias', [])
        quantidade_total = data.get('quantidade_total', 50)
        tempo_minutos = data.get('tempo_minutos', 180)
        aleatorio = data.get('aleatorio', True)
        
        if not materias:
            return jsonify({'success': False, 'error': 'Nenhuma matéria selecionada'}), 400
        
        simulado_id = f"simulado_{int(time.time())}_{random.randint(1000, 9999)}"
        
        conn = get_db_connection()
        
        placeholders = ','.join(['?'] * len(materias))
        query = f'SELECT * FROM questoes WHERE materia IN ({placeholders})'
        
        if aleatorio:
            query += ' ORDER BY RANDOM()'
        else:
            query += ' ORDER BY materia, dificuldade'
        
        query += ' LIMIT ?'
        
        questões = conn.execute(query, materias + [quantidade_total]).fetchall()
        
        if not questões:
            return jsonify({'success': False, 'error': 'Nenhuma questão encontrada'}), 400
        
        primeira_questao = {
            'id': questões[0]['id'],
            'disciplina': questões[0]['disciplina'],
            'materia': questões[0]['materia'],
            'enunciado': questões[0]['enunciado'],
            'alternativas': json.loads(questões[0]['alternativas']),
            'dificuldade': questões[0]['dificuldade']
        }
        
        if 'user_id' not in session:
            session['user_id'] = f"user_{random.randint(10000, 99999)}"
        
        config_simulado = {
            'materias': materias,
            'quantidade_total': quantidade_total,
            'tempo_minutos': tempo_minutos,
            'aleatorio': aleatorio,
            'questoes_ids': [q['id'] for q in questões],
            'data_inicio': datetime.now().isoformat()
        }
        
        session['simulado_atual'] = {
            'simulado_id': simulado_id,
            'config': config_simulado,
            'respostas': {},
            'questao_atual': 0,
            'iniciado_em': datetime.now().isoformat()
        }
        
        return jsonify({
            'success': True,
            'simulado_id': simulado_id,
            'total_questoes': len(questões),
            'tempo_limite_seg': tempo_minutos * 60,
            'primeira_questao': primeira_questao
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/<simulado_id>/questao/<int:questao_index>')
def get_questao(simulado_id, questao_index):
    try:
        simulado_data = session.get('simulado_atual')
        if not simulado_data or simulado_data['simulado_id'] != simulado_id:
            return jsonify({'success': False, 'error': 'Simulado não encontrado'}), 404
        
        config = simulado_data['config']
        questao_id = config['questoes_ids'][questao_index]
        
        conn = get_db_connection()
        questao = conn.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,)).fetchone()
        
        if not questao:
            return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404
        
        resposta_anterior = None
        respostas = simulado_data.get('respostas', {})
        if str(questao_index) in respostas:
            resposta_anterior = respostas[str(questao_index)]
        
        questao_formatada = {
            'id': questao['id'],
            'disciplina': questao['disciplina'],
            'materia': questao['materia'],
            'enunciado': questao['enunciado'],
            'alternativas': json.loads(questao['alternativas']),
            'dificuldade': questao['dificuldade']
        }
        
        return jsonify({
            'success': True,
            'questao': questao_formatada,
            'resposta_anterior': resposta_anterior
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/<simulado_id>/responder', methods=['POST'])
def responder_questao(simulado_id):
    try:
        data = request.get_json()
        questao_index = data.get('questao_index')
        alternativa = data.get('alternativa')
        tempo_gasto = data.get('tempo_gasto', 0)
        
        simulado_data = session.get('simulado_atual')
        if not simulado_data or simulado_data['simulado_id'] != simulado_id:
            return jsonify({'success': False, 'error': 'Simulado não encontrado'}), 404
        
        config = simulado_data['config']
        questao_id = config['questoes_ids'][questao_index]
        
        conn = get_db_connection()
        questao = conn.execute('SELECT * FROM questoes WHERE id = ?', (questao_id,)).fetchone()
        
        if not questao:
            return jsonify({'success': False, 'error': 'Questão não encontrada'}), 404
        
        acertou = alternativa.upper() == questao['resposta_correta'].upper()
        
        feedback = {
            'acertou': acertou,
            'resposta_correta': questao['resposta_correta'],
            'justificativa': questao['justificativa'],
            'dica': questao['dica'],
            'formula': questao['formula']
        }
        
        if 'respostas' not in simulado_data:
            simulado_data['respostas'] = {}
        
        simulado_data['respostas'][str(questao_index)] = {
            'alternativa': alternativa,
            'tempo_gasto': tempo_gasto,
            'feedbackData': feedback
        }
        
        session.modified = True
        
        return jsonify({
            'success': True,
            **feedback
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/simulado/<simulado_id>/finalizar', methods=['POST'])
def finalizar_simulado(simulado_id):
    try:
        simulado_data = session.get('simulado_atual')
        if not simulado_data or simulado_data['simulado_id'] != simulado_id:
            return jsonify({'success': False, 'error': 'Simulado não encontrado'}), 404
        
        config = simulado_data['config']
        respostas = simulado_data.get('respostas', {})
        
        relatorio = {
            'simulado_id': simulado_id,
            'data': datetime.now().strftime('%Y-%m-%d %H:%M'),
            'geral': {
                'total_questoes': len(config['questoes_ids']),
                'questoes_respondidas': len(respostas),
                'acertos': sum(1 for r in respostas.values() if r['feedbackData']['acertou']),
                'tempo_total_minutos': 0
            }
        }
        
        conn = get_db_connection()
        conn.execute('''
            INSERT INTO historico_simulados 
            (user_id, simulado_id, config, respostas, relatorio, data_fim)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            session.get('user_id', 'anon'),
            simulado_id,
            json.dumps(config),
            json.dumps(respostas),
            json.dumps(relatorio),
            datetime.now().isoformat()
        ))
        conn.commit()
        conn.close()
        
        session.pop('simulado_atual', None)
        
        return jsonify({
            'success': True,
            'relatorio': relatorio
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/redacao/temas')
def get_temas_redacao():
    try:
        conn = get_db_connection()
        temas = conn.execute('SELECT * FROM temas_redacao ORDER BY dificuldade, titulo').fetchall()
        
        temas_list = []
        for tema in temas:
            temas_list.append({
                'id': tema['id'],
                'titulo': tema['titulo'],
                'descricao': tema['descricao'],
                'tipo': tema['tipo'],
                'dificuldade': tema['dificuldade'],
                'palavras_chave': tema['palavras_chave']
            })
        
        return jsonify({
            'success': True,
            'temas': temas_list
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/redacao/corrigir', methods=['POST'])
def corrigir_redacao():
    try:
        data = request.get_json()
        texto = data.get('texto', '')
        tema_id = data.get('tema_id')
        
        palavras = len(texto.split())
        paragrafos = texto.count('\n\n') + 1
        
        competencias = {
            'competencia1': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Bom domínio da norma padrão.'},
            'competencia2': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Boa compreensão do tema.'},
            'competencia3': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Argumentação coerente.'},
            'competencia4': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Boa organização textual.'},
            'competencia5': {'nota': random.randint(160, 200), 'max': 200, 'comentario': 'Proposta de intervenção adequada.'}
        }
        
        nota_final = sum(comp['nota'] for comp in competencias.values()) / 5
        
        correcao = {
            'nota_final': round(nota_final, 1),
            'competencias': competencias,
            'estatisticas': {
                'palavras': palavras,
                'paragrafos': paragrafos,
                'linhas': texto.count('\n') + 1
            },
            'sugestoes': [
                'Revise a concordância verbal.',
                'Desenvolva mais o segundo argumento.',
                'Mantenha o foco no tema proposto.'
            ]
        }
        
        return jsonify({
            'success': True,
            'correcao': correcao
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    init_db()
    print("🚀 Servidor ConcursoMaster AI V4.1 iniciando...")
    print("📚 Acesse: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
